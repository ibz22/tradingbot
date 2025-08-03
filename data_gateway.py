import asyncio
import json
import sqlite3
import time
from typing import Any, Dict, Optional

import aiohttp


class DataGateway:
    """Abstract gateway for financial data providers."""

    async def get_statement(self, ticker: str) -> Dict[str, Any]:
        """Return combined financial statements for the given ticker."""
        raise NotImplementedError


class FMPGateway(DataGateway):
    """Financial Modeling Prep data gateway with basic caching and rate limiting."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: str, cache_db: str = "fmp_cache.db", cache_expiry: int = 60 * 60 * 24,
                 max_per_second: int = 5):
        self.api_key = api_key
        self.cache_expiry = cache_expiry
        self.max_per_second = max_per_second
        self._last_request: float = 0.0
        self._rate_lock = asyncio.Lock()
        self._conn = sqlite3.connect(cache_db)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, fetched REAL)"
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    async def _rate_limited_get(self, url: str) -> Any:
        async with self._rate_lock:
            elapsed = time.time() - self._last_request
            wait = max(0.0, 1.0 / self.max_per_second - elapsed)
            if wait:
                await asyncio.sleep(wait)
            self._last_request = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                resp.raise_for_status()
                return await resp.json()

    # ------------------------------------------------------------------
    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute("SELECT value, fetched FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            value, fetched = row
            if time.time() - fetched < self.cache_expiry:
                return json.loads(value)
        return None

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self._conn.execute(
            "REPLACE INTO cache (key, value, fetched) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    async def get_statement(self, ticker: str) -> Dict[str, Any]:
        key = f"statement:{ticker}"
        cached = self._get_cache(key)
        if cached:
            return cached

        income_url = f"{self.BASE_URL}/income-statement/{ticker}?limit=1&apikey={self.api_key}"
        balance_url = f"{self.BASE_URL}/balance-sheet-statement/{ticker}?limit=1&apikey={self.api_key}"

        income_data, balance_data = await asyncio.gather(
            self._rate_limited_get(income_url),
            self._rate_limited_get(balance_url),
        )

        if not income_data or not balance_data:
            return {}

        combined = {**income_data[0], **balance_data[0]}
        self._set_cache(key, combined)
        return combined
