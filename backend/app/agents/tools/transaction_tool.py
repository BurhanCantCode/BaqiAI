"""CrewAI tool for querying user transactions from Supabase."""

from crewai.tools import BaseTool
from pydantic import Field


class TransactionQueryTool(BaseTool):
    name: str = "Transaction Query"
    description: str = (
        "Query a user's transaction history from the database. "
        "Input: user_id as a string number (e.g. '1'). "
        "Returns a JSON summary of their transactions grouped by category."
    )

    def _run(self, user_id: str) -> str:
        from app.database import supabase

        result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", int(user_id))
            .order("date")
            .execute()
        )

        if not result.data:
            return '{"error": "No transactions found for this user"}'

        # Summarize by category
        from collections import defaultdict
        import json

        categories = defaultdict(lambda: {"count": 0, "total": 0.0, "merchants": set()})
        for txn in result.data:
            cat = txn.get("category", "unknown")
            categories[cat]["count"] += 1
            categories[cat]["total"] += float(txn["amount"])
            categories[cat]["merchants"].add(txn.get("merchant", ""))

        summary = {}
        for cat, data in categories.items():
            summary[cat] = {
                "count": data["count"],
                "total_pkr": round(data["total"], 2),
                "merchants": list(data["merchants"])[:5],
            }

        return json.dumps(summary, indent=2)
