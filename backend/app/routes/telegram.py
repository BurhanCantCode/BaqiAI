"""Telegram bot status endpoint for the frontend."""

from fastapi import APIRouter

from app.services.telegram_bot import bot_status

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.get("/status")
async def get_telegram_status():
    """Return current Telegram bot status for the frontend dashboard."""
    return bot_status()
