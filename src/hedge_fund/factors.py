"""Factor signal construction from price, fundamental, and insider-trade panels."""
from __future__ import annotations

import pandas as pd


def momentum_12_1(prices: pd.DataFrame) -> pd.DataFrame:
    """12-1 momentum: 11-month return ending one month before formation.

    Skipping the most recent month avoids contamination by short-term reversal.
    Indexed at month-end; signal at t is observable at the start of month t+1.
    """
    monthly = prices.resample("ME").last()
    return monthly.pct_change(11).shift(1)


def cross_sectional_zscore(panel: pd.DataFrame) -> pd.DataFrame:
    """Row-wise (per-date) z-score across the cross-section."""
    mean = panel.mean(axis=1)
    std = panel.std(axis=1)
    return panel.sub(mean, axis=0).div(std, axis=0)


def _available_as_of(df: pd.DataFrame, filing_lag_days: int) -> pd.DatetimeIndex:
    """Date at which a fundamental row becomes usable in a backtest.

    Prefers the explicit `filing_date` column if the API returns it; otherwise
    falls back to `report_period + filing_lag_days`. The default 75-day lag is
    a conservative midpoint between the 10-Q (45-day) and 10-K (90-day)
    SEC filing windows.
    """
    if "filing_date" in df.columns:
        return pd.DatetimeIndex(pd.to_datetime(df["filing_date"]))
    return pd.DatetimeIndex(df.index + pd.Timedelta(days=filing_lag_days))


def quality_score(
    metrics: dict[str, pd.DataFrame],
    filing_lag_days: int = 75,
) -> pd.DataFrame:
    """Equal-weighted z-score of return on invested capital and gross margin.

    Each fundamental observation is stamped with its as-of date (filing_date
    when available, else report_period plus a conservative lag) so a backtest
    cannot see numbers that hadn't yet been reported.
    """
    cols = ("return_on_invested_capital", "gross_margin")
    z_panels: list[pd.DataFrame] = []
    for col in cols:
        per_ticker: dict[str, pd.Series] = {}
        for ticker, df in metrics.items():
            if df.empty or col not in df.columns:
                continue
            asof = _available_as_of(df, filing_lag_days)
            series = pd.Series(df[col].to_numpy(), index=asof, name=ticker).sort_index()
            per_ticker[ticker] = series.resample("ME").last().ffill()
        if not per_ticker:
            continue
        wide = pd.concat(per_ticker, axis=1).sort_index()
        z_panels.append(cross_sectional_zscore(wide))
    if not z_panels:
        return pd.DataFrame()
    stacked = pd.concat(
        {i: p for i, p in enumerate(z_panels)}, axis=0, names=["panel", "date"]
    )
    return stacked.groupby(level="date").mean().sort_index()


_SENIOR_TITLE_PATTERN = r"\b(?:CEO|CFO|COO|PRESIDENT|CHAIR|CHAIRMAN)\b"


def weighted_insider_signal(
    trades: dict[str, pd.DataFrame],
    rebalance_dates: pd.DatetimeIndex,
    tickers: list[str],
    window_days: int = 90,
    min_transaction_value: float = 50_000.0,
    senior_only: bool = True,
) -> pd.DataFrame:
    """Net insider dollar flow restricted to senior officers and meaningful trades.

    Filters apply, in order:
      1. If `senior_only`, keep only rows where `title` matches CEO/CFO/COO/
         President/Chair* or `is_board_director` is True.
      2. Drop trades with absolute dollar value below `min_transaction_value`.

    Per Cohen-Malloy-Pomorski (2012) and Lakonishok-Lee (2001), routine
    small trades and trades by lower-ranked insiders carry far less
    predictive content than concentrated buying by C-suite officers. The
    raw `insider_buying_signal` is preserved for callers that want the
    unfiltered series.
    """
    out = pd.DataFrame(0.0, index=pd.DatetimeIndex(rebalance_dates), columns=list(tickers))
    ticker_set = set(tickers)
    for ticker, df in trades.items():
        if df.empty or ticker not in ticker_set:
            continue
        f = df
        if senior_only:
            title_mask = (
                f["title"].fillna("").str.upper().str.contains(_SENIOR_TITLE_PATTERN, regex=True)
                if "title" in f.columns
                else pd.Series(False, index=f.index)
            )
            director_mask = (
                f["is_board_director"].fillna(False)
                if "is_board_director" in f.columns
                else pd.Series(False, index=f.index)
            )
            f = f[title_mask | director_mask]
        if f.empty:
            continue
        if "transaction_shares" in f.columns and "transaction_price_per_share" in f.columns:
            dollar = f["transaction_shares"] * f["transaction_price_per_share"]
        elif "transaction_value" in f.columns:
            dollar = f["transaction_value"]
        else:
            continue
        dollar = dollar[dollar.abs() >= min_transaction_value].sort_index()
        for d in out.index:
            window_start = d - pd.Timedelta(days=window_days)
            out.at[d, ticker] = float(dollar.loc[window_start:d].sum())
    return out


def insider_buying_signal(
    trades: dict[str, pd.DataFrame],
    rebalance_dates: pd.DatetimeIndex,
    tickers: list[str],
    window_days: int = 90,
) -> pd.DataFrame:
    """Net insider dollar flow over the trailing window, per ticker per rebalance.

    The financialdatasets.ai schema reports `transaction_shares` signed
    (positive = acquired, negative = disposed) and a per-share price. Net
    dollar flow is shares * price. Falls back to `transaction_value` if
    shares/price aren't both present. Output is dollars; the caller is
    expected to z-score it cross-sectionally before combining with other
    factors.
    """
    out = pd.DataFrame(0.0, index=pd.DatetimeIndex(rebalance_dates), columns=list(tickers))
    ticker_set = set(tickers)
    for ticker, df in trades.items():
        if df.empty or ticker not in ticker_set:
            continue
        if "transaction_shares" in df.columns and "transaction_price_per_share" in df.columns:
            dollar_flow = df["transaction_shares"] * df["transaction_price_per_share"]
        elif "transaction_value" in df.columns:
            dollar_flow = df["transaction_value"]
        else:
            continue
        dollar_flow = dollar_flow.sort_index()
        for d in out.index:
            window_start = d - pd.Timedelta(days=window_days)
            window = dollar_flow.loc[window_start:d]
            out.at[d, ticker] = float(window.sum())
    return out
