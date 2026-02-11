"""Chat endpoints for Ollama-powered local LLM conversations."""

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.ollama_engine import (
    process_ollama_chat,
    stream_ollama_chat,
    get_chat_history,
    clear_chat_history,
    check_ollama_status,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: int
    message: str
    data_source: str = "csv"


@router.get("/status")
async def chat_status():
    """Check if Ollama is running and model is available."""
    return await check_ollama_status()


@router.post("/message")
async def send_message(req: ChatRequest):
    """Send a message and get a complete response."""
    reply = await process_ollama_chat(req.user_id, req.message, req.data_source)
    return {"reply": reply, "user_id": req.user_id}


@router.post("/stream")
async def stream_message(req: ChatRequest):
    """Send a message and get a streaming SSE response."""
    async def event_generator():
        async for token in stream_ollama_chat(req.user_id, req.message, req.data_source):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{user_id}")
async def get_history(user_id: int):
    """Get conversation history for a user."""
    return {"user_id": user_id, "messages": get_chat_history(user_id)}


@router.delete("/history/{user_id}")
async def delete_history(user_id: int):
    """Clear conversation history for a user."""
    clear_chat_history(user_id)
    return {"success": True, "user_id": user_id}
