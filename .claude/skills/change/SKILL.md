---
name: change
description: Analyze material changes from the last quarter — financial, strategic, management, risk, and competitive.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# Last Quarter Changes Analysis

Identify and categorize everything that materially changed for a company last quarter.

## Input
- `$ARGUMENTS`: Ticker symbol (required). Example: `AMZN`

## Process

1. **Pull SEC filings** using SEC EDGAR MCP:
   - Latest 10-Q and the prior 10-Q for comparison.
   - Any recent 8-K filings (material events).

2. **Search for recent news and earnings** using WebSearch:
   - "{TICKER} earnings call transcript latest quarter"
   - "{TICKER} news last 90 days"
   - "{TICKER} analyst upgrades downgrades"

3. **Pull market data** from Yahoo Finance MCP:
   - Stock price performance last quarter.
   - Analyst recommendation changes.
   - Any significant volume events.

4. **Categorize all material changes:**

### Financial Changes
| Change | Prior Q | Current Q | Delta | Impact |
|--------|---------|-----------|-------|--------|
| Revenue trajectory | | | | {+/-} |
| Gross margin | {%} | {%} | {bps} | {+/-} |
| Operating margin | {%} | {%} | {bps} | {+/-} |
| FCF generation | | | | {+/-} |
| Debt level | | | | {+/-} |

### Strategic Changes
- New products/services launched
- Acquisitions or divestitures
- Geographic expansion or contraction
- Major partnerships or contract wins/losses
- Pricing actions

### Management Changes
- Executive departures or hires
- Board changes
- Compensation structure changes
- Activist investor involvement

### Risk Changes
- New risk factors added to 10-Q
- Litigation updates
- Regulatory changes
- Customer concentration changes

### Market/Competitive Changes
- Pricing actions by competitors
- Market share shifts
- New entrants or exits
- Industry-wide trends

5. **Rate each change**: Positive / Negative / Neutral with impact magnitude (1-5 scale).

6. **Net assessment**: Overall, did the company's position improve, deteriorate, or stay flat?

7. **Write output** to `analysis/{TICKER}/changes/Q{N}_{YEAR}.md`.

8. **Display summary**: Top 3 most impactful changes with ratings.
