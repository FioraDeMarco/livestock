from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import accuracy_score

from data.fetch_historical import fetch_historical
from features.targets import add_targets
from features.technical_indicators import add_technical_indicators
from models.significance import evaluate_with_significance, format_significance

SENTIMENT_CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

PUBLIC_TICKERS = [
    # Tech / semiconductors
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "TSLA", "AMD",
    # Financials
    "JPM", "GS",
    # Healthcare
    "JNJ", "UNH",
    # Energy
    "XOM", "CVX",
    # Consumer staples
    "WMT", "COST",
    # Consumer discretionary
    "HD",
    # Industrials
    "CAT",
]
BENCHMARK_TICKER = "SPY"

# Base features: absolute-level signals for this ticker in isolation.
FEATURE_COLUMNS_BASE = [
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "close_to_sma20",
    "close_to_sma50",
    "close_to_sma200",
    "daily_return",
    "realized_vol_20",
    "atr_pct_14",
    "relative_volume_20",
    "excess_return",
    "relative_sma20",
    "avg_sentiment",
]

# Cross-sectional rank features: percentile rank of each signal within the 18-stock
# universe on the same date. "RSI rank 0.9" = higher RSI than 90% of peers today.
# Absolute levels answer "is this stock overbought?"; ranks answer "is it overbought
# *relative to peers*?" — a different, market-neutral signal that the absolute value
# can't express on its own.
CROSS_SECTIONAL_RANK_FEATURES = [
    "rsi_14",
    "daily_return",
    "excess_return",
    "realized_vol_20",
    "close_to_sma20",
    "relative_volume_20",
]

FEATURE_COLUMNS = FEATURE_COLUMNS_BASE + [
    f"{f}_xrank" for f in CROSS_SECTIONAL_RANK_FEATURES
]


def _load_sentiment(ticker: str) -> pd.Series:
    """Load pre-built daily avg_sentiment for a ticker from cache.
    Returns a Series indexed by date, or an empty Series if uncached.
    NaN-filled rows (days with no news) are treated as 0 (neutral).
    """
    path = SENTIMENT_CACHE_DIR / f"{ticker}_sentiment.csv"
    if not path.exists():
        return pd.Series(dtype=float, name="avg_sentiment")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df["avg_sentiment"]


def fetch_benchmark(symbol: str = BENCHMARK_TICKER) -> pd.DataFrame:
    """Market benchmark OHLCV, for market-relative features. Fetch once
    and share across tickers -- the benchmark series is the same
    regardless of which stock we're building features for."""
    return fetch_historical(symbol)


def build_features(df: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    """Turn raw indicators into scale-invariant features XGBoost can
    generalize from (relative distances/returns instead of raw price
    levels, which just encode "what year is it"), plus market-relative
    features.

    With 6 correlated mega-cap tech tickers pooled together, a lot of
    daily_return's variance is just "the market moved that day" -- the
    model previously had no feature that separated stock-specific
    movement from a market-wide move on the same date.
    """
    out = df.copy()

    out["close_to_sma20"] = out["close"] / out["sma_20"] - 1
    out["close_to_sma50"] = out["close"] / out["sma_50"] - 1
    out["close_to_sma200"] = out["close"] / out["sma_200"] - 1
    out["daily_return"] = out["close"].pct_change()

    bench_return = benchmark["close"].pct_change().reindex(out.index)
    bench_sma20_ratio = (
        benchmark["close"] / benchmark["close"].rolling(window=20).mean() - 1
    ).reindex(out.index)

    out["excess_return"] = out["daily_return"] - bench_return
    out["relative_sma20"] = out["close_to_sma20"] - bench_sma20_ratio

    return out


def latest_features_cross_sectional(
    tickers: list[str] = PUBLIC_TICKERS,
    benchmark: pd.DataFrame | None = None,
) -> dict[str, pd.Series]:
    """Latest feature row for all tickers, with cross-sectional ranks computed.

    Cross-sectional rank features require the full peer universe on the same date —
    you can't compute "this stock's RSI rank among 18 peers" from one ticker's data
    alone. This fetches all tickers, stacks the most recent row from each, computes
    ranks across the peer universe, and returns a dict so callers can look up any
    individual ticker without repeating the fetch.
    """
    if benchmark is None:
        benchmark = fetch_benchmark()

    rows: dict[str, pd.Series] = {}
    for ticker in tickers:
        df = fetch_historical(ticker)
        df = add_technical_indicators(df)
        df = build_features(df, benchmark)
        sentiment = _load_sentiment(ticker)
        if not sentiment.empty:
            df = df.join(sentiment, how="left")
        df["avg_sentiment"] = (
            df.get("avg_sentiment", pd.Series(0.0, index=df.index)).fillna(0.0)
        )
        rows[ticker] = df[FEATURE_COLUMNS_BASE].dropna().iloc[-1]

    # Stack into one row per ticker, then rank across the peer cross-section.
    cross = pd.DataFrame(rows).T
    for feat in CROSS_SECTIONAL_RANK_FEATURES:
        cross[f"{feat}_xrank"] = cross[feat].rank(pct=True)

    return {ticker: cross.loc[ticker, FEATURE_COLUMNS] for ticker in tickers}


def latest_features(ticker: str, benchmark: pd.DataFrame | None = None) -> pd.Series:
    """Most recent feature row for a single ticker, with cross-sectional ranks.

    Thin wrapper around latest_features_cross_sectional. For repeated calls
    (e.g. serving many tickers from one request), call the cross-sectional
    version directly and look up each ticker from the returned dict.
    """
    return latest_features_cross_sectional([ticker] + PUBLIC_TICKERS, benchmark)[ticker]


def prepare_dataset(
    ticker: str, horizon: int, benchmark: pd.DataFrame | None = None
) -> pd.DataFrame:
    if benchmark is None:
        benchmark = fetch_benchmark()
    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = add_targets(df, horizons=[horizon])
    df = build_features(df, benchmark)

    sentiment = _load_sentiment(ticker)
    if not sentiment.empty:
        df = df.join(sentiment, how="left")
    df["avg_sentiment"] = df.get("avg_sentiment", pd.Series(0.0, index=df.index)).fillna(0.0)

    target_col = f"target_{horizon}d"
    # Only select base features here — cross-sectional rank columns (_xrank) are
    # computed in prepare_pooled_dataset after all tickers are stacked together.
    columns = FEATURE_COLUMNS_BASE + [target_col]
    return df[columns].dropna()


def _add_cross_sectional_ranks(pooled: pd.DataFrame) -> pd.DataFrame:
    """Append cross-sectional rank columns to a pooled multi-ticker DataFrame.

    For each date, ranks each ticker's feature value as a percentile (0–1)
    within the peer universe. Requires the DataFrame to be indexed by date
    with a 'ticker' column so groupby(date) gives the right cross-section.
    """
    rank_cols = {
        f"{feat}_xrank": pooled.groupby(level=0)[feat].rank(pct=True)
        for feat in CROSS_SECTIONAL_RANK_FEATURES
    }
    return pooled.assign(**rank_cols)


def prepare_pooled_dataset(
    tickers: list[str], horizon: int, since: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Pool feature/target rows across multiple tickers.

    A single ticker's daily history is small and heavily autocorrelated,
    especially at longer horizons where consecutive rows share most of
    their future window. Pooling tickers gives more rows and pushes the
    model toward patterns that hold across companies, not one company's
    idiosyncratic history.

    `since` restricts to rows on/after a date — used to build a baseline
    on the same window as sentiment data (which has much shorter history
    than price data), so a comparison isn't confounded by sample size.
    """
    benchmark = fetch_benchmark()

    frames = []
    for ticker in tickers:
        data = prepare_dataset(ticker, horizon, benchmark=benchmark)
        data["ticker"] = ticker
        frames.append(data)

    pooled = pd.concat(frames).sort_index()
    if since is not None:
        pooled = pooled[pooled.index >= since]

    # Compute cross-sectional ranks after all tickers are pooled together,
    # since ranking requires the full peer universe on each date.
    return _add_cross_sectional_ranks(pooled)


def train_pooled_model(
    tickers: list[str] = PUBLIC_TICKERS,
    horizon: int = 30,
    test_size: float = 0.2,
    since: pd.Timestamp | None = None,
):
    """Train on a date-based split across pooled tickers.

    Splitting by row fraction (like a single-ticker split) would let a
    train row from one ticker and a test row from another ticker share
    the same calendar date, leaking shared market conditions across the
    split. A single date cutoff applied to every ticker avoids that.
    """
    target_col = f"target_{horizon}d"
    pooled = prepare_pooled_dataset(tickers, horizon, since=since)

    unique_dates = pooled.index.unique().sort_values()
    cutoff_date = unique_dates[int(len(unique_dates) * (1 - test_size))]

    train = pooled[pooled.index < cutoff_date]
    test = pooled[pooled.index >= cutoff_date]

    X_train, y_train = train[FEATURE_COLUMNS], train[target_col]
    X_test, y_test = test[FEATURE_COLUMNS], test[target_col]

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test))
    majority_baseline = max(y_test.mean(), 1 - y_test.mean())

    return model, accuracy, majority_baseline, X_test, cutoff_date, y_test, test["ticker"]


def _default_xgb_model():
    return xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        eval_metric="logloss",
    )


def walk_forward_eval(
    tickers: list[str] = PUBLIC_TICKERS,
    horizon: int = 30,
    n_folds: int = 5,
    model_factory=_default_xgb_model,
) -> list[dict]:
    """Evaluate across several expanding-window folds instead of one
    train/test split.

    A single split is one noisy draw -- the journal shows the majority
    baseline itself swings from 54% to 77% depending on which window
    you happen to test on. Walk-forward shows the DISTRIBUTION of
    results across time: a real edge should turn up as small-but-
    consistently-positive across folds, not a coin-flip of some folds
    up and some sharply down.

    Each fold's test set is the next chronological chunk after an
    ever-larger training set -- fold i trains on chunks 0..i and tests
    on chunk i+1, so test sets never overlap and never precede their
    training data.
    """
    target_col = f"target_{horizon}d"
    pooled = prepare_pooled_dataset(tickers, horizon)

    unique_dates = pooled.index.unique().sort_values()
    chunks = np.array_split(unique_dates, n_folds + 1)

    results = []
    for i in range(n_folds):
        train_dates = pd.Index(np.concatenate(chunks[: i + 1]))
        test_dates = pd.Index(chunks[i + 1])

        train = pooled[pooled.index.isin(train_dates)]
        test = pooled[pooled.index.isin(test_dates)]

        X_train, y_train = train[FEATURE_COLUMNS], train[target_col]
        X_test, y_test = test[FEATURE_COLUMNS], test[target_col]

        model = model_factory()
        model.fit(X_train, y_train)

        result = evaluate_with_significance(y_test, model.predict(X_test), test["ticker"])
        result["fold"] = i
        result["train_start"] = train_dates.min().date()
        result["test_start"] = test_dates.min().date()
        result["test_end"] = test_dates.max().date()
        results.append(result)

    return results


def explain_latest(model: xgb.XGBClassifier, X: pd.DataFrame, top_n: int = 5):
    """Return the top SHAP feature contributions for the most recent row."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    latest = pd.Series(shap_values[-1], index=X.columns)
    top_features = latest.abs().sort_values(ascending=False).head(top_n)

    return [
        {"feature": name, "shap_value": round(float(latest[name]), 4)}
        for name in top_features.index
    ]


if __name__ == "__main__":
    horizon = 7
    model, accuracy, majority_baseline, X_test, cutoff_date, y_test, ticker_test = (
        train_pooled_model(horizon=horizon)
    )

    print(f"Pooled {horizon}-day direction model: {PUBLIC_TICKERS}")
    print(f"Test period starts: {cutoff_date.date()}, {len(X_test)} test rows")
    result = evaluate_with_significance(y_test, model.predict(X_test), ticker_test)
    print(format_significance(result))
    print("\nTop SHAP features for the most recent prediction:")
    for item in explain_latest(model, X_test):
        print(f"  {item['feature']}: {item['shap_value']}")

    print(f"\n--- Walk-forward evaluation, {horizon}-day horizon, 5 expanding folds ---")
    for fold_result in walk_forward_eval(horizon=horizon, n_folds=5):
        print(
            f"Fold {fold_result['fold']}: train from {fold_result['train_start']}, "
            f"test {fold_result['test_start']} to {fold_result['test_end']}"
        )
        print(f"  {format_significance(fold_result)}")
