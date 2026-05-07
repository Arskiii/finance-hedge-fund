"""Claude-based qualitative analysis of SEC filings.

`FilingAnalyzer` wraps the Anthropic SDK with two ergonomic choices:

  * the analyst persona and scoring guide are sent as a cacheable system
    prompt, so the prefix is paid once and reused across thousands of
    filings (prompt caching);
  * structured output is forced via `tool_use` so callers receive a typed
    `FilingSentiment` rather than free-form text that needs parsing.

The `anthropic` SDK is imported lazily so the rest of the package and its
test suite remain installable without it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL = "claude-sonnet-4-6"

ANALYST_SYSTEM_PROMPT = (
    "You are a buy-side equity analyst evaluating SEC filings for systematic "
    "incorporation into a quantitative model. Read the supplied filing text "
    "carefully and produce structured scores on five dimensions. Be neutral "
    "and evidence-based; do not anchor on prior performance or general market "
    "sentiment. Report what management's own language and disclosed numbers "
    "imply for the next 6-12 months."
)

SCORING_GUIDE = (
    "Scoring dimensions, each on a -1.0 (very bearish) to +1.0 (very bullish) "
    "scale:\n\n"
    "  revenue_outlook       — likelihood of accelerating top-line growth\n"
    "  margin_pressure       — direction of operating margins (+ = expansion)\n"
    "  demand_strength       — current end-market demand signals\n"
    "  competitive_position  — moat / share gain or loss\n"
    "  balance_sheet_health  — leverage, liquidity, capital structure\n\n"
    "Use the full range. Reserve scores beyond +/-0.7 for filings with very "
    "explicit language. Default to 0.0 when the filing is silent on a "
    "dimension. The summary must be at most two sentences and reference "
    "specific evidence from the filing."
)

REPORT_TOOL: dict[str, Any] = {
    "name": "report_filing_sentiment",
    "description": "Submit the structured sentiment scores for the filing.",
    "input_schema": {
        "type": "object",
        "properties": {
            "revenue_outlook": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "margin_pressure": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "demand_strength": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "competitive_position": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "balance_sheet_health": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "summary": {"type": "string"},
        },
        "required": [
            "revenue_outlook",
            "margin_pressure",
            "demand_strength",
            "competitive_position",
            "balance_sheet_health",
            "summary",
        ],
    },
}


@dataclass(frozen=True)
class FilingSentiment:
    revenue_outlook: float
    margin_pressure: float
    demand_strength: float
    competitive_position: float
    balance_sheet_health: float
    summary: str

    @property
    def composite(self) -> float:
        return (
            self.revenue_outlook
            + self.margin_pressure
            + self.demand_strength
            + self.competitive_position
            + self.balance_sheet_health
        ) / 5.0


class FilingAnalyzer:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        client: Any | None = None,
    ) -> None:
        if client is None:
            from anthropic import Anthropic  # lazy: keeps anthropic optional

            client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._client = client
        self.model = model

    def score(
        self,
        filing_text: str,
        ticker: str | None = None,
        max_chars: int = 60_000,
    ) -> FilingSentiment:
        text = filing_text[:max_chars]
        header = f"Filing for {ticker}:\n\n" if ticker else "Filing:\n\n"
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=[
                {"type": "text", "text": ANALYST_SYSTEM_PROMPT},
                {
                    "type": "text",
                    "text": SCORING_GUIDE,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            tools=[REPORT_TOOL],
            tool_choice={"type": "tool", "name": REPORT_TOOL["name"]},
            messages=[{"role": "user", "content": header + text}],
        )
        return _extract_sentiment(response)


def _extract_sentiment(response: Any) -> FilingSentiment:
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == REPORT_TOOL["name"]:
            args = block.input
            return FilingSentiment(
                revenue_outlook=float(args["revenue_outlook"]),
                margin_pressure=float(args["margin_pressure"]),
                demand_strength=float(args["demand_strength"]),
                competitive_position=float(args["competitive_position"]),
                balance_sheet_health=float(args["balance_sheet_health"]),
                summary=str(args["summary"]),
            )
    raise RuntimeError("Model did not call the report_filing_sentiment tool.")
