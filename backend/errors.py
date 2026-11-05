"""API error types and safe translation of council failures.

The council's agent nodes record failures as ``"ExceptionType: message"``
strings. Those raw strings can contain provider response bodies, so they are
logged server-side (with credential redaction) and translated into a fixed
set of categories with user-safe messages before reaching the client.
"""

import re

GROQ_KEY_PATTERN = re.compile(r"gsk_[A-Za-z0-9]{8,}")
BEARER_PATTERN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def redact(text: str) -> str:
    text = GROQ_KEY_PATTERN.sub("gsk_[REDACTED]", text)
    return BEARER_PATTERN.sub("Bearer [REDACTED]", text)


# (category, user-facing message). Order matters: first match wins.
_AGENT_ERROR_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("GROQ_API_KEY is missing", "GROQ_MODEL is missing"),
        "configuration",
        "The analysis service is not configured with model credentials.",
    ),
    (
        ("RateLimitError", "Error code: 429", "rate_limit_exceeded"),
        "rate_limit",
        "The language model provider rate limit or quota was reached. "
        "Try again later.",
    ),
    (
        ("AuthenticationError", "PermissionDeniedError", "Error code: 401",
         "Error code: 403"),
        "provider_auth",
        "The analysis service could not authenticate with the language "
        "model provider.",
    ),
    (
        ("At least 50 valid closing prices",),
        "insufficient_price_history",
        "At least 50 valid closing prices are required to compute momentum "
        "indicators.",
    ),
    (
        ("APIConnectionError", "APITimeoutError", "Timeout"),
        "provider_unavailable",
        "The language model provider could not be reached or timed out.",
    ),
    (
        ("JSONDecodeError", "ValidationError", "empty valuation response",
         "json_validate_failed", "Invalid valuation field"),
        "invalid_model_output",
        "The language model returned output that did not match the "
        "required assessment schema.",
    ),
    (
        ("InternalServerError", "APIStatusError", "BadRequestError",
         "Error code: 5"),
        "provider_error",
        "The language model provider returned an error.",
    ),
]


def categorize_agent_error(raw_error: str) -> tuple[str, str]:
    for needles, category, message in _AGENT_ERROR_RULES:
        if any(needle in raw_error for needle in needles):
            return category, message
    return "unknown", "The agent failed for an unexpected reason."
