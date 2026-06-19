import { notFound } from "next/navigation";
import CompanyHeader from "@/components/CompanyHeader";
import CompanyTabs from "@/components/CompanyTabs";
import { getCompanyByParam } from "@/lib/companies";
import { getQuote } from "@/lib/finnhub";
import { getHistoricalCandles } from "@/lib/yahooFinance";
import type { Candle, Quote } from "@/lib/types";

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const company = getCompanyByParam(ticker);

  if (!company) {
    notFound();
  }

  let quote: Quote | null = null;
  let candles: Candle[] = [];

  if (company.isPublic && company.ticker) {
    const [quoteResult, candlesResult] = await Promise.allSettled([
      getQuote(company.ticker),
      getHistoricalCandles(company.ticker, 90),
    ]);

    quote = quoteResult.status === "fulfilled" ? quoteResult.value : null;
    candles = candlesResult.status === "fulfilled" ? candlesResult.value : [];
  }

  return (
    <main className="flex-1">
      <CompanyHeader company={company} quote={quote} />
      <CompanyTabs company={company} quote={quote} candles={candles} />
    </main>
  );
}
