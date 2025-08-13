"""
Market Data Provider
===================

Provides market data for traditional assets.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Market data provider for traditional assets"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    async def get_price(self, symbol: str) -> Decimal:
        """Get current price for symbol"""
        # Mock implementation
        mock_prices = {
            'AAPL': Decimal('175.43'),
            'MSFT': Decimal('380.52'),
            'GOOGL': Decimal('142.65'),
            'GLD': Decimal('185.20'),
            'SPY': Decimal('450.30')
        }
        return mock_prices.get(symbol, Decimal('100.00'))
    
    async def get_historical_data(
        self,
        symbol: str,
        days: int = 30
    ) -> pd.DataFrame:
        """Get historical OHLCV data"""
        # Mock implementation
        import numpy as np
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='D'
        )
        
        # Generate mock OHLCV data
        base_price = float(await self.get_price(symbol))
        returns = np.random.normal(0, 0.02, len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })
        
        return df