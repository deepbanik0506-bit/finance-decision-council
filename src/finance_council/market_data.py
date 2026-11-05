from datetime import datetime, timezone
from typing import Optional

import yfinance as yf
from pydantic import BaseModel, Field


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved or validated."""


class OHLCV(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None


class MarketEvidence(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None

    current_price: Optional[float] = None
    market_cap: Optional[float] = None

    trailing_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None

    beta: Optional[float] = None
    debt_to_equity: Optional[float] = None

    history: list[OHLCV] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    fetched_at: datetime


def fetch_market_data(ticker: str) -> MarketEvidence:
    """
    Fetch and normalize market data for a ticker.
    Raises MarketDataError if the ticker/history is unusable.
    """
    ticker = ticker.strip().upper()

    if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
        raise MarketDataError(f"Invalid ticker format: {ticker!r}")

    try:
        stock = yf.Ticker(ticker)

        # Historical prices are the minimum required evidence.
        raw_history = stock.history(period="1y", interval="1d")

        if raw_history.empty:
            raise MarketDataError(
                f"No price history found for ticker {ticker}"
            )

        history = []
        for date, row in raw_history.iterrows():
            history.append(
                OHLCV(
                    date=date.strftime("%Y-%m-%d"),
                    open=_safe_float(row.get("Open")),
                    high=_safe_float(row.get("High")),
                    low=_safe_float(row.get("Low")),
                    close=_safe_float(row.get("Close")),
                    volume=_safe_int(row.get("Volume")),
                )
            )

        # Company metadata may be incomplete. Missing values are explicit.
        try:
            info = stock.info or {}
        except Exception:
            info = {}

        latest_close = next(
            (row.close for row in reversed(history) if row.close is not None),
            None,
        )   

        evidence = MarketEvidence(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency"),
            current_price=latest_close,
            market_cap=_safe_float(info.get("marketCap")),
            trailing_pe=_safe_float(info.get("trailingPE")),
            price_to_book=_safe_float(info.get("priceToBook")),
            enterprise_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),
            beta=_safe_float(info.get("beta")),
            debt_to_equity=_safe_float(info.get("debtToEquity")),
            history=history,
            missing_fields=[],
            fetched_at=datetime.now(timezone.utc),
        )

        # Explicitly track missing evidence rather than treating it as zero.
        for field in [
            "company_name", "sector", "market_cap",
            "trailing_pe", "price_to_book",
            "enterprise_to_ebitda", "beta", "debt_to_equity",
        ]:
            if getattr(evidence, field) is None:
                evidence.missing_fields.append(field)

        return evidence

    except MarketDataError:
        raise
    except Exception as exc:
        raise MarketDataError(
            f"Failed to fetch market data for {ticker}: {exc}"
        ) from exc


def _safe_float(value) -> Optional[float]:
    try:
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
