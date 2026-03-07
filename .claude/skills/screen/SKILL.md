---
name: screen
description: Quantitative stock screening against investment criteria defined in CLAUDE.md. Pass a sector name, ticker list, or custom filters.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# Stock Screener

Screen stocks against the investment criteria defined in CLAUDE.md.

## Input
- `$ARGUMENTS`: Sector name (e.g., "Technology"), comma-separated tickers, or custom filter description.
- If no arguments provided, use default criteria from CLAUDE.md across all focus sectors.

## Process

1. **Parse input**: Determine if screening by sector, specific tickers, or custom criteria.

2. **Gather screening data** using Yahoo Finance MCP and WebSearch:
   - For sector screening: search for top companies in the sector by market cap.
   - For ticker list: pull data for each specified ticker.
   - Pull for each candidate: market cap, revenue (3yr history), ROIC, net debt/EBITDA, insider ownership %.

3. **Apply CLAUDE.md screening criteria** to each candidate:
   - Revenue growth > 5% CAGR (3yr): Pass/Fail
   - ROIC > 12% (or improving): Pass/Fail
   - Net Debt/EBITDA < 3x: Pass/Fail
   - Insider ownership > 2%: Pass/Fail
   - Market cap > $500M: Pass/Fail
   - Not a recent IPO (< 2 years): Pass/Fail

4. **Score and rank** passing candidates:
   - +1 point per percentage of revenue growth above 5%.
   - +2 points per percentage of ROIC above 12%.
   - +1 point if Net Debt/EBITDA < 1x (strong balance sheet).
   - +1 point per percentage of insider ownership above 2%.

5. **Output results** to `analysis/screen_{DATE}.md`:

| Rank | Ticker | Company | Sector | Mkt Cap | Rev Gr 3Y | ROIC | Debt/EBITDA | Insider % | Score | Pass/Fail |
|------|--------|---------|--------|---------|-----------|------|-------------|-----------|-------|-----------|

6. **Highlight top 5** with a 2-sentence thesis for each explaining why it merits further diligence.

7. **Display summary** to the user with the top candidates and suggested next step: "Run `/diligence-checklist {TICKER}` for a deep dive."
