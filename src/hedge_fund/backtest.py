"""Vectorized monthly long-only backtester for cross-sectional factor signals."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    returns: pd.Series
    weights: pd.DataFrame
    equity_curve: pd.Series

    @property
    def cagr(self) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        years = (self.returns.index[-1] - self.returns.index[0]).days / 365.25
        if years <= 0:
            return 0.0
        return float(self.equity_curve.iloc[-1] ** (1 / years) - 1)

    @property
    def sharpe(self) -> float:
        std = self.returns.std()
        if std == 0 or np.isnan(std):
            return 0.0
        return float(self.returns.mean() / std * np.sqrt(12))

    @property
    def max_drawdown(self) -> float:
        cummax = self.equity_curve.cummax()
        return float((self.equity_curve / cummax - 1).min())

    def summary(self) -> dict[str, float]:
        return {
            "cagr": self.cagr,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "vol_annualized": float(self.returns.std() * np.sqrt(12)),
            "n_months": int(len(self.returns)),
        }


def top_quantile_weights(signal: pd.DataFrame, top_pct: float = 0.2) -> pd.DataFrame:
    """Equal-weight the top `top_pct` of names by signal each row, zero elsewhere."""
    ranks = signal.rank(axis=1, pct=True, ascending=False)
    selected = (ranks <= top_pct) & signal.notna()
    counts = selected.sum(axis=1).replace(0, np.nan)
    return selected.div(counts, axis=0).fillna(0.0)


def run_backtest(
    prices: pd.DataFrame,
    signal: pd.DataFrame,
    top_pct: float = 0.2,
    cost_bps: float = 10.0,
) -> BacktestResult:
    """Monthly rebalanced long-only backtest.

    The signal value at month-end t determines weights held over [t, t+1].
    Transaction costs are charged on turnover at the rebalance.
    """
    monthly = prices.resample("ME").last()
    fwd_returns = monthly.pct_change().shift(-1)
    aligned = signal.reindex(monthly.index).reindex(columns=monthly.columns)
    weights = top_quantile_weights(aligned, top_pct=top_pct)

    gross = (weights * fwd_returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = float(weights.iloc[0].abs().sum())
    costs = turnover * (cost_bps / 10_000.0)
    net = (gross - costs).dropna()

    equity = (1 + net).cumprod()
    return BacktestResult(returns=net, weights=weights, equity_curve=equity)
