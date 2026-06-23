from pathlib import Path

from data.fetch_news import fetch_ticker_news
from models.baseline_xgboost import PUBLIC_TICKERS

CACHE_DIR = Path(__file__).parent / "cache"


def build_raw_news_cache(tickers: list[str] = PUBLIC_TICKERS, days_back: int = 365):
    """Cache raw headlines per ticker, decoupled from sentiment scoring.

    Lets us re-filter/re-score without re-hitting Finnhub every time we
    tune the relevance filter.
    """
    CACHE_DIR.mkdir(exist_ok=True)

    for ticker in tickers:
        out_path = CACHE_DIR / f"{ticker}_news_raw.csv"
        news = fetch_ticker_news(ticker, days_back=days_back)
        news.to_csv(out_path, index=False)
        print(f"{ticker}: {len(news)} headlines -> {out_path}")


if __name__ == "__main__":
    build_raw_news_cache()
