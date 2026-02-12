"""Local LLM chat engine for the BAQI AI web app.

Uses Ollama (llama3.1:8b) running locally on Apple Silicon.
"""

import logging
from typing import AsyncGenerator

import httpx

from app.services.chat_engine import _get_transactions, _build_financial_context
from app.services.spending_analyzer import analyze_transactions
from app.services.insights_engine import extract_data_exhaust
from app.database import supabase

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"

_web_chat_histories: dict[int, list[dict]] = {}
_MAX_HISTORY = 20

SYSTEM_PROMPT = """You are BAQI AI, a witty and encouraging personal financial assistant.
You specialize in Islamic (Shariah-compliant) finance and help users understand spending, save money, and invest wisely.

Personality:
- Like a financially-savvy best friend — fun, supportive, gently honest about bad habits
- Use emoji naturally (1-2 per message)
- Keep responses concise (2-4 sentences) unless user asks for detail
- Reference specific merchants and dollar/PKR amounts from their data
- When suggesting savings, name exact merchants and amounts they could cut
- For investment advice, emphasize you provide educational context, not financial advice
- Be playful — make money conversations feel less stressful
- Use **bold** for emphasis (standard Markdown)

Here is this user's complete financial picture:

{financial_context}

Rules:
- ONLY reference numbers from the context above. Never invent or hallucinate data.
- If asked about data you don't have, say so honestly.
- If asked something unrelated to finance, briefly engage then gently steer back.
- Keep responses under 300 words.
- Use the correct currency shown in the context above."""


def _get_user_by_id(user_id: int) -> dict | None:
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


def _get_context_and_prompt(user_id: int) -> tuple[str, str] | None:
    user = _get_user_by_id(user_id)
    if not user:
        user = {"id": user_id, "name": "User", "risk_profile": "not assessed"}

    txns, source = _get_transactions(user_id)
    if not txns:
        return None

    analysis = analyze_transactions(txns)
    data_exhaust = extract_data_exhaust(txns)
    context = _build_financial_context(user, analysis, data_exhaust, source, transactions=txns)
    system = SYSTEM_PROMPT.format(financial_context=context)
    return system, source


async def check_ollama_status() -> dict:
    """Check if Ollama is running and model is available."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_loaded = any(OLLAMA_MODEL in m for m in models)
                return {
                    "online": True,
                    "model": OLLAMA_MODEL,
                    "model_loaded": model_loaded,
                    "available_models": models,
                }
    except Exception:
        pass
    return {
        "online": False,
        "model": OLLAMA_MODEL,
        "model_loaded": False,
        "available_models": [],
    }


async def process_ollama_chat(user_id: int, message: str, data_source: str = "csv") -> str:
    """Process chat via local Ollama."""
    result = _get_context_and_prompt(user_id)
    if not result:
        return "I don't have your spending data yet! Upload a bank statement on the Dashboard first."

    system_prompt, source = result

    if user_id not in _web_chat_histories:
        _web_chat_histories[user_id] = []
    history = _web_chat_histories[user_id]

    history.append({"role": "user", "content": message})
    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    try:
        ollama_messages = [{"role": "system", "content": system_prompt}] + history
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": ollama_messages, "stream": False},
                timeout=120.0,
            )
            resp.raise_for_status()
            reply = resp.json()["message"]["content"]

        history.append({"role": "assistant", "content": reply})
        if len(history) > _MAX_HISTORY:
            history[:] = history[-_MAX_HISTORY:]

        return reply
    except Exception as e:
        logger.error(f"Chat error: {e}")
        if history and history[-1]["role"] == "user":
            history.pop()
        return "Oops, something went wrong! Make sure Ollama is running (`ollama serve`)."


async def stream_ollama_chat(user_id: int, message: str, data_source: str = "csv") -> AsyncGenerator[str, None]:
    """Stream chat via local Ollama."""
    result = _get_context_and_prompt(user_id)
    if not result:
        yield "I don't have your spending data yet! Upload a bank statement on the Dashboard first."
        return

    system_prompt, source = result

    if user_id not in _web_chat_histories:
        _web_chat_histories[user_id] = []
    history = _web_chat_histories[user_id]

    history.append({"role": "user", "content": message})
    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    full_response = ""

    try:
        ollama_messages = [{"role": "system", "content": system_prompt}] + history
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": ollama_messages, "stream": True},
                timeout=120.0,
            ) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full_response += token
                            yield token

        if full_response:
            history.append({"role": "assistant", "content": full_response})
            if len(history) > _MAX_HISTORY:
                history[:] = history[-_MAX_HISTORY:]
        else:
            history.pop()

    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        if history and history[-1]["role"] == "user":
            history.pop()
        yield "Oops, something went wrong! Make sure Ollama is running (`ollama serve`)."


def get_chat_history(user_id: int) -> list[dict]:
    return _web_chat_histories.get(user_id, [])


def clear_chat_history(user_id: int) -> bool:
    if user_id in _web_chat_histories:
        del _web_chat_histories[user_id]
    return True
