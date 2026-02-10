from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.services.spending_analyzer import analyze_transactions

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/{user_id}/analysis")
async def get_spending_analysis(
    user_id: int,
    db: Client = Depends(get_supabase),
):
    """Analyze user spending patterns and calculate baqi (investable surplus)."""
    # Verify user exists
    user_result = db.table("users").select("id").eq("id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all transactions
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

    analysis = analyze_transactions(txn_result.data)
    return analysis


@router.get("/{user_id}/list")
async def list_transactions(
    user_id: int,
    limit: int = 50,
    db: Client = Depends(get_supabase),
):
    """List user transactions (most recent first)."""
    result = (
        db.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return {"transactions": result.data, "count": len(result.data)}
