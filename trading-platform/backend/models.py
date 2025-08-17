"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    SOLANA = "Solana"
    STOCKS = "Stocks"


class Strategy(str, Enum):
    MOMENTUM = "Momentum"
    GRID = "Grid"
    MEAN_REVERSION = "Mean Reversion"


class Timeframe(str, Enum):
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"


class BotStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class BotMode(str, Enum):
    PAPER = "Paper"
    LIVE = "Live"


class BotAction(str, Enum):
    START = "start"
    PAUSE = "pause"
    STOP = "stop"


# Request models
class BotConfigRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    asset_type: AssetType = Field(..., alias="assetType")
    market: str = Field(..., min_length=1, max_length=20)
    strategy: Strategy
    timeframe: Timeframe
    paper_trading: bool = Field(True, alias="paperTrading")
    connect_api: bool = Field(False, alias="connectApi")
    initial_balance: float = Field(..., ge=100, le=1000000, alias="initialBalance")


class BotControlRequest(BaseModel):
    action: BotAction


# Response models
class BotResponse(BaseModel):
    id: str
    name: str
    strategy: str
    type: AssetType
    market: str
    mode: BotMode
    is_connected: bool = Field(alias="isConnected")
    runtime: str
    daily_pnl: float = Field(alias="dailyPnl")
    status: BotStatus
    created_at: str = Field(alias="createdAt")


class PortfolioStats(BaseModel):
    total_value: float = Field(alias="totalValue")
    pnl: float
    pnl_percent: float = Field(alias="pnlPercent")
    active_bots: int = Field(alias="activeBots")
    new_bots: int = Field(alias="newBots")
    win_rate: int = Field(alias="winRate")
    total_trades: int = Field(alias="totalTrades")
    volume_24h: float = Field(alias="volume24h")
    sharpe_ratio: float = Field(alias="sharpeRatio")


class PortfolioDataPoint(BaseModel):
    timestamp: str
    value: float
    pnl: float


class ApiResponse(BaseModel):
    data: Any
    success: bool
    message: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]


class PriceData(BaseModel):
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: str