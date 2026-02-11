"""
PSX Prediction Service - Orchestrates ML predictions for 5 sector stocks.

Runs predictions sequentially (one at a time), persists results to cache,
and provides a clean interface for CrewAI agents to consume.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)

# --- Configuration ---

SECTOR_STOCKS = {
    "cement": {"symbol": "LUCK", "name": "Lucky Cement", "pe_ratio": 12.5},
    "fertilizer": {"symbol": "FFC", "name": "Fauji Fertilizer", "pe_ratio": 8.5},
    "energy": {"symbol": "OGDC", "name": "OGDC", "pe_ratio": 5.2},
    "banking": {"symbol": "UBL", "name": "United Bank", "pe_ratio": 6.8},
    "tech": {"symbol": "SYS", "name": "Systems Limited", "pe_ratio": 18.2},
}

# Execution order for sequential prediction
PREDICTION_ORDER = ["LUCK", "FFC", "OGDC", "UBL", "SYS"]

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CACHE_FILE = DATA_DIR / "psx_predictions_cache.json"
SEED_DIR = DATA_DIR / "psx_seed"

# Sector name mapping (symbol -> display sector)
SYMBOL_SECTOR_MAP = {v["symbol"]: k.title() for k, v in SECTOR_STOCKS.items()}
SYMBOL_NAME_MAP = {v["symbol"]: v["name"] for k, v in SECTOR_STOCKS.items()}
SYMBOL_PE_MAP = {v["symbol"]: v["pe_ratio"] for k, v in SECTOR_STOCKS.items()}


def load_cached_predictions() -> Optional[Dict]:
    """
    Load predictions using 3-tier fallback:
    1. Live ML cache (psx_predictions_cache.json)
    2. Seed data (pre-computed predictions)
    3. None (caller falls back to hardcoded)
    """
    # Tier 1: Live cache
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
            if cache.get("stocks") and len(cache["stocks"]) > 0:
                logger.info(f"Loaded live cache with {len(cache['stocks'])} stocks")
                return cache
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Cache file corrupt: {e}")

    # Tier 2: Seed data
    return _load_seed_data()


def _load_seed_data() -> Optional[Dict]:
    """Load pre-computed seed predictions from JSON files."""
    if not SEED_DIR.exists():
        logger.warning(f"Seed directory not found: {SEED_DIR}")
        return None

    stocks = {}
    for symbol in PREDICTION_ORDER:
        seed_file = SEED_DIR / f"{symbol}_research_predictions_2026.json"
        if seed_file.exists():
            try:
                with open(seed_file) as f:
                    data = json.load(f)
                stocks[symbol] = {
                    "symbol": symbol,
                    "sector": SYMBOL_SECTOR_MAP.get(symbol, "Unknown"),
                    "current_price": _extract_current_price(data),
                    "daily_predictions": data.get("daily_predictions", [])[:21],
                    "prediction_reasoning": data.get("prediction_reasoning", {}),
                    "metrics": data.get("metrics", {}),
                }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load seed for {symbol}: {e}")

    if stocks:
        logger.info(f"Loaded seed data for {len(stocks)} stocks")
        return {
            "generated_at": "seed_data",
            "source": "pre_computed",
            "stocks": stocks,
        }

    return None


def _extract_current_price(prediction_data: Dict) -> float:
    """Extract current price from prediction data."""
    # If current_price field exists, use it
    if "current_price" in prediction_data:
        return prediction_data["current_price"]

    # Otherwise derive from first prediction's upside_potential
    predictions = prediction_data.get("daily_predictions", [])
    if predictions:
        first = predictions[0]
        predicted_price = first.get("predicted_price", 0)
        upside_pct = first.get("upside_potential", 0) / 100
        if upside_pct != 0:
            return round(predicted_price / (1 + upside_pct), 2)
        return predicted_price

    return 0.0


def is_cache_fresh(cache: Optional[Dict], max_age_hours: int = 24) -> bool:
    """Check if cache is fresh (generated within max_age_hours)."""
    if not cache:
        return False

    generated_at = cache.get("generated_at")
    if not generated_at or generated_at == "seed_data":
        return False

    try:
        gen_time = datetime.fromisoformat(generated_at)
        return datetime.now() - gen_time < timedelta(hours=max_age_hours)
    except (ValueError, TypeError):
        return False


def _save_cache(stocks: Dict):
    """Save predictions to cache file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache = {
        "generated_at": datetime.now().isoformat(),
        "source": "ml_prediction",
        "stocks": stocks,
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    logger.info(f"Cache saved with {len(stocks)} stocks")


async def run_predictions_for_all_sectors(
    progress_callback: Optional[Callable] = None,
    force_fresh: bool = False,
) -> Dict:
    """
    Run 21-day ML predictions for all 5 sector stocks, sequentially.

    Stocks are processed one at a time: LUCK -> FFC -> OGDC -> UBL -> SYS.
    Cache is updated incrementally after each stock completes.

    If force_fresh=False (default), retains existing cached results for stocks
    that already have predictions. Only runs predictions for stocks missing
    from the cache. If force_fresh=True, re-runs ALL stocks from scratch.

    Args:
        progress_callback: Optional callable(symbol: str, pct: int, message: str)
        force_fresh: If True, ignore existing cache and re-run all stocks.

    Returns:
        Dict of predictions keyed by symbol
    """
    from app.services.psx_engine.data_fetcher import fetch_historical_data
    from app.services.psx_engine.research_model import PSXResearchModel
    from app.services.psx_engine.external_features import merge_external_features
    from app.services.psx_engine.validated_indicators import calculate_validated_indicators

    # Load existing cache to retain previous results
    stocks = {}
    if not force_fresh:
        existing = load_cached_predictions()
        if existing and existing.get("stocks"):
            stocks = dict(existing["stocks"])
            logger.info(f"Retaining {len(stocks)} existing predictions: {list(stocks.keys())}")

    total = len(PREDICTION_ORDER)

    for i, symbol in enumerate(PREDICTION_ORDER):
        pct = int((i / total) * 100)

        if progress_callback:
            progress_callback(symbol, pct, f"Starting prediction for {symbol} ({i+1}/{total})")

        # Skip stocks that already have cached predictions (unless force_fresh)
        if not force_fresh and symbol in stocks:
            logger.info(f"[{i+1}/{total}] {symbol} already cached, skipping (use force_fresh=True to re-run)")
            if progress_callback:
                progress_callback(symbol, pct + 18, f"Skipping {symbol} (already cached)")
            continue

        try:
            logger.info(f"[{i+1}/{total}] Running prediction for {symbol}...")

            # Step 1: Fetch historical OHLCV data from PSX
            if progress_callback:
                progress_callback(symbol, pct + 5, f"Fetching historical data for {symbol}...")

            raw_data = await fetch_historical_data(symbol)

            if not raw_data or len(raw_data) < 200:
                logger.warning(f"{symbol}: Insufficient data ({len(raw_data) if raw_data else 0} records)")
                continue

            # Step 2: Convert to DataFrame and add features
            import pandas as pd
            df = pd.DataFrame(raw_data)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)

            if progress_callback:
                progress_callback(symbol, pct + 8, f"Engineering features for {symbol}...")

            # Add external features (USD/PKR, KSE-100, oil)
            try:
                df = merge_external_features(df, symbol)
            except Exception as e:
                logger.warning(f"{symbol}: External features failed ({e}), continuing without")

            # Add validated technical indicators
            try:
                df = calculate_validated_indicators(df)
            except Exception as e:
                logger.warning(f"{symbol}: Indicator calculation failed ({e}), continuing without")

            # Step 3: Train model
            if progress_callback:
                progress_callback(symbol, pct + 10, f"Training ML model for {symbol}...")

            model = PSXResearchModel(
                symbol=symbol,
                use_wavelet=True,
                use_returns_model=True,
            )
            metrics = model.fit(df, verbose=False)

            # Step 4: Generate 21-day prediction
            if progress_callback:
                progress_callback(symbol, pct + 15, f"Generating 21-day forecast for {symbol}...")

            predictions = model.predict_daily(df, max_horizon=21)

            if not predictions:
                logger.warning(f"{symbol}: No predictions generated")
                continue

            # Get current price (last close in data)
            current_price = float(df['Close'].iloc[-1])

            stocks[symbol] = {
                "symbol": symbol,
                "sector": SYMBOL_SECTOR_MAP.get(symbol, "Unknown"),
                "current_price": current_price,
                "daily_predictions": predictions[:21],
                "prediction_reasoning": getattr(model, 'last_reasoning', {}),
                "metrics": metrics if isinstance(metrics, dict) else {},
            }

            # Incremental save after each stock
            _save_cache(stocks)

            logger.info(f"[{i+1}/{total}] {symbol} done: {len(predictions[:21])} day predictions")

        except Exception as e:
            logger.error(f"[{i+1}/{total}] {symbol} FAILED: {e}")
            if progress_callback:
                progress_callback(symbol, pct, f"Error on {symbol}: {str(e)[:100]}")
            continue

    if progress_callback:
        progress_callback("DONE", 100, f"All predictions complete. {len(stocks)}/{total} stocks successful.")

    return stocks


def get_predictions_for_crew() -> Optional[Dict]:
    """
    Get predictions in the format expected by PSXPredictionTool.

    Returns dict with:
    - "stocks": {symbol: {name, sector, price, predicted_return, pe_ratio, prediction_detail}}
    - "mutual_funds": (from hardcoded data, unchanged)

    Returns None if no predictions available.
    """
    cache = load_cached_predictions()
    if not cache or not cache.get("stocks"):
        return None

    stocks = {}
    for symbol, data in cache["stocks"].items():
        predictions_21d = data.get("daily_predictions", [])

        # Calculate predicted return from day 21 prediction
        predicted_return = 0.0
        if predictions_21d:
            last_pred = predictions_21d[-1]
            predicted_return = round(last_pred.get("upside_potential", 0) / 100, 4)

        # Derive direction from actual 21-day predicted return (not stored direction,
        # which is based on 357-day horizon and can contradict short-term predictions)
        if predicted_return > 0.02:
            direction = "BULLISH"
        elif predicted_return < -0.02:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        stock_entry = {
            "name": SYMBOL_NAME_MAP.get(symbol, symbol),
            "sector": SYMBOL_SECTOR_MAP.get(symbol, "Unknown"),
            "price": data.get("current_price", 0),
            "predicted_return": predicted_return,
            "pe_ratio": SYMBOL_PE_MAP.get(symbol, 10.0),
            "ml_prediction": {
                "direction": direction,
                "confidence": predictions_21d[0].get("confidence", 0) if predictions_21d else 0,
                "day_21_price": predictions_21d[-1].get("predicted_price", 0) if predictions_21d else 0,
                "daily_predictions": predictions_21d,
            },
        }

        # Enrich with sentiment data (cached, non-blocking)
        try:
            from app.services.psx_engine.sentiment_analyzer import get_stock_sentiment
            sentiment = get_stock_sentiment(symbol, use_cache=True)
            stock_entry["sentiment"] = {
                "score": sentiment.get("sentiment_score", 0),
                "signal": sentiment.get("signal_simple", "NEUTRAL"),
                "confidence": sentiment.get("confidence", 0),
                "news_count": sentiment.get("news_count", 0),
                "summary": sentiment.get("summary", ""),
            }
        except Exception:
            stock_entry["sentiment"] = None

        stocks[symbol] = stock_entry

    return {"stocks": stocks}
