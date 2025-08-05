"""
Simple script to run the halal trading bot in live (paper) mode.

This script loads configuration from ``config.yaml``, constructs the data
gateway, broker gateway, strategy and position store, then launches the
``TradingEngine`` in live mode.  To use the Alpaca paper API you must set
the environment variables ``ALPACA_API_KEY`` and ``ALPACA_SECRET_KEY``.
"""

import asyncio
import yaml

from halalbot.core.engine import TradingEngine
from halalbot.core.position_store_sqlite import SQLitePositionStore
from halalbot.gateway.broker_gateway import AlpacaBrokerGateway
from halalbot.screening.data_gateway import FMPGateway
from halalbot.strategies.momentum import MomentumStrategy


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


async def main() -> None:
    config = load_config()
    # Set up gateways and strategy
    data_gateway = FMPGateway(api_key=config.get("fmp_api_key", "demo"))
    broker_gateway = AlpacaBrokerGateway()  # requires API keys in env vars
    strategy = MomentumStrategy()
    # Create engine
    engine = TradingEngine(
        config=config,
        strategy=strategy,
        data_gateway=data_gateway,
        broker_gateway=broker_gateway,
    )
    # Use SQLite for position storage
    engine.position_store = SQLitePositionStore(config.get("position_db", "positions.db"))
    await engine.run_live()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass