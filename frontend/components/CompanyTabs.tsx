"use client";

import { useState } from "react";
import AIOutlookTab from "./AIOutlookTab";
import CompanyNewsTab from "./CompanyNewsTab";
import OverviewTab from "./OverviewTab";
import type { Candle, Company, Quote } from "@/lib/types";

const TABS = ["Overview", "Company News", "Market Signals", "AI Outlook"] as const;
type Tab = (typeof TABS)[number];

type CompanyTabsProps = {
  company: Company;
  quote: Quote | null;
  candles: Candle[];
};

export default function CompanyTabs({ company, quote, candles }: CompanyTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Overview");

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-8">
      <nav className="flex gap-6 border-b border-neutral-200">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`-mb-px border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "border-neutral-900 text-neutral-900"
                : "border-transparent text-neutral-500 hover:text-neutral-900"
            }`}
          >
            {tab}
          </button>
        ))}
      </nav>

      <div className="py-8">
        {activeTab === "Overview" && (
          <OverviewTab company={company} quote={quote} candles={candles} />
        )}
        {activeTab === "Company News" && (
          <CompanyNewsTab ticker={company.ticker} />
        )}
        {activeTab === "AI Outlook" && <AIOutlookTab ticker={company.ticker} />}
        {activeTab === "Market Signals" && (
          <p className="text-sm text-neutral-400">Market Signals is coming soon.</p>
        )}
      </div>
    </div>
  );
}
