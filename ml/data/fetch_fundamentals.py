"""
Fetch current fundamental metrics from Finnhub for live inference and
Claude synthesis context. Not used in historical model training (we only
have current-snapshot fundamentals, not point-in-time history).

Finnhub's /stock/metric endpoint is on the free tier and returns ~100
ratios computed from reported financials. We pull the handful that are
most informative for stock direction: valuation (P/E, P/B), profitability
(ROE, net margin), and growth (revenue, EPS growth YoY).
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://finnhub.io/api/v1"


def _api_key() -> str:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY is not set")
    return key


def fetch_fundamentals(ticker: str) -> dict:
    """
    Current fundamental metrics for a ticker from Finnhub.
    Returns a flat dict; values are float or None if unavailable.

    Keys:
        pe_ttm            Trailing 12-month P/E ratio
        pb                Price-to-book (most recent quarter)
        roe_ttm           Return on equity TTM (%)
        revenue_growth    Revenue growth YoY TTM (%)
        eps_growth        EPS growth YoY TTM (%)
        net_margin        Net profit margin TTM (%)
    """
    res = requests.get(
        f"{BASE_URL}/stock/metric",
        params={"metric": "all", "symbol": ticker},
        headers={"X-Finnhub-Token": _api_key()},
        timeout=10,
    )
    res.raise_for_status()
    metric = res.json().get("metric", {})

    return {
        "pe_ttm":         metric.get("peTTM"),
        "pb":             metric.get("pbQuarterly"),
        "roe_ttm":        metric.get("roeTTM"),
        "revenue_growth": metric.get("revenueGrowthTTMYoy"),
        "eps_growth":     metric.get("epsGrowthTTMYoy"),
        "net_margin":     metric.get("netMarginTTM"),
    }


def fundamentals_for_prompt(ticker: str, fundamentals: dict | None = None) -> str:
    """
    Format fundamentals as a concise string for the Claude synthesis prompt.
    Fetches fresh data if fundamentals dict not provided.
    Every number is sourced from Finnhub — never from Claude's memory.
    """
    if fundamentals is None:
        try:
            fundamentals = fetch_fundamentals(ticker)
        except Exception:
            return ""

    def fmt(val, suffix=""):
        return f"{val:.1f}{suffix}" if val is not None else "n/a"

    lines = [
        f"- Trailing P/E: {fmt(fundamentals.get('pe_ttm'), 'x')}",
        f"- Price/Book: {fmt(fundamentals.get('pb'), 'x')}",
        f"- ROE (TTM): {fmt(fundamentals.get('roe_ttm'), '%')}",
        f"- Revenue growth YoY: {fmt(fundamentals.get('revenue_growth'), '%')}",
        f"- EPS growth YoY: {fmt(fundamentals.get('eps_growth'), '%')}",
    ]
    active = [l for l in lines if "n/a" not in l]
    if not active:
        return ""
    return f"Fundamentals for {ticker} (source: Finnhub):\n" + "\n".join(active)


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    f = fetch_fundamentals(ticker)
    print(f"\n{ticker} fundamentals:")
    for k, v in f.items():
        print(f"  {k}: {v}")
    print(f"\nPrompt snippet:\n{fundamentals_for_prompt(ticker, f)}")
