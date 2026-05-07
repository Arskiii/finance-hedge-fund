"""End-to-end demo:

  1. Load a point-in-time universe and a sectors map.
  2. Pull prices, financial metrics, insider trades, and a market proxy.
  3. Build a momentum + quality + senior-insider composite (and, if
     ANTHROPIC_API_KEY is set, blend in Claude-scored filing sentiment).
  4. Sector- and beta-neutralize the composite.
  5. Backtest with universe masking.

Requires FINANCIAL_DATASETS_API_KEY in the environment. ANTHROPIC_API_KEY
is optional and enables the LLM-based filing-sentiment signal.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from hedge_fund.backtest import run_backtest
from hedge_fund.data import FinancialDatasetsClient, load_price_panel, load_sectors
from hedge_fund.factors import (
    cross_sectional_zscore,
    momentum_12_1,
    quality_score,
    weighted_insider_signal,
)
from hedge_fund.risk import beta_neutralize, rolling_beta, sector_neutralize
from hedge_fund.universe import PointInTimeUniverse

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UNIVERSE_CSV = DATA_DIR / "sp500_membership_sample.csv"
SECTORS_CSV = DATA_DIR / "sectors_sample.csv"
MARKET_TICKER = "SPY"


def main() -> None:
    client = FinancialDatasetsClient()
    start, end = date(2018, 1, 1), date(2024, 12, 31)

    universe = PointInTimeUniverse.from_csv(UNIVERSE_CSV)
    sectors = load_sectors(SECTORS_CSV)
    tickers = universe.all_tickers
    print(f"Universe: {len(tickers)} tickers, {len(universe.snapshots)} snapshots.")

    print("Loading prices...")
    prices = load_price_panel(tickers, start, end, client)
    if prices.empty:
        raise SystemExit("No price data returned. Check your API key and tickers.")

    print(f"Loading market proxy {MARKET_TICKER}...")
    market_df = client.get_prices(MARKET_TICKER, start, end)
    market_returns = market_df["close"].pct_change().rename(MARKET_TICKER)

    print("Loading financial metrics and insider trades...")
    metrics = {t: client.get_financial_metrics(t) for t in tickers}
    trades = {t: client.get_insider_trades(t) for t in tickers}

    monthly_dates = prices.resample("ME").last().index

    # --- factor signals ---
    mom_z = cross_sectional_zscore(momentum_12_1(prices))
    qual_z = quality_score(metrics).reindex(mom_z.index).reindex(columns=mom_z.columns)
    insider_z = cross_sectional_zscore(
        weighted_insider_signal(trades, monthly_dates, list(prices.columns))
    )

    factor_zscores = [mom_z, qual_z, insider_z]

    if os.environ.get("ANTHROPIC_API_KEY"):
        from hedge_fund.filings import fetch_and_score_filings, filing_sentiment_signal
        from hedge_fund.llm import FilingAnalyzer

        print("Scoring filings with Claude...")
        analyzer = FilingAnalyzer()
        sentiment_per_ticker = fetch_and_score_filings(tickers, client, analyzer)
        sentiment_z = cross_sectional_zscore(
            filing_sentiment_signal(
                sentiment_per_ticker, monthly_dates, list(prices.columns)
            )
        )
        factor_zscores.append(sentiment_z)
    else:
        print("ANTHROPIC_API_KEY not set; skipping filing-sentiment factor.")

    template = mom_z
    aligned = [
        z.reindex(template.index).reindex(columns=template.columns).fillna(0.0)
        for z in factor_zscores
    ]
    composite = sum(aligned) / len(aligned)

    # --- risk neutralization ---
    daily_returns = prices.pct_change()
    betas = rolling_beta(daily_returns, market_returns).resample("ME").last()
    betas = betas.reindex(composite.index).reindex(columns=composite.columns)
    composite = sector_neutralize(composite, sectors)
    composite = beta_neutralize(composite, betas)

    mask = universe.mask(monthly_dates, list(prices.columns))
    result = run_backtest(prices, composite, universe_mask=mask, top_pct=0.2, cost_bps=10.0)

    print("\nBacktest summary:")
    for k, v in result.summary().items():
        print(f"  {k:18s} {v:.4f}")

    client.close()


if __name__ == "__main__":
    main()
