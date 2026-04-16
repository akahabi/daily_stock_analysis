#!/usr/bin/env python3
"""Daily Stock Analysis - Main entry point.

Runs stock analysis for a list of tickers, computes technical indicators,
and outputs a summary report to stdout or a file.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from stock_analyzer import get_stock_data, compute_indicators, generate_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


DEFAULT_TICKERS = os.getenv("TICKERS", "AAPL,MSFT,GOOGL,AMZN,TSLA").split(",")
DEFAULT_PERIOD = os.getenv("ANALYSIS_PERIOD", "6mo")
DEFAULT_OUTPUT_DIR = os.getenv("OUTPUT_DIR", "reports")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run daily stock analysis and generate summary reports."
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help="Space-separated list of stock ticker symbols (default: from TICKERS env var).",
    )
    parser.add_argument(
        "--period",
        default=DEFAULT_PERIOD,
        choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        help="Historical data period to fetch (default: 6mo).",
    )
    parser.add_argument(
        "--output",
        choices=["stdout", "json", "both"],
        default="both",
        help="Output format: print to stdout, save JSON file, or both.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save JSON reports (default: reports/).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level.",
    )
    return parser.parse_args()


def analyze_ticker(ticker: str, period: str) -> dict:
    """Fetch data, compute indicators, and return summary for a single ticker."""
    logger.info("Analyzing %s over period %s", ticker, period)
    df = get_stock_data(ticker, period=period)
    if df is None or df.empty:
        logger.warning("No data returned for %s — skipping.", ticker)
        return {"ticker": ticker, "error": "No data available"}

    df = compute_indicators(df)
    summary = generate_summary(df, ticker=ticker)
    return summary


def save_report(results: list[dict], output_dir: str) -> Path:
    """Persist analysis results to a timestamped JSON file."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = out_path / f"stock_report_{timestamp}.json"

    with report_file.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)

    logger.info("Report saved to %s", report_file)
    return report_file


def main() -> int:
    args = parse_args()
    logging.getLogger().setLevel(args.log_level)

    tickers = [t.strip().upper() for t in args.tickers if t.strip()]
    if not tickers:
        logger.error("No tickers provided. Exiting.")
        return 1

    logger.info("Starting analysis for %d ticker(s): %s", len(tickers), ", ".join(tickers))

    results = []
    for ticker in tickers:
        try:
            result = analyze_ticker(ticker, args.period)
            results.append(result)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to analyze %s: %s", ticker, exc)
            results.append({"ticker": ticker, "error": str(exc)})

    if args.output in ("stdout", "both"):
        print(json.dumps(results, indent=2, default=str))

    if args.output in ("json", "both"):
        save_report(results, args.output_dir)

    errors = [r for r in results if "error" in r]
    if errors:
        logger.warning("%d ticker(s) had errors.", len(errors))

    logger.info("Analysis complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
