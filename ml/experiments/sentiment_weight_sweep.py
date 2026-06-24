from pathlib import Path

import pandas as pd
import xgboost as xgb

import features.relevance as relevance
from features.sentiment import score_headlines
from models.baseline_xgboost import (
    FEATURE_COLUMNS,
    PUBLIC_TICKERS,
    fetch_benchmark,
    prepare_dataset,
)
from models.significance import evaluate_with_significance, format_significance

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
SENTIMENT_COLUMNS = ["avg_sentiment", "headline_count", "had_news"]


def load_scored_headlines(ticker: str) -> pd.DataFrame:
    """Score each ticker's cached raw headlines once with FinBERT.

    The expensive part (model inference) doesn't depend on the
    relevance weight -- only the daily aggregation step does -- so
    scoring once and reusing across the whole sweep avoids re-running
    FinBERT for every weight value tested.
    """
    raw_path = CACHE_DIR / f"{ticker}_news_raw.csv"
    news = pd.read_csv(raw_path, parse_dates=["date"])
    news["date"] = news["date"].dt.date
    news = news.dropna(subset=["headline"])

    scored = score_headlines(news["headline"].tolist())
    scored["date"] = news["date"].values
    return scored


def mentions_mask(scored: pd.DataFrame, ticker: str) -> pd.Series:
    terms = [ticker.lower()] + relevance.COMPANY_ALIASES.get(ticker, [])
    pattern = "|".join(terms)
    return scored["headline"].str.lower().str.contains(pattern, regex=True)


def daily_sentiment_with_weight(
    scored: pd.DataFrame, mentions: pd.Series, weight: float
) -> pd.DataFrame:
    w = mentions.map({True: 1.0, False: weight}).to_numpy()
    weighted_score = scored["sentiment_score"].to_numpy() * w

    df = pd.DataFrame(
        {"date": scored["date"].to_numpy(), "weighted_score": weighted_score, "weight": w}
    )
    daily = df.groupby("date").apply(
        lambda g: pd.Series(
            {
                "avg_sentiment": g["weighted_score"].sum() / g["weight"].sum(),
                "headline_count": len(g),
            }
        ),
        include_groups=False,
    )
    daily.index = pd.to_datetime(daily.index)
    return daily


def run_sweep(
    horizon: int = 7, weights: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
):
    benchmark = fetch_benchmark()

    scored_by_ticker = {}
    mentions_by_ticker = {}
    for ticker in PUBLIC_TICKERS:
        scored = load_scored_headlines(ticker)
        scored_by_ticker[ticker] = scored
        mentions_by_ticker[ticker] = mentions_mask(scored, ticker)
        print(f"Scored {len(scored)} headlines for {ticker}")

    target_col = f"target_{horizon}d"
    feature_cols = FEATURE_COLUMNS + SENTIMENT_COLUMNS

    print(f"\n--- Sentiment weight sweep, {horizon}-day horizon ---")
    for weight in weights:
        frames = []
        for ticker in PUBLIC_TICKERS:
            daily = daily_sentiment_with_weight(
                scored_by_ticker[ticker], mentions_by_ticker[ticker], weight
            )
            data = prepare_dataset(ticker, horizon, benchmark=benchmark)
            merged = data.join(daily, how="inner")
            merged["had_news"] = merged["headline_count"].notna().astype(int)
            merged["avg_sentiment"] = merged["avg_sentiment"].fillna(0)
            merged["headline_count"] = merged["headline_count"].fillna(0)
            merged["ticker"] = ticker
            frames.append(merged)
        pooled = pd.concat(frames).sort_index()

        unique_dates = pooled.index.unique().sort_values()
        cutoff_date = unique_dates[int(len(unique_dates) * 0.8)]
        train = pooled[pooled.index < cutoff_date]
        test = pooled[pooled.index >= cutoff_date]

        X_train, y_train = train[feature_cols], train[target_col]
        X_test, y_test = test[feature_cols], test[target_col]

        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric="logloss"
        )
        model.fit(X_train, y_train)

        result = evaluate_with_significance(y_test, model.predict(X_test), test["ticker"])
        print(f"weight={weight}: {format_significance(result)}")


if __name__ == "__main__":
    run_sweep()
