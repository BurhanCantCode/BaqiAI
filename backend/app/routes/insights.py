"""AI-powered data exhaust insights endpoint."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.database import get_supabase
from app.services.insights_engine import generate_insights, parse_csv_transactions

router = APIRouter(prefix="/insights", tags=["Insights"])

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "transactions1 cleaned2.csv")


@router.get("/{user_id}")
async def get_insights(
    user_id: int,
    source: Optional[str] = Query(None, description="Data source: csv or supabase"),
    db: Client = Depends(get_supabase),
):
    """Generate AI insights from transaction data exhaust."""
    transactions = None

    if source == "csv":
        if os.path.exists(CSV_PATH):
            csv_txns = parse_csv_transactions(CSV_PATH)
            if len(csv_txns) >= 10:
                transactions = csv_txns
        if transactions is None:
            raise HTTPException(status_code=404, detail="CSV data not available")

    elif source == "supabase":
        user_res = db.table("users").select("id").eq("id", user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="User not found")
        txn_res = db.table("transactions").select("*").eq("user_id", user_id).order("date").execute()
        if not txn_res.data or len(txn_res.data) < 10:
            raise HTTPException(status_code=400, detail="Not enough transaction data. Generate demo data first.")
        transactions = txn_res.data

    else:
        # Auto-detect: prefer CSV
        if os.path.exists(CSV_PATH):
            csv_txns = parse_csv_transactions(CSV_PATH)
            if len(csv_txns) >= 10:
                transactions = csv_txns

        if transactions is None:
            user_res = db.table("users").select("id").eq("id", user_id).execute()
            if not user_res.data:
                raise HTTPException(status_code=404, detail="User not found")
            txn_res = db.table("transactions").select("*").eq("user_id", user_id).order("date").execute()
            if not txn_res.data or len(txn_res.data) < 10:
                raise HTTPException(status_code=400, detail="Not enough transaction data. Generate demo data first.")
            transactions = txn_res.data

    result = await generate_insights(user_id, transactions)
    return result
