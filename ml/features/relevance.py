import pandas as pd

COMPANY_ALIASES = {
    "TSLA": ["tesla"],
    "NVDA": ["nvidia"],
    "MSFT": ["microsoft"],
    "META": ["meta", "facebook"],
    "AMZN": ["amazon"],
    "GOOGL": ["google", "alphabet"],
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
