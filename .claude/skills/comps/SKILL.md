---
name: comps
description: Build comparable company valuation tables with implied fair value range. Optionally specify peers or auto-select.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# Comparable Company Analysis

Build a comps table and derive implied fair value from peer multiples.

## Input
- `$ARGUMENTS`: Primary ticker, optionally followed by comma-separated peer tickers.
  - Examples: `AAPL`, `AAPL MSFT,GOOGL,AMZN,META`
  - If no peers provided, auto-select 5-8 relevant peers.

## Process

1. **Identify the primary company** using Yahoo Finance MCP:
   - Get sector, industry, market cap, and business description.

2. **Select peers** (if not provided):
   - Search "{TICKER} competitors" and "{TICKER} peer companies" via WebSearch.
   - Use Yahoo Finance MCP to pull sector/industry peers.
   - Select 5-8 peers by: same industry, similar market cap range, similar business model.
   - Exclude companies from different sectors unless directly competitive.

3. **Pull financial data** for primary + all peers using Yahoo Finance MCP and SEC EDGAR MCP:
   - Market cap, enterprise value
   - Revenue (TTM), EBITDA (TTM), net income (TTM), FCF (TTM)
   - Revenue growth rates (1yr, 3yr CAGR)
   - Margins: gross, operating, net, FCF
   - Balance sheet: net debt, cash
   - NTM estimates if available via WebSearch

4. **Build the comps table:**

| Company | Ticker | Mkt Cap ($B) | EV ($B) | EV/Rev | EV/EBITDA | P/E | FCF Yield | Rev Gr 3Y | EBITDA Mgn | Net Debt ($B) |
|---------|--------|-------------|---------|--------|-----------|-----|-----------|-----------|------------|--------------|
| **{PRIMARY}** | | | | | | | | | | |
| {Peer 1} | | | | | | | | | | |
| ... | | | | | | | | | | |
| **Median** | | | | **{x}** | **{x}** | **{x}** | **{%}** | **{%}** | **{%}** | |
| **Mean** | | | | **{x}** | **{x}** | **{x}** | **{%}** | **{%}** | **{%}** | |

5. **Calculate implied fair values:**

| Multiple | Peer Median | Applied Metric | Implied EV/Price | vs Current |
|----------|------------|----------------|-----------------|------------|
| EV/EBITDA | {x} | EBITDA: ${val}M | ${price} | {+/- %} |
| EV/Revenue | {x} | Rev: ${val}M | ${price} | {+/- %} |
| P/E | {x} | EPS: ${val} | ${price} | {+/- %} |

   - Fair value range: 25th percentile to 75th percentile of peer multiples.

6. **Commentary:**
   - Premium/discount justification for the primary company.
   - Most comparable peer and why.
   - Key differentiators (positive and negative).

7. **Read template** from `templates/comps-table.md` and use it to format output.

8. **Write output** to `analysis/{TICKER}/comps.md`.

9. **Display summary**: Current valuation vs peer median, implied upside/downside, and fair value range.
