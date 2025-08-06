"""
Database models for the Trading Bot GUI system
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
import json

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, VARCHAR
from pydantic import BaseModel

Base = declarative_base()

class JSONType(TypeDecorator):
    """SQLAlchemy type to handle JSON data"""
    impl = VARCHAR
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class BotStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting" 
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    BACKTESTING = "backtesting"

class BotInstance(Base):
    """Database model for bot instances"""
    __tablename__ = "bot_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    config_file = Column(String(255))
    status = Column(String(20), default=BotStatus.STOPPED)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Configuration
    initial_capital = Column(Float, default=100000.0)
    max_portfolio_risk = Column(Float, default=0.02)
    max_position_risk = Column(Float, default=0.01)
    strategy_weights = Column(JSONType)
    stock_universe = Column(JSONType)
    crypto_universe = Column(JSONType)
    
    # Runtime info
    process_id = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Performance summary
    current_equity = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    # Relationships
    trades = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="bot", cascade="all, delete-orphan")

class Trade(Base):
    """Database model for individual trades"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bot_instances.id"), nullable=False)
    
    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy/sell
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    
    # Timing
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    
    # Strategy info
    strategy_name = Column(String(50))
    confidence = Column(Float, default=0.5)
    
    # Results
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="open")  # open/closed/failed
    broker_order_id = Column(String(100), nullable=True)
    
    # Metadata
    is_halal = Column(Boolean, default=True)
    risk_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    bot = relationship("BotInstance", back_populates="trades")

class PerformanceLog(Base):
    """Database model for performance snapshots"""
    __tablename__ = "performance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bot_instances.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Portfolio metrics
    equity = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    daily_return = Column(Float, nullable=False)
    
    # Risk metrics
    portfolio_risk = Column(Float, nullable=False)
    var_95 = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=False)
    
    # Trade metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Performance ratios
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)
    
    # Additional metrics
    open_positions = Column(Integer, default=0)
    avg_trade_duration = Column(Float, nullable=True)  # in hours
    total_fees = Column(Float, default=0.0)
    
    # Relationships
    bot = relationship("BotInstance", back_populates="performance_logs")

# Pydantic models for API
class BotInstanceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config_file: Optional[str] = None
    initial_capital: float = 100000.0
    max_portfolio_risk: float = 0.02
    max_position_risk: float = 0.01
    strategy_weights: Optional[Dict[str, float]] = None
    stock_universe: Optional[list] = None
    crypto_universe: Optional[list] = None

class BotInstanceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: BotStatus
    created_at: datetime
    updated_at: datetime
    initial_capital: float
    current_equity: float
    total_return: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    last_heartbeat: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class TradeCreate(BaseModel):
    bot_id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    strategy_name: Optional[str] = None
    confidence: float = 0.5
    is_halal: bool = True

class TradeResponse(BaseModel):
    id: int
    bot_id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    strategy_name: Optional[str]
    pnl: Optional[float]
    pnl_pct: Optional[float]
    status: str
    is_halal: bool

    class Config:
        from_attributes = True

class PerformanceSnapshot(BaseModel):
    bot_id: int
    timestamp: datetime
    equity: float
    cash: float
    positions_value: float
    total_return: float
    daily_return: float
    portfolio_risk: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    sharpe_ratio: Optional[float]
    open_positions: int

    class Config:
        from_attributes = True

# Database setup
DATABASE_URL = "sqlite:///./trading_bots.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()