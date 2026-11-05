import pytest

from src.finance_council.market_data import (
    MarketDataError,
    _safe_float,
    fetch_market_data,
)


def test_invalid_ticker_format():
    with pytest.raises(MarketDataError):
        fetch_market_data("")


def test_invalid_ticker_characters():
    with pytest.raises(MarketDataError):
        fetch_market_data("AAPL!")


def test_missing_numeric_value():
    assert _safe_float(None) is None


def test_nan_is_normalized():
    assert _safe_float(float("nan")) is None


def test_valid_ticker_returns_evidence():
    evidence = fetch_market_data("AAPL")

    assert evidence.ticker == "AAPL"
    assert evidence.current_price is not None
    assert evidence.current_price > 0
    assert len(evidence.history) > 0
