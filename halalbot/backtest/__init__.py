"""
Backtesting utilities for the halalbot trading system.

The backtest subpackage includes an event-driven simulation engine capable of
running trading strategies over historical price data.  It is designed to
iterate through each bar of data, generate signals from the strategy and
simulate fills with slippage and transaction costs.  The resulting equity
curve and performance metrics provide a realistic view of how a strategy
would have behaved historically.
"""

from .engine import BacktestEngine  # noqa: F401
