"""Request/response contracts for the HTTP API.

Wherever possible these reuse the council's own models (agent assessments,
MarketEvidence, report TypedDicts) so the API exposes exactly what the
council produces, without invented fields.
"""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.finance_council.council_graph import (
    AgreementReport,
    DisagreementReport,
    EvidenceQualityReport,
    ExecutionReport,
)
from src.finance_council.market_data import MarketEvidence
from src.finance_council.momentum_agent import MomentumAssessment
from src.finance_council.risk_agent import RiskAssessment
from src.finance_council.valuation_agent import ValuationAssessment

# Same character set accepted by fetch_market_data (alphanumerics, '.', '-'),
# with a length cap. Must start with an alphanumeric character.
TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")

DISCLAIMER = (
    "Finance Decision Council is an analytical research prototype. Outputs "
    "are not personalized investment advice. Confidence scores are heuristic "
    "and do not represent probabilities of correctness."
)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        max_length=16,
        description="Ticker symbol, e.g. AAPL, BRK-B, RELIANCE.NS",
        examples=["AAPL"],
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(
                "Ticker must be 1-10 characters: letters, digits, '.' or '-', "
                "starting with a letter or digit."
            )
        return ticker


class AgentFailure(BaseModel):
    category: str
    message: str


class ValuationResult(BaseModel):
    agent: Literal["valuation"] = "valuation"
    status: Literal["succeeded", "failed"]
    assessment: ValuationAssessment | None
    failure: AgentFailure | None


class RiskResult(BaseModel):
    agent: Literal["risk"] = "risk"
    status: Literal["succeeded", "failed"]
    assessment: RiskAssessment | None
    failure: AgentFailure | None


class MomentumResult(BaseModel):
    agent: Literal["momentum"] = "momentum"
    status: Literal["succeeded", "failed"]
    assessment: MomentumAssessment | None
    failure: AgentFailure | None


class AgentResults(BaseModel):
    valuation: ValuationResult
    risk: RiskResult
    momentum: MomentumResult


class MomentumIndicators(BaseModel):
    """Output of the council's deterministic calculate_momentum_indicators."""

    current_close: float | None = None
    ma_20: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None
    price_change_20d_pct: float | None = None
    price_change_50d_pct: float | None = None
    average_volume_20d: float | None = None
    latest_volume: float | None = None


class FinalOutlook(BaseModel):
    """Mirror of the dict produced by council_graph.final_outlook_node."""

    ticker: str
    dimensions: dict[str, str]
    overall_outlook: str
    interpretation: str
    evidence_quality: EvidenceQualityReport
    analytical_agreement: AgreementReport
    execution_reliability: ExecutionReport
    disagreement: str
    failed_agents: list[str]
    evidence_gaps: list[str]


class AnalysisResponse(BaseModel):
    ticker: str
    analyzed_at: datetime
    duration_seconds: float
    status: Literal["complete", "partial"] = Field(
        description="complete: all agents executed; partial: some failed."
    )
    model: str | None
    final_outlook: FinalOutlook
    agents: AgentResults
    disagreement: DisagreementReport
    evidence_quality: EvidenceQualityReport
    analytical_agreement: AgreementReport
    execution_reliability: ExecutionReport
    market_evidence: MarketEvidence
    momentum_indicators: MomentumIndicators | None
    momentum_indicators_unavailable_reason: str | None
    disclaimer: str = DISCLAIMER


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    council_configured: bool
    model: str | None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
