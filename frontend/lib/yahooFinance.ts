import YahooFinance from "yahoo-finance2";
import type { Candle } from "./types";

const yahooFinance = new YahooFinance({ suppressNotices: ["yahooSurvey"] });

export async function getHistoricalCandles(
  ticker: string,
  days = 90
): Promise<Candle[]> {
  const period2 = new Date();
  const period1 = new Date(period2.getTime() - days * 24 * 60 * 60 * 1000);

  const result = await yahooFinance.chart(ticker, {
    period1,
    period2,
    interval: "1d",
  });

  return result.quotes
    .filter((quote) => quote.close !== null)
    .map((quote) => ({
      date: quote.date.toISOString().slice(0, 10),
      close: quote.close as number,
    }));
}
