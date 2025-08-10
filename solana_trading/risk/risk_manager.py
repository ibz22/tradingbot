import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    POSITION_SIZE = "position_size"
    PORTFOLIO_LOSS = "portfolio_loss"
    DAILY_LOSS = "daily_loss"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    CORRELATION = "correlation"
    DRAWDOWN = "drawdown"
    STOP_LOSS = "stop_loss"

@dataclass
class RiskAlert:
    """Risk management alert"""
    alert_type: AlertType
    level: RiskLevel
    message: str
    token_mint: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    recommended_action: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class RiskConfig:
    """Risk management configuration"""
    # Position limits
    max_position_size_sol: float = 2.0
    max_position_percent: float = 25.0  # % of total portfolio
    min_position_size_sol: float = 0.01
    
    # Portfolio limits
    max_portfolio_loss_percent: float = 15.0  # Stop trading if down this much
    max_daily_loss_percent: float = 5.0      # Stop trading for day if down this much
    max_weekly_loss_percent: float = 10.0    # Stop trading for week if down this much
    
    # Volatility limits
    max_position_volatility: float = 0.8  # Maximum acceptable volatility (ATR/price)
    volatility_lookback_hours: int = 24   # Hours to look back for volatility calculation
    
    # Liquidity requirements
    min_liquidity_sol: float = 1.0        # Minimum liquidity required for entry
    liquidity_safety_factor: float = 0.1  # Only use 10% of available liquidity
    
    # Stop loss settings
    enable_stop_losses: bool = True
    default_stop_loss_percent: float = 5.0    # Default stop loss percentage
    trailing_stop_percent: float = 3.0        # Trailing stop percentage
    max_stop_loss_percent: float = 10.0       # Maximum stop loss allowed
    
    # Correlation limits
    max_correlation: float = 0.7          # Maximum correlation between positions
    correlation_lookback_days: int = 30   # Days to look back for correlation
    
    # Emergency shutdown
    enable_circuit_breaker: bool = True
    circuit_breaker_loss_percent: float = 20.0  # Emergency shutdown threshold
    cooldown_minutes_after_stop: int = 60       # Cooldown after emergency stop

@dataclass
class StopLossOrder:
    """Stop loss order tracking"""
    token_mint: str
    quantity: float
    stop_price: float
    is_trailing: bool
    created_time: float
    last_update_time: float
    highest_price: Optional[float] = None  # For trailing stops
    triggered: bool = False

class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        
        # Dependencies (injected)
        self.portfolio = None
        self.price_feed = None
        self.technical_analyzer = None
        
        # State tracking
        self.daily_start_value: Optional[float] = None
        self.daily_start_time: float = 0.0
        self.weekly_start_value: Optional[float] = None
        self.weekly_start_time: float = 0.0
        self.emergency_stop_active: bool = False
        self.emergency_stop_time: Optional[float] = None
        
        # Stop loss tracking
        self.stop_loss_orders: Dict[str, StopLossOrder] = {}
        
        # Alert history
        self.alerts_history: List[RiskAlert] = []
        self.active_alerts: Dict[str, RiskAlert] = {}
        
        # Performance tracking
        self.risk_events: List[Dict[str, Any]] = []
        
    def set_dependencies(self, portfolio=None, price_feed=None, technical_analyzer=None):
        """Inject dependencies"""
        self.portfolio = portfolio
        self.price_feed = price_feed
        self.technical_analyzer = technical_analyzer
        
        # Initialize daily/weekly tracking
        if self.portfolio and self.price_feed:
            self._initialize_period_tracking()
    
    def _initialize_period_tracking(self):
        """Initialize daily and weekly tracking values"""
        if not self.portfolio or not self.price_feed:
            return
            
        current_time = time.time()
        current_value = self.portfolio.get_portfolio_value(self.price_feed)
        
        # Initialize daily tracking
        if self.daily_start_value is None:
            self.daily_start_value = current_value
            self.daily_start_time = current_time
        
        # Reset daily tracking if it's a new day
        hours_since_daily_start = (current_time - self.daily_start_time) / 3600
        if hours_since_daily_start >= 24:
            self.daily_start_value = current_value
            self.daily_start_time = current_time
        
        # Initialize weekly tracking
        if self.weekly_start_value is None:
            self.weekly_start_value = current_value
            self.weekly_start_time = current_time
        
        # Reset weekly tracking if it's a new week
        hours_since_weekly_start = (current_time - self.weekly_start_time) / 3600
        if hours_since_weekly_start >= 168:  # 7 days
            self.weekly_start_value = current_value
            self.weekly_start_time = current_time
    
    async def validate_trade(self, token_mint: str, side: str, size_sol: float, 
                           current_price: float) -> Tuple[bool, List[RiskAlert]]:
        """Validate a trade against risk limits"""
        alerts = []
        
        # Check emergency stop
        if self.emergency_stop_active:
            cooldown_remaining = self._get_emergency_cooldown_remaining()
            if cooldown_remaining > 0:
                alerts.append(RiskAlert(
                    alert_type=AlertType.PORTFOLIO_LOSS,
                    level=RiskLevel.CRITICAL,
                    message=f"Emergency stop active. Cooldown remaining: {cooldown_remaining:.1f} minutes",
                    recommended_action="Wait for cooldown to complete"
                ))
                return False, alerts
        
        # Check position size limits
        if not self._check_position_size_limits(size_sol, token_mint, alerts):
            return False, alerts
        
        # Check portfolio loss limits
        if not await self._check_portfolio_loss_limits(alerts):
            return False, alerts
        
        # Check volatility limits
        if not await self._check_volatility_limits(token_mint, alerts):
            return False, alerts
        
        # Check liquidity requirements
        if not await self._check_liquidity_requirements(token_mint, size_sol, alerts):
            return False, alerts
        
        # Check correlation limits (for new positions)
        if side == "buy":
            if not await self._check_correlation_limits(token_mint, alerts):
                return False, alerts
        
        return True, alerts
    
    def _check_position_size_limits(self, size_sol: float, token_mint: str, alerts: List[RiskAlert]) -> bool:
        """Check position size limits"""
        # Check absolute size limit
        if size_sol > self.config.max_position_size_sol:
            alerts.append(RiskAlert(
                alert_type=AlertType.POSITION_SIZE,
                level=RiskLevel.HIGH,
                message=f"Position size {size_sol:.3f} SOL exceeds maximum {self.config.max_position_size_sol:.3f} SOL",
                token_mint=token_mint,
                current_value=size_sol,
                threshold=self.config.max_position_size_sol,
                recommended_action="Reduce position size"
            ))
            return False
        
        if size_sol < self.config.min_position_size_sol:
            alerts.append(RiskAlert(
                alert_type=AlertType.POSITION_SIZE,
                level=RiskLevel.LOW,
                message=f"Position size {size_sol:.3f} SOL below minimum {self.config.min_position_size_sol:.3f} SOL",
                token_mint=token_mint,
                current_value=size_sol,
                threshold=self.config.min_position_size_sol,
                recommended_action="Increase position size or skip trade"
            ))
            return False
        
        # Check percentage of portfolio limit
        if self.portfolio and self.price_feed:
            portfolio_value = self.portfolio.get_portfolio_value(self.price_feed)
            if portfolio_value > 0:
                position_percent = (size_sol / portfolio_value) * 100
                if position_percent > self.config.max_position_percent:
                    alerts.append(RiskAlert(
                        alert_type=AlertType.POSITION_SIZE,
                        level=RiskLevel.HIGH,
                        message=f"Position would be {position_percent:.1f}% of portfolio (max: {self.config.max_position_percent:.1f}%)",
                        token_mint=token_mint,
                        current_value=position_percent,
                        threshold=self.config.max_position_percent,
                        recommended_action="Reduce position size"
                    ))
                    return False
        
        return True
    
    async def _check_portfolio_loss_limits(self, alerts: List[RiskAlert]) -> bool:
        """Check portfolio loss limits"""
        if not self.portfolio or not self.price_feed:
            return True
        
        self._initialize_period_tracking()
        current_value = self.portfolio.get_portfolio_value(self.price_feed)
        
        # Check daily loss limit
        if self.daily_start_value and self.daily_start_value > 0:
            daily_loss_percent = ((self.daily_start_value - current_value) / self.daily_start_value) * 100
            
            if daily_loss_percent >= self.config.max_daily_loss_percent:
                alerts.append(RiskAlert(
                    alert_type=AlertType.DAILY_LOSS,
                    level=RiskLevel.HIGH,
                    message=f"Daily loss {daily_loss_percent:.1f}% exceeds limit {self.config.max_daily_loss_percent:.1f}%",
                    current_value=daily_loss_percent,
                    threshold=self.config.max_daily_loss_percent,
                    recommended_action="Stop trading for today"
                ))
                return False
        
        # Check weekly loss limit
        if self.weekly_start_value and self.weekly_start_value > 0:
            weekly_loss_percent = ((self.weekly_start_value - current_value) / self.weekly_start_value) * 100
            
            if weekly_loss_percent >= self.config.max_weekly_loss_percent:
                alerts.append(RiskAlert(
                    alert_type=AlertType.DAILY_LOSS,
                    level=RiskLevel.HIGH,
                    message=f"Weekly loss {weekly_loss_percent:.1f}% exceeds limit {self.config.max_weekly_loss_percent:.1f}%",
                    current_value=weekly_loss_percent,
                    threshold=self.config.max_weekly_loss_percent,
                    recommended_action="Stop trading for this week"
                ))
                return False
        
        # Check overall portfolio loss (circuit breaker)
        initial_value = self.portfolio.initial_balance
        if initial_value > 0:
            total_loss_percent = ((initial_value - current_value) / initial_value) * 100
            
            if total_loss_percent >= self.config.circuit_breaker_loss_percent:
                self._trigger_emergency_stop("Circuit breaker triggered", total_loss_percent)
                alerts.append(RiskAlert(
                    alert_type=AlertType.PORTFOLIO_LOSS,
                    level=RiskLevel.CRITICAL,
                    message=f"Portfolio loss {total_loss_percent:.1f}% triggered circuit breaker",
                    current_value=total_loss_percent,
                    threshold=self.config.circuit_breaker_loss_percent,
                    recommended_action="Emergency stop activated"
                ))
                return False
        
        return True
    
    async def _check_volatility_limits(self, token_mint: str, alerts: List[RiskAlert]) -> bool:
        """Check volatility limits for a token"""
        if not self.technical_analyzer or not self.price_feed:
            return True
        
        try:
            # Get technical indicators
            indicators = self.technical_analyzer.get_latest_indicators(token_mint)
            if not indicators or not indicators.atr_14:
                return True  # Skip check if no volatility data
            
            # Get current price
            price_data = self.price_feed.get_current_price(token_mint)
            if not price_data:
                return True
            
            current_price = price_data.price
            volatility_ratio = indicators.atr_14 / current_price if current_price > 0 else 0
            
            if volatility_ratio > self.config.max_position_volatility:
                alerts.append(RiskAlert(
                    alert_type=AlertType.VOLATILITY,
                    level=RiskLevel.MEDIUM,
                    message=f"Token volatility {volatility_ratio:.3f} exceeds limit {self.config.max_position_volatility:.3f}",
                    token_mint=token_mint,
                    current_value=volatility_ratio,
                    threshold=self.config.max_position_volatility,
                    recommended_action="Avoid trading highly volatile tokens"
                ))
                return False
                
        except Exception as e:
            logger.error(f"Error checking volatility limits for {token_mint}: {e}")
        
        return True
    
    async def _check_liquidity_requirements(self, token_mint: str, size_sol: float, alerts: List[RiskAlert]) -> bool:
        """Check liquidity requirements"""
        # This would require integration with DEX APIs to get real liquidity data
        # For now, we'll use a simplified check based on volume
        
        if not self.price_feed:
            return True
        
        try:
            price_data = self.price_feed.get_current_price(token_mint)
            if not price_data:
                return True
            
            # Use 24h volume as a proxy for liquidity
            volume_24h_sol = price_data.volume_24h
            
            if volume_24h_sol < self.config.min_liquidity_sol:
                alerts.append(RiskAlert(
                    alert_type=AlertType.LIQUIDITY,
                    level=RiskLevel.MEDIUM,
                    message=f"Low liquidity: {volume_24h_sol:.1f} SOL 24h volume < {self.config.min_liquidity_sol:.1f} SOL minimum",
                    token_mint=token_mint,
                    current_value=volume_24h_sol,
                    threshold=self.config.min_liquidity_sol,
                    recommended_action="Avoid trading low liquidity tokens"
                ))
                return False
            
            # Check if trade size is reasonable relative to liquidity
            max_safe_size = volume_24h_sol * self.config.liquidity_safety_factor
            if size_sol > max_safe_size:
                alerts.append(RiskAlert(
                    alert_type=AlertType.LIQUIDITY,
                    level=RiskLevel.HIGH,
                    message=f"Trade size {size_sol:.1f} SOL too large for liquidity (max safe: {max_safe_size:.1f} SOL)",
                    token_mint=token_mint,
                    current_value=size_sol,
                    threshold=max_safe_size,
                    recommended_action="Reduce trade size"
                ))
                return False
                
        except Exception as e:
            logger.error(f"Error checking liquidity requirements for {token_mint}: {e}")
        
        return True
    
    async def _check_correlation_limits(self, token_mint: str, alerts: List[RiskAlert]) -> bool:
        """Check correlation limits with existing positions"""
        # Simplified correlation check - in practice would need price correlation analysis
        # For now, just check if we already have a position in this token
        
        if not self.portfolio:
            return True
        
        existing_position = self.portfolio.get_position(token_mint)
        if existing_position and existing_position.quantity > 0:
            # Already have a position, consider this as potential over-concentration
            alerts.append(RiskAlert(
                alert_type=AlertType.CORRELATION,
                level=RiskLevel.LOW,
                message=f"Already have position in {token_mint}, consider correlation risk",
                token_mint=token_mint,
                recommended_action="Monitor for over-concentration"
            ))
            # Don't block the trade, just warn
        
        return True
    
    def create_stop_loss(self, token_mint: str, quantity: float, stop_price: float, 
                        is_trailing: bool = False) -> str:
        """Create a stop loss order"""
        stop_id = f"{token_mint}_{int(time.time())}"
        
        stop_order = StopLossOrder(
            token_mint=token_mint,
            quantity=quantity,
            stop_price=stop_price,
            is_trailing=is_trailing,
            created_time=time.time(),
            last_update_time=time.time(),
            highest_price=stop_price if is_trailing else None
        )
        
        self.stop_loss_orders[stop_id] = stop_order
        
        logger.info(f"Created {'trailing ' if is_trailing else ''}stop loss for {token_mint}: {quantity} @ {stop_price}")
        
        return stop_id
    
    async def check_stop_losses(self) -> List[Dict[str, Any]]:
        """Check all stop losses and return triggered ones"""
        triggered_stops = []
        
        if not self.price_feed:
            return triggered_stops
        
        for stop_id, stop_order in list(self.stop_loss_orders.items()):
            if stop_order.triggered:
                continue
            
            # Get current price
            price_data = self.price_feed.get_current_price(stop_order.token_mint)
            if not price_data:
                continue
            
            current_price = price_data.price
            
            # Update trailing stop if applicable
            if stop_order.is_trailing:
                if stop_order.highest_price is None or current_price > stop_order.highest_price:
                    stop_order.highest_price = current_price
                    # Update trailing stop price
                    trail_percent = self.config.trailing_stop_percent / 100
                    stop_order.stop_price = current_price * (1 - trail_percent)
                    stop_order.last_update_time = time.time()
            
            # Check if stop is triggered
            if current_price <= stop_order.stop_price:
                stop_order.triggered = True
                
                triggered_stop = {
                    'stop_id': stop_id,
                    'token_mint': stop_order.token_mint,
                    'quantity': stop_order.quantity,
                    'stop_price': stop_order.stop_price,
                    'current_price': current_price,
                    'is_trailing': stop_order.is_trailing,
                    'trigger_time': time.time()
                }
                
                triggered_stops.append(triggered_stop)
                
                # Create alert
                self._add_alert(RiskAlert(
                    alert_type=AlertType.STOP_LOSS,
                    level=RiskLevel.HIGH,
                    message=f"Stop loss triggered for {stop_order.token_mint}: {current_price:.6f} <= {stop_order.stop_price:.6f}",
                    token_mint=stop_order.token_mint,
                    current_value=current_price,
                    threshold=stop_order.stop_price,
                    recommended_action="Execute stop loss order"
                ))
                
                logger.warning(f"Stop loss triggered: {stop_order.token_mint} at {current_price}")
        
        return triggered_stops
    
    def remove_stop_loss(self, stop_id: str) -> bool:
        """Remove a stop loss order"""
        if stop_id in self.stop_loss_orders:
            del self.stop_loss_orders[stop_id]
            logger.info(f"Removed stop loss order: {stop_id}")
            return True
        return False
    
    def _trigger_emergency_stop(self, reason: str, loss_percent: float):
        """Trigger emergency stop"""
        self.emergency_stop_active = True
        self.emergency_stop_time = time.time()
        
        event = {
            'type': 'emergency_stop',
            'reason': reason,
            'loss_percent': loss_percent,
            'timestamp': time.time(),
            'portfolio_value': self.portfolio.get_portfolio_value(self.price_feed) if self.portfolio and self.price_feed else 0
        }
        
        self.risk_events.append(event)
        
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason} (Loss: {loss_percent:.1f}%)")
    
    def _get_emergency_cooldown_remaining(self) -> float:
        """Get remaining emergency stop cooldown in minutes"""
        if not self.emergency_stop_active or not self.emergency_stop_time:
            return 0.0
        
        elapsed_minutes = (time.time() - self.emergency_stop_time) / 60
        remaining_minutes = self.config.cooldown_minutes_after_stop - elapsed_minutes
        
        if remaining_minutes <= 0:
            self.emergency_stop_active = False
            self.emergency_stop_time = None
            return 0.0
        
        return remaining_minutes
    
    def _add_alert(self, alert: RiskAlert):
        """Add a risk alert"""
        self.alerts_history.append(alert)
        
        # Keep only recent alerts in active alerts
        alert_key = f"{alert.alert_type.value}_{alert.token_mint or 'global'}"
        self.active_alerts[alert_key] = alert
        
        # Clean old active alerts (keep only last hour)
        current_time = time.time()
        self.active_alerts = {
            k: v for k, v in self.active_alerts.items()
            if current_time - v.timestamp < 3600
        }
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        current_time = time.time()
        
        summary = {
            'timestamp': datetime.fromtimestamp(current_time).isoformat(),
            'emergency_stop_active': self.emergency_stop_active,
            'emergency_cooldown_remaining': self._get_emergency_cooldown_remaining(),
            'active_alerts_count': len(self.active_alerts),
            'stop_losses_count': len([s for s in self.stop_loss_orders.values() if not s.triggered]),
            'triggered_stops_count': len([s for s in self.stop_loss_orders.values() if s.triggered]),
            'config': {
                'max_position_size_sol': self.config.max_position_size_sol,
                'max_position_percent': self.config.max_position_percent,
                'max_daily_loss_percent': self.config.max_daily_loss_percent,
                'circuit_breaker_loss_percent': self.config.circuit_breaker_loss_percent
            }
        }
        
        # Add portfolio-specific metrics if available
        if self.portfolio and self.price_feed:
            current_value = self.portfolio.get_portfolio_value(self.price_feed)
            
            if self.daily_start_value:
                daily_pnl_percent = ((current_value - self.daily_start_value) / self.daily_start_value) * 100
                summary['daily_pnl_percent'] = daily_pnl_percent
            
            total_pnl_percent = self.portfolio.get_total_pnl_percent(self.price_feed)
            summary['total_pnl_percent'] = total_pnl_percent
        
        return summary
    
    def get_active_alerts(self) -> List[RiskAlert]:
        """Get active risk alerts"""
        return list(self.active_alerts.values())
    
    def get_stop_losses(self) -> Dict[str, Dict[str, Any]]:
        """Get all stop loss orders"""
        return {
            stop_id: {
                'token_mint': order.token_mint,
                'quantity': order.quantity,
                'stop_price': order.stop_price,
                'is_trailing': order.is_trailing,
                'created_time': datetime.fromtimestamp(order.created_time).isoformat(),
                'triggered': order.triggered,
                'highest_price': order.highest_price
            }
            for stop_id, order in self.stop_loss_orders.items()
        }
    
    def get_risk_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent risk events"""
        return self.risk_events[-limit:] if self.risk_events else []