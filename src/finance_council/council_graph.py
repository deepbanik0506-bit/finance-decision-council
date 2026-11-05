from typing import TypedDict

from src.finance_council.market_data import MarketEvidence
from src.finance_council.valuation_agent import ValuationAssessment
from src.finance_council.risk_agent import RiskAssessment
from src.finance_council.momentum_agent import MomentumAssessment


class CouncilState(TypedDict):
    evidence: MarketEvidence
    valuation: ValuationAssessment | None
    risk: RiskAssessment | None
    momentum: MomentumAssessment | None
    disagreement: DisagreementReport | None
    confidence: ConfidenceReport | None
    final_outlook: dict | None


from langgraph.graph import StateGraph, START, END

from src.finance_council.valuation_agent import ValuationAgent
from src.finance_council.risk_agent import RiskAgent
from src.finance_council.momentum_agent import MomentumAgent


def valuation_node(state: CouncilState) -> dict:
    agent = ValuationAgent()
    result = agent.assess(state["evidence"])
    return {"valuation": result}


def risk_node(state: CouncilState) -> dict:
    agent = RiskAgent()
    result = agent.assess(state["evidence"])
    return {"risk": result}


def momentum_node(state: CouncilState) -> dict:
    agent = MomentumAgent()
    result = agent.assess(state["evidence"])
    return {"momentum": result}


def build_council_graph():
    graph = StateGraph(CouncilState)

    graph.add_node("valuation", valuation_node)
    graph.add_node("risk", risk_node)
    graph.add_node("momentum", momentum_node)
    graph.add_node("disagreement", disagreement_node)
    graph.add_node("confidence", confidence_node)
    graph.add_node("final_outlook", final_outlook_node)

    graph.add_edge(START, "valuation")
    graph.add_edge(START, "risk")
    graph.add_edge(START, "momentum")

    graph.add_edge("valuation", "disagreement")
    graph.add_edge("risk", "disagreement")
    graph.add_edge("momentum", "disagreement")
    graph.add_edge("disagreement", "confidence")
    graph.add_edge("confidence", "final_outlook")
    graph.add_edge("final_outlook", END)

    return graph.compile()


class DisagreementReport(TypedDict):
    classification: str
    conflicting_agents: list[str]
    evidence_gaps: list[str]
    explanation: str


def disagreement_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    risk = state["risk"]
    momentum = state["momentum"]

    evidence_gaps = []
    conflicting_agents = []

    if valuation.stance == "insufficient_evidence":
        evidence_gaps.append("valuation")

    if risk.risk_level == "insufficient_evidence":
        evidence_gaps.append("risk")

    if momentum.stance == "insufficient_evidence":
        evidence_gaps.append("momentum")

    # Valuation and momentum are directional signals.
    directional = {
        "valuation": valuation.stance,
        "momentum": momentum.stance,
    }

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
    elif evidence_gaps:
        classification = "insufficient_evidence"
        explanation = (
            "One or more agents could not reach an assessment due to "
            "insufficient evidence."
        )
    else:
        classification = "no_conflict"
        explanation = (
            "No opposing directional assessments were detected."
        )

    report: DisagreementReport = {
        "classification": classification,
        "conflicting_agents": conflicting_agents,
        "evidence_gaps": evidence_gaps,
        "explanation": explanation,
    }

    return {"disagreement": report}


class ConfidenceReport(TypedDict):
    score: int
    level: str
    factors: list[str]
    explanation: str


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
        valuation.stance != "insufficient_evidence",
        risk.risk_level != "insufficient_evidence",
        momentum.stance != "insufficient_evidence",
    ])

    coverage_score = usable_agents / 3
    coverage_penalty = round((1 - coverage_score) * 30)
    score -= coverage_penalty

    if coverage_penalty:
        factors.append(
            f"Insufficient agent assessments: -{coverage_penalty}"
        )

    # Directional conflict
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
            "and directional consistency. It does not predict returns."
        ),
    }

    return {"confidence": report}


def final_outlook_node(state: CouncilState) -> dict:
    valuation = state["valuation"]
    momentum = state["momentum"]

    v = valuation.stance
    m = momentum.stance

    if v == "insufficient_evidence" or m == "insufficient_evidence":
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
        rationale = (
            "Available directional assessments do not establish "
            "a consistent positive or negative outlook."
        )

    return {
        "final_outlook": {
            "outlook": outlook,
            "rationale": rationale,
        }
    }
