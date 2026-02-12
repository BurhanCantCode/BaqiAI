"""
AI-powered sentiment analyzer for PSX stocks.
Uses news scraping + Groq LLM (Llama 3.3 70B) for intelligent analysis.
"""

import os
import json
import subprocess
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Groq imports
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed — sentiment analysis will use fallback")

# ============================================================================
# CONFIGURATION
# ============================================================================

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "news_cache"
CACHE_DURATION_HOURS = 4

# Stock symbol to company name mapping
STOCK_COMPANIES = {
    'LUCK': ('Lucky Cement', 'Lucky Cement Limited', 'LUCK'),
    'HBL': ('Habib Bank', 'Habib Bank Limited', 'HBL'),
    'UBL': ('United Bank', 'United Bank Limited', 'UBL'),
    'MCB': ('MCB Bank', 'MCB Bank Limited', 'Muslim Commercial Bank'),
    'OGDC': ('OGDC', 'Oil and Gas Development Company', 'Oil Gas Development'),
    'PPL': ('Pakistan Petroleum', 'PPL', 'Pakistan Petroleum Limited'),
    'PSO': ('Pakistan State Oil', 'PSO', 'State Oil'),
    'ENGRO': ('Engro', 'Engro Corporation', 'Engro Corp'),
    'FFC': ('Fauji Fertilizer', 'FFC', 'Fauji Fertilizer Company'),
    'FATIMA': ('Fatima Fertilizer', 'Fatima', 'Fatima Group'),
    'HUBC': ('Hub Power', 'HUBCO', 'Hub Power Company'),
    'SYS': ('Systems Limited', 'SYS', 'Systems Ltd'),
    'TRG': ('TRG Pakistan', 'TRG', 'The Resource Group'),
    'NESTLE': ('Nestle Pakistan', 'Nestle', 'NESTLE'),
    'MARI': ('Mari Petroleum', 'MARI', 'Mari Gas'),
    'MEBL': ('Meezan Bank', 'MEBL', 'Meezan'),
    'SEARL': ('Searle Pakistan', 'SEARL', 'Searle'),
    'PIOC': ('Pioneer Cement', 'PIOC', 'Pioneer'),
    'DGKC': ('DG Khan Cement', 'DGKC', 'DG Cement'),
    'MLCF': ('Maple Leaf Cement', 'MLCF', 'Maple Leaf'),
    'KEL': ('K-Electric', 'KEL', 'Karachi Electric'),
    'NBP': ('National Bank', 'NBP', 'National Bank Pakistan'),
    'ABL': ('Allied Bank', 'ABL', 'Allied Bank Limited'),
    'BAFL': ('Bank Alfalah', 'BAFL', 'Alfalah'),
    'BAHL': ('Bank Al Habib', 'BAHL', 'Al Habib'),
    'POL': ('Pakistan Oilfields', 'POL', 'Pakistan Oilfields Limited'),
    'ATRL': ('Attock Refinery', 'ATRL', 'Attock'),
    'EFERT': ('Engro Fertilizers', 'EFERT', 'Engro Fert'),
}


# ============================================================================
# CACHING SYSTEM
# ============================================================================

def _get_cache_path(symbol: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{symbol.upper()}_news.json"


def _load_cached_news(symbol: str) -> Optional[Dict]:
    cache_path = _get_cache_path(symbol)
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
                return cached
        except Exception:
            pass
    return None


def _save_to_cache(symbol: str, data: Dict):
    cache_path = _get_cache_path(symbol)
    data['cached_at'] = datetime.now().isoformat()
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ============================================================================
# NEWS FETCHING (curl-based — no Selenium dependency)
# ============================================================================

def _scrape_psx_announcements(symbol: str) -> List[Dict]:
    """Scrape PSX company announcements page via curl."""
    news_items = []
    try:
        url = f"https://dps.psx.com.pk/company/{symbol.upper()}"
        result = subprocess.run(
            ['curl', '-s', '-L', '--max-time', '15', url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            rows = re.findall(r'<tr[^>]*>.*?</tr>', result.stdout, re.DOTALL | re.IGNORECASE)
            for row in rows:
                cells = re.findall(r'<td[^>]*>([^<]+)</td>', row)
                if len(cells) >= 2:
                    date_text = cells[0].strip()
                    title = ' '.join(cells[1:3]).strip()
                    if len(title) > 10:
                        news_items.append({
                            'title': title[:300],
                            'date': date_text,
                            'source': 'PSX',
                            'url': url
                        })
    except Exception:
        pass
    return news_items[:10]


def _fetch_news_curl(search_term: str, source_url: str, source_name: str) -> List[Dict]:
    """Fetch news from a source using curl."""
    news = []
    try:
        url = source_url.format(search_term.replace(' ', '+'))
        result = subprocess.run(
            ['curl', '-s', '-L', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            matches = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]{20,200})</a>', result.stdout)
            for href, title in matches[:8]:
                title_clean = title.strip()
                if len(title_clean) > 15:
                    news.append({
                        'title': title_clean,
                        'url': href,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': source_name
                    })
    except Exception:
        pass
    return news


def fetch_all_news(symbol: str) -> List[Dict]:
    """Fetch news from multiple Pakistani sources."""
    company_names = STOCK_COMPANIES.get(symbol, (symbol,))
    all_news = []

    # PSX announcements
    psx_news = _scrape_psx_announcements(symbol)
    all_news.extend(psx_news)

    # Search Pakistani news sites
    sources = {
        'Business Recorder': 'https://www.brecorder.com/?s={}',
        'Dawn': 'https://www.dawn.com/search?q={}',
        'Tribune': 'https://tribune.com.pk/?s={}',
    }

    search_terms = [symbol] + list(company_names[:2])
    for source_name, source_url in sources.items():
        for term in search_terms:
            items = _fetch_news_curl(term, source_url, source_name)
            # Filter to relevant articles
            relevant = [
                item for item in items
                if any(t.lower() in item['title'].lower() for t in [symbol] + list(company_names))
            ]
            all_news.extend(relevant)
            if relevant:
                break  # Found relevant news for this source

    # Deduplicate
    seen = set()
    unique = []
    for item in all_news:
        key = item['title'].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:25]


# ============================================================================
# GROQ LLM ANALYSIS
# ============================================================================

def _get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return Groq(api_key=api_key)


def _analyze_with_ai(symbol: str, company_name: str, news_items: List[Dict]) -> Dict:
    """Use Groq (Llama 3.3 70B) for sentiment analysis."""
    if not GROQ_AVAILABLE:
        return _fallback_analysis(news_items)

    current_date = datetime.now().strftime('%Y-%m-%d')

    news_text = "\n".join([
        f"• [{item.get('date', 'unknown')}] [{item.get('source', 'Unknown')}] {item['title']}"
        for item in news_items[:15]
    ]) if news_items else "No recent news found."

    prompt = f"""You are a BALANCED Pakistani stock market analyst. Today's date is {current_date}.

CRITICAL RULES:
1. Only cite facts from the provided news headlines
2. Never invent or hallucinate data
3. Use 0 for sentiment_score if unclear
4. Be appropriately uncertain given sparse data

Analyze the following news about {symbol} ({company_name}):

{news_text}

RESPOND IN JSON FORMAT ONLY:
{{
    "sentiment_score": <float from -1.0 to +1.0, use 0 if unclear>,
    "signal": "<BUY|HOLD|SELL>",
    "confidence": <float 0.0-1.0, lower if news is sparse or old>,
    "key_events": ["ONLY list events that appear verbatim in headlines above"],
    "price_impact": {{
        "estimate": "<use 'unclear' unless there is very specific financial data>",
        "timeframe": "<unclear if not specified in news>",
        "reasoning": "<brief reasoning based ONLY on provided headlines>"
    }},
    "risks": ["only risks mentioned or implied in the headlines"],
    "catalysts": ["ONLY catalysts explicitly mentioned in headlines"],
    "data_quality": "<good|limited|poor>",
    "summary": "<2-3 factual sentences ONLY referencing the actual headlines>"
}}

Return ONLY valid JSON."""

    try:
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1024,
            temperature=0.05,
        )
        result = json.loads(completion.choices[0].message.content.strip())
        result['model'] = 'llama-3.3-70b-versatile'
        result['analyzed_at'] = datetime.now().isoformat()

        # Map signal
        signal_map = {'BUY': 'BULLISH', 'HOLD': 'NEUTRAL', 'SELL': 'BEARISH'}
        result['signal_simple'] = signal_map.get(result.get('signal', 'HOLD'), 'NEUTRAL')

        return result
    except Exception as e:
        logger.error(f"Groq analysis error for {symbol}: {e}")
        return _fallback_analysis(news_items)


def _fallback_analysis(news_items: List[Dict]) -> Dict:
    """Keyword-based fallback when Groq is unavailable."""
    text = ' '.join([item.get('title', '') for item in news_items]).lower()

    bullish = sum(1 for w in ['profit', 'growth', 'dividend', 'acquire', 'expansion', 'record', 'surge'] if w in text)
    bearish = sum(1 for w in ['loss', 'decline', 'drop', 'fraud', 'investigation', 'shutdown'] if w in text)

    if bullish > bearish:
        score, signal = min(0.5, bullish * 0.15), 'BULLISH'
    elif bearish > bullish:
        score, signal = max(-0.5, -bearish * 0.15), 'BEARISH'
    else:
        score, signal = 0.0, 'NEUTRAL'

    return {
        'sentiment_score': score,
        'signal': signal,
        'signal_simple': signal,
        'confidence': 0.3,
        'key_events': [],
        'price_impact': {'estimate': 'unclear', 'timeframe': 'unclear', 'reasoning': 'Keyword analysis only'},
        'summary': 'Analysis based on keyword matching (AI unavailable)',
        'model': 'fallback',
        'analyzed_at': datetime.now().isoformat()
    }


# ============================================================================
# MAIN API
# ============================================================================

def get_stock_sentiment(symbol: str, use_cache: bool = True) -> Dict:
    """Get sentiment from pre-existing cached news JSON files only."""
    symbol = symbol.upper()
    company_names = STOCK_COMPANIES.get(symbol, (symbol,))
    company_name = company_names[0]

    logger.info(f"Sentiment analysis: {symbol} ({company_name})")

    # Only read from existing cache files — no live fetching
    cache_path = _get_cache_path(symbol)
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            logger.info(f"Loaded cached sentiment for {symbol} ({cached.get('news_count', 0)} news items)")
            return cached
        except Exception as e:
            logger.error(f"Failed to read cache for {symbol}: {e}")

    # No cache file exists — return neutral placeholder
    return {
        'symbol': symbol,
        'company': company_name,
        'news_count': 0,
        'news_items': [],
        'sentiment_score': 0.0,
        'signal': 'NEUTRAL',
        'signal_simple': 'NEUTRAL',
        'confidence': 0.0,
        'key_events': [],
        'price_impact': {'estimate': 'unclear', 'timeframe': 'unclear', 'reasoning': 'No cached news available'},
        'summary': 'No cached news data available for this stock',
        'model': 'cache-only',
        'analyzed_at': datetime.now().isoformat(),
        'signal_emoji': '🟡',
    }


def get_sentiment_score_for_model(symbol: str, use_cache: bool = True) -> Dict:
    """
    Get sentiment features suitable for ML model integration.

    Returns:
        news_bias: -1 to +1 (bearish to bullish)
        news_volume: 0-1 normalized
        news_recency: 0-1 (0=old/no news, 1=very recent)
        available: bool
    """
    NEUTRAL = {'news_bias': 0.0, 'news_volume': 0.5, 'news_recency': 0.5, 'available': False}

    try:
        result = get_stock_sentiment(symbol, use_cache=use_cache)
        if result.get('error'):
            return NEUTRAL

        sentiment = result.get('sentiment_score', 0)
        signal = result.get('signal', 'NEUTRAL')
        if sentiment == 0:
            if signal in ['BUY', 'BULLISH']:
                sentiment = 0.3
            elif signal in ['SELL', 'BEARISH']:
                sentiment = -0.3

        news_items = result.get('news_items', [])
        news_volume = min(len(news_items) / 10.0, 1.0)

        news_recency = 0.5
        if news_items:
            dates = []
            for item in news_items:
                date_str = item.get('date', '')
                if date_str:
                    try:
                        d = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        dates.append(d)
                    except ValueError:
                        pass
            if dates:
                most_recent = max(dates)
                days_old = (datetime.now() - most_recent).days
                news_recency = max(0, 1.0 - (days_old / 7.0))

        return {
            'news_bias': round(sentiment, 4),
            'news_volume': round(news_volume, 4),
            'news_recency': round(news_recency, 4),
            'available': True
        }
    except Exception as e:
        logger.warning(f"Sentiment score error for {symbol}: {e}")
        return NEUTRAL
