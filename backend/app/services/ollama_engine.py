"""Ollama-powered local LLM chat engine for the BAQI AI web app.

Uses the same financial context as the Telegram Claude chat engine,
but runs entirely locally via Ollama on Apple Silicon.
"""

import json
import logging
from typing import AsyncGenerator

import httpx

from app.database import supabase
from app.services.spending_analyzer import analyze_transactions, normalize_csv_transactions
from app.services.insights_engine import parse_csv_transactions, extract_data_exhaust
from app.services.chat_engine import _get_transactions, _build_financial_context

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"

# In-memory conversation history: user_id -> list of messages
_web_chat_histories: dict[int, list[dict]] = {}
_MAX_HISTORY = 20  # 10 turns

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
    """Look up user by ID."""
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


def _get_context_and_prompt(user_id: int) -> tuple[str, str] | None:
    """Build system prompt with financial context. Returns (system_prompt, source) or None."""
    user = _get_user_by_id(user_id)
    if not user:
        user = {"id": user_id, "name": "User", "risk_profile": "not assessed"}

    txns, source = _get_transactions(user_id)
    if not txns:
        return None

    analysis = analyze_transactions(txns)
    data_exhaust = extract_data_exhaust(txns)
    context = _build_financial_context(user, analysis, data_exhaust, source)
    system = SYSTEM_PROMPT.format(financial_context=context)
    return system, source


async def check_ollama_status() -> dict:
    """Check if Ollama is running and has the model available."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_model = any(OLLAMA_MODEL in name for name in model_names)
                return {
                    "online": True,
                    "model": OLLAMA_MODEL,
                    "model_loaded": has_model,
                    "available_models": model_names,
                }
    except Exception:
        pass
    return {"online": False, "model": OLLAMA_MODEL, "model_loaded": False}


async def process_ollama_chat(user_id: int, message: str, data_source: str = "csv") -> str:
    """Process a chat message via Ollama and return the response."""
    result = _get_context_and_prompt(user_id)
    if not result:
        return "I don't have your spending data yet! Upload a bank statement on the Dashboard first."

    system_prompt, source = result

    # Get or create conversation history
    if user_id not in _web_chat_histories:
        _web_chat_histories[user_id] = []
    history = _web_chat_histories[user_id]

    # Add user message
    history.append({"role": "user", "content": message})

    # Trim if too long
    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    # Build messages with system prompt as first message
    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("message", {}).get("content", "")

            if not reply:
                history.pop()
                return "Hmm, I got an empty response. Try asking again!"

            # Store assistant reply
            history.append({"role": "assistant", "content": reply})
            if len(history) > _MAX_HISTORY:
                history[:] = history[-_MAX_HISTORY:]

            return reply

    except httpx.ConnectError:
        history.pop()
        return "Ollama is not running! Please start it with `ollama serve` in your terminal."
    except Exception as e:
        logger.error(f"Ollama chat error: {e}")
        history.pop()
        return "Something went wrong with the local AI. Make sure Ollama is running and try again."


async def stream_ollama_chat(user_id: int, message: str, data_source: str = "csv") -> AsyncGenerator[str, None]:
    """Stream a chat response from Ollama token by token."""
    result = _get_context_and_prompt(user_id)
    if not result:
        yield "I don't have your spending data yet! Upload a bank statement on the Dashboard first."
        return

    system_prompt, source = result

    # Get or create conversation history
    if user_id not in _web_chat_histories:
        _web_chat_histories[user_id] = []
    history = _web_chat_histories[user_id]

    # Add user message
    history.append({"role": "user", "content": message})
    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    messages = [{"role": "system", "content": system_prompt}] + history
    full_response = ""

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": True,
                },
                timeout=120.0,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full_response += token
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        # Store the full response in history
        if full_response:
            history.append({"role": "assistant", "content": full_response})
            if len(history) > _MAX_HISTORY:
                history[:] = history[-_MAX_HISTORY:]
        else:
            history.pop()

    except httpx.ConnectError:
        history.pop()
        yield "Ollama is not running! Please start it with `ollama serve` in your terminal."
    except Exception as e:
        logger.error(f"Ollama stream error: {e}")
        history.pop()
        yield "Something went wrong with the local AI. Make sure Ollama is running and try again."


def get_chat_history(user_id: int) -> list[dict]:
    """Return conversation history for a user."""
    return _web_chat_histories.get(user_id, [])


def clear_chat_history(user_id: int) -> bool:
    """Clear conversation history for a user."""
    if user_id in _web_chat_histories:
        del _web_chat_histories[user_id]
    return True
