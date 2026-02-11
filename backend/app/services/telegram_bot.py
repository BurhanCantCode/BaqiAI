"""Telegram Bot service for BAQI AI - spending notifications & account queries."""

import asyncio
import logging
from typing import Optional

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.config import settings
from app.database import supabase
from app.services.spending_analyzer import analyze_transactions, normalize_csv_transactions
from app.services.insights_engine import parse_csv_transactions
from app.services.conversation_manager import process_message

import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_app: Optional[Application] = None
_bot_username: Optional[str] = None
_running = False

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "transactions1 cleaned2.csv",
)


def bot_status() -> dict:
    """Return current bot status for the frontend."""
    return {
        "running": _running,
        "bot_username": _bot_username,
        "bot_link": f"https://t.me/{_bot_username}" if _bot_username else None,
    }


# ---------------------------------------------------------------------------
# Helpers — data access (reuses existing services)
# ---------------------------------------------------------------------------

def _get_user_by_telegram(telegram_id: int) -> Optional[dict]:
    """Look up a BAQI user by their Telegram ID."""
    res = supabase.table("users").select("*").eq("phone", str(telegram_id)).execute()
    return res.data[0] if res.data else None


def _register_user(telegram_id: int, name: str) -> dict:
    """Register a new user using their Telegram ID as identifier."""
    from app.services.synthetic_data import generate_synthetic_transactions

    result = supabase.table("users").insert({
        "name": name,
        "phone": str(telegram_id),
        "age": 28,
        "monthly_income": 150000,
        "halal_preference": True,
    }).execute()

    if not result.data:
        raise RuntimeError("Failed to create user")

    user = result.data[0]
    # Generate sample data for demo
    txns = generate_synthetic_transactions(user["id"], months=6, income=150000)
    supabase.table("transactions").insert(txns).execute()
    return user


def _get_spending_analysis(user_id: int) -> Optional[dict]:
    """Get spending analysis — tries CSV first, then Supabase."""
    # Try CSV
    if os.path.exists(CSV_PATH):
        csv_txns = parse_csv_transactions(CSV_PATH)
        if len(csv_txns) >= 10:
            normalized = normalize_csv_transactions(csv_txns)
            analysis = analyze_transactions(normalized)
            analysis["source"] = "csv"
            analysis["currency"] = "USD"
            return analysis

    # Fallback to Supabase
    txn_res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    if txn_res.data and len(txn_res.data) >= 10:
        analysis = analyze_transactions(txn_res.data)
        analysis["source"] = "supabase"
        analysis["currency"] = "PKR"
        return analysis

    return None


def _format_spending_alerts(analysis: dict) -> str:
    """Generate overspending alerts from analysis data."""
    alerts = []
    currency = analysis.get("currency", "PKR")
    months = len(analysis.get("monthly_breakdown", [])) or 1

    # Check watery spending (reducible expenses)
    watery = analysis.get("watery", {})
    watery_pct = watery.get("percentage", 0)
    if watery_pct > 30:
        monthly_watery = round(watery.get("total", 0) / months)
        alerts.append(
            f"!! High discretionary spending! ~{currency} {monthly_watery:,}/month "
            f"on reducible expenses ({watery_pct:.1f}% of spending)."
        )

    # Check top watery merchants — show monthly averages
    watery_items = watery.get("items", [])
    for item in watery_items[:3]:
        merchant = item["merchant"]
        monthly_avg = round(item["total"] / months)
        if monthly_avg > 50:  # Significant monthly amount
            alerts.append(
                f"~*{currency} {monthly_avg:,}/month* on *{merchant}*"
            )

    # Savings rate warning
    savings_rate = analysis.get("savings_rate", 0)
    if savings_rate < 10:
        alerts.append(
            f"Low savings rate: {savings_rate:.1f}% - "
            f"aim for at least 20% to build your investment surplus."
        )
    elif savings_rate > 30:
        alerts.append(
            f"Great savings rate: {savings_rate:.1f}% - "
            f"you're in a strong position to invest!"
        )

    return "\n\n".join(alerts) if alerts else "Your spending looks healthy! No alerts."


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome & register."""
    tg_user = update.effective_user
    user = _get_user_by_telegram(tg_user.id)

    if user:
        await update.message.reply_text(
            f"Welcome back, *{user['name']}*! \n\n"
            f"I'm *BAQI AI* - your personal Islamic investment assistant.\n\n"
            f"Use these commands:\n"
            f"/balance - Income, expenses & investable surplus\n"
            f"/spending - Category breakdown with alerts\n"
            f"/insights - AI-powered financial tips\n"
            f"/help - Show all commands",
            parse_mode="Markdown",
        )
    else:
        # Auto-register with Telegram name
        name = tg_user.first_name or "User"
        if tg_user.last_name:
            name += f" {tg_user.last_name}"

        try:
            user = _register_user(tg_user.id, name)
            await update.message.reply_text(
                f"Assalam o Alaikum, *{name}*! \n\n"
                f"I'm *BAQI AI* - your personal Islamic investment assistant.\n\n"
                f"I analyze your spending, find your *baqi* (leftover money), "
                f"and recommend Shariah-compliant investments.\n\n"
                f"Account created with 6 months of sample data!\n\n"
                f"Try these commands:\n"
                f"/balance - Income, expenses & investable surplus\n"
                f"/spending - Category breakdown with alerts\n"
                f"/insights - AI-powered financial tips\n"
                f"/help - Show all commands",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            await update.message.reply_text(
                "Sorry, something went wrong during registration. Please try again with /start."
            )


async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance — show income, expenses, investable surplus."""
    user = _get_user_by_telegram(update.effective_user.id)
    if not user:
        await update.message.reply_text("Please /start first to set up your account.")
        return

    analysis = _get_spending_analysis(user["id"])
    if not analysis:
        await update.message.reply_text(
            "No transaction data found yet. Please upload data via the web dashboard."
        )
        return

    currency = analysis.get("currency", "PKR")
    months = len(analysis.get("monthly_breakdown", [])) or 1
    monthly_income = round(analysis["total_income"] / months)
    monthly_spending = round(analysis["total_spending"] / months)
    monthly_baqi = round(analysis["baqi_amount"] / months)
    monthly_watery_potential = round(analysis["watery_savings_potential"] / months)

    await update.message.reply_text(
        f"💰 *Your Monthly Financial Summary*\n\n"
        f"📥 Avg Monthly Income: {currency} {monthly_income:,}\n"
        f"📤 Avg Monthly Spending: {currency} {monthly_spending:,}\n"
        f"📈 Savings Rate: {analysis['savings_rate']:.1f}%\n\n"
        f"✅ *Your BAQI (investable surplus): {currency} {monthly_baqi:,}/month*\n\n"
        f"💡 Potential extra savings: {currency} {monthly_watery_potential:,}/month "
        f"by reducing discretionary spending by 50%",
        parse_mode="Markdown",
    )


async def cmd_spending(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /spending — category breakdown + alerts."""
    user = _get_user_by_telegram(update.effective_user.id)
    if not user:
        await update.message.reply_text("Please /start first to set up your account.")
        return

    analysis = _get_spending_analysis(user["id"])
    if not analysis:
        await update.message.reply_text(
            "No transaction data found yet. Please upload data via the web dashboard."
        )
        return

    currency = analysis.get("currency", "PKR")
    months = len(analysis.get("monthly_breakdown", [])) or 1
    alerts = _format_spending_alerts(analysis)

    # Top merchants per category — show monthly averages
    def _top(items, n=3):
        return "\n".join(
            f"  • {it['merchant']}: ~{currency} {round(it['total'] / months):,}/mo"
            for it in items[:n]
        ) or "  (none)"

    def _monthly(cat):
        return round(analysis[cat]["total"] / months)

    await update.message.reply_text(
        f"📊 *Monthly Spending Breakdown*\n\n"
        f"🏠 *Fixed:* {analysis['fixed']['percentage']:.1f}% (~{currency} {_monthly('fixed'):,}/mo)\n"
        f"{_top(analysis['fixed']['items'])}\n\n"
        f"🛒 *Discretionary:* {analysis['discretionary']['percentage']:.1f}% (~{currency} {_monthly('discretionary'):,}/mo)\n"
        f"{_top(analysis['discretionary']['items'])}\n\n"
        f"💧 *Watery (reducible):* {analysis['watery']['percentage']:.1f}% (~{currency} {_monthly('watery'):,}/mo)\n"
        f"{_top(analysis['watery']['items'])}\n\n"
        f"{'─' * 24}\n"
        f"🔔 *Spending Alerts*\n\n{alerts}",
        parse_mode="Markdown",
    )


async def cmd_insights(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /insights — quick AI tips based on spending."""
    user = _get_user_by_telegram(update.effective_user.id)
    if not user:
        await update.message.reply_text("Please /start first to set up your account.")
        return

    analysis = _get_spending_analysis(user["id"])
    if not analysis:
        await update.message.reply_text(
            "No transaction data found yet. Please upload data via the web dashboard."
        )
        return

    currency = analysis.get("currency", "PKR")
    savings_rate = analysis["savings_rate"]
    watery_pct = analysis["watery"]["percentage"]
    monthly_baqi = round(analysis["baqi_amount"] / max(len(analysis.get("monthly_breakdown", [])), 1), 0)

    # Generate persona
    if savings_rate >= 30:
        persona = "The Disciplined Saver"
        tip = "You're saving well! Consider diversifying into Shariah-compliant mutual funds."
    elif savings_rate >= 15:
        persona = "The Balanced Spender"
        tip = "Good balance! Try reducing watery expenses by 20% to boost your investment potential."
    else:
        persona = "The Active Spender"
        tip = "Focus on cutting reducible expenses - even a 30% reduction can unlock significant investment capital."

    # Monthly trend
    monthly = analysis.get("monthly_breakdown", [])
    trend = ""
    if len(monthly) >= 2:
        last_two = monthly[-2:]
        if last_two[1]["spending"] > last_two[0]["spending"]:
            diff = last_two[1]["spending"] - last_two[0]["spending"]
            trend = f"\n📈 Spending *increased* by {currency} {diff:,.0f} vs last month."
        else:
            diff = last_two[0]["spending"] - last_two[1]["spending"]
            trend = f"\n📉 Spending *decreased* by {currency} {diff:,.0f} vs last month. Keep it up!"

    await update.message.reply_text(
        f"🧠 *AI Financial Insights*\n\n"
        f"{persona}\n"
        f"💡 {tip}\n\n"
        f"📊 *Key Numbers:*\n"
        f"  • Savings rate: {savings_rate:.1f}%\n"
        f"  • Reducible spending: {watery_pct:.1f}%\n"
        f"  • Monthly investable: {currency} {monthly_baqi:,.0f}\n"
        f"{trend}\n\n"
        f"💎 For full AI-powered recommendations with 6 specialized agents, "
        f"visit the BAQI AI web dashboard!",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — list commands."""
    await update.message.reply_text(
        "BAQI AI Commands\n\n"
        "/start - Welcome & account setup\n"
        "/balance - Income, expenses & investable surplus\n"
        "/spending - Category breakdown + overspending alerts\n"
        "/insights - AI-powered financial tips & persona\n"
        "/help - Show this message\n\n"
        "You can also type any financial question and I'll try to help!\n\n"
        "Visit the web dashboard for full analytics, AI recommendations, "
        "and investment execution.",
        parse_mode="Markdown",
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages through the AI chat engine."""
    tg_user = update.effective_user
    user = _get_user_by_telegram(tg_user.id)

    if not user:
        await update.message.reply_text(
            "Please send /start first to set up your account!"
        )
        return

    # Show typing indicator while Claude thinks
    await update.message.chat.send_action("typing")

    try:
        from app.services.chat_engine import process_chat
        response = await process_chat(tg_user.id, update.message.text)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Chat engine error: {e}")
        await update.message.reply_text(
            "Oops, my brain glitched! Try again or use /help for commands."
        )


# ---------------------------------------------------------------------------
# Bot lifecycle
# ---------------------------------------------------------------------------

async def start_bot() -> None:
    """Start the Telegram bot (non-blocking, runs in background)."""
    global _app, _bot_username, _running

    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot will not start.")
        return

    # Use a longer timeout for bot API calls to handle slow network
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    
    _app = Application.builder().token(token).request(request).build()

    # Register handlers
    _app.add_handler(CommandHandler("start", cmd_start))
    _app.add_handler(CommandHandler("balance", cmd_balance))
    _app.add_handler(CommandHandler("spending", cmd_spending))
    _app.add_handler(CommandHandler("insights", cmd_insights))
    _app.add_handler(CommandHandler("help", cmd_help))
    _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    try:
        # Initialize and start polling
        await _app.initialize()
        await _app.start()
        await _app.updater.start_polling(drop_pending_updates=True)

        # Set bot commands for Telegram menu (non-critical)
        try:
            await _app.bot.set_my_commands([
                BotCommand("start", "Welcome & account setup"),
                BotCommand("balance", "Income, expenses & investable surplus"),
                BotCommand("spending", "Category breakdown + alerts"),
                BotCommand("insights", "AI financial tips & persona"),
                BotCommand("help", "Show all commands"),
            ])
        except Exception:
            pass  # Non-critical, menu commands just won't show

        # Get bot info
        bot_info = await _app.bot.get_me()
        _bot_username = bot_info.username
        _running = True
        logger.info(f"Telegram bot started: @{_bot_username}")
        print(f"Telegram bot started: @{_bot_username} -- https://t.me/{_bot_username}")
    except Exception as e:
        logger.error(f"Telegram bot failed to start: {e}")
        _bot_username = None
        _running = False
        _app = None
        print(f"Telegram bot could not start: {e}")


async def stop_bot() -> None:
    """Stop the Telegram bot gracefully."""
    global _app, _running

    if _app and _running:
        try:
            _running = False
            await _app.updater.stop()
            await _app.stop()
            await _app.shutdown()
            logger.info("Telegram bot stopped.")
            print("Telegram bot stopped.")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")


# ---------------------------------------------------------------------------
# Public helpers — used by admin endpoints
# ---------------------------------------------------------------------------

async def send_message(telegram_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a proactive message to a user by Telegram ID. Used by admin endpoints."""
    if not _app or not _running:
        logger.warning("Cannot send message — bot not running")
        return False
    try:
        await _app.bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode=parse_mode,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send message to {telegram_id}: {e}")
        return False


def get_registered_telegram_users() -> list[dict]:
    """Get all users registered via Telegram (phone field stores telegram_id)."""
    res = supabase.table("users").select("id, name, phone").execute()
    return [
        {"id": u["id"], "name": u["name"], "telegram_id": u["phone"]}
        for u in (res.data or [])
        if u.get("phone", "").isdigit()
    ]
