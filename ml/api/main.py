from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException

from data.fetch_fundamentals import fetch_fundamentals
from models.baseline_xgboost import (
    PUBLIC_TICKERS,
    explain_latest,
    latest_features_cross_sectional,
    train_pooled_model,
)
from models.significance import evaluate_with_significance

HORIZON_DAYS = 7
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model, _, _, X_test, cutoff_date, y_test, ticker_test = train_pooled_model(
        horizon=HORIZON_DAYS
    )
    significance = evaluate_with_significance(y_test, model.predict(X_test), ticker_test)

    # Pre-compute latest cross-sectional features for all tickers at startup.
    # Cross-sectional ranking requires the full peer universe simultaneously, so
    # we fetch all 18 tickers once and cache the result — predict endpoints just
    # do a dict lookup rather than a full yfinance round-trip per request.
    latest_cs = latest_features_cross_sectional(PUBLIC_TICKERS)

    state["model"] = model
    state["significance"] = significance
    state["latest_cross_section"] = latest_cs
    print(
        f"Model ready: accuracy={significance['accuracy']:.3f}, "
        f"majority_baseline={significance['majority_baseline']:.3f}, "
        f"mcnemar_p={significance['mcnemar_p']:.3f}, "
        f"test period from {cutoff_date.date()}"
    )
    yield
    state.clear()


app = FastAPI(title="LiveStock ML API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": "model" in state}


@app.get("/predict/{ticker}")
def predict(ticker: str):
    ticker = ticker.upper()
    if ticker not in PUBLIC_TICKERS:
        raise HTTPException(
            status_code=404,
            detail=f"No model for {ticker}. Supported: {PUBLIC_TICKERS}",
        )
    if "model" not in state:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    row = state["latest_cross_section"][ticker]
    X = pd.DataFrame([row])

    model = state["model"]
    probability_up = float(model.predict_proba(X)[0][1])
    sig = state["significance"]

    try:
        fundamentals = fetch_fundamentals(ticker)
    except Exception:
        fundamentals = {}

    return {
        "ticker": ticker,
        "horizon_days": HORIZON_DAYS,
        "probability_up": round(probability_up, 4),
        "top_features": explain_latest(model, X),
        "fundamentals": fundamentals,
        # No configuration tested in our rigor pass (this model, logistic
        # regression, with/without sentiment, several feature sets) showed
        # a statistically validated edge over the majority-class baseline,
        # and results don't replicate across walk-forward time periods —
        # see docs/JOURNAL.mdx. Expose the actual significance numbers
        # alongside every prediction, not just a confident-looking
        # probability with no context — the product's whole premise is
        # plain-spoken honesty, not implying confidence the model hasn't earned.
        "model_accuracy": round(sig["accuracy"], 4),
        "majority_baseline": round(sig["majority_baseline"], 4),
        "accuracy_ci_95": [round(v, 4) for v in sig["accuracy_ci_95"]],
        "mcnemar_p": round(sig["mcnemar_p"], 4),
        "is_significant": sig["mcnemar_p"] < 0.05,
    }
