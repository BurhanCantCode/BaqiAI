"""Data exhaust extraction and AI-powered insights generation."""

import json
import math
from collections import defaultdict
from datetime import datetime

import anthropic

from app.config import settings
from app.services.spending_analyzer import analyze_transactions


def extract_data_exhaust(transactions: list[dict]) -> dict:
    """
    Extract 8 behavioral signals from raw transaction data.
    Pure Python — no pandas needed.
    """
    # Filter out income transactions
    spending_txns = [
        t for t in transactions
        if t.get("category") != "salary" and t.get("spending_type") != "income"
    ]

    return {
        "day_of_week_pattern": _day_of_week_pattern(spending_txns),
        "merchant_loyalty": _merchant_loyalty(spending_txns),
        "amount_variance": _amount_variance_by_category(spending_txns),
        "spending_velocity": _spending_velocity(spending_txns),
        "category_trends": _category_trends(spending_txns),
        "outlier_transactions": _outlier_transactions(spending_txns),
        "subscription_detection": _subscription_detection(spending_txns),
        "watery_baqi_correlation": _watery_baqi_correlation(transactions),
    }


def _day_of_week_pattern(txns: list[dict]) -> dict:
    """Spending totals by day of week."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    totals = defaultdict(float)
    counts = defaultdict(int)
    for t in txns:
        try:
            dt = datetime.strptime(t["date"][:10], "%Y-%m-%d")
            day_name = days[dt.weekday()]
            totals[day_name] += float(t["amount"])
            counts[day_name] += 1
        except (ValueError, KeyError):
            continue
    return {
        "totals": {d: round(totals.get(d, 0), 0) for d in days},
        "counts": {d: counts.get(d, 0) for d in days},
        "peak_day": max(totals, key=totals.get) if totals else "N/A",
    }


def _merchant_loyalty(txns: list[dict]) -> list[dict]:
    """Top merchants by visit frequency + total spend."""
    freq = defaultdict(int)
    totals = defaultdict(float)
    for t in txns:
        m = t.get("merchant", "Unknown")
        freq[m] += 1
        totals[m] += float(t["amount"])
    merchants = sorted(
        [{"merchant": m, "visits": freq[m], "total": round(totals[m], 0)}
         for m in freq],
        key=lambda x: x["visits"],
        reverse=True,
    )
    return merchants[:10]


def _amount_variance_by_category(txns: list[dict]) -> dict:
    """Std deviation of transaction amounts per category — high = impulse spending."""
    by_cat = defaultdict(list)
    for t in txns:
        cat = t.get("category", "other")
        by_cat[cat].append(float(t["amount"]))
    result = {}
    for cat, amounts in by_cat.items():
        if len(amounts) < 2:
            continue
        mean = sum(amounts) / len(amounts)
        variance = sum((a - mean) ** 2 for a in amounts) / (len(amounts) - 1)
        result[cat] = {
            "std_dev": round(math.sqrt(variance), 0),
            "mean": round(mean, 0),
            "count": len(amounts),
        }
    return result


def _spending_velocity(txns: list[dict]) -> list[dict]:
    """Month-over-month spending change percentage."""
    monthly = defaultdict(float)
    for t in txns:
        month_key = t["date"][:7]
        monthly[month_key] += float(t["amount"])
    months = sorted(monthly.keys())
    velocity = []
    for i in range(1, len(months)):
        prev = monthly[months[i - 1]]
        curr = monthly[months[i]]
        change = ((curr - prev) / prev * 100) if prev > 0 else 0
        velocity.append({
            "period": f"{months[i-1]} → {months[i]}",
            "previous": round(prev, 0),
            "current": round(curr, 0),
            "change_pct": round(change, 1),
        })
    return velocity


def _category_trends(txns: list[dict]) -> dict:
    """Direction of spending per category over last 3 months vs first 3 months."""
    by_cat_month = defaultdict(lambda: defaultdict(float))
    for t in txns:
        cat = t.get("category", "other")
        month_key = t["date"][:7]
        by_cat_month[cat][month_key] += float(t["amount"])
    result = {}
    for cat, months_data in by_cat_month.items():
        months = sorted(months_data.keys())
        if len(months) < 4:
            continue
        mid = len(months) // 2
        first_half_avg = sum(months_data[m] for m in months[:mid]) / mid
        second_half_avg = sum(months_data[m] for m in months[mid:]) / (len(months) - mid)
        change = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
        if change > 10:
            direction = "increasing"
        elif change < -10:
            direction = "decreasing"
        else:
            direction = "stable"
        result[cat] = {
            "direction": direction,
            "change_pct": round(change, 1),
            "first_half_avg": round(first_half_avg, 0),
            "second_half_avg": round(second_half_avg, 0),
        }
    return result


def _outlier_transactions(txns: list[dict]) -> list[dict]:
    """Transactions > 2 std devs from their category mean."""
    by_cat = defaultdict(list)
    for t in txns:
        cat = t.get("category", "other")
        by_cat[cat].append(t)
    outliers = []
    for cat, items in by_cat.items():
        amounts = [float(t["amount"]) for t in items]
        if len(amounts) < 3:
            continue
        mean = sum(amounts) / len(amounts)
        std_dev = math.sqrt(sum((a - mean) ** 2 for a in amounts) / len(amounts))
        if std_dev == 0:
            continue
        threshold = mean + 2 * std_dev
        for t in items:
            amt = float(t["amount"])
            if amt > threshold:
                outliers.append({
                    "merchant": t.get("merchant", "Unknown"),
                    "amount": round(amt, 0),
                    "category": cat,
                    "date": t["date"],
                    "category_avg": round(mean, 0),
                    "deviation": round((amt - mean) / std_dev, 1),
                })
    return sorted(outliers, key=lambda x: x["deviation"], reverse=True)[:5]


def _subscription_detection(txns: list[dict]) -> list[dict]:
    """Detect recurring payments: same merchant with similar amount across months."""
    merchant_monthly = defaultdict(lambda: defaultdict(list))
    for t in txns:
        m = t.get("merchant", "Unknown")
        month_key = t["date"][:7]
        merchant_monthly[m][month_key].append(float(t["amount"]))
    subscriptions = []
    for merchant, months_data in merchant_monthly.items():
        if len(months_data) < 3:
            continue
        # Take one amount per month (the first or only)
        monthly_amounts = [amounts[0] for amounts in months_data.values()]
        mean = sum(monthly_amounts) / len(monthly_amounts)
        if mean == 0:
            continue
        # Check consistency: all amounts within 20% of mean
        consistent = all(abs(a - mean) / mean < 0.2 for a in monthly_amounts)
        if consistent:
            subscriptions.append({
                "merchant": merchant,
                "avg_amount": round(mean, 0),
                "months_detected": len(months_data),
                "monthly_cost": round(mean, 0),
                "annual_cost": round(mean * 12, 0),
            })
    return sorted(subscriptions, key=lambda x: x["annual_cost"], reverse=True)


def _watery_baqi_correlation(all_txns: list[dict]) -> dict:
    """Calculate how much extra BAQI if watery spending is reduced by 30%."""
    total_income = sum(
        float(t["amount"]) for t in all_txns
        if t.get("category") == "salary" or t.get("spending_type") == "income"
    )
    watery_total = sum(
        float(t["amount"]) for t in all_txns
        if t.get("spending_type") == "watery"
    )
    total_spending = sum(
        float(t["amount"]) for t in all_txns
        if t.get("category") != "salary" and t.get("spending_type") != "income"
    )
    current_baqi = total_income - total_spending
    potential_savings = watery_total * 0.3
    return {
        "current_watery_total": round(watery_total, 0),
        "potential_30pct_savings": round(potential_savings, 0),
        "current_baqi": round(current_baqi, 0),
        "projected_baqi": round(current_baqi + potential_savings, 0),
        "baqi_increase_pct": round(
            (potential_savings / current_baqi * 100) if current_baqi > 0 else 0, 1
        ),
    }


async def generate_insights(user_id: int, transactions: list[dict]) -> dict:
    """
    Generate AI-powered insights from transaction data exhaust.
    Uses direct Anthropic API call (fast, ~3-5s) — CrewAI pipeline remains separate for investments.
    """
    analysis = analyze_transactions(transactions)
    data_exhaust = extract_data_exhaust(transactions)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = f"""You are BAQI AI, an expert financial behavior analyst for Pakistani banking customers.

Analyze this user's DATA EXHAUST — the hidden behavioral patterns in their transaction data that they can't see themselves.

## Raw Data Exhaust Signals
{json.dumps(data_exhaust, indent=2, default=str)}

## Spending Summary
- Total Income (6mo): PKR {analysis['total_income']:,.0f}
- Total Spending: PKR {analysis['total_spending']:,.0f}
- BAQI (surplus): PKR {analysis['baqi_amount']:,.0f}
- Savings Rate: {analysis['savings_rate']}%
- Watery spending: PKR {analysis['watery']['total']:,.0f} ({analysis['watery']['percentage']:.1f}%)

## Instructions
Generate exactly 5 insights. Each must:
1. Reveal a SPECIFIC pattern the user doesn't know about (use exact PKR amounts, merchant names, days from the data above)
2. Explain WHY it matters financially
3. Give ONE concrete action with estimated PKR impact
4. Be categorized as: "behavioral", "saving_opportunity", "anomaly", "trend", or "optimization"
5. Have a severity: "info", "warning", or "opportunity"

Return ONLY a valid JSON array (no markdown, no explanation):
[{{"title": "short title", "description": "2-3 sentence explanation with specific numbers", "action": "one concrete step", "category": "behavioral|saving_opportunity|anomaly|trend|optimization", "severity": "info|warning|opportunity", "impact_pkr": number_or_null}}]"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse JSON from response — handle possible markdown wrapping
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    insights = json.loads(raw)

    return {
        "user_id": user_id,
        "insights": insights,
        "data_exhaust": data_exhaust,
        "generated_at": datetime.utcnow().isoformat(),
    }
