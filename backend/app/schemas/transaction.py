from pydantic import BaseModel
from typing import Optional


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    date: str
    amount: float
    merchant: str
    category: Optional[str] = None
    is_recurring: bool = False
    spending_type: Optional[str] = None


class CategoryBreakdown(BaseModel):
    total: float
    percentage: float
    items: list[dict]


class SpendingAnalysis(BaseModel):
    total_income: float
    total_spending: float
    fixed: CategoryBreakdown
    discretionary: CategoryBreakdown
    watery: CategoryBreakdown
    baqi_amount: float  # income - spending
    savings_rate: float  # percentage
    watery_savings_potential: float  # 50% of watery that could be redirected
    recommended_investment: float  # baqi + watery_savings_potential
    monthly_breakdown: list[dict]
