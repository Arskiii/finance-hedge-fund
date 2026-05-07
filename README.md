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
| `src/hedge_fund/data.py` | Adapter for the financialdatasets.ai REST API (prices, financial metrics, insider trades) |
| `src/hedge_fund/factors.py` | 12-1 momentum, quality (filing-lagged), and insider-buying signals |
| `src/hedge_fund/universe.py` | Point-in-time index membership |
| `src/hedge_fund/backtest.py` | Monthly long-only top-quantile backtester with optional universe mask |
| `data/sp500_membership_sample.csv` | Tiny sample of (as_of_date, ticker) snapshots — replace with a real source |
| `scripts/run_backtest.py` | End-to-end demo combining all three signals with universe masking |
| `tests/` | Unit tests for factors, universe, and the backtester |

## Setup

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in FINANCIAL_DATASETS_API_KEY
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
4. **No risk model.** Production work needs factor risk decomposition,
   sector/beta neutrality, and explicit position limits.
5. **No execution layer.** The backtester stops at portfolio weights; live
   trading requires broker integration, slippage modeling, and monitoring.
6. **Insider-flow signal is unsophisticated.** Net dollar flow ignores
   officer rank, prior trading patterns, 10b5-1 plans, and clustering — all
   of which carry most of the predictive content in the academic literature.

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
