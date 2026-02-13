"""Admin endpoints for triggering Telegram bot notifications (demo/hackathon)."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.database import supabase
from app.services.spending_analyzer import (
    analyze_transactions,
    normalize_csv_transactions,
    _classify_merchant,
)
from app.services.insights_engine import parse_csv_transactions
from app.services.chat_engine import generate_spending_alert

import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "transactions1 cleaned2.csv",
)


def _get_user(user_id: int) -> dict:
    """Get user by ID, raise 404 if not found."""
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return res.data[0]


def _get_analysis(user_id: int) -> tuple[dict, str]:
    """Get spending analysis from real data. Returns (analysis, source)."""
    # Try CSV first (real bank statement)
    if os.path.exists(CSV_PATH):
        csv_txns = parse_csv_transactions(CSV_PATH)
        if len(csv_txns) >= 10:
            normalized = normalize_csv_transactions(csv_txns)
            return analyze_transactions(normalized), "csv"

    # Fallback to Supabase
    res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    if res.data and len(res.data) >= 10:
        return analyze_transactions(res.data), "supabase"

    raise HTTPException(status_code=404, detail="No spending data available for this user")


def _filter_transactions_by_days(txns: list[dict], days: int = 7) -> list[dict]:
    """Filter normalized transactions to only the last N days."""
    # Find the most recent date in the data to use as reference
    # (not today's date, since bank statement may not be up to the minute)
    latest_date = None
    for t in txns:
        d = t.get("date", "")
        if d and (latest_date is None or d > latest_date):
            latest_date = d

    if not latest_date:
        return []

    try:
        ref = datetime.strptime(latest_date, "%Y-%m-%d")
    except ValueError:
        return []

    cutoff = (ref - timedelta(days=days)).strftime("%Y-%m-%d")
    return [t for t in txns if t.get("date", "") > cutoff]


def _get_weekly_analysis(user_id: int) -> tuple[dict, dict, str]:
    """Get weekly + all-time analysis. Returns (weekly_analysis, alltime_analysis, source)."""
    if os.path.exists(CSV_PATH):
        csv_txns = parse_csv_transactions(CSV_PATH)
        if len(csv_txns) >= 10:
            all_normalized = normalize_csv_transactions(csv_txns)
            weekly_txns = _filter_transactions_by_days(all_normalized, days=7)
            alltime = analyze_transactions(all_normalized)
            weekly = analyze_transactions(weekly_txns) if weekly_txns else None
            return weekly, alltime, "csv"

    res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    if res.data and len(res.data) >= 10:
        weekly_txns = _filter_transactions_by_days(res.data, days=7)
        alltime = analyze_transactions(res.data)
        weekly = analyze_transactions(weekly_txns) if weekly_txns else None
        return weekly, alltime, "supabase"

    raise HTTPException(status_code=404, detail="No spending data available for this user")


@router.post("/simulate-transaction")
async def simulate_transaction(user_id: int, merchant: str, amount: float):
    """
    Simulate a transaction and send a fun contextual Telegram alert.

    Admin types any merchant name and amount — backend auto-classifies the category
    and builds the alert using the user's real bank statement data.
    """
    user = _get_user(user_id)
    telegram_id = user.get("phone", "")

    if not telegram_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="User does not have a Telegram ID (registered via web, not Telegram)",
        )

    # Auto-classify merchant
    category, spending_type = _classify_merchant(merchant)

    # Get real spending analysis
    analysis, source = _get_analysis(user_id)

    # Generate fun alert using Claude
    alert_text = await generate_spending_alert(
        user_id=user_id,
        merchant=merchant,
        amount=amount,
        analysis=analysis,
        category=category,
        source=source,
    )

    # Send via Telegram
    from app.services.telegram_bot import send_message
    sent = await send_message(int(telegram_id), alert_text)

    return {
        "success": sent,
        "notification": alert_text,
        "category": category,
        "spending_type": spending_type,
        "telegram_id": telegram_id,
    }


@router.post("/send-weekly-report")
async def send_weekly_report(user_id: int):
    """Generate and send a weekly spending summary via Telegram (last 7 days only)."""
    user = _get_user(user_id)
    telegram_id = user.get("phone", "")

    if not telegram_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="User does not have a Telegram ID",
        )

    weekly, alltime, source = _get_weekly_analysis(user_id)
    currency = "USD" if source == "csv" else "PKR"

    if not weekly or weekly.get("total_spending", 0) == 0:
        from app.services.telegram_bot import send_message
        await send_message(
            int(telegram_id),
            "*Weekly Report*\n\nNo spending recorded in the last 7 days. Quiet week!",
        )
        return {"success": True, "report": "No spending in last 7 days", "telegram_id": telegram_id}

    week_spent = weekly["total_spending"]
    week_income = weekly["total_income"]

    # Compare to weekly average from all-time data
    alltime_months = len(alltime.get("monthly_breakdown", [])) or 1
    avg_weekly_spend = round(alltime["total_spending"] / (alltime_months * 4.33))
    weekly_vs_avg = ((week_spent - avg_weekly_spend) / avg_weekly_spend * 100) if avg_weekly_spend > 0 else 0

    # Weekly category breakdown
    categories = []
    for cat_name in ["fixed", "discretionary", "watery"]:
        cat = weekly.get(cat_name, {})
        if cat.get("total", 0) > 0:
            categories.append(
                f"*{cat_name.title()}*: {currency} {cat['total']:,.0f} ({cat['percentage']:.0f}%)"
            )

    # Top merchants this week
    all_items = []
    for cat_name in ["fixed", "discretionary", "watery"]:
        all_items.extend(weekly.get(cat_name, {}).get("items", []))
    all_items.sort(key=lambda x: x["total"], reverse=True)
    top_merchants = "\n".join(
        f"  {i+1}. *{m['merchant']}* — {currency} {m['total']:,.0f}"
        for i, m in enumerate(all_items[:5])
    )

    # Trend indicator
    if weekly_vs_avg > 15:
        trend = f"*{weekly_vs_avg:+.0f}%* vs your weekly average — spending up!"
    elif weekly_vs_avg < -15:
        trend = f"*{weekly_vs_avg:+.0f}%* vs your weekly average — nice savings!"
    else:
        trend = f"*{weekly_vs_avg:+.0f}%* vs your weekly average — on track"

    # Contextual tip based on this week
    watery_total = weekly.get("watery", {}).get("total", 0)
    if watery_total > avg_weekly_spend * 0.3:
        tip = f"You spent {currency} {watery_total:,.0f} on reducible expenses this week. Small cuts here add up fast!"
    elif week_spent > avg_weekly_spend * 1.2:
        tip = "Heavier week than usual. Review your top merchants above — any surprises?"
    elif week_spent < avg_weekly_spend * 0.8:
        tip = "Great discipline this week! That extra savings could go straight into your BAQI investments."
    else:
        tip = "Steady week. Keep this pace and your BAQI surplus will grow nicely."

    report = (
        f"*Your Weekly BAQI Report*\n"
        f"_Last 7 days_\n\n"
        f"*Spent This Week:* {currency} {week_spent:,.0f}\n"
        f"*Weekly Average:* {currency} {avg_weekly_spend:,.0f}\n"
        f"{trend}\n\n"
        f"*This Week's Breakdown:*\n"
        + "\n".join(categories)
        + f"\n\n*Top Merchants This Week:*\n{top_merchants}\n\n"
        f"*Tip:* {tip}\n\n"
        f"_Your BAQI AI Weekly Digest_"
    )

    from app.services.telegram_bot import send_message
    sent = await send_message(int(telegram_id), report)

    return {
        "success": sent,
        "report": report,
        "telegram_id": telegram_id,
    }


@router.post("/send-notification")
async def send_custom_notification(user_id: int, message: str):
    """Send a custom notification message to a user via Telegram."""
    user = _get_user(user_id)
    telegram_id = user.get("phone", "")

    if not telegram_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="User does not have a Telegram ID",
        )

    from app.services.telegram_bot import send_message
    sent = await send_message(int(telegram_id), message)

    return {"success": sent, "telegram_id": telegram_id}


@router.post("/notify-investment")
async def notify_investment(user_id: int, total: float, expected_return: str, holdings: str):
    """Send a fun Telegram notification when a user executes an investment."""
    user = _get_user(user_id)
    telegram_id = user.get("phone", "")

    if not telegram_id.isdigit():
        return {"success": False, "detail": "No Telegram ID"}

    # Get real spending data for context
    try:
        analysis, source = _get_analysis(user_id)
        currency = "USD" if source == "csv" else "PKR"
        months = len(analysis.get("monthly_breakdown", [])) or 1
        savings_rate = analysis.get("savings_rate", 0)
        monthly_baqi = round(analysis.get("baqi_amount", 0) / months)
    except Exception:
        currency = "USD"
        savings_rate = 0
        monthly_baqi = 0

    prompt = f"""Generate a fun, celebratory Telegram notification (3-4 sentences, 2-3 emoji) about an investment.

The user just invested {currency} {total:,.0f} into: {holdings}
Expected annual return: {expected_return}%
Their savings rate: {savings_rate:.1f}%
Their monthly investable BAQI: {currency} {monthly_baqi:,}/month
All investments are 100% Shariah-compliant (Halal).

Be excited and celebratory! Mention the specific holdings. Use Telegram Markdown (*bold*)."""

    try:
        import anthropic
        from app.config import settings
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        notification = response.content[0].text
    except Exception as e:
        logger.error(f"Investment notification generation failed: {e}")
        notification = (
            f"🎉 *Investment Executed!*\n\n"
            f"You just invested *{currency} {total:,.0f}* into:\n{holdings}\n\n"
            f"Expected return: *{expected_return}%* annually. All 100% Halal! 🌙"
        )

    from app.services.telegram_bot import send_message
    sent = await send_message(int(telegram_id), notification)

    return {"success": sent, "notification": notification}


@router.get("/users")
async def get_telegram_users():
    """List all registered Telegram users (for admin dropdown)."""
    from app.services.telegram_bot import get_registered_telegram_users
    return get_registered_telegram_users()
