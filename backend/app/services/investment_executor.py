"""Simulated investment execution and portfolio snapshot creation."""

from datetime import date

from app.database import supabase


async def execute_investment(user_id: int, portfolio: list[dict]) -> dict:
    """
    Execute a recommended portfolio by creating investment records in Supabase.
    This is simulated — no real brokerage connection.

    Returns summary of executed investments.
    """
    today = date.today().isoformat()
    executed = []

    for alloc in portfolio:
        ticker = alloc.get("ticker", "")
        amount = alloc.get("amount_pkr", 0)
        # Simulate purchase price from PSX data or use amount
        purchase_price = alloc.get("purchase_price", amount)
        quantity = round(amount / purchase_price, 4) if purchase_price > 0 else 0

        record = {
            "user_id": user_id,
            "investment_date": today,
            "asset_type": alloc.get("asset_type", "stock"),
            "asset_name": alloc.get("asset_name", ""),
            "ticker": ticker,
            "amount": amount,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "current_price": purchase_price,  # Same at time of purchase
            "status": "active",
        }

        result = supabase.table("investments").insert(record).execute()
        if result.data:
            executed.append(result.data[0])

    # Create portfolio snapshot
    total_invested = sum(a.get("amount_pkr", 0) for a in portfolio)
    snapshot = {
        "user_id": user_id,
        "snapshot_date": today,
        "total_invested": total_invested,
        "current_value": total_invested,  # Same at time of purchase
        "return_percentage": 0.0,
    }
    supabase.table("portfolio_snapshots").insert(snapshot).execute()

    return {
        "user_id": user_id,
        "investments_created": len(executed),
        "total_invested": total_invested,
        "investment_date": today,
        "status": "active",
        "holdings": executed,
    }


async def get_portfolio(user_id: int) -> dict:
    """
    Fetch current portfolio holdings and snapshots for a user.
    Simulates current prices with a small random gain.
    """
    import random

    # Fetch active investments
    inv_result = (
        supabase.table("investments")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .execute()
    )
    holdings = inv_result.data or []

    # Simulate current price movement (±5% for demo)
    total_invested = 0.0
    current_value = 0.0
    for h in holdings:
        invested = float(h.get("amount", 0))
        total_invested += invested
        # Simulate small gain for demo purposes
        gain = random.uniform(-0.02, 0.08)
        simulated_value = invested * (1 + gain)
        h["current_value"] = round(simulated_value, 2)
        h["return_pct"] = round(gain * 100, 2)
        current_value += simulated_value

    total_return = current_value - total_invested
    return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0

    # Fetch snapshots
    snap_result = (
        supabase.table("portfolio_snapshots")
        .select("*")
        .eq("user_id", user_id)
        .order("snapshot_date")
        .execute()
    )
    snapshots = snap_result.data or []

    return {
        "user_id": user_id,
        "holdings": holdings,
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "total_return": round(total_return, 2),
        "return_percentage": round(return_pct, 2),
        "snapshots": snapshots,
    }
