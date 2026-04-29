from __future__ import annotations

from typing import Any

import requests

from .metrics import compute_growth_from_net_income, compute_growth_over_pe, to_float


class StockNotFoundError(Exception):
    pass


class StockDataError(Exception):
    pass


class AlphaVantageStockProvider:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = session or requests.Session()

    def _request(self, params: dict[str, str]) -> dict[str, Any]:
        response = self.session.get(self.base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def _raise_if_provider_message(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return

        message = data.get("Error Message") or data.get("Information") or data.get("Note")
        if message:
            raise StockDataError(str(message))

    def _fetch_overview(self, symbol: str) -> dict[str, Any]:
        data = self._request(
            {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": self.api_key,
            }
        )
        self._raise_if_provider_message(data)
        if not data or "Symbol" not in data:
            raise StockNotFoundError(f"Ticker '{symbol}' not found")
        return data

    def _fetch_income_statement(self, symbol: str) -> dict[str, Any]:
        data = self._request(
            {
                "function": "INCOME_STATEMENT",
                "symbol": symbol,
                "apikey": self.api_key,
            }
        )
        self._raise_if_provider_message(data)
        reports = data.get("annualReports", []) if isinstance(data, dict) else []
        if len(reports) < 2:
            raise StockDataError("Insufficient annual net income history for growth calculation")
        return data

    def get_stock_metrics(self, symbol: str) -> dict[str, Any]:
        ticker = symbol.upper().strip()
        if not ticker:
            raise StockNotFoundError("Ticker cannot be empty")

        overview = self._fetch_overview(ticker)
        income_statement = self._fetch_income_statement(ticker)

        growth_rate = compute_growth_from_net_income(income_statement["annualReports"])

        pe_ratio = None
        growth_over_pe = None
        growth_over_pe_pass = None
        lynch_rule_pass = None
        try:
            pe_ratio = to_float(overview.get("PERatio"))
            growth_over_pe = compute_growth_over_pe(growth_rate, pe_ratio)
            growth_over_pe_pass = growth_over_pe > 1
            lynch_rule_pass = pe_ratio < growth_rate
        except (ValueError, TypeError):
            pass

        def parse_optional_number(value: Any) -> float | None:
            try:
                return to_float(value)
            except (ValueError, TypeError):
                return None

        return {
            "ticker": overview.get("Symbol", ticker),
            "name": overview.get("Name"),
            "industry": overview.get("Industry"),
            "sector": overview.get("Sector"),
            "pe_ratio": pe_ratio,
            "growth_rate": round(growth_rate, 2),
            "growth_over_pe": round(growth_over_pe, 2) if growth_over_pe is not None else None,
            "growth_over_pe_pass": growth_over_pe_pass,
            "lynch_rule_pass": lynch_rule_pass,
            "latest_quarter": overview.get("LatestQuarter"),
            "analyst_target_price": parse_optional_number(overview.get("AnalystTargetPrice")),
            "week_52_high": parse_optional_number(overview.get("52WeekHigh")),
            "week_52_low": parse_optional_number(overview.get("52WeekLow")),
            "description": overview.get("Description"),
        }
