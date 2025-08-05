"""
SQLite-backed position store for recording open trades.

This class provides the same interface as ``PositionStore`` but persists
positions in a SQLite database instead of an in‑memory dictionary/JSON file.
It supports adding, closing and listing positions.  Each position is
identified by its symbol; adding a position with an existing symbol will
overwrite the previous entry.
"""

from __future__ import annotations

import sqlite3
from typing import Dict, Any


class SQLitePositionStore:
    """Persist open positions in a SQLite database."""

    def __init__(self, filename: str = "positions.db") -> None:
        self.conn = sqlite3.connect(filename)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                side TEXT,
                qty REAL,
                entry_price REAL,
                stop REAL,
                target REAL,
                strategy_tag TEXT
            )
            """
        )
        self.conn.commit()

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
        """Insert or replace a position in the database."""
        self.conn.execute(
            """
            INSERT INTO positions (symbol, side, qty, entry_price, stop, target, strategy_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                side=excluded.side,
                qty=excluded.qty,
                entry_price=excluded.entry_price,
                stop=excluded.stop,
                target=excluded.target,
                strategy_tag=excluded.strategy_tag
            """,
            (symbol, side, qty, entry_price, stop, target, tag),
        )
        self.conn.commit()

    def close_position(self, symbol: str) -> None:
        """Delete a position from the database."""
        self.conn.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
        self.conn.commit()

    def get_open_positions(self) -> Dict[str, Dict[str, Any]]:
        """Return all open positions as a dict keyed by symbol."""
        cur = self.conn.execute("SELECT symbol, side, qty, entry_price, stop, target, strategy_tag FROM positions")
        rows = cur.fetchall()
        positions: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            symbol, side, qty, entry_price, stop, target, tag = row
            positions[symbol] = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "entry_price": entry_price,
                "stop": stop,
                "target": target,
                "strategy_tag": tag,
            }
        return positions
