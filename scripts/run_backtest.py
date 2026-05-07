"""End-to-end demo: load a point-in-time universe, fetch prices/metrics/insider
trades, build a momentum + quality + insider-flow composite, and backtest with
universe masking.

Requires FINANCIAL_DATASETS_API_KEY in the environment.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from hedge_fund.backtest import run_backtest
from hedge_fund.data import FinancialDatasetsClient, load_price_panel
from hedge_fund.factors import (
    cross_sectional_zscore,
    insider_buying_signal,
    momentum_12_1,
    quality_score,
)
from hedge_fund.universe import PointInTimeUniverse

UNIVERSE_CSV = Path(__file__).resolve().parent.parent / "data" / "sp500_membership_sample.csv"


def main() -> None:
    client = FinancialDatasetsClient()
    start, end = date(2018, 1, 1), date(2024, 12, 31)

    universe = PointInTimeUniverse.from_csv(UNIVERSE_CSV)
    tickers = universe.all_tickers
    print(f"Universe has {len(tickers)} unique tickers across "
          f"{len(universe.snapshots)} snapshots.")

    print("Loading prices...")
    prices = load_price_panel(tickers, start, end, client)
    if prices.empty:
        raise SystemExit("No price data returned. Check your API key and tickers.")

    print("Loading financial metrics...")
    metrics = {t: client.get_financial_metrics(t) for t in tickers}

    print("Loading insider trades...")
    trades = {t: client.get_insider_trades(t) for t in tickers}

    monthly_dates = prices.resample("ME").last().index

    mom_z = cross_sectional_zscore(momentum_12_1(prices))
    qual_z = quality_score(metrics).reindex(mom_z.index).reindex(columns=mom_z.columns)
    insider_z = cross_sectional_zscore(
        insider_buying_signal(trades, monthly_dates, list(prices.columns))
    )

    combined = (
        mom_z.fillna(0.0)
        .add(qual_z.fillna(0.0))
        .add(insider_z.reindex(mom_z.index).reindex(columns=mom_z.columns).fillna(0.0))
        .div(3.0)
    )

    mask = universe.mask(monthly_dates, list(prices.columns))
    result = run_backtest(prices, combined, universe_mask=mask, top_pct=0.2, cost_bps=10.0)

    print("\nBacktest summary:")
    for k, v in result.summary().items():
        print(f"  {k:18s} {v:.4f}")

    client.close()


if __name__ == "__main__":
    main()
