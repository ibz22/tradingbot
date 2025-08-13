"""
Traditional Asset Trading Module
================================

Professional trading system for traditional assets (stocks, ETFs, commodities)
with full halal compliance screening and multiple broker integrations.
"""

from .brokers.alpaca_broker import AlpacaBroker
from .screening.stock_screener import StockScreener
from .strategies.traditional_strategies import TraditionalMomentumStrategy, TraditionalMeanReversionStrategy
from .market_data.data_provider import MarketDataProvider

__version__ = "1.0.0"
__all__ = [
    "AlpacaBroker",
    "StockScreener",
    "TraditionalMomentumStrategy",
    "TraditionalMeanReversionStrategy",
    "MarketDataProvider"
]