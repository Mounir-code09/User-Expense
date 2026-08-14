"""Currency conversion service with local caching and offline fallback."""
import json
import os
import threading
import requests

CACHE_FILE = "last_known_rates.json"


class CurrencyService:
    """Handles live exchange rate updates, persistent caching, and conversions."""

    def __init__(self):
        self.fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 150.0,
            "CAD": 1.36,
            "AUD": 1.52,
            "CHF": 0.90,
            "CNY": 7.24,
            "INR": 83.5,
        }
        self.is_offline = False
        self._consecutive_failures = 0
        self._lock = threading.Lock()
        self.rates = self._load_cache()

    def _load_cache(self):
        """Load previously saved rates from disk or return fallback rates."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return data
            except (json.JSONDecodeError, OSError):
                pass
        return self.fallback_rates.copy()

    def _save_cache(self, rates):
        """Save rates to disk cache."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(rates, f, indent=4)
        except OSError:
            pass

    def fetch_live_rates(self):
        """Fetch live exchange rates from the API and update the cache."""
        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                new_rates = data.get("rates", {})
                if new_rates:
                    with self._lock:
                        self.rates.update(new_rates)
                        self.is_offline = False
                        self._consecutive_failures = 0
                    self._save_cache(self.rates)
                    return True
            self._handle_failure()
        except requests.RequestException:
            self._handle_failure()
        return False

    def fetch_rates_async(self):
        """Fetch live exchange rates in a background thread."""
        thread = threading.Thread(target=self.fetch_live_rates, daemon=True)
        thread.start()
        return thread

    def _handle_failure(self):
        """Track consecutive network failures and enable offline mode if needed."""
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self.is_offline = True

    def convert(self, amount, from_curr: str, to_curr: str):
        """Convert amount between currencies using live or cached rates."""
        if from_curr == to_curr:
            return round(float(amount), 2)

        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        with self._lock:
            rates_map = self.rates if self.rates else self.fallback_rates
            from_rate = rates_map.get(from_curr, self.fallback_rates.get(from_curr, 1.0))
            to_rate = rates_map.get(to_curr, self.fallback_rates.get(to_curr, 1.0))

        if from_rate <= 0:
            from_rate = 1.0

        converted = (float(amount) / from_rate) * to_rate
        return round(converted, 2)


currency_service = CurrencyService()