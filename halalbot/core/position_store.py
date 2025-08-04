"""
PositionStore implements a very lightweight mechanism for persisting open
positions between sessions.  It writes the current positions to a JSON file
and can reload them on startup.  Each position entry contains the symbol,
side, quantity, entry price, stop loss, target price and a user provided tag
identifying the strategy that opened the trade.

This class is intentionally simple: it does not handle concurrent writes or
sophisticated auditing.  For production usage you may want to replace it with
a database-backed implementation (e.g. SQLite or Redis).
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any


class PositionStore:
    """Persist open positions to a JSON file and reload them at runtime."""

    def __init__(self, filename: str = "positions.json") -> None:
        self.filename = filename
        self.positions: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load positions from disk if the file exists."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.positions = json.load(f)
            except Exception:
                # If the file is corrupted or unreadable start fresh
                self.positions = {}

    def _save(self) -> None:
        """Save the current positions to disk."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.positions, f, indent=2)
        except Exception:
            # errors are intentionally swallowed to avoid bringing down the bot
            pass

    def add_position(
        self,
        symbol: str,
        side: str,
        qty: float,
        entry_price: float,
        stop: float,
        target: float,
        tag: str,
    ) -> None:
        """Record a newly opened position and persist it to disk."""
        self.positions[symbol] = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry_price": entry_price,
            "stop": stop,
            "target": target,
            "strategy_tag": tag,
        }
        self._save()

    def close_position(self, symbol: str) -> None:
        """Remove a position from the store when it has been closed."""
        if symbol in self.positions:
            del self.positions[symbol]
            self._save()

    def get_open_positions(self) -> Dict[str, Dict[str, Any]]:
        """Return a dictionary of all currently open positions."""
        return self.positions
