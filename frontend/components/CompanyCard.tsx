"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import CompanyLogo from "./CompanyLogo";
import PriceChange from "./PriceChange";
import type { Company, Quote } from "@/lib/types";

async function fetchQuote(ticker: string): Promise<Quote> {
  const res = await fetch(`/api/stock/${ticker}`);
  if (!res.ok) {
    throw new Error("Failed to load quote");
  }
  const data = await res.json();
  return data.quote;
}

export default function CompanyCard({ company }: { company: Company }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["quote", company.ticker],
    queryFn: () => fetchQuote(company.ticker as string),
    enabled: company.isPublic && !!company.ticker,
  });

  return (
    <Link
      href={`/company/${(company.ticker ?? company.slug).toLowerCase()}`}
      className="block border border-neutral-200 p-5 transition-colors hover:border-neutral-900"
    >
      <div className="flex items-center gap-4">
        <CompanyLogo
          name={company.name}
          ticker={company.ticker}
          brandColor={company.brandColor}
          size={48}
        />
        <div>
          <p className="font-semibold text-neutral-900">{company.name}</p>
          <p className="text-sm text-neutral-500">
            {company.ticker ?? "Private"}
          </p>
        </div>
      </div>

      <div className="mt-4">
        {!company.isPublic ? (
          <span className="text-sm text-neutral-500">No public ticker</span>
        ) : isLoading ? (
          <span className="text-sm text-neutral-400">Loading...</span>
        ) : isError || !data ? (
          <span className="text-sm text-neutral-400">Price unavailable</span>
        ) : (
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-semibold text-neutral-900">
              ${data.price.toFixed(2)}
            </span>
            <PriceChange change={data.change} percentChange={data.percentChange} />
          </div>
        )}
      </div>
    </Link>
  );
}
