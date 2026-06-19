import { getMarketNews } from "@/lib/finnhub";

export async function GET() {
  try {
    const news = await getMarketNews("general");
    return Response.json({ news });
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 502 }
    );
  }
}
