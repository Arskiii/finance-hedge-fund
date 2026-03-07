---
name: mgmt
description: Track management guidance vs actual results to score credibility over 3 years (12 quarters).
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
---

# Management Guidance Tracker

Track how accurately management has guided over the last 3 years.

## Input
- `$ARGUMENTS`: Ticker symbol (required). Example: `GOOGL`

## Process

1. **Search for earnings call transcripts** over the last 12 quarters using WebSearch:
   - Query: "{TICKER} earnings call transcript Q{N} {YEAR}"
   - For each quarter, extract all forward-looking guidance statements:
     - Revenue guidance (range or point estimate).
     - EPS guidance.
     - Margin targets.
     - Capex guidance.
     - Any specific quantitative commitments.

2. **Pull actual reported results** from SEC EDGAR MCP for each corresponding quarter.

3. **Build the guidance accuracy table:**

| Quarter | Metric | Guidance Low | Guidance High | Midpoint | Actual | vs Mid | Result |
|---------|--------|-------------|---------------|----------|--------|--------|--------|
| Q4 2025 | Revenue | $XM | $XM | $XM | $XM | +X% | Beat |
| Q4 2025 | EPS | $X | $X | $X | $X | +$X | Beat |

4. **Score each quarter:**
   - Beat guidance midpoint: +1 point
   - Within guidance range but below midpoint: 0 points
   - Missed guidance range entirely: -2 points
   - Raised guidance and then beat: +2 points
   - Cut guidance: -1 point

5. **Calculate the credibility score:**
   - Score = (total_points + abs(min_possible)) / (max_possible + abs(min_possible)) * 100
   - Rating: >80% Highly Credible | 60-80% Credible | 40-60% Mixed | <40% Unreliable

6. **Pattern analysis:**
   - Sandbagging pattern (consistently guide low, beat)?
   - Over-promising pattern (guide high, miss)?
   - Credibility trend over time (improving or worsening)?
   - Which metrics are most/least accurately guided?

7. **Write output** to `analysis/{TICKER}/mgmt-credibility.md`.

8. **Display summary**: Credibility score, rating, trend direction, and key pattern.
