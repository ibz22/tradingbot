"""
A simple momentum based trading strategy.

This strategy compares the current price to a moving average calculated over a
lookback window.  If the price is above the moving average it returns a
``"buy"`` signal, if it is below the moving average it returns a ``"sell"``
signal, otherwise it returns ``"hold"``.  The moving average is calculated
over the closing prices in the supplied data.
"""

from __future__ import annotations

import pandas as pd


class MomentumStrategy:
    """Momentum trading strategy using a simple moving average crossover."""

    def __init__(self, lookback: int = 20) -> None:
        self.lookback = lookback

    def generate_signal(self, data: pd.DataFrame, index: int) -> str:
        """Generate trading signal for a given row of data.

        Parameters
        ----------
        data:
            Price history with a ``close`` column.
        index:
            Current row index within ``data``.

        Returns
        -------
        str
            One of ``"buy"``, ``"sell"`` or ``"hold"``.
        """
        if index < self.lookback:
            return "hold"
        window = data["close"].iloc[index - self.lookback : index]
        if len(window) < self.lookback:
            return "hold"
        ma = window.mean()
        price = data["close"].iloc[index]
        if price > ma:
            return "buy"
        elif price < ma:
            return "sell"
        return "hold"