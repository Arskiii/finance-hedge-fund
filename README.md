# finance-hedge-fund

A starter quantitative research platform for systematic equity strategies.

**This is a foundation, not an edge.** The repo gives you the plumbing — data
ingestion, factor computation, vectorized backtesting, performance metrics — so
you can iterate on theses quickly. It does not give you a profitable strategy.
The included quality+momentum demo is a textbook factor combination, well-known
and crowded.

## Layout

| Path | Purpose |
| ---- | ------- |
| `src/hedge_fund/data.py` | Adapter for the financialdatasets.ai REST API (prices, fundamentals, insider trades, filings) and a sectors CSV loader |
| `src/hedge_fund/factors.py` | 12-1 momentum, filing-lagged quality, raw and senior-only insider signals |
| `src/hedge_fund/risk.py` | Rolling beta, sector and beta neutralization |
| `src/hedge_fund/universe.py` | Point-in-time index membership |
| `src/hedge_fund/llm.py` | `FilingAnalyzer` — Claude-backed structured scoring with prompt caching |
| `src/hedge_fund/filings.py` | Fetch and score 10-K/10-Q sections; aggregate into a per-rebalance signal |
| `src/hedge_fund/backtest.py` | Monthly long-only top-quantile backtester with optional universe mask |
| `data/sp500_membership_sample.csv` | Sample (as_of_date, ticker) snapshots — replace with a real source |
| `data/sectors_sample.csv` | Sample (ticker, sector) classification — replace with a real source |
| `scripts/run_backtest.py` | Full pipeline: signals → sector/beta neutralization → masked backtest |
| `tests/` | Unit tests for factors, risk, universe, llm, filings, and the backtester |

## Setup

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,llm]"   # drop ",llm" if you don't want the Anthropic SDK
cp .env.example .env          # fill FINANCIAL_DATASETS_API_KEY (and optionally ANTHROPIC_API_KEY)
```

## Run

```sh
pytest                         # offline, uses synthetic data
python scripts/run_backtest.py # hits the live API
```

## Honest limitations

1. **Survivorship bias — partially addressed.** `PointInTimeUniverse` enforces
   that only names in the index on date `t` can be selected at `t`. The
   bundled sample CSV has three snapshots and is illustrative only — for real
   work, replace it with a proper membership source (CRSP/Compustat, the
   iShares holdings history, or a curated Wikipedia + delisting log).
2. **Fundamental look-ahead — partially addressed.** `quality_score` stamps
   each row with `filing_date` if the API exposes it, otherwise applies a
   conservative 75-day lag from `report_period`. Restatements and amendments
   are not handled.
3. **Naïve transaction costs.** A flat 10 bps assumption ignores liquidity,
   market impact, and short borrow costs.
4. **Partial risk model.** `sector_neutralize` and `beta_neutralize` strip
   the most obvious unintended exposures, but there is still no full factor
   risk model (Barra-style), no explicit position limits, and the long-only
   selection still tilts toward whatever residual factor the signal loads on.
5. **Static sector mapping.** `sectors_sample.csv` is constant in time;
   reclassifications (META 2018 IT → Comm. Services) are ignored.
6. **No execution layer.** The backtester stops at portfolio weights; live
   trading requires broker integration, slippage modeling, and monitoring.
7. **Insider-flow signal still simplified.** `weighted_insider_signal`
   filters to senior officers / directors and meaningful trade sizes, but
   does not exclude 10b5-1 planned trades, weight by deviation from each
   insider's baseline, or detect clustered buying. The literature shows
   those refinements carry most of the remaining predictive content
   (Cohen-Malloy-Pomorski 2012; Lakonishok-Lee 2001).
8. **Filing-sentiment costs and caching.** Each filing scored is one
   Anthropic API call. `fetch_and_score_filings` does no persistence — a
   real backtest should cache per-filing scores to disk so you only pay
   for new filings. Truncating long filings to 60k chars is a cost / signal
   trade-off; the model may miss material in items past the cutoff.

## What it takes to actually run a fund

The platform above is table stakes. None of the items below are software
problems, and all are required to compete:

- A **differentiated thesis** — alt-data, longer holding periods, or a niche
  where competition is thinner. Public-data factor strategies are largely
  arbitraged.
- **Point-in-time data** with proper survivorship correction.
- A **risk and portfolio-construction layer** beyond equal-weight quintiles
  (e.g., mean-variance / Black-Litterman / hierarchical risk parity, with
  factor exposure and turnover constraints).
- **Legal and operational infrastructure** — fund admin, prime broker, auditor,
  compliance officer, RIA / CPO-CTA registration.
- A **track record** built on paper, then own capital, before institutional
  allocators will return your call.
