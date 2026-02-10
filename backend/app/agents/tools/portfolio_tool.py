"""CrewAI tool for reading/writing portfolio data in Supabase."""

import json
from crewai.tools import BaseTool


class PortfolioReadTool(BaseTool):
    name: str = "Portfolio Reader"
    description: str = (
        "Read the current investment portfolio for a user. "
        "Input: user_id as a string number (e.g. '1'). "
        "Returns current holdings with amounts and returns."
    )

    def _run(self, user_id: str) -> str:
        from app.database import supabase

        result = (
            supabase.table("investments")
            .select("*")
            .eq("user_id", int(user_id))
            .eq("status", "active")
            .execute()
        )

        if not result.data:
            return json.dumps({"message": "No active investments found", "holdings": []})

        total_invested = sum(float(h["amount"]) for h in result.data)
        return json.dumps({
            "holdings": result.data,
            "total_invested": total_invested,
            "count": len(result.data),
        }, indent=2, default=str)
