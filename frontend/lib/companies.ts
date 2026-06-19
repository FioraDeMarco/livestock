import type { Company, FundingRound } from "./types";

export const companies: Company[] = [
  {
    slug: "tsla",
    ticker: "TSLA",
    name: "Tesla",
    isPublic: true,
    brandColor: "#CC0000",
    industry: "Automobile Manufacturers",
    sector: "Consumer Discretionary",
    founded: "2003",
    employees: "~140,000",
    about:
      "Tesla designs and manufactures electric vehicles, battery energy storage, and solar products. The company also develops autonomous driving software and has expanded into robotics and AI compute.",
  },
  {
    slug: "nvda",
    ticker: "NVDA",
    name: "NVIDIA",
    isPublic: true,
    brandColor: "#76B900",
    industry: "Semiconductors",
    sector: "Technology",
    founded: "1993",
    employees: "~36,000",
    about:
      "NVIDIA designs graphics processing units and AI accelerator chips that power gaming, data centers, and machine learning workloads across the industry.",
  },
  {
    slug: "msft",
    ticker: "MSFT",
    name: "Microsoft",
    isPublic: true,
    brandColor: "#00A4EF",
    industry: "Software Infrastructure",
    sector: "Technology",
    founded: "1975",
    employees: "~228,000",
    about:
      "Microsoft develops operating systems, productivity software, cloud infrastructure through Azure, and gaming hardware, with a growing investment in AI products.",
  },
  {
    slug: "meta",
    ticker: "META",
    name: "Meta Platforms",
    isPublic: true,
    brandColor: "#0866FF",
    industry: "Internet Content & Social Media",
    sector: "Technology",
    founded: "2004",
    employees: "~74,000",
    about:
      "Meta Platforms builds social networking apps including Facebook, Instagram, and WhatsApp, and is investing heavily in AI and virtual and augmented reality hardware.",
  },
  {
    slug: "amzn",
    ticker: "AMZN",
    name: "Amazon",
    isPublic: true,
    brandColor: "#FF9900",
    industry: "Internet Retail",
    sector: "Consumer Discretionary",
    founded: "1994",
    employees: "~1,550,000",
    about:
      "Amazon operates a global e-commerce marketplace alongside Amazon Web Services, the leading cloud computing platform, and a growing advertising and logistics business.",
  },
  {
    slug: "googl",
    ticker: "GOOGL",
    name: "Alphabet",
    isPublic: true,
    brandColor: "#4285F4",
    industry: "Internet Content & Information",
    sector: "Technology",
    founded: "1998",
    employees: "~180,000",
    about:
      "Alphabet is the parent company of Google, the dominant search and advertising platform, along with YouTube, Android, Google Cloud, and AI research through Google DeepMind.",
  },
  {
    slug: "anthropic",
    ticker: null,
    name: "Anthropic",
    isPublic: false,
    brandColor: "#CC785C",
    industry: "Artificial Intelligence",
    sector: "Technology",
    founded: "2021",
    employees: "~2,000 (estimate)",
    about:
      "Anthropic is an AI safety and research company that builds Claude, a family of large language models, with a focus on making frontier AI systems reliable and interpretable.",
  },
];

export const fundingRounds: FundingRound[] = [
  { round: "Series A", date: "May 2021", amount: "$124M", valuation: "n/a", leadInvestor: "Jaan Tallinn" },
  { round: "Series B", date: "Apr 2022", amount: "$580M", valuation: "$4.1B", leadInvestor: "Sam Bankman-Fried" },
  { round: "Series C", date: "May 2023", amount: "$450M", valuation: "$4.1B", leadInvestor: "Spark Capital" },
  { round: "Strategic", date: "Sep 2023", amount: "Up to $4B", valuation: "n/a", leadInvestor: "Amazon" },
  { round: "Series D", date: "Jan 2024", amount: "$750M", valuation: "$18.4B", leadInvestor: "Menlo Ventures" },
  { round: "Series E", date: "Mar 2025", amount: "$3.5B", valuation: "$61.5B", leadInvestor: "Lightspeed Venture Partners" },
  { round: "Series F", date: "Sep 2025", amount: "$13B", valuation: "$183B", leadInvestor: "ICONIQ Capital" },
];

export function getCompanyByParam(param: string): Company | undefined {
  const value = param.toLowerCase();
  return companies.find(
    (c) => c.slug === value || c.ticker?.toLowerCase() === value
  );
}
