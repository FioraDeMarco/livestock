"""
Kalshi prediction market signals for macro context.

Kalshi is a CFTC-regulated exchange where traders bet real money on future
events. A market's yes_bid price (in cents) is the crowd-sourced probability
that the event resolves YES -- e.g. yes_bid=72 means the market gives 72%
odds. This is generally more accurate than polls or analyst forecasts because
people put real money behind their predictions.

Auth: RSA key signing (3 headers). Market *data* endpoints are public (no
auth needed), but price data requires authentication.

Env vars required:
    KALSHI_API_KEY_ID       -- your key ID from kalshi.com/settings/api
    KALSHI_PRIVATE_KEY_PATH -- path to your RSA private key .pem file
                               (alternatively set KALSHI_PRIVATE_KEY with
                               the PEM content directly)
"""

import base64
import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"


def _load_private_key():
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    pem_content = os.environ.get("KALSHI_PRIVATE_KEY")
    if not pem_content:
        key_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH")
        if not key_path:
            raise RuntimeError(
                "Set KALSHI_PRIVATE_KEY (PEM content) or "
                "KALSHI_PRIVATE_KEY_PATH (path to .pem file)"
            )
        pem_content = Path(key_path).read_text()

    return serialization.load_pem_private_key(pem_content.encode(), password=None)


def _auth_headers(method: str, path: str) -> dict:
    """Generate the 3 Kalshi RSA auth headers for a request."""
    key_id = os.environ.get("KALSHI_API_KEY_ID")
    if not key_id:
        raise RuntimeError("KALSHI_API_KEY_ID is not set")

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    timestamp_ms = str(int(time.time() * 1000))
    message = f"{timestamp_ms}{method.upper()}{path}".encode()

    private_key = _load_private_key()
    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(signature).decode()

    return {
        "kalshiAccessKey": key_id,
        "kalshiAccessTimestamp": timestamp_ms,
        "kalshiAccessSignature": sig_b64,
    }


def _get(path: str, params: dict | None = None) -> dict:
    """Authenticated GET against the Kalshi API."""
    full_path = f"/trade-api/v2{path}"
    headers = _auth_headers("GET", full_path)
    res = requests.get(f"{BASE_URL}{path}", params=params, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json()


# --- Series tickers for the macro signals we care about ---
# These are episodic: markets open a few weeks before each event and settle
# after. get_macro_signals() returns None for any signal with no open market.
MACRO_SERIES = {
    "fed_rate_cut":  "RATECUT",    # Will the Fed cut rates at the next meeting?
    "fed_rate_hike": "RATEHIKE",   # Will the Fed hike rates at the next meeting?
    "cpi_beat":      "CPIYOY",     # Will CPI come in above consensus?
    "recession":     "KXRECESSION",# Will the US enter a recession?
    "nasdaq_up":     "NASDAQ100",  # Will Nasdaq close higher this week/month?
}


def _best_probability(series_ticker: str) -> Optional[float]:
    """
    Find the most relevant open market for a series and return its
    yes_bid as a 0-1 probability. Returns None if no active market exists.
    """
    try:
        data = _get(
            "/events",
            params={
                "series_ticker": series_ticker,
                "status": "open",
                "with_nested_markets": "true",
                "limit": 5,
            },
        )
        events = data.get("events", [])
        for event in events:
            for market in event.get("markets", []):
                yes_bid = market.get("yes_bid")
                if yes_bid is not None and yes_bid > 0:
                    return round(yes_bid / 100, 4)
    except Exception:
        pass
    return None


def get_macro_signals() -> dict[str, Optional[float]]:
    """
    Fetch current prediction-market probabilities for key macro events.
    Returns a dict with float values (0-1) when a market is active,
    None when no market is currently open for that event.

    Example return:
        {
            "fed_rate_cut":  0.72,   # 72% odds of a rate cut at next meeting
            "fed_rate_hike": None,   # no active hike market
            "cpi_beat":      0.38,
            "recession":     0.21,
            "nasdaq_up":     None,
        }
    """
    return {
        signal: _best_probability(series)
        for signal, series in MACRO_SERIES.items()
    }


def signals_for_prompt(signals: dict[str, Optional[float]]) -> str:
    """
    Format active Kalshi signals as a concise string for the Claude
    synthesis prompt. Omits signals with no open market.
    """
    LABELS = {
        "fed_rate_cut":  "Fed rate cut at next meeting",
        "fed_rate_hike": "Fed rate hike at next meeting",
        "cpi_beat":      "CPI above consensus (next release)",
        "recession":     "US recession this year",
        "nasdaq_up":     "Nasdaq higher by end of month",
    }
    active = [
        f"{LABELS[k]}: {round(v * 100)}% (Kalshi)"
        for k, v in signals.items()
        if v is not None
    ]
    if not active:
        return ""
    return "Prediction market probabilities (Kalshi):\n" + "\n".join(f"- {s}" for s in active)


if __name__ == "__main__":
    print("Fetching Kalshi macro signals...")
    signals = get_macro_signals()
    for k, v in signals.items():
        status = f"{round(v * 100)}%" if v is not None else "no active market"
        print(f"  {k:20s}: {status}")
    prompt_text = signals_for_prompt(signals)
    if prompt_text:
        print(f"\nPrompt snippet:\n{prompt_text}")
    else:
        print("\nNo active macro markets right now.")
