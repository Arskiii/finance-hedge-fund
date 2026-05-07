from dataclasses import asdict

import pandas as pd
import pytest

from hedge_fund.filings import fetch_and_score_filings, filing_sentiment_signal
from hedge_fund.llm import FilingSentiment


class _FakeClient:
    def __init__(self, filings_by_ticker, items_by_filing_id):
        self._filings = filings_by_ticker
        self._items = items_by_filing_id

    def get_filings(self, ticker, limit=50):
        return self._filings.get(ticker, [])

    def get_filing_items(self, filing_id, item_types=None):
        return self._items.get(filing_id, "")


class _FakeAnalyzer:
    def __init__(self, scorer):
        self._scorer = scorer
        self.calls: list[tuple[str, str | None]] = []

    def score(self, text, ticker=None):
        self.calls.append((text, ticker))
        return self._scorer(text, ticker)


def _sentiment(value: float) -> FilingSentiment:
    return FilingSentiment(
        revenue_outlook=value,
        margin_pressure=value,
        demand_strength=value,
        competitive_position=value,
        balance_sheet_health=value,
        summary="t",
    )


def test_fetch_and_score_filings_collects_per_ticker_frame():
    filings = {
        "A": [
            {"filing_id": "f1", "filed_date": "2024-02-15"},
            {"filing_id": "f2", "filed_date": "2024-05-15"},
        ],
        "B": [{"filing_id": "f3", "filed_date": "2024-03-01"}],
    }
    items = {"f1": "filing one text", "f2": "filing two text", "f3": "filing three"}
    client = _FakeClient(filings, items)
    scores = {"f1": 0.2, "f2": 0.6, "f3": -0.4}
    analyzer = _FakeAnalyzer(
        lambda text, ticker: _sentiment(scores[next(k for k, v in items.items() if v == text)])
    )
    out = fetch_and_score_filings(["A", "B"], client, analyzer)
    assert set(out.keys()) == {"A", "B"}
    assert list(out["A"].columns) >= list(asdict(_sentiment(0.0)).keys()) + ["composite"]
    assert out["A"].loc["2024-02-15", "composite"] == pytest.approx(0.2)
    assert out["A"].loc["2024-05-15", "composite"] == pytest.approx(0.6)
    assert out["B"].loc["2024-03-01", "composite"] == pytest.approx(-0.4)
    # All three filings were scored, with ticker context passed through.
    assert {c[1] for c in analyzer.calls} == {"A", "B"}


def test_fetch_and_score_skips_filings_with_no_text():
    filings = {"A": [{"filing_id": "f1", "filed_date": "2024-02-15"}]}
    items: dict[str, str] = {"f1": ""}
    client = _FakeClient(filings, items)
    analyzer = _FakeAnalyzer(lambda text, ticker: _sentiment(1.0))
    out = fetch_and_score_filings(["A"], client, analyzer)
    assert out == {}
    assert analyzer.calls == []


def test_filing_sentiment_signal_averages_window():
    sentiment = {
        "A": pd.DataFrame(
            {"composite": [0.5, 0.3, 0.7]},
            index=pd.to_datetime(["2024-01-15", "2024-06-01", "2024-08-01"]),
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-08-31"])
    sig = filing_sentiment_signal(sentiment, rebalance, ["A"], window_days=120)
    # 120-day window from 2024-08-31 starts 2024-05-03, so 06-01 and 08-01 are in.
    assert sig.loc["2024-08-31", "A"] == pytest.approx(0.5)


def test_filing_sentiment_signal_nan_when_no_filings_in_window():
    sentiment = {
        "A": pd.DataFrame(
            {"composite": [0.5]}, index=pd.to_datetime(["2020-01-01"])
        ),
    }
    rebalance = pd.DatetimeIndex(["2024-08-31"])
    sig = filing_sentiment_signal(sentiment, rebalance, ["A"], window_days=120)
    assert pd.isna(sig.loc["2024-08-31", "A"])
