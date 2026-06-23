import pandas as pd

COMPANY_ALIASES = {
    "AAPL": ["apple"],
    "MSFT": ["microsoft"],
    "GOOGL": ["google", "alphabet"],
    "META": ["meta", "facebook", "instagram", "whatsapp"],
    "AMZN": ["amazon", "aws"],
    "NVDA": ["nvidia"],
    "TSLA": ["tesla"],
    "AMD": ["amd", "advanced micro devices"],
    "JPM": ["jpmorgan", "jp morgan", "chase"],
    "GS": ["goldman sachs", "goldman"],
    "JNJ": ["johnson & johnson", "johnson and johnson", r"j\&j"],
    "UNH": ["unitedhealth", "united health", "optum"],
    "XOM": ["exxonmobil", "exxon"],
    "CVX": ["chevron"],
    "WMT": ["walmart"],
    "COST": ["costco"],
    "HD": ["home depot"],
    "CAT": ["caterpillar"],
}

# Each ticker's GICS sector ETF — fetched alongside company news so the
# model sees industry-wide moves (e.g. "chip sector selloff") not just
# headlines that name the company directly.
SECTOR_ETF = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AMD": "XLK",
    "GOOGL": "XLC", "META": "XLC",
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY",
    "JPM": "XLF", "GS": "XLF",
    "JNJ": "XLV", "UNH": "XLV",
    "XOM": "XLE", "CVX": "XLE",
    "WMT": "XLP", "COST": "XLP",
    "CAT": "XLI",
}

# Headlines that don't directly mention the company (sector/macro news)
# still affect price and shouldn't be discarded outright -- a hard
# filter would skew sentiment optimistic, since negative macro news
# rarely names individual companies while positive company news
# (earnings, launches) almost always does. Down-weight instead.
INDIRECT_SENTIMENT_WEIGHT = 0.5


def relevance_weight(news: pd.DataFrame, ticker: str) -> pd.Series:
    """Per-headline weight: 1.0 if it mentions the company, else
    INDIRECT_SENTIMENT_WEIGHT."""
    terms = [ticker.lower()] + COMPANY_ALIASES.get(ticker, [])
    pattern = "|".join(terms)
    mentions = news["headline"].str.lower().str.contains(pattern, regex=True)
    return mentions.map({True: 1.0, False: INDIRECT_SENTIMENT_WEIGHT})


if __name__ == "__main__":
    sample = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "headline": [
                "NVIDIA stock soars on record earnings",
                "Why Marvell Technology Stock Sank Today",
                "Tech sector broadly higher as chip stocks rally",
            ],
        }
    )
    sample["weight"] = relevance_weight(sample, "NVDA")
    print(sample)
