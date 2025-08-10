import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
from datetime import datetime

from .base_strategy import BaseStrategy, TradeSignal, OrderSide, StrategyConfig
from ..market_data.technical_analysis import MarketSignal

logger = logging.getLogger(__name__)

@dataclass
class MomentumConfig(StrategyConfig):
    """Configuration for Momentum trading strategy"""
    # Price momentum thresholds
    strong_momentum_threshold: float = 5.0  # % price change for strong momentum
    weak_momentum_threshold: float = 2.0    # % price change for weak momentum
    
    # Time windows for momentum calculation
    short_window_minutes: int = 15  # Short-term momentum
    long_window_minutes: int = 60   # Long-term momentum
    
    # Entry/Exit criteria
    min_volume_ratio: float = 1.5   # Minimum volume vs average for entry
    rsi_overbought: float = 75.0    # RSI threshold for overbought
    rsi_oversold: float = 25.0      # RSI threshold for oversold
    
    # Position sizing
    momentum_position_multiplier: float = 1.2  # Increase position size for strong momentum
    max_momentum_position: float = 0.5         # Max position size for momentum trades
    
    # Risk management
    enable_trailing_stop: bool = True
    trailing_stop_percent: float = 3.0  # Trailing stop loss percentage
    take_profit_multiplier: float = 2.0  # Take profit at 2x trailing stop distance
    
    # Signal filters
    require_volume_confirmation: bool = True
    require_technical_confirmation: bool = True
    min_price_usd: float = 0.01  # Minimum price in USD to avoid pump/dump tokens

class MomentumStrategy(BaseStrategy):
    """Momentum-based trading strategy for Solana tokens"""
    
    def __init__(self, config: MomentumConfig):
        super().__init__("Momentum_Strategy", config)
        self.momentum_config = config
        
        # Track open positions for trailing stops
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        
        # Track momentum signals history for filtering
        self.momentum_history: Dict[str, List[Dict]] = {}
    
    async def generate_signals(self, tokens: List[str]) -> List[TradeSignal]:
        """Generate momentum-based trading signals"""
        signals = []
        
        if not self.enabled:
            return signals
        
        for token_mint in tokens:
            try:
                # Generate entry signals
                entry_signal = await self._generate_entry_signal(token_mint)
                if entry_signal:
                    signals.append(entry_signal)
                
                # Generate exit signals for existing positions
                exit_signal = await self._generate_exit_signal(token_mint)
                if exit_signal:
                    signals.append(exit_signal)
                    
            except Exception as e:
                logger.error(f"Error generating momentum signals for {token_mint}: {e}")
        
        return signals
    
    async def _generate_entry_signal(self, token_mint: str) -> Optional[TradeSignal]:
        """Generate entry signal based on momentum"""
        
        # Skip if we already have a position
        if token_mint in self.open_positions:
            return None
        
        # Get current price data
        current_price_data = self.price_feed.get_current_price(token_mint) if self.price_feed else None
        if not current_price_data:
            return None
        
        current_price = current_price_data.price
        
        # Check minimum price filter
        if current_price < self.momentum_config.min_price_usd:
            return None
        
        # Get technical analysis
        indicators = None
        if self.technical_analyzer:
            indicators = self.technical_analyzer.get_latest_indicators(token_mint)
        
        # Calculate momentum
        momentum_data = await self._calculate_momentum(token_mint)
        if not momentum_data:
            return None
        
        # Determine signal direction and strength
        signal_data = self._analyze_momentum_signal(momentum_data, indicators, current_price_data)
        if not signal_data:
            return None
        
        side, confidence, reason, metadata = signal_data
        
        # Apply filters
        if not self._passes_entry_filters(momentum_data, indicators, current_price_data):
            return None
        
        # Calculate position size
        position_size = self._calculate_position_size(confidence, momentum_data.get('strength', 1.0))
        
        # Create signal
        signal = TradeSignal(
            token_mint=token_mint,
            side=side,
            size_sol=position_size,
            confidence=confidence,
            strategy=self.name,
            reason=reason,
            metadata=metadata
        )
        
        # Set stop loss and take profit if enabled
        if self.momentum_config.enable_trailing_stop:
            stop_distance = current_price * (self.momentum_config.trailing_stop_percent / 100)
            if side == OrderSide.BUY:
                signal.stop_loss = current_price - stop_distance
                signal.take_profit = current_price + (stop_distance * self.momentum_config.take_profit_multiplier)
            else:  # SELL
                signal.stop_loss = current_price + stop_distance
                signal.take_profit = current_price - (stop_distance * self.momentum_config.take_profit_multiplier)
        
        return signal
    
    async def _generate_exit_signal(self, token_mint: str) -> Optional[TradeSignal]:
        """Generate exit signal for existing position"""
        
        if token_mint not in self.open_positions:
            return None
        
        position = self.open_positions[token_mint]
        
        # Get current price
        current_price_data = self.price_feed.get_current_price(token_mint) if self.price_feed else None
        if not current_price_data:
            return None
        
        current_price = current_price_data.price
        
        # Check trailing stop
        if self._should_exit_trailing_stop(position, current_price):
            return self._create_exit_signal(token_mint, "Trailing stop triggered", current_price)
        
        # Check take profit
        if self._should_exit_take_profit(position, current_price):
            return self._create_exit_signal(token_mint, "Take profit reached", current_price)
        
        # Check momentum reversal
        momentum_data = await self._calculate_momentum(token_mint)
        if momentum_data and self._should_exit_momentum_reversal(position, momentum_data):
            return self._create_exit_signal(token_mint, "Momentum reversal detected", current_price)
        
        # Update trailing stop
        self._update_trailing_stop(position, current_price)
        
        return None
    
    async def _calculate_momentum(self, token_mint: str) -> Optional[Dict[str, Any]]:
        """Calculate momentum indicators for a token"""
        if not self.price_feed:
            return None
        
        try:
            # Get recent price history
            short_history = self.price_feed.get_price_history(token_mint, limit=self.momentum_config.short_window_minutes)
            long_history = self.price_feed.get_price_history(token_mint, limit=self.momentum_config.long_window_minutes)
            
            if len(short_history) < 5 or len(long_history) < 10:
                return None
            
            # Calculate price changes
            current_price = short_history[-1].price
            short_start_price = short_history[0].price
            long_start_price = long_history[0].price
            
            short_momentum = ((current_price - short_start_price) / short_start_price) * 100
            long_momentum = ((current_price - long_start_price) / long_start_price) * 100
            
            # Calculate momentum strength (combination of short and long term)
            momentum_strength = abs(short_momentum) * 0.7 + abs(long_momentum) * 0.3
            
            # Calculate momentum direction consistency
            direction_consistency = 1.0 if (short_momentum >= 0) == (long_momentum >= 0) else 0.5
            
            # Calculate volume momentum if available
            volumes = [p.volume_24h for p in short_history if p.volume_24h > 0]
            volume_momentum = 1.0
            if len(volumes) >= 2:
                volume_momentum = volumes[-1] / (sum(volumes[:-1]) / len(volumes[:-1]))
            
            return {
                'short_momentum': short_momentum,
                'long_momentum': long_momentum,
                'strength': momentum_strength,
                'direction': 1 if short_momentum > 0 else -1,
                'consistency': direction_consistency,
                'volume_momentum': volume_momentum,
                'current_price': current_price,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum for {token_mint}: {e}")
            return None
    
    def _analyze_momentum_signal(self, momentum_data: Dict[str, Any], 
                                indicators: Any, 
                                price_data: Any) -> Optional[tuple]:
        """Analyze momentum data to generate signal"""
        
        short_momentum = momentum_data['short_momentum']
        long_momentum = momentum_data['long_momentum']
        strength = momentum_data['strength']
        consistency = momentum_data['consistency']
        
        # Determine signal strength based on momentum thresholds
        if strength >= self.momentum_config.strong_momentum_threshold:
            confidence = min(0.9, 0.7 + (strength / 20))  # Higher confidence for stronger momentum
        elif strength >= self.momentum_config.weak_momentum_threshold:
            confidence = min(0.7, 0.5 + (strength / 10))
        else:
            return None  # Too weak
        
        # Reduce confidence if directions are inconsistent
        confidence *= consistency
        
        # Determine direction
        if short_momentum > 0 and long_momentum > 0:
            side = OrderSide.BUY
            reason = f"Bullish momentum: {short_momentum:.1f}% (short), {long_momentum:.1f}% (long)"
        elif short_momentum < 0 and long_momentum < 0:
            side = OrderSide.SELL
            reason = f"Bearish momentum: {short_momentum:.1f}% (short), {long_momentum:.1f}% (long)"
        else:
            return None  # Mixed signals
        
        # Additional confidence adjustments based on technical indicators
        if indicators:
            if indicators.rsi_14:
                if side == OrderSide.BUY and indicators.rsi_14 > self.momentum_config.rsi_overbought:
                    confidence *= 0.7  # Reduce confidence for overbought conditions
                elif side == OrderSide.SELL and indicators.rsi_14 < self.momentum_config.rsi_oversold:
                    confidence *= 0.7  # Reduce confidence for oversold conditions
            
            # Volume confirmation
            if indicators.volume_ratio and indicators.volume_ratio < self.momentum_config.min_volume_ratio:
                confidence *= 0.8  # Reduce confidence for low volume
        
        metadata = {
            'short_momentum': short_momentum,
            'long_momentum': long_momentum,
            'momentum_strength': strength,
            'direction_consistency': consistency,
            'volume_momentum': momentum_data['volume_momentum'],
            'rsi': indicators.rsi_14 if indicators else None,
            'volume_ratio': indicators.volume_ratio if indicators else None
        }
        
        return side, confidence, reason, metadata
    
    def _passes_entry_filters(self, momentum_data: Dict[str, Any], 
                             indicators: Any, 
                             price_data: Any) -> bool:
        """Apply entry filters to momentum signal"""
        
        # Volume filter
        if self.momentum_config.require_volume_confirmation:
            volume_momentum = momentum_data.get('volume_momentum', 1.0)
            if volume_momentum < self.momentum_config.min_volume_ratio:
                return False
        
        # Technical confirmation filter
        if self.momentum_config.require_technical_confirmation and indicators:
            # Require at least some technical indicators to be favorable
            favorable_indicators = 0
            total_indicators = 0
            
            if indicators.rsi_14 is not None:
                total_indicators += 1
                if 30 <= indicators.rsi_14 <= 70:  # Not in extreme territory
                    favorable_indicators += 1
            
            if indicators.macd_line is not None and indicators.macd_signal is not None:
                total_indicators += 1
                direction = momentum_data['direction']
                macd_bullish = indicators.macd_line > indicators.macd_signal
                if (direction > 0 and macd_bullish) or (direction < 0 and not macd_bullish):
                    favorable_indicators += 1
            
            # Require at least 50% of indicators to be favorable
            if total_indicators > 0 and (favorable_indicators / total_indicators) < 0.5:
                return False
        
        return True
    
    def _calculate_position_size(self, confidence: float, momentum_strength: float) -> float:
        """Calculate position size based on confidence and momentum"""
        base_size = self.config.min_trade_size
        
        # Adjust for confidence
        confidence_multiplier = 1.0 + confidence
        
        # Adjust for momentum strength
        momentum_multiplier = min(self.momentum_config.momentum_position_multiplier, 
                                1.0 + (momentum_strength / 20))
        
        position_size = base_size * confidence_multiplier * momentum_multiplier
        
        # Apply maximum position limit
        position_size = min(position_size, self.momentum_config.max_momentum_position)
        position_size = min(position_size, self.config.max_position_size)
        
        return position_size
    
    def _create_exit_signal(self, token_mint: str, reason: str, current_price: float) -> TradeSignal:
        """Create exit signal for a position"""
        position = self.open_positions[token_mint]
        
        # Determine exit side (opposite of entry)
        exit_side = OrderSide.SELL if position['side'] == 'buy' else OrderSide.BUY
        
        return TradeSignal(
            token_mint=token_mint,
            side=exit_side,
            size_sol=position['size_sol'],
            confidence=0.9,  # High confidence for exits
            strategy=self.name,
            reason=reason,
            metadata={
                'exit_price': current_price,
                'entry_price': position['entry_price'],
                'position_age_minutes': (time.time() - position['entry_time']) / 60
            }
        )
    
    def _should_exit_trailing_stop(self, position: Dict, current_price: float) -> bool:
        """Check if trailing stop should be triggered"""
        if not self.momentum_config.enable_trailing_stop:
            return False
        
        trailing_stop = position.get('trailing_stop')
        if not trailing_stop:
            return False
        
        if position['side'] == 'buy':
            return current_price <= trailing_stop
        else:  # sell position
            return current_price >= trailing_stop
    
    def _should_exit_take_profit(self, position: Dict, current_price: float) -> bool:
        """Check if take profit should be triggered"""
        take_profit = position.get('take_profit')
        if not take_profit:
            return False
        
        if position['side'] == 'buy':
            return current_price >= take_profit
        else:  # sell position
            return current_price <= take_profit
    
    def _should_exit_momentum_reversal(self, position: Dict, momentum_data: Dict) -> bool:
        """Check if momentum has reversed significantly"""
        position_direction = 1 if position['side'] == 'buy' else -1
        current_direction = momentum_data['direction']
        
        # Exit if momentum has reversed and is strong in opposite direction
        if position_direction != current_direction:
            if momentum_data['strength'] > self.momentum_config.weak_momentum_threshold:
                return True
        
        return False
    
    def _update_trailing_stop(self, position: Dict, current_price: float):
        """Update trailing stop for a position"""
        if not self.momentum_config.enable_trailing_stop:
            return
        
        stop_distance = current_price * (self.momentum_config.trailing_stop_percent / 100)
        
        if position['side'] == 'buy':
            new_stop = current_price - stop_distance
            # Only update if new stop is higher (better for long position)
            if 'trailing_stop' not in position or new_stop > position['trailing_stop']:
                position['trailing_stop'] = new_stop
        else:  # sell position
            new_stop = current_price + stop_distance
            # Only update if new stop is lower (better for short position)
            if 'trailing_stop' not in position or new_stop < position['trailing_stop']:
                position['trailing_stop'] = new_stop
    
    def record_position_entry(self, token_mint: str, side: str, size_sol: float, 
                             entry_price: float, stop_loss: Optional[float] = None,
                             take_profit: Optional[float] = None):
        """Record when a momentum position is entered"""
        self.open_positions[token_mint] = {
            'side': side,
            'size_sol': size_sol,
            'entry_price': entry_price,
            'entry_time': time.time(),
            'trailing_stop': stop_loss,
            'take_profit': take_profit
        }
        
        logger.info(f"Momentum: Entered {side} position for {token_mint}: {size_sol} SOL at {entry_price}")
    
    def record_position_exit(self, token_mint: str, exit_price: float):
        """Record when a momentum position is exited"""
        if token_mint not in self.open_positions:
            return
        
        position = self.open_positions.pop(token_mint)
        
        # Calculate P&L
        entry_price = position['entry_price']
        size_sol = position['size_sol']
        
        if position['side'] == 'buy':
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        else:  # sell position
            pnl_percent = ((entry_price - exit_price) / entry_price) * 100
        
        hold_time_minutes = (time.time() - position['entry_time']) / 60
        
        logger.info(f"Momentum: Exited {position['side']} position for {token_mint}")
        logger.info(f"Entry: {entry_price}, Exit: {exit_price}, P&L: {pnl_percent:.2f}%, Hold: {hold_time_minutes:.1f}m")
    
    def get_open_positions(self) -> Dict[str, Any]:
        """Get all open momentum positions"""
        return self.open_positions.copy()
    
    def get_position_status(self, token_mint: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific position"""
        if token_mint not in self.open_positions:
            return None
        
        position = self.open_positions[token_mint]
        current_time = time.time()
        
        # Get current price for P&L calculation
        current_price = 0.0
        if self.price_feed:
            price_data = self.price_feed.get_current_price(token_mint)
            current_price = price_data.price if price_data else 0.0
        
        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        if current_price > 0:
            entry_price = position['entry_price']
            if position['side'] == 'buy':
                unrealized_pnl = ((current_price - entry_price) / entry_price) * 100
            else:  # sell
                unrealized_pnl = ((entry_price - current_price) / entry_price) * 100
        
        return {
            'token_mint': token_mint,
            'side': position['side'],
            'size_sol': position['size_sol'],
            'entry_price': position['entry_price'],
            'current_price': current_price,
            'entry_time': datetime.fromtimestamp(position['entry_time']).isoformat(),
            'hold_time_minutes': (current_time - position['entry_time']) / 60,
            'unrealized_pnl_percent': unrealized_pnl,
            'trailing_stop': position.get('trailing_stop'),
            'take_profit': position.get('take_profit')
        }