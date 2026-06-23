import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import accuracy_score

from data.fetch_historical import fetch_historical
from features.targets import add_targets
from features.technical_indicators import add_technical_indicators
from models.significance import evaluate_with_significance, format_significance

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

FEATURE_COLUMNS = [
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
]


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


def latest_features(ticker: str, benchmark: pd.DataFrame | None = None) -> pd.Series:
    """Most recent feature row, for live inference.

    Unlike `prepare_dataset`, this doesn't need a target column —
    today's row has no label yet (that's the point of predicting it),
    so dropping rows with a missing target would also drop the very
    row we want to predict on.
    """
    if benchmark is None:
        benchmark = fetch_benchmark()
    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = build_features(df, benchmark)
    return df[FEATURE_COLUMNS].dropna().iloc[-1]


def prepare_dataset(
    ticker: str, horizon: int, benchmark: pd.DataFrame | None = None
) -> pd.DataFrame:
    if benchmark is None:
        benchmark = fetch_benchmark()
    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = add_targets(df, horizons=[horizon])
    df = build_features(df, benchmark)

    target_col = f"target_{horizon}d"
    columns = FEATURE_COLUMNS + [target_col]
    return df[columns].dropna()


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
    return pooled


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
