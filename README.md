# Finance Decision Council

A multi-agent AI financial analysis system. It evaluates valuation, risk, and momentum independently, then combines conflicting evidence into an outlook with explicit evidence-quality, agreement, and reliability reporting.

It ships as a Python CLI and as a web application: a React frontend backed by a FastAPI service that runs the same LangGraph council.

> **Disclaimer:** Finance Decision Council is an analytical research prototype. Outputs are not personalized investment advice. Confidence scores are heuristic and do not represent probabilities of correctness.

## Architecture

```
Browser ─▶ Vercel: React + TypeScript + Vite (frontend/)
              │  POST {VITE_API_BASE_URL}/api/analyze
              ▼
           Render: FastAPI (backend/)
              │  backend/council_service.py — integration only, no financial logic
              ▼
           LangGraph council (src/finance_council/)
              ├─ market_data.py      ─▶ Yahoo Finance (yfinance)
              ├─ valuation_agent.py  ─┐
              ├─ risk_agent.py       ─┼▶ Groq (parallel)
              ├─ momentum_agent.py   ─┘
              └─ council_graph.py: disagreement → evidence quality / agreement /
                                   execution reliability → final outlook
```

### Council components

- **Market data layer:** retrieves and normalizes one year of daily OHLCV plus fundamentals using `yfinance`. Missing fields are tracked explicitly.
- **Valuation agent:** evaluates valuation metrics and identifies evidence gaps.
- **Risk agent:** assesses risk from beta, debt-to-equity, and historical prices.
- **Momentum agent:** interprets deterministic moving-average, price-change, and volume indicators.
- **Orchestrator:** LangGraph runs the three agents in parallel and merges their outputs. Each agent's failure is captured rather than raised.
- **Disagreement engine:** detects opposing directional assessments, evidence gaps, and agent failures.
- **Heuristic confidence indicators:** categorical *evidence quality*, *analytical agreement*, and *execution reliability*. The council does **not** produce a numeric confidence score. The Sprint 13 refactor replaced the earlier numeric score with these indicators.
- **Final outlook:** a deterministic synthesis of valuation and momentum: `positive`, `negative`, `mixed`, `partial_directional`, or `insufficient_evidence`. Risk is context only.

### Web application

- **Backend (`backend/`):** FastAPI wrapper. It validates input, calls `fetch_market_data` and the compiled council graph with the same initial state as the CLI, then maps the state to a typed response. The response reuses the council's own Pydantic models and report types.
- **Frontend (`frontend/`):** a dark analytical interface. It shows the outlook, the three heuristic indicators, separate agent panels (signal, inputs, evidence, assumptions, limitations, reasoning, execution status), an agreement/disagreement view, price and volume charts, and JSON export.

## Features

- Ticker input with client-side and server-side validation.
- Loading state that reports what is actually happening. The API returns once, when the council finishes, so the UI shows a single "analysis running" state with elapsed time and no invented per-agent progress.
- Final outlook, evidence quality, analytical agreement, and execution reliability, rendered from the returned values.
- Separate Valuation, Risk, and Momentum panels. A failed agent shows its failure category, never an invented assessment.
- Directional alignment view (negative / no direction / positive) with conflicts, evidence gaps, and failures.
- Price and volume charts built from the same yfinance history the agents received, with 1M/3M/6M/1Y ranges, a crosshair tooltip, a table view, and markers for the momentum agent's 20- and 50-session windows. Momentum indicator values come from the council's own `calculate_momentum_indicators`.
- JSON export of the exact API response.
- Error handling for: invalid ticker, unknown ticker, market-data outage, partial agent failure, all agents failing, Groq rate limits, server busy, a misconfigured backend, a misconfigured frontend, timeout, and network failure. Each error has a retry button.

## Screenshots

_Placeholder. Add screenshots from a live deployment run here (e.g. `docs/screenshots/result.png`)._

## Tech stack

**Council:** Python · LangGraph · Groq · Pydantic · yfinance · pytest
**API:** FastAPI · uvicorn
**Frontend:** React 19 · TypeScript · Vite · Tailwind CSS v4 · Recharts
**Hosting (target):** Render (API) · Vercel (frontend)

## Local setup

Requirements: Python 3.14 (the verified version), Node.js 20+.

### Backend

```bash
git clone <repository-url>
cd finance-decision-council

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env   # then set GROQ_API_KEY
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # optional; defaults work for local dev
```

## Environment variables

**Backend** (`.env` locally, Render dashboard in production). Full list in [`.env.example`](.env.example):

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq credential (secret, server-side only) |
| `GROQ_MODEL` | yes | e.g. `openai/gpt-oss-20b` |
| `ALLOWED_ORIGINS` | prod | Comma-separated CORS origins |
| `ALLOWED_ORIGIN_REGEX` | no | Extra origins pattern (e.g. Vercel previews) |
| `RATE_LIMIT_PER_MINUTE` | no | Default `5` per client IP |
| `MAX_CONCURRENT_ANALYSES` | no | Default `2` |
| `ENABLE_DOCS` | no | Default `true` (`/docs`) |

**Frontend** (`frontend/.env.local` locally, Vercel dashboard in production):

| Variable | Required | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | prod | Backend URL. Public: never put secrets in `VITE_*`. |
| `DEV_API_PROXY_TARGET` | no | Dev-server proxy target, default `http://127.0.0.1:8000` |

## Running locally

```bash
# Terminal 1 — API (from repository root)
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev        # http://localhost:5173
```

In development, leave `VITE_API_BASE_URL` empty. The Vite dev server then proxies `/api` and `/health` to the local API.

CLI (unchanged):

```bash
python -m src.finance_council AAPL
```

## API

Interactive docs: `GET /docs` (OpenAPI at `/openapi.json`).

### `GET /health`

```json
{"status":"ok","service":"finance-decision-council-api","version":"1.0.0","council_configured":true,"model":"openai/gpt-oss-20b"}
```

### `POST /api/analyze`

Request:

```json
{"ticker": "AAPL"}
```

The ticker is trimmed and upper-cased. It must be 1–10 characters (letters, digits, `.`, `-`), starting with a letter or digit. Unknown fields are rejected.

Response `200` (abridged; all fields come from the council):

```jsonc
{
  "ticker": "AAPL",
  "analyzed_at": "2026-11-05T13:05:41Z",
  "duration_seconds": 8.4,
  "status": "complete",              // "partial" if 1–2 agents failed
  "model": "openai/gpt-oss-20b",
  "final_outlook": { "overall_outlook": "mixed", "dimensions": {...}, "interpretation": "...", ... },
  "agents": {
    "valuation": { "status": "succeeded", "assessment": { "stance", "evidence", "assumptions", "limitations", "reasoning", ... }, "failure": null },
    "risk":      { "status": "succeeded", "assessment": { "risk_level", ... }, "failure": null },
    "momentum":  { "status": "failed", "assessment": null, "failure": { "category": "rate_limit", "message": "..." } }
  },
  "disagreement":          { "classification", "conflicting_agents", "failed_agents", "evidence_gaps", "explanation" },
  "evidence_quality":      { "level", "usable_dimensions", "insufficient_dimensions", "failed_dimensions", "explanation" },
  "analytical_agreement":  { "classification", "directional_agents", "positive_agents", "negative_agents", "explanation" },
  "execution_reliability": { "successful_agents", "failed_agents", "success_count", "total_agents", "reliability", "explanation" },
  "market_evidence":       { "company_name", "trailing_pe", ..., "history": [{ "date", "open", "high", "low", "close", "volume" }], "missing_fields": [...] },
  "momentum_indicators":   { "ma_20", "ma_50", "ma_200", "price_change_20d_pct", ... },
  "disclaimer": "..."
}
```

Errors use one shape, `{"error": {"code", "message", "details?"}}`:

| HTTP | `code` | When |
|---|---|---|
| 422 | `invalid_request` | Malformed body or ticker |
| 404 | `ticker_not_found` | yfinance returned no price history |
| 429 | `rate_limited` | API throttle (`Retry-After` header set) |
| 429 | `provider_rate_limited` | All three agents hit Groq rate limits; no result produced |
| 502 | `market_data_unavailable` | yfinance failure |
| 502 | `council_execution_failed` | All three agents failed; `details.agent_failures` lists categories |
| 503 | `service_misconfigured` / `server_busy` | Missing Groq config / concurrency cap reached |
| 500 | `internal_error` | Unexpected error (no stack trace exposed) |

**Failure semantics.** If at least one agent succeeds, the API returns the council's result, with `status: "partial"` and each failed agent listed as failed. If all agents fail, the API returns an error instead of a result. Otherwise the council's `insufficient_evidence` synthesis would be presented as if the evidence had been assessed. Raw agent error strings are logged server-side with credential redaction. Clients receive only a fixed category (`rate_limit`, `provider_auth`, `invalid_model_output`, `insufficient_price_history`, …) and a safe message.

## Tests

```bash
pytest
```

61 tests pass: 29 existing council, market-data, and manual-review tests, plus 32 API tests in `tests/test_api.py`. The API tests mock yfinance and the three agents' Groq calls, so they use no quota. The real LangGraph graph and its synthesis nodes run unmodified. `tests/test_market_data.py::test_valid_ticker_returns_evidence` still makes a live yfinance request.

## Deployment

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for step-by-step Render and Vercel instructions. In short:

- **Render:** build `pip install -r requirements.txt`, start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`, health check `/health`, secrets `GROQ_API_KEY` and `ALLOWED_ORIGINS`. A `render.yaml` blueprint is included.
- **Vercel:** root directory `frontend`, Vite preset, set `VITE_API_BASE_URL` to the Render URL.

## Evaluation

The project includes:

- A 10-case benchmark evaluation framework.
- A 13-dimension analytical evaluation rubric.
- A critical failure taxonomy covering evidence fabrication, unsupported directional claims, misinterpretation, synthesis contradictions, and forecast misrepresentation.
- A structured manual review schema and validator.
- Outlook consistency checks and agent execution reliability tracking.

**Evaluation limitation:** Groq rate limits and daily token quota exhaustion affected benchmark execution. The available runs demonstrate that the system and evaluation infrastructure execute. They do not establish analytical accuracy or investment performance.

## Important limitations

- This is an analytical research prototype, not a validated investment system.
- Market data comes from Yahoo Finance through `yfinance`. Availability and accuracy depend on that source.
- LLM agents interpret supplied evidence. They do not retrieve live news or analyst reports.
- Valuation lacks peer and historical benchmarking.
- Risk assessments are qualitative, not statistically calibrated.
- Confidence indicators are heuristic, not probabilities of correctness. There is no numeric confidence score.
- Outputs are analytical outlooks, not personalized buy/sell recommendations.
- **Web app:** each analysis makes three Groq calls, so throughput is bound by Groq quota. Rate limiting and the concurrency cap are in-memory and per process (fine for one Render instance, not shared across replicas). The per-IP limit relies on proxy headers and is best-effort. The API is synchronous, so there is no streaming progress. Free Render instances cold-start slowly.

## Project status

**Core system implemented.**

- Multi-agent analysis and LangGraph orchestration.
- Deterministic financial metrics and structured agent outputs.
- Disagreement handling, heuristic confidence indicators, and evidence quality assessment.
- Agent failure handling and CLI execution.
- Evaluation framework and manual review infrastructure.

**Sprint 13:** Evaluation infrastructure complete. Benchmark validation remains limited by model quota and incomplete manual scoring.

**Sprint 14:** Interactive website implemented (FastAPI + React) and prepared for Render/Vercel deployment. Not yet deployed.

**Sprint 15:** Interview defense and architectural understanding.
