import { notFound } from "next/navigation";
import CompanyHeader from "@/components/CompanyHeader";
import CompanyTabs from "@/components/CompanyTabs";
import { getCompanyByParam } from "@/lib/companies";
import { getCandles, getQuote } from "@/lib/finnhub";
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
    try {
      [quote, candles] = await Promise.all([
        getQuote(company.ticker),
        getCandles(company.ticker, 90),
      ]);
    } catch {
      quote = null;
      candles = [];
    }
  }

  return (
    <main className="flex-1">
      <CompanyHeader company={company} quote={quote} />
      <CompanyTabs company={company} quote={quote} candles={candles} />
    </main>
  );
}
