"use client";

import { useQuery } from "@tanstack/react-query";
import type { NewsItem } from "@/lib/types";

async function fetchNews(ticker: string): Promise<NewsItem[]> {
  const res = await fetch(`/api/news/${ticker}`);
  if (!res.ok) {
    throw new Error("Failed to load news");
  }
  const data = await res.json();
  return data.news;
}

export default function CompanyNewsTab({ ticker }: { ticker: string | null }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["news", ticker],
    queryFn: () => fetchNews(ticker as string),
    enabled: !!ticker,
  });

  if (!ticker) {
    return (
      <p className="text-sm text-neutral-400">
        News is unavailable for private companies.
      </p>
    );
  }

  if (isLoading) {
    return <p className="text-sm text-neutral-400">Loading news...</p>;
  }

  if (isError || !data) {
    return <p className="text-sm text-neutral-400">News unavailable.</p>;
  }

  if (data.length === 0) {
    return <p className="text-sm text-neutral-400">No recent news.</p>;
  }

  return (
    <ul className="divide-y divide-neutral-100 border border-neutral-200">
      {data.slice(0, 20).map((item) => (
        <li key={item.id} className="p-4">
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-neutral-900 hover:underline"
          >
            {item.headline}
          </a>
          <p className="mt-1 text-sm text-neutral-600">{item.summary}</p>
          <p className="mt-2 text-xs text-neutral-400">
            {item.source} ·{" "}
            {new Date(item.datetime * 1000).toLocaleDateString()}
          </p>
        </li>
      ))}
    </ul>
  );
}
