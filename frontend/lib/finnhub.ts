import type { NewsItem, Quote } from "./types";

const BASE_URL = "https://finnhub.io/api/v1";

function requireApiKey(): string {
  const key = process.env.FINNHUB_API_KEY;
  if (!key) {
    throw new Error("FINNHUB_API_KEY is not set");
  }
  return key;
}

export async function getQuote(ticker: string): Promise<Quote> {
  const key = requireApiKey();
  const res = await fetch(
    `${BASE_URL}/quote?symbol=${encodeURIComponent(ticker)}&token=${key}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`Finnhub quote request failed: ${res.status}`);
  }

  const data = await res.json();

  return {
    price: data.c,
    change: data.d,
    percentChange: data.dp,
    high: data.h,
    low: data.l,
    open: data.o,
    previousClose: data.pc,
  };
}

export async function getCompanyNews(
  ticker: string,
  days = 14
): Promise<NewsItem[]> {
  const key = requireApiKey();
  const to = new Date();
  const from = new Date(to.getTime() - days * 24 * 60 * 60 * 1000);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);

  const res = await fetch(
    `${BASE_URL}/company-news?symbol=${encodeURIComponent(
      ticker
    )}&from=${fmt(from)}&to=${fmt(to)}&token=${key}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`Finnhub company news request failed: ${res.status}`);
  }

  const data = await res.json();

  return (Array.isArray(data) ? data : []).map((item) => ({
    id: item.id,
    headline: item.headline,
    summary: item.summary,
    source: item.source,
    url: item.url,
    datetime: item.datetime,
    image: item.image,
  }));
}

export async function getMarketNews(category = "general"): Promise<NewsItem[]> {
  const key = requireApiKey();
  const res = await fetch(
    `${BASE_URL}/news?category=${encodeURIComponent(category)}&token=${key}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`Finnhub market news request failed: ${res.status}`);
  }

  const data = await res.json();

  return (Array.isArray(data) ? data : []).map((item) => ({
    id: item.id,
    headline: item.headline,
    summary: item.summary,
    source: item.source,
    url: item.url,
    datetime: item.datetime,
    image: item.image,
  }));
}
