"""
Alpaca Markets Broker Integration
=================================

Complete integration with Alpaca Markets for stock trading.
Supports both paper and live trading modes.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import json

from .base_broker import BaseBroker, Order, Position, AccountInfo

logger = logging.getLogger(__name__)


class AlpacaBroker(BaseBroker):
    """Alpaca Markets broker implementation"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        paper: bool = True
    ):
        """
        Initialize Alpaca broker connection
        
        Args:
            api_key: Alpaca API key (defaults to env ALPACA_API_KEY)
            api_secret: Alpaca API secret (defaults to env ALPACA_SECRET_KEY)
            base_url: Override base URL (defaults to paper/live based on paper flag)
            paper: Use paper trading (default True)
        """
        api_key = api_key or os.getenv('ALPACA_API_KEY')
        api_secret = api_secret or os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not api_secret:
            raise ValueError("Alpaca API credentials required")
        
        if base_url is None:
            base_url = (
                "https://paper-api.alpaca.markets" if paper
                else "https://api.alpaca.markets"
            )
        
        super().__init__(api_key, api_secret, base_url)
        self.is_paper = paper
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        
    async def connect(self) -> bool:
        """Establish connection to Alpaca"""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession(headers=self.headers)
            
            # Test connection by getting account info
            account = await self.get_account()
            logger.info(f"Connected to Alpaca ({'paper' if self.is_paper else 'live'} mode)")
            logger.info(f"Account ID: {account.account_id}, Buying Power: ${account.buying_power}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            return False
    
    async def disconnect(self):
        """Close Alpaca connection"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from Alpaca")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request to Alpaca"""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}{endpoint}"
        
        async with self.session.request(method, url, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Alpaca API error ({response.status}): {error_text}")
    
    async def get_account(self) -> AccountInfo:
        """Get account information"""
        data = await self._request('GET', '/v2/account')
        
        return AccountInfo(
            account_id=data['id'],
            buying_power=Decimal(data['buying_power']),
            cash=Decimal(data['cash']),
            portfolio_value=Decimal(data['portfolio_value']),
            pattern_day_trader=data.get('pattern_day_trader', False),
            trading_blocked=data.get('trading_blocked', False),
            transfers_blocked=data.get('transfers_blocked', False),
            account_blocked=data.get('account_blocked', False),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            currency=data.get('currency', 'USD')
        )
    
    async def get_positions(self) -> List[Position]:
        """Get all current positions"""
        positions_data = await self._request('GET', '/v2/positions')
        
        positions = []
        for pos in positions_data:
            positions.append(Position(
                symbol=pos['symbol'],
                quantity=Decimal(pos['qty']),
                average_price=Decimal(pos['avg_entry_price']),
                current_price=Decimal(pos.get('current_price', 0)) if pos.get('current_price') else None,
                market_value=Decimal(pos.get('market_value', 0)) if pos.get('market_value') else None,
                unrealized_pnl=Decimal(pos.get('unrealized_pl', 0)) if pos.get('unrealized_pl') else None,
                realized_pnl=Decimal(pos.get('realized_pl', 0)) if pos.get('realized_pl') else None,
                cost_basis=Decimal(pos['cost_basis'])
            ))
        
        return positions
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        try:
            pos = await self._request('GET', f'/v2/positions/{symbol}')
            
            return Position(
                symbol=pos['symbol'],
                quantity=Decimal(pos['qty']),
                average_price=Decimal(pos['avg_entry_price']),
                current_price=Decimal(pos.get('current_price', 0)) if pos.get('current_price') else None,
                market_value=Decimal(pos.get('market_value', 0)) if pos.get('market_value') else None,
                unrealized_pnl=Decimal(pos.get('unrealized_pl', 0)) if pos.get('unrealized_pl') else None,
                realized_pnl=Decimal(pos.get('realized_pl', 0)) if pos.get('realized_pl') else None,
                cost_basis=Decimal(pos['cost_basis'])
            )
        except Exception:
            return None
    
    async def place_order(self, order: Order) -> Order:
        """Place an order"""
        order_data = {
            'symbol': order.symbol,
            'qty': str(order.quantity),
            'side': order.side,
            'type': order.order_type,
            'time_in_force': order.time_in_force
        }
        
        if order.limit_price:
            order_data['limit_price'] = str(order.limit_price)
        if order.stop_price:
            order_data['stop_price'] = str(order.stop_price)
        
        result = await self._request('POST', '/v2/orders', json=order_data)
        
        order.order_id = result['id']
        order.status = result['status']
        order.created_at = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
        order.updated_at = datetime.fromisoformat(result['updated_at'].replace('Z', '+00:00'))
        
        if result.get('filled_qty'):
            order.filled_quantity = Decimal(result['filled_qty'])
        if result.get('filled_avg_price'):
            order.average_price = Decimal(result['filled_avg_price'])
        
        logger.info(f"Order placed: {order.order_id} - {order.symbol} {order.side} {order.quantity}")
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            await self._request('DELETE', f'/v2/orders/{order_id}')
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        try:
            result = await self._request('GET', f'/v2/orders/{order_id}')
            
            order = Order(
                symbol=result['symbol'],
                quantity=Decimal(result['qty']),
                side=result['side'],
                order_type=result['order_type'],
                time_in_force=result['time_in_force'],
                order_id=result['id'],
                status=result['status']
            )
            
            if result.get('limit_price'):
                order.limit_price = Decimal(result['limit_price'])
            if result.get('stop_price'):
                order.stop_price = Decimal(result['stop_price'])
            if result.get('filled_qty'):
                order.filled_quantity = Decimal(result['filled_qty'])
            if result.get('filled_avg_price'):
                order.average_price = Decimal(result['filled_avg_price'])
            
            order.created_at = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
            order.updated_at = datetime.fromisoformat(result['updated_at'].replace('Z', '+00:00'))
            
            return order
            
        except Exception:
            return None
    
    async def get_orders(self, status: str = 'open') -> List[Order]:
        """Get orders by status"""
        params = {'status': status}
        results = await self._request('GET', '/v2/orders', params=params)
        
        orders = []
        for result in results:
            order = Order(
                symbol=result['symbol'],
                quantity=Decimal(result['qty']),
                side=result['side'],
                order_type=result['order_type'],
                time_in_force=result['time_in_force'],
                order_id=result['id'],
                status=result['status']
            )
            
            if result.get('limit_price'):
                order.limit_price = Decimal(result['limit_price'])
            if result.get('stop_price'):
                order.stop_price = Decimal(result['stop_price'])
            if result.get('filled_qty'):
                order.filled_quantity = Decimal(result['filled_qty'])
            if result.get('filled_avg_price'):
                order.average_price = Decimal(result['filled_avg_price'])
            
            order.created_at = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
            order.updated_at = datetime.fromisoformat(result['updated_at'].replace('Z', '+00:00'))
            
            orders.append(order)
        
        return orders
    
    async def get_market_hours(self, symbol: str = 'SPY') -> Dict[str, Any]:
        """Get market hours"""
        today = datetime.now().date()
        calendar = await self._request('GET', f'/v2/calendar', params={
            'start': today.isoformat(),
            'end': today.isoformat()
        })
        
        if calendar:
            cal = calendar[0]
            return {
                'date': cal['date'],
                'open': cal['open'],
                'close': cal['close'],
                'is_open': True
            }
        
        return {'is_open': False}
    
    async def is_market_open(self) -> bool:
        """Check if market is currently open"""
        clock = await self._request('GET', '/v2/clock')
        return clock['is_open']
    
    async def get_latest_price(self, symbol: str) -> Decimal:
        """Get latest price for symbol"""
        trades = await self._request('GET', f'/v2/stocks/{symbol}/trades/latest')
        return Decimal(trades['trade']['p'])
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = '1Day'
    ) -> Dict[str, Any]:
        """Get historical price data"""
        params = {
            'symbols': symbol,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'timeframe': timeframe,
            'limit': 10000
        }
        
        bars = await self._request('GET', f'/v2/stocks/{symbol}/bars', params=params)
        
        return {
            'symbol': symbol,
            'bars': bars.get('bars', []),
            'timeframe': timeframe
        }
    
    async def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed asset information"""
        asset = await self._request('GET', f'/v2/assets/{symbol}')
        return asset
    
    async def get_watchlist(self, name: str = 'primary') -> List[str]:
        """Get symbols from watchlist"""
        try:
            watchlist = await self._request('GET', f'/v2/watchlists/{name}')
            return [asset['symbol'] for asset in watchlist.get('assets', [])]
        except:
            return []
    
    async def add_to_watchlist(self, symbol: str, watchlist_name: str = 'primary') -> bool:
        """Add symbol to watchlist"""
        try:
            await self._request('POST', f'/v2/watchlists/{watchlist_name}', json={'symbol': symbol})
            return True
        except:
            return False