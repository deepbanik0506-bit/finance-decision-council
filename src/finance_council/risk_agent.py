import json
import os

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

from src.finance_council.market_data import MarketEvidence

load_dotenv()


class RiskAssessment(BaseModel):
    ticker: str
    risk_level: str = Field(
        description="low, moderate, high, or insufficient_evidence"
    )
    evidence: list[str]
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    reasoning: str = "Reasoning not provided by model."


class RiskAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from .env")
        if not model:
            raise ValueError("GROQ_MODEL is missing from .env")

        self.client = Groq(api_key=api_key)
        self.model = model

    def assess(self, evidence: MarketEvidence) -> RiskAssessment:
        risk_data = {
            "ticker": evidence.ticker,
            "company": evidence.company_name,
            "sector": evidence.sector,
            "beta": evidence.beta,
            "debt_to_equity": evidence.debt_to_equity,
            "history": [
                {"date": row.date, "close": row.close}
                for row in evidence.history
            ],
            "missing_fields": evidence.missing_fields,
        }

        system_prompt = """
You are an independent financial risk analyst.

Assess risk using ONLY the supplied evidence.
Do not invent metrics, benchmarks, or facts.
Beta measures sensitivity to broad market movements, not total risk.
Debt-to-equity indicates leverage, but interpretation depends on industry.
Historical price variability is not a complete measure of future risk.
Missing evidence is not negative evidence.

Return JSON with exactly these fields:
ticker, risk_level, evidence, assumptions, limitations, reasoning.

risk_level must be one of:
low, moderate, high, insufficient_evidence.

Be concise, evidence-grounded, and cautious.
This is analytical research, not personalized financial advice.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(risk_data)},
            ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "risk_assessment",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "risk_level": {
                                    "type": "string",
                                    "enum": ["low", "moderate", "high", "insufficient_evidence"],
                                },
                                "evidence": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "assumptions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "limitations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "reasoning": {"type": "string"},
                            },
                            "required": [
                                "ticker",
                                "risk_level",
                                "evidence",
                                "assumptions",
                                "limitations",
                                "reasoning",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
            temperature=0.1,
        )

        raw_output = response.choices[0].message.content
        parsed_output = json.loads(raw_output)

        return RiskAssessment.model_validate(parsed_output)
