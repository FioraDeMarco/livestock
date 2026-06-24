import CompanyLogo from "../ui/CompanyLogo";
import PriceChange from "../ui/PriceChange";
import WatchButton from "../ui/WatchButton";
import { darken } from "@/lib/color";
import type { Company, Quote } from "@/lib/types";

type CompanyHeaderProps = {
  company: Company;
  quote: Quote | null;
};

export default function CompanyHeader({ company, quote }: CompanyHeaderProps) {
  return (
    <div>
      <div
        className="h-40 w-full sm:h-48"
        style={{ backgroundColor: darken(company.brandColor, 0.18) }}
      />

      <div className="mx-auto w-full max-w-5xl px-6">
        <div className="-mt-10 flex items-end justify-between">
          <CompanyLogo
            name={company.name}
            ticker={company.ticker}
            brandColor={company.brandColor}
            size={88}
            className="border-4 border-white"
          />
          <div className="pb-1">
            <WatchButton />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-baseline gap-3">
          <h1 className="text-2xl font-bold text-neutral-900">{company.name}</h1>
          <span className="text-base text-neutral-500">
            {company.ticker ?? "Private"}
          </span>
          {quote && (
            <>
              <span className="text-xl font-semibold text-neutral-900">
                ${quote.price.toFixed(2)}
              </span>
              <PriceChange change={quote.change} percentChange={quote.percentChange} />
            </>
          )}
          {!company.isPublic && (
            <span className="border border-neutral-300 px-2 py-0.5 text-xs font-medium uppercase tracking-wide text-neutral-600">
              Private company
            </span>
          )}
        </div>

        <p className="mt-2 text-sm text-neutral-500">
          {company.industry} · {company.sector} · Founded {company.founded} ·{" "}
          {company.employees} employees
        </p>
      </div>
    </div>
  );
}
