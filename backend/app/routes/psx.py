"""PSX stock prediction API routes."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.psx_prediction_service import (
    load_cached_predictions,
    is_cache_fresh,
    get_predictions_for_crew,
    run_predictions_for_all_sectors,
    PREDICTION_ORDER,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["psx"])

# Global state for background prediction tracking
_prediction_status = {
    "running": False,
    "progress": 0,
    "current_stock": None,
    "started_at": None,
    "completed_at": None,
    "error": None,
    "stocks_done": 0,
    "stocks_total": len(PREDICTION_ORDER),
}


def _progress_callback(symbol: str, pct: int, message: str):
    """Update global prediction status."""
    _prediction_status["current_stock"] = symbol
    _prediction_status["progress"] = pct
    if symbol != "DONE":
        _prediction_status["stocks_done"] = PREDICTION_ORDER.index(symbol) if symbol in PREDICTION_ORDER else 0
    else:
        _prediction_status["stocks_done"] = _prediction_status["stocks_total"]
    logger.info(f"[PSX Prediction] {pct}% - {message}")


@router.get("/psx/status")
async def get_prediction_status():
    """Get the current status of prediction generation."""
    return _prediction_status


@router.get("/psx/cache-info")
async def get_cache_info():
    """Get information about the prediction cache."""
    cache = load_cached_predictions()
    fresh = is_cache_fresh(cache)

    return {
        "cache_exists": bool(cache and cache.get("stocks")),
        "cache_fresh": fresh,
        "source": cache.get("source", "none") if cache else "none",
        "generated_at": cache.get("generated_at") if cache else None,
        "stocks_count": len(cache.get("stocks", {})) if cache else 0,
        "stocks": list(cache.get("stocks", {}).keys()) if cache else [],
    }


@router.post("/psx/run-predictions")
async def trigger_predictions(force_fresh: bool = False):
    """
    Trigger ML prediction generation for all 5 sector stocks.
    Runs in background (~4-7 minutes). Use GET /api/psx/status to check progress.
    Stocks run sequentially: LUCK -> FFC -> OGDC -> UBL -> SYS

    Query params:
        force_fresh: If true, re-runs ALL stocks. If false (default), skips
                     stocks that already have cached predictions.
    """
    if _prediction_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Prediction generation already running. Check /api/psx/status for progress.",
        )

    # Reset status
    _prediction_status.update({
        "running": True,
        "progress": 0,
        "current_stock": None,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
        "stocks_done": 0,
    })

    async def _run_in_background():
        try:
            await run_predictions_for_all_sectors(
                progress_callback=_progress_callback,
                force_fresh=force_fresh,
            )
            _prediction_status["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            _prediction_status["error"] = str(e)
            logger.error(f"Prediction generation failed: {e}")
        finally:
            _prediction_status["running"] = False

    asyncio.create_task(_run_in_background())

    return {
        "message": f"Prediction generation started (force_fresh={force_fresh})",
        "status_url": "/api/psx/status",
        "stocks": PREDICTION_ORDER,
        "estimated_time_seconds": 350 if force_fresh else 70,
    }


@router.get("/psx/predictions")
async def get_current_predictions():
    """Get the current predictions (from cache or seed data)."""
    predictions = get_predictions_for_crew()
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail="No predictions available. Run POST /api/psx/run-predictions first, or ensure seed data exists.",
        )
    return predictions
