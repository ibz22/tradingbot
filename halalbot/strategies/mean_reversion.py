"""
A basic mean reversion trading strategy.

This strategy measures how far the current price deviates from a moving
average and issues a ``"buy"`` signal when the price is sufficiently below
the average (anticipating a reversion upwards), and a ``"sell"`` signal when
the price is sufficiently above the average.  The threshold is expressed in
standard deviations of the past price series.
"""

from __future__ import annotations

import pandas as pd


class MeanReversionStrategy:
    """Mean reversion strategy using z‑score thresholds."""

    def __init__(
        self, lookback: int = 20, entry_z: float = 1.0, exit_z: float = 0.5
    ) -> None:
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.position = 0  # internal state: -1 for short, 1 for long

    def generate_signal(self, data: pd.DataFrame, index: int) -> str:
        """Generate a trading signal based on z‑score of price deviation."""
        if index < self.lookback:
            return "hold"
        window = data["close"].iloc[index - self.lookback : index]
        mean = window.mean()
        std = window.std()
        if std == 0:
            return "hold"
        price = data["close"].iloc[index]
        z_score = (price - mean) / std
        # Entry conditions
        if self.position == 0:
            if z_score > self.entry_z:
                self.position = -1
                return "sell"
            elif z_score < -self.entry_z:
                self.position = 1
                return "buy"
        # Exit conditions
        else:
            if abs(z_score) < self.exit_z:
                sig = "sell" if self.position > 0 else "buy"
                self.position = 0
                return sig
        return "hold"