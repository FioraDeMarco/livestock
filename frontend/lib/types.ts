export type Company = {
  slug: string;
  ticker: string | null;
  name: string;
  isPublic: boolean;
  brandColor: string;
  industry: string;
  sector: string;
  founded: string;
  employees: string;
  about: string;
};

export type Quote = {
  price: number;
  change: number;
  percentChange: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
};

export type Candle = {
  date: string;
  close: number;
};

export type NewsItem = {
  id: number;
  headline: string;
  summary: string;
  source: string;
  url: string;
  datetime: number;
  image?: string;
};

export type FundingRound = {
  round: string;
  date: string;
  amount: string;
  valuation: string;
  leadInvestor: string;
};
