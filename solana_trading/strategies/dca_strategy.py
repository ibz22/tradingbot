import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
from datetime import datetime, timedelta

from .base_strategy import BaseStrategy, TradeSignal, OrderSide, StrategyConfig

logger = logging.getLogger(__name__)

@dataclass
class DCAConfig(StrategyConfig):
    """Configuration for DCA (Dollar Cost Averaging) strategy"""
    purchase_amount: float = 0.1  # Amount to purchase in SOL each interval
    interval_minutes: int = 60  # Interval between purchases (default: 1 hour)
    max_total_investment: float = 10.0  # Maximum total investment per token in SOL
    target_tokens: List[str] = field(default_factory=list)  # Tokens to DCA into
    price_deviation_threshold: float = 0.05  # Only buy if price is within 5% of recent average
    enable_volatility_adjustment: bool = True  # Adjust buy size based on volatility
    volatility_multiplier: float = 1.5  # Multiplier for high volatility periods

@dataclass
class DCAState:
    """State tracking for DCA strategy"""
    token_mint: str
    total_invested: float = 0.0
    total_tokens_bought: float = 0.0
    last_purchase_time: float = 0.0
    purchase_count: int = 0
    average_buy_price: float = 0.0
    
    def update_purchase(self, amount_sol: float, tokens_received: float, price: float):
        """Update state after a purchase"""
        self.total_invested += amount_sol
        self.total_tokens_bought += tokens_received
        self.last_purchase_time = time.time()
        self.purchase_count += 1
        
        # Update average buy price
        if self.total_tokens_bought > 0:
            self.average_buy_price = self.total_invested / self.total_tokens_bought

class DCAStrategy(BaseStrategy):
    """Dollar Cost Averaging strategy for Solana tokens"""
    
    def __init__(self, config: DCAConfig):
        super().__init__("DCA_Strategy", config)
        self.dca_config = config
        
        # State tracking for each token
        self.dca_states: Dict[str, DCAState] = {}
        
        # Initialize states for target tokens
        for token in config.target_tokens:
            self.dca_states[token] = DCAState(token_mint=token)
    
    async def generate_signals(self, tokens: List[str]) -> List[TradeSignal]:
        """Generate DCA signals for target tokens"""
        signals = []
        
        if not self.enabled:
            return signals
            
        current_time = time.time()
        
        # Only consider tokens that are in our DCA target list
        target_tokens = [t for t in tokens if t in self.dca_config.target_tokens]
        
        for token_mint in target_tokens:
            try:
                signal = await self._generate_dca_signal(token_mint, current_time)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating DCA signal for {token_mint}: {e}")
        
        return signals
    
    async def _generate_dca_signal(self, token_mint: str, current_time: float) -> Optional[TradeSignal]:
        """Generate DCA signal for a specific token"""
        
        # Get or create DCA state for this token
        if token_mint not in self.dca_states:
            self.dca_states[token_mint] = DCAState(token_mint=token_mint)
        
        state = self.dca_states[token_mint]
        
        # Check if it's time for next purchase
        time_since_last = current_time - state.last_purchase_time
        interval_seconds = self.dca_config.interval_minutes * 60
        
        if time_since_last < interval_seconds:
            return None  # Not time yet
        
        # Check if we've reached maximum investment limit
        if state.total_invested >= self.dca_config.max_total_investment:
            logger.info(f"DCA: Maximum investment reached for {token_mint}")
            return None
        
        # Get current price
        current_price = await self.get_current_price(token_mint)
        if current_price is None:
            logger.warning(f"DCA: No current price available for {token_mint}")
            return None
        
        # Price deviation check
        if not await self._is_price_reasonable(token_mint, current_price):
            logger.info(f"DCA: Price deviation too high for {token_mint}, skipping")
            return None
        
        # Calculate purchase amount
        purchase_amount = self._calculate_purchase_amount(token_mint, current_price)
        
        # Ensure we don't exceed maximum investment
        remaining_budget = self.dca_config.max_total_investment - state.total_invested
        purchase_amount = min(purchase_amount, remaining_budget)
        
        if purchase_amount < self.config.min_trade_size:
            return None
        
        # Generate signal
        signal = TradeSignal(
            token_mint=token_mint,
            side=OrderSide.BUY,
            size_sol=purchase_amount,
            confidence=0.9,  # DCA is high confidence by nature
            strategy=self.name,
            reason=f"DCA purchase #{state.purchase_count + 1}, interval: {self.dca_config.interval_minutes}m",
            metadata={
                "dca_purchase_count": state.purchase_count + 1,
                "total_invested": state.total_invested,
                "average_buy_price": state.average_buy_price,
                "current_price": current_price,
                "remaining_budget": remaining_budget
            }
        )
        
        return signal
    
    async def _is_price_reasonable(self, token_mint: str, current_price: float) -> bool:
        """Check if current price is within reasonable bounds for DCA"""
        if not self.price_feed or not self.dca_config.price_deviation_threshold:
            return True  # Skip check if no price feed or threshold disabled
        
        try:
            # Get recent price history to calculate average
            price_history = self.price_feed.get_price_history(token_mint, limit=24)  # Last 24 data points
            if len(price_history) < 10:
                return True  # Not enough history, allow purchase
            
            recent_prices = [p.price for p in price_history[-10:]]  # Last 10 prices
            average_price = sum(recent_prices) / len(recent_prices)
            
            price_deviation = abs(current_price - average_price) / average_price
            
            if price_deviation > self.dca_config.price_deviation_threshold:
                logger.info(f"DCA: Price deviation {price_deviation:.2%} exceeds threshold {self.dca_config.price_deviation_threshold:.2%}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking price reasonableness for {token_mint}: {e}")
            return True  # Default to allowing purchase on error
    
    def _calculate_purchase_amount(self, token_mint: str, current_price: float) -> float:
        """Calculate purchase amount, potentially adjusted for volatility"""
        base_amount = self.dca_config.purchase_amount
        
        if not self.dca_config.enable_volatility_adjustment:
            return base_amount
        
        try:
            # Get volatility measure (ATR or price standard deviation)
            if self.technical_analyzer:
                indicators = self.technical_analyzer.get_latest_indicators(token_mint)
                if indicators and indicators.atr_14:
                    # Use ATR as volatility measure
                    volatility_ratio = indicators.atr_14 / current_price
                    
                    # Increase purchase size during high volatility (buying the dip)
                    if volatility_ratio > 0.05:  # High volatility threshold (5% ATR)
                        adjusted_amount = base_amount * self.dca_config.volatility_multiplier
                        logger.info(f"DCA: High volatility detected, increasing purchase size by {self.dca_config.volatility_multiplier}x")
                        return min(adjusted_amount, self.config.max_position_size)
            
            return base_amount
            
        except Exception as e:
            logger.error(f"Error calculating volatility-adjusted amount: {e}")
            return base_amount
    
    def record_purchase(self, token_mint: str, amount_sol: float, tokens_received: float, price: float):
        """Record a completed DCA purchase"""
        if token_mint not in self.dca_states:
            self.dca_states[token_mint] = DCAState(token_mint=token_mint)
        
        state = self.dca_states[token_mint]
        state.update_purchase(amount_sol, tokens_received, price)
        
        logger.info(f"DCA: Recorded purchase of {tokens_received} tokens for {amount_sol} SOL at price {price}")
        logger.info(f"DCA: Total invested: {state.total_invested} SOL, Avg price: {state.average_buy_price:.6f}")
    
    def get_dca_status(self, token_mint: str) -> Dict[str, Any]:
        """Get DCA status for a token"""
        if token_mint not in self.dca_states:
            return {"error": "Token not in DCA program"}
        
        state = self.dca_states[token_mint]
        current_time = time.time()
        
        next_purchase_time = state.last_purchase_time + (self.dca_config.interval_minutes * 60)
        time_until_next = max(0, next_purchase_time - current_time)
        
        return {
            "token_mint": token_mint,
            "total_invested_sol": state.total_invested,
            "total_tokens_bought": state.total_tokens_bought,
            "average_buy_price": state.average_buy_price,
            "purchase_count": state.purchase_count,
            "last_purchase_time": datetime.fromtimestamp(state.last_purchase_time).isoformat(),
            "next_purchase_in_seconds": int(time_until_next),
            "remaining_budget_sol": self.dca_config.max_total_investment - state.total_invested,
            "progress_percent": (state.total_invested / self.dca_config.max_total_investment) * 100
        }
    
    def get_all_dca_status(self) -> Dict[str, Any]:
        """Get DCA status for all tokens"""
        return {
            token: self.get_dca_status(token)
            for token in self.dca_config.target_tokens
        }
    
    def add_token(self, token_mint: str):
        """Add a token to DCA program"""
        if token_mint not in self.dca_config.target_tokens:
            self.dca_config.target_tokens.append(token_mint)
            self.dca_states[token_mint] = DCAState(token_mint=token_mint)
            logger.info(f"DCA: Added {token_mint} to DCA program")
    
    def remove_token(self, token_mint: str):
        """Remove a token from DCA program"""
        if token_mint in self.dca_config.target_tokens:
            self.dca_config.target_tokens.remove(token_mint)
            # Keep the state for historical purposes
            logger.info(f"DCA: Removed {token_mint} from DCA program")
    
    def update_config(self, **kwargs):
        """Update DCA configuration"""
        for key, value in kwargs.items():
            if hasattr(self.dca_config, key):
                setattr(self.dca_config, key, value)
                logger.info(f"DCA: Updated {key} to {value}")
            else:
                logger.warning(f"DCA: Unknown config parameter: {key}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all DCA positions"""
        summary = {
            "total_invested_sol": 0.0,
            "total_current_value_sol": 0.0,
            "total_pnl_sol": 0.0,
            "total_pnl_percent": 0.0,
            "positions": {}
        }
        
        for token_mint in self.dca_states:
            state = self.dca_states[token_mint]
            
            # Get current price
            current_price_data = self.price_feed.get_current_price(token_mint) if self.price_feed else None
            current_price = current_price_data.price if current_price_data else 0.0
            
            current_value = state.total_tokens_bought * current_price
            pnl = current_value - state.total_invested
            pnl_percent = (pnl / state.total_invested * 100) if state.total_invested > 0 else 0.0
            
            position_data = {
                "invested_sol": state.total_invested,
                "tokens_bought": state.total_tokens_bought,
                "average_buy_price": state.average_buy_price,
                "current_price": current_price,
                "current_value_sol": current_value,
                "pnl_sol": pnl,
                "pnl_percent": pnl_percent,
                "purchase_count": state.purchase_count
            }
            
            summary["positions"][token_mint] = position_data
            summary["total_invested_sol"] += state.total_invested
            summary["total_current_value_sol"] += current_value
            summary["total_pnl_sol"] += pnl
        
        if summary["total_invested_sol"] > 0:
            summary["total_pnl_percent"] = (summary["total_pnl_sol"] / summary["total_invested_sol"]) * 100
        
        return summary