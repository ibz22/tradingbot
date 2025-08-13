"""
Unified Risk Management System
==============================

Comprehensive risk management for both traditional and Solana assets.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for a position or portfolio"""
    value_at_risk: Decimal  # VaR
    max_drawdown: Decimal
    sharpe_ratio: float
    beta: float
    correlation: float
    volatility: float
    exposure: Decimal


@dataclass
class PositionRisk:
    """Risk assessment for a single position"""
    symbol: str
    asset_type: str  # 'stock', 'crypto', 'commodity'
    position_size: Decimal
    current_value: Decimal
    risk_score: float  # 0-100
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    max_position_pct: float = 0.05  # Max 5% per position
    warnings: List[str] = field(default_factory=list)


@dataclass 
class PortfolioRisk:
    """Overall portfolio risk assessment"""
    total_value: Decimal
    cash_available: Decimal
    total_exposure: Decimal
    risk_score: float  # 0-100
    traditional_allocation: float  # Percentage in traditional assets
    crypto_allocation: float  # Percentage in crypto
    diversification_score: float  # 0-100
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class UnifiedRiskManager:
    """
    Unified risk management across traditional and Solana assets
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize unified risk manager
        
        Args:
            config: Risk management configuration
        """
        self.config = config or {}
        
        # Default risk parameters
        self.risk_params = {
            # Portfolio level
            'max_portfolio_risk': 0.20,  # Max 20% portfolio at risk
            'max_daily_loss': 0.05,  # Max 5% daily loss
            'max_crypto_allocation': 0.40,  # Max 40% in crypto
            'min_cash_reserve': 0.10,  # Min 10% cash
            
            # Position level
            'max_position_size': 0.10,  # Max 10% per position
            'max_correlated_exposure': 0.30,  # Max 30% in correlated assets
            'default_stop_loss': 0.02,  # 2% stop loss
            
            # Asset class specific
            'stock_max_leverage': 2.0,
            'crypto_max_leverage': 1.0,  # No leverage for crypto
            'commodity_max_position': 0.15,
            
            # Halal compliance
            'require_halal_compliance': True,
            'max_questionable_allocation': 0.0  # 0% in questionable assets
        }
        
        if 'risk_params' in self.config:
            self.risk_params.update(self.config['risk_params'])
        
        # Track positions and metrics
        self.positions: Dict[str, PositionRisk] = {}
        self.daily_pnl: List[Tuple[datetime, Decimal]] = []
        self.risk_events: List[Dict] = []
    
    async def evaluate_position_risk(
        self,
        symbol: str,
        asset_type: str,
        position_size: Decimal,
        current_price: Decimal,
        entry_price: Optional[Decimal] = None,
        is_halal: bool = True
    ) -> PositionRisk:
        """
        Evaluate risk for a single position
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset ('stock', 'crypto', 'commodity')
            position_size: Number of shares/tokens
            current_price: Current market price
            entry_price: Entry price (for P&L calculation)
            is_halal: Whether asset is halal compliant
            
        Returns:
            Position risk assessment
        """
        current_value = position_size * current_price
        risk_score = 0.0
        warnings = []
        
        # Check halal compliance
        if self.risk_params['require_halal_compliance'] and not is_halal:
            risk_score = 100.0  # Maximum risk
            warnings.append("Asset is not halal compliant")
        
        # Asset type risk scoring
        base_risk = {
            'stock': 30.0,
            'crypto': 50.0,
            'commodity': 20.0
        }.get(asset_type, 40.0)
        
        risk_score = max(risk_score, base_risk)
        
        # Position concentration risk
        portfolio_value = self._get_portfolio_value()
        if portfolio_value > 0:
            position_pct = float(current_value / portfolio_value)
            
            if position_pct > self.risk_params['max_position_size']:
                risk_score += 20
                warnings.append(f"Position exceeds max size ({position_pct:.1%} > {self.risk_params['max_position_size']:.0%})")
            elif position_pct > self.risk_params['max_position_size'] * 0.8:
                risk_score += 10
                warnings.append(f"Position approaching max size ({position_pct:.1%})")
        
        # Volatility risk (simplified)
        if asset_type == 'crypto':
            risk_score += 10  # Higher volatility
        
        # Calculate stop loss and take profit
        stop_loss = None
        take_profit = None
        
        if entry_price:
            stop_loss = entry_price * Decimal(1 - self.risk_params['default_stop_loss'])
            
            # Risk/reward ratio of 2:1
            risk_amount = entry_price - stop_loss
            take_profit = entry_price + (risk_amount * Decimal('2'))
        
        return PositionRisk(
            symbol=symbol,
            asset_type=asset_type,
            position_size=position_size,
            current_value=current_value,
            risk_score=min(100, risk_score),
            stop_loss=stop_loss,
            take_profit=take_profit,
            warnings=warnings
        )
    
    async def evaluate_portfolio_risk(self) -> PortfolioRisk:
        """
        Evaluate overall portfolio risk
        
        Returns:
            Portfolio risk assessment
        """
        total_value = self._get_portfolio_value()
        cash_available = self._get_cash_available()
        
        # Calculate allocations
        traditional_value = Decimal('0')
        crypto_value = Decimal('0')
        
        for pos in self.positions.values():
            if pos.asset_type in ['stock', 'commodity']:
                traditional_value += pos.current_value
            elif pos.asset_type == 'crypto':
                crypto_value += pos.current_value
        
        total_exposure = traditional_value + crypto_value
        
        traditional_allocation = float(traditional_value / total_value) if total_value > 0 else 0
        crypto_allocation = float(crypto_value / total_value) if total_value > 0 else 0
        
        # Calculate risk score
        risk_score = 0.0
        warnings = []
        recommendations = []
        
        # Check crypto allocation
        if crypto_allocation > self.risk_params['max_crypto_allocation']:
            risk_score += 30
            warnings.append(f"Crypto allocation too high ({crypto_allocation:.1%} > {self.risk_params['max_crypto_allocation']:.0%})")
            recommendations.append("Consider reducing crypto exposure")
        
        # Check cash reserve
        cash_pct = float(cash_available / total_value) if total_value > 0 else 1.0
        if cash_pct < self.risk_params['min_cash_reserve']:
            risk_score += 20
            warnings.append(f"Low cash reserve ({cash_pct:.1%} < {self.risk_params['min_cash_reserve']:.0%})")
            recommendations.append("Increase cash reserves for risk management")
        
        # Calculate diversification score
        diversification_score = self._calculate_diversification_score()
        
        if diversification_score < 50:
            risk_score += 20
            warnings.append("Poor portfolio diversification")
            recommendations.append("Diversify across more assets and sectors")
        
        # Check for concentrated positions
        for pos in self.positions.values():
            if pos.risk_score > 70:
                risk_score += 10
                warnings.append(f"High risk position: {pos.symbol}")
        
        return PortfolioRisk(
            total_value=total_value,
            cash_available=cash_available,
            total_exposure=total_exposure,
            risk_score=min(100, risk_score),
            traditional_allocation=traditional_allocation,
            crypto_allocation=crypto_allocation,
            diversification_score=diversification_score,
            warnings=warnings,
            recommendations=recommendations
        )
    
    async def check_trade_risk(
        self,
        symbol: str,
        asset_type: str,
        trade_type: str,  # 'buy' or 'sell'
        quantity: Decimal,
        price: Decimal,
        is_halal: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Check if a trade meets risk requirements
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            trade_type: Buy or sell
            quantity: Trade quantity
            price: Trade price
            is_halal: Halal compliance status
            
        Returns:
            Tuple of (approved, reasons)
        """
        reasons = []
        approved = True
        
        # Check halal compliance
        if self.risk_params['require_halal_compliance'] and not is_halal:
            approved = False
            reasons.append("Asset is not halal compliant")
            return approved, reasons
        
        trade_value = quantity * price
        portfolio_value = self._get_portfolio_value()
        
        if trade_type == 'buy':
            # Check position sizing
            new_position_value = trade_value
            if symbol in self.positions:
                new_position_value += self.positions[symbol].current_value
            
            position_pct = float(new_position_value / portfolio_value) if portfolio_value > 0 else 1.0
            
            if position_pct > self.risk_params['max_position_size']:
                approved = False
                reasons.append(f"Position would exceed max size ({position_pct:.1%})")
            
            # Check cash available
            cash = self._get_cash_available()
            if trade_value > cash:
                approved = False
                reasons.append("Insufficient cash for trade")
            
            # Check asset class limits
            if asset_type == 'crypto':
                current_crypto = sum(
                    pos.current_value for pos in self.positions.values()
                    if pos.asset_type == 'crypto'
                )
                new_crypto_pct = float((current_crypto + trade_value) / portfolio_value) if portfolio_value > 0 else 1.0
                
                if new_crypto_pct > self.risk_params['max_crypto_allocation']:
                    approved = False
                    reasons.append(f"Would exceed max crypto allocation ({new_crypto_pct:.1%})")
        
        # Check daily loss limit
        daily_loss = self._calculate_daily_loss()
        if daily_loss > self.risk_params['max_daily_loss']:
            approved = False
            reasons.append(f"Daily loss limit reached ({daily_loss:.1%})")
        
        # Log risk event
        self.risk_events.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'trade_type': trade_type,
            'quantity': str(quantity),
            'price': str(price),
            'approved': approved,
            'reasons': reasons
        })
        
        return approved, reasons
    
    def add_position(self, position: PositionRisk):
        """Add or update a position"""
        self.positions[position.symbol] = position
    
    def remove_position(self, symbol: str):
        """Remove a position"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def update_daily_pnl(self, pnl: Decimal):
        """Update daily P&L tracking"""
        self.daily_pnl.append((datetime.now(), pnl))
        
        # Keep last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.daily_pnl = [(dt, val) for dt, val in self.daily_pnl if dt > cutoff]
    
    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value"""
        positions_value = sum(pos.current_value for pos in self.positions.values())
        cash = self._get_cash_available()
        return positions_value + cash
    
    def _get_cash_available(self) -> Decimal:
        """Get available cash (mock implementation)"""
        # In production, this would connect to broker APIs
        return Decimal('10000')  # Mock $10k cash
    
    def _calculate_daily_loss(self) -> float:
        """Calculate today's loss percentage"""
        if not self.daily_pnl:
            return 0.0
        
        today = datetime.now().date()
        today_pnl = [
            pnl for dt, pnl in self.daily_pnl
            if dt.date() == today
        ]
        
        if today_pnl:
            total_loss = sum(pnl for pnl in today_pnl if pnl < 0)
            portfolio_value = self._get_portfolio_value()
            if portfolio_value > 0:
                return abs(float(total_loss / portfolio_value))
        
        return 0.0
    
    def _calculate_diversification_score(self) -> float:
        """Calculate portfolio diversification score (0-100)"""
        if not self.positions:
            return 100.0  # Fully in cash is considered diversified
        
        # Simple diversification based on number of positions and asset types
        num_positions = len(self.positions)
        asset_types = set(pos.asset_type for pos in self.positions.values())
        
        # Score based on number of positions (max at 10+)
        position_score = min(num_positions * 10, 50)
        
        # Score based on asset type diversity
        type_score = len(asset_types) * 25
        
        return min(100, position_score + type_score)
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        portfolio_risk = asyncio.run(self.evaluate_portfolio_risk())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio': {
                'total_value': str(portfolio_risk.total_value),
                'cash_available': str(portfolio_risk.cash_available),
                'total_exposure': str(portfolio_risk.total_exposure),
                'risk_score': portfolio_risk.risk_score,
                'traditional_allocation': portfolio_risk.traditional_allocation,
                'crypto_allocation': portfolio_risk.crypto_allocation,
                'diversification_score': portfolio_risk.diversification_score
            },
            'positions': [
                {
                    'symbol': pos.symbol,
                    'asset_type': pos.asset_type,
                    'value': str(pos.current_value),
                    'risk_score': pos.risk_score,
                    'warnings': pos.warnings
                }
                for pos in self.positions.values()
            ],
            'warnings': portfolio_risk.warnings,
            'recommendations': portfolio_risk.recommendations,
            'recent_events': self.risk_events[-10:]  # Last 10 events
        }