from functools import lru_cache

import pandas as pd
from transformers import pipeline

FINBERT_MODEL = "ProsusAI/finbert"


@lru_cache(maxsize=1)
def _get_pipeline():
    """Load FinBERT once per process. Loading is slow (model download
    + weights init), so every caller shares the same cached pipeline."""
    return pipeline("sentiment-analysis", model=FINBERT_MODEL)


def score_headlines(headlines: list[str]) -> pd.DataFrame:
    """Score headlines with FinBERT.

    Returns a DataFrame with one row per headline: label (positive/
    negative/neutral), confidence, and a signed sentiment_score in
    [-1, 1] (positive confidence minus negative confidence, 0 for
    neutral) that's easier to feed into a model than three separate
    label probabilities.
    """
    if not headlines:
        return pd.DataFrame(columns=["headline", "label", "confidence", "sentiment_score"])

    classifier = _get_pipeline()
    results = classifier(headlines)

    sign = {"positive": 1, "negative": -1, "neutral": 0}
    return pd.DataFrame(
        {
            "headline": headlines,
            "label": [r["label"] for r in results],
            "confidence": [r["score"] for r in results],
            "sentiment_score": [
                sign[r["label"]] * r["score"] for r in results
            ],
        }
    )


def daily_sentiment(news: pd.DataFrame, weights: pd.Series | None = None) -> pd.DataFrame:
    """Aggregate per-headline scores into one row per date.

    `news` must have `date` and `headline` columns (the shape returned
    by `fetch_company_news`). `weights`, if given, must align with
    `news`'s rows (e.g. from `relevance_weight`) and is used for a
    weighted average instead of a plain mean — see
    `features/relevance.py` for why headlines aren't just kept/dropped.

    Returns a DataFrame indexed by date with avg_sentiment and
    headline_count.
    """
    if news.empty:
        return pd.DataFrame(columns=["avg_sentiment", "headline_count"])

    scored = score_headlines(news["headline"].tolist())
    scored["date"] = news["date"].values
    scored["weight"] = weights.values if weights is not None else 1.0
    scored["weighted_score"] = scored["sentiment_score"] * scored["weight"]

    daily = scored.groupby("date").apply(
        lambda g: pd.Series(
            {
                "avg_sentiment": g["weighted_score"].sum() / g["weight"].sum(),
                "headline_count": len(g),
            }
        ),
        include_groups=False,
    )
    daily.index = pd.to_datetime(daily.index)
    return daily


if __name__ == "__main__":
    sample_headlines = [
        "NVIDIA stock soars to record high on blowout earnings",
        "NVIDIA shares plunge amid chip shortage fears",
        "NVIDIA announces quarterly dividend, unchanged from prior quarter",
    ]
    print(score_headlines(sample_headlines))
