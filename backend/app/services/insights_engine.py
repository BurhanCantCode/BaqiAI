"""Data exhaust extraction and AI-powered behavioral insights generation.

Works with both:
- Real CSV data (date, name, amount) — from uploaded bank statements
- Synthetic Supabase data (date, merchant, amount, category, spending_type)
"""

import csv
import io
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import anthropic

from app.config import settings


# ---------------------------------------------------------------------------
# CSV Parsing — turn raw bank CSV into normalised transaction dicts
# ---------------------------------------------------------------------------

def parse_csv_transactions(csv_path: str) -> list[dict]:
    """Parse the real bank CSV (date, name, amount) into normalised dicts."""
    txns = []
    path = Path(csv_path)
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))

    header = None
    for row in reader:
        if not row or not row[0].strip():
            continue
        # Detect header row
        if row[0].strip().lower() in ("date", "transactions1"):
            header = row
            continue
        if header is None:
            # Skip rows before header (like "transactions1")
            if not re.match(r"\d{4}-\d{2}-\d{2}", row[0].strip()):
                continue

        date_str = row[0].strip()
        name = row[1].strip() if len(row) > 1 else ""
        try:
            amount = float(row[2].strip()) if len(row) > 2 and row[2].strip() else 0
        except ValueError:
            continue

        if not date_str or not name:
            continue

        txns.append({
            "date": date_str,
            "name": name,
            "amount": amount,
        })

    return txns


# ---------------------------------------------------------------------------
# Rich Data Exhaust Extraction — works on raw (date, name, amount) data
# ---------------------------------------------------------------------------

def extract_data_exhaust(txns: list[dict]) -> dict:
    """
    Extract rich behavioral signals from raw transactions.
    Handles both CSV format (name) and Supabase format (merchant).
    """
    # Normalise: ensure every txn has a "name" field
    for t in txns:
        if "name" not in t and "merchant" in t:
            t["name"] = t["merchant"]
        if "name" not in t:
            t["name"] = "Unknown"

    # Separate inflows (negative amounts or known income patterns) from outflows
    inflows = [t for t in txns if _is_inflow(t)]
    outflows = [t for t in txns if not _is_inflow(t) and float(t["amount"]) > 0]

    return {
        "overview": _overview(txns, inflows, outflows),
        "day_of_week_pattern": _day_of_week_pattern(outflows),
        "hourly_density": _daily_transaction_density(outflows),
        "merchant_loyalty": _merchant_loyalty(outflows),
        "merchant_clusters": _merchant_clusters(outflows),
        "spending_velocity": _spending_velocity(outflows),
        "big_moves": _big_moves(txns),
        "outlier_transactions": _outlier_transactions(outflows),
        "subscription_detection": _subscription_detection(outflows),
        "binge_days": _binge_days(outflows),
        "geographic_signals": _geographic_signals(outflows),
        "lifestyle_indicators": _lifestyle_indicators(outflows),
        "income_patterns": _income_patterns(inflows),
        "micro_transactions": _micro_transactions(outflows),
    }


def _is_inflow(t: dict) -> bool:
    """Detect income / inflow transactions."""
    amount = float(t["amount"])
    name = t.get("name", "").lower()
    # Negative amount = credit/inflow in this CSV format
    if amount < 0:
        return True
    # Known income keywords
    if t.get("spending_type") == "income" or t.get("category") == "salary":
        return True
    if any(kw in name for kw in ["payment received", "incoming wire", "interest earned",
                                   "deposit", "payment - thank"]):
        return True
    return False


def _overview(txns, inflows, outflows) -> dict:
    total_in = sum(abs(float(t["amount"])) for t in inflows)
    total_out = sum(float(t["amount"]) for t in outflows)
    dates = [t["date"][:10] for t in txns if t.get("date")]
    dates_sorted = sorted(dates)
    return {
        "total_transactions": len(txns),
        "total_inflows": round(total_in, 2),
        "total_outflows": round(total_out, 2),
        "net_flow": round(total_in - total_out, 2),
        "date_range": f"{dates_sorted[0]} to {dates_sorted[-1]}" if dates_sorted else "N/A",
        "months_covered": len(set(d[:7] for d in dates_sorted)),
        "avg_daily_spend": round(total_out / max(len(set(dates_sorted)), 1), 2),
        "avg_transaction_size": round(total_out / max(len(outflows), 1), 2),
    }


def _day_of_week_pattern(txns: list[dict]) -> dict:
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
        "totals": {d: round(totals.get(d, 0), 2) for d in days},
        "counts": {d: counts.get(d, 0) for d in days},
        "peak_day": max(totals, key=totals.get) if totals else "N/A",
        "quietest_day": min(totals, key=totals.get) if totals else "N/A",
    }


def _daily_transaction_density(txns: list[dict]) -> dict:
    """How many transactions per day — reveals busy vs calm spending days."""
    by_date = defaultdict(int)
    for t in txns:
        by_date[t["date"][:10]] += 1
    counts = list(by_date.values())
    if not counts:
        return {}
    return {
        "avg_per_day": round(sum(counts) / len(counts), 1),
        "max_in_one_day": max(counts),
        "days_with_10plus": sum(1 for c in counts if c >= 10),
        "days_with_zero": 0,  # Only counted days have entries
    }


def _merchant_loyalty(txns: list[dict]) -> list[dict]:
    freq = defaultdict(int)
    totals = defaultdict(float)
    for t in txns:
        m = t.get("name", "Unknown")
        freq[m] += 1
        totals[m] += float(t["amount"])
    merchants = sorted(
        [{"merchant": m, "visits": freq[m], "total": round(totals[m], 2),
          "avg_per_visit": round(totals[m] / freq[m], 2)}
         for m in freq],
        key=lambda x: x["visits"],
        reverse=True,
    )
    return merchants[:15]


def _merchant_clusters(txns: list[dict]) -> dict:
    """Group merchants into behavioral clusters by keyword matching."""
    clusters = {
        "coffee_cafes": ["coffee", "cafe", "caf", "starbucks", "blue bottle", "pret", "devocion",
                         "grind", "roast", "espresso", "latte", "butler"],
        "restaurants_dining": ["rest", "restaurant", "diner", "taco", "pizza", "sushi", "poke",
                               "kitchen", "grill", "burger", "shake shack", "dig inn", "dig ",
                               "mealpal", "wonder", "popeyes", "mcdonald"],
        "transport_mobility": ["uber", "lyft", "lime", "nyct", "tfl", "citibik", "ferry",
                               "renfe", "transport", "alpytransfer"],
        "subscriptions_digital": ["netflix", "spotify", "youtube", "patreon", "substack",
                                  "rocket money", "porkbun", "appscreen", "gotinder",
                                  "kindle", "amazon digital"],
        "groceries_market": ["trader joe", "mercadona", "market", "whole", "produce",
                             "carniceria", "fruter"],
        "travel_accommodation": ["airbnb", "kiwi.com", "hotel", "esf chamonix", "thermes",
                                 "edreams"],
        "financial_transfers": ["venmo", "zelle", "wise", "xoom", "robinhood", "brokerage",
                                "barclaycard", "applecard", "chase credit", "payment"],
        "shopping_retail": ["amazon", "uniqlo", "david mellor", "superdrug", "tiger"],
        "health_wellness": ["medical", "biotech", "city medical", "oral"],
    }

    result = {}
    for cluster_name, keywords in clusters.items():
        matching_txns = [
            t for t in txns
            if any(kw in t.get("name", "").lower() for kw in keywords)
        ]
        if matching_txns:
            total = sum(float(t["amount"]) for t in matching_txns)
            result[cluster_name] = {
                "count": len(matching_txns),
                "total": round(total, 2),
                "avg": round(total / len(matching_txns), 2),
                "top_merchants": list(dict.fromkeys(
                    t.get("name", "") for t in sorted(matching_txns, key=lambda x: float(x["amount"]), reverse=True)
                ))[:5],
            }
    return result


def _spending_velocity(txns: list[dict]) -> list[dict]:
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
            "previous": round(prev, 2),
            "current": round(curr, 2),
            "change_pct": round(change, 1),
        })
    return velocity


def _big_moves(txns: list[dict]) -> list[dict]:
    """Transactions over $500 (or equivalent) — reveals major financial decisions."""
    big = []
    for t in txns:
        amt = float(t["amount"])
        if abs(amt) >= 500:
            big.append({
                "date": t["date"][:10],
                "name": t.get("name", "Unknown"),
                "amount": round(amt, 2),
                "type": "inflow" if amt < 0 else "outflow",
            })
    return sorted(big, key=lambda x: abs(x["amount"]), reverse=True)[:15]


def _outlier_transactions(txns: list[dict]) -> list[dict]:
    amounts = [float(t["amount"]) for t in txns]
    if len(amounts) < 3:
        return []
    mean = sum(amounts) / len(amounts)
    std_dev = math.sqrt(sum((a - mean) ** 2 for a in amounts) / len(amounts))
    if std_dev == 0:
        return []
    threshold = mean + 2 * std_dev
    outliers = []
    for t in txns:
        amt = float(t["amount"])
        if amt > threshold:
            outliers.append({
                "name": t.get("name", "Unknown"),
                "amount": round(amt, 2),
                "date": t["date"][:10],
                "avg": round(mean, 2),
                "deviation": round((amt - mean) / std_dev, 1),
            })
    return sorted(outliers, key=lambda x: x["deviation"], reverse=True)[:8]


def _subscription_detection(txns: list[dict]) -> list[dict]:
    merchant_monthly = defaultdict(lambda: defaultdict(list))
    for t in txns:
        m = t.get("name", "Unknown")
        month_key = t["date"][:7]
        merchant_monthly[m][month_key].append(float(t["amount"]))
    subscriptions = []
    for merchant, months_data in merchant_monthly.items():
        if len(months_data) < 3:
            continue
        monthly_amounts = [amounts[0] for amounts in months_data.values()]
        mean = sum(monthly_amounts) / len(monthly_amounts)
        if mean <= 0:
            continue
        consistent = all(abs(a - mean) / mean < 0.25 for a in monthly_amounts)
        if consistent:
            subscriptions.append({
                "merchant": merchant,
                "avg_amount": round(mean, 2),
                "months_detected": len(months_data),
                "monthly_cost": round(mean, 2),
                "annual_cost": round(mean * 12, 2),
            })
    return sorted(subscriptions, key=lambda x: x["annual_cost"], reverse=True)


def _binge_days(txns: list[dict]) -> list[dict]:
    """Days with unusually high transaction count or spending — reveals binge behavior."""
    by_date = defaultdict(lambda: {"count": 0, "total": 0.0, "merchants": []})
    for t in txns:
        d = t["date"][:10]
        by_date[d]["count"] += 1
        by_date[d]["total"] += float(t["amount"])
        by_date[d]["merchants"].append(t.get("name", "Unknown"))

    all_totals = [v["total"] for v in by_date.values()]
    if not all_totals:
        return []
    mean_daily = sum(all_totals) / len(all_totals)
    threshold = mean_daily * 2.5

    binges = []
    for date, data in by_date.items():
        if data["total"] > threshold:
            unique_merchants = list(dict.fromkeys(data["merchants"]))[:5]
            binges.append({
                "date": date,
                "transaction_count": data["count"],
                "total_spent": round(data["total"], 2),
                "daily_avg": round(mean_daily, 2),
                "multiplier": round(data["total"] / mean_daily, 1),
                "merchants": unique_merchants,
            })
    return sorted(binges, key=lambda x: x["total_spent"], reverse=True)[:5]


def _geographic_signals(txns: list[dict]) -> dict:
    """Detect geographic patterns from merchant names."""
    geo_keywords = {
        "New York / Brooklyn": ["nyct", "williamsbur", "brooklyn", "east vi", "bed-stuy",
                                 "fort gree", "essex r", "nyc ferry", "con ed of ny"],
        "Mexico": ["condesa", "tacos", "mex", "clip mx", "merpago", "bpk*", "ztl*",
                    "miravalle", "califa", "caiman", "nonna h", "felix mex", "baltra",
                    "baveno", "contramar", "chui", "malhecho"],
        "Spain": ["almeria", "mercadona", "renfe", "carniceria", "fruter", "campillo",
                   "vecino", "pintamonas"],
        "France": ["chamonix", "thermes", "pitte", "societe d equipe", "hvgge geneve"],
        "United Kingdom": ["tfl", "pret a manger", "uniqlo 311 oxford", "essex rd",
                           "ole and steen", "david mellor", "superdrug"],
    }

    result = {}
    for region, keywords in geo_keywords.items():
        matching = [t for t in txns if any(kw in t.get("name", "").lower() for kw in keywords)]
        if matching:
            dates = sorted(set(t["date"][:10] for t in matching))
            total = sum(float(t["amount"]) for t in matching)
            result[region] = {
                "transactions": len(matching),
                "total_spent": round(total, 2),
                "date_range": f"{dates[0]} to {dates[-1]}",
                "avg_per_transaction": round(total / len(matching), 2),
            }
    return result


def _lifestyle_indicators(txns: list[dict]) -> dict:
    """Infer lifestyle traits from spending patterns."""
    names_lower = [t.get("name", "").lower() for t in txns]
    amounts = [float(t["amount"]) for t in txns]

    coffee_count = sum(1 for n in names_lower if any(k in n for k in
                       ["coffee", "cafe", "caf", "pret", "devocion", "blue bottle", "grind", "roast"]))
    dining_count = sum(1 for n in names_lower if any(k in n for k in
                       ["rest", "diner", "taco", "pizza", "burger", "kitchen", "grill", "poke"]))
    ride_count = sum(1 for n in names_lower if any(k in n for k in ["uber", "lyft", "lime"]))
    subscription_names = [n for n in names_lower if any(k in n for k in
                          ["substack", "patreon", "netflix", "spotify", "youtube", "kindle"])]
    travel_count = sum(1 for n in names_lower if any(k in n for k in
                       ["airbnb", "kiwi", "edreams", "renfe", "esf", "thermes"]))

    total_out = sum(a for a in amounts if a > 0)
    small_txns = sum(1 for a in amounts if 0 < a < 10)

    return {
        "coffee_addict_score": coffee_count,
        "foodie_score": dining_count,
        "ride_hailing_dependency": ride_count,
        "digital_subscriber_count": len(subscription_names),
        "travel_transactions": travel_count,
        "micro_transaction_ratio": round(small_txns / max(len(amounts), 1) * 100, 1),
        "avg_coffee_spend": round(
            sum(float(txns[i]["amount"]) for i, n in enumerate(names_lower)
                if any(k in n for k in ["coffee", "cafe", "caf", "pret", "devocion", "blue bottle"]))
            / max(coffee_count, 1), 2),
    }


def _income_patterns(inflows: list[dict]) -> dict:
    """Analyze income sources and regularity."""
    sources = defaultdict(lambda: {"count": 0, "total": 0.0})
    for t in inflows:
        name = t.get("name", "Unknown")
        sources[name]["count"] += 1
        sources[name]["total"] += abs(float(t["amount"]))

    sorted_sources = sorted(sources.items(), key=lambda x: x[1]["total"], reverse=True)
    return {
        "sources": [
            {"name": name, "count": data["count"], "total": round(data["total"], 2)}
            for name, data in sorted_sources[:8]
        ],
        "total_income": round(sum(d["total"] for _, d in sorted_sources), 2),
        "income_sources_count": len(sorted_sources),
    }


def _micro_transactions(txns: list[dict]) -> dict:
    """Analyze sub-$10 spending — death by a thousand cuts."""
    micro = [t for t in txns if 0 < float(t["amount"]) < 10]
    total_micro = sum(float(t["amount"]) for t in micro)
    total_all = sum(float(t["amount"]) for t in txns if float(t["amount"]) > 0)
    return {
        "count": len(micro),
        "total": round(total_micro, 2),
        "pct_of_spending": round(total_micro / max(total_all, 1) * 100, 1),
        "avg_amount": round(total_micro / max(len(micro), 1), 2),
        "top_merchants": list(dict.fromkeys(
            t.get("name", "") for t in sorted(micro, key=lambda x: float(x["amount"]))
        ))[:5],
    }


# ---------------------------------------------------------------------------
# AI Insights Generation — send grouped data exhaust to Claude
# ---------------------------------------------------------------------------

async def generate_insights(user_id: int, transactions: list[dict], *, from_csv: bool = False) -> dict:
    """
    Generate AI-powered behavioral insights from transaction data exhaust.
    Uses direct Anthropic API call (~5-10s) — CrewAI pipeline remains separate for investments.
    """
    data_exhaust = extract_data_exhaust(transactions)

    # Build a compact summary for Claude (grouping, not raw rows)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = f"""You are BAQI AI, a world-class financial behavior analyst. You specialize in discovering hidden personality traits, lifestyle patterns, and financial behaviors from raw transaction data — things the user CANNOT see about themselves.

You are given DATA EXHAUST — pre-computed behavioral signals extracted from {data_exhaust['overview']['total_transactions']} real bank transactions spanning {data_exhaust['overview']['date_range']}.

## DATA EXHAUST SIGNALS

### Overview
{json.dumps(data_exhaust['overview'], indent=2)}

### Day-of-Week Spending Pattern
{json.dumps(data_exhaust['day_of_week_pattern'], indent=2)}

### Transaction Density
{json.dumps(data_exhaust['hourly_density'], indent=2)}

### Top 15 Most-Visited Merchants (Loyalty)
{json.dumps(data_exhaust['merchant_loyalty'], indent=2)}

### Merchant Clusters (Behavioral Groupings)
{json.dumps(data_exhaust['merchant_clusters'], indent=2)}

### Monthly Spending Velocity (Month-over-Month Changes)
{json.dumps(data_exhaust['spending_velocity'], indent=2)}

### Big Financial Moves (>$500)
{json.dumps(data_exhaust['big_moves'], indent=2)}

### Spending Outliers
{json.dumps(data_exhaust['outlier_transactions'], indent=2)}

### Detected Subscriptions (Recurring Payments)
{json.dumps(data_exhaust['subscription_detection'], indent=2)}

### Binge Spending Days
{json.dumps(data_exhaust['binge_days'], indent=2)}

### Geographic Footprint
{json.dumps(data_exhaust['geographic_signals'], indent=2)}

### Lifestyle Indicators
{json.dumps(data_exhaust['lifestyle_indicators'], indent=2)}

### Income Sources
{json.dumps(data_exhaust['income_patterns'], indent=2)}

### Micro-Transactions (Under $10)
{json.dumps(data_exhaust['micro_transactions'], indent=2)}

---

## YOUR TASK

Produce a JSON object with TWO sections:

### 1. "persona" — A Financial Personality Profile
Build a rich profile of WHO this person is based ONLY on the data above. Include:
- An archetype name (e.g. "The Urban Nomad", "The Quiet Accumulator")
- 3-4 personality traits inferred from spending
- Lifestyle description (1-2 sentences)
- Financial behavior type

### 2. "insights" — Exactly 7 Behavioral Insights
Each insight must:
1. Reveal a SPECIFIC hidden pattern (use exact amounts, merchant names, days, percentages from the data)
2. Explain the psychological or financial WHY behind it
3. Give ONE concrete action
4. Categories: "behavioral", "saving_opportunity", "anomaly", "trend", "optimization", "lifestyle", "personality"
5. Severity: "info", "warning", "opportunity"

Return ONLY valid JSON (no markdown, no explanation):
{{
  "persona": {{
    "archetype": "string",
    "traits": ["trait1", "trait2", "trait3"],
    "lifestyle_summary": "1-2 sentences",
    "financial_type": "string",
    "spending_personality": "string"
  }},
  "insights": [
    {{
      "title": "short title",
      "description": "2-3 sentences with SPECIFIC numbers from the data",
      "action": "one concrete step",
      "category": "behavioral|saving_opportunity|anomaly|trend|optimization|lifestyle|personality",
      "severity": "info|warning|opportunity",
      "impact_amount": null
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse JSON from response — handle possible markdown wrapping
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    result = json.loads(raw)

    return {
        "user_id": user_id,
        "persona": result.get("persona", {}),
        "insights": result.get("insights", []),
        "data_exhaust": data_exhaust,
        "generated_at": datetime.utcnow().isoformat(),
    }
