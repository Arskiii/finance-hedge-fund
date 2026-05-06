"""Factor signal construction from price and fundamental panels."""
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


def quality_score(metrics: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Average cross-sectional z-score of return on invested capital and gross margin.

    Inputs are per-ticker fundamental frames indexed by report period. The
    output is monthly, forward-filled between reports. Note: this uses
    report period as the available-as-of date, which understates the true
    publication lag (typically 30-90 days for SEC filings).
    """
    cols = ("return_on_invested_capital", "gross_margin")
    z_panels: list[pd.DataFrame] = []
    for col in cols:
        per_ticker = {
            ticker: df[col].resample("ME").last().ffill()
            for ticker, df in metrics.items()
            if col in df.columns
        }
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
