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
| `src/hedge_fund/data.py` | Adapter for the financialdatasets.ai REST API |
| `src/hedge_fund/factors.py` | 12-1 momentum and quality factor signals |
| `src/hedge_fund/backtest.py` | Monthly long-only top-quantile backtester with metrics |
| `scripts/run_backtest.py` | Runnable end-to-end example |
| `tests/` | Unit tests for factors and the backtester |

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

1. **Survivorship bias.** The demo universe is today's mega-caps. Real backtests
   require point-in-time index membership snapshots.
2. **Fundamental look-ahead.** `quality_score` uses the report period as the
   available-as-of date; the actual filing typically lags by 30-90 days.
3. **Naïve transaction costs.** A flat 10 bps assumption ignores liquidity,
   market impact, and short borrow costs.
4. **No risk model.** Production work needs factor risk decomposition,
   sector/beta neutrality, and explicit position limits.
5. **No execution layer.** The backtester stops at portfolio weights; live
   trading requires broker integration, slippage modeling, and monitoring.

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
