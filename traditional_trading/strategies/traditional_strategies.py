"""
Traditional Trading Strategies
==============================

Professional trading strategies for stocks and commodities.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Trading signal with metadata"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    price: Decimal
    quantity: Optional[int] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    reason: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseTraditionalStrategy:
    """Base class for traditional trading strategies"""
    
    def __init__(self, params: Optional[Dict] = None):
        self.params = params or {}
        self.positions = {}
        self.signals_history = []
        
    async def analyze(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        current_price: Decimal
    ) -> TradingSignal:
        """
        Analyze symbol and generate trading signal
        
        Args:
            symbol: Stock symbol
            price_data: Historical price data (OHLCV)
            current_price: Current market price
            
        Returns:
            Trading signal
        """
        raise NotImplementedError
    
    def calculate_position_size(
        self,
        account_value: Decimal,
        risk_per_trade: Decimal = Decimal('0.02')
    ) -> int:
        """Calculate position size based on risk management"""
        position_value = account_value * risk_per_trade
        return int(position_value / 100)  # Simplified calculation
    
    def set_stop_loss(
        self,
        entry_price: Decimal,
        atr: Decimal,
        multiplier: float = 2.0
    ) -> Decimal:
        """Calculate stop loss based on ATR"""
        return entry_price - (atr * Decimal(multiplier))
    
    def set_take_profit(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        risk_reward_ratio: float = 2.0
    ) -> Decimal:
        """Calculate take profit based on risk/reward ratio"""
        risk = entry_price - stop_loss
        return entry_price + (risk * Decimal(risk_reward_ratio))


class TraditionalMomentumStrategy(BaseTraditionalStrategy):
    """
    Momentum trading strategy for stocks
    Uses moving averages, RSI, and volume analysis
    """
    
    def __init__(self, params: Optional[Dict] = None):
        default_params = {
            'fast_ma': 20,
            'slow_ma': 50,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_ma': 20,
            'min_volume_ratio': 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    async def analyze(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        current_price: Decimal
    ) -> TradingSignal:
        """Generate momentum-based trading signal"""
        
        if len(price_data) < self.params['slow_ma']:
            return TradingSignal(
                symbol=symbol,
                signal_type='hold',
                confidence=0.0,
                price=current_price,
                reason="Insufficient data"
            )
        
        # Calculate indicators
        price_data['fast_ma'] = price_data['close'].rolling(self.params['fast_ma']).mean()
        price_data['slow_ma'] = price_data['close'].rolling(self.params['slow_ma']).mean()
        price_data['rsi'] = self._calculate_rsi(price_data['close'], self.params['rsi_period'])
        price_data['volume_ma'] = price_data['volume'].rolling(self.params['volume_ma']).mean()
        price_data['atr'] = self._calculate_atr(price_data)
        
        # Get latest values
        latest = price_data.iloc[-1]
        prev = price_data.iloc[-2]
        
        # Volume confirmation
        volume_ratio = latest['volume'] / latest['volume_ma'] if latest['volume_ma'] > 0 else 0
        strong_volume = volume_ratio >= self.params['min_volume_ratio']
        
        # Generate signal
        signal_type = 'hold'
        confidence = 0.0
        reason = []
        
        # Bullish crossover
        if (latest['fast_ma'] > latest['slow_ma'] and 
            prev['fast_ma'] <= prev['slow_ma']):
            signal_type = 'buy'
            confidence = 0.7
            reason.append("Golden cross (bullish MA crossover)")
            
            if latest['rsi'] < self.params['rsi_overbought']:
                confidence += 0.1
                reason.append("RSI not overbought")
            
            if strong_volume:
                confidence += 0.2
                reason.append("Strong volume confirmation")
        
        # Bearish crossover
        elif (latest['fast_ma'] < latest['slow_ma'] and 
              prev['fast_ma'] >= prev['slow_ma']):
            signal_type = 'sell'
            confidence = 0.7
            reason.append("Death cross (bearish MA crossover)")
            
            if latest['rsi'] > self.params['rsi_oversold']:
                confidence += 0.1
                reason.append("RSI not oversold")
            
            if strong_volume:
                confidence += 0.2
                reason.append("Strong volume confirmation")
        
        # Momentum continuation
        elif latest['fast_ma'] > latest['slow_ma']:
            if latest['rsi'] < self.params['rsi_oversold']:
                signal_type = 'buy'
                confidence = 0.5
                reason.append("Oversold in uptrend")
        
        elif latest['fast_ma'] < latest['slow_ma']:
            if latest['rsi'] > self.params['rsi_overbought']:
                signal_type = 'sell'
                confidence = 0.5
                reason.append("Overbought in downtrend")
        
        # Calculate stop loss and take profit
        stop_loss = None
        take_profit = None
        
        if signal_type == 'buy':
            stop_loss = self.set_stop_loss(current_price, Decimal(str(latest['atr'])))
            take_profit = self.set_take_profit(current_price, stop_loss)
        elif signal_type == 'sell' and symbol in self.positions:
            # Exit signal for existing position
            stop_loss = current_price * Decimal('0.98')  # 2% stop
        
        signal = TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=min(1.0, confidence),
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason='; '.join(reason) if reason else "No clear signal"
        )
        
        self.signals_history.append(signal)
        return signal
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr


class TraditionalMeanReversionStrategy(BaseTraditionalStrategy):
    """
    Mean reversion strategy for stocks
    Uses Bollinger Bands, Z-score, and mean reversion indicators
    """
    
    def __init__(self, params: Optional[Dict] = None):
        default_params = {
            'bb_period': 20,
            'bb_std': 2.0,
            'zscore_period': 20,
            'zscore_threshold': 2.0,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    async def analyze(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        current_price: Decimal
    ) -> TradingSignal:
        """Generate mean reversion trading signal"""
        
        if len(price_data) < self.params['bb_period']:
            return TradingSignal(
                symbol=symbol,
                signal_type='hold',
                confidence=0.0,
                price=current_price,
                reason="Insufficient data"
            )
        
        # Calculate Bollinger Bands
        price_data['sma'] = price_data['close'].rolling(self.params['bb_period']).mean()
        price_data['std'] = price_data['close'].rolling(self.params['bb_period']).std()
        price_data['upper_band'] = price_data['sma'] + (price_data['std'] * self.params['bb_std'])
        price_data['lower_band'] = price_data['sma'] - (price_data['std'] * self.params['bb_std'])
        
        # Calculate Z-score
        price_data['zscore'] = (
            (price_data['close'] - price_data['sma']) / price_data['std']
        )
        
        # Calculate RSI
        price_data['rsi'] = self._calculate_rsi(price_data['close'], self.params['rsi_period'])
        
        # Get latest values
        latest = price_data.iloc[-1]
        
        signal_type = 'hold'
        confidence = 0.0
        reason = []
        
        # Check for oversold condition (buy signal)
        if latest['close'] <= latest['lower_band']:
            signal_type = 'buy'
            confidence = 0.6
            reason.append("Price at lower Bollinger Band")
            
            if latest['zscore'] <= -self.params['zscore_threshold']:
                confidence += 0.2
                reason.append(f"Z-score extreme ({latest['zscore']:.2f})")
            
            if latest['rsi'] < self.params['rsi_oversold']:
                confidence += 0.2
                reason.append(f"RSI oversold ({latest['rsi']:.1f})")
        
        # Check for overbought condition (sell signal)
        elif latest['close'] >= latest['upper_band']:
            signal_type = 'sell'
            confidence = 0.6
            reason.append("Price at upper Bollinger Band")
            
            if latest['zscore'] >= self.params['zscore_threshold']:
                confidence += 0.2
                reason.append(f"Z-score extreme ({latest['zscore']:.2f})")
            
            if latest['rsi'] > self.params['rsi_overbought']:
                confidence += 0.2
                reason.append(f"RSI overbought ({latest['rsi']:.1f})")
        
        # Mean reversion opportunity
        elif abs(latest['zscore']) > 1.5:
            if latest['zscore'] < 0:
                signal_type = 'buy'
                confidence = 0.4
                reason.append("Moderate oversold condition")
            else:
                signal_type = 'sell'
                confidence = 0.4
                reason.append("Moderate overbought condition")
        
        # Calculate stops
        stop_loss = None
        take_profit = None
        
        if signal_type == 'buy':
            stop_loss = Decimal(str(latest['lower_band'] * 0.98))
            take_profit = Decimal(str(latest['sma']))
        elif signal_type == 'sell':
            stop_loss = Decimal(str(latest['upper_band'] * 1.02))
            take_profit = Decimal(str(latest['sma']))
        
        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=min(1.0, confidence),
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason='; '.join(reason) if reason else "No clear signal"
        )
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class TraditionalBreakoutStrategy(BaseTraditionalStrategy):
    """
    Breakout trading strategy
    Identifies and trades price breakouts from consolidation patterns
    """
    
    def __init__(self, params: Optional[Dict] = None):
        default_params = {
            'lookback_period': 20,
            'breakout_threshold': 0.02,  # 2% above resistance
            'volume_multiplier': 2.0,
            'atr_period': 14,
            'min_consolidation_days': 5
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    async def analyze(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        current_price: Decimal
    ) -> TradingSignal:
        """Generate breakout trading signal"""
        
        if len(price_data) < self.params['lookback_period']:
            return TradingSignal(
                symbol=symbol,
                signal_type='hold',
                confidence=0.0,
                price=current_price,
                reason="Insufficient data"
            )
        
        # Calculate resistance and support levels
        lookback_data = price_data.tail(self.params['lookback_period'])
        resistance = lookback_data['high'].max()
        support = lookback_data['low'].min()
        
        # Calculate ATR for volatility
        price_data['atr'] = self._calculate_atr(price_data, self.params['atr_period'])
        
        # Volume analysis
        price_data['volume_ma'] = price_data['volume'].rolling(20).mean()
        latest = price_data.iloc[-1]
        
        # Check for consolidation
        price_range = resistance - support
        avg_price = (resistance + support) / 2
        consolidation_ratio = price_range / avg_price
        is_consolidating = consolidation_ratio < 0.1  # Less than 10% range
        
        signal_type = 'hold'
        confidence = 0.0
        reason = []
        
        # Bullish breakout
        if float(current_price) > resistance * (1 + self.params['breakout_threshold']):
            signal_type = 'buy'
            confidence = 0.7
            reason.append(f"Bullish breakout above {resistance:.2f}")
            
            # Volume confirmation
            volume_ratio = latest['volume'] / latest['volume_ma'] if latest['volume_ma'] > 0 else 0
            if volume_ratio >= self.params['volume_multiplier']:
                confidence += 0.3
                reason.append(f"Strong volume ({volume_ratio:.1f}x average)")
            
            if is_consolidating:
                confidence = min(1.0, confidence + 0.1)
                reason.append("Breaking from consolidation")
        
        # Bearish breakdown
        elif float(current_price) < support * (1 - self.params['breakout_threshold']):
            signal_type = 'sell'
            confidence = 0.7
            reason.append(f"Bearish breakdown below {support:.2f}")
            
            # Volume confirmation
            volume_ratio = latest['volume'] / latest['volume_ma'] if latest['volume_ma'] > 0 else 0
            if volume_ratio >= self.params['volume_multiplier']:
                confidence += 0.3
                reason.append(f"Strong volume ({volume_ratio:.1f}x average)")
        
        # Set stops and targets
        stop_loss = None
        take_profit = None
        
        if signal_type == 'buy':
            stop_loss = Decimal(str(resistance * 0.98))  # Just below breakout level
            breakout_target = resistance + (price_range * 1.5)  # 1.5x range projection
            take_profit = Decimal(str(breakout_target))
        elif signal_type == 'sell':
            stop_loss = Decimal(str(support * 1.02))  # Just above breakdown level
            breakdown_target = support - (price_range * 1.5)
            take_profit = Decimal(str(breakdown_target))
        
        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=min(1.0, confidence),
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason='; '.join(reason) if reason else "No breakout detected"
        )
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr