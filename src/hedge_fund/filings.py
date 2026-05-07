"""Build filing-sentiment factors by combining the filings endpoints with the
LLM-based analyzer.

The high-level flow:

  1. For each ticker, list recent 10-K/10-Q filings via the data client.
  2. Pull the textual sections we want to score (MD&A by default).
  3. Send each section to `FilingAnalyzer` and collect the structured
     sentiment dataclass.
  4. Aggregate into a per-rebalance signal (mean composite of filings
     filed within a trailing window).

Calling Claude on every filing in a real universe is expensive; in
practice you would persist the per-filing scores to disk so subsequent
backtests reuse them. That cache is intentionally out of scope here.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict

import pandas as pd

from .data import FinancialDatasetsClient
from .llm import FilingAnalyzer

DEFAULT_ITEM_TYPES: tuple[str, ...] = (
    "Item 7",
    "Item 7A",
    "MD&A",
    "ManagementDiscussion",
)


def fetch_and_score_filings(
    tickers: Iterable[str],
    client: FinancialDatasetsClient,
    analyzer: FilingAnalyzer,
    item_types: tuple[str, ...] = DEFAULT_ITEM_TYPES,
    max_filings_per_ticker: int = 8,
) -> dict[str, pd.DataFrame]:
    """Per-ticker DataFrame indexed by filed_date with sentiment columns."""
    out: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        filings = client.get_filings(ticker)
        if not filings:
            continue
        rows: list[dict] = []
        for filing in filings[:max_filings_per_ticker]:
            text = client.get_filing_items(filing.get("filing_id"), item_types)
            if not text:
                continue
            sentiment = analyzer.score(text, ticker=ticker)
            row = asdict(sentiment)
            row["composite"] = sentiment.composite
            row["filed_date"] = filing.get("filed_date")
            rows.append(row)
        if not rows:
            continue
        df = pd.DataFrame(rows)
        df["filed_date"] = pd.to_datetime(df["filed_date"])
        out[ticker] = df.set_index("filed_date").sort_index()
    return out


def filing_sentiment_signal(
    sentiment_per_ticker: dict[str, pd.DataFrame],
    rebalance_dates: pd.DatetimeIndex,
    tickers: list[str],
    window_days: int = 180,
    column: str = "composite",
) -> pd.DataFrame:
    """Mean of `column` across filings filed in the trailing window."""
    out = pd.DataFrame(
        float("nan"),
        index=pd.DatetimeIndex(rebalance_dates),
        columns=list(tickers),
    )
    ticker_set = set(tickers)
    for ticker, df in sentiment_per_ticker.items():
        if df.empty or ticker not in ticker_set or column not in df.columns:
            continue
        series = df[column].sort_index()
        for d in out.index:
            window_start = d - pd.Timedelta(days=window_days)
            window = series.loc[window_start:d]
            if not window.empty:
                out.at[d, ticker] = float(window.mean())
    return out
