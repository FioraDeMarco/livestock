import { getCandles, getQuote } from "@/lib/finnhub";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params;

  try {
    const [quote, candles] = await Promise.all([
      getQuote(ticker),
      getCandles(ticker, 90),
    ]);

    return Response.json({ quote, candles });
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 502 }
    );
  }
}
