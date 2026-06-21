import type { Candle, Quote } from "./types";

export async function fetchStock(
  ticker: string
): Promise<{ quote: Quote; candles: Candle[] }> {
  const res = await fetch(`/api/stock/${ticker}`);
  if (!res.ok) {
    throw new Error("Failed to load stock data");
  }
  return res.json();
}
