"""
Order blotter for recording all submitted orders and their statuses.

This class uses SQLite to persist order information.  Each order has a
timestamp, symbol, side, quantity, price at which it was submitted, and a
status field (e.g. ``"submitted"``, ``"filled"``, ``"rejected"``).
"""

from __future__ import annotations

import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime


class OrderBlotter:
    """Simple order blotter backed by SQLite."""

    def __init__(self, filename: str = "orders.db") -> None:
        self.conn = sqlite3.connect(filename)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                price REAL,
                status TEXT
            )
            """
        )
        self.conn.commit()

    def add_order(self, symbol: str, side: str, qty: float, price: float, status: str = "submitted") -> int:
        """Insert a new order and return its row id."""
        ts = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO orders (timestamp, symbol, side, qty, price, status) VALUES (?, ?, ?, ?, ?, ?)",
            (ts, symbol, side, qty, price, status),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_status(self, order_id: int, status: str) -> None:
        """Update the status of an existing order."""
        self.conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        self.conn.commit()

    def list_orders(self) -> Dict[int, Dict[str, Any]]:
        """Return all orders keyed by their id."""
        cur = self.conn.execute("SELECT id, timestamp, symbol, side, qty, price, status FROM orders")
        rows = cur.fetchall()
        orders: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            order_id, ts, symbol, side, qty, price, status = row
            orders[order_id] = {
                "timestamp": ts,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "status": status,
            }
        return orders