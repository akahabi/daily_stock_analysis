#!/usr/bin/env python3
"""
Daily Stock Analysis - Main Entry Point
Fetches, analyzes, and reports on stock data for configured tickers.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stock_analysis.log"),
    ],
)
logger = logging.getLogger(__name__)


def get_stock_data(ticker: str, period_days: int = 30) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        period_days: Number of days of historical data to fetch

    Returns:
        DataFrame with OHLCV data or None on failure
    """
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=period_days)
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date.strftime("%Y-%m-%d"),
                           end=end_date.strftime("%Y-%m-%d"))
        if df.empty:
            logger.warning(f"No data returned for ticker: {ticker}")
            return None
        logger.info(f"Fetched {len(df)} rows for {ticker}")
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basic technical indicators: SMA, EMA, and daily return.

    Args:
        df: DataFrame with at least a 'Close' column

    Returns:
        DataFrame with additional indicator columns
    """
    df = df.copy()
    df["SMA_5"] = df["Close"].rolling(window=5).mean()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    return df


def generate_summary(ticker: str, df: pd.DataFrame) -> dict:
    """
    Generate a summary dict for the latest trading day.

    Args:
        ticker: Stock ticker symbol
        df: DataFrame with computed indicators

    Returns:
        Dictionary with summary statistics
    """
    latest = df.iloc[-1]
    summary = {
        "ticker": ticker,
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "close": round(latest["Close"], 2),
        "volume": int(latest["Volume"]),
        "sma_5": round(latest["SMA_5"], 2) if pd.notna(latest["SMA_5"]) else None,
        "sma_20": round(latest["SMA_20"], 2) if pd.notna(latest["SMA_20"]) else None,
        "ema_12": round(latest["EMA_12"], 2) if pd.notna(latest["EMA_12"]) else None,
        "daily_return_pct": round(latest["Daily_Return"], 2) if pd.notna(latest["Daily_Return"]) else None,
    }
    return summary


def analyze_tickers(tickers: list[str]) -> list[dict]:
    """
    Run full analysis pipeline for a list of ticker symbols.

    Args:
        tickers: List of stock ticker symbols

    Returns:
        List of summary dictionaries
    """
    results = []
    for ticker in tickers:
        logger.info(f"Analyzing {ticker}...")
        df = get_stock_data(ticker)
        if df is None:
            continue
        df = compute_indicators(df)
        summary = generate_summary(ticker, df)
        results.append(summary)
        logger.info(f"Summary for {ticker}: {summary}")
    return results


if __name__ == "__main__":
    raw_tickers = os.getenv("TICKERS", "AAPL,MSFT,TSLA")
    ticker_list = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]
    logger.info(f"Starting daily analysis for: {ticker_list}")
    summaries = analyze_tickers(ticker_list)
    print("\n=== Daily Stock Analysis ===")
    for s in summaries:
        print(s)
