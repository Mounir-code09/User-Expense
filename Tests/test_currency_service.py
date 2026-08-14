"""Currency conversion, exchange rates, and offline fallback tests."""
import threading
import pytest
from core.currency_service import CurrencyService


def test_currency_conversion_fallback():
    """Offline mode uses static fallback exchange rates."""
    service = CurrencyService()
    service.rates = {}
    service.is_offline = True

    converted_eur = service.convert(100.0, "USD", "EUR")
    assert converted_eur == 92.0

    converted_cross = service.convert(100.0, "EUR", "GBP")
    assert isinstance(converted_cross, float)


def test_same_currency_conversion():
    """Same currency conversion returns amount unchanged."""
    service = CurrencyService()
    assert service.convert(50.0, "USD", "USD") == 50.0
    assert service.convert(250.50, "JPY", "JPY") == 250.50


def test_same_currency_rounds_to_two_decimals():
    """All conversions are rounded consistently to 2 decimal places."""
    service = CurrencyService()
    assert service.convert(19.999, "USD", "USD") == 20.0
    assert service.convert(10.005, "EUR", "EUR") == 10.01


def test_failure_threshold_logic():
    """Service switches to offline mode only after 3 consecutive failures."""
    service = CurrencyService()
    assert service.is_offline is False
    assert service._consecutive_failures == 0

    service._handle_failure()
    assert service._consecutive_failures == 1
    assert service.is_offline is False

    service._handle_failure()
    assert service._consecutive_failures == 2
    assert service.is_offline is False

    service._handle_failure()
    assert service._consecutive_failures == 3
    assert service.is_offline is True


def test_fetch_rates_async():
    """Async rate fetching returns a running or completed thread."""
    service = CurrencyService()
    thread = service.fetch_rates_async()
    assert isinstance(thread, threading.Thread)
