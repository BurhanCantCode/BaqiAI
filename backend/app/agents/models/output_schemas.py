"""Pydantic models for structured agent output."""

from pydantic import BaseModel, Field


class SpendingAnalysisOutput(BaseModel):
    total_income: float = Field(description="Total income in PKR")
    total_spending: float = Field(description="Total spending in PKR")
    baqi_amount: float = Field(description="Investable surplus in PKR")
    fixed_pct: float = Field(description="Fixed spending percentage")
    discretionary_pct: float = Field(description="Discretionary spending percentage")
    watery_pct: float = Field(description="Watery spending percentage")
    top_reductions: list[str] = Field(description="Top 3 spending reduction suggestions")


class RiskProfileOutput(BaseModel):
    risk_category: str = Field(description="conservative, moderate, or aggressive")
    risk_score: float = Field(description="Risk score 1-10")
    equity_pct: float = Field(description="Equity allocation 0-1")
    fixed_income_pct: float = Field(description="Fixed income allocation 0-1")
    mutual_fund_pct: float = Field(description="Mutual fund allocation 0-1")
    rationale: str = Field(description="Explanation of risk assessment")


class MarketSentimentOutput(BaseModel):
    market_outlook: str = Field(description="bullish, neutral, or bearish")
    kse100_trend: str = Field(description="KSE-100 trend description")
    top_sectors: list[str] = Field(description="Top sectors for investment")
    risks: list[str] = Field(description="Market risk factors")
    opportunities: list[str] = Field(description="Market opportunities")


class HalalScreenResult(BaseModel):
    ticker: str
    is_halal: bool
    reason: str


class HalalScreeningOutput(BaseModel):
    screened_stocks: list[HalalScreenResult]
    compliant_count: int
    total_screened: int


class PortfolioAllocationOutput(BaseModel):
    asset_name: str = Field(description="Full name of stock or fund")
    ticker: str = Field(description="Ticker symbol")
    asset_type: str = Field(description="stock, mutual_fund, or fixed_income")
    amount_pkr: float = Field(description="Amount to invest in PKR")
    percentage: float = Field(description="Percentage of total portfolio")
    expected_return: float = Field(description="Expected annual return as decimal")
    is_halal: bool = Field(description="Whether the asset is Shariah compliant")
    rationale: str = Field(description="Reason for selecting this asset")


class InvestmentRecommendationOutput(BaseModel):
    portfolio: list[PortfolioAllocationOutput] = Field(description="List of portfolio allocations")
    total_invested: float = Field(description="Total amount invested in PKR")
    expected_annual_return: float = Field(description="Expected annual return as decimal")
    summary: str = Field(description="2-3 sentence summary of the investment strategy")
