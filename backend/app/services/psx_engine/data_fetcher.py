"""PSX historical data fetcher - extracted from stock_analyzer_fixed.py"""

import json
import subprocess
import re
import pandas as pd
import asyncio
from datetime import datetime
from pathlib import Path


def fetch_month_data(symbol: str, month: int, year: int):
    """Fetch historical data for a specific month from PSX DPS API."""
    url = "https://dps.psx.com.pk/historical"
    post_data = f"month={month}&year={year}&symbol={symbol}"

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', url, '-d', post_data],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None


def parse_html_table(html):
    """Parse HTML table to extract OHLCV data."""
    rows = re.findall(r'<tr>.*?</tr>', html, re.DOTALL)
    data = []

    for row in rows:
        cells = re.findall(r'<td[^>]*>([^<]+)</td>', row)

        if len(cells) >= 6:
            try:
                date_str = cells[0].strip()
                date_obj = datetime.strptime(date_str, "%b %d, %Y")

                open_price = float(cells[1].strip().replace(',', ''))
                high_price = float(cells[2].strip().replace(',', ''))
                low_price = float(cells[3].strip().replace(',', ''))
                close_price = float(cells[4].strip().replace(',', ''))
                volume = float(cells[5].strip().replace(',', ''))

                data.append({
                    'Date': date_obj.strftime('%Y-%m-%d'),
                    'Open': open_price,
                    'High': high_price,
                    'Low': low_price,
                    'Close': close_price,
                    'Volume': volume
                })
            except Exception:
                continue

    return data


def calculate_basic_indicators(data):
    """Calculate basic technical indicators."""
    if not data or len(data) == 0:
        return []

    df = pd.DataFrame(data)

    if 'Date' not in df.columns:
        return []

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Price_Change'] = df['Close'].diff()
    df['Price_Change_Pct'] = df['Close'].pct_change() * 100
    df['Volume_Change'] = df['Volume'].diff()

    for window in [20, 50, 200]:
        df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()

    records = df.to_dict('records')
    for record in records:
        if 'Date' in record and pd.notna(record['Date']):
            record['Date'] = record['Date'].strftime('%Y-%m-%d')
    return records


async def fetch_historical_data(symbol: str, progress_callback=None):
    """
    Fetch historical OHLCV data for a PSX stock.

    Args:
        symbol: PSX ticker symbol (e.g., 'LUCK')
        progress_callback: Optional callable(symbol, message) for status updates

    Returns:
        list of dicts with Date, Open, High, Low, Close, Volume + basic indicators
    """
    symbol = symbol.upper()
    all_data = []
    current_year = datetime.now().year
    current_month = datetime.now().month
    start_year = 2020

    total_months = (current_year - start_year) * 12 + current_month
    fetched = 0

    if progress_callback:
        progress_callback(symbol, f"Fetching historical data from {start_year} to {current_year}...")

    for year in range(start_year, current_year + 1):
        end_month = current_month if year == current_year else 12

        for month in range(1, end_month + 1):
            fetched += 1

            html = fetch_month_data(symbol, month, year)

            if html:
                month_data = parse_html_table(html)
                if month_data:
                    all_data.extend(month_data)

            await asyncio.sleep(0.05)

    if not all_data:
        raise ValueError(f"No historical data found for symbol {symbol}")

    if progress_callback:
        progress_callback(symbol, f"Fetched {len(all_data)} trading days. Calculating indicators...")

    all_data = calculate_basic_indicators(all_data)

    if not all_data:
        raise ValueError(f"Failed to process data for symbol {symbol}")

    # Deduplicate by date
    seen_dates = set()
    unique_data = []
    for record in all_data:
        date_key = record.get('Date', '')
        if date_key and date_key not in seen_dates:
            seen_dates.add(date_key)
            unique_data.append(record)

    unique_data.sort(key=lambda x: x.get('Date', ''))

    if progress_callback:
        progress_callback(symbol, f"Ready: {len(unique_data)} records for {symbol}")

    return unique_data
