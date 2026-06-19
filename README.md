# livestock
LiveStock explores whether price history, technical indicators, and news sentiment carry signal about stock direction over short time horizons. Each company gets its own page with live data, curated news, an XGBoost model outputting probability estimates, and Claude synthesizing the top SHAP features into plain English. Not a trading product.

#### 🏗️ Under Construction 🏗️

<img width="715" alt="Nvidia company page with live quote, brand banner, and 90-day price chart" src="docs/nvidia-overview.png" />

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
   - `FINNHUB_API_KEY` — required for live stock quotes and news
   - `ANTHROPIC_API_KEY` — required for the AI outlook synthesis (placeholder for now)
   - `ML_BACKEND_URL` — defaults to `http://localhost:8000`, not used until `ml/` is built
3. Run the dev server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000).

Without a `FINNHUB_API_KEY`, the homepage and company pages still render, but live price data will show as unavailable. The 90-day price chart uses `yahoo-finance2` and works without any API key.
