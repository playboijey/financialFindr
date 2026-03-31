from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request


app = Flask(__name__)

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def fetch_json(url: str) -> dict[str, Any]:
    user_agent = os.getenv("SEC_USER_AGENT", "financialfindr.app support@example.com")
    request_obj = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request_obj, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError(f"Unable to fetch SEC data: {exc}") from exc


def find_company_cik(ticker_symbol: str) -> tuple[str, str]:
    ticker_map = fetch_json(SEC_TICKER_URL)

    for company in ticker_map.values():
        if str(company.get("ticker", "")).upper() == ticker_symbol:
            cik = str(company.get("cik_str", "")).zfill(10)
            title = str(company.get("title", ticker_symbol))
            if cik.strip("0"):
                return cik, title

    raise ValueError("Ticker not found in SEC company list.")


def build_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    accession_no_dashes = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dashes}/{primary_document}"


def get_latest_filings(ticker_symbol: str) -> dict[str, Any]:
    cik, company_name = find_company_cik(ticker_symbol)
    submissions = fetch_json(SEC_SUBMISSIONS_URL.format(cik=cik))
    recent = submissions.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    filing_dates = recent.get("filingDate", [])

    filings: dict[str, Any] = {}
    for form, accession, document, filing_date in zip(forms, accession_numbers, primary_documents, filing_dates):
        if form in {"10-K", "10-Q", "8-K"} and form not in filings and accession and document:
            filings[form] = {
                "filing_date": filing_date,
                "filing_url": build_filing_url(cik, accession, document),
            }

    if not filings:
        raise ValueError("No recent SEC filings found for this ticker.")

    return {
        "ticker": ticker_symbol,
        "company": company_name,
        "cik": cik,
        "filings": filings,
    }


@app.after_request
def add_cors_headers(response: Any) -> Any:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/", methods=["GET", "OPTIONS"])
def filings() -> Any:
    if request.method == "OPTIONS":
        return ("", 200)

    ticker_symbol = request.args.get("ticker", "").strip().upper()
    if not ticker_symbol:
        return jsonify({"error": "Ticker query parameter is required."}), 400

    try:
        return jsonify(get_latest_filings(ticker_symbol))
    except ValueError as exc:
        return jsonify({"error": str(exc), "ticker": ticker_symbol}), 404
    except Exception as exc:
        return jsonify({"error": f"Unexpected server error: {exc}", "ticker": ticker_symbol}), 500


if __name__ == "__main__":
    app.run(debug=True)
