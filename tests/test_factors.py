import numpy as np
import pandas as pd

from hedge_fund.factors import cross_sectional_zscore, momentum_12_1, quality_score


def test_momentum_12_1_uses_11_month_return_lagged():
    # 14 months of monthly prices, deterministic 1% per month growth on A,
    # 2% on B, flat on C. Momentum should rank B > A > C.
    idx = pd.date_range("2020-01-31", periods=14, freq="ME")
    prices = pd.DataFrame(
        {
            "A": 100 * (1.01 ** np.arange(14)),
            "B": 100 * (1.02 ** np.arange(14)),
            "C": np.full(14, 100.0),
        },
        index=idx,
    )
    mom = momentum_12_1(prices)
    last = mom.iloc[-1].dropna()
    assert last["B"] > last["A"] > last["C"]


def test_momentum_first_12_months_are_nan():
    idx = pd.date_range("2020-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        np.cumprod(1 + np.random.RandomState(0).normal(0, 0.01, (15, 3)), axis=0),
        index=idx,
        columns=list("ABC"),
    )
    mom = momentum_12_1(prices)
    assert mom.iloc[:12].isna().all().all()
    assert mom.iloc[12:].notna().any().any()


def test_cross_sectional_zscore_centers_each_row():
    df = pd.DataFrame({"A": [1.0, 10.0], "B": [3.0, 20.0], "C": [5.0, 30.0]})
    z = cross_sectional_zscore(df)
    assert np.allclose(z.mean(axis=1), 0.0, atol=1e-12)
    assert np.allclose(z.std(axis=1, ddof=1), 1.0, atol=1e-12)


def test_quality_score_aggregates_two_columns():
    idx = pd.date_range("2023-01-01", periods=4, freq="QE")
    metrics = {
        "A": pd.DataFrame(
            {"return_on_invested_capital": [0.20, 0.20, 0.20, 0.20],
             "gross_margin": [0.50, 0.50, 0.50, 0.50]},
            index=idx,
        ),
        "B": pd.DataFrame(
            {"return_on_invested_capital": [0.05, 0.05, 0.05, 0.05],
             "gross_margin": [0.20, 0.20, 0.20, 0.20]},
            index=idx,
        ),
        "C": pd.DataFrame(
            {"return_on_invested_capital": [0.10, 0.10, 0.10, 0.10],
             "gross_margin": [0.30, 0.30, 0.30, 0.30]},
            index=idx,
        ),
    }
    q = quality_score(metrics)
    assert not q.empty
    last = q.iloc[-1]
    assert last["A"] > last["C"] > last["B"]
