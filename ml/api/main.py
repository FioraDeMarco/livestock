from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException

from models.baseline_xgboost import (
    PUBLIC_TICKERS,
    explain_latest,
    latest_features,
    train_pooled_model,
)

HORIZON_DAYS = 30
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model, accuracy, majority_baseline, _, cutoff_date = train_pooled_model(
        horizon=HORIZON_DAYS
    )
    state["model"] = model
    state["accuracy"] = accuracy
    state["majority_baseline"] = majority_baseline
    print(
        f"Model ready: accuracy={accuracy:.3f}, "
        f"majority_baseline={majority_baseline:.3f}, "
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

    row = latest_features(ticker)
    X = pd.DataFrame([row])

    model = state["model"]
    probability_up = float(model.predict_proba(X)[0][1])

    return {
        "ticker": ticker,
        "horizon_days": HORIZON_DAYS,
        "probability_up": round(probability_up, 4),
        "top_features": explain_latest(model, X),
        # The model barely beats (or loses to) the majority-class baseline
        # in our own testing (see docs/JOURNAL.mdx) -- expose this
        # alongside every prediction rather than hiding it, since the
        # whole point of the product is plain-spoken honesty, not
        # implying a confidence the model hasn't earned.
        "model_accuracy": round(state["accuracy"], 4),
        "majority_baseline": round(state["majority_baseline"], 4),
    }
