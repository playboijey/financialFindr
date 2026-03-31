# Pluto

Financial analysis for publicly traded companies, one ticker away.

## Features

- Analyze a public company by ticker
- Calculate core financial ratios
- Generate 20-day and 50-day moving averages
- Return a simple Buy, Sell, or Hold signal
- Surface recent SEC filing links for 10-K, 10-Q, and 8-K reports

## Stack

- `flask`
- `yfinance`
- `pandas`
- `numpy`
- Vercel serverless Python functions

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python app.py
```

Example local endpoints:

```bash
http://127.0.0.1:5000/api/analyze?ticker=AAPL
http://127.0.0.1:5000/api/filings?ticker=AAPL
```

## Project Structure

```text
financialfindr/
|-- api/
|   |-- analyze.py
|   |-- filings.py
|-- app.py
|-- index.html
|-- requirements.txt
|-- vercel.json
|-- README.md
```

## Deployment

This repo is structured for Vercel:

- `api/analyze.py` serves the analysis endpoint
- `api/filings.py` serves the SEC filings endpoint
- `index.html` is the frontend entry page

Deploy steps:

1. Push the repo to GitHub.
2. Import the project into Vercel.
3. Use the `Other` framework preset if prompted.
4. Deploy it.

## How It Works

The frontend (`index.html`) calls `/api/analyze?ticker=AAPL` for ratio and signal data and `/api/filings?ticker=AAPL` for recent SEC filing links.

## Notes

- `yfinance` powers the financial data and price-history analysis.
- SEC filing links are fetched from the SEC company ticker mapping and submissions feeds.
- Optional environment variable for SEC requests: `SEC_USER_AGENT=Pluto your-email@example.com`
- No external paid market-data API key is required for the current implementation.
