"""
Database configuration and models
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "solsak.db")


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    async def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()
    
    async def execute_one(self, query: str, params: tuple = ()):
        """Execute a query and return one result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()


# Global database instance
db = Database()


async def init_db():
    """Initialize database tables"""
    
    # Bots table
    await db.execute_query("""
        CREATE TABLE IF NOT EXISTS bots (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            market TEXT NOT NULL,
            strategy TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            paper_trading BOOLEAN NOT NULL,
            connect_api BOOLEAN NOT NULL,
            initial_balance REAL NOT NULL,
            current_balance REAL,
            status TEXT DEFAULT 'stopped',
            daily_pnl REAL DEFAULT 0.0,
            total_pnl REAL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            config_json TEXT,
            runtime_seconds INTEGER DEFAULT 0
        )
    """)
    
    # Portfolio history table
    await db.execute_query("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_value REAL NOT NULL,
            pnl REAL NOT NULL,
            pnl_percent REAL NOT NULL,
            active_bots INTEGER NOT NULL
        )
    """)
    
    # Trades table
    await db.execute_query("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total_value REAL NOT NULL,
            pnl REAL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (bot_id) REFERENCES bots (id)
        )
    """)
    
    # Settings table
    await db.execute_query("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    logger.info("Database initialized successfully")


async def get_db():
    """Dependency to get database instance"""
    return db


class BotRepository:
    """Bot database operations"""
    
    @staticmethod
    async def create_bot(bot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new bot"""
        await db.execute_query("""
            INSERT INTO bots (
                id, name, asset_type, market, strategy, timeframe,
                paper_trading, connect_api, initial_balance, current_balance,
                created_at, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bot_data["id"],
            bot_data["name"],
            bot_data["asset_type"],
            bot_data["market"],
            bot_data["strategy"],
            bot_data["timeframe"],
            bot_data["paper_trading"],
            bot_data["connect_api"],
            bot_data["initial_balance"],
            bot_data["initial_balance"],  # current_balance starts equal
            bot_data["created_at"],
            json.dumps(bot_data.get("config", {}))
        ))
        
        return bot_data
    
    @staticmethod
    async def get_bot(bot_id: str) -> Optional[Dict[str, Any]]:
        """Get bot by ID"""
        result = await db.execute_one(
            "SELECT * FROM bots WHERE id = ?", (bot_id,)
        )
        return dict(result) if result else None
    
    @staticmethod
    async def get_all_bots() -> List[Dict[str, Any]]:
        """Get all bots"""
        results = await db.execute_query("SELECT * FROM bots ORDER BY created_at DESC")
        return [dict(row) for row in results]
    
    @staticmethod
    async def update_bot(bot_id: str, updates: Dict[str, Any]) -> bool:
        """Update bot data"""
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE bots SET {set_clause}, updated_at = ? WHERE id = ?"
        
        params = list(updates.values()) + [datetime.now().isoformat(), bot_id]
        
        await db.execute_query(query, tuple(params))
        return True
    
    @staticmethod
    async def delete_bot(bot_id: str) -> bool:
        """Delete bot"""
        await db.execute_query("DELETE FROM bots WHERE id = ?", (bot_id,))
        return True
    
    @staticmethod
    async def update_bot_pnl(bot_id: str, daily_pnl: float, total_pnl: float):
        """Update bot P&L"""
        await db.execute_query("""
            UPDATE bots SET daily_pnl = ?, total_pnl = ?, updated_at = ?
            WHERE id = ?
        """, (daily_pnl, total_pnl, datetime.now().isoformat(), bot_id))


class PortfolioRepository:
    """Portfolio database operations"""
    
    @staticmethod
    async def add_history_point(data: Dict[str, Any]):
        """Add portfolio history point"""
        await db.execute_query("""
            INSERT INTO portfolio_history (
                timestamp, total_value, pnl, pnl_percent, active_bots
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data["timestamp"],
            data["total_value"],
            data["pnl"],
            data["pnl_percent"],
            data["active_bots"]
        ))
    
    @staticmethod
    async def get_history(days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio history"""
        results = await db.execute_query("""
            SELECT * FROM portfolio_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (days * 24,))  # Assuming hourly data points
        
        return [dict(row) for row in results]


class TradeRepository:
    """Trade database operations"""
    
    @staticmethod
    async def record_trade(trade_data: Dict[str, Any]):
        """Record a trade"""
        await db.execute_query("""
            INSERT INTO trades (
                bot_id, symbol, side, quantity, price, total_value, pnl, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data["bot_id"],
            trade_data["symbol"],
            trade_data["side"],
            trade_data["quantity"],
            trade_data["price"],
            trade_data["total_value"],
            trade_data.get("pnl", 0),
            trade_data["timestamp"]
        ))
    
    @staticmethod
    async def get_trades(bot_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades, optionally filtered by bot"""
        if bot_id:
            results = await db.execute_query("""
                SELECT * FROM trades WHERE bot_id = ? 
                ORDER BY timestamp DESC LIMIT ?
            """, (bot_id, limit))
        else:
            results = await db.execute_query("""
                SELECT * FROM trades 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in results]