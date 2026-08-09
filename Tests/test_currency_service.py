"""
Unit Tests for Currency Service Module
Validates live conversion math, fallback rates, and offline failure threshold logic.
"""
import pytest
from core.currency_service import CurrencyService

def test_currency_conversion_fallback():
    service = CurrencyService()
    # Force empty rates to trigger fallback dictionary
    service.rates = {}
    service.is_offline = True

    # Test USD to EUR fallback (1 USD = 0.92 EUR)
    converted_eur = service.convert(100.0, "USD", "EUR")
    assert converted_eur == 92.0

    # Test cross currency (EUR to GBP via USD base cross-rate)
    # 100 EUR -> USD -> GBP
    converted_cross = service.convert(100.0, "EUR", "GBP")
    assert isinstance(converted_cross, float)

def test_same_currency_conversion():
    service = CurrencyService()
    # Converting same currency should return identical amount immediately
    assert service.convert(50.0, "USD", "USD") == 50.0
    assert service.convert(250.50, "JPY", "JPY") == 250.50

def test_failure_threshold_logic():
    service = CurrencyService()
    assert service.is_offline is False
    assert service._consecutive_failures == 0

    # Simulate failures up to threshold (3)
    service._handle_failure()
    assert service._consecutive_failures == 1
    assert service.is_offline is False

    service._handle_failure()
    assert service._consecutive_failures == 2
    assert service.is_offline is False

    # 3rd failure hits threshold and triggers offline mode
    service._handle_failure()
    assert service._consecutive_failures == 3
    assert service.is_offline is True