import asyncio
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from collections import deque
import pandas as pd
from .price_feed import PriceData, OHLCV

logger = logging.getLogger(__name__)

@dataclass
class TechnicalIndicators:
    """Collection of technical indicators for a token"""
    token_mint: str
    timestamp: float
    
    # Trend indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    
    # Momentum indicators
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    
    # Volatility indicators
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr_14: Optional[float] = None
    
    # Volume indicators
    volume_sma_20: Optional[float] = None
    volume_ratio: Optional[float] = None  # Current volume / Average volume
    
    # Custom indicators
    price_momentum_5m: Optional[float] = None  # 5-minute price change %
    price_momentum_1h: Optional[float] = None  # 1-hour price change %
    price_momentum_24h: Optional[float] = None  # 24-hour price change %

@dataclass
class MarketSignal:
    """Trading signal generated from technical analysis"""
    token_mint: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reason: str
    timestamp: float
    indicators: Dict[str, float]
    
    def is_strong(self, threshold: float = 0.7) -> bool:
        """Check if signal is strong enough to act on"""
        return self.strength >= threshold and self.confidence >= threshold

class TechnicalAnalyzer:
    """Technical analysis engine for Solana tokens"""
    
    def __init__(self, price_feed=None):
        self.price_feed = price_feed
        self.indicators_history: Dict[str, deque] = {}
        self.signals_history: Dict[str, deque] = {}
        
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
            
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Initial SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        if len(gains) < period:
            return None
            
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[float], 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow_period:
            return None, None, None
            
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        if ema_fast is None or ema_slow is None:
            return None, None, None
            
        macd_line = ema_fast - ema_slow
        
        # For signal line, we need historical MACD values
        # This is a simplified version - in practice you'd maintain MACD history
        signal_line = macd_line  # Placeholder
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: List[float], 
                                 period: int = 20, 
                                 std_dev: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
            
        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period  # SMA
        
        variance = sum((price - middle) ** 2 for price in recent_prices) / period
        std = variance ** 0.5
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def calculate_atr(self, ohlcv_data: List[OHLCV], period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(ohlcv_data) < period + 1:
            return None
            
        true_ranges = []
        for i in range(1, len(ohlcv_data)):
            current = ohlcv_data[i]
            previous = ohlcv_data[i-1]
            
            tr1 = current.high - current.low
            tr2 = abs(current.high - previous.close)
            tr3 = abs(current.low - previous.close)
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return None
            
        return sum(true_ranges[-period:]) / period
    
    def calculate_price_momentum(self, prices: List[float], periods_back: int) -> Optional[float]:
        """Calculate price momentum (percentage change)"""
        if len(prices) < periods_back + 1:
            return None
            
        current_price = prices[-1]
        past_price = prices[-(periods_back + 1)]
        
        if past_price == 0:
            return None
            
        return ((current_price - past_price) / past_price) * 100
    
    async def analyze_token(self, token_mint: str) -> Optional[TechnicalIndicators]:
        """Perform technical analysis on a token"""
        if not self.price_feed:
            logger.warning("No price feed available for technical analysis")
            return None
            
        try:
            # Get price history
            price_history = self.price_feed.get_price_history(token_mint, limit=200)
            if len(price_history) < 20:
                logger.warning(f"Insufficient price history for {token_mint}: {len(price_history)} points")
                return None
                
            prices = [p.price for p in price_history]
            volumes = [p.volume_24h for p in price_history]
            
            # Get OHLCV data for ATR calculation
            ohlcv_data = self.price_feed.get_ohlcv(token_mint, '1h', limit=50)
            
            # Calculate all indicators
            indicators = TechnicalIndicators(
                token_mint=token_mint,
                timestamp=price_history[-1].timestamp,
                
                # Trend indicators
                sma_20=self.calculate_sma(prices, 20),
                sma_50=self.calculate_sma(prices, 50),
                ema_12=self.calculate_ema(prices, 12),
                ema_26=self.calculate_ema(prices, 26),
                
                # Momentum indicators
                rsi_14=self.calculate_rsi(prices, 14),
                
                # Volatility indicators
                atr_14=self.calculate_atr(ohlcv_data, 14) if ohlcv_data else None,
                
                # Volume indicators
                volume_sma_20=self.calculate_sma(volumes, 20) if volumes else None,
                
                # Price momentum
                price_momentum_5m=self.calculate_price_momentum(prices, 5),
                price_momentum_1h=self.calculate_price_momentum(prices, 60),
                price_momentum_24h=self.calculate_price_momentum(prices, min(len(prices)-1, 1440))
            )
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self.calculate_macd(prices)
            indicators.macd_line = macd_line
            indicators.macd_signal = macd_signal
            indicators.macd_histogram = macd_histogram
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
            indicators.bb_upper = bb_upper
            indicators.bb_middle = bb_middle
            indicators.bb_lower = bb_lower
            
            # Calculate volume ratio
            if indicators.volume_sma_20 and volumes:
                current_volume = volumes[-1]
                indicators.volume_ratio = current_volume / indicators.volume_sma_20 if indicators.volume_sma_20 > 0 else 1.0
            
            # Store indicators history
            if token_mint not in self.indicators_history:
                self.indicators_history[token_mint] = deque(maxlen=1000)
            self.indicators_history[token_mint].append(indicators)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing token {token_mint}: {e}")
            return None
    
    def generate_signals(self, indicators: TechnicalIndicators) -> List[MarketSignal]:
        """Generate trading signals from technical indicators"""
        signals = []
        token_mint = indicators.token_mint
        timestamp = indicators.timestamp
        
        try:
            # RSI-based signals
            if indicators.rsi_14 is not None:
                if indicators.rsi_14 < 30:
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='buy',
                        strength=min((30 - indicators.rsi_14) / 30, 1.0),
                        confidence=0.7,
                        reason=f"RSI oversold at {indicators.rsi_14:.1f}",
                        timestamp=timestamp,
                        indicators={'rsi': indicators.rsi_14}
                    ))
                elif indicators.rsi_14 > 70:
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='sell',
                        strength=min((indicators.rsi_14 - 70) / 30, 1.0),
                        confidence=0.7,
                        reason=f"RSI overbought at {indicators.rsi_14:.1f}",
                        timestamp=timestamp,
                        indicators={'rsi': indicators.rsi_14}
                    ))
            
            # Moving average crossover signals
            if (indicators.sma_20 is not None and indicators.sma_50 is not None):
                ma_ratio = indicators.sma_20 / indicators.sma_50
                if ma_ratio > 1.02:  # 20-day SMA > 50-day SMA by 2%
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='buy',
                        strength=min((ma_ratio - 1) * 10, 1.0),
                        confidence=0.6,
                        reason=f"SMA20 above SMA50 by {((ma_ratio-1)*100):.1f}%",
                        timestamp=timestamp,
                        indicators={'sma_20': indicators.sma_20, 'sma_50': indicators.sma_50}
                    ))
                elif ma_ratio < 0.98:  # 20-day SMA < 50-day SMA by 2%
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='sell',
                        strength=min((1 - ma_ratio) * 10, 1.0),
                        confidence=0.6,
                        reason=f"SMA20 below SMA50 by {((1-ma_ratio)*100):.1f}%",
                        timestamp=timestamp,
                        indicators={'sma_20': indicators.sma_20, 'sma_50': indicators.sma_50}
                    ))
            
            # Bollinger Bands signals
            current_price = self.price_feed.get_current_price(token_mint)
            if (current_price and indicators.bb_upper is not None and 
                indicators.bb_lower is not None and indicators.bb_middle is not None):
                
                price = current_price.price
                if price <= indicators.bb_lower:
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='buy',
                        strength=0.8,
                        confidence=0.75,
                        reason="Price at lower Bollinger Band",
                        timestamp=timestamp,
                        indicators={'price': price, 'bb_lower': indicators.bb_lower}
                    ))
                elif price >= indicators.bb_upper:
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='sell',
                        strength=0.8,
                        confidence=0.75,
                        reason="Price at upper Bollinger Band",
                        timestamp=timestamp,
                        indicators={'price': price, 'bb_upper': indicators.bb_upper}
                    ))
            
            # Momentum-based signals
            if indicators.price_momentum_1h is not None:
                if indicators.price_momentum_1h > 5:  # Strong upward momentum
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='buy',
                        strength=min(indicators.price_momentum_1h / 10, 1.0),
                        confidence=0.6,
                        reason=f"Strong 1h momentum: {indicators.price_momentum_1h:.1f}%",
                        timestamp=timestamp,
                        indicators={'momentum_1h': indicators.price_momentum_1h}
                    ))
                elif indicators.price_momentum_1h < -5:  # Strong downward momentum
                    signals.append(MarketSignal(
                        token_mint=token_mint,
                        signal_type='sell',
                        strength=min(abs(indicators.price_momentum_1h) / 10, 1.0),
                        confidence=0.6,
                        reason=f"Strong 1h decline: {indicators.price_momentum_1h:.1f}%",
                        timestamp=timestamp,
                        indicators={'momentum_1h': indicators.price_momentum_1h}
                    ))
            
            # Volume confirmation
            if indicators.volume_ratio is not None and indicators.volume_ratio > 2.0:
                # High volume can increase confidence of existing signals
                for signal in signals:
                    signal.confidence = min(signal.confidence * 1.2, 1.0)
                    signal.reason += f" (High volume: {indicators.volume_ratio:.1f}x avg)"
            
            # Store signals history
            if token_mint not in self.signals_history:
                self.signals_history[token_mint] = deque(maxlen=1000)
            
            for signal in signals:
                self.signals_history[token_mint].append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {token_mint}: {e}")
            return []
    
    async def analyze_and_signal(self, token_mint: str) -> Tuple[Optional[TechnicalIndicators], List[MarketSignal]]:
        """Analyze token and generate signals in one call"""
        indicators = await self.analyze_token(token_mint)
        if indicators is None:
            return None, []
            
        signals = self.generate_signals(indicators)
        return indicators, signals
    
    def get_latest_indicators(self, token_mint: str) -> Optional[TechnicalIndicators]:
        """Get latest indicators for a token"""
        history = self.indicators_history.get(token_mint, [])
        return history[-1] if history else None
    
    def get_latest_signals(self, token_mint: str, limit: int = 10) -> List[MarketSignal]:
        """Get latest signals for a token"""
        history = list(self.signals_history.get(token_mint, []))
        return history[-limit:] if history else []
    
    def get_signal_summary(self, token_mint: str, timeframe_hours: int = 1) -> Dict[str, Any]:
        """Get summary of recent signals"""
        import time
        cutoff_time = time.time() - (timeframe_hours * 3600)
        
        recent_signals = [
            signal for signal in self.signals_history.get(token_mint, [])
            if signal.timestamp >= cutoff_time
        ]
        
        if not recent_signals:
            return {"signal_count": 0, "dominant_signal": "hold", "confidence": 0.0}
        
        buy_signals = [s for s in recent_signals if s.signal_type == 'buy']
        sell_signals = [s for s in recent_signals if s.signal_type == 'sell']
        
        buy_strength = sum(s.strength * s.confidence for s in buy_signals)
        sell_strength = sum(s.strength * s.confidence for s in sell_signals)
        
        if buy_strength > sell_strength:
            dominant_signal = "buy"
            confidence = buy_strength / len(buy_signals) if buy_signals else 0.0
        elif sell_strength > buy_strength:
            dominant_signal = "sell"
            confidence = sell_strength / len(sell_signals) if sell_signals else 0.0
        else:
            dominant_signal = "hold"
            confidence = 0.5
        
        return {
            "signal_count": len(recent_signals),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "dominant_signal": dominant_signal,
            "confidence": confidence,
            "buy_strength": buy_strength,
            "sell_strength": sell_strength
        }