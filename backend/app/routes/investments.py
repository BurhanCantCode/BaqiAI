from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.investment_executor import execute_investment

router = APIRouter(prefix="/investments", tags=["Investments"])


class ExecuteRequest(BaseModel):
    user_id: int
    portfolio: list[dict]  # List of allocation dicts from recommendation


@router.post("/execute")
async def execute_investments(request: ExecuteRequest):
    """
    Execute an approved investment recommendation.
    Creates investment records and a portfolio snapshot in Supabase.
    """
    if not request.portfolio:
        raise HTTPException(status_code=400, detail="Portfolio cannot be empty")

    try:
        result = await execute_investment(request.user_id, request.portfolio)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investment execution failed: {str(e)}")
