import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    return pd.DataFrame(
        {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_hist": macd_line - signal_line,
        }
    )


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI, MACD, and moving average columns to an OHLCV DataFrame."""
    out = df.copy()

    out["rsi_14"] = rsi(out["close"])

    macd_df = macd(out["close"])
    out = out.join(macd_df)

    out["sma_20"] = out["close"].rolling(window=20).mean()
    out["sma_50"] = out["close"].rolling(window=50).mean()
    out["sma_200"] = out["close"].rolling(window=200).mean()

    return out


if __name__ == "__main__":
    from data.fetch_historical import fetch_historical

    data = add_technical_indicators(fetch_historical("NVDA"))
    print(data.tail())
