"""Orchestrates the CrewAI pipeline from async FastAPI."""

import asyncio
import json
import os

from app.database import supabase
from app.services.spending_analyzer import analyze_transactions, normalize_csv_transactions
from app.services.insights_engine import parse_csv_transactions
from app.agents.crew import BaqiCrew

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "transactions1 cleaned2.csv")


async def generate_recommendation(user_id: int, source: str | None = None) -> dict:
    """
    Run the full AI recommendation pipeline for a user.

    1. Fetch user profile + transactions (source-aware)
    2. Run spending analysis
    3. Launch CrewAI crew in a thread (sync -> async bridge)
    4. Return structured recommendation
    """
    # 1. Fetch user
    user_result = supabase.table("users").select("*").eq("id", user_id).single().execute()
    user = user_result.data

    # 2. Fetch transactions based on source
    transactions = None

    if source == "csv":
        if os.path.exists(CSV_PATH):
            csv_txns = parse_csv_transactions(CSV_PATH)
            if len(csv_txns) >= 10:
                transactions = normalize_csv_transactions(csv_txns)
    elif source != "supabase":
        # Auto-detect: try CSV first
        if os.path.exists(CSV_PATH):
            csv_txns = parse_csv_transactions(CSV_PATH)
            if len(csv_txns) >= 10:
                transactions = normalize_csv_transactions(csv_txns)

    if transactions is None:
        txn_result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("date")
            .execute()
        )
        transactions = txn_result.data

    # 3. Run spending analysis
    analysis = analyze_transactions(transactions)

    # 4. Prepare inputs for CrewAI
    months = len(analysis.get("monthly_breakdown", [])) or 6
    crew_inputs = {
        "user_id": str(user_id),
        "income": user.get("monthly_income", 150000),
        "age": user.get("age", 28),
        "quiz_answers": "[3,3,3,3,3]",
        "risk_profile": user.get("risk_profile", "moderate"),
        "baqi_amount": analysis["baqi_amount"] / months,  # Monthly average
        "halal_preference": user.get("halal_preference", True),
        "spending_data": json.dumps({
            "fixed_pct": analysis["fixed"]["percentage"],
            "discretionary_pct": analysis["discretionary"]["percentage"],
            "watery_pct": analysis["watery"]["percentage"],
            "baqi": analysis["baqi_amount"],
            "top_watery": analysis["watery"]["items"][:3],
        }),
    }

    # 5. Run CrewAI in a thread to avoid blocking the event loop
    crew = BaqiCrew()
    result = await asyncio.to_thread(crew.run, crew_inputs)

    # 6. Save recommendation to Supabase if it has portfolio data
    if isinstance(result, dict) and "portfolio" in result:
        for alloc in result["portfolio"]:
            ticker = alloc.get("ticker", "")[:30]  # Truncate to fit DB column
            supabase.table("investments").insert({
                "user_id": user_id,
                "investment_date": None,  # Not executed yet
                "asset_type": alloc.get("asset_type", "stock"),
                "asset_name": alloc.get("asset_name", "")[:100],
                "ticker": ticker,
                "amount": alloc.get("amount_pkr", 0),
                "quantity": 0,
                "purchase_price": 0,
                "current_price": 0,
                "status": "recommended",
            }).execute()

    return {
        "user_id": user_id,
        "spending_analysis": {
            "total_income": analysis["total_income"],
            "total_spending": analysis["total_spending"],
            "baqi_amount": analysis["baqi_amount"],
            "monthly_baqi": round(analysis["baqi_amount"] / months, 2),
        },
        "risk_profile": user.get("risk_profile", "moderate"),
        "recommendation": result,
    }
