import time
from typing import Dict, Any
import httpx

# In-memory cache for live exchange rates
_RATE_CACHE: Dict[str, Any] = {
    "rates": {
        "INR": 1.0,
        "USD": 0.0119,
        "EUR": 0.0111,
        "GBP": 0.0094,
        "AED": 0.0437,
        "CAD": 0.0164,
        "AUD": 0.0182,
        "SGD": 0.0160,
        "JPY": 1.83,
    },
    "last_fetched": 0,
    "base": "INR",
}

CACHE_TTL_SECONDS = 3600  # 1 hour cache

class CurrencyService:
    @staticmethod
    async def get_exchange_rates() -> Dict[str, Any]:
        """
        Fetches latest currency exchange rates with base INR (₹)
        using free public exchange rate APIs with in-memory caching.
        """
        now = time.time()
        if now - _RATE_CACHE["last_fetched"] < CACHE_TTL_SECONDS and _RATE_CACHE["rates"]:
            return {
                "base": "INR",
                "rates": _RATE_CACHE["rates"],
                "cached": True,
                "symbols": {
                    "INR": "₹",
                    "USD": "$",
                    "EUR": "€",
                    "GBP": "£",
                    "AED": "AED",
                    "CAD": "CA$",
                    "AUD": "A$",
                    "SGD": "S$",
                    "JPY": "¥",
                }
            }

        # Query free public exchange rate API
        api_endpoints = [
            "https://open.er-api.com/v6/latest/INR",
            "https://api.exchangerate-api.com/v4/latest/INR",
        ]

        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in api_endpoints:
                try:
                    res = await client.get(endpoint)
                    if res.status_code == 200:
                        data = res.json()
                        rates = data.get("rates", {})
                        if rates and "USD" in rates:
                            _RATE_CACHE["rates"] = {
                                "INR": 1.0,
                                "USD": round(rates.get("USD", 0.0119), 5),
                                "EUR": round(rates.get("EUR", 0.0111), 5),
                                "GBP": round(rates.get("GBP", 0.0094), 5),
                                "AED": round(rates.get("AED", 0.0437), 5),
                                "CAD": round(rates.get("CAD", 0.0164), 5),
                                "AUD": round(rates.get("AUD", 0.0182), 5),
                                "SGD": round(rates.get("SGD", 0.0160), 5),
                                "JPY": round(rates.get("JPY", 1.83), 3),
                            }
                            _RATE_CACHE["last_fetched"] = now
                            break
                except Exception:
                    continue

        return {
            "base": "INR",
            "rates": _RATE_CACHE["rates"],
            "cached": False,
            "symbols": {
                "INR": "₹",
                "USD": "$",
                "EUR": "€",
                "GBP": "£",
                "AED": "AED",
                "CAD": "CA$",
                "AUD": "A$",
                "SGD": "S$",
                "JPY": "¥",
            }
        }

    @staticmethod
    def convert_from_inr(amount_inr: float, target_currency: str = "USD") -> float:
        rate = _RATE_CACHE["rates"].get(target_currency.upper(), 1.0)
        return round(amount_inr * rate, 2)
