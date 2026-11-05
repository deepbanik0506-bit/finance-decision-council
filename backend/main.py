"""FastAPI application exposing the Finance Decision Council over HTTP.

Run locally (from the repository root):
    uvicorn backend.main:app --reload --port 8000
"""

import logging
import math

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend import council_service
from backend.config import get_settings
from backend.errors import ApiError
from backend.rate_limit import ConcurrencyGate, SlidingWindowRateLimiter
from backend.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    ErrorResponse,
    HealthResponse,
)

API_VERSION = "1.0.0"

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("finance_council.api")

app = FastAPI(
    title="Finance Decision Council API",
    version=API_VERSION,
    description=(
        "HTTP interface to the Finance Decision Council multi-agent analysis "
        "system. Analytical research prototype; not investment advice."
    ),
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)

rate_limiter = SlidingWindowRateLimiter(settings.rate_limit_per_minute)
concurrency_gate = ConcurrencyGate(settings.max_concurrent_analyses)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def _error(status: int, code: str, message: str, details=None, headers=None):
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body, headers=headers)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    headers = None
    if exc.status_code == 429 and exc.details and "retry_after" in exc.details:
        headers = {"Retry-After": str(exc.details["retry_after"])}
    return _error(exc.status_code, exc.code, exc.message, exc.details, headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    problems = []
    for err in exc.errors():
        message = str(err.get("msg", "Invalid value"))
        problems.append(
            {
                "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                "message": message.removeprefix("Value error, "),
            }
        )
    first = problems[0]["message"] if problems else "Invalid request."
    return _error(422, "invalid_request", first, {"problems": problems})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return _error(exc.status_code, code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", type(exc).__name__)
    return _error(500, "internal_error", "An unexpected server error occurred.")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="finance-decision-council-api",
        version=API_VERSION,
        council_configured=settings.council_configured,
        model=settings.model_name,
    )


@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    tags=["analysis"],
    responses={
        404: {"model": ErrorResponse, "description": "Ticker has no price history"},
        422: {"model": ErrorResponse, "description": "Malformed request or ticker"},
        429: {"model": ErrorResponse, "description": "Rate limited (API or model provider)"},
        502: {"model": ErrorResponse, "description": "Market data or council execution failed"},
        503: {"model": ErrorResponse, "description": "Server busy or misconfigured"},
    },
)
def analyze(payload: AnalyzeRequest, request: Request) -> AnalysisResponse:
    """Run the full council for one ticker.

    Synchronous: the request returns once all three agents and the
    synthesis have finished (typically several seconds to a minute).
    A 200 response always contains at least one successfully executed agent;
    `status` is `partial` when some agents failed.
    """
    client = request.client.host if request.client else "unknown"
    retry_after = rate_limiter.check(client)
    if retry_after is not None:
        seconds = math.ceil(retry_after)
        raise ApiError(
            429,
            "rate_limited",
            f"Too many analyses requested. Try again in {seconds} seconds.",
            {"retry_after": seconds},
        )

    if not settings.council_configured:
        raise ApiError(
            503,
            "service_misconfigured",
            "The analysis service is not configured with model credentials.",
        )

    if not concurrency_gate.try_acquire():
        raise ApiError(
            503,
            "server_busy",
            "The server is already running the maximum number of analyses. "
            "Try again shortly.",
        )
    try:
        return council_service.run_analysis(payload.ticker)
    finally:
        concurrency_gate.release()
