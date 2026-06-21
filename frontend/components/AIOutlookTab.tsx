"use client";

import { useQuery } from "@tanstack/react-query";

type Outlook = {
  ticker: string;
  probabilityUp?: number;
  modelAccuracy?: number;
  majorityBaseline?: number;
  accuracyCi95?: [number, number];
  isSignificant?: boolean;
  topFeatures?: { feature: string; shap_value: number }[];
  summary: string;
};

async function fetchOutlook(ticker: string): Promise<Outlook> {
  const res = await fetch(`/api/outlook/${ticker}`);
  if (!res.ok) {
    throw new Error("Failed to load AI outlook");
  }
  return res.json();
}

export default function AIOutlookTab({ ticker }: { ticker: string | null }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["outlook", ticker],
    queryFn: () => fetchOutlook(ticker as string),
    enabled: !!ticker,
  });

  if (!ticker) {
    return (
      <p className="text-sm text-neutral-400">
        AI outlook is unavailable for private companies.
      </p>
    );
  }

  if (isLoading) {
    return <p className="text-sm text-neutral-400">Loading AI outlook...</p>;
  }

  if (isError || !data) {
    return <p className="text-sm text-neutral-400">AI outlook unavailable.</p>;
  }

  const hasModel = data.probabilityUp !== undefined;

  return (
    <div className="max-w-2xl space-y-6">
      {hasModel && (
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-neutral-200 p-4">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Probability Up
            </p>
            <p className="mt-1 text-lg font-semibold text-neutral-900">
              {(data.probabilityUp! * 100).toFixed(1)}%
            </p>
          </div>
          <div className="border border-neutral-200 p-4">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Model Accuracy
            </p>
            <p className="mt-1 text-lg font-semibold text-neutral-900">
              {(data.modelAccuracy! * 100).toFixed(1)}%
            </p>
          </div>
          <div className="border border-neutral-200 p-4">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Majority Baseline
            </p>
            <p className="mt-1 text-lg font-semibold text-neutral-900">
              {(data.majorityBaseline! * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {hasModel && (
        <div className="flex items-center gap-2">
          <span
            className={`border px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${
              data.isSignificant
                ? "border-green-600 text-green-700"
                : "border-neutral-300 text-neutral-600"
            }`}
          >
            {data.isSignificant ? "Statistically significant" : "Not statistically significant"}
          </span>
          {data.accuracyCi95 && (
            <span className="text-xs text-neutral-500">
              95% CI: {(data.accuracyCi95[0] * 100).toFixed(1)}%–
              {(data.accuracyCi95[1] * 100).toFixed(1)}%
            </span>
          )}
        </div>
      )}

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          What&apos;s driving this
        </h2>
        <p className="text-sm leading-relaxed text-neutral-700">{data.summary}</p>
      </div>

      <p className="text-xs text-neutral-400">
        Exploratory signal, not investment advice. Not a trading product.
      </p>
    </div>
  );
}
