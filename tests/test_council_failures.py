
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.finance_council.council_graph import build_council_graph
from src.finance_council.market_data import MarketEvidence


def make_evidence():
    return MarketEvidence.model_construct(
        ticker="AAPL",
        missing_fields=[],
    )


def make_initial_state():
    return {
        "evidence": make_evidence(),
        "valuation": None,
        "risk": None,
        "momentum": None,
        "valuation_error": None,
        "risk_error": None,
        "momentum_error": None,
        "disagreement": None,
        "evidence_quality": None,
        "analytical_agreement": None,
        "execution_reliability": None,
        "final_outlook": None,
    }


def make_mock_assessments():
    return {
        "ValuationAgent": SimpleNamespace(stance="positive"),
        "RiskAgent": SimpleNamespace(risk_level="moderate"),
        "MomentumAgent": SimpleNamespace(stance="positive"),
    }


@pytest.mark.parametrize(
    "agent_name,error_key",
    [
        ("ValuationAgent", "valuation_error"),
        ("RiskAgent", "risk_error"),
        ("MomentumAgent", "momentum_error"),
    ],
)
def test_each_agent_failure_is_captured(agent_name, error_key):
    mocks = make_mock_assessments()

    with (
        patch(
            "src.finance_council.council_graph.ValuationAgent.assess",
            side_effect=(
                RuntimeError("Simulated failure")
                if agent_name == "ValuationAgent"
                else None
            ),
            return_value=mocks["ValuationAgent"],
        ),
        patch(
            "src.finance_council.council_graph.RiskAgent.assess",
            side_effect=(
                RuntimeError("Simulated failure")
                if agent_name == "RiskAgent"
                else None
            ),
            return_value=mocks["RiskAgent"],
        ),
        patch(
            "src.finance_council.council_graph.MomentumAgent.assess",
            side_effect=(
                RuntimeError("Simulated failure")
                if agent_name == "MomentumAgent"
                else None
            ),
            return_value=mocks["MomentumAgent"],
        ),
    ):
        result = build_council_graph().invoke(make_initial_state())

    assert "Simulated failure" in result[error_key]
    assert result["disagreement"]["classification"] == "agent_failure"
    assert agent_name.replace("Agent", "").lower() in (
        result["disagreement"]["failed_agents"]
    )


def test_multiple_agent_failures_are_captured():
    with (
        patch(
            "src.finance_council.council_graph.ValuationAgent.assess",
            side_effect=RuntimeError("Valuation failure"),
        ),
        patch(
            "src.finance_council.council_graph.RiskAgent.assess",
            side_effect=RuntimeError("Risk failure"),
        ),
        patch(
            "src.finance_council.council_graph.MomentumAgent.assess",
            return_value=SimpleNamespace(stance="positive"),
        ),
    ):
        result = build_council_graph().invoke(make_initial_state())

    assert result["disagreement"]["classification"] == "agent_failure"
    assert set(result["disagreement"]["failed_agents"]) == {
        "valuation",
        "risk",
    }
    assert (
        result["final_outlook"]["overall_outlook"]
        == "partial_directional"
    )

    assert (
        result["final_outlook"]["dimensions"]["valuation"]
        == "failed"
    )

    assert (
        result["final_outlook"]["dimensions"]["risk"]
        == "failed"
    )

    assert (
        result["final_outlook"]["dimensions"]["momentum"]
        == "positive"
    )


def test_insufficient_valuation_does_not_erase_positive_momentum():
    with (
        patch(
            "src.finance_council.council_graph.ValuationAgent.assess",
            return_value=SimpleNamespace(
                stance="insufficient_evidence"
            ),
        ),
        patch(
            "src.finance_council.council_graph.RiskAgent.assess",
            return_value=SimpleNamespace(risk_level="moderate"),
        ),
        patch(
            "src.finance_council.council_graph.MomentumAgent.assess",
            return_value=SimpleNamespace(stance="positive"),
        ),
    ):
        result = build_council_graph().invoke(make_initial_state())

    assert result["final_outlook"]["overall_outlook"] == "partial_directional"
    assert result["final_outlook"]["dimensions"]["valuation"] == "insufficient_evidence"
    assert result["final_outlook"]["dimensions"]["momentum"] == "positive"

    assert result["evidence_quality"]["level"] == "partial"
    assert result["analytical_agreement"]["classification"] == "limited"
    assert result["execution_reliability"]["reliability"] == "complete"


def test_opposing_valuation_and_momentum_produce_mixed_outlook():
    with (
        patch(
            "src.finance_council.council_graph.ValuationAgent.assess",
            return_value=SimpleNamespace(stance="positive"),
        ),
        patch(
            "src.finance_council.council_graph.RiskAgent.assess",
            return_value=SimpleNamespace(risk_level="moderate"),
        ),
        patch(
            "src.finance_council.council_graph.MomentumAgent.assess",
            return_value=SimpleNamespace(stance="negative"),
        ),
    ):
        result = build_council_graph().invoke(make_initial_state())

    assert result["final_outlook"]["overall_outlook"] == "mixed"
    assert result["analytical_agreement"]["classification"] == "conflicting"
    assert result["disagreement"]["classification"] == "conflict"
