
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


class EvidenceQualityReport(TypedDict):
    level: str
    usable_dimensions: list[str]
    insufficient_dimensions: list[str]
    failed_dimensions: list[str]
    explanation: str


class AgreementReport(TypedDict):
    classification: str
    directional_agents: list[str]
    positive_agents: list[str]
    negative_agents: list[str]
    explanation: str


class ExecutionReport(TypedDict):
    successful_agents: list[str]
    failed_agents: list[str]
    success_count: int
    total_agents: int
    reliability: str
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
    evidence_quality: EvidenceQualityReport | None
    analytical_agreement: AgreementReport | None
    execution_reliability: ExecutionReport | None
    final_outlook: dict | None


# --------------------------------------------------
# Agent Nodes
# --------------------------------------------------

def valuation_node(state: CouncilState) -> dict:
    try:
        result = ValuationAgent().assess(state["evidence"])
        return {"valuation": result, "valuation_error": None}
    except Exception as exc:
        return {
            "valuation": None,
            "valuation_error": f"{type(exc).__name__}: {exc}",
        }


def risk_node(state: CouncilState) -> dict:
    try:
        result = RiskAgent().assess(state["evidence"])
        return {"risk": result, "risk_error": None}
    except Exception as exc:
        return {
            "risk": None,
            "risk_error": f"{type(exc).__name__}: {exc}",
        }


def momentum_node(state: CouncilState) -> dict:
    try:
        result = MomentumAgent().assess(state["evidence"])
        return {"momentum": result, "momentum_error": None}
    except Exception as exc:
        return {
            "momentum": None,
            "momentum_error": f"{type(exc).__name__}: {exc}",
        }


# --------------------------------------------------
# Disagreement and Quality Analysis
# --------------------------------------------------

def disagreement_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    risk = state["risk"]
    momentum = state["momentum"]

    failed_agents = []
    evidence_gaps = []
    conflicting_agents = []

    if state["valuation_error"]:
        failed_agents.append("valuation")
    elif valuation is None or valuation.stance == "insufficient_evidence":
        evidence_gaps.append("valuation")

    if state["risk_error"]:
        failed_agents.append("risk")
    elif risk is None or risk.risk_level == "insufficient_evidence":
        evidence_gaps.append("risk")

    if state["momentum_error"]:
        failed_agents.append("momentum")
    elif momentum is None or momentum.stance == "insufficient_evidence":
        evidence_gaps.append("momentum")

    directional = {}
    if valuation is not None and not state["valuation_error"]:
        if valuation.stance in ("positive", "negative"):
            directional["valuation"] = valuation.stance

    if momentum is not None and not state["momentum_error"]:
        if momentum.stance in ("positive", "negative"):
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
        explanation = "Directional agents produced opposing assessments."
    elif failed_agents:
        classification = "agent_failure"
        explanation = "One or more agents failed during execution."
    elif evidence_gaps:
        classification = "evidence_gap"
        explanation = "One or more dimensions lack sufficient evidence."
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


def evidence_quality_node(state: CouncilState) -> dict:
    assessments = {
        "valuation": (
            state["valuation"],
            state["valuation_error"],
            "stance",
        ),
        "risk": (
            state["risk"],
            state["risk_error"],
            "risk_level",
        ),
        "momentum": (
            state["momentum"],
            state["momentum_error"],
            "stance",
        ),
    }

    usable = []
    insufficient = []
    failed = []

    for name, (assessment, error, field) in assessments.items():
        if error:
            failed.append(name)
        elif assessment is not None and getattr(assessment, field) != "insufficient_evidence":
            usable.append(name)
        else:
            insufficient.append(name)

    if len(usable) == 3:
        level = "complete"
    elif usable:
        level = "partial"
    else:
        level = "poor"

    report: EvidenceQualityReport = {
        "level": level,
        "usable_dimensions": usable,
        "insufficient_dimensions": insufficient,
        "failed_dimensions": failed,
        "explanation": (
            f"{len(usable)} of 3 dimensions produced usable assessments. "
            "Execution failures are tracked separately."
        ),
    }

    return {"evidence_quality": report}


def analytical_agreement_node(state: CouncilState) -> dict:
    directional = {}

    valuation = state["valuation"]
    momentum = state["momentum"]

    if valuation is not None and not state["valuation_error"]:
        if valuation.stance in ("positive", "negative"):
            directional["valuation"] = valuation.stance

    if momentum is not None and not state["momentum_error"]:
        if momentum.stance in ("positive", "negative"):
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
        classification = "conflicting"
        explanation = "Directional assessments disagree."
    elif len(directional) >= 2:
        classification = "aligned"
        explanation = "Available directional assessments agree."
    elif directional:
        classification = "limited"
        explanation = "Only one directional assessment is available."
    else:
        classification = "unestablished"
        explanation = "No usable directional assessments are available."

    report: AgreementReport = {
        "classification": classification,
        "directional_agents": list(directional),
        "positive_agents": positive,
        "negative_agents": negative,
        "explanation": explanation,
    }

    return {"analytical_agreement": report}


def execution_reliability_node(state: CouncilState) -> dict:
    errors = {
        "valuation": state["valuation_error"],
        "risk": state["risk_error"],
        "momentum": state["momentum_error"],
    }

    failed = [name for name, error in errors.items() if error]
    successful = [name for name, error in errors.items() if not error]

    count = len(successful)

    if count == 3:
        reliability = "complete"
    elif count > 0:
        reliability = "partial"
    else:
        reliability = "failed"

    report: ExecutionReport = {
        "successful_agents": successful,
        "failed_agents": failed,
        "success_count": count,
        "total_agents": 3,
        "reliability": reliability,
        "explanation": (
            f"{count} of 3 agents executed successfully. "
            "Successful execution does not imply sufficient evidence."
        ),
    }

    return {"execution_reliability": report}


# --------------------------------------------------
# Dimension-Aware Final Outlook
# --------------------------------------------------

def final_outlook_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    risk = state["risk"]
    momentum = state["momentum"]

    valuation_status = (
        valuation.stance if valuation is not None else "failed"
    )
    risk_status = (
        risk.risk_level if risk is not None else "failed"
    )
    momentum_status = (
        momentum.stance if momentum is not None else "failed"
    )

    dimensions = {
        "valuation": valuation_status,
        "risk": risk_status,
        "momentum": momentum_status,
    }

    usable_directional = [
        value for value in (valuation_status, momentum_status)
        if value in ("positive", "negative")
    ]

    if len(usable_directional) == 2:
        if usable_directional[0] == usable_directional[1]:
            overall = usable_directional[0]
            rationale = (
                "Valuation and momentum support the same direction. "
                "Risk remains a separate contextual assessment."
            )
        else:
            overall = "mixed"
            rationale = (
                "Valuation and momentum provide opposing directional signals."
            )
    elif len(usable_directional) == 1:
        overall = "partial_directional"
        rationale = (
            "One dimension provides a directional signal; "
            "the other does not establish direction."
        )
    else:
        overall = "insufficient_evidence"
        rationale = "No usable directional synthesis can be established."

    result = {
        "ticker": state["evidence"].ticker,
        "dimensions": dimensions,
        "overall_outlook": overall,
        "interpretation": rationale,
        "evidence_quality": state["evidence_quality"],
        "analytical_agreement": state["analytical_agreement"],
        "execution_reliability": state["execution_reliability"],
        "disagreement": state["disagreement"]["classification"],
        "failed_agents": state["disagreement"]["failed_agents"],
        "evidence_gaps": state["disagreement"]["evidence_gaps"],
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
    graph.add_node("evidence_quality", evidence_quality_node)
    graph.add_node("analytical_agreement", analytical_agreement_node)
    graph.add_node("execution_reliability", execution_reliability_node)
    graph.add_node("final_outlook", final_outlook_node)

    graph.add_edge(START, "valuation")
    graph.add_edge(START, "risk")
    graph.add_edge(START, "momentum")

    graph.add_edge("valuation", "disagreement")
    graph.add_edge("risk", "disagreement")
    graph.add_edge("momentum", "disagreement")

    graph.add_edge("disagreement", "evidence_quality")
    graph.add_edge("disagreement", "analytical_agreement")
    graph.add_edge("disagreement", "execution_reliability")

    graph.add_edge("evidence_quality", "final_outlook")
    graph.add_edge("analytical_agreement", "final_outlook")
    graph.add_edge("execution_reliability", "final_outlook")

    graph.add_edge("final_outlook", END)

    return graph.compile()
