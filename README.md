# financialfindr.app

Instant financial statements, one ticker away.

## Flask Backend

This repo now also includes a local Flask backend in `app.py`.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
python app.py
```

### API endpoint

```bash
http://127.0.0.1:5000/analyze?ticker=AAPL
```

Example JSON response:

```json
{
  "ticker": "AAPL",
  "ratios": {
    "roa": 0.2742,
    "roe": 1.5621,
    "net_profit_margin": 0.2413,
    "current_ratio": 0.9881,
    "debt_to_equity": 1.8234,
    "asset_turnover": 1.1362
  },
  "moving_averages": {
    "20_day": 214.63,
    "50_day": 209.18
  },
  "signal": "Buy"
}
```

The endpoint handles:
- invalid tickers
- missing financial statement data
- missing or insufficient historical price data

## Project Structure

```
financialfindr/
├── index.html        # Frontend (plain HTML/CSS/JS)
├── vercel.json       # Vercel routing config
├── api/
│   └── finance.js    # Serverless function — proxies FMP API (keeps key secret)
└── README.md
```

## Deploy to Vercel (Step-by-Step)

### 1. Push to GitHub
Create a new repo on GitHub and push this folder:
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/financialfindr.git
git push -u origin main
```

### 2. Import to Vercel
- Go to [vercel.com](https://vercel.com) → **Add New Project**
- Import your GitHub repo
- Framework preset: **Other** (no framework needed)
- Click **Deploy** (it will fail on first deploy — that's expected until you add the API key)

### 3. Add Your FMP API Key
- In your Vercel project → **Settings** → **Environment Variables**
- Add:
  - **Name:** `FMP_API_KEY`
  - **Value:** your key from [financialmodelingprep.com](https://financialmodelingprep.com)
  - **Environments:** Production, Preview, Development ✓

### 4. Redeploy
- Go to **Deployments** tab → click the three dots on the latest deploy → **Redeploy**
- Your site is now live 🎉

## Local Development

To test locally with Vercel CLI:
```bash
npm i -g vercel
vercel dev
```
Then add `FMP_API_KEY=your_key_here` to a `.env.local` file in the project root.

## How It Works

The frontend (`index.html`) calls `/api/finance?ticker=AAPL&type=all` instead of hitting FMP directly. The serverless function (`api/finance.js`) reads the API key from Vercel's environment variables and proxies the request — **your API key is never exposed to the browser**.
