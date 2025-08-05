"""
Simple broker gateway for paper trading using Alpaca.

This gateway demonstrates how you could wrap a broker API to place orders and
query account information.  It uses the `alpaca-py` SDK to send
market orders to Alpaca's paper trading endpoint.  To use this class you
need to set the environment variables ``ALPACA_API_KEY`` and
``ALPACA_SECRET_KEY`` or pass them explicitly when constructing the gateway.

Example
-------
    from halalbot.broker_gateway import AlpacaBrokerGateway

    broker = AlpacaBrokerGateway()
    await broker.place_order("AAPL", "buy", 10)
    equity = await broker.get_account_value()
    print(equity)
"""

from __future__ import annotations

import os
from typing import Optional

import aiohttp


class AlpacaBrokerGateway:
    """Asynchronous broker gateway for Alpaca paper trading."""

    BASE_URL = "https://paper-api.alpaca.markets"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_SECRET_KEY")
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials are required")

    async def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }
        url = f"{self.BASE_URL}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=json, timeout=15) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_account_value(self) -> float:
        """Return the current equity in the Alpaca account."""
        data = await self._request("GET", "/v2/account")
        return float(data.get("equity", 0.0))

    async def place_order(self, symbol: str, side: str, qty: float, order_type: str = "market", time_in_force: str = "day") -> dict:
        """Place a market order and return the order response."""
        order = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        return await self._request("POST", "/v2/orders", json=order)
type
        
        return await self._request("GET", "/v2/account/activities", params=params)
    
    async def get_portfolio_history(self, period: str = "1D", 
                                   timeframe: str = "1Min") -> Dict[str, Any]:
        """Get portfolio history"""
        params = {
            "period": period,
            "timeframe": timeframe
        }
        
        return await self._request("GET", "/v2/account/portfolio/history", params=params)
    
    async def get_market_hours(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get market hours for a specific date"""
        params = {}
        if date:
            params["date"] = date
        
        return await self._request("GET", "/v2/calendar", params=params)
    
    async def get_bars(self, symbols: List[str], timeframe: str = "1Day",
                      start: Optional[str] = None, end: Optional[str] = None,
                      limit: int = 1000) -> Dict[str, Any]:
        """Get historical bars"""
        params = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "limit": limit
        }
        
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        # Use data endpoint for market data
        url = f"{self.data_url}/v2/stocks/bars"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        await self._ensure_session()
        await self._rate_limit()
        
        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest quote for symbol"""
        url = f"{self.data_url}/v2/stocks/{symbol}/quotes/latest"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        await self._ensure_session()
        await self._rate_limit()
        
        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_latest_trade(self, symbol: str) -> Dict[str, Any]:
        """Get latest trade for symbol"""
        url = f"{self.data_url}/v2/stocks/{symbol}/trades/latest"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        await self._ensure_session()
        await self._rate_limit()
        
        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def reconcile_positions(self, expected_positions: Dict[str, float]) -> Dict[str, Any]:
        """Reconcile expected positions with actual broker positions"""
        try:
            actual_positions = await self.get_positions()
            actual_dict = {pos['symbol']: float(pos['qty']) for pos in actual_positions}
            
            discrepancies = {}
            
            # Check expected vs actual
            for symbol, expected_qty in expected_positions.items():
                actual_qty = actual_dict.get(symbol, 0.0)
                
                if abs(expected_qty - actual_qty) > 0.001:  # Account for floating point precision
                    discrepancies[symbol] = {
                        'expected': expected_qty,
                        'actual': actual_qty,
                        'difference': actual_qty - expected_qty
                    }
            
            # Check for unexpected positions
            for symbol, actual_qty in actual_dict.items():
                if symbol not in expected_positions and abs(actual_qty) > 0.001:
                    discrepancies[symbol] = {
                        'expected': 0.0,
                        'actual': actual_qty,
                        'difference': actual_qty,
                        'unexpected': True
                    }
            
            if discrepancies:
                logging.warning(f"⚠️ Position discrepancies found: {len(discrepancies)} symbols")
                for symbol, disc in discrepancies.items():
                    logging.warning(f"  {symbol}: expected {disc['expected']}, actual {disc['actual']}")
            else:
                logging.info("✅ All positions reconciled successfully")
            
            return {
                'reconciled': len(discrepancies) == 0,
                'discrepancies': discrepancies,
                'total_positions': len(actual_dict),
                'discrepancy_count': len(discrepancies)
            }
            
        except Exception as e:
            logging.error(f"❌ Position reconciliation failed: {e}")
            return {
                'reconciled': False,
                'error': str(e),
                'discrepancies': {},
                'total_positions': 0,
                'discrepancy_count': 0
            }
    
    async def get_buying_power(self) -> float:
        """Get available buying power"""
        try:
            account = await self.get_account()
            return float(account.get('buying_power', 0))
        except Exception as e:
            logging.error(f"Error getting buying power: {e}")
            return 0.0
    
    async def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        try:
            account = await self.get_account()
            return float(account.get('portfolio_value', 0))
        except Exception as e:
            logging.error(f"Error getting portfolio value: {e}")
            return 0.0
    
    async def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = await self._request("GET", "/v2/clock")
            return clock.get('is_open', False)
        except Exception as e:
            logging.error(f"Error checking market status: {e}")
            return False
    
    async def get_order_fills(self, order_id: str) -> List[Dict[str, Any]]:
        """Get fills for a specific order"""
        try:
            activities = await self.get_account_activities("FILL")
            
            # Filter fills for this order
            order_fills = []
            for activity in activities:
                if activity.get('order_id') == order_id:
                    order_fills.append({
                        'timestamp': activity.get('transaction_time'),
                        'qty': float(activity.get('qty', 0)),
                        'price': float(activity.get('price', 0)),
                        'side': activity.get('side'),
                        'symbol': activity.get('symbol')
                    })
            
            return order_fills
            
        except Exception as e:
            logging.error(f"Error getting order fills: {e}")
            return []
    
    async def get_daily_pnl(self) -> Dict[str, float]:
        """Get daily P&L information"""
        try:
            account = await self.get_account()
            
            return {
                'unrealized_pnl': float(account.get('unrealized_pl', 0)),
                'unrealized_pnl_percent': float(account.get('unrealized_plpc', 0)),
                'realized_pnl': float(account.get('realized_pl', 0)),  # This might not be available
                'total_pnl': float(account.get('unrealized_pl', 0))  # + realized if available
            }
            
        except Exception as e:
            logging.error(f"Error getting daily P&L: {e}")
            return {
                'unrealized_pnl': 0.0,
                'unrealized_pnl_percent': 0.0,
                'realized_pnl': 0.0,
                'total_pnl': 0.0
            }
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logging.info("🔌 Broker gateway connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This will issue a warning in async contexts
            # Better to use async context manager or explicit close()
            pass


class MockBrokerGateway:
    """Mock broker gateway for testing and dry-run mode"""
    
    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.account_value = 100000.0
        self.order_counter = 1000
        
        logging.info("🎭 Mock broker gateway initialized")
    
    async def place_order(self, symbol: str, side: str, qty: float, **kwargs) -> Dict[str, Any]:
        """Simulate order placement"""
        order_id = str(self.order_counter)
        self.order_counter += 1
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'qty': str(qty),
            'status': 'filled',  # Mock immediate fill
            'filled_qty': str(qty),
            'filled_avg_price': '100.00',  # Mock price
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        
        # Update mock positions
        current_qty = self.positions.get(symbol, 0.0)
        if side == 'buy':
            self.positions[symbol] = current_qty + qty
        else:
            self.positions[symbol] = current_qty - qty
        
        logging.info(f"🎭 Mock order placed: {side.upper()} {qty} {symbol} (ID: {order_id})")
        return order
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get mock order"""
        return self.orders.get(order_id, {})
    
    async def cancel_order(self, order_id: str) -> bool:
        """Mock order cancellation"""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'cancelled'
            logging.info(f"🎭 Mock order cancelled: {order_id}")
            return True
        return False
    
    async def get_account(self) -> Dict[str, Any]:
        """Mock account information"""
        return {
            'account_number': 'MOCK123456',
            'status': 'ACTIVE',
            'currency': 'USD',
            'buying_power': str(self.account_value),
            'portfolio_value': str(self.account_value),
            'cash': str(self.account_value * 0.5),
            'market_value': str(self.account_value * 0.5)
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Mock positions"""
        positions = []
        for symbol, qty in self.positions.items():
            if abs(qty) > 0.001:
                positions.append({
                    'symbol': symbol,
                    'qty': str(qty),
                    'side': 'long' if qty > 0 else 'short',
                    'market_value': str(abs(qty) * 100),  # Mock value
                    'avg_entry_price': '100.00',
                    'unrealized_pl': '0.00'
                })
        return positions
    
    async def reconcile_positions(self, expected_positions: Dict[str, float]) -> Dict[str, Any]:
        """Mock position reconciliation"""
        return {
            'reconciled': True,
            'discrepancies': {},
            'total_positions': len(self.positions),
            'discrepancy_count': 0
        }
    
    async def is_market_open(self) -> bool:
        """Mock market status"""
        return True
    
    async def health_check(self) -> bool:
        """Mock health check"""
        return True
    
    async def close(self):
        """Mock cleanup"""
        pass
