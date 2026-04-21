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


def get_stock_data(ticker: str, period_days: int = 90) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        period_days: Number of days of historical data to fetch (bumped to 90
                     so RSI_14 and SMA_20 both have comfortable warm-up periods)

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
    Compute basic technical indicators: SMA, EMA, RSI, MACD, and daily return.

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

    # Added RSI_14 - useful for spotting overbought/oversold conditions
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # Added MACD (12/26 EMA crossover) and signal line - handy for momentum checks
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - ema_26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

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
     