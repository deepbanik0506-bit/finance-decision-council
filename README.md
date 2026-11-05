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

Latest recorded test result: 29 passing tests. Tests have not been rerun as part of the final closure.

## Evaluation

The project includes:

- A 10-case benchmark evaluation framework.
- A 13-dimension analytical evaluation rubric.
- A critical failure taxonomy covering evidence fabrication, unsupported directional claims, misinterpretation, synthesis contradictions, and forecast misrepresentation.
- A structured manual review schema and validator.
- Outlook consistency checks and agent execution reliability tracking.

**Evaluation limitation:** Benchmark execution was affected by Groq rate limits and daily token quota exhaustion. The available runs demonstrate system execution and evaluation infrastructure, but do not establish robust analytical accuracy or investment performance.

## Important Limitations

- This is an analytical research prototype, not a validated investment system.
- Market data comes from Yahoo Finance through `yfinance`.
- LLM agents interpret supplied evidence; they do not retrieve live financial news or analyst reports.
- Valuation lacks peer and historical benchmarking.
- Risk assessments are qualitative, not statistically calibrated.
- Confidence scores are heuristic, not probabilities of correctness.
- Outputs are analytical outlooks, not personalized buy/sell recommendations.

## Project Status

**Core system implemented.**

- Multi-agent analysis and LangGraph orchestration.
- Deterministic financial metrics and structured agent outputs.
- Disagreement handling, confidence scoring, and evidence quality assessment.
- Agent failure handling and CLI execution.
- Evaluation framework and manual review infrastructure.

**Sprint 13:** Evaluation infrastructure complete. Benchmark validation remains limited by model quota and incomplete manual scoring.

**Sprint 14:** Deployable interactive project website.

**Sprint 15:** Interview defense and architectural understanding.
