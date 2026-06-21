from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException

from models.baseline_xgboost import (
    PUBLIC_TICKERS,
    explain_latest,
    latest_features,
    train_pooled_model,
)
from models.significance import evaluate_with_significance

HORIZON_DAYS = 30
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model, _, _, X_test, cutoff_date, y_test, ticker_test = train_pooled_model(
        horizon=HORIZON_DAYS
    )
    significance = evaluate_with_significance(y_test, model.predict(X_test), ticker_test)
    state["model"] = model
    state["significance"] = significance
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

    row = latest_features(ticker)
    X = pd.DataFrame([row])

    model = state["model"]
    probability_up = float(model.predict_proba(X)[0][1])
    sig = state["significance"]

    return {
        "ticker": ticker,
        "horizon_days": HORIZON_DAYS,
        "probability_up": round(probability_up, 4),
        "top_features": explain_latest(model, X),
        # No configuration tested in our rigor pass (this model, logistic
        # regression, with/without sentiment, several feature sets) showed
        # a statistically validated edge over the majority-class baseline,
        # and results don't replicate across walk-forward time periods --
        # see docs/JOURNAL.mdx. Expose the actual significance numbers
        # alongside every prediction, not just a confident-looking
        # probability with no context -- the product's whole premise is
        # plain-spoken honesty, not implying confidence the model hasn't
        # earned.
        "model_accuracy": round(sig["accuracy"], 4),
        "majority_baseline": round(sig["majority_baseline"], 4),
        "accuracy_ci_95": [round(v, 4) for v in sig["accuracy_ci_95"]],
        "mcnemar_p": round(sig["mcnemar_p"], 4),
        "is_significant": sig["mcnemar_p"] < 0.05,
    }
