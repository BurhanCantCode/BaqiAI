import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.database import get_supabase
from app.services.spending_analyzer import analyze_transactions, normalize_csv_transactions
from app.services.insights_engine import parse_csv_transactions

router = APIRouter(prefix="/transactions", tags=["Transactions"])

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "transactions1 cleaned2.csv")


def _get_csv_transactions() -> list[dict] | None:
    """Load and normalize CSV transactions if the file exists."""
    if os.path.exists(CSV_PATH):
        csv_txns = parse_csv_transactions(CSV_PATH)
        if len(csv_txns) >= 10:
            return normalize_csv_transactions(csv_txns)
    return None


def _get_supabase_transactions(user_id: int, db: Client) -> list[dict]:
    """Fetch transactions from Supabase for a given user."""
    user_result = db.table("users").select("id").eq("id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")

    txn_result = (
        db.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )

    if not txn_result.data:
        raise HTTPException(
            status_code=404,
            detail="No transactions found. Generate demo data first via POST /api/demo/synthetic-data",
        )
    return txn_result.data


@router.get("/{user_id}/analysis")
async def get_spending_analysis(
    user_id: int,
    source: Optional[str] = Query(None, description="Data source: csv or supabase"),
    db: Client = Depends(get_supabase),
):
    """Analyze user spending patterns and calculate baqi (investable surplus)."""
    if source == "csv":
        csv_transactions = _get_csv_transactions()
        if not csv_transactions:
            raise HTTPException(status_code=404, detail="CSV data not available")
        analysis = analyze_transactions(csv_transactions)
        analysis["source"] = "csv"
        analysis["currency"] = "USD"
        return analysis

    if source == "supabase":
        transactions = _get_supabase_transactions(user_id, db)
        analysis = analyze_transactions(transactions)
        analysis["source"] = "supabase"
        analysis["currency"] = "PKR"
        return analysis

    # Auto-detect: prefer CSV if available
    csv_transactions = _get_csv_transactions()
    if csv_transactions:
        analysis = analyze_transactions(csv_transactions)
        analysis["source"] = "csv"
        analysis["currency"] = "USD"
        return analysis

    transactions = _get_supabase_transactions(user_id, db)
    analysis = analyze_transactions(transactions)
    analysis["source"] = "supabase"
    analysis["currency"] = "PKR"
    return analysis


@router.get("/{user_id}/list")
async def list_transactions(
    user_id: int,
    limit: int = 50,
    source: Optional[str] = Query(None, description="Data source: csv or supabase"),
    db: Client = Depends(get_supabase),
):
    """List user transactions (most recent first)."""
    if source == "csv":
        csv_transactions = _get_csv_transactions()
        if not csv_transactions:
            raise HTTPException(status_code=404, detail="CSV data not available")
        sorted_txns = sorted(csv_transactions, key=lambda t: t["date"], reverse=True)
        return {"transactions": sorted_txns[:limit], "count": len(sorted_txns[:limit]), "source": "csv"}

    if source == "supabase":
        result = (
            db.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )
        return {"transactions": result.data, "count": len(result.data), "source": "supabase"}

    # Auto-detect
    csv_transactions = _get_csv_transactions()
    if csv_transactions:
        sorted_txns = sorted(csv_transactions, key=lambda t: t["date"], reverse=True)
        return {"transactions": sorted_txns[:limit], "count": len(sorted_txns[:limit]), "source": "csv"}

    result = (
        db.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return {"transactions": result.data, "count": len(result.data), "source": "supabase"}
