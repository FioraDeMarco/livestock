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


if __name__ == "__main__":
    from data.fetch_historical import fetch_historical

    data = add_targets(fetch_historical("NVDA"))
    print(data[["close", "target_7d", "target_30d", "target_90d"]].head())
    print(data[["close", "target_7d", "target_30d", "target_90d"]].tail())
