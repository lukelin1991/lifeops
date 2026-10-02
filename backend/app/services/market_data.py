"""
Market prices, fetched by the backend only (API keys never reach the
browser).

- Stocks:  Twelve Data   GET https://api.twelvedata.com/price
- Crypto:  CoinGecko     GET https://api.coingecko.com/api/v3/simple/price
           (Demo plan, key sent in the x-cg-demo-api-key header)

Rules:
- Every call has a timeout.
- Prices are cached in memory for MARKET_CACHE_TTL_SECONDS (default 60)
  so refreshing the dashboard doesn't burn the free-tier quota.
- Nothing here raises: a missing key or a failed call becomes a Quote
  with price=None and a price_status explaining why.
"""

import logging
import threading
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TWELVE_DATA_URL = "https://api.twelvedata.com"
COINGECKO_URL = "https://api.coingecko.com/api/v3"

# Common tickers -> CoinGecko coin ids. Anything else is looked up with
# CoinGecko's /search endpoint (and the answer is cached for a day).
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LTC": "litecoin",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "BNB": "binancecoin",
    "USDC": "usd-coin",
    "USDT": "tether",
    "ATOM": "cosmos",
    "XLM": "stellar",
    "SHIB": "shiba-inu",
}

ID_CACHE_SECONDS = 24 * 60 * 60


@dataclass
class PriceResult:
    symbol: str
    asset_type: str
    price: Decimal | None
    price_status: str
    source: str | None = None
    message: str | None = None


class TTLCache:
    """A tiny thread-safe dict with per-key expiry."""

    def __init__(self):
        self._data: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value, ttl_seconds: float) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


def _to_decimal(value) -> Decimal | None:
    try:
        price = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return price if price.is_finite() else None


class MarketDataService:
    def __init__(
        self,
        twelve_data_api_key: str = "",
        coingecko_api_key: str = "",
        cache_ttl_seconds: int = 60,
        timeout_seconds: float = 8,
        transport: httpx.BaseTransport | None = None,
        cache: TTLCache | None = None,
    ):
        self.twelve_data_api_key = twelve_data_api_key
        self.coingecko_api_key = coingecko_api_key
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        # `transport` lets tests swap in httpx.MockTransport (no network).
        self.transport = transport
        self.cache = cache or TTLCache()

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout_seconds,
            transport=self.transport,
        )

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def get_prices(
        self,
        assets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], PriceResult]:
        """
        assets: [(symbol, asset_type), ...]
        returns: {(symbol, asset_type): PriceResult}
        """
        stocks = sorted({s.upper() for s, t in assets if t == "stock"})
        cryptos = sorted({s.upper() for s, t in assets if t == "crypto"})

        results: dict[tuple[str, str], PriceResult] = {}

        for result in self._stock_prices(stocks):
            results[(result.symbol, "stock")] = result

        for result in self._crypto_prices(cryptos):
            results[(result.symbol, "crypto")] = result

        return results

    def get_price(self, symbol: str, asset_type: str) -> PriceResult:
        symbol = symbol.upper()
        return self.get_prices([(symbol, asset_type)])[(symbol, asset_type)]

    # -----------------------------------------------------
    # Stocks (Twelve Data)
    # -----------------------------------------------------

    def _stock_prices(self, symbols: list[str]) -> list[PriceResult]:
        if not symbols:
            return []

        if not self.twelve_data_api_key:
            return [
                PriceResult(
                    s, "stock", None, "missing_api_key",
                    message="Set TWELVE_DATA_API_KEY to load stock prices",
                )
                for s in symbols
            ]

        results = []
        to_fetch = []

        for symbol in symbols:
            cached = self.cache.get(f"stock:{symbol}")
            if cached is not None:
                results.append(
                    PriceResult(symbol, "stock", cached, "ok", "twelvedata")
                )
            else:
                to_fetch.append(symbol)

        if not to_fetch:
            return results

        try:
            with self._client() as client:
                response = client.get(
                    f"{TWELVE_DATA_URL}/price",
                    params={"symbol": ",".join(to_fetch)},
                    headers={
                        "Authorization": f"apikey {self.twelve_data_api_key}"
                    },
                )
            data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("Twelve Data request failed: %s", error)
            return results + [
                PriceResult(
                    s, "stock", None, "unavailable",
                    message="Stock price service unavailable",
                )
                for s in to_fetch
            ]

        if response.status_code >= 400:
            # e.g. 401 bad key, 429 out of credits: pass the reason along
            message = (
                data.get("message") if isinstance(data, dict) else None
            ) or f"Twelve Data returned HTTP {response.status_code}"
            logger.warning("Twelve Data error: %s", message)
            return results + [
                PriceResult(s, "stock", None, "unavailable", message=message)
                for s in to_fetch
            ]

        # One symbol -> {"price": "..."}
        # Several   -> {"AAPL": {"price": "..."}, "MSFT": {...}}
        # Errors    -> {"code": 404, "message": "...", "status": "error"}
        if len(to_fetch) == 1:
            entries = {to_fetch[0]: data}
        elif isinstance(data, dict) and data.get("status") == "error":
            entries = {s: data for s in to_fetch}
        else:
            entries = data if isinstance(data, dict) else {}

        for symbol in to_fetch:
            entry = entries.get(symbol)
            results.append(self._parse_twelve_data_entry(symbol, entry))

        return results

    def _parse_twelve_data_entry(self, symbol: str, entry) -> PriceResult:
        if isinstance(entry, dict) and "price" in entry:
            price = _to_decimal(entry["price"])
            if price is not None:
                self.cache.set(
                    f"stock:{symbol}", price, self.cache_ttl_seconds
                )
                return PriceResult(symbol, "stock", price, "ok", "twelvedata")

        if isinstance(entry, dict) and entry.get("status") == "error":
            status = (
                "not_found" if entry.get("code") in (400, 404)
                else "unavailable"
            )
            return PriceResult(
                symbol, "stock", None, status,
                message=entry.get("message"),
            )

        return PriceResult(
            symbol, "stock", None, "not_found",
            message="No price returned for this symbol",
        )

    # -----------------------------------------------------
    # Crypto (CoinGecko)
    # -----------------------------------------------------

    def _coingecko_headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "x-cg-demo-api-key": self.coingecko_api_key,
        }

    def _coingecko_id(self, client: httpx.Client, symbol: str) -> str | None:
        if symbol in COINGECKO_IDS:
            return COINGECKO_IDS[symbol]

        cached = self.cache.get(f"cgid:{symbol}")
        if cached is not None:
            return cached or None

        response = client.get(
            f"{COINGECKO_URL}/search",
            params={"query": symbol},
            headers=self._coingecko_headers(),
        )
        response.raise_for_status()

        # Results come back ordered by market cap rank, so the first
        # exact symbol match is almost always the coin people mean.
        coin_id = ""
        for coin in response.json().get("coins", []):
            if str(coin.get("symbol", "")).upper() == symbol:
                coin_id = coin.get("id", "")
                break

        self.cache.set(f"cgid:{symbol}", coin_id, ID_CACHE_SECONDS)
        return coin_id or None

    def _crypto_prices(self, symbols: list[str]) -> list[PriceResult]:
        if not symbols:
            return []

        if not self.coingecko_api_key:
            return [
                PriceResult(
                    s, "crypto", None, "missing_api_key",
                    message="Set COINGECKO_API_KEY to load crypto prices",
                )
                for s in symbols
            ]

        results = []
        to_fetch = []

        for symbol in symbols:
            cached = self.cache.get(f"crypto:{symbol}")
            if cached is not None:
                results.append(
                    PriceResult(symbol, "crypto", cached, "ok", "coingecko")
                )
            else:
                to_fetch.append(symbol)

        if not to_fetch:
            return results

        try:
            with self._client() as client:
                ids = {s: self._coingecko_id(client, s) for s in to_fetch}
                wanted = sorted({i for i in ids.values() if i})

                data = {}
                if wanted:
                    response = client.get(
                        f"{COINGECKO_URL}/simple/price",
                        params={"ids": ",".join(wanted), "vs_currencies": "usd"},
                        headers=self._coingecko_headers(),
                    )
                    response.raise_for_status()
                    data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("CoinGecko request failed: %s", error)
            return results + [
                PriceResult(
                    s, "crypto", None, "unavailable",
                    message="Crypto price service unavailable",
                )
                for s in to_fetch
            ]

        for symbol in to_fetch:
            coin_id = ids[symbol]
            price = None
            if coin_id and isinstance(data.get(coin_id), dict):
                price = _to_decimal(data[coin_id].get("usd"))

            if price is None:
                results.append(
                    PriceResult(
                        symbol, "crypto", None, "not_found",
                        message="CoinGecko has no USD price for this symbol",
                    )
                )
                continue

            self.cache.set(f"crypto:{symbol}", price, self.cache_ttl_seconds)
            results.append(
                PriceResult(symbol, "crypto", price, "ok", "coingecko")
            )

        return results


# One shared service (and cache) for the running app.
_market_data = MarketDataService(
    twelve_data_api_key=settings.twelve_data_api_key,
    coingecko_api_key=settings.coingecko_api_key,
    cache_ttl_seconds=settings.market_cache_ttl_seconds,
    timeout_seconds=settings.market_http_timeout_seconds,
)


def get_market_data() -> MarketDataService:
    """FastAPI dependency. Tests override this with a fake."""
    return _market_data
