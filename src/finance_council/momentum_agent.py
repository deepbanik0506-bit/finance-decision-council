import json
import os

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

from src.finance_council.market_data import MarketEvidence

load_dotenv()


class MomentumAssessment(BaseModel):
    ticker: str
    stance: str = Field(
        description="positive, neutral, negative, or insufficient_evidence"
    )
    evidence: list[str]
    assumptions: list[str]
    limitations: list[str]
    reasoning: str


def calculate_momentum_indicators(evidence: MarketEvidence) -> dict:
    closes = [
        row.close
        for row in evidence.history
        if row.close is not None
    ]

    volumes = [
        row.volume
        for row in evidence.history
        if row.volume is not None
    ]

    if len(closes) < 50:
        raise ValueError("At least 50 valid closing prices are required")

    def moving_average(period: int):
        return sum(closes[-period:]) / period

    price_20d_ago = closes[-21] if len(closes) >= 21 else None
    price_50d_ago = closes[-51] if len(closes) >= 51 else None

    price_change_20d = (
        ((closes[-1] / price_20d_ago) - 1) * 100
        if price_20d_ago
        else None
    )

    price_change_50d = (
        ((closes[-1] / price_50d_ago) - 1) * 100
        if price_50d_ago
        else None
    )

    return {
        "current_close": closes[-1],
        "ma_20": moving_average(20),
        "ma_50": moving_average(50),
        "ma_200": moving_average(200) if len(closes) >= 200 else None,
        "price_change_20d_pct": price_change_20d,
        "price_change_50d_pct": price_change_50d,
        "average_volume_20d": (
            sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None
        ),
        "latest_volume": volumes[-1] if volumes else None,
    }


class MomentumAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from .env")
        if not model:
            raise ValueError("GROQ_MODEL is missing from .env")

        self.client = Groq(api_key=api_key)
        self.model = model

    def assess(self, evidence: MarketEvidence) -> MomentumAssessment:
        indicators = calculate_momentum_indicators(evidence)

        momentum_data = {
            "ticker": evidence.ticker,
            "indicators": indicators,
        }

        system_prompt = """
You are an independent market momentum analyst.

Interpret ONLY the supplied indicators.
Do not invent values, news, catalysts, or market facts.
Do not treat momentum as proof of fundamental value.
Distinguish short-term and longer-term signals.
If indicators conflict, explicitly acknowledge the conflict.
Missing evidence is not negative evidence.

Return ALL SIX required fields. Never omit a field.

- ticker: string
- stance: valid enum value
- evidence: array of strings
- assumptions: array of strings (use [] if none)
- limitations: array of strings (use [] if none)
- reasoning: string

Every response must include assumptions, limitations, and reasoning.

stance must be one of:
positive, neutral, negative, insufficient_evidence.

Be concise and evidence-grounded.
This is analytical research, not personalized financial advice.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(momentum_data)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "momentum_assessment",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "stance": {
                                "type": "string",
                                "enum": [
                                    "positive",
                                    "neutral",
                                    "negative",
                                    "insufficient_evidence",
                                ],
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
                            "stance",
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

        return MomentumAssessment.model_validate(parsed_output)
