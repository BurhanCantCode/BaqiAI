"""CrewAI tool for Shariah compliance screening of PSX stocks."""

import json
from crewai.tools import BaseTool


# KMI-30 Index components (Karachi Meezan Index - Shariah compliant)
# Based on Meezan Bank Shariah screening criteria
HALAL_STOCKS = {
    "LUCK": {"is_halal": True, "reason": "Manufacturing (cement), debt/equity < 33%, no haram revenue"},
    "SYS": {"is_halal": True, "reason": "IT services, halal business, compliant financials"},
    "ENGRO": {"is_halal": True, "reason": "Conglomerate (fertilizer, food), screened by KMI-30"},
    "FFC": {"is_halal": True, "reason": "Fertilizer manufacturing, compliant capital structure"},
    "OGDC": {"is_halal": True, "reason": "Oil & gas exploration, KMI-30 component"},
    "PPL": {"is_halal": True, "reason": "Petroleum exploration, Shariah compliant"},
    "HUBC": {"is_halal": True, "reason": "Power generation, screened by KMI-30"},
    "MARI": {"is_halal": True, "reason": "Petroleum exploration, compliant financials"},
    "PSO": {"is_halal": True, "reason": "Oil marketing, KMI-30 component"},
    "SEARL": {"is_halal": True, "reason": "Pharmaceutical company, halal business"},
    "TRG": {"is_halal": True, "reason": "Technology investment, compliant structure"},
    "EFERT": {"is_halal": True, "reason": "Fertilizer (Engro subsidiary), Shariah compliant"},
    "FCCL": {"is_halal": True, "reason": "Cement manufacturing, KMI-30 component"},
    "DGKC": {"is_halal": True, "reason": "Cement manufacturing, compliant financials"},
    "UNITY": {"is_halal": True, "reason": "Food products, halal business operations"},
    "MEBL": {"is_halal": True, "reason": "Islamic banking (Meezan Bank), fully Shariah compliant"},
    # Non-halal stocks
    "UBL": {"is_halal": False, "reason": "Conventional banking, interest-based income > 5%"},
    "HBL": {"is_halal": False, "reason": "Conventional banking, interest-based business model"},
    "NESTLE": {"is_halal": True, "reason": "Food & beverages (halal products in Pakistan)"},
    "COLG": {"is_halal": True, "reason": "Consumer goods, compliant capital structure"},
}


class HalalScreeningTool(BaseTool):
    name: str = "Halal Stock Screener"
    description: str = (
        "Check if PSX stocks are Shariah-compliant based on KMI-30 criteria. "
        "Input: comma-separated ticker symbols (e.g. 'LUCK,UBL,SYS'). "
        "Returns halal status and reason for each stock."
    )

    def _run(self, tickers: str) -> str:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        results = []
        for ticker in ticker_list:
            if ticker in HALAL_STOCKS:
                info = HALAL_STOCKS[ticker]
                results.append({
                    "ticker": ticker,
                    "is_halal": info["is_halal"],
                    "reason": info["reason"],
                })
            else:
                results.append({
                    "ticker": ticker,
                    "is_halal": False,
                    "reason": f"Not found in Shariah screening database. Treat as non-compliant.",
                })

        compliant = sum(1 for r in results if r["is_halal"])
        return json.dumps({
            "screened_stocks": results,
            "compliant_count": compliant,
            "total_screened": len(results),
        }, indent=2)
