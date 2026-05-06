import numpy as np
import pandas as pd

from hedge_fund.backtest import BacktestResult, run_backtest, top_quantile_weights


def test_top_quantile_weights_sum_to_one_and_select_top_pct():
    signal = pd.DataFrame(
        {f"S{i}": [float(i)] for i in range(10)},
        index=[pd.Timestamp("2024-01-31")],
    )
    weights = top_quantile_weights(signal, top_pct=0.2)
    assert np.isclose(weights.sum(axis=1).iloc[0], 1.0)
    # Top 20% of 10 names = 2; the two highest signals are S9 and S8.
    selected = weights.columns[(weights.iloc[0] > 0).values].tolist()
    assert set(selected) == {"S8", "S9"}


def test_top_quantile_ignores_nan_signals():
    signal = pd.DataFrame(
        {"A": [np.nan], "B": [1.0], "C": [2.0], "D": [3.0], "E": [4.0]},
        index=[pd.Timestamp("2024-01-31")],
    )
    weights = top_quantile_weights(signal, top_pct=0.25)
    assert weights.iloc[0]["A"] == 0.0


def test_backtest_picks_top_assets_and_grows_equity():
    np.random.seed(0)
    idx = pd.date_range("2020-01-01", periods=600, freq="B")
    n = 10
    drifts = np.linspace(0.0002, 0.0010, n)  # S0 worst, S9 best
    rets = np.random.normal(loc=drifts, scale=0.005, size=(len(idx), n))
    prices = pd.DataFrame(
        np.cumprod(1 + rets, axis=0) * 100.0,
        index=idx,
        columns=[f"S{i}" for i in range(n)],
    )
    monthly_idx = prices.resample("ME").last().index
    # Signal equals the drift rank — perfect foresight, constant in time.
    signal = pd.DataFrame(
        np.tile(drifts, (len(monthly_idx), 1)),
        index=monthly_idx,
        columns=prices.columns,
    )
    result = run_backtest(prices, signal, top_pct=0.2, cost_bps=0.0)
    assert isinstance(result, BacktestResult)
    assert result.equity_curve.iloc[-1] > 1.0
    # Latest weights should hold S8 and S9 (the two highest-drift names).
    last_w = result.weights.dropna(how="all").iloc[-1]
    assert last_w["S9"] > 0 and last_w["S8"] > 0
    assert last_w["S0"] == 0


def test_backtest_summary_contains_expected_keys():
    np.random.seed(1)
    idx = pd.date_range("2021-01-01", periods=300, freq="B")
    prices = pd.DataFrame(
        np.cumprod(1 + np.random.normal(0.0005, 0.01, (300, 5)), axis=0) * 100,
        index=idx,
        columns=list("ABCDE"),
    )
    monthly_idx = prices.resample("ME").last().index
    signal = pd.DataFrame(
        np.random.normal(size=(len(monthly_idx), 5)),
        index=monthly_idx,
        columns=list("ABCDE"),
    )
    summary = run_backtest(prices, signal).summary()
    assert set(summary) == {"cagr", "sharpe", "max_drawdown", "vol_annualized", "n_months"}
