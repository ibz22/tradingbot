"""
Simple broker gateway for paper trading using Alpaca.

This gateway demonstrates how you could wrap a broker API to place orders and
query account information.  It uses the `alpaca-py` SDK to send
market orders to Alpaca’s paper trading endpoint.  To use this class you
need to set the environment variables ``ALPACA_API_KEY`` and
``ALPACA_SECRET_KEY`` or pass them explicitly when constructing the gateway.

Example
-------
    from halalbot.gateway.broker_gateway import AlpacaBrokerGateway

    broker = AlpacaBrokerGateway()
    await broker.place_order("AAPL", "buy", 10)
    equity = await broker.get_account_value()
    print(equity)
"""

from __future__ import annotations

import os
from typing import Optional

import aiohttp


class AlpacaBrokerGateway:
    """Asynchronous broker gateway for Alpaca paper trading."""

    BASE_URL = "https://paper-api.alpaca.markets"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_SECRET_KEY")
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials are required")

    async def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }
        url = f"{self.BASE_URL}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=json, timeout=15) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_account_value(self) -> float:
        """Return the current equity in the Alpaca account."""
        data = await self._request("GET", "/v2/account")
        return float(data.get("equity", 0.0))

    async def place_order(self, symbol: str, side: str, qty: float, order_type: str = "market", time_in_force: str = "day") -> dict:
        """Place a market order and return the order response."""
        order = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        return await self._request("POST", "/v2/orders", json=order)