import pytest

from hedge_fund.llm import (
    REPORT_TOOL,
    FilingAnalyzer,
    FilingSentiment,
    _extract_sentiment,
)


class _FakeBlock:
    def __init__(self, type_, name=None, input=None):
        self.type = type_
        self.name = name
        self.input = input


class _FakeResponse:
    def __init__(self, blocks):
        self.content = blocks


class _StubClient:
    """Minimal stand-in for anthropic.Anthropic (just `.messages.create`)."""

    def __init__(self, response):
        self._response = response
        self.last_kwargs: dict | None = None
        self.messages = self  # so client.messages.create works

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


def _scored_response(**scores) -> _FakeResponse:
    payload = {
        "revenue_outlook": 0.0,
        "margin_pressure": 0.0,
        "demand_strength": 0.0,
        "competitive_position": 0.0,
        "balance_sheet_health": 0.0,
        "summary": "neutral",
        **scores,
    }
    return _FakeResponse([_FakeBlock("tool_use", name=REPORT_TOOL["name"], input=payload)])


def test_extract_sentiment_parses_tool_use():
    response = _scored_response(
        revenue_outlook=0.5,
        margin_pressure=0.2,
        demand_strength=0.3,
        competitive_position=0.0,
        balance_sheet_health=0.4,
        summary="okay",
    )
    s = _extract_sentiment(response)
    assert isinstance(s, FilingSentiment)
    assert s.revenue_outlook == 0.5
    assert s.composite == pytest.approx((0.5 + 0.2 + 0.3 + 0.0 + 0.4) / 5)


def test_extract_sentiment_raises_when_tool_not_called():
    response = _FakeResponse([_FakeBlock("text")])
    with pytest.raises(RuntimeError, match="report_filing_sentiment"):
        _extract_sentiment(response)


def test_score_forces_tool_choice_and_uses_prompt_caching():
    stub = _StubClient(_scored_response())
    analyzer = FilingAnalyzer(client=stub)
    analyzer.score("filing text", ticker="AAPL")
    kwargs = stub.last_kwargs
    assert kwargs is not None
    assert kwargs["tool_choice"] == {"type": "tool", "name": REPORT_TOOL["name"]}
    # Last system block carries the cache_control marker.
    assert kwargs["system"][-1].get("cache_control") == {"type": "ephemeral"}
    # Ticker context is prepended to the user message.
    assert "AAPL" in kwargs["messages"][0]["content"]
    # Tools list contains exactly the report tool.
    assert kwargs["tools"][0]["name"] == REPORT_TOOL["name"]


def test_score_truncates_long_text():
    stub = _StubClient(_scored_response())
    analyzer = FilingAnalyzer(client=stub)
    long_text = "x" * 100_000
    analyzer.score(long_text, max_chars=1000)
    user_msg = stub.last_kwargs["messages"][0]["content"]
    # Header plus 1000 chars of text.
    assert user_msg.count("x") == 1000
