---
name: earnings
description: Comprehensive earnings analysis — beat/miss, guidance changes, call highlights, and price reaction.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# Earnings Analysis

Analyze a company's earnings release and call in detail.

## Input
- `$ARGUMENTS`: Ticker symbol, optionally followed by quarter. Example: `NVDA` or `NVDA Q4 2025`
- If no quarter specified, analyze the most recent earnings.

## Process

1. **Pull reported financials** using SEC EDGAR MCP:
   - Latest 8-K (earnings release) or 10-Q.
   - Extract: revenue, EPS, gross margin, operating margin, segment breakdown.

2. **Pull consensus estimates** using WebSearch:
   - "{TICKER} earnings estimates Q{N} {YEAR}"
   - "{TICKER} consensus revenue EPS"
   - Find: consensus revenue, EPS, and margin expectations.

3. **Beat/Miss analysis:**

| Metric | Consensus | Actual | Result | Magnitude |
|--------|-----------|--------|--------|-----------|
| Revenue | ${val}M | ${val}M | Beat/Miss | +/- {%} |
| EPS | ${val} | ${val} | Beat/Miss | +/- ${val} |
| Gross Margin | {%} | {%} | Beat/Miss | +/- {bps} |
| Op Margin | {%} | {%} | Beat/Miss | +/- {bps} |

4. **Guidance analysis:**
   - Search for earnings call transcript via WebSearch.
   - Extract next-quarter and full-year guidance.
   - Compare to prior guidance: Raised / Cut / Maintained.
   - Compare to consensus expectations.

5. **Earnings call highlights:**
   - Top 3 positive takeaways
   - Top 3 concerns raised
   - Notable management commentary (paraphrased, not quoted verbatim)
   - Tone vs prior quarter: More/less confident?

6. **Price reaction** from Yahoo Finance MCP:
   - After-hours/pre-market move
   - 1-day close change
   - 5-day change
   - Volume vs 30-day average

7. **Thesis impact assessment:**
   - Does this quarter change the thesis? Yes/No
   - Any changes to fair value estimate?
   - Conviction impact: Increased / Decreased / Unchanged

8. **Read template** from `templates/earnings-summary.md` and use it to format output.

9. **Write output** to `analysis/{TICKER}/earnings/Q{N}_{YEAR}.md`.

10. **Display summary** to user: Beat/miss headline, guidance direction, and thesis impact.
