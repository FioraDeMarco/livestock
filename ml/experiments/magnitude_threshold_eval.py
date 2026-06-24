import numpy as np
import pandas as pd
import xgboost as xgb

from data.fetch_historical import fetch_historical
from features.targets import add_magnitude_targets
from features.technical_indicators import add_technical_indicators
from models.baseline_xgboost import (
    FEATURE_COLUMNS,
    PUBLIC_TICKERS,
    build_features,
    fetch_benchmark,
)
from models.significance import evaluate_with_significance, format_significance


def prepare_filtered_dataset(
    ticker: str, horizon: int, benchmark: pd.DataFrame, vol_multiplier: float = 1.0
) -> pd.DataFrame:
    """Same pipeline as baseline_xgboost.prepare_dataset, but only keeps
    rows where the forward move was "clear" (see add_magnitude_targets) --
    tests whether near-zero moves are unpredictable noise diluting the
    signal in the clear-move cases, rather than retraining the target
    definition outright."""
    target_col = f"target_{horizon}d"
    clear_col = f"is_clear_move_{horizon}d"

    df = fetch_historical(ticker)
    df = add_technical_indicators(df)
    df = add_magnitude_targets(df, horizons=[horizon], vol_multiplier=vol_multiplier)
    df = build_features(df, benchmark)

    columns = FEATURE_COLUMNS + [target_col, clear_col]
    data = df[columns].dropna(subset=FEATURE_COLUMNS + [target_col])
    return data[data[clear_col]]


def walk_forward_eval_filtered(
    tickers: list[str] = PUBLIC_TICKERS,
    horizon: int = 30,
    n_folds: int = 5,
    vol_multiplier: float = 1.0,
) -> list[dict]:
    target_col = f"target_{horizon}d"
    benchmark = fetch_benchmark()

    frames = []
    for ticker in tickers:
        data = prepare_filtered_dataset(ticker, horizon, benchmark, vol_multiplier)
        data["ticker"] = ticker
        frames.append(data)
    pooled = pd.concat(frames).sort_index()

    unique_dates = pooled.index.unique().sort_values()
    chunks = np.array_split(unique_dates, n_folds + 1)

    results = []
    for i in range(n_folds):
        train_dates = pd.Index(np.concatenate(chunks[: i + 1]))
        test_dates = pd.Index(chunks[i + 1])

        train = pooled[pooled.index.isin(train_dates)]
        test = pooled[pooled.index.isin(test_dates)]

        if len(test) < 20:
            continue

        X_train, y_train = train[FEATURE_COLUMNS], train[target_col]
        X_test, y_test = test[FEATURE_COLUMNS], test[target_col]

        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric="logloss"
        )
        model.fit(X_train, y_train)

        result = evaluate_with_significance(y_test, model.predict(X_test), test["ticker"])
        result["fold"] = i
        result["train_start"] = train_dates.min().date()
        result["test_start"] = test_dates.min().date()
        result["test_end"] = test_dates.max().date()
        results.append(result)

    return results


if __name__ == "__main__":
    horizon = 30
    print(
        f"Filtered (clear-moves-only) walk-forward, {horizon}-day horizon: {PUBLIC_TICKERS}"
    )
    for fold_result in walk_forward_eval_filtered(horizon=horizon, n_folds=5):
        print(
            f"Fold {fold_result['fold']}: train from {fold_result['train_start']}, "
            f"test {fold_result['test_start']} to {fold_result['test_end']}"
        )
        print(f"  {format_significance(fold_result)}")
