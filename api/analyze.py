from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, request


app = Flask(__name__)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    try:
        numeric_value = float(value)
        if not np.isfinite(numeric_value):
            return None
        return numeric_value
    except (TypeError, ValueError):
        return None


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator, 4)


def extract_first_available(row_labels: list[str], statement: pd.DataFrame) -> float | None:
    if statement.empty:
        return None

    for label in row_labels:
        if label in statement.index:
            row = statement.loc[label]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]

            values = pd.to_numeric(row, errors="coerce").dropna()
            if not values.empty:
                return safe_float(values.iloc[0])
    return None


def fetch_financial_data(ticker_symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(ticker_symbol)

    income_statement = ticker.financials
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow
    history = ticker.history(period="1y")
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError("Invalid ticker or ticker data unavailable.")

    if income_statement.empty or balance_sheet.empty or cash_flow.empty:
        raise ValueError("Missing required financial statement data for this ticker.")

    if history.empty or "Close" not in history.columns:
        raise ValueError("Missing historical price data for this ticker.")

    return {
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "history": history,
    }


def calculate_ratios(
    income_statement: pd.DataFrame,
    balance_sheet: pd.DataFrame,
) -> dict[str, float | None]:
    net_income = extract_first_available(["Net Income", "NetIncome"], income_statement)
    revenue = extract_first_available(["Total Revenue", "Operating Revenue", "Revenue"], income_statement)
    total_assets = extract_first_available(["Total Assets"], balance_sheet)
    shareholder_equity = extract_first_available(
        ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"],
        balance_sheet,
    )
    current_assets = extract_first_available(["Current Assets", "Total Current Assets"], balance_sheet)
    current_liabilities = extract_first_available(
        ["Current Liabilities", "Total Current Liabilities"],
        balance_sheet,
    )
    total_debt = extract_first_available(
        ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
        balance_sheet,
    )

    ratios = {
        "roa": safe_divide(net_income, total_assets),
        "roe": safe_divide(net_income, shareholder_equity),
        "net_profit_margin": safe_divide(net_income, revenue),
        "current_ratio": safe_divide(current_assets, current_liabilities),
        "debt_to_equity": safe_divide(total_debt, shareholder_equity),
        "asset_turnover": safe_divide(revenue, total_assets),
    }

    if all(value is None for value in ratios.values()):
        raise ValueError("Unable to calculate ratios because the required statement fields are missing.")

    return ratios


def calculate_moving_averages(history: pd.DataFrame) -> dict[str, float | str]:
    close_prices = pd.to_numeric(history["Close"], errors="coerce").dropna()

    if len(close_prices) < 50:
        raise ValueError("Not enough historical price data to calculate moving averages.")

    ma_20 = safe_float(close_prices.rolling(window=20).mean().iloc[-1])
    ma_50 = safe_float(close_prices.rolling(window=50).mean().iloc[-1])

    if ma_20 is None or ma_50 is None:
        raise ValueError("Unable to calculate moving averages from historical price data.")

    signal = "Hold"
    if ma_20 > ma_50:
        signal = "Buy"
    elif ma_20 < ma_50:
        signal = "Sell"

    return {
        "20_day": round(ma_20, 2),
        "50_day": round(ma_50, 2),
        "signal": signal,
    }


@app.after_request
def add_cors_headers(response: Any) -> Any:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/", methods=["GET", "OPTIONS"])
def analyze() -> Any:
    if request.method == "OPTIONS":
        return ("", 200)

    ticker_symbol = request.args.get("ticker", "").strip().upper()
    if not ticker_symbol:
        return jsonify({"error": "Ticker query parameter is required."}), 400

    try:
        data = fetch_financial_data(ticker_symbol)
        ratios = calculate_ratios(data["income_statement"], data["balance_sheet"])
        moving_average_data = calculate_moving_averages(data["history"])

        return jsonify(
            {
                "ticker": ticker_symbol,
                "ratios": ratios,
                "moving_averages": {
                    "20_day": moving_average_data["20_day"],
                    "50_day": moving_average_data["50_day"],
                },
                "signal": moving_average_data["signal"],
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "ticker": ticker_symbol}), 404
    except Exception as exc:
        return jsonify({"error": f"Unexpected server error: {exc}", "ticker": ticker_symbol}), 500


if __name__ == "__main__":
    app.run(debug=True)
