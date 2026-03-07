---
name: diligence-checklist
description: Full investment diligence checklist for a ticker. Spawns 5 parallel sub-agents for comprehensive analysis and synthesizes into a unified memo.
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash, Task
---

# Investment Diligence Checklist

Run a complete diligence process for the specified ticker.

## Input
- `$ARGUMENTS`: Ticker symbol (required). Example: `AAPL`

## Pre-flight

1. Validate that the ticker argument was provided. If not, ask the user for a ticker.
2. Create the output directory `analysis/{TICKER}/` if it doesn't exist.
3. Pull basic company info using Yahoo Finance MCP to confirm the ticker is valid and get: company name, sector, market cap, current price.
4. Display: "Starting full diligence on {COMPANY} ({TICKER}) — launching 5 parallel research agents..."

## Parallel Analysis — Launch 5 Sub-Agents

Use the Task tool to launch all 5 agents in parallel. Each agent should be launched with `subagent_type: "general-purpose"` and given its specific research prompt:

### Agent 1: Revenue Quality
Prompt: "You are a revenue quality analyst. Analyze revenue quality for {TICKER}. Examine: recurring vs non-recurring revenue %, customer concentration, geographic mix, revenue recognition policies, and revenue volatility over 3 years. Use SEC EDGAR MCP for 10-K data and Yahoo Finance MCP for current metrics. Score revenue quality 1-10. Write a complete analysis to analysis/{TICKER}/revenue-quality.md"

### Agent 2: Management Credibility
Prompt: "You are a management credibility analyst. Score management credibility for {TICKER} by comparing forward guidance to actual results over the last 3 years (12 quarters). Search for earnings call transcripts via WebSearch. Pull actual results from SEC EDGAR MCP. Calculate a credibility score (0-100%). Write a complete analysis to analysis/{TICKER}/mgmt-credibility.md"

### Agent 3: Bear Case
Prompt: "You are a skeptical equity analyst. Construct a detailed bear case for {TICKER}. Identify key risks from SEC EDGAR 10-K risk factors and WebSearch. Build a bear case financial model with worst-case revenue, margins, and multiples. Quantify the downside with a specific fair value. Write a complete analysis to analysis/{TICKER}/bear-case.md"

### Agent 4: Bull Case
Prompt: "You are an optimistic equity analyst. Construct a detailed bull case for {TICKER}. Research growth catalysts via WebSearch and SEC EDGAR MCP. Build a bull case financial model with best-case revenue, margins, and multiples. Quantify the upside with a specific fair value. Write a complete analysis to analysis/{TICKER}/bull-case.md"

### Agent 5: Insider Transactions
Prompt: "You are an insider transaction analyst. Analyze insider transactions for {TICKER} over the last 12 months. Use SEC EDGAR MCP for Form 4 filings. Categorize as open market buys/sells vs option exercises. Identify cluster buying/selling patterns. Calculate an insider sentiment score. Write a complete analysis to analysis/{TICKER}/insider-transactions.md"

## Synthesis — After All Agents Return

1. Read all 5 output files from `analysis/{TICKER}/`.
2. Read the diligence memo template from `templates/diligence-memo.md`.
3. Synthesize all findings into a unified diligence memo following the template structure.
4. Compute an overall conviction rating (1-10) based on:
   - Revenue quality score (weight: 20%)
   - Management credibility score (weight: 20%)
   - Bull/bear asymmetry — upside vs downside ratio (weight: 30%)
   - Insider sentiment (weight: 15%)
   - Business quality assessment (weight: 15%)
5. Write the final memo to `analysis/{TICKER}/diligence-memo.md`.

## Present Results

Display to the user:
- Overall conviction: {1-10}/10
- One-line thesis
- Top 3 strengths
- Top 3 risks
- Fair value range (bear/base/bull)
- Recommended action: BUY / HOLD / PASS
- Suggested position size
- "Full memo saved to analysis/{TICKER}/diligence-memo.md"
