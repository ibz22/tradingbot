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
        """Run the engine in live trading mode.

        This loop periodically re‑evaluates open positions and scans the
        configured stock universe for new opportunities.  For each open
        position, if the strategy provides a ``should_exit`` method and it
        returns ``True``, the position will be closed.  For each ticker in
        the universe, if it passes the halal financial screen and the strategy
        indicates a ``buy`` signal, an order size is calculated via the
        risk manager and the position is recorded in the position store.  The
        actual order execution via a broker API is left to the user to
        implement.
        """
        poll_interval = self.config.get("poll_interval_seconds", 300)
        stock_universe = self.config.get("stock_universe", [])
        while True:
            # Evaluate existing positions
            await self._evaluate_positions()
            # Scan for new opportunities
            await self._screen_universe(stock_universe)
            await asyncio.sleep(poll_interval)

    # ------------------------------------------------------------------
    async def _evaluate_positions(self) -> None:
        """Check open positions and close them if the strategy signals an exit."""
        positions = self.position_store.get_open_positions()
        for symbol, pos in list(positions.items()):
            # Only proceed if the strategy defines a should_exit method
            if hasattr(self.strategy, "should_exit"):
                try:
                    should_exit = self.strategy.should_exit(pos, None)
                except Exception:
                    should_exit = False
                if should_exit:
                    # In a real implementation you would execute a sell order via broker
                    # and update the position store accordingly
                    self.position_store.close_position(symbol)

    # ------------------------------------------------------------------
    async def _screen_universe(self, universe: list[str]) -> None:
        """Screen tickers and open new positions when appropriate."""
        for ticker in universe:
            # Skip if we already hold this ticker
            if ticker in self.position_store.get_open_positions():
                continue
            # Check if ticker passes the halal screen
            try:
                is_halal = await self.screener.is_halal(ticker)
            except Exception:
                is_halal = False
            if not is_halal:
                continue
            # Ask the strategy for a buy/sell/hold signal; we need the latest price
            price = await self._get_latest_price(ticker)
            if price is None:
                continue
            # For simplicity, we call generate_signal with ``None`` data and index 0.
            # In a real bot you would supply a DataFrame of recent bars to the strategy.
            try:
                signal = self.strategy.generate_signal(None, 0)  # type: ignore[arg-type]
            except Exception:
                signal = "hold"
            if signal != "buy":
                continue
            # Calculate order size (units) using risk manager and actual price
            qty = self.risk_manager.calculate_position_size(
                account_value=self.config.get("initial_capital", 100000),
                current_price=price,
                stop_price=None,
            )
            if qty <= 0:
                continue
            # Record position; normally you would send a buy order via broker here
            self.position_store.add_position(
                symbol=ticker,
                side="long",
                qty=qty,
                entry_price=price,
                stop=0.0,
                target=0.0,
                tag=self.strategy.__class__.__name__,
            )

    # ------------------------------------------------------------------
    async def _get_latest_price(self, ticker: str) -> float | None:
        """Fetch the latest price for ``ticker`` using Financial Modeling Prep."""
        api_key = self.config.get("fmp_api_key", "demo")
        url = f"https://financialmodelingprep.com/api/v3/quote-short/{ticker}?apikey={api_key}"
        import aiohttp  # imported here to avoid making aiohttp a strict dependency for backtesting
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            if data:
                return float(data[0].get("price", 0))
        except Exception:
            return None
        return None