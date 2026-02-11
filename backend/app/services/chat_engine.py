"""Claude-powered conversational AI engine for the BAQI AI Telegram bot.

Replaces the rigid state-machine conversation manager with a free-text
Claude-powered chat that has full context about the user's finances.
"""

import logging
import os
from typing import Optional

import anthropic

from app.config import settings
from app.database import supabase
from app.services.spending_analyzer import analyze_transactions, normalize_csv_transactions
from app.services.insights_engine import parse_csv_transactions, extract_data_exhaust

logger = logging.getLogger(__name__)

# In-memory conversation history: telegram_id -> list of messages
_chat_histories: dict[int, list[dict]] = {}
_MAX_HISTORY = 20  # 10 turns

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "transactions1 cleaned2.csv",
)

SYSTEM_PROMPT = """You are BAQI AI, a witty and encouraging personal financial assistant on Telegram.
You specialize in Islamic (Shariah-compliant) finance and help users understand spending, save money, and invest wisely.

Personality:
- Like a financially-savvy best friend — fun, supportive, gently honest about bad habits
- Use emoji naturally (1-2 per message), Telegram Markdown (*bold*, _italic_)
- Keep responses concise (2-4 sentences) unless user asks for detail
- Reference specific merchants and dollar/PKR amounts from their data
- When suggesting savings, name exact merchants and amounts they could cut
- For investment advice, emphasize you provide educational context, not financial advice
- Be playful — make money conversations feel less stressful

Here is this user's complete financial picture:

{financial_context}

Rules:
- ONLY reference numbers from the context above. Never invent or hallucinate data.
- If asked about data you don't have, say so honestly.
- If asked something unrelated to finance, briefly engage then gently steer back.
- Keep responses under 300 words for Telegram readability.
- Use the correct currency shown in the context above."""


def _get_transactions(user_id: int) -> tuple[list[dict], str]:
    """Get transactions — CSV first, Supabase fallback. Returns (txns, source)."""
    if os.path.exists(CSV_PATH):
        csv_txns = parse_csv_transactions(CSV_PATH)
        if len(csv_txns) >= 10:
            normalized = normalize_csv_transactions(csv_txns)
            return normalized, "csv"

    res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    if res.data and len(res.data) >= 10:
        return res.data, "supabase"

    return [], "none"


def _build_financial_context(user: dict, analysis: dict, data_exhaust: dict, source: str) -> str:
    """Build a compact financial context string for Claude's system prompt."""
    currency = "USD" if source == "csv" else "PKR"
    months = len(analysis.get("monthly_breakdown", [])) or 1
    monthly_baqi = round(analysis.get("baqi_amount", 0) / months)

    avg_monthly_income = round(analysis.get("total_income", 0) / months)
    avg_monthly_spending = round(analysis.get("total_spending", 0) / months)
    watery_potential_monthly = round(analysis.get("watery_savings_potential", 0) / months)

    lines = [
        f"User: {user.get('name', 'Unknown')}",
        f"Currency: {currency}",
        f"Data spans {months} month(s)",
        f"Risk Profile: {user.get('risk_profile', 'not assessed yet')}",
        "",
        f"Monthly Average Income: {currency} {avg_monthly_income:,}/month",
        f"Monthly Average Spending: {currency} {avg_monthly_spending:,}/month",
        f"Savings Rate: {analysis.get('savings_rate', 0):.1f}%",
        f"Monthly Investable BAQI: {currency} {monthly_baqi:,}/month",
        f"Potential Extra Monthly Savings (50% watery cut): {currency} {watery_potential_monthly:,}/month",
        "",
    ]

    # Category breakdown — show monthly averages, not all-time totals
    for cat_name in ["fixed", "discretionary", "watery"]:
        cat = analysis.get(cat_name, {})
        pct = cat.get("percentage", 0)
        total = cat.get("total", 0)
        monthly_avg = round(total / months)
        items = cat.get("items", [])
        lines.append(f"{cat_name.title()} Spending: {pct:.1f}% (~{currency} {monthly_avg:,}/month)")
        for item in items[:5]:
            item_monthly = round(item["total"] / months)
            lines.append(f"  - {item['merchant']}: ~{currency} {item_monthly:,}/month")
        lines.append("")

    # Monthly trend (last 3 months)
    monthly = analysis.get("monthly_breakdown", [])
    if monthly:
        lines.append("Monthly Spending Trend:")
        for m in monthly[-3:]:
            lines.append(f"  {m.get('month', '?')}: {currency} {m.get('spending', 0):,.0f}")
        lines.append("")

    # Lifestyle indicators from data exhaust
    lifestyle = data_exhaust.get("lifestyle_indicators", {})
    if lifestyle:
        indicators = []
        if lifestyle.get("coffee_addict_score", 0) > 3:
            indicators.append(f"Coffee addict score: {lifestyle['coffee_addict_score']}/10")
        if lifestyle.get("foodie_score", 0) > 3:
            indicators.append(f"Foodie score: {lifestyle['foodie_score']}/10")
        if lifestyle.get("ride_hailing_dependency", 0) > 3:
            indicators.append(f"Ride-hailing dependency: {lifestyle['ride_hailing_dependency']}/10")
        if lifestyle.get("digital_subscriber_count", 0) > 0:
            indicators.append(f"Digital subscriptions: {lifestyle['digital_subscriber_count']}")
        if indicators:
            lines.append("Lifestyle Signals:")
            for ind in indicators:
                lines.append(f"  - {ind}")
            lines.append("")

    # Subscriptions
    subs = data_exhaust.get("subscription_detection", [])
    if subs:
        lines.append("Detected Subscriptions:")
        for s in subs[:8]:
            lines.append(f"  - {s.get('merchant', '?')}: ~{currency} {s.get('avg_amount', 0):,.0f}/month")
        lines.append("")

    # Top merchants by loyalty — show monthly averages
    loyalty = data_exhaust.get("merchant_loyalty", [])
    if loyalty:
        lines.append("Most Visited Merchants (monthly avg):")
        for m in loyalty[:8]:
            total = m.get("total", 0)
            monthly_avg = round(total / months)
            visits_monthly = round(m.get("visits", 0) / months, 1)
            lines.append(f"  - {m.get('merchant', '?')}: ~{visits_monthly} visits/month, ~{currency} {monthly_avg:,}/month")
        lines.append("")

    # PSX predictions summary (if available)
    try:
        from app.services.psx_prediction_service import get_predictions_for_crew
        psx = get_predictions_for_crew()
        if psx and psx.get("stocks"):
            lines.append("PSX Stock Predictions (21-day ML forecast):")
            for sym, data in psx["stocks"].items():
                ml = data.get("ml_prediction", {})
                lines.append(
                    f"  - {data.get('name', sym)} ({sym}): "
                    f"Price {data.get('price', 0):,.0f}, "
                    f"Predicted return: {data.get('predicted_return', 0):+.1%}, "
                    f"Direction: {ml.get('direction', 'N/A')}"
                )
            lines.append("")
    except Exception:
        pass

    return "\n".join(lines)


async def process_chat(telegram_id: int, message: str) -> str:
    """Process a free-text message and return Claude's response."""
    # Look up user
    res = supabase.table("users").select("*").eq("phone", str(telegram_id)).execute()
    if not res.data:
        return "I don't have your account yet! Send /start to get set up."

    user = res.data[0]

    # Get transactions and analysis
    txns, source = _get_transactions(user["id"])
    if not txns:
        return (
            "I don't have your spending data yet! "
            "Upload a bank statement on the web dashboard, or send /start to generate sample data."
        )

    analysis = analyze_transactions(txns)
    data_exhaust = extract_data_exhaust(txns)
    context = _build_financial_context(user, analysis, data_exhaust, source)

    # Build system prompt
    system = SYSTEM_PROMPT.format(financial_context=context)

    # Get or create conversation history
    if telegram_id not in _chat_histories:
        _chat_histories[telegram_id] = []
    history = _chat_histories[telegram_id]

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Trim history if too long
    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system=system,
            messages=history,
        )

        reply = response.content[0].text

        # Store assistant reply in history
        history.append({"role": "assistant", "content": reply})

        # Trim again if needed
        if len(history) > _MAX_HISTORY:
            history[:] = history[-_MAX_HISTORY:]

        return reply

    except Exception as e:
        logger.error(f"Chat engine error: {e}")
        # Remove the user message we added since we failed
        if history and history[-1]["role"] == "user":
            history.pop()
        return "Oops, my brain glitched for a second! Try again or use /help for commands."


async def generate_spending_alert(
    user_id: int,
    merchant: str,
    amount: float,
    analysis: dict,
    category: str,
    source: str,
) -> str:
    """Generate a fun, contextual spending alert using Claude."""
    currency = "USD" if source == "csv" else "PKR"
    months = len(analysis.get("monthly_breakdown", [])) or 1

    # Find the specific merchant's total from all category items
    merchant_total = 0
    spending_type = _spending_type_for_category(category)
    for cat_name in ["fixed", "discretionary", "watery"]:
        for item in analysis.get(cat_name, {}).get("items", []):
            if item["merchant"].lower() == merchant.lower():
                merchant_total = item["total"]

    # Get the specific category's total (e.g. "food" total, not all of "watery")
    # The analysis groups by spending_type, so find items matching this category
    category_total = 0
    for cat_name in ["fixed", "discretionary", "watery"]:
        for item in analysis.get(cat_name, {}).get("items", []):
            category_total += item["total"]  # we sum the type total
        # But we want the spending_type total, not per-category
    # Use the spending type total and divide by months for monthly average
    type_total = analysis.get(spending_type, {}).get("total", 0)
    avg_monthly_type = round(type_total / months)

    # Monthly average for the whole account
    avg_monthly_spend = round(analysis["total_spending"] / months)
    savings_rate = analysis.get("savings_rate", 0)

    prompt = f"""Generate a fun, short Telegram spending notification (2-3 sentences max, 1-2 emoji).

Transaction: {currency} {amount:,.2f} at {merchant} ({category})
Their monthly average total spending: {currency} {avg_monthly_spend:,.0f}/month
Their monthly average on {spending_type} expenses: {currency} {avg_monthly_type:,.0f}/month
{"They have spent " + currency + " " + f"{merchant_total:,.0f}" + " at " + merchant + " historically." if merchant_total > 0 else "This is a new merchant for them."}
Their savings rate: {savings_rate:.1f}%

Be witty and reference the specific merchant by name. If they're overspending, be playfully concerned.
If under budget, celebrate briefly. Use Telegram Markdown (*bold*). Keep it 2-3 sentences."""

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Alert generation error: {e}")
        return f"💸 You just spent {currency} {amount:,.2f} at *{merchant}*!"


def _spending_type_for_category(category: str) -> str:
    """Map a category to its spending type (fixed/discretionary/watery).

    Handles both constants.py categories AND CSV-specific categories
    from spending_analyzer._classify_merchant.
    """
    from app.utils.constants import FIXED_CATEGORIES, DISCRETIONARY_CATEGORIES, WATERY_CATEGORIES
    cat_lower = category.lower()

    # Standard constants
    if cat_lower in {c.lower() for c in FIXED_CATEGORIES}:
        return "fixed"
    if cat_lower in {c.lower() for c in DISCRETIONARY_CATEGORIES}:
        return "discretionary"
    if cat_lower in {c.lower() for c in WATERY_CATEGORIES}:
        return "watery"

    # CSV-specific categories from _classify_merchant that aren't in constants
    csv_fixed = {"taxes", "management", "subscription", "health_insurance"}
    if cat_lower in csv_fixed:
        return "fixed"

    return "watery"
