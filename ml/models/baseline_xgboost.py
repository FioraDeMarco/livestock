import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import accuracy_score

from data.fetch_historical import fetch_historical
from features.targets import add_targets
from features.technical_indicators import add_technical_indicators

PUBLIC_TICKERS = ["TSLA", "NVDA", "MSFT", "META", "AMZN", "GOOGL"]

FEATURE_COLUMNS = [
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "close_to_sma20",
    "close_to_sma50",
    "close_to_sma200",
    "daily_return",
    "volume_change",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw indicators into scale-invariant features XGBoost can
    generalize from (relative distances/returns instead of raw price
    levels, which just encode "what year is it")."""
    out = df.copy()

    out["close_to_sma20"] = out["close"] / out["sma_20"] - 1
    out["close_to_sma50"] = out["close"] / out["sma_50"] - 1
    out["close_to_sma200"] = out["close"] / out["sma_200"] - 1
    out["daily_return"] = out["close"].pct_change()
    out["volume_change"] = out["volume"].pct_change()

    return out


def latest_features(ticker: str) -> pd.Series:
    """Most recent feature row, for live inference.

    Unlike `prepare_dataset`, this doesn't need a target column —
    today's row has no label yet (that's the point of predicting it),
    so dropping rows with a missing target would also drop the very
    row we want to predict on.
    """
    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = build_features(df)
    return df[FEATURE_COLUMNS].dropna().iloc[-1]


def prepare_dataset(ticker: str, horizon: int) -> pd.DataFrame:
    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = add_targets(df, horizons=[horizon])
    df = build_features(df)

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
    frames = []
    for ticker in tickers:
        data = prepare_dataset(ticker, horizon)
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

    return model, accuracy, majority_baseline, X_test, cutoff_date


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
    horizon = 30
    model, accuracy, majority_baseline, X_test, cutoff_date = train_pooled_model(
        horizon=horizon
    )

    print(f"Pooled {horizon}-day direction model: {PUBLIC_TICKERS}")
    print(f"Test period starts: {cutoff_date.date()}, {len(X_test)} test rows")
    print(f"Majority-class baseline: {majority_baseline:.3f}")
    print(f"Model accuracy: {accuracy:.3f}")
    print("\nTop SHAP features for the most recent prediction:")
    for item in explain_latest(model, X_test):
        print(f"  {item['feature']}: {item['shap_value']}")
