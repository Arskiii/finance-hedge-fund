"""End-to-end demo: pull prices and metrics, build a quality+momentum signal,
and run the monthly long-only top-quintile backtest.

Requires FINANCIAL_DATASETS_API_KEY in the environment.
"""
from __future__ import annotations

from datetime import date

from hedge_fund.backtest import run_backtest
from hedge_fund.data import DEFAULT_UNIVERSE, FinancialDatasetsClient, load_price_panel
from hedge_fund.factors import cross_sectional_zscore, momentum_12_1, quality_score


def main() -> None:
    client = FinancialDatasetsClient()
    start, end = date(2018, 1, 1), date(2024, 12, 31)

    print(f"Loading prices for {len(DEFAULT_UNIVERSE)} tickers...")
    prices = load_price_panel(DEFAULT_UNIVERSE, start, end, client)
    if prices.empty:
        raise SystemExit("No price data returned. Check your API key and tickers.")

    print("Loading financial metrics...")
    metrics = {t: client.get_financial_metrics(t) for t in DEFAULT_UNIVERSE}

    mom_z = cross_sectional_zscore(momentum_12_1(prices))
    qual_z = quality_score(metrics).reindex(mom_z.index).reindex(columns=mom_z.columns)

    combined = mom_z.add(qual_z, fill_value=0.0).div(2.0)

    result = run_backtest(prices, combined, top_pct=0.2, cost_bps=10.0)

    print("\nBacktest summary:")
    for k, v in result.summary().items():
        print(f"  {k:18s} {v:.4f}")

    client.close()


if __name__ == "__main__":
    main()
