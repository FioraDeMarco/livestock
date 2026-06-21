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
        res = requests.get(
            f"{BASE_URL}/company-news",
            params={
                "symbol": ticker,
                "from": chunk_start.isoformat(),
                "to": chunk_end.isoformat(),
            },
            headers=headers,
        )
        if res.status_code == 429:
            time.sleep(5)
            res = requests.get(res.url, headers=headers)
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


if __name__ == "__main__":
    news = fetch_company_news("NVDA", days_back=30)
    print(f"{len(news)} headlines in the last 30 days")
    print(news.head())
