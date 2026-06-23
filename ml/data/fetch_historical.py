import pandas as pd
import yfinance as yf


def fetch_historical(ticker: str, period: str = "10y") -> pd.DataFrame:
    """Fetch daily OHLCV history for a ticker.

    Returns a DataFrame indexed by date with columns:
    open, high, low, close, volume.
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False)

    if df.empty:
        raise ValueError(f"No historical data returned for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns=str.lower)
    return df[["open", "high", "low", "close", "volume"]]


if __name__ == "__main__":
    data = fetch_historical("NVDA")
    print(data.head())
    print(data.tail())
    print(f"\n{len(data)} rows")
