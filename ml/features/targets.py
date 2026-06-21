import pandas as pd


def add_targets(df: pd.DataFrame, horizons: list[int] = [7, 30, 90]) -> pd.DataFrame:
    """Add binary target columns: is price higher N days from now?

    The last `horizon` rows for each target will be NaN, since there's
    no future price to compare against yet. Drop those before training.
    """
    out = df.copy()

    for horizon in horizons:
        future_close = out["close"].shift(-horizon)
        out[f"target_{horizon}d"] = (future_close > out["close"]).astype("Int64")
        out.loc[future_close.isna(), f"target_{horizon}d"] = pd.NA

    return out


def add_magnitude_targets(
    df: pd.DataFrame, horizons: list[int] = [7, 30, 90], vol_multiplier: float = 1.0
) -> pd.DataFrame:
    """Like add_targets, but also flags whether each forward move is
    "clear" -- larger than a multiple of the ticker's own trailing
    volatility, scaled to the horizon via the square-root-of-time rule.

    Binary up/down at any magnitude treats a +0.01% day the same as a
    +8% day. Using volatility-scaled thresholds (instead of a fixed
    percentage) means "clear move" means different things for a calm
    stock like MSFT vs. a volatile one like TSLA, rather than one
    arbitrary cutoff applied to both.
    """
    out = add_targets(df, horizons=horizons)
    daily_vol = out["close"].pct_change().rolling(window=20).std()

    for horizon in horizons:
        future_close = out["close"].shift(-horizon)
        forward_return = future_close / out["close"] - 1
        horizon_threshold = vol_multiplier * daily_vol * (horizon**0.5)
        out[f"is_clear_move_{horizon}d"] = forward_return.abs() > horizon_threshold

    return out


if __name__ == "__main__":
    from data.fetch_historical import fetch_historical

    data = add_targets(fetch_historical("NVDA"))
    print(data[["close", "target_7d", "target_30d", "target_90d"]].head())
    print(data[["close", "target_7d", "target_30d", "target_90d"]].tail())
