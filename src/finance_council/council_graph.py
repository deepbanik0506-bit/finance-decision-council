
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.finance_council.market_data import MarketEvidence
from src.finance_council.valuation_agent import (
    ValuationAssessment,
    ValuationAgent,
)
from src.finance_council.risk_agent import (
    RiskAssessment,
    RiskAgent,
)
from src.finance_council.momentum_agent import (
    MomentumAssessment,
    MomentumAgent,
)


class DisagreementReport(TypedDict):
    classification: str
    conflicting_agents: list[str]
    failed_agents: list[str]
    evidence_gaps: list[str]
    explanation: str


class ConfidenceReport(TypedDict):
    score: int
    level: str
    factors: list[str]
    explanation: str


class CouncilState(TypedDict):
    evidence: MarketEvidence

    valuation: ValuationAssessment | None
    risk: RiskAssessment | None
    momentum: MomentumAssessment | None

    valuation_error: str | None
    risk_error: str | None
    momentum_error: str | None

    disagreement: DisagreementReport | None
    confidence: ConfidenceReport | None
    final_outlook: dict | None


# --------------------------------------------------
# Agent Nodes
# --------------------------------------------------

def valuation_node(state: CouncilState) -> dict:
    try:
        agent = ValuationAgent()
        result = agent.assess(state["evidence"])

        return {
            "valuation": result,
            "valuation_error": None,
        }

    except Exception as exc:
        return {
            "valuation": None,
            "valuation_error": f"{type(exc).__name__}: {exc}",
        }


def risk_node(state: CouncilState) -> dict:
    try:
        agent = RiskAgent()
        result = agent.assess(state["evidence"])

        return {
            "risk": result,
            "risk_error": None,
        }

    except Exception as exc:
        return {
            "risk": None,
            "risk_error": f"{type(exc).__name__}: {exc}",
        }


def momentum_node(state: CouncilState) -> dict:
    try:
        agent = MomentumAgent()
        result = agent.assess(state["evidence"])

        return {
            "momentum": result,
            "momentum_error": None,
        }

    except Exception as exc:
        return {
            "momentum": None,
            "momentum_error": f"{type(exc).__name__}: {exc}",
        }


# --------------------------------------------------
# Disagreement Engine
# --------------------------------------------------

def disagreement_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    risk = state["risk"]
    momentum = state["momentum"]

    evidence_gaps = []
    failed_agents = []
    conflicting_agents = []

    if state["valuation_error"]:
        failed_agents.append("valuation")
    elif valuation.stance == "insufficient_evidence":
        evidence_gaps.append("valuation")

    if state["risk_error"]:
        failed_agents.append("risk")
    elif risk.risk_level == "insufficient_evidence":
        evidence_gaps.append("risk")

    if state["momentum_error"]:
        failed_agents.append("momentum")
    elif momentum.stance == "insufficient_evidence":
        evidence_gaps.append("momentum")

    directional = {}

    if valuation is not None and not state["valuation_error"]:
        directional["valuation"] = valuation.stance

    if momentum is not None and not state["momentum_error"]:
        directional["momentum"] = momentum.stance

    positive = [
        name for name, stance in directional.items()
        if stance == "positive"
    ]

    negative = [
        name for name, stance in directional.items()
        if stance == "negative"
    ]

    if positive and negative:
        conflicting_agents = positive + negative
        classification = "conflict"

        explanation = (
            "Directional agents produced opposing positive and negative "
            "assessments."
        )

    elif failed_agents:
        classification = "agent_failure"

        explanation = (
            "One or more agents failed during execution: "
            + ", ".join(failed_agents)
        )

    elif evidence_gaps:
        classification = "insufficient_evidence"

        explanation = (
            "One or more agents could not reach an assessment due to "
            "insufficient evidence."
        )

    else:
        classification = "no_conflict"
        explanation = "No opposing directional assessments were detected."

    report: DisagreementReport = {
        "classification": classification,
        "conflicting_agents": conflicting_agents,
        "failed_agents": failed_agents,
        "evidence_gaps": evidence_gaps,
        "explanation": explanation,
    }

    return {"disagreement": report}


# --------------------------------------------------
# Confidence Model
# --------------------------------------------------

def confidence_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    risk = state["risk"]
    momentum = state["momentum"]
    disagreement = state["disagreement"]

    score = 100
    factors = []

    # Evidence completeness
    missing_count = len(state["evidence"].missing_fields)
    evidence_penalty = min(missing_count * 5, 30)

    score -= evidence_penalty

    if evidence_penalty:
        factors.append(
            f"Missing market fields: -{evidence_penalty}"
        )

    # Agent coverage
    usable_agents = sum([
        valuation is not None
        and valuation.stance != "insufficient_evidence",

        risk is not None
        and risk.risk_level != "insufficient_evidence",

        momentum is not None
        and momentum.stance != "insufficient_evidence",
    ])

    coverage_score = usable_agents / 3
    coverage_penalty = round((1 - coverage_score) * 30)

    score -= coverage_penalty

    if coverage_penalty:
        factors.append(
            f"Insufficient agent assessments: -{coverage_penalty}"
        )

    # Execution failures
    failed_agents = disagreement["failed_agents"]

    if failed_agents:
        failure_penalty = min(len(failed_agents) * 20, 60)

        score -= failure_penalty

        factors.append(
            f"Agent execution failures: -{failure_penalty}"
        )

    # Directional conflict and evidence gaps
    if disagreement["classification"] == "conflict":
        score -= 20
        factors.append("Directional disagreement: -20")

    elif disagreement["classification"] == "insufficient_evidence":
        score -= 10
        factors.append("Evidence gaps: -10")

    score = max(0, min(100, score))

    if score >= 80:
        level = "high"
    elif score >= 60:
        level = "moderate"
    else:
        level = "low"

    report: ConfidenceReport = {
        "score": score,
        "level": level,
        "factors": factors,
        "explanation": (
            "Confidence reflects evidence completeness, agent coverage, "
            "execution reliability, and directional consistency. "
            "It does not predict returns and is not a probability."
        ),
    }

    return {"confidence": report}


# --------------------------------------------------
# Final Outlook
# --------------------------------------------------

def final_outlook_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    momentum = state["momentum"]
    disagreement = state["disagreement"]

    valuation_failed = state["valuation_error"] is not None
    momentum_failed = state["momentum_error"] is not None

    v = valuation.stance if valuation is not None else None
    m = momentum.stance if momentum is not None else None

    if valuation_failed or momentum_failed:
        outlook = "insufficient_evidence"

        rationale = (
            "At least one directional agent failed during execution. "
            "A reliable directional outlook cannot be established."
        )

    elif v == "insufficient_evidence" or m == "insufficient_evidence":
        outlook = "insufficient_evidence"

        rationale = (
            "At least one directional agent lacks sufficient evidence."
        )

    elif v == "positive" and m == "positive":
        outlook = "positive"

        rationale = (
            "Valuation and momentum assessments are both positive."
        )

    elif v == "negative" and m == "negative":
        outlook = "negative"

        rationale = (
            "Valuation and momentum assessments are both negative."
        )

    elif v in ("positive", "negative") and m in ("positive", "negative"):
        outlook = "neutral"

        rationale = (
            "Valuation and momentum assessments conflict."
        )

    else:
        outlook = "neutral"
        rationale = "No consistent directional outlook was established."

    result = {
        "ticker": state["evidence"].ticker,
        "outlook": outlook,
        "confidence": state["confidence"]["score"],
        "confidence_level": state["confidence"]["level"],
        "rationale": rationale,
        "disagreement": disagreement["classification"],
        "failed_agents": disagreement["failed_agents"],
        "evidence_gaps": disagreement["evidence_gaps"],
    }

    return {"final_outlook": result}


# --------------------------------------------------
# LangGraph Construction
# --------------------------------------------------

def build_council_graph():
    graph = StateGraph(CouncilState)

    graph.add_node("valuation", valuation_node)
    graph.add_node("risk", risk_node)
    graph.add_node("momentum", momentum_node)

    graph.add_node("disagreement", disagreement_node)
    graph.add_node("confidence", confidence_node)
    graph.add_node("final_outlook", final_outlook_node)

    # Parallel agent execution
    graph.add_edge(START, "valuation")
    graph.add_edge(START, "risk")
    graph.add_edge(START, "momentum")

    # Fan-in barrier
    graph.add_edge("valuation", "disagreement")
    graph.add_edge("risk", "disagreement")
    graph.add_edge("momentum", "disagreement")

    # Sequential synthesis
    graph.add_edge("disagreement", "confidence")
    graph.add_edge("confidence", "final_outlook")
    graph.add_edge("final_outlook", END)

    return graph.compile()
