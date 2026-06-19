import { getCandles, getQuote } from "@/lib/finnhub";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params;

  const [quoteResult, candlesResult] = await Promise.allSettled([
    getQuote(ticker),
    getCandles(ticker, 90),
  ]);

  if (quoteResult.status === "rejected") {
    return Response.json(
      { error: quoteResult.reason?.message ?? "Unknown error" },
      { status: 502 }
    );
  }

  return Response.json({
    quote: quoteResult.value,
    candles: candlesResult.status === "fulfilled" ? candlesResult.value : [],
  });
}
