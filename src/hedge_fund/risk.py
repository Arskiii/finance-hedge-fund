"""Risk-model utilities: rolling beta, sector and beta neutralization.

A long-only top-quintile portfolio built directly on a raw signal usually
ends up loaded on whatever sector or beta the signal happens to correlate
with. These helpers strip out those exposures so the backtest reflects the
signal's idiosyncratic content rather than a sector or beta bet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_beta(
    returns: pd.DataFrame,
    market: pd.Series,
    window: int = 252,
    min_periods: int = 60,
) -> pd.DataFrame:
    """Rolling OLS beta of each column to the market series.

    Aligned on the inner intersection of dates. Output entry [t, i] is the
    beta of column i estimated over the trailing `window` observations
    ending at t.
    """
    aligned, m = returns.align(market, axis=0, join="inner")
    cov = aligned.rolling(window, min_periods=min_periods).cov(m)
    var = m.rolling(window, min_periods=min_periods).var()
    return cov.div(var, axis=0)


def sector_neutralize(signal: pd.DataFrame, sectors: pd.Series) -> pd.DataFrame:
    """Subtract the sector mean from each name's signal at every date.

    `sectors` maps ticker -> sector label. Names with no mapping are placed
    in an "UNKNOWN" bucket and demeaned within that bucket.
    """
    aligned = sectors.reindex(signal.columns).fillna("UNKNOWN")
    means = signal.T.groupby(aligned, sort=False).transform("mean").T
    return signal - means


def beta_neutralize(signal: pd.DataFrame, betas: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional residualization of `signal` against `betas`.

    For each row, fits y = a + c*x by OLS and returns residuals. Rows with
    fewer than three valid (signal, beta) pairs or constant betas are
    returned unchanged.
    """
    betas = betas.reindex_like(signal)
    valid = signal.notna() & betas.notna()
    n = valid.sum(axis=1)
    x = betas.where(valid)
    y = signal.where(valid)
    x_mean = x.mean(axis=1)
    y_mean = y.mean(axis=1)
    x_dev = x.sub(x_mean, axis=0)
    y_dev = y.sub(y_mean, axis=0)
    cov = (x_dev * y_dev).sum(axis=1)
    var = (x_dev ** 2).sum(axis=1)
    c = (cov / var.replace(0.0, np.nan)).fillna(0.0)
    a = y_mean - c * x_mean
    fitted = betas.mul(c, axis=0).add(a, axis=0)
    residuals = signal - fitted
    return residuals.where(n >= 3, signal)
