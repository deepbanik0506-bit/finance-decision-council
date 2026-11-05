"""Runtime configuration for the API, read from environment variables.

Secrets (GROQ_API_KEY) are read by the existing council agents directly from
the environment; this module only reports whether they are present and never
stores or returns their values.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DEV_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]
    allowed_origin_regex: str | None
    rate_limit_per_minute: int
    max_concurrent_analyses: int
    enable_docs: bool
    log_level: str

    @property
    def council_configured(self) -> bool:
        return bool(os.getenv("GROQ_API_KEY")) and bool(os.getenv("GROQ_MODEL"))

    @property
    def model_name(self) -> str | None:
        return os.getenv("GROQ_MODEL") or None


@lru_cache
def get_settings() -> Settings:
    origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_DEV_ORIGINS)
    return Settings(
        allowed_origins=tuple(
            o.strip().rstrip("/") for o in origins.split(",") if o.strip()
        ),
        allowed_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX") or None,
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 5),
        max_concurrent_analyses=_int_env("MAX_CONCURRENT_ANALYSES", 2),
        enable_docs=_bool_env("ENABLE_DOCS", True),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
