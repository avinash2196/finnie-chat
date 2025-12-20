"""
External Portfolio Adapter (skeleton)

This provides a drop-in client with the same methods as the internal `PortfolioClient`.
By default this module is a no-op/skeleton so tests and local dev keep using the mock
implementation. When you have a real external portfolio service, configure the
`PORTFOLIO_BACKEND=external` and set `EXTERNAL_PORTFOLIO_BASE_URL` and
`EXTERNAL_PORTFOLIO_API_KEY` env vars.

The class implements:
- get_holdings()
- get_profile()
- get_transactions()
- get_dividends()
- get_performance()
- record_buy(), record_sell(), record_dividend()

This skeleton uses `httpx` when implemented, but currently returns structured
error responses to make failures explicit.
"""
from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

EXTERNAL_BASE_URL = os.getenv("EXTERNAL_PORTFOLIO_BASE_URL", "")
EXTERNAL_API_KEY = os.getenv("EXTERNAL_PORTFOLIO_API_KEY", "")


class ExternalPortfolioClient:
    """Skeleton external portfolio client.

    Replace internals with actual HTTP calls to the external portfolio API.
    """
    def __init__(self, user_id: str = "user_123"):
        self.user_id = user_id
        self.base_url = EXTERNAL_BASE_URL
        self.api_key = EXTERNAL_API_KEY

    def _not_configured(self):
        return {
            "error": "external_backend_not_configured",
            "message": "External portfolio backend not configured. Set EXTERNAL_PORTFOLIO_BASE_URL and EXTERNAL_PORTFOLIO_API_KEY."
        }

    def get_holdings(self) -> Dict:
        # TODO: Implement real HTTP call. For now return a clear error structure.
        if not (self.base_url and self.api_key):
            return self._not_configured()
        # Implementation placeholder
        return {"error": "not_implemented", "holdings": {}}

    def get_profile(self) -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented", "profile": None}

    def get_transactions(self, days: Optional[int] = None) -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented", "transactions": []}

    def get_dividends(self, days: Optional[int] = 365) -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented", "dividends": []}

    def get_performance(self, ticker: Optional[str] = None) -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented", "performance": {}}

    def record_buy(self, ticker: str, quantity: int, price: float, notes: str = "") -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented"}

    def record_sell(self, ticker: str, quantity: int, price: float, notes: str = "") -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented"}

    def record_dividend(self, ticker: str, amount: float, notes: str = "") -> Dict:
        if not (self.base_url and self.api_key):
            return self._not_configured()
        return {"error": "not_implemented"}
