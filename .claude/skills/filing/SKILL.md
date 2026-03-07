---
name: filing
description: SEC filings analysis comparing current filing to prior periods. Supports 10-K, 10-Q, and 8-K analysis.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# SEC Filing Analysis

Analyze SEC filings for a company, comparing current period to prior periods.

## Input
- `$ARGUMENTS`: Ticker symbol followed by optional filing type and period count.
  - Examples: `MSFT`, `MSFT 10-K`, `AAPL 10-Q 6`
  - Default filing type: 10-Q
  - Default comparison periods: 4

## Process

1. **Look up the CIK** for the ticker using SEC EDGAR MCP.

2. **Retrieve filings** using SEC EDGAR MCP:
   - Pull the latest filing of the specified type.
   - Pull the prior N filings of the same type for comparison.

3. **Extract key financial data** from each filing:

### Income Statement
| Metric | Current | Q-1 | Q-2 | Q-3 | YoY |
|--------|---------|-----|-----|-----|-----|
| Revenue | | | | | {%} |
| Gross Profit | | | | | {%} |
| Operating Income | | | | | {%} |
| Net Income | | | | | {%} |
| EPS (Diluted) | | | | | {%} |

### Margins
| Margin | Current | Q-1 | Q-2 | Q-3 | Trend |
|--------|---------|-----|-----|-----|-------|
| Gross Margin | {%} | | | | {arrow} |
| Operating Margin | {%} | | | | {arrow} |
| Net Margin | {%} | | | | {arrow} |

### Balance Sheet
| Metric | Current | Prior Year | Change |
|--------|---------|-----------|--------|
| Total Assets | | | {%} |
| Total Debt | | | {%} |
| Cash & Equivalents | | | {%} |
| Shareholders' Equity | | | {%} |
| Net Debt/EBITDA | | | {delta} |

### Cash Flow
| Metric | Current | Prior Year | Change |
|--------|---------|-----------|--------|
| Operating CF | | | {%} |
| Capex | | | {%} |
| Free Cash Flow | | | {%} |
| FCF Margin | {%} | {%} | {delta} |

4. **Flag material changes** (auto-detect):
   - Revenue growth deceleration or acceleration > 200bps.
   - Margin expansion or compression > 100bps.
   - Debt increases > 20%.
   - New risk factors added to the filing.
   - Accounting policy changes.
   - Related party transaction changes.
   - Goodwill impairment or write-downs.

5. **Extract MD&A highlights** from the Management Discussion & Analysis section.

6. **Write output** to `analysis/{TICKER}/filings/{filing_type}_{date}.md`.

7. **Display summary** to the user with the most important changes flagged.
