from pathlib import Path

import pandas as pd

from features.relevance import relevance_weight
from features.sentiment import daily_sentiment
from models.baseline_xgboost import PUBLIC_TICKERS

CACHE_DIR = Path(__file__).parent / "cache"


def build_filtered_cache(tickers: list[str] = PUBLIC_TICKERS):
    for ticker in tickers:
        raw_path = CACHE_DIR / f"{ticker}_news_raw.csv"
        out_path = CACHE_DIR / f"{ticker}_sentiment_filtered.csv"

        news = pd.read_csv(raw_path, parse_dates=["date"])
        news["date"] = news["date"].dt.date
        news = news.dropna(subset=["headline"])

        weights = relevance_weight(news, ticker)
        daily = daily_sentiment(news, weights=weights)
        daily.to_csv(out_path)

        direct_pct = (weights == 1.0).mean()
        print(
            f"{ticker}: {len(news)} headlines, {direct_pct:.0%} direct mentions "
            f"-> {len(daily)} days -> {out_path}"
        )


if __name__ == "__main__":
    build_filtered_cache()
