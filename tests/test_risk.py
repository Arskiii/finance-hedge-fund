import numpy as np
import pandas as pd
import pytest

from hedge_fund.risk import beta_neutralize, rolling_beta, sector_neutralize


def test_rolling_beta_recovers_constructed_beta():
    np.random.seed(0)
    n = 600
    market = pd.Series(np.random.normal(0, 0.01, n), index=pd.date_range("2020-01-01", periods=n))
    # A has beta 1.5, B has beta 0.5, plus idiosyncratic noise.
    a = 1.5 * market + np.random.normal(0, 0.005, n)
    b = 0.5 * market + np.random.normal(0, 0.005, n)
    returns = pd.DataFrame({"A": a.values, "B": b.values}, index=market.index)
    betas = rolling_beta(returns, market, window=252, min_periods=60)
    last_a = betas["A"].dropna().iloc[-1]
    last_b = betas["B"].dropna().iloc[-1]
    assert last_a == pytest.approx(1.5, abs=0.1)
    assert last_b == pytest.approx(0.5, abs=0.1)


def test_sector_neutralize_demeans_within_sector():
    signal = pd.DataFrame(
        {"A": [1.0, 2.0], "B": [3.0, 4.0], "C": [10.0, 20.0]},
        index=pd.to_datetime(["2024-01-31", "2024-02-29"]),
    )
    sectors = pd.Series({"A": "Tech", "B": "Tech", "C": "Energy"})
    out = sector_neutralize(signal, sectors)
    # Tech mean per row: 2 and 3 -> A becomes -1, -1; B becomes 1, 1.
    assert out.loc["2024-01-31", "A"] == pytest.approx(-1.0)
    assert out.loc["2024-01-31", "B"] == pytest.approx(1.0)
    # Single-name sector demeans to zero.
    assert out.loc["2024-01-31", "C"] == pytest.approx(0.0)
    assert out.loc["2024-02-29", "C"] == pytest.approx(0.0)


def test_sector_neutralize_unknown_bucket_for_missing():
    signal = pd.DataFrame({"A": [1.0], "B": [3.0]}, index=[pd.Timestamp("2024-01-31")])
    sectors = pd.Series({"A": "Tech"})  # B has no sector
    out = sector_neutralize(signal, sectors)
    # B is alone in UNKNOWN; demeans to zero.
    assert out.loc["2024-01-31", "B"] == pytest.approx(0.0)


def test_beta_neutralize_removes_beta_correlation():
    rng = np.random.default_rng(1)
    n_dates, n_names = 5, 50
    betas = pd.DataFrame(
        rng.uniform(0.5, 2.0, (n_dates, n_names)),
        index=pd.date_range("2024-01-31", periods=n_dates, freq="ME"),
        columns=[f"S{i}" for i in range(n_names)],
    )
    # Construct signal as 2*beta + noise — strongly correlated with beta.
    signal = 2.0 * betas + rng.normal(0, 0.1, betas.shape)
    residuals = beta_neutralize(signal, betas)
    # Cross-sectional correlation of residuals with beta should be ~0.
    for d in residuals.index:
        corr = residuals.loc[d].corr(betas.loc[d])
        assert abs(corr) < 0.05


def test_beta_neutralize_passthrough_when_too_few_names():
    signal = pd.DataFrame({"A": [1.0], "B": [2.0]}, index=[pd.Timestamp("2024-01-31")])
    betas = pd.DataFrame({"A": [1.0], "B": [1.5]}, index=[pd.Timestamp("2024-01-31")])
    out = beta_neutralize(signal, betas)
    pd.testing.assert_frame_equal(out, signal)
