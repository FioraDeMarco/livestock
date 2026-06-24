from pathlib import Path

import pandas as pd
import xgboost as xgb

from models.baseline_xgboost import (
    FEATURE_COLUMNS,
    PUBLIC_TICKERS,
    explain_latest,
    prepare_dataset,
)
from models.significance import evaluate_with_significance, format_significance, mcnemar_test

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

    return model, X_test, y_test, test["ticker"], cutoff_date


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
    model_base, X_test_base, y_test, ticker_test, cutoff = train_and_eval(
        pooled, FEATURE_COLUMNS, horizon
    )
    pred_base = model_base.predict(X_test_base)
    result_base = evaluate_with_significance(y_test, pred_base, ticker_test)
    print(f"Test starts {cutoff.date()}")
    print(format_significance(result_base))

    print("\n--- Technicals + sentiment ---")
    model_sent, X_test_sent, y_test_sent, ticker_test_sent, cutoff = train_and_eval(
        pooled, FEATURE_COLUMNS + SENTIMENT_COLUMNS, horizon
    )
    pred_sent = model_sent.predict(X_test_sent)
    result_sent = evaluate_with_significance(y_test_sent, pred_sent, ticker_test_sent)
    print(f"Test starts {cutoff.date()}")
    print(format_significance(result_sent))

    print(
        f"\nDelta vs technicals-only: {result_sent['accuracy'] - result_base['accuracy']:+.3f}"
    )
    # Direct paired comparison: does adding sentiment change correctness on
    # the SAME rows often enough to be more than noise? (Same cutoff/rows
    # for both models since they're trained on the same pooled dataframe.)
    base_correct = pred_base == y_test.to_numpy()
    sent_correct = pred_sent == y_test_sent.to_numpy()
    head_to_head_p = mcnemar_test(sent_correct, base_correct)
    print(
        f"Technicals+sentiment vs technicals-only, paired comparison: "
        f"p={head_to_head_p:.3f} "
        f"({'SIGNIFICANT' if head_to_head_p < 0.05 else 'not significant'})"
    )

    print("\nTop SHAP features for the most recent prediction (with sentiment):")
    for item in explain_latest(model_sent, X_test_sent):
        print(f"  {item['feature']}: {item['shap_value']}")
