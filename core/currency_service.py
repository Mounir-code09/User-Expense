"""Currency conversion and exchange-rate fetching."""
import socket
import threading

import requests


class CurrencyService:
    """Provides live or fallback conversion rates."""

    def __init__(self):
        self.is_offline = False
        self.rates: dict[str, float] = {}
        self._consecutive_failures = 0
        self._rates_lock = threading.Lock()

        self._fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 155.0,
            "CAD": 1.36,
        }

    def _check_internet_connection(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 2):
        """Check internet connectivity without affecting other modules."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, OSError):
            return False

    def _handle_failure(self):
        """Increment failures and switch offline mode after 3 consecutive failures."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= 3:
            self.is_offline = True

    def _handle_success(self):
        """Reset failure count and mark service as online."""
        self._consecutive_failures = 0
        self.is_offline = False

    def fetch_rates_async(self):
        """Fetch exchange rates in background thread without blocking GUI."""
        threading.Thread(target=self._fetch_rates_task, daemon=True).start()

    def _fetch_rates_task(self):
        """Download latest USD-based exchange rates from API."""
        if not self._check_internet_connection():
            self._handle_failure()
            return

        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=3,
            )
            if response.status_code == 200:
                self._handle_success()
                with self._rates_lock:
                    self.rates = response.json().get("rates", {})
            else:
                self._handle_failure()
        except (requests.ConnectionError, requests.Timeout, requests.RequestException):
            self._handle_failure()

    def _active_rates(self):
        """Return live rates if online, otherwise fallback to static estimates."""
        with self._rates_lock:
            if not self.is_offline and self.rates:
                return dict(self.rates)
        return dict(self._fallback_rates)

    def convert(self, amount, from_currency: str, to_currency: str):
        """Convert amount between currencies via USD cross-rates. Returns rounded to 2 decimals."""
        if from_currency == to_currency:
            return round(amount, 2)

        rates = self._active_rates()
        rates.setdefault("USD", 1.0)

        from_rate = rates.get(from_currency, 1.0)
        to_rate = rates.get(to_currency, 1.0)

        if from_rate == 0:
            raise ValueError(f"Invalid exchange rate for {from_currency}.")

        amount_in_usd = amount / from_rate
        return round(amount_in_usd * to_rate, 2)


# Shared instance imported across the application
currency_service = CurrencyService()
