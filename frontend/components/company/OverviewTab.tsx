import FundingHistory from "./FundingHistory";
import PriceChart from "./PriceChart";
import StatCard from "../ui/StatCard";
import { fundingRounds } from "@/lib/companies";
import type { Candle, Company, Quote } from "@/lib/types";

type OverviewTabProps = {
  company: Company;
  quote: Quote | null;
  candles: Candle[];
};

export default function OverviewTab({ company, quote, candles }: OverviewTabProps) {
  return (
    <div className="space-y-8">
      {company.isPublic && quote ? (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Open" value={`$${quote.open.toFixed(2)}`} />
            <StatCard label="Day High" value={`$${quote.high.toFixed(2)}`} />
            <StatCard label="Day Low" value={`$${quote.low.toFixed(2)}`} />
            <StatCard label="Previous Close" value={`$${quote.previousClose.toFixed(2)}`} />
          </div>
          <PriceChart candles={candles} color={company.brandColor} />
        </>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Latest Valuation" value="$183B" />
          <StatCard label="Total Raised" value="$19.6B+" />
          <StatCard label="Last Round" value="Series F" />
          <StatCard label="Founded" value={company.founded} />
        </div>
      )}

      {!company.isPublic && <FundingHistory rounds={fundingRounds} />}

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          About
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-neutral-700">
          {company.about}
        </p>
      </div>
    </div>
  );
}
