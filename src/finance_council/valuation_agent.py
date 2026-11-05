
import json
import os

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

from src.finance_council.market_data import MarketEvidence

load_dotenv()


class ValuationAssessment(BaseModel):
    ticker: str
    stance: str = Field(
        description="positive, neutral, negative, or insufficient_evidence"
    )
    evidence: list[str]
    assumptions: list[str]
    limitations: list[str]
    reasoning: str


class ValuationAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from .env")
        if not model:
            raise ValueError("GROQ_MODEL is missing from .env")

        self.client = Groq(api_key=api_key)
        self.model = model

    @staticmethod
    def normalize_list_fields(data: dict) -> dict:
        for field in ("evidence", "assumptions", "limitations"):
            value = data.get(field)

            if isinstance(value, str):
                data[field] = [value]
            elif value is None:
                data[field] = []
            elif not isinstance(value, list):
                raise ValueError(
                    f"Invalid valuation field '{field}': "
                    f"expected list or string, got {type(value).__name__}"
                )

        return data

    def assess(self, evidence: MarketEvidence) -> ValuationAssessment:
        financial_data = {
            "ticker": evidence.ticker,
            "company": evidence.company_name,
            "sector": evidence.sector,
            "industry": evidence.industry,
            "market_cap": evidence.market_cap,
            "trailing_pe": evidence.trailing_pe,
            "price_to_book": evidence.price_to_book,
            "enterprise_to_ebitda": evidence.enterprise_to_ebitda,
            "missing_fields": evidence.missing_fields,
        }

        system_prompt = """
You are an independent stock valuation analyst.

Analyze ONLY the supplied financial evidence.
Do not invent values, benchmarks, peer averages, or facts.
Do not calculate metrics that are not supplied.
A valuation ratio alone does not prove a stock is cheap or expensive.
Without peer/sector benchmarks, explicitly state that relative valuation
cannot be established reliably.
Missing evidence is not negative evidence.

Return JSON with exactly these fields:
ticker, stance, evidence, assumptions, limitations, reasoning.

stance must be one of:
positive, neutral, negative, insufficient_evidence.

evidence, assumptions, and limitations MUST be JSON arrays of strings.
Never return these fields as plain strings.

This is analytical research, not personalized financial advice.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(financial_data),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_output = response.choices[0].message.content

        if not raw_output:
            raise ValueError("Groq returned an empty valuation response")

        parsed_output = json.loads(raw_output)
        normalized_output = self.normalize_list_fields(parsed_output)

        return ValuationAssessment.model_validate(normalized_output)
