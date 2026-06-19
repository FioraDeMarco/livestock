# livestock
LiveStock explores whether price history, technical indicators, and news sentiment carry signal about stock direction over short time horizons. Each company gets its own page with live data, curated news, an XGBoost model outputting probability estimates, and Claude synthesizing the top SHAP features into plain English. Not a trading product.

#### 🏗️ Under Construction 🏗️

<img width="715" height="556" alt="Screenshot 2026-06-19 at 8 56 53 AM" src="https://github.com/user-attachments/assets/b9f0003d-45e3-4b43-9e46-14655139f708" />

## Getting Started

The frontend is a Next.js app in `frontend/`. The ML backend (`ml/`) is not built yet.

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Copy the env template and fill in your keys:
   ```bash
   cp .env.example .env.local
   ```
   - `FINNHUB_API_KEY` — required for live stock quotes, candles, and news
   - `ANTHROPIC_API_KEY` — required for the AI outlook synthesis (placeholder for now)
   - `ML_BACKEND_URL` — defaults to `http://localhost:8000`, not used until `ml/` is built
3. Run the dev server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000).

Without a `FINNHUB_API_KEY`, the homepage and company pages still render, but price data will show as unavailable.
