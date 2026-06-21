from pathlib import Path

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score

from models.baseline_xgboost import (
    FEATURE_COLUMNS,
    PUBLIC_TICKERS,
    explain_latest,
    prepare_dataset,
)

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

SENTIMENT_COLUMNS = ["avg_sentiment", "headline_count", "had_news"]


def load_sentiment(ticker: str) -> pd.DataFrame:
    path = CACHE_DIR / f"{ticker}_sentiment_filtered.csv"
    sentiment = pd.read_csv(path, index_col="date", parse_dates=True)
    return sentiment


def prepare_dataset_with_sentiment(ticker: str, horizon: int) -> pd.DataFrame:
    """Merge technicals+target rows with cached daily sentiment.

    Sentiment only exists for days that had news (and only within
    Finnhub's free-tier lookback, see docs/JOURNAL.mdx), so this is
    a left join: missing sentiment becomes neutral (0) with a
    had_news=0 flag, rather than dropping those rows. Rows outside
    the sentiment cache's date range entirely are dropped, since we
    want a fair comparison against the same window.
    """
    data = prepare_dataset(ticker, horizon)
    sentiment = load_sentiment(ticker)

    merged = data.join(sentiment, how="inner")
    merged["had_news"] = merged["headline_count"].notna().astype(int)
    merged["avg_sentiment"] = merged["avg_sentiment"].fillna(0)
    merged["headline_count"] = merged["headline_count"].fillna(0)

    return merged


def train_and_eval(pooled: pd.DataFrame, feature_columns: list[str], horizon: int):
    target_col = f"target_{horizon}d"
    unique_dates = pooled.index.unique().sort_values()
    cutoff_date = unique_dates[int(len(unique_dates) * 0.8)]

    train = pooled[pooled.index < cutoff_date]
    test = pooled[pooled.index >= cutoff_date]

    X_train, y_train = train[feature_columns], train[target_col]
    X_test, y_test = test[feature_columns], test[target_col]

    model = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric="logloss"
    )
    model.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test))
    majority_baseline = max(y_test.mean(), 1 - y_test.mean())

    return model, accuracy, majority_baseline, X_test, cutoff_date, len(test)


if __name__ == "__main__":
    horizon = 7

    frames = []
    for ticker in PUBLIC_TICKERS:
        merged = prepare_dataset_with_sentiment(ticker, horizon)
        merged["ticker"] = ticker
        frames.append(merged)
    pooled = pd.concat(frames).sort_index()

    print(f"Pooled rows with matching sentiment data: {len(pooled)}")
    print(f"Date range: {pooled.index.min().date()} to {pooled.index.max().date()}")

    print("\n--- Technicals only (same window) ---")
    _, acc_base, maj_base, _, cutoff, n_test = train_and_eval(
        pooled, FEATURE_COLUMNS, horizon
    )
    print(f"Test starts {cutoff.date()}, {n_test} test rows")
    print(f"Majority baseline: {maj_base:.3f}")
    print(f"Accuracy: {acc_base:.3f}")

    print("\n--- Technicals + sentiment ---")
    model, acc_sent, maj_sent, X_test, cutoff, n_test = train_and_eval(
        pooled, FEATURE_COLUMNS + SENTIMENT_COLUMNS, horizon
    )
    print(f"Test starts {cutoff.date()}, {n_test} test rows")
    print(f"Majority baseline: {maj_sent:.3f}")
    print(f"Accuracy: {acc_sent:.3f}")

    print(f"\nDelta vs technicals-only: {acc_sent - acc_base:+.3f}")

    print("\nTop SHAP features for the most recent prediction (with sentiment):")
    for item in explain_latest(model, X_test):
        print(f"  {item['feature']}: {item['shap_value']}")
