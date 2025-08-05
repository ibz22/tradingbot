"""
Core components of the halalbot trading system.

This subpackage contains the primary engine that ties together the various
components, a simple risk manager and a persistent position store.  The
``TradingEngine`` class provides an asynchronous event loop for live trading
and a synchronous wrapper for backtesting.  Risk management and position
storage are factored out into their own classes to make the system easier to
test and extend.

Enhanced with comprehensive order management and execution tracking.
"""

from .engine import TradingEngine  # noqa: F401
from .risk import RiskManager  # noqa: F401
from .position_store import PositionStore  # noqa: F401
from .order_manager import OrderManager, EnhancedOrder, OrderStatus  # noqa: F401
from .trade_executor import EnhancedTradeExecutor, ExecutionResult  # noqa: F401
