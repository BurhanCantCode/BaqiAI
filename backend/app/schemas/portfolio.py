from pydantic import BaseModel


class PortfolioSnapshot(BaseModel):
    id: int
    user_id: int
    snapshot_date: str
    total_invested: float
    current_value: float
    return_percentage: float


class PortfolioResponse(BaseModel):
    user_id: int
    holdings: list[dict]
    total_invested: float
    current_value: float
    total_return: float
    return_percentage: float
    snapshots: list[PortfolioSnapshot]
