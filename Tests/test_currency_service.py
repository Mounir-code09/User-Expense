import threading
from core.currency_service import CurrencyService


def _isolated_service(monkeypatch):
    monkeypatch.setattr("core.currency_service.CACHE_FILE", "/dev/null")
    svc = CurrencyService()
    svc.rates = {}
    return svc


def test_conversion_fallback_offline(monkeypatch):
    svc = _isolated_service(monkeypatch)
    svc.is_offline = True

    expected_eur = round((100.0 / svc.fallback_rates["USD"]) * svc.fallback_rates["EUR"], 2)
    assert svc.convert(100.0, "USD", "EUR") == expected_eur
    assert isinstance(svc.convert(100.0, "EUR", "GBP"), float)


def test_same_currency_passthrough():
    svc = CurrencyService()
    assert svc.convert(50.0, "USD", "USD") == 50.0
    assert svc.convert(250.50, "JPY", "JPY") == 250.50


def test_rounding_precision(monkeypatch):
    svc = _isolated_service(monkeypatch)
    svc.fallback_rates = {"USD": 1.0, "EUR": 0.5}

    # 100 USD -> EUR at 0.5 rate = 50.00 exactly; confirms rounding works on actual cross-currency math
    assert svc.convert(100.0, "USD", "EUR") == 50.0
    # Odd floating-point amount
    assert svc.convert(33.333, "USD", "EUR") == 16.67


def test_offline_threshold():
    svc = CurrencyService()
    assert not svc.is_offline

    svc._handle_failure()
    svc._handle_failure()
    assert not svc.is_offline

    svc._handle_failure()
    assert svc.is_offline


def test_missing_rate_fallback_no_crash(monkeypatch):
    svc = _isolated_service(monkeypatch)
    svc.fallback_rates = {}
    result = svc.convert(100.0, "XYZ", "ABC")
    assert isinstance(result, float)
    assert result == 100.0  # both rates default to 1.0 → amount unchanged


def test_async_fetch_returns_thread():
    svc = CurrencyService()
    t = svc.fetch_rates_async()
    assert isinstance(t, threading.Thread)

