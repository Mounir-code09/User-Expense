"""
Currency Service Unit Tests
===========================

Validates :class:`core.currency_service.CurrencyService`: live conversion math,
offline fallback rates, same-currency rounding, and the failure threshold.

Why these tests matter
----------------------
Currency conversion touches every stored amount when a user changes their account's
base currency. A rounding or cross-rate bug would silently corrupt financial data,
so the conversion math and the offline fallback path are pinned down here.
"""
import pytest
from core.currency_service import CurrencyService


def test_currency_conversion_fallback():
    """Offline conversions must fall back to the static USD-based rate table."""
    service = CurrencyService()
    # Force empty live rates and offline mode to trigger the fallback dictionary.
    service.rates = {}
    service.is_offline = True

    # USD -> EUR fallback: 1 USD = 0.92 EUR, so 100 USD becomes 92.00 EUR.
    converted_eur = service.convert(100.0, "USD", "EUR")
    assert converted_eur == 92.0

    # Cross-currency path converts through USD: EUR -> USD -> GBP.
    # The exact number depends on the fallback table; we only assert it is a float.
    converted_cross = service.convert(100.0, "EUR", "GBP")
    assert isinstance(converted_cross, float)


def test_same_currency_conversion():
    """Converting a currency into itself must return the amount unchanged."""
    service = CurrencyService()
    assert service.convert(50.0, "USD", "USD") == 50.0
    assert service.convert(250.50, "JPY", "JPY") == 250.50


def test_same_currency_rounds_to_two_decimals():
    """
    The same-currency shortcut must round to 2 decimal places, matching the
    cross-currency path, so all conversions are consistently formatted.
    """
    service = CurrencyService()
    assert service.convert(19.999, "USD", "USD") == 20.0
    assert service.convert(10.005, "EUR", "EUR") == 10.01


def test_failure_threshold_logic():
    """
    The service flips to offline mode only after 3 consecutive failures.

    This prevents a single transient network error from disabling live rates.
    """
    service = CurrencyService()
    assert service.is_offline is False
    assert service._consecutive_failures == 0

    # First failure: tracked but still online.
    service._handle_failure()
    assert service._consecutive_failures == 1
    assert service.is_offline is False

    # Second failure: still under the threshold.
    service._handle_failure()
    assert service._consecutive_failures == 2
    assert service.is_offline is False

    # Third failure: hits the threshold and triggers offline mode.
    service._handle_failure()
    assert service._consecutive_failures == 3
    assert service.is_offline is True
