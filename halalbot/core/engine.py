"""
TradingEngine coordinates the various subsystems of the trading bot.  It is
responsible for orchestrating the data acquisition, running the halal
screening, generating orders via strategies, executing orders through a
gateway and monitoring open positions.  For simplicity this implementation
provides a synchronous backtest runner and stubs for live trading.

The engine exposes two main entry points:

``run_backtest``:  Accepts a pandas DataFrame of historical price data and a
    strategy instance.  It passes the data to the backtesting engine and
    returns a performance report.

``run_live``:  An asynchronous coroutine that continually polls for new market
    data, evaluates screening criteria and risk, generates orders and updates
    positions.  Only a skeleton implementation is provided here.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pandas as pd

from .position_store import PositionStore
from .risk import RiskManager
from ..backtest.engine import BacktestEngine
from ..screening.data_gateway import FMPGateway, DataGateway
from ..screening.halal_rules import load_rules
from ..screening.advanced_screener import AdvancedHalalScreener


class TradingEngine:
    """Top level orchestrator for the halalbot trading system."""

    def __init__(
        self,
        config: Dict[str, Any],
        strategy: Any,
        data_gateway: DataGateway | None = None,
    ) -> None:
        # Configuration dictionary loaded from YAML
        self.config = config
        self.strategy = strategy
        # Use provided gateway or default to FMPGateway with API key from env
        api_key = config.get("fmp_api_key", "demo")
        self.data_gateway: DataGateway = data_gateway or FMPGateway(api_key)
        # Persisted positions across sessions
        self.position_store = PositionStore(config.get("position_file", "positions.json"))
        # Simple risk manager
        self.risk_manager = RiskManager(
            max_portfolio_risk=config.get("max_portfolio_risk", 0.02),
            max_position_risk=config.get("max_position_risk", 0.01),
            max_position_pct=config.get("max_position_pct", 0.1),
        )
        # Backtest engine
        self.backtester = BacktestEngine(config.get("initial_capital", 100000))
        # Load halal rules for crypto screening
        self.rules = load_rules(config.get("config_path", "config.yaml"))

        # Financial screener using real statements and thresholds
        # Thresholds (max interest income percentage and debt ratio) are read
        # from the configuration.  If not present, sensible defaults are used.
        self.screener = AdvancedHalalScreener(
            self.data_gateway,
            {
                "max_interest_pct": config.get("max_interest_pct", 0.05),
                "max_debt_ratio": config.get("max_debt_ratio", 0.33),
            },
        )

    def run_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run a synchronous backtest on the provided price data."""
        return self.backtester.run_backtest(data, self.strategy)

    async def run_live(self) -> None:
        """Run the engine in live trading mode (skeleton implementation)."""
        while True:
            # TODO: fetch latest market data via broker/data gateway
            await asyncio.sleep(60)
            # TODO: evaluate open positions using self.position_store and strategy.should_exit
            # TODO: screen universe for new opportunities using halal rules and data gateway
            # TODO: calculate risk-adjusted order sizes with self.risk_manager
            # TODO: send orders via broker gateway and record them in position_store
            # This loop is intentionally minimal; production bots would integrate
            # real-time data feeds, order execution and error handling here.
            pass