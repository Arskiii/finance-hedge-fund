import numpy as np
import pandas as pd
import pytest

from hedge_fund.factors import (
    cross_sectional_zscore,
    insider_buying_signal,
    momentum_12_1,
    quality_score,
    weighted_insider_signal,
)


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


def test_quality_score_lags_report_period_by_default():
    # report_period 2023-03-31 with default 75-day lag becomes available
    # ~2023-06-14, so first non-NaN row should be no earlier than 2023-06-30.
    idx = pd.date_range("2023-03-31", periods=2, freq="QE")
    metrics = {
        "A": pd.DataFrame(
            {"return_on_invested_capital": [0.2, 0.2], "gross_margin": [0.5, 0.5]},
            index=idx,
        ),
        "B": pd.DataFrame(
            {"return_on_invested_capital": [0.1, 0.1], "gross_margin": [0.3, 0.3]},
            index=idx,
        ),
    }
    q = quality_score(metrics, filing_lag_days=75)
    first = q.dropna(how="all").index.min()
    assert first >= pd.Timestamp("2023-06-30")


def test_quality_score_uses_filing_date_when_present():
    idx = pd.date_range("2023-03-31", periods=2, freq="QE")
    # filing_date is two months earlier than report_period+lag would suggest;
    # the explicit field should win.
    df_a = pd.DataFrame(
        {
            "return_on_invested_capital": [0.2, 0.2],
            "gross_margin": [0.5, 0.5],
            "filing_date": ["2023-04-15", "2023-07-15"],
        },
        index=idx,
    )
    df_b = pd.DataFrame(
        {
            "return_on_invested_capital": [0.1, 0.1],
            "gross_margin": [0.3, 0.3],
            "filing_date": ["2023-04-15", "2023-07-15"],
        },
        index=idx,
    )
    q = quality_score({"A": df_a, "B": df_b}, filing_lag_days=75)
    first = q.dropna(how="all").index.min()
    assert first == pd.Timestamp("2023-04-30")


def test_insider_buying_signal_sums_window():
    trades = {
        "A": pd.DataFrame(
            {
                "transaction_shares": [1000, -500, 2000],
                "transaction_price_per_share": [100.0, 100.0, 100.0],
            },
            index=pd.to_datetime(["2024-01-15", "2024-02-15", "2024-03-15"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-03-31"])
    sig = insider_buying_signal(trades, rebalance, ["A"], window_days=120)
    assert sig.loc["2024-03-31", "A"] == pytest.approx(250_000.0)


def test_insider_buying_signal_excludes_outside_window():
    trades = {
        "A": pd.DataFrame(
            {
                "transaction_shares": [1000, 1000],
                "transaction_price_per_share": [100.0, 100.0],
            },
            index=pd.to_datetime(["2024-01-01", "2024-06-01"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-06-30"])
    sig = insider_buying_signal(trades, rebalance, ["A"], window_days=60)
    # Only the 2024-06-01 trade falls in the 60-day window.
    assert sig.loc["2024-06-30", "A"] == pytest.approx(100_000.0)


def test_insider_buying_signal_skips_tickers_without_data():
    rebalance = pd.DatetimeIndex(["2024-03-31"])
    sig = insider_buying_signal({}, rebalance, ["A", "B"], window_days=90)
    assert sig.shape == (1, 2)
    assert (sig == 0.0).all().all()


def test_weighted_insider_signal_filters_to_senior_titles():
    trades = {
        "A": pd.DataFrame(
            {
                "title": ["CEO", "Junior Engineer", "CFO"],
                "is_board_director": [False, False, False],
                "transaction_shares": [1000, 1000, 1000],
                "transaction_price_per_share": [100.0, 100.0, 100.0],
            },
            index=pd.to_datetime(["2024-03-01", "2024-03-05", "2024-03-10"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-03-31"])
    sig = weighted_insider_signal(trades, rebalance, ["A"], window_days=90)
    # Junior Engineer trade dropped; CEO + CFO = 200_000.
    assert sig.loc["2024-03-31", "A"] == pytest.approx(200_000.0)


def test_weighted_insider_signal_includes_directors_without_senior_title():
    trades = {
        "A": pd.DataFrame(
            {
                "title": ["Director", "Junior Engineer"],
                "is_board_director": [True, False],
                "transaction_shares": [500, 500],
                "transaction_price_per_share": [200.0, 200.0],
            },
            index=pd.to_datetime(["2024-03-01", "2024-03-10"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-03-31"])
    sig = weighted_insider_signal(trades, rebalance, ["A"], window_days=90)
    assert sig.loc["2024-03-31", "A"] == pytest.approx(100_000.0)


def test_weighted_insider_signal_drops_small_trades():
    trades = {
        "A": pd.DataFrame(
            {
                "title": ["CEO", "CEO"],
                "is_board_director": [False, False],
                "transaction_shares": [10, 1000],   # $1k and $100k
                "transaction_price_per_share": [100.0, 100.0],
            },
            index=pd.to_datetime(["2024-03-01", "2024-03-10"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-03-31"])
    sig = weighted_insider_signal(trades, rebalance, ["A"], min_transaction_value=50_000.0)
    assert sig.loc["2024-03-31", "A"] == pytest.approx(100_000.0)
