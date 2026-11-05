"""Integration layer between the HTTP API and the existing council.

This module does not implement any financial logic. It:
  1. fetches evidence with the existing ``fetch_market_data``,
  2. invokes the existing LangGraph council (same initial state as the CLI),
  3. maps the resulting state to the API response contract,
  4. translates failures into safe, typed API errors.
"""

import logging
import time
from datetime import datetime, timezone
from functools import lru_cache

from src.finance_council.council_graph import build_council_graph
from src.finance_council.market_data import MarketDataError, fetch_market_data
from src.finance_council.momentum_agent import calculate_momentum_indicators

from backend.config import get_settings
from backend.errors import ApiError, categorize_agent_error, redact
from backend.schemas import (
    AgentFailure,
    AgentResults,
    AnalysisResponse,
    FinalOutlook,
    MomentumIndicators,
    MomentumResult,
    RiskResult,
    ValuationResult,
)

logger = logging.getLogger("finance_council.api")

AGENTS = ("valuation", "risk", "momentum")


@lru_cache
def _graph():
    return build_council_graph()


def _initial_state(evidence) -> dict:
    # Identical to the state constructed by the CLI (src/finance_council/__main__.py).
    return {
        "evidence": evidence,
        "valuation": None,
        "risk": None,
        "momentum": None,
        "disagreement": None,
        "evidence_quality": None,
        "analytical_agreement": None,
        "execution_reliability": None,
        "final_outlook": None,
        "valuation_error": None,
        "risk_error": None,
        "momentum_error": None,
    }


def _fetch_evidence(ticker: str):
    try:
        return fetch_market_data(ticker)
    except MarketDataError as exc:
        message = str(exc)
        logger.info("Market data error for %s: %s", ticker, redact(message))
        if message.startswith("No price history found"):
            raise ApiError(
                404,
                "ticker_not_found",
                f"No price history was found for {ticker}. Check the symbol "
                "and exchange suffix (e.g. RELIANCE.NS).",
            ) from exc
        if message.startswith("Invalid ticker format"):
            raise ApiError(422, "invalid_ticker", "Invalid ticker format.") from exc
        raise ApiError(
            502,
            "market_data_unavailable",
            f"Market data for {ticker} could not be retrieved from Yahoo "
            "Finance. Try again later.",
        ) from exc


def _failure(raw_error: str | None, agent: str, ticker: str) -> AgentFailure | None:
    if not raw_error:
        return None
    logger.warning("Agent %s failed for %s: %s", agent, ticker, redact(raw_error))
    category, message = categorize_agent_error(raw_error)
    return AgentFailure(category=category, message=message)


def _momentum_indicators(evidence) -> tuple[MomentumIndicators | None, str | None]:
    try:
        return MomentumIndicators(**calculate_momentum_indicators(evidence)), None
    except ValueError as exc:
        return None, str(exc)


def _raise_if_all_failed(failures: dict[str, AgentFailure | None]) -> None:
    if not all(failures.values()):
        return

    details = {
        "agent_failures": {
            name: failure.model_dump() for name, failure in failures.items()
        }
    }
    categories = {failure.category for failure in failures.values()}

    if categories == {"rate_limit"}:
        raise ApiError(
            429,
            "provider_rate_limited",
            "All council agents hit the language model provider's rate limit "
            "or quota. No analysis was produced. Try again later.",
            details,
        )
    if "configuration" in categories:
        raise ApiError(
            503,
            "service_misconfigured",
            "The analysis service is not configured with model credentials.",
            details,
        )
    raise ApiError(
        502,
        "council_execution_failed",
        "All council agents failed. No analysis was produced.",
        details,
    )


def run_analysis(ticker: str) -> AnalysisResponse:
    started = time.monotonic()
    evidence = _fetch_evidence(ticker)

    result = _graph().invoke(_initial_state(evidence))

    failures = {
        name: _failure(result.get(f"{name}_error"), name, ticker)
        for name in AGENTS
    }

    # Never present a "result" when no agent executed: the council's
    # synthesis would read "insufficient_evidence", which would misrepresent
    # an execution failure as an evidence assessment.
    _raise_if_all_failed(failures)

    def status(name: str) -> str:
        return "failed" if failures[name] else "succeeded"

    agents = AgentResults(
        valuation=ValuationResult(
            status=status("valuation"),
            assessment=None if failures["valuation"] else result["valuation"],
            failure=failures["valuation"],
        ),
        risk=RiskResult(
            status=status("risk"),
            assessment=None if failures["risk"] else result["risk"],
            failure=failures["risk"],
        ),
        momentum=MomentumResult(
            status=status("momentum"),
            assessment=None if failures["momentum"] else result["momentum"],
            failure=failures["momentum"],
        ),
    )

    indicators, indicators_reason = _momentum_indicators(evidence)
    execution = result["execution_reliability"]

    response = AnalysisResponse(
        ticker=evidence.ticker,
        analyzed_at=datetime.now(timezone.utc),
        duration_seconds=round(time.monotonic() - started, 2),
        status="complete" if execution["reliability"] == "complete" else "partial",
        model=get_settings().model_name,
        final_outlook=FinalOutlook.model_validate(result["final_outlook"]),
        agents=agents,
        disagreement=result["disagreement"],
        evidence_quality=result["evidence_quality"],
        analytical_agreement=result["analytical_agreement"],
        execution_reliability=execution,
        market_evidence=evidence,
        momentum_indicators=indicators,
        momentum_indicators_unavailable_reason=indicators_reason,
    )

    logger.info(
        "Analysis %s completed: status=%s outlook=%s duration=%.2fs",
        ticker,
        response.status,
        response.final_outlook.overall_outlook,
        response.duration_seconds,
    )
    return response
