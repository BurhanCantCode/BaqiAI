"""Rule-based spending categorization and baqi (leftover) calculation."""

from collections import defaultdict

from app.utils.constants import FIXED_CATEGORIES, DISCRETIONARY_CATEGORIES, WATERY_CATEGORIES


def analyze_transactions(transactions: list[dict]) -> dict:
    """
    Analyze a list of transactions and return spending breakdown.

    Each transaction dict must have: amount, category, spending_type, merchant, date.
    """
    total_income = 0.0
    total_spending = 0.0

    fixed_items = []
    discretionary_items = []
    watery_items = []

    fixed_total = 0.0
    discretionary_total = 0.0
    watery_total = 0.0

    monthly_data = defaultdict(lambda: {"income": 0.0, "spending": 0.0})

    for txn in transactions:
        amount = float(txn["amount"])
        category = txn.get("category", "")
        spending_type = txn.get("spending_type", "")
        month_key = txn["date"][:7]  # YYYY-MM

        if category == "salary" or spending_type == "income":
            total_income += amount
            monthly_data[month_key]["income"] += amount
            continue

        total_spending += amount
        monthly_data[month_key]["spending"] += amount

        item = {
            "merchant": txn.get("merchant", ""),
            "amount": amount,
            "category": category,
            "date": txn["date"],
        }

        if category in FIXED_CATEGORIES or spending_type == "fixed":
            fixed_items.append(item)
            fixed_total += amount
        elif category in DISCRETIONARY_CATEGORIES or spending_type == "discretionary":
            discretionary_items.append(item)
            discretionary_total += amount
        elif category in WATERY_CATEGORIES or spending_type == "watery":
            watery_items.append(item)
            watery_total += amount
        else:
            # Default unrecognized to watery
            watery_items.append(item)
            watery_total += amount

    baqi_amount = total_income - total_spending
    savings_rate = (baqi_amount / total_income * 100) if total_income > 0 else 0
    watery_savings_potential = watery_total * 0.5
    recommended_investment = baqi_amount + watery_savings_potential

    # Build monthly breakdown sorted by month
    monthly_breakdown = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        monthly_breakdown.append({
            "month": month_key,
            "income": round(data["income"], 2),
            "spending": round(data["spending"], 2),
            "surplus": round(data["income"] - data["spending"], 2),
        })

    def _pct(val: float) -> float:
        return round(val / total_spending * 100, 1) if total_spending > 0 else 0

    return {
        "total_income": round(total_income, 2),
        "total_spending": round(total_spending, 2),
        "fixed": {
            "total": round(fixed_total, 2),
            "percentage": _pct(fixed_total),
            "items": _top_merchants(fixed_items),
        },
        "discretionary": {
            "total": round(discretionary_total, 2),
            "percentage": _pct(discretionary_total),
            "items": _top_merchants(discretionary_items),
        },
        "watery": {
            "total": round(watery_total, 2),
            "percentage": _pct(watery_total),
            "items": _top_merchants(watery_items),
        },
        "baqi_amount": round(baqi_amount, 2),
        "savings_rate": round(savings_rate, 1),
        "watery_savings_potential": round(watery_savings_potential, 2),
        "recommended_investment": round(recommended_investment, 2),
        "monthly_breakdown": monthly_breakdown,
    }


def _top_merchants(items: list[dict], limit: int = 5) -> list[dict]:
    """Aggregate items by merchant and return top spenders."""
    merchant_totals = defaultdict(float)
    for item in items:
        merchant_totals[item["merchant"]] += item["amount"]

    sorted_merchants = sorted(
        merchant_totals.items(), key=lambda x: x[1], reverse=True
    )
    return [
        {"merchant": name, "total": round(total, 2)}
        for name, total in sorted_merchants[:limit]
    ]
