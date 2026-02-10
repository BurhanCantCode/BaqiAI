from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    name: str
    phone: str
    age: Optional[int] = None
    monthly_income: Optional[int] = 150000
    halal_preference: bool = True


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    age: Optional[int] = None
    risk_profile: str = "moderate"
    halal_preference: bool = True
    monthly_income: int = 0


class RiskQuizRequest(BaseModel):
    answers: list[int]  # List of 5 answers, each 1-5


class RiskQuizResponse(BaseModel):
    risk_profile: str  # conservative / moderate / aggressive
    risk_score: float  # 1-10
    allocation: dict  # {"equity": 0.3, "fixed_income": 0.5, "mutual_fund": 0.2}
