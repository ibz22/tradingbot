"""
An event-driven backtesting engine for the halalbot trading system.

This implementation simulates trading over a pandas DataFrame of price data.  It
assumes a simple long-only strategy but can be extended for short selling by
changing the position accounting.  At each bar the engine calls a user
supplied strategy to generate a signal (``"buy"``, ``"sell"`` or ``"hold"``),
executes orders with a configurable slippage model and tracks the resulting
equity curve.  After running through all bars the engine computes common
performance metrics including total return, annualized return, Sharpe ratio,
Sortino ratio, Calmar ratio and maximum drawdown.

Example:

    >>> from halalbot.backtest.engine import BacktestEngine
    >>> engine = BacktestEngine(initial_capital=10000)
    >>> results = engine.run_backtest(price_df, my_strategy)
    >>> print(results["performance_metrics"])

The ``strategy`` object passed to ``run_backtest`` must implement a
``generate_signal`` method with signature ``generate_signal(data: pandas.DataFrame, index: int) -> str``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class Trade:
    """Represents an executed trade in the backtest order blotter."""

    timestamp: pd.Timestamp
    action: str  # "buy" or "sell"
    price: float
    quantity: float


class BacktestEngine:
    """A simple event-driven backtesting engine."""

    def __init__(
        self,
        initial_capital: float,
        slippage_pct: float = 0.0005,
        fee_per_trade: float = 0.0,
    ) -> None:
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.fee_per_trade = fee_per_trade

    def run_backtest(
        self, data: pd.DataFrame, strategy: Any
    ) -> Dict[str, Any]:
        """Simulate trading over ``data`` using ``strategy``.

        Parameters
        ----------
        data:
            A pandas DataFrame indexed by time with at least a ``close`` column.
        strategy:
            An object with a ``generate_signal(data, index)`` method returning
            "buy", "sell" or "hold" for each bar.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the initial and final equity, total number
            of trades, the order blotter and a nested performance_metrics dict.
        """
        if "close" not in data.columns:
            raise ValueError("price data must contain a 'close' column")
        capital = self.initial_capital
        position_size: float = 0.0  # number of units currently held
        equity_curve: List[float] = []
        blotter: List[Trade] = []
        # Precompute whether data index is datetime for metrics scaling
        is_datetime_index = isinstance(data.index, pd.DatetimeIndex)

        for i in range(len(data)):
            price = float(data["close"].iloc[i])
            signal = "hold"
            # Let the strategy decide what to do; catch errors to avoid halting the loop
            try:
                signal = strategy.generate_signal(data, i)
            except Exception:
                signal = "hold"
            # Execute orders
            if signal == "buy" and position_size == 0:
                # Determine how many units we can buy
                unit_price = price * (1 + self.slippage_pct)
                qty = (capital - self.fee_per_trade) / unit_price
                if qty > 0:
                    position_size = qty
                    capital -= qty * unit_price + self.fee_per_trade
                    blotter.append(
                        Trade(timestamp=data.index[i], action="buy", price=unit_price, quantity=qty)
                    )
            elif signal == "sell" and position_size > 0:
                unit_price = price * (1 - self.slippage_pct)
                capital += position_size * unit_price - self.fee_per_trade
                blotter.append(
                    Trade(timestamp=data.index[i], action="sell", price=unit_price, quantity=position_size)
                )
                position_size = 0.0
            # Update equity
            equity = capital + position_size * price
            equity_curve.append(equity)

        # Close any open position at the end
        if position_size > 0:
            price = float(data["close"].iloc[-1])
            unit_price = price * (1 - self.slippage_pct)
            capital += position_size * unit_price - self.fee_per_trade
            blotter.append(
                Trade(timestamp=data.index[-1], action="sell", price=unit_price, quantity=position_size)
            )
            position_size = 0.0
            equity_curve[-1] = capital

        # Compute performance metrics
        equity_array = np.array(equity_curve)
        total_return = (equity_array[-1] / self.initial_capital) - 1.0
        # Assume daily bars if datetime index; else use bar count as days
        n_periods = len(equity_array)
        if is_datetime_index:
            # approximate trading days based on number of rows; actual spacing may vary
            annual_factor = math.sqrt(252 / n_periods) if n_periods > 0 else 0
        else:
            annual_factor = math.sqrt(252 / n_periods) if n_periods > 0 else 0
        # Compute returns
        pct_changes = np.diff(equity_array) / equity_array[:-1]
        mean_ret = np.mean(pct_changes) if len(pct_changes) > 0 else 0.0
        std_ret = np.std(pct_changes) if len(pct_changes) > 0 else 0.0
        sharpe = (mean_ret / std_ret) * math.sqrt(252) if std_ret > 0 else 0.0
        # Sortino ratio: use downside deviation
        downside = pct_changes[pct_changes < 0]
        std_down = np.std(downside) if len(downside) > 0 else 0.0
        sortino = (mean_ret / std_down) * math.sqrt(252) if std_down > 0 else 0.0
        # Max drawdown
        running_max = np.maximum.accumulate(equity_array)
        drawdowns = (equity_array - running_max) / running_max
        max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        # Calmar ratio: annualized return / max drawdown
        ann_ret = ((equity_array[-1] / self.initial_capital) ** (252 / max(n_periods, 1))) - 1.0 if n_periods > 0 else 0.0
        calmar = ann_ret / max_drawdown if max_drawdown > 0 else 0.0

        performance_metrics = {
            "total_return": total_return,
            "annualized_return": ann_ret,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
        }

        return {
            "initial_capital": self.initial_capital,
            "final_equity": equity_array[-1] if len(equity_array) > 0 else self.initial_capital,
            "total_trades": len(blotter),
            "trades": [trade.__dict__ for trade in blotter],
            "equity_curve": equity_curve,
            "performance_metrics": performance_metrics,
        }
