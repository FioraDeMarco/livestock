import os
import time
from datetime import date, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://finnhub.io/api/v1"
REQUEST_DELAY_SECONDS = 1.1  # free tier allows 60/min; stay under that


def _api_key() -> str:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY is not set (check ml/.env)")
    return key


def fetch_company_news(ticker: str, days_back: int = 365) -> pd.DataFrame:
    """Fetch headlines for a ticker over the last `days_back` days.

    Finnhub's free tier only retains ~12-14 months of company news
    (confirmed by direct testing, see docs/JOURNAL.mdx), so requesting
    more than that just returns fewer rows, not an error. Queried in
    weekly chunks since a single year-long request risks the response
    being capped or truncated.

    The token is sent as a header, not a query param — `requests`
    includes the full request URL in HTTPError messages, which would
    otherwise leak the key into any logs/output that capture the error.
    """
    headers = {"X-Finnhub-Token": _api_key()}
    end = date.today()
    start = end - timedelta(days=days_back)

    rows = []
    chunk_start = start
    while chunk_start < end:
        chunk_end = min(chunk_start + timedelta(days=7), end)
        for attempt in range(4):
            res = requests.get(
                f"{BASE_URL}/company-news",
                params={
                    "symbol": ticker,
                    "from": chunk_start.isoformat(),
                    "to": chunk_end.isoformat(),
                },
                headers=headers,
            )
            if res.status_code != 429:
                break
            wait = 15 * (attempt + 1)
            time.sleep(wait)
        res.raise_for_status()
        rows.extend(res.json())
        chunk_start = chunk_end
        time.sleep(REQUEST_DELAY_SECONDS)

    if not rows:
        return pd.DataFrame(columns=["date", "headline"])

    news = pd.DataFrame(rows)
    news["date"] = pd.to_datetime(news["datetime"], unit="s").dt.date
    news = news.dropna(subset=["headline"])
    return news[["date", "headline"]].drop_duplicates()


def fetch_ticker_news(ticker: str, days_back: int = 365) -> pd.DataFrame:
    """Company news + sector ETF news for a ticker, merged and deduplicated.

    Fetching only company-tagged headlines misses industry-wide moves
    (e.g. "chip sector selloff hits semis") that don't name the company
    directly. The sector ETF's news feed captures those. Headlines are
    tagged with a `source` column ("company" or "sector") so downstream
    relevance weighting can treat them differently.
    """
    from features.relevance import SECTOR_ETF

    company_news = fetch_company_news(ticker, days_back=days_back)
    company_news["source"] = "company"

    sector_etf = SECTOR_ETF.get(ticker)
    if sector_etf:
        time.sleep(REQUEST_DELAY_SECONDS)
        sector_news = fetch_company_news(sector_etf, days_back=days_back)
        sector_news["source"] = "sector"
        combined = pd.concat([company_news, sector_news])
    else:
        combined = company_news

    return combined.drop_duplicates(subset=["date", "headline"]).reset_index(drop=True)


if __name__ == "__main__":
    news = fetch_ticker_news("NVDA", days_back=30)
    print(f"{len(news)} headlines in the last 30 days (company + sector)")
    print(news.groupby("source").size())
    print(news.head(10))
