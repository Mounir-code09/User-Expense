import json
import os
import threading
import requests

CACHE_FILE = "last_known_rates.json"


class CurrencyService:

    def __init__(self):
        self.fallback_rates = {
            "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.0,
            "CAD": 1.36, "AUD": 1.52, "CHF": 0.90, "CNY": 7.24, "INR": 83.5,
        }
        self.is_offline = False
        self.last_error = ""
        self._consecutive_failures = 0
        self._lock = threading.Lock()
        self.rates = self._load_cache()

    def _load_cache(self):
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
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(rates, f, indent=4)
        except OSError:
            pass

    def fetch_live_rates(self):
        # 1. Try Primary API (ExchangeRate-API)
        try:
            resp = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=5,
            )
            if resp.status_code == 200:
                new_rates = resp.json().get("rates", {})
                if new_rates:
                    with self._lock:
                        self.rates.update(new_rates)
                        self.is_offline = False
                        self.last_error = ""
                        self._consecutive_failures = 0
                    self._save_cache(self.rates)
                    return True
        except requests.RequestException:
            pass

        # 2. Try Secondary Fallback API (Frankfurter API)
        try:
            resp = requests.get(
                "https://api.frankfurter.dev/v1/latest?base=USD",
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                new_rates = data.get("rates", {})
                if new_rates:
                    new_rates["USD"] = 1.0
                    with self._lock:
                        self.rates.update(new_rates)
                        self.is_offline = False
                        self.last_error = ""
                        self._consecutive_failures = 0
                    self._save_cache(self.rates)
                    return True
        except requests.RequestException as e:
            self._handle_failure(str(e))
            return False

        self._handle_failure("Primary and fallback rate providers unreachable")
        return False

    def fetch_rates_async(self):
        t = threading.Thread(target=self.fetch_live_rates, daemon=True)
        t.start()
        return t

    def _handle_failure(self, reason="Network error"):
        with self._lock:
            self.last_error = reason
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self.is_offline = True

    def convert(self, amount, from_curr: str, to_curr: str):
        if from_curr == to_curr:
            return round(float(amount), 2)

        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        with self._lock:
            pool = self.rates if self.rates else self.fallback_rates
            from_rate = pool.get(from_curr) or self.fallback_rates.get(from_curr) or 1.0
            to_rate = pool.get(to_curr) or self.fallback_rates.get(to_curr) or 1.0

        return round((float(amount) / from_rate) * to_rate, 2)


currency_service = CurrencyService()