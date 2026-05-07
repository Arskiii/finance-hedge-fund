"""Adapter for the financialdatasets.ai REST API.

The client wraps the prices and financial-metrics endpoints and reshapes the
responses into pandas frames suitable for cross-sectional analysis.
"""
from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import date

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.financialdatasets.ai"


class FinancialDatasetsClient:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        if not self.api_key:
            raise RuntimeError("FINANCIAL_DATASETS_API_KEY is not set")
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-API-KEY": self.api_key},
            timeout=30.0,
        )

    def get_prices(
        self,
        ticker: str,
        start: date,
        end: date,
        interval: str = "day",
    ) -> pd.DataFrame:
        r = self._client.get(
            "/prices/",
            params={
                "ticker": ticker,
                "interval": interval,
                "interval_multiplier": 1,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )
        r.raise_for_status()
        rows = r.json().get("prices", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["time"])
        return df.set_index("time").sort_index()

    def get_financial_metrics(
        self,
        ticker: str,
        period: str = "ttm",
        limit: int = 40,
    ) -> pd.DataFrame:
        r = self._client.get(
            "/financial-metrics/",
            params={"ticker": ticker, "period": period, "limit": limit},
        )
        r.raise_for_status()
        rows = r.json().get("financial_metrics", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if "report_period" in df.columns:
            df["report_period"] = pd.to_datetime(df["report_period"])
            df = df.set_index("report_period").sort_index()
        return df

    def get_insider_trades(self, ticker: str, limit: int = 1000) -> pd.DataFrame:
        r = self._client.get(
            "/insider-trades/",
            params={"ticker": ticker, "limit": limit},
        )
        r.raise_for_status()
        rows = r.json().get("insider_trades", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"])
            df = df.set_index("transaction_date").sort_index()
        return df

    def close(self) -> None:
        self._client.close()


def load_price_panel(
    tickers: Iterable[str],
    start: date,
    end: date,
    client: FinancialDatasetsClient | None = None,
) -> pd.DataFrame:
    """Wide DataFrame of close prices: rows = dates, columns = tickers."""
    client = client or FinancialDatasetsClient()
    frames: dict[str, pd.Series] = {}
    for t in tickers:
        df = client.get_prices(t, start, end)
        if not df.empty and "close" in df.columns:
            frames[t] = df["close"]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index()


# Demo universe of large, liquid US names. A real backtest must use a
# point-in-time index membership snapshot to avoid survivorship bias.
DEFAULT_UNIVERSE: tuple[str, ...] = (
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO",
    "JPM", "V", "MA", "BAC", "WFC", "GS",
    "JNJ", "PFE", "UNH", "LLY", "MRK",
    "XOM", "CVX", "COP",
    "WMT", "COST", "PG", "KO", "PEP",
    "HD", "MCD", "NKE",
)
