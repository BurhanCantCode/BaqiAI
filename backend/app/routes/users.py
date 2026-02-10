from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.schemas.user import UserCreate, UserResponse, RiskQuizRequest, RiskQuizResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Client = Depends(get_supabase),
):
    """Register a new user."""
    result = (
        db.table("users")
        .insert({
            "name": user_data.name,
            "phone": user_data.phone,
            "age": user_data.age,
            "monthly_income": user_data.monthly_income,
            "halal_preference": user_data.halal_preference,
        })
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create user")

    return result.data[0]


@router.get("/{user_id}/profile", response_model=UserResponse)
async def get_user_profile(
    user_id: int,
    db: Client = Depends(get_supabase),
):
    """Get user profile including risk assessment."""
    result = db.table("users").select("*").eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return result.data[0]


@router.post("/{user_id}/risk-quiz", response_model=RiskQuizResponse)
async def submit_risk_quiz(
    user_id: int,
    quiz: RiskQuizRequest,
    db: Client = Depends(get_supabase),
):
    """Submit risk assessment quiz and get risk profile."""
    if len(quiz.answers) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 answers required")

    for ans in quiz.answers:
        if not 1 <= ans <= 5:
            raise HTTPException(status_code=400, detail="Each answer must be 1-5")

    # Fetch user for age adjustment
    user_result = db.table("users").select("age").eq("id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")

    age = user_result.data[0].get("age") or 30

    # Calculate risk score
    raw_score = sum(quiz.answers) / len(quiz.answers)
    age_factor = max(0, (65 - age) / 65)
    adjusted_score = raw_score * 0.7 + age_factor * 5 * 0.3

    # Classify
    if adjusted_score <= 2.0:
        profile = "conservative"
        allocation = {"equity": 0.2, "fixed_income": 0.6, "mutual_fund": 0.2}
    elif adjusted_score <= 3.5:
        profile = "moderate"
        allocation = {"equity": 0.4, "fixed_income": 0.3, "mutual_fund": 0.3}
    else:
        profile = "aggressive"
        allocation = {"equity": 0.6, "fixed_income": 0.1, "mutual_fund": 0.3}

    # Update user risk profile
    db.table("users").update({"risk_profile": profile}).eq("id", user_id).execute()

    return RiskQuizResponse(
        risk_profile=profile,
        risk_score=round(adjusted_score, 1),
        allocation=allocation,
    )
