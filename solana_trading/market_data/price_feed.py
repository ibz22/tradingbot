import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Price data point for a token"""
    token_mint: str
    symbol: str
    price: float
    volume_24h: float
    market_cap: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    source: str = "jupiter"
    
    def age_seconds(self) -> float:
        """Get age of this price data in seconds"""
        return time.time() - self.timestamp
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if price data is stale (default: 5 minutes)"""
        return self.age_seconds() > max_age_seconds

@dataclass
class OHLCV:
    """OHLC with Volume data"""
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: float
    
    def __post_init__(self):
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            logger.warning(f"Invalid OHLC data: O={self.open}, H={self.high}, L={self.low}, C={self.close}")

class PriceFeed:
    """Real-time price feed manager for Solana tokens"""
    
    def __init__(self, 
                 jupiter_client=None,
                 update_interval: float = 30.0,
                 max_history: int = 1000,
                 timeout: float = 10.0):
        self.jupiter_client = jupiter_client
        self.update_interval = update_interval
        self.max_history = max_history
        self.timeout = timeout
        
        # Price data storage
        self.current_prices: Dict[str, PriceData] = {}
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.ohlcv_data: Dict[str, Dict[str, deque]] = defaultdict(lambda: {
            '1m': deque(maxlen=1440),   # 1 day of 1-minute candles
            '5m': deque(maxlen=288),    # 1 day of 5-minute candles
            '1h': deque(maxlen=168),    # 1 week of hourly candles
            '1d': deque(maxlen=30)      # 30 days of daily candles
        })
        
        # Subscribers for price updates
        self.subscribers: List[Callable] = []
        
        # State management
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Supported tokens (will be populated from Jupiter)
        self.supported_tokens: Dict[str, Dict[str, Any]] = {}
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def start(self):
        """Start the price feed"""
        if self._running:
            logger.warning("Price feed is already running")
            return
            
        self._running = True
        logger.info("Starting price feed...")
        
        try:
            # Load supported tokens from Jupiter
            await self._load_supported_tokens()
            
            # Start price update task
            self._task = asyncio.create_task(self._price_update_loop())
            logger.info(f"Price feed started with {len(self.supported_tokens)} tokens")
            
        except Exception as e:
            logger.error(f"Failed to start price feed: {e}")
            self._running = False
            raise
    
    async def stop(self):
        """Stop the price feed"""
        if not self._running:
            return
            
        logger.info("Stopping price feed...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            
        if self.session and not self.session.closed:
            await self.session.close()
            
        logger.info("Price feed stopped")
    
    async def _load_supported_tokens(self):
        """Load supported tokens from Jupiter"""
        if not self.jupiter_client:
            logger.warning("No Jupiter client provided, using default token list")
            # Default Solana token list
            self.supported_tokens = {
                "So11111111111111111111111111111111111111112": {
                    "symbol": "SOL",
                    "name": "Solana",
                    "decimals": 9
                },
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                    "symbol": "USDC", 
                    "name": "USD Coin",
                    "decimals": 6
                },
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                    "symbol": "USDT",
                    "name": "Tether",
                    "decimals": 6
                }
            }
            return
            
        try:
            tokens = await self.jupiter_client.get_tokens()
            for token in tokens:
                if token.get("address") and token.get("symbol"):
                    self.supported_tokens[token["address"]] = {
                        "symbol": token["symbol"],
                        "name": token.get("name", token["symbol"]),
                        "decimals": token.get("decimals", 9),
                        "logoURI": token.get("logoURI"),
                        "tags": token.get("tags", [])
                    }
            
            logger.info(f"Loaded {len(self.supported_tokens)} supported tokens from Jupiter")
            
        except Exception as e:
            logger.error(f"Failed to load supported tokens: {e}")
            # Fall back to default list
            await self._load_supported_tokens()
    
    async def _price_update_loop(self):
        """Main price update loop"""
        while self._running:
            try:
                # Update prices for all supported tokens
                await self._update_all_prices()
                
                # Notify subscribers
                await self._notify_subscribers()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                await asyncio.sleep(min(self.update_interval, 10))  # Backoff on error
    
    async def _update_all_prices(self):
        """Update prices for all supported tokens"""
        # Get prices via CoinGecko API as Jupiter doesn't provide direct price feeds
        session = await self._get_session()
        
        try:
            # For simplicity, we'll use CoinGecko for major tokens
            # In production, you might want to use multiple sources or on-chain price feeds
            major_tokens = {
                "So11111111111111111111111111111111111111112": "solana",
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "usd-coin",
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "tether"
            }
            
            # Build CoinGecko request
            coin_ids = ",".join(major_tokens.values())
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_ids,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for mint_address, coin_id in major_tokens.items():
                        if coin_id in data:
                            coin_data = data[coin_id]
                            token_info = self.supported_tokens.get(mint_address, {})
                            
                            price_data = PriceData(
                                token_mint=mint_address,
                                symbol=token_info.get("symbol", "UNKNOWN"),
                                price=coin_data.get("usd", 0.0),
                                volume_24h=coin_data.get("usd_24h_vol", 0.0),
                                market_cap=coin_data.get("usd_market_cap"),
                                timestamp=time.time(),
                                source="coingecko"
                            )
                            
                            # Update current prices
                            self.current_prices[mint_address] = price_data
                            
                            # Add to price history
                            self.price_history[mint_address].append(price_data)
                            
                            # Update OHLCV data
                            self._update_ohlcv(mint_address, price_data.price)
                            
                else:
                    logger.warning(f"Failed to fetch prices from CoinGecko: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    def _update_ohlcv(self, token_mint: str, price: float):
        """Update OHLCV data for different timeframes"""
        timestamp = time.time()
        
        for timeframe in ['1m', '5m', '1h', '1d']:
            interval_seconds = {
                '1m': 60,
                '5m': 300, 
                '1h': 3600,
                '1d': 86400
            }[timeframe]
            
            # Get current interval timestamp
            interval_ts = int(timestamp // interval_seconds) * interval_seconds
            
            ohlcv_deque = self.ohlcv_data[token_mint][timeframe]
            
            # If we have existing data for this interval, update it
            if ohlcv_deque and ohlcv_deque[-1].timestamp == interval_ts:
                candle = ohlcv_deque[-1]
                candle.high = max(candle.high, price)
                candle.low = min(candle.low, price)
                candle.close = price
                candle.volume += 1  # Placeholder volume increment
            else:
                # Create new candle
                new_candle = OHLCV(
                    open=price,
                    high=price, 
                    low=price,
                    close=price,
                    volume=1,  # Placeholder volume
                    timestamp=interval_ts
                )
                ohlcv_deque.append(new_candle)
    
    async def _notify_subscribers(self):
        """Notify all subscribers of price updates"""
        if not self.subscribers:
            return
            
        for subscriber in self.subscribers.copy():  # Copy to avoid modification during iteration
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(dict(self.current_prices))
                else:
                    subscriber(dict(self.current_prices))
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to price updates"""
        self.subscribers.append(callback)
        logger.info(f"Added price feed subscriber: {callback.__name__}")
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from price updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Removed price feed subscriber: {callback.__name__}")
    
    def get_current_price(self, token_mint: str) -> Optional[PriceData]:
        """Get current price for a token"""
        return self.current_prices.get(token_mint)
    
    def get_price_history(self, token_mint: str, limit: Optional[int] = None) -> List[PriceData]:
        """Get price history for a token"""
        history = list(self.price_history.get(token_mint, []))
        if limit:
            return history[-limit:]
        return history
    
    def get_ohlcv(self, token_mint: str, timeframe: str = '1h', limit: Optional[int] = None) -> List[OHLCV]:
        """Get OHLCV data for a token"""
        if timeframe not in ['1m', '5m', '1h', '1d']:
            raise ValueError(f"Invalid timeframe: {timeframe}")
            
        ohlcv_data = list(self.ohlcv_data.get(token_mint, {}).get(timeframe, []))
        if limit:
            return ohlcv_data[-limit:]
        return ohlcv_data
    
    def get_supported_tokens(self) -> Dict[str, Dict[str, Any]]:
        """Get list of supported tokens"""
        return self.supported_tokens.copy()
    
    def is_supported(self, token_mint: str) -> bool:
        """Check if a token is supported"""
        return token_mint in self.supported_tokens
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()