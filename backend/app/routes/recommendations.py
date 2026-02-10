from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.recommendation_engine import generate_recommendation

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationRequest(BaseModel):
    user_id: int
    source: str | None = None


@router.post("/generate")
async def generate_recommendations(request: RecommendationRequest):
    """
    Main endpoint - triggers the full CrewAI multi-agent pipeline.

    This is the core AI feature: spending analysis -> risk profiling ->
    market sentiment -> halal screening -> portfolio recommendation.

    Takes 30-90 seconds depending on LLM response time.
    """
    try:
        result = await generate_recommendation(request.user_id, source=request.source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")
