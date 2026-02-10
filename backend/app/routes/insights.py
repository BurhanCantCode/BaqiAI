"""AI-powered data exhaust insights endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.services.insights_engine import generate_insights

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/{user_id}")
async def get_insights(user_id: int, db: Client = Depends(get_supabase)):
    """Generate AI insights from transaction data exhaust."""
    # Verify user exists
    user_res = db.table("users").select("id").eq("id", user_id).execute()
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all transactions
    txn_res = db.table("transactions").select("*").eq("user_id", user_id).order("date").execute()
    if not txn_res.data or len(txn_res.data) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough transaction data. Generate demo data first.",
        )

    result = await generate_insights(user_id, txn_res.data)
    return result
