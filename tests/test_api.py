"""HTTP API tests. Market data and Groq agents are mocked: no network calls,
no Groq quota consumed. The real LangGraph council and its deterministic
synthesis nodes run unmodified."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.errors import categorize_agent_error, redact
from backend.rate_limit import SlidingWindowRateLimiter
from src.finance_council.market_data import OHLCV, MarketDataError, MarketEvidence
from src.finance_council.momentum_agent import MomentumAssessment
from src.finance_council.risk_agent import RiskAssessment
from src.finance_council.valuation_agent import ValuationAssessment

FETCH = "backend.council_service.fetch_market_data"
VALUATION = "src.finance_council.council_graph.ValuationAgent.assess"
RISK = "src.finance_council.council_graph.RiskAgent.assess"
MOMENTUM = "src.finance_council.council_graph.MomentumAgent.assess"


def make_evidence(ticker="TEST", days=120):
    start = datetime(2026, 1, 1)
    history = [
        OHLCV(
            date=(start + timedelta(days=i)).strftime("%Y-%m-%d"),
            open=100 + i, high=101 + i, low=99 + i, close=100 + i,
            volume=1_000_000 + i,
        )
        for i in range(days)
    ]
    return MarketEvidence(
        ticker=ticker,
        company_name="Test Corp",
        current_price=history[-1].close if history else None,
        history=history,
        missing_fields=["trailing_pe"],
        fetched_at=datetime.now(timezone.utc),
    )


def valuation(stance="positive"):
    return ValuationAssessment(
        ticker="TEST", stance=stance, evidence=["P/B supplied"],
        assumptions=["a"], limitations=["no peers"], reasoning="r",
    )


def risk(level="moderate"):
    return RiskAssessment(
        ticker="TEST", risk_level=level, evidence=["beta"], reasoning="r",
    )


def momentum(stance="positive"):
    return MomentumAssessment(
        ticker="TEST", stance=stance, evidence=["above MA50"],
        assumptions=[], limitations=[], reasoning="r",
    )


@pytest.fixture(autouse=True)
def configured_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_testplaceholder000000")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    monkeypatch.setattr(main, "rate_limiter", SlidingWindowRateLimiter(100))


@pytest.fixture
def client():
    return TestClient(main.app)


def post(client, ticker="TEST"):
    return client.post("/api/analyze", json={"ticker": ticker})


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["council_configured"] is True
    assert "gsk_" not in res.text


@pytest.mark.parametrize(
    "payload",
    [
        {"ticker": ""},
        {"ticker": "AAPL!"},
        {"ticker": "../etc"},
        {"ticker": "TOOLONGTICKER"},
        {"ticker": "<script>"},
        {},
        {"ticker": "AAPL", "extra": 1},
        {"ticker": 123},
    ],
)
def test_malformed_requests_rejected(client, payload):
    with patch(FETCH) as fetch:
        res = client.post("/api/analyze", json=payload)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_request"
    fetch.assert_not_called()


def test_ticker_is_normalized(client):
    with (
        patch(FETCH, return_value=make_evidence("BRK-B")) as fetch,
        patch(VALUATION, return_value=valuation()),
        patch(RISK, return_value=risk()),
        patch(MOMENTUM, return_value=momentum()),
    ):
        res = post(client, "  brk-b ")
    assert res.status_code == 200
    fetch.assert_called_once_with("BRK-B")


def test_successful_analysis_returns_council_outputs(client):
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, return_value=valuation("positive")),
        patch(RISK, return_value=risk("moderate")),
        patch(MOMENTUM, return_value=momentum("positive")),
    ):
        res = post(client)

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "complete"
    assert body["final_outlook"]["overall_outlook"] == "positive"
    assert body["analytical_agreement"]["classification"] == "aligned"
    assert body["evidence_quality"]["level"] == "complete"
    assert body["execution_reliability"]["reliability"] == "complete"
    assert body["disagreement"]["classification"] == "no_conflict"
    assert body["agents"]["valuation"]["assessment"]["limitations"] == ["no peers"]
    assert body["agents"]["risk"]["assessment"]["risk_level"] == "moderate"
    assert len(body["market_evidence"]["history"]) == 120
    assert body["momentum_indicators"]["ma_50"] is not None
    assert "not personalized investment advice" in body["disclaimer"]


def test_conflict_produces_mixed_outlook(client):
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, return_value=valuation("negative")),
        patch(RISK, return_value=risk()),
        patch(MOMENTUM, return_value=momentum("positive")),
    ):
        body = post(client).json()
    assert body["final_outlook"]["overall_outlook"] == "mixed"
    assert body["disagreement"]["classification"] == "conflict"
    assert set(body["disagreement"]["conflicting_agents"]) == {"valuation", "momentum"}


def test_insufficient_evidence_is_returned_not_forced(client):
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, return_value=valuation("insufficient_evidence")),
        patch(RISK, return_value=risk("insufficient_evidence")),
        patch(MOMENTUM, return_value=momentum("neutral")),
    ):
        res = post(client)
    assert res.status_code == 200
    body = res.json()
    assert body["final_outlook"]["overall_outlook"] == "insufficient_evidence"
    assert body["analytical_agreement"]["classification"] == "unestablished"


def test_partial_agent_failure_is_reported_safely(client):
    secret_error = RuntimeError(
        "Error code: 429 - rate_limit_exceeded for key gsk_abcdefghijklmnop123"
    )
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, side_effect=secret_error),
        patch(RISK, return_value=risk()),
        patch(MOMENTUM, return_value=momentum("positive")),
    ):
        res = post(client)

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "partial"
    v = body["agents"]["valuation"]
    assert v["status"] == "failed"
    assert v["assessment"] is None
    assert v["failure"]["category"] == "rate_limit"
    assert body["final_outlook"]["overall_outlook"] == "partial_directional"
    assert body["final_outlook"]["dimensions"]["valuation"] == "failed"
    assert "gsk_" not in res.text
    assert "Traceback" not in res.text


def test_all_agents_rate_limited_returns_429_not_result(client):
    err = RuntimeError("Error code: 429 - rate limit")
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, side_effect=err),
        patch(RISK, side_effect=err),
        patch(MOMENTUM, side_effect=err),
    ):
        res = post(client)
    assert res.status_code == 429
    body = res.json()
    assert body["error"]["code"] == "provider_rate_limited"
    assert "final_outlook" not in body
    assert set(body["error"]["details"]["agent_failures"]) == {"valuation", "risk", "momentum"}


def test_all_agents_failed_mixed_errors_returns_502(client):
    with (
        patch(FETCH, return_value=make_evidence()),
        patch(VALUATION, side_effect=RuntimeError("boom")),
        patch(RISK, side_effect=ValueError("bad json")),
        patch(MOMENTUM, side_effect=RuntimeError("Error code: 429")),
    ):
        res = post(client)
    assert res.status_code == 502
    assert res.json()["error"]["code"] == "council_execution_failed"


def test_unknown_ticker_returns_404(client):
    with patch(FETCH, side_effect=MarketDataError("No price history found for ticker ZZZZ")):
        res = post(client, "ZZZZ")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ticker_not_found"


def test_market_data_failure_returns_502_without_internals(client):
    with patch(FETCH, side_effect=MarketDataError("Failed to fetch: HTTPSConnectionPool secret-host")):
        res = post(client)
    assert res.status_code == 502
    assert res.json()["error"]["code"] == "market_data_unavailable"
    assert "HTTPSConnectionPool" not in res.text


def test_short_history_reports_indicator_unavailability(client):
    with (
        patch(FETCH, return_value=make_evidence(days=30)),
        patch(VALUATION, return_value=valuation()),
        patch(RISK, return_value=risk()),
    ):
        # Momentum agent runs for real up to its deterministic indicator step,
        # which raises before any Groq call is made.
        res = post(client)
    body = res.json()
    assert res.status_code == 200
    assert body["agents"]["momentum"]["failure"]["category"] == "insufficient_price_history"
    assert body["momentum_indicators"] is None
    assert "50" in body["momentum_indicators_unavailable_reason"]


def test_missing_credentials_returns_503(client, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    with patch(FETCH) as fetch:
        res = post(client)
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "service_misconfigured"
    fetch.assert_not_called()


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", SlidingWindowRateLimiter(1))
    with patch(FETCH, side_effect=MarketDataError("No price history found")):
        assert post(client).status_code == 404
        res = post(client)
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "rate_limited"
    assert "Retry-After" in res.headers


def test_unhandled_exception_is_sanitized(client):
    with patch(FETCH, side_effect=KeyError("internal detail")):
        res = TestClient(main.app, raise_server_exceptions=False).post(
            "/api/analyze", json={"ticker": "TEST"}
        )
    assert res.status_code == 500
    assert res.json()["error"]["code"] == "internal_error"
    assert "internal detail" not in res.text


def test_cors_allows_configured_origin_only(client):
    ok = client.options(
        "/api/analyze",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(
        "/api/analyze",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in bad.headers


@pytest.mark.parametrize(
    "raw,category",
    [
        ("RateLimitError: Error code: 429", "rate_limit"),
        ("ValueError: GROQ_API_KEY is missing from .env", "configuration"),
        ("AuthenticationError: Error code: 401", "provider_auth"),
        ("ValueError: At least 50 valid closing prices are required", "insufficient_price_history"),
        ("JSONDecodeError: Expecting value", "invalid_model_output"),
        ("APIConnectionError: Connection error.", "provider_unavailable"),
        ("InternalServerError: Error code: 503", "provider_error"),
        ("RuntimeError: something", "unknown"),
    ],
)
def test_agent_error_categories(raw, category):
    assert categorize_agent_error(raw)[0] == category


def test_redaction():
    assert "gsk_abcdefgh1234" not in redact("key gsk_abcdefgh1234 Bearer abc.def")
    assert "Bearer abc" not in redact("Bearer abc.def")
