# Finance Decision Council

A multi-agent AI financial analysis system that independently evaluates valuation, risk, and momentum, then synthesizes conflicting evidence into a confidence-scored investment outlook.

## Architecture

- **Market Data Layer:** Retrieves and normalizes market data using `yfinance`.
- **Valuation Agent:** Evaluates valuation metrics and identifies evidence gaps.
- **Risk Agent:** Assesses risk using beta, debt-to-equity, and historical price data.
- **Momentum Agent:** Interprets deterministic price and volume indicators.
- **Orchestrator:** Uses LangGraph to execute specialized agents in parallel and merge their outputs.
- **Disagreement Engine:** Detects conflicting directional assessments and insufficient evidence.
- **Confidence Model:** Produces a heuristic analysis-confidence score.
- **CLI:** Runs the complete council for a specified ticker.

## Tech Stack

Python · LangGraph · Groq · Pydantic · yfinance · pytest

## Setup

```bash
git clone <repository-url>
cd finance-decision-council

python3 -m venv .venv
source .venv/bin/activate

pip install yfinance pydantic pytest python-dotenv groq langgraph
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

## Run

```bash
python -m src.finance_council AAPL
```

Replace `AAPL` with another supported ticker.

## Tests

```bash
pytest
```

## Important Limitations

- This is an analytical research prototype, not a validated investment system.
- Market data comes from Yahoo Finance through `yfinance`.
- LLM agents interpret supplied evidence; they do not retrieve live financial news or analyst reports.
- Valuation lacks peer and historical benchmarking.
- Risk assessments are qualitative, not statistically calibrated.
- Confidence scores are heuristic, not probabilities of correctness.
- Outputs are analytical outlooks, not personalized buy/sell recommendations.

## Project Status

Core multi-agent orchestration and CLI implemented. Failure engineering, systematic evaluation, analytical improvements, and final validation remain planned.
