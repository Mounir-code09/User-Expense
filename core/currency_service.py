"""
Currency Exchange Service
Handles real-time exchange rates, caching, consecutive failure tracking, and instant socket-based network connectivity polling.
"""
import requests
import threading
import socket

class CurrencyService:
    def __init__(self):
        self.is_offline = False
        self.rates = {}
        self._consecutive_failures = 0

    def _check_internet_connection(self, host="8.8.8.8", port=53, timeout=2):
        """Quickly checks actual internet connectivity via socket to detect Wi-Fi drops instantly."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.error, OSError):
            return False

    def _handle_failure(self):
        """Increments consecutive failure count and sets offline status when threshold is reached."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= 3:
            self.is_offline = True

    def _handle_success(self):
        """Resets consecutive failures and sets online status."""
        self._consecutive_failures = 0
        self.is_offline = False

    def fetch_rates_async(self):
        # Run network requests in a background thread to prevent GUI freezing
        threading.Thread(target=self._fetch_rates_task, daemon=True).start()

    def _fetch_rates_task(self):
        # Instantly check socket connectivity
        if not self._check_internet_connection():
            self._handle_failure()
            return

        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
            
            if response.status_code == 200:
                self._handle_success()
                data = response.json()
                self.rates = data.get("rates", {})
            else:
                self._handle_failure()
                
        except (requests.ConnectionError, requests.Timeout, requests.RequestException):
            self._handle_failure()

    def convert(self, amount, from_currency, to_currency):
        if from_currency == to_currency:
            return amount
        
        # Fallback static rates used when offline or rates dictionary is empty
        fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 155.0,
            "CAD": 1.36
        }
        
        rates = self.rates if self.rates else fallback_rates
        if "USD" not in rates:
            rates["USD"] = 1.0
            
        from_rate = rates.get(from_currency, 1.0)
        to_rate = rates.get(to_currency, 1.0)
        
        # Convert amounts through USD base cross-rate calculation
        amount_in_usd = amount / from_rate
        converted_amount = amount_in_usd * to_rate
        return round(converted_amount, 2)

# Global singleton instance imported across modules
currency_service = CurrencyService()