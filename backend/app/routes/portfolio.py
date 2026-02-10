from fastapi import APIRouter, HTTPException

from app.services.investment_executor import get_portfolio
from app.database import supabase

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{user_id}")
async def get_user_portfolio(user_id: int):
    """
    Get current portfolio holdings, performance, and historical snapshots.
    """
    try:
        result = await get_portfolio(user_id)
        if not result["holdings"]:
            return {
                "user_id": user_id,
                "holdings": [],
                "total_invested": 0,
                "current_value": 0,
                "total_return": 0,
                "return_percentage": 0,
                "snapshots": [],
                "message": "No active investments. Generate a recommendation first.",
            }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio fetch failed: {str(e)}")


@router.post("/{user_id}/rebalance")
async def rebalance_portfolio(user_id: int):
    """
    Trigger portfolio rebalancing — marks old investments as 'rebalanced'
    and generates a new recommendation.
    """
    # Mark current active investments as rebalanced
    supabase.table("investments").update(
        {"status": "rebalanced"}
    ).eq("user_id", user_id).eq("status", "active").execute()

    return {
        "user_id": user_id,
        "status": "rebalanced",
        "message": "Previous investments marked as rebalanced. Generate a new recommendation to get updated allocations.",
    }
