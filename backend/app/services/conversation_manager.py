"""Conversation state machine for BAQI AI (Telegram / generic chat)."""

import json
from app.database import supabase
from app.services.spending_analyzer import analyze_transactions
from app.services.synthetic_data import generate_synthetic_transactions

# In-memory conversation state (for hackathon; production would use Redis/DB)
conversations: dict[str, dict] = {}


def get_state(phone: str) -> dict:
    """Get or create conversation state for a phone number."""
    if phone not in conversations:
        conversations[phone] = {"state": "WELCOME", "user_id": None, "quiz_answers": [], "data": {}}
    return conversations[phone]


def process_message(phone: str, message: str) -> str:
    """
    Process incoming WhatsApp message and return response.
    Implements a state machine flow:
    WELCOME -> REGISTERED -> RISK_QUIZ -> ANALYZING -> RECOMMENDATION_READY
    """
    conv = get_state(phone)
    state = conv["state"]
    msg = message.strip().lower()

    if msg in ("reset", "start over", "restart"):
        conversations[phone] = {"state": "WELCOME", "user_id": None, "quiz_answers": [], "data": {}}
        return _welcome_message()

    if state == "WELCOME":
        return _handle_welcome(conv, phone, message)
    elif state == "ASK_NAME":
        return _handle_name(conv, phone, message)
    elif state == "REGISTERED":
        return _handle_registered(conv, phone, msg)
    elif state == "RISK_QUIZ":
        return _handle_quiz(conv, phone, msg)
    elif state == "QUIZ_DONE":
        return _handle_quiz_done(conv, phone, msg)
    elif state == "RECOMMENDATION_READY":
        return _handle_recommendation(conv, phone, msg)
    else:
        conv["state"] = "WELCOME"
        return _welcome_message()


def _welcome_message() -> str:
    return (
        "Assalam o Alaikum! \n\n"
        "I'm *BAQI AI* - your personal Islamic investment assistant.\n\n"
        "I analyze your spending, find your *baqi* (leftover money), "
        "and recommend Shariah-compliant investments on PSX.\n\n"
        "What's your name?"
    )


def _handle_welcome(conv: dict, phone: str, message: str) -> str:
    # If the first message looks like a name (not a number/command), treat it as one
    msg = message.strip()
    if msg and not msg.isdigit() and msg.lower() not in ("hi", "hello", "hey", "start", "help"):
        conv["state"] = "ASK_NAME"
        return _handle_name(conv, phone, msg)
    conv["state"] = "ASK_NAME"
    return _welcome_message()


def _handle_name(conv: dict, phone: str, name: str) -> str:
    name = name.strip().title()

    # Check if user already exists by phone
    clean_phone = phone.replace("whatsapp:", "").replace("telegram:", "")
    existing = supabase.table("users").select("*").eq("phone", clean_phone).execute()

    if existing.data:
        user = existing.data[0]
        conv["user_id"] = user["id"]
        conv["state"] = "REGISTERED"
        return (
            f"Welcome back, *{user['name']}*! \n\n"
            f"I already have your data on file.\n\n"
            f"Would you like to:\n"
            f"1. *Analyze* - View your spending analysis\n"
            f"2. *Quiz* - Retake the risk assessment\n"
            f"3. *Recommend* - Get AI investment recommendations\n\n"
            f"Reply with a number or keyword."
        )

    # Create new user
    result = supabase.table("users").insert({
        "name": name,
        "phone": clean_phone,
        "age": 28,
        "monthly_income": 150000,
        "halal_preference": True,
    }).execute()

    if not result.data:
        return "Sorry, something went wrong. Please try again."

    user = result.data[0]
    conv["user_id"] = user["id"]

    # Generate synthetic data for demo
    txns = generate_synthetic_transactions(user["id"], months=6, income=150000)
    supabase.table("transactions").insert(txns).execute()

    conv["state"] = "REGISTERED"
    return (
        f"Nice to meet you, *{name}*! \n\n"
        f"I've set up your account and loaded 6 months of sample transaction data.\n\n"
        f"Would you like to:\n"
        f"1. *Analyze* - View your spending breakdown\n"
        f"2. *Quiz* - Take the risk assessment quiz\n"
        f"3. *Recommend* - Get AI investment recommendations\n\n"
        f"Reply with a number or keyword."
    )


def _handle_registered(conv: dict, phone: str, msg: str) -> str:
    user_id = conv["user_id"]

    if msg in ("1", "analyze", "analysis", "spending"):
        # Run spending analysis
        txn_result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("date")
            .execute()
        )
        analysis = analyze_transactions(txn_result.data or [])

        conv["data"]["analysis"] = analysis
        baqi = analysis["baqi_amount"]
        monthly_baqi = round(baqi / 6, 0)

        return (
            f"Your Spending Analysis\n\n"
            f"Total Income: PKR {analysis['total_income']:,.0f}\n"
            f"Total Spending: PKR {analysis['total_spending']:,.0f}\n"
            f"Savings Rate: {analysis['savings_rate']:.1f}%\n\n"
            f"*Breakdown:*\n"
            f"Fixed: {analysis['fixed']['percentage']:.1f}%\n"
            f"Discretionary: {analysis['discretionary']['percentage']:.1f}%\n"
            f"Watery (reducible): {analysis['watery']['percentage']:.1f}%\n\n"
            f"Your BAQI (investable surplus): PKR {monthly_baqi:,.0f}/month\n\n"
            f"Reply:\n"
            f"2. *Quiz* - Take risk assessment\n"
            f"3. *Recommend* - Get AI recommendations"
        )

    elif msg in ("2", "quiz", "risk"):
        conv["state"] = "RISK_QUIZ"
        conv["quiz_answers"] = []
        return _quiz_question(0)

    elif msg in ("3", "recommend", "recommendation", "invest"):
        conv["state"] = "RECOMMENDATION_READY"
        return (
            "🤖 To generate your personalized AI recommendation, "
            "please use our web dashboard or API.\n\n"
            f"POST /api/recommendations/generate with user_id: {user_id}\n\n"
            "The AI pipeline takes 30-90 seconds and uses 6 specialized agents:\n"
            "1. Spending Analyzer\n"
            "2. Risk Profiler\n"
            "3. Market Sentiment Analyst\n"
            "4. Halal Compliance Officer\n"
            "5. PSX Investment Strategist\n\n"
            "Reply *menu* to go back."
        )

    return (
        "I didn't catch that. Reply with:\n"
        "1. *Analyze* - Spending analysis\n"
        "2. *Quiz* - Risk assessment\n"
        "3. *Recommend* - AI recommendations"
    )


RISK_QUESTIONS = [
    {
        "question": "How would you react if your investment lost 20% in one month?",
        "options": ["Sell immediately", "Worry a lot", "Wait and watch", "Buy more at lower price", "Not concerned at all"],
    },
    {
        "question": "What's your investment time horizon?",
        "options": ["Less than 1 year", "1-2 years", "3-5 years", "5-10 years", "10+ years"],
    },
    {
        "question": "What's more important to you?",
        "options": ["Protect my capital", "Steady income", "Balance of growth and safety", "Long-term growth", "Maximum returns"],
    },
    {
        "question": "Have you invested in stocks before?",
        "options": ["Never", "Heard about it", "Tried once", "Some experience", "Regular investor"],
    },
    {
        "question": "Can you afford to lose this investment money?",
        "options": ["Absolutely not", "Would be very difficult", "Would be uncomfortable", "Could manage", "Yes, it's extra money"],
    },
]


def _quiz_question(index: int) -> str:
    q = RISK_QUESTIONS[index]
    options = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
    return f"Question {index + 1}/5\n\n{q['question']}\n\n{options}\n\nReply with a number (1-5)."


def _handle_quiz(conv: dict, phone: str, msg: str) -> str:
    try:
        answer = int(msg)
        if not 1 <= answer <= 5:
            raise ValueError()
    except ValueError:
        return "Please reply with a number from 1 to 5."

    conv["quiz_answers"].append(answer)
    q_index = len(conv["quiz_answers"])

    if q_index < 5:
        return _quiz_question(q_index)

    # Quiz complete — calculate risk profile
    answers = conv["quiz_answers"]
    raw_score = sum(answers) / len(answers)

    # Age adjustment (fetch from DB)
    user = supabase.table("users").select("age").eq("id", conv["user_id"]).execute()
    age = user.data[0].get("age", 30) if user.data else 30
    age_factor = max(0, (65 - age) / 65)
    adjusted_score = raw_score * 0.7 + age_factor * 5 * 0.3

    if adjusted_score <= 2.0:
        profile = "conservative"
        emoji = "[Safe]"
    elif adjusted_score <= 3.5:
        profile = "moderate"
        emoji = "[Balanced]"
    else:
        profile = "aggressive"
        emoji = "[Growth]"

    # Save to DB
    supabase.table("users").update({"risk_profile": profile}).eq("id", conv["user_id"]).execute()

    conv["state"] = "QUIZ_DONE"
    conv["data"]["risk_profile"] = profile
    conv["data"]["risk_score"] = round(adjusted_score, 1)

    return (
        f"Risk Assessment Complete!\n\n"
        f"{emoji} Your profile: *{profile.upper()}*\n"
        f"Risk score: {adjusted_score:.1f}/5.0\n\n"
        f"This means your recommended allocation is:\n"
        + _allocation_text(profile) +
        f"\n\nReply:\n"
        f"3. *Recommend* - Get AI investment picks\n"
        f"*Menu* - Back to main menu"
    )


def _allocation_text(profile: str) -> str:
    allocs = {
        "conservative": "• 20% Equities\n• 60% Fixed Income\n• 20% Mutual Funds",
        "moderate": "• 40% Equities\n• 30% Fixed Income\n• 30% Mutual Funds",
        "aggressive": "• 60% Equities\n• 10% Fixed Income\n• 30% Mutual Funds",
    }
    return allocs.get(profile, allocs["moderate"])


def _handle_quiz_done(conv: dict, phone: str, msg: str) -> str:
    if msg in ("3", "recommend", "recommendation", "invest"):
        conv["state"] = "RECOMMENDATION_READY"
        return (
            "🤖 To generate your personalized AI recommendation, "
            "use our web dashboard or the API endpoint.\n\n"
            f"Your user ID is: *{conv['user_id']}*\n\n"
            "Reply *menu* to go back."
        )
    elif msg in ("menu", "back"):
        conv["state"] = "REGISTERED"
        return (
            "What would you like to do?\n"
            "1. *Analyze* - Spending analysis\n"
            "2. *Quiz* - Retake risk assessment\n"
            "3. *Recommend* - AI recommendations"
        )
    return "Reply *3* for recommendations or *menu* to go back."


def _handle_recommendation(conv: dict, phone: str, msg: str) -> str:
    if msg in ("menu", "back"):
        conv["state"] = "REGISTERED"
        return (
            "What would you like to do?\n"
            "1. *Analyze* - Spending analysis\n"
            "2. *Quiz* - Risk assessment\n"
            "3. *Recommend* - AI recommendations"
        )
    return (
        f"Your user ID is: *{conv['user_id']}*\n\n"
        "Use the web dashboard for the full AI recommendation experience.\n\n"
        "Reply *menu* to go back."
    )
