"""
Currency Exchange Service
-------------------------
Fetches live exchange rates in a background thread and converts amounts with offline
fallback rates when the network is unavailable.

Thread-safe rate access is enforced via a lock so background updates never race with
on-demand conversions on the main thread.
"""
import socket
import threading
import requests


class CurrencyService:
    """Singleton-friendly service for live and fallback currency conversion."""

    def __init__(self):
        self.is_offline = False
        self.rates: dict[str, float] = {}
        self._consecutive_failures = 0
        self._rates_lock = threading.Lock()

        # Static fallback rates (USD base) used when live data is unavailable
        self._fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 155.0,
            "CAD": 1.36,
        }

    def _check_internet_connection(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 2):
        """
        Probe internet connectivity without mutating global socket defaults.

        Uses a scoped connection attempt so other modules are unaffected.
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, OSError):
            return False

    def _handle_failure(self):
        """Track consecutive failures and flip to offline mode at the threshold."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= 3:
            self.is_offline = True

    def _handle_success(self):
        """Reset failure counters and mark the service as online."""
        self._consecutive_failures = 0
        self.is_offline = False

    def fetch_rates_async(self):
        """Schedule a background rate fetch so the GUI thread is never blocked."""
        threading.Thread(target=self._fetch_rates_task, daemon=True).start()

    def _fetch_rates_task(self):
        """Worker that downloads the latest USD-based exchange rates."""
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
        """
        Return the best available rate table.

        Prefers live rates when online; falls back to static estimates when offline
        or when no live data has been fetched yet.
        """
        with self._rates_lock:
            if not self.is_offline and self.rates:
                return dict(self.rates)
        return dict(self._fallback_rates)

    def convert(self, amount, from_currency: str, to_currency: str):
        """
        Convert *amount* from *from_currency* to *to_currency* via USD cross-rates.

        A no-op (still rounded to two decimals) when both currencies match.
        """
        if from_currency == to_currency:
            # Round even for the same-currency case so every code path returns a
            # consistent, currency-formatted value (e.g. 10 → 10.0).
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
