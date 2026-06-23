import time
from pathlib import Path

from data.fetch_news import fetch_ticker_news
from features.sentiment import daily_sentiment
from models.baseline_xgboost import PUBLIC_TICKERS

CACHE_DIR = Path(__file__).parent / "cache"


def build_cache(tickers: list[str] = PUBLIC_TICKERS, days_back: int = 365):
    CACHE_DIR.mkdir(exist_ok=True)

    for ticker in tickers:
        out_path = CACHE_DIR / f"{ticker}_sentiment.csv"
        start = time.time()

        news = fetch_ticker_news(ticker, days_back=days_back)
        daily = daily_sentiment(news)
        daily.to_csv(out_path)

        elapsed = time.time() - start
        print(
            f"{ticker}: {len(news)} headlines -> {len(daily)} days "
            f"({elapsed:.0f}s) -> {out_path}"
        )


if __name__ == "__main__":
    build_cache()
