from pydantic import BaseModel
from typing import Optional


class InvestmentResponse(BaseModel):
    id: int
    user_id: int
    investment_date: str
    asset_type: str
    asset_name: str
    ticker: str
    amount: float
    quantity: float
    purchase_price: float
    current_price: float
    status: str


class PortfolioAllocation(BaseModel):
    asset_name: str
    ticker: str
    asset_type: str  # stock | mutual_fund | fixed_income
    amount_pkr: float
    percentage: float
    expected_return: float
    is_halal: bool
    rationale: str


class InvestmentRecommendation(BaseModel):
    portfolio: list[PortfolioAllocation]
    total_invested: float
    expected_monthly_return: float
    summary: str


class ExecuteInvestmentRequest(BaseModel):
    user_id: int
    recommendation: InvestmentRecommendation
