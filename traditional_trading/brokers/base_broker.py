"""
Base Broker Interface
====================

Abstract base class for all broker integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Order:
    """Order representation"""
    symbol: str
    quantity: Decimal
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market', 'limit', 'stop'
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = 'day'  # 'day', 'gtc', 'ioc', 'fok'
    order_id: Optional[str] = None
    status: str = 'pending'
    filled_quantity: Decimal = Decimal('0')
    average_price: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Position:
    """Position representation"""
    symbol: str
    quantity: Decimal
    average_price: Decimal
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None


@dataclass
class AccountInfo:
    """Account information"""
    account_id: str
    buying_power: Decimal
    cash: Decimal
    portfolio_value: Decimal
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: datetime
    currency: str = 'USD'


class BaseBroker(ABC):
    """Abstract base class for broker integrations"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.is_paper = True  # Default to paper trading
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close broker connection"""
        pass
    
    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all current positions"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_orders(self, status: str = 'open') -> List[Order]:
        """Get orders by status"""
        pass
    
    @abstractmethod
    async def get_market_hours(self, symbol: str) -> Dict[str, Any]:
        """Get market hours for symbol"""
        pass
    
    @abstractmethod
    async def is_market_open(self) -> bool:
        """Check if market is currently open"""
        pass
    
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Decimal:
        """Get latest price for symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = '1Day'
    ) -> Dict[str, Any]:
        """Get historical price data"""
        pass