from __future__ import annotations

from typing import Any

import requests
import yfinance as yf

from .metrics import compute_growth_from_net_income, compute_growth_over_pe, to_float


class StockNotFoundError(Exception):
    pass


class StockDataError(Exception):
    pass


class FallbackStockProvider:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def get_stock_metrics(self, symbol: str) -> dict[str, Any]:
        try:
            return self.primary.get_stock_metrics(symbol)
        except StockNotFoundError:
            raise
        except StockDataError as exc:
            message = str(exc).lower()
            # Alpha Vantage free tier frequently responds with throttling messages.
            if "thank you for using alpha vantage" in message or "rate limit" in message:
                return self.fallback.get_stock_metrics(symbol)
            raise


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


class FinnhubStockProvider:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.session = session or requests.Session()

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query = {**params, "token": self.api_key}
        response = self.session.get(f"{self.base_url}/{path}", params=query, timeout=15)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise StockDataError(str(data.get("error")))
        return data

    def _extract_net_income_reports(self, financials_payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = financials_payload.get("data", []) if isinstance(financials_payload, dict) else []
        reports: list[dict[str, Any]] = []
        for entry in data:
            # quarter=0 usually indicates annual filing in Finnhub financials-reported endpoint.
            if int(entry.get("quarter") or 0) != 0:
                continue

            report = entry.get("report", {})
            income_statements = report.get("ic", []) if isinstance(report, dict) else []

            net_income_value = None
            for line in income_statements:
                concept = str(line.get("concept", ""))
                label = str(line.get("label", "")).lower()
                if concept == "us-gaap_NetIncomeLoss" or "net income" in label:
                    try:
                        net_income_value = to_float(line.get("value"))
                        break
                    except (TypeError, ValueError):
                        continue

            if net_income_value is None:
                continue

            year = entry.get("year")
            if year is None:
                continue

            reports.append(
                {
                    "fiscalDateEnding": f"{int(year)}-12-31",
                    "netIncome": str(net_income_value),
                }
            )

        return reports

    def get_stock_metrics(self, symbol: str) -> dict[str, Any]:
        ticker = symbol.upper().strip()
        if not ticker:
            raise StockNotFoundError("Ticker cannot be empty")
        if not self.api_key:
            raise StockDataError("Finnhub API key is missing")

        try:
            profile = self._request("stock/profile2", {"symbol": ticker})
            metrics_payload = self._request("stock/metric", {"symbol": ticker, "metric": "all"})
            financials = self._request("stock/financials-reported", {"symbol": ticker})
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                raise StockDataError("Finnhub rate limit reached") from exc
            raise StockDataError("Could not fetch ticker data") from exc
        except requests.RequestException as exc:
            raise StockDataError("Could not fetch ticker data") from exc

        if not profile or not profile.get("ticker"):
            raise StockNotFoundError(f"Ticker '{ticker}' not found")

        reports = self._extract_net_income_reports(financials)
        if len(reports) < 2:
            raise StockDataError("Insufficient annual net income history for growth calculation")

        growth_rate = compute_growth_from_net_income(reports)

        metric_values = metrics_payload.get("metric", {}) if isinstance(metrics_payload, dict) else {}

        pe_ratio = None
        growth_over_pe = None
        growth_over_pe_pass = None
        lynch_rule_pass = None
        try:
            pe_ratio = to_float(metric_values.get("peBasicExclExtraTTM"))
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

        latest_report = sorted(reports, key=lambda x: x["fiscalDateEnding"], reverse=True)[0]

        return {
            "ticker": profile.get("ticker", ticker),
            "name": profile.get("name"),
            "industry": profile.get("finnhubIndustry"),
            "sector": None,
            "pe_ratio": pe_ratio,
            "growth_rate": round(growth_rate, 2),
            "growth_over_pe": round(growth_over_pe, 2) if growth_over_pe is not None else None,
            "growth_over_pe_pass": growth_over_pe_pass,
            "lynch_rule_pass": lynch_rule_pass,
            "latest_quarter": latest_report.get("fiscalDateEnding"),
            "analyst_target_price": parse_optional_number(metric_values.get("targetPrice")),
            "week_52_high": parse_optional_number(metric_values.get("52WeekHigh")),
            "week_52_low": parse_optional_number(metric_values.get("52WeekLow")),
            "description": self._fetch_description(ticker),
        }

    def _fetch_description(self, ticker: str) -> str | None:
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info or {}
            return info.get("longBusinessSummary") or None
        except Exception:
            return None


class YFinanceStockProvider:
    def get_stock_metrics(self, symbol: str) -> dict[str, Any]:
        ticker = symbol.upper().strip()
        if not ticker:
            raise StockNotFoundError("Ticker cannot be empty")

        try:
            security = yf.Ticker(ticker)
            info = security.info or {}
        except Exception as exc:
            raise StockDataError("Could not fetch ticker data") from exc

        name = info.get("shortName") or info.get("longName")
        if not name:
            raise StockNotFoundError(f"Ticker '{ticker}' not found")

        financials = security.financials
        if financials is None or financials.empty or "Net Income" not in financials.index:
            raise StockDataError("Insufficient annual net income history for growth calculation")

        net_income_series = financials.loc["Net Income"].dropna()
        if len(net_income_series) < 2:
            raise StockDataError("Insufficient annual net income history for growth calculation")

        ending_value = float(net_income_series.iloc[0])
        beginning_value = float(net_income_series.iloc[1])
        growth_rate = ((ending_value - beginning_value) / beginning_value) * 100

        pe_ratio = None
        growth_over_pe = None
        growth_over_pe_pass = None
        lynch_rule_pass = None

        try:
            pe_ratio = to_float(info.get("trailingPE"))
            growth_over_pe = compute_growth_over_pe(growth_rate, pe_ratio)
            growth_over_pe_pass = growth_over_pe > 1
            lynch_rule_pass = pe_ratio < growth_rate
        except (ValueError, TypeError):
            pass

        latest_quarter = info.get("mostRecentQuarter")
        if latest_quarter is not None:
            latest_quarter = str(latest_quarter)

        return {
            "ticker": ticker,
            "name": name,
            "industry": info.get("industry"),
            "sector": info.get("sector"),
            "pe_ratio": pe_ratio,
            "growth_rate": round(growth_rate, 2),
            "growth_over_pe": round(growth_over_pe, 2) if growth_over_pe is not None else None,
            "growth_over_pe_pass": growth_over_pe_pass,
            "lynch_rule_pass": lynch_rule_pass,
            "latest_quarter": latest_quarter,
            "analyst_target_price": info.get("targetMeanPrice"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "description": info.get("longBusinessSummary"),
        }
