import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import time
from datetime import datetime, timedelta

from ..paper_trading.portfolio import VirtualPortfolio, Position

logger = logging.getLogger(__name__)

@dataclass
class PortfolioConfig:
    """Configuration for portfolio management"""
    max_positions: int = 10
    max_position_percent: float = 20.0  # Max % of portfolio per position
    min_position_percent: float = 1.0   # Min % of portfolio per position
    rebalance_threshold: float = 5.0    # Rebalance when position deviates by this %
    rebalance_frequency_hours: int = 24 # How often to check for rebalancing
    
    # Diversification rules
    max_sector_concentration: float = 40.0  # Max % in any single sector
    correlation_threshold: float = 0.8      # Avoid highly correlated assets
    
    # Risk management
    max_drawdown_percent: float = 10.0  # Stop trading if portfolio down by this %
    trailing_stop_percent: float = 5.0  # Trailing stop for entire portfolio
    
    # Target allocations (token_mint -> target_percent)
    target_allocations: Dict[str, float] = field(default_factory=dict)

@dataclass
class RebalanceRecommendation:
    """Recommendation for portfolio rebalancing"""
    token_mint: str
    symbol: str
    current_percent: float
    target_percent: float
    deviation: float
    action: str  # 'buy', 'sell', 'hold'
    amount_sol: float
    reason: str

class PortfolioManager:
    """Advanced portfolio management system"""
    
    def __init__(self, config: PortfolioConfig, portfolio: VirtualPortfolio = None):
        self.config = config
        self.portfolio = portfolio or VirtualPortfolio()
        
        # Dependencies (injected)
        self.price_feed = None
        self.risk_manager = None
        
        # State tracking
        self.last_rebalance_time = time.time()
        self.portfolio_high_water_mark = 0.0
        self.rebalance_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.daily_values: List[Tuple[float, float]] = []  # (timestamp, portfolio_value)
        self.last_daily_record = 0.0
    
    def set_dependencies(self, price_feed=None, risk_manager=None):
        """Inject dependencies"""
        self.price_feed = price_feed
        self.risk_manager = risk_manager
    
    def update_target_allocations(self, allocations: Dict[str, float]):
        """Update target portfolio allocations"""
        total_percent = sum(allocations.values())
        if abs(total_percent - 100.0) > 1.0:
            raise ValueError(f"Target allocations must sum to 100%, got {total_percent}%")
        
        self.config.target_allocations = allocations.copy()
        logger.info(f"Updated target allocations: {len(allocations)} assets")
    
    def get_current_allocations(self) -> Dict[str, float]:
        """Get current portfolio allocations as percentages"""
        if not self.price_feed:
            return {}
        
        total_value = self.portfolio.get_portfolio_value(self.price_feed)
        if total_value == 0:
            return {}
        
        allocations = {}
        
        # SOL allocation
        sol_percent = (self.portfolio.sol_balance / total_value) * 100
        if sol_percent > 0.1:  # Only include if > 0.1%
            allocations["SOL"] = sol_percent
        
        # Token positions
        for token_mint, position in self.portfolio.positions.items():
            price_data = self.price_feed.get_current_price(token_mint)
            if price_data:
                position_value = position.quantity * price_data.price
                position_percent = (position_value / total_value) * 100
                if position_percent > 0.1:  # Only include if > 0.1%
                    allocations[token_mint] = position_percent
        
        return allocations
    
    def analyze_portfolio_balance(self) -> List[RebalanceRecommendation]:
        """Analyze portfolio and generate rebalancing recommendations"""
        recommendations = []
        
        if not self.config.target_allocations or not self.price_feed:
            return recommendations
        
        current_allocations = self.get_current_allocations()
        total_value = self.portfolio.get_portfolio_value(self.price_feed)
        
        for token_mint, target_percent in self.config.target_allocations.items():
            current_percent = current_allocations.get(token_mint, 0.0)
            deviation = current_percent - target_percent
            
            # Check if rebalancing is needed
            if abs(deviation) >= self.config.rebalance_threshold:
                if deviation > 0:
                    # Overallocated - need to sell
                    action = "sell"
                    amount_sol = (abs(deviation) / 100) * total_value
                    reason = f"Overallocated by {deviation:.1f}% (target: {target_percent:.1f}%)"
                else:
                    # Underallocated - need to buy
                    action = "buy"
                    amount_sol = (abs(deviation) / 100) * total_value
                    reason = f"Underallocated by {abs(deviation):.1f}% (target: {target_percent:.1f}%)"
                
                # Get token symbol for display
                symbol = token_mint
                if self.price_feed:
                    supported_tokens = self.price_feed.get_supported_tokens()
                    token_info = supported_tokens.get(token_mint, {})
                    symbol = token_info.get('symbol', token_mint[:8])
                
                recommendation = RebalanceRecommendation(
                    token_mint=token_mint,
                    symbol=symbol,
                    current_percent=current_percent,
                    target_percent=target_percent,
                    deviation=deviation,
                    action=action,
                    amount_sol=amount_sol,
                    reason=reason
                )
                
                recommendations.append(recommendation)
        
        # Sort by deviation magnitude (largest first)
        recommendations.sort(key=lambda x: abs(x.deviation), reverse=True)
        
        return recommendations
    
    def should_rebalance(self) -> bool:
        """Check if portfolio should be rebalanced"""
        current_time = time.time()
        time_since_last = current_time - self.last_rebalance_time
        hours_since_last = time_since_last / 3600
        
        # Check time-based rebalancing
        if hours_since_last >= self.config.rebalance_frequency_hours:
            return True
        
        # Check deviation-based rebalancing
        recommendations = self.analyze_portfolio_balance()
        significant_deviations = [r for r in recommendations if abs(r.deviation) >= self.config.rebalance_threshold]
        
        return len(significant_deviations) > 0
    
    async def execute_rebalancing(self, recommendations: List[RebalanceRecommendation]) -> Dict[str, Any]:
        """Execute portfolio rebalancing"""
        rebalance_session = {
            'timestamp': time.time(),
            'recommendations': len(recommendations),
            'executed_trades': 0,
            'total_volume': 0.0,
            'success': False,
            'errors': []
        }
        
        try:
            # Execute sell orders first (to free up SOL for buys)
            sell_recommendations = [r for r in recommendations if r.action == "sell"]
            for recommendation in sell_recommendations:
                try:
                    success = await self._execute_rebalance_trade(recommendation)
                    if success:
                        rebalance_session['executed_trades'] += 1
                        rebalance_session['total_volume'] += recommendation.amount_sol
                except Exception as e:
                    error_msg = f"Failed to sell {recommendation.symbol}: {str(e)}"
                    rebalance_session['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Execute buy orders
            buy_recommendations = [r for r in recommendations if r.action == "buy"]
            for recommendation in buy_recommendations:
                try:
                    success = await self._execute_rebalance_trade(recommendation)
                    if success:
                        rebalance_session['executed_trades'] += 1
                        rebalance_session['total_volume'] += recommendation.amount_sol
                except Exception as e:
                    error_msg = f"Failed to buy {recommendation.symbol}: {str(e)}"
                    rebalance_session['errors'].append(error_msg)
                    logger.error(error_msg)
            
            self.last_rebalance_time = time.time()
            rebalance_session['success'] = rebalance_session['executed_trades'] > 0
            
        except Exception as e:
            logger.error(f"Rebalancing failed: {e}")
            rebalance_session['errors'].append(str(e))
        
        finally:
            self.rebalance_history.append(rebalance_session)
        
        return rebalance_session
    
    async def _execute_rebalance_trade(self, recommendation: RebalanceRecommendation) -> bool:
        """Execute a single rebalancing trade"""
        if not self.price_feed:
            return False
        
        price_data = self.price_feed.get_current_price(recommendation.token_mint)
        if not price_data:
            logger.warning(f"No price data for {recommendation.symbol}")
            return False
        
        current_price = price_data.price
        
        if recommendation.action == "buy":
            # Buy tokens with SOL
            success = self.portfolio.buy_token(
                token_mint=recommendation.token_mint,
                symbol=recommendation.symbol,
                sol_amount=recommendation.amount_sol,
                price=current_price,
                fee_percent=0.1  # Assume 0.1% fee
            )
            
            if success:
                logger.info(f"Rebalance: Bought {recommendation.amount_sol:.3f} SOL worth of {recommendation.symbol}")
            
            return success
            
        else:  # sell
            # Calculate quantity to sell based on SOL amount
            position = self.portfolio.get_position(recommendation.token_mint)
            if not position or position.quantity == 0:
                return False
            
            # Sell the required SOL amount worth of tokens
            tokens_to_sell = min(recommendation.amount_sol / current_price, position.quantity)
            
            success = self.portfolio.sell_token(
                token_mint=recommendation.token_mint,
                quantity=tokens_to_sell,
                price=current_price,
                fee_percent=0.1  # Assume 0.1% fee
            )
            
            if success:
                logger.info(f"Rebalance: Sold {tokens_to_sell:.6f} {recommendation.symbol} for {tokens_to_sell * current_price:.3f} SOL")
            
            return success
    
    def check_risk_limits(self) -> Dict[str, Any]:
        """Check if portfolio is within risk limits"""
        risk_status = {
            'within_limits': True,
            'warnings': [],
            'violations': []
        }
        
        if not self.price_feed:
            return risk_status
        
        current_value = self.portfolio.get_portfolio_value(self.price_feed)
        allocations = self.get_current_allocations()
        
        # Update high water mark
        if current_value > self.portfolio_high_water_mark:
            self.portfolio_high_water_mark = current_value
        
        # Check maximum drawdown
        if self.portfolio_high_water_mark > 0:
            drawdown_percent = ((self.portfolio_high_water_mark - current_value) / self.portfolio_high_water_mark) * 100
            if drawdown_percent >= self.config.max_drawdown_percent:
                risk_status['within_limits'] = False
                risk_status['violations'].append(f"Maximum drawdown exceeded: {drawdown_percent:.1f}% >= {self.config.max_drawdown_percent}%")
        
        # Check position concentration
        for token_mint, percent in allocations.items():
            if percent >= self.config.max_position_percent:
                risk_status['warnings'].append(f"Position {token_mint} is {percent:.1f}% of portfolio (max: {self.config.max_position_percent}%)")
        
        # Check maximum positions limit
        active_positions = len([p for p in self.portfolio.positions.values() if p.quantity > 0])
        if active_positions >= self.config.max_positions:
            risk_status['warnings'].append(f"Maximum positions limit reached: {active_positions}/{self.config.max_positions}")
        
        return risk_status
    
    def record_daily_value(self):
        """Record daily portfolio value for performance tracking"""
        current_time = time.time()
        
        # Only record once per day
        if current_time - self.last_daily_record < 86400:  # 24 hours
            return
        
        if self.price_feed:
            portfolio_value = self.portfolio.get_portfolio_value(self.price_feed)
            self.daily_values.append((current_time, portfolio_value))
            
            # Keep only last 365 days
            cutoff_time = current_time - (365 * 86400)
            self.daily_values = [(t, v) for t, v in self.daily_values if t > cutoff_time]
            
            self.last_daily_record = current_time
    
    def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive portfolio performance metrics"""
        if not self.price_feed or len(self.daily_values) < 2:
            return {"error": "Insufficient data for metrics calculation"}
        
        current_value = self.portfolio.get_portfolio_value(self.price_feed)
        
        # Calculate returns
        daily_returns = []
        for i in range(1, len(self.daily_values)):
            prev_value = self.daily_values[i-1][1]
            curr_value = self.daily_values[i][1]
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)
        
        if not daily_returns:
            return {"error": "No return data available"}
        
        # Calculate metrics
        import statistics
        
        avg_daily_return = statistics.mean(daily_returns)
        std_daily_return = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0.0
        
        # Annualized metrics (assuming 365 trading days)
        annual_return = (avg_daily_return * 365) * 100
        annual_volatility = (std_daily_return * (365 ** 0.5)) * 100
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Maximum drawdown
        peak = self.daily_values[0][1]
        max_drawdown = 0.0
        
        for timestamp, value in self.daily_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Total return
        initial_value = self.daily_values[0][1]
        total_return = ((current_value - initial_value) / initial_value) * 100
        
        return {
            'current_value': current_value,
            'initial_value': initial_value,
            'total_return_percent': total_return,
            'annual_return_percent': annual_return,
            'annual_volatility_percent': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_percent': max_drawdown * 100,
            'days_tracked': len(self.daily_values),
            'avg_daily_return_percent': avg_daily_return * 100,
            'win_rate_days': sum(1 for r in daily_returns if r > 0) / len(daily_returns) * 100,
            'best_day_return': max(daily_returns) * 100,
            'worst_day_return': min(daily_returns) * 100
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        current_allocations = self.get_current_allocations()
        risk_status = self.check_risk_limits()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_value_sol': self.portfolio.get_portfolio_value(self.price_feed) if self.price_feed else 0,
            'sol_balance': self.portfolio.sol_balance,
            'positions_count': len(self.portfolio.positions),
            'allocations': current_allocations,
            'risk_status': risk_status,
            'performance': self.portfolio.get_performance_stats(self.price_feed),
            'config': {
                'max_positions': self.config.max_positions,
                'max_position_percent': self.config.max_position_percent,
                'rebalance_threshold': self.config.rebalance_threshold,
                'target_allocations': self.config.target_allocations
            }
        }
        
        # Add portfolio metrics if available
        try:
            summary['portfolio_metrics'] = self.calculate_portfolio_metrics()
        except Exception as e:
            logger.warning(f"Could not calculate portfolio metrics: {e}")
        
        return summary
    
    def get_rebalance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent rebalancing history"""
        return self.rebalance_history[-limit:] if self.rebalance_history else []