"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import CompanyLogo from "./CompanyLogo";
import PriceChange from "./PriceChange";
import Sparkline from "./Sparkline";
import { fetchStock } from "@/lib/stockApi";
import type { Company } from "@/lib/types";

export default function WatchlistCard({ company }: { company: Company }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["stock", company.ticker],
    queryFn: () => fetchStock(company.ticker as string),
    enabled: company.isPublic && !!company.ticker,
  });
  const quote = data?.quote;
  const candles = data?.candles ?? [];

  return (
    <Link
      href={`/company/${(company.ticker ?? company.slug).toLowerCase()}`}
      className="block border border-neutral-200 transition-colors hover:border-neutral-900"
    >
      <div className="flex items-center justify-between p-5 pb-3">
        <div className="flex items-center gap-3">
          <CompanyLogo
            name={company.name}
            ticker={company.ticker}
            brandColor={company.brandColor}
            size={40}
          />
          <div>
            <p className="font-semibold text-neutral-900">{company.name}</p>
            <p className="text-xs text-neutral-500">
              {company.ticker ?? "Private"}
            </p>
          </div>
        </div>
        {/* AI Outlook isn't connected to the frontend yet (see ml/api),
            so no sentiment badge here -- showing a fabricated signal
            would be worse than showing nothing. */}
      </div>

      <div className="px-5">
        {!company.isPublic ? (
          <span className="text-sm text-neutral-500">No public ticker</span>
        ) : isLoading ? (
          <span className="text-sm text-neutral-400">Loading...</span>
        ) : isError || !quote ? (
          <span className="text-sm text-neutral-400">Price unavailable</span>
        ) : (
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-semibold text-neutral-900">
              ${quote.price.toFixed(2)}
            </span>
            <PriceChange change={quote.change} percentChange={quote.percentChange} />
          </div>
        )}
      </div>

      <Sparkline candles={candles} color={company.brandColor} />
    </Link>
  );
}
