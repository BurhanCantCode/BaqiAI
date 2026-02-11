"""CrewAI tool for fetching PSX stock predictions.

Uses ML-predicted data from cache/seed when available,
falls back to hardcoded data if predictions unavailable.
"""

import json
import logging
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

# Hardcoded realistic data for top KSE-100 stocks
# Used as fallback when ML predictions are unavailable
PSX_STOCK_DATA = {
    "LUCK": {"name": "Lucky Cement", "sector": "Cement", "price": 875, "predicted_return": 0.08, "pe_ratio": 12.5},
    "SYS": {"name": "Systems Limited", "sector": "Technology", "price": 520, "predicted_return": 0.12, "pe_ratio": 18.2},
    "ENGRO": {"name": "Engro Corporation", "sector": "Conglomerate", "price": 310, "predicted_return": 0.06, "pe_ratio": 9.8},
    "FFC": {"name": "Fauji Fertilizer", "sector": "Fertilizer", "price": 165, "predicted_return": 0.05, "pe_ratio": 8.5},
    "OGDC": {"name": "OGDC", "sector": "Oil & Gas", "price": 128, "predicted_return": 0.07, "pe_ratio": 5.2},
    "PPL": {"name": "Pakistan Petroleum", "sector": "Oil & Gas", "price": 95, "predicted_return": 0.09, "pe_ratio": 4.8},
    "HUBC": {"name": "Hub Power", "sector": "Power", "price": 105, "predicted_return": 0.04, "pe_ratio": 6.1},
    "MARI": {"name": "Mari Petroleum", "sector": "Oil & Gas", "price": 1650, "predicted_return": 0.10, "pe_ratio": 7.3},
    "PSO": {"name": "Pakistan State Oil", "sector": "Oil Marketing", "price": 245, "predicted_return": 0.06, "pe_ratio": 3.9},
    "SEARL": {"name": "Searle Company", "sector": "Pharma", "price": 58, "predicted_return": 0.11, "pe_ratio": 22.1},
    "TRG": {"name": "TRG Pakistan", "sector": "Technology", "price": 135, "predicted_return": 0.15, "pe_ratio": 25.0},
    "EFERT": {"name": "Engro Fertilizers", "sector": "Fertilizer", "price": 78, "predicted_return": 0.07, "pe_ratio": 7.8},
    "FCCL": {"name": "Fauji Cement", "sector": "Cement", "price": 23, "predicted_return": 0.09, "pe_ratio": 10.5},
    "DGKC": {"name": "DG Khan Cement", "sector": "Cement", "price": 85, "predicted_return": 0.06, "pe_ratio": 11.2},
    "MEBL": {"name": "Meezan Bank", "sector": "Banking (Islamic)", "price": 235, "predicted_return": 0.08, "pe_ratio": 9.5},
    "UBL": {"name": "United Bank", "sector": "Banking", "price": 195, "predicted_return": 0.07, "pe_ratio": 6.8},
    "HBL": {"name": "Habib Bank", "sector": "Banking", "price": 118, "predicted_return": 0.05, "pe_ratio": 5.5},
    "NESTLE": {"name": "Nestle Pakistan", "sector": "FMCG", "price": 6250, "predicted_return": 0.04, "pe_ratio": 28.5},
    "COLG": {"name": "Colgate Palmolive", "sector": "FMCG", "price": 2450, "predicted_return": 0.05, "pe_ratio": 24.0},
    "UNITY": {"name": "Unity Foods", "sector": "Food", "price": 28, "predicted_return": 0.13, "pe_ratio": 15.0},
}

# Mutual fund data
MUTUAL_FUNDS = {
    "ALMEEZAN_EQUITY": {"name": "Al Meezan Mutual Fund", "type": "Islamic Equity", "nav": 85.5, "annual_return": 0.18, "is_halal": True},
    "NBP_STOCK": {"name": "NBP Stock Fund", "type": "Equity", "nav": 42.3, "annual_return": 0.15, "is_halal": False},
    "HBL_ISLAMIC": {"name": "HBL Islamic Equity Fund", "type": "Islamic Equity", "nav": 35.8, "annual_return": 0.14, "is_halal": True},
    "ALMEEZAN_INCOME": {"name": "Al Meezan Islamic Income Fund", "type": "Islamic Fixed Income", "nav": 55.2, "annual_return": 0.09, "is_halal": True},
    "NBP_INCOME": {"name": "NBP Income Fund", "type": "Fixed Income", "nav": 12.5, "annual_return": 0.11, "is_halal": False},
}


def _load_ml_predictions() -> dict | None:
    """Try to load ML predictions from cache/seed data."""
    try:
        from app.services.psx_prediction_service import get_predictions_for_crew
        return get_predictions_for_crew()
    except Exception as e:
        logger.warning(f"Failed to load ML predictions: {e}")
        return None


class PSXPredictionTool(BaseTool):
    name: str = "PSX Stock Predictor"
    description: str = (
        "Get stock predictions and data for PSX-listed companies. "
        "Input: comma-separated ticker symbols (e.g. 'LUCK,SYS,ENGRO') "
        "or 'ALL' to get all available stocks. "
        "Returns price, predicted return, sector, and PE ratio for each. "
        "ML-powered predictions include 21-day forecasts with confidence scores."
    )

    def _run(self, tickers: str) -> str:
        tickers = tickers.strip().upper()

        # Try ML predictions first, fallback to hardcoded
        ml_data = _load_ml_predictions()
        stocks = ml_data["stocks"] if ml_data else PSX_STOCK_DATA
        funds = MUTUAL_FUNDS

        if ml_data:
            logger.info(f"Using ML predictions for {list(ml_data['stocks'].keys())}")
        else:
            logger.info("Using fallback hardcoded stock data")

        if tickers == "ALL":
            result = {
                "stocks": stocks,
                "mutual_funds": funds,
            }
            return json.dumps(result, indent=2)

        ticker_list = [t.strip() for t in tickers.split(",")]
        result = {}
        for ticker in ticker_list:
            if ticker in stocks:
                result[ticker] = stocks[ticker]
            elif ticker in funds:
                result[ticker] = funds[ticker]
            else:
                result[ticker] = {"error": f"Ticker {ticker} not found in database"}

        return json.dumps(result, indent=2)
