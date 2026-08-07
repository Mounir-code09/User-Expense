"""
Currency Exchange Service
Handles real-time exchange rates, caching, and background network polling.
"""
import urllib.request
import json
import time
import threading

class CurrencyService:
    def __init__(self, ttl_seconds=3600):
        self.ttl = ttl_seconds
        self.rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 155.50, "CAD": 1.37}
        self.last_fetch = 0
        self.is_offline = False
        self._lock = threading.Lock()

    def fetch_rates_async(self):
        """Spawns a non-blocking background thread to fetch latest rates."""
        thread = threading.Thread(target=self._fetch_rates_worker, daemon=True)
        thread.start()

    def _fetch_rates_worker(self):
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                with self._lock:
                    self.rates = data.get("rates", self.rates)
                    self.last_fetch = time.time()
                    self.is_offline = False
        except Exception:
            with self._lock:
                self.is_offline = True

    def convert(self, amount, from_currency, to_currency):
        # Trigger background refresh if cache expired
        if time.time() - self.last_fetch > self.ttl:
            self.fetch_rates_async()

        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

        with self._lock:
            if from_curr not in self.rates or to_curr not in self.rates:
                raise ValueError(f"Unsupported currency conversion: {from_curr} -> {to_curr}")
            return round((amount / self.rates[from_curr]) * self.rates[to_curr], 2)

# Singleton service instance
currency_service = CurrencyService()