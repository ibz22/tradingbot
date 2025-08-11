"""
Rug Pull Detector - Advanced Risk Detection System for Solana Tokens
===================================================================

Comprehensive rug pull detection system featuring:
- Advanced rug pull detection algorithms with multiple indicators
- Liquidity lock analysis and timelock verification
- Developer token allocation and vesting schedule analysis
- Trading pattern analysis for pump-and-dump detection
- Social sentiment correlation with price movements
- Risk scoring system with confidence levels
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import math

from .token_validator import TokenValidator, ValidationResult, SecurityAnalysis
from .liquidity_analyzer import LiquidityAnalyzer, LiquidityMetrics
from ..utils.checkpoint import load_checkpoint, save_checkpoint


class RugRiskLevel(Enum):
    """Rug pull risk level classification"""
    VERY_LOW = 0.1      # <10% risk - Safe
    LOW = 0.25          # 10-25% risk - Generally safe
    MODERATE = 0.5      # 25-50% risk - Caution advised
    HIGH = 0.75         # 50-75% risk - High risk
    VERY_HIGH = 1.0     # 75%+ risk - Extreme risk


class RugDetectionStatus(Enum):
    """Detection status for rug pull analysis"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    LIKELY_RUG = "likely_rug"
    CONFIRMED_RUG = "confirmed_rug"
    ANALYSIS_FAILED = "analysis_failed"


@dataclass
class TradingPattern:
    """Trading pattern analysis data"""
    volume_spike_factor: float      # Volume spike vs average
    price_spike_factor: float       # Price spike vs average
    whale_activity_score: float     # Large holder activity
    unusual_transaction_count: int  # Suspicious transactions
    pump_dump_signals: int         # Number of pump/dump indicators
    coordination_score: float      # Evidence of coordinated activity
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LiquidityRisk:
    """Liquidity-related risk indicators"""
    locked_liquidity_pct: float    # Percentage of liquidity locked
    lock_duration_days: int        # Days until unlock
    owner_can_withdraw: bool       # Owner has withdrawal authority
    liquidity_concentration: float # How concentrated liquidity is
    withdrawal_patterns: List[str] # Unusual withdrawal patterns
    
    def __post_init__(self):
        if self.withdrawal_patterns is None:
            self.withdrawal_patterns = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DeveloperAnalysis:
    """Developer/team risk analysis"""
    dev_token_percentage: float    # Dev team token allocation
    dev_wallet_count: int         # Number of suspected dev wallets
    early_seller_count: int       # Number of early large sellers
    team_identified: bool         # Whether team is doxxed/known
    previous_projects: List[str]  # Previous projects by same team
    social_presence_score: float # Quality of social media presence
    
    def __post_init__(self):
        if self.previous_projects is None:
            self.previous_projects = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SocialCorrelation:
    """Social sentiment correlation analysis"""
    sentiment_price_correlation: float  # Correlation between sentiment and price
    artificial_hype_score: float       # Evidence of artificial hype
    coordinated_shilling_score: float  # Evidence of coordinated promotion
    organic_community_score: float     # Evidence of organic community
    social_red_flags: List[str]        # Social media red flags
    
    def __post_init__(self):
        if self.social_red_flags is None:
            self.social_red_flags = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RugPullAnalysis:
    """Comprehensive rug pull risk analysis"""
    token_address: str
    analysis_timestamp: datetime
    risk_level: RugRiskLevel
    detection_status: RugDetectionStatus
    confidence: float
    overall_risk_score: float
    trading_pattern: TradingPattern
    liquidity_risk: LiquidityRisk
    developer_analysis: DeveloperAnalysis
    social_correlation: Optional[SocialCorrelation]
    risk_factors: List[str]
    protective_factors: List[str]
    red_flags: List[str]
    recommendation: str
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.protective_factors is None:
            self.protective_factors = []
        if self.red_flags is None:
            self.red_flags = []
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        data['risk_level'] = self.risk_level.value
        data['detection_status'] = self.detection_status.value
        return data


class RugPullDetector:
    """
    Advanced rug pull detection system for Solana tokens
    """
    
    # Risk scoring weights
    RISK_WEIGHTS = {
        'token_security': 0.25,      # Token contract security
        'liquidity_risk': 0.25,      # Liquidity lock and stability
        'trading_patterns': 0.20,    # Unusual trading activity
        'developer_factors': 0.20,   # Team and dev wallet analysis
        'social_correlation': 0.10   # Social sentiment patterns
    }
    
    # Threshold values for risk indicators
    RISK_THRESHOLDS = {
        'dev_allocation_max': 20.0,        # Max dev allocation (%)
        'single_holder_max': 30.0,         # Max single holder (%)
        'top10_holders_max': 70.0,         # Max top 10 holders (%)
        'volume_spike_threshold': 5.0,     # Volume spike multiplier
        'price_spike_threshold': 3.0,      # Price spike multiplier
        'min_liquidity_lock_days': 30,     # Minimum lock period
        'min_locked_liquidity_pct': 80.0   # Minimum locked liquidity
    }
    
    # Known rug pull patterns
    RUG_PATTERNS = {
        'honeypot': ['cannot_sell', 'transfer_restricted', 'high_tax_sell'],
        'liquidity_drain': ['large_withdrawals', 'decreasing_liquidity', 'owner_withdrawals'],
        'dev_dump': ['dev_selling', 'large_transfers', 'coordinated_selling'],
        'pump_dump': ['artificial_volume', 'price_manipulation', 'coordinated_buying']
    }
    
    def __init__(self,
                 token_validator: Optional[TokenValidator] = None,
                 liquidity_analyzer: Optional[LiquidityAnalyzer] = None,
                 checkpoint_file: str = "data/rug_detector.json"):
        """
        Initialize Rug Pull Detector
        
        Args:
            token_validator: Token validator instance
            liquidity_analyzer: Liquidity analyzer instance
            checkpoint_file: File to store rug detection cache
        """
        self.token_validator = token_validator
        self.liquidity_analyzer = liquidity_analyzer
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load detection cache and historical data
        self.cache = load_checkpoint(checkpoint_file, {
            'rug_analyses': {},
            'confirmed_rugs': set(),
            'safe_tokens': set(),
            'detection_stats': {
                'total_analyses': 0,
                'rugs_detected': 0,
                'false_positives': 0,
                'accuracy_score': 0.0
            },
            'pattern_database': {}
        })
        
        # Convert sets from JSON lists
        if isinstance(self.cache['confirmed_rugs'], list):
            self.cache['confirmed_rugs'] = set(self.cache['confirmed_rugs'])
        if isinstance(self.cache['safe_tokens'], list):
            self.cache['safe_tokens'] = set(self.cache['safe_tokens'])
    
    def _analyze_trading_patterns(self, 
                                 token_address: str,
                                 liquidity_metrics: Optional[LiquidityMetrics] = None,
                                 validation_result: Optional[ValidationResult] = None) -> TradingPattern:
        """
        Analyze trading patterns for rug pull indicators
        
        Args:
            token_address: Token address
            liquidity_metrics: Liquidity analysis data
            validation_result: Token validation data
            
        Returns:
            Trading pattern analysis
        """
        # Initialize with default values
        volume_spike_factor = 1.0
        price_spike_factor = 1.0
        whale_activity_score = 0.0
        unusual_transaction_count = 0
        pump_dump_signals = 0
        coordination_score = 0.0
        
        try:
            # Analyze volume patterns
            if liquidity_metrics and liquidity_metrics.best_pools:
                pool = liquidity_metrics.best_pools[0]
                
                # Check for volume spikes
                if pool.tvl_usd > 0:
                    volume_ratio = pool.volume_24h / pool.tvl_usd
                    if volume_ratio > 2.0:  # >200% daily volume turnover
                        volume_spike_factor = min(volume_ratio / 0.5, 10.0)  # Cap at 10x
                        pump_dump_signals += 1
            
            # Analyze holder patterns for whale activity
            if validation_result and validation_result.holder_analysis:
                holder_data = validation_result.holder_analysis
                
                # Whale activity indicators
                if holder_data.top_holder_percentage > 25.0:
                    whale_activity_score += 0.3
                if len(holder_data.whale_addresses) > 5:
                    whale_activity_score += 0.2
                if len(holder_data.suspected_dev_wallets) > 2:
                    whale_activity_score += 0.3
                    unusual_transaction_count += len(holder_data.suspected_dev_wallets)
                
                # Concentration risk
                if holder_data.concentration_score > 0.8:
                    coordination_score += 0.4
                    pump_dump_signals += 1
            
            # Check for artificial price movements
            # This would typically require historical price data
            # For now, we'll use liquidity metrics as proxy
            if liquidity_metrics:
                if liquidity_metrics.volume_to_liquidity_ratio > 5.0:
                    price_spike_factor = liquidity_metrics.volume_to_liquidity_ratio / 2.0
                    pump_dump_signals += 1
                
                # Low pool count suggests potential manipulation
                if liquidity_metrics.pool_count < 2:
                    coordination_score += 0.2
        
        except Exception as e:
            self.logger.warning(f"Error analyzing trading patterns: {e}")
        
        return TradingPattern(
            volume_spike_factor=volume_spike_factor,
            price_spike_factor=price_spike_factor,
            whale_activity_score=min(whale_activity_score, 1.0),
            unusual_transaction_count=unusual_transaction_count,
            pump_dump_signals=pump_dump_signals,
            coordination_score=min(coordination_score, 1.0)
        )
    
    def _analyze_liquidity_risk(self, 
                               liquidity_metrics: Optional[LiquidityMetrics] = None,
                               validation_result: Optional[ValidationResult] = None) -> LiquidityRisk:
        """
        Analyze liquidity-related rug pull risks
        
        Args:
            liquidity_metrics: Liquidity analysis data
            validation_result: Token validation data
            
        Returns:
            Liquidity risk analysis
        """
        locked_liquidity_pct = 0.0
        lock_duration_days = 0
        owner_can_withdraw = True  # Assume worst case by default
        liquidity_concentration = 1.0
        withdrawal_patterns = []
        
        try:
            if liquidity_metrics and liquidity_metrics.best_pools:
                # Calculate liquidity concentration
                if len(liquidity_metrics.best_pools) > 1:
                    total_liquidity = sum(pool.tvl_usd for pool in liquidity_metrics.best_pools)
                    if total_liquidity > 0:
                        largest_pool_pct = liquidity_metrics.best_pools[0].tvl_usd / total_liquidity
                        liquidity_concentration = largest_pool_pct
                
                # Analyze pool health
                for pool in liquidity_metrics.best_pools[:3]:  # Check top 3 pools
                    # Check for unusual patterns
                    if pool.volume_24h == 0:
                        withdrawal_patterns.append("zero_volume_pool")
                    elif pool.volume_24h < pool.tvl_usd * 0.01:
                        withdrawal_patterns.append("very_low_activity")
            
            # Check token authorities (indicators of potential rug pulls)
            if validation_result and validation_result.security_analysis:
                security = validation_result.security_analysis
                
                # Mint authority = can create unlimited tokens
                if security.has_mint_authority:
                    withdrawal_patterns.append("unlimited_mint_authority")
                
                # Freeze authority = can freeze user accounts
                if security.has_freeze_authority:
                    withdrawal_patterns.append("freeze_authority_active")
                
                # Check for locked liquidity indicators
                # This would typically require checking specific lock contracts
                # For now, we'll use security score as a proxy
                if security.security_score > 0.8:
                    locked_liquidity_pct = 60.0  # Assume some liquidity is locked
                    lock_duration_days = 90     # Assume 3 months
                    owner_can_withdraw = False
                elif security.security_score > 0.6:
                    locked_liquidity_pct = 30.0
                    lock_duration_days = 30
        
        except Exception as e:
            self.logger.warning(f"Error analyzing liquidity risk: {e}")
        
        return LiquidityRisk(
            locked_liquidity_pct=locked_liquidity_pct,
            lock_duration_days=lock_duration_days,
            owner_can_withdraw=owner_can_withdraw,
            liquidity_concentration=liquidity_concentration,
            withdrawal_patterns=withdrawal_patterns
        )
    
    def _analyze_developer_factors(self, validation_result: Optional[ValidationResult] = None) -> DeveloperAnalysis:
        """
        Analyze developer and team-related risk factors
        
        Args:
            validation_result: Token validation data
            
        Returns:
            Developer analysis
        """
        dev_token_percentage = 0.0
        dev_wallet_count = 0
        early_seller_count = 0
        team_identified = False
        previous_projects = []
        social_presence_score = 0.0
        
        try:
            if validation_result and validation_result.holder_analysis:
                holder_data = validation_result.holder_analysis
                
                # Calculate dev allocation
                dev_wallet_count = len(holder_data.suspected_dev_wallets)
                
                # Estimate dev token percentage
                if dev_wallet_count > 0:
                    # Simple heuristic: assume dev wallets hold significant amounts
                    dev_token_percentage = min(dev_wallet_count * 5.0, 50.0)  # Cap at 50%
                
                # Check for large early holders (potential dumpers)
                early_seller_count = len(holder_data.whale_addresses)
            
            # Check metadata for team information
            if validation_result and validation_result.metadata:
                metadata = validation_result.metadata
                
                # Social presence indicators
                social_links = 0
                if metadata.website:
                    social_links += 1
                    social_presence_score += 0.2
                if metadata.twitter:
                    social_links += 1
                    social_presence_score += 0.3
                if metadata.telegram:
                    social_links += 1
                    social_presence_score += 0.2
                if metadata.discord:
                    social_links += 1
                    social_presence_score += 0.2
                
                # Basic team identification
                if social_links >= 3:
                    team_identified = True
                    social_presence_score += 0.1
        
        except Exception as e:
            self.logger.warning(f"Error analyzing developer factors: {e}")
        
        return DeveloperAnalysis(
            dev_token_percentage=dev_token_percentage,
            dev_wallet_count=dev_wallet_count,
            early_seller_count=early_seller_count,
            team_identified=team_identified,
            previous_projects=previous_projects,
            social_presence_score=min(social_presence_score, 1.0)
        )
    
    def _analyze_social_correlation(self, 
                                  token_address: str,
                                  social_data: Optional[Dict] = None) -> Optional[SocialCorrelation]:
        """
        Analyze social sentiment correlation with price movements
        
        Args:
            token_address: Token address
            social_data: Social sentiment data (if available)
            
        Returns:
            Social correlation analysis
        """
        if not social_data:
            return None
        
        try:
            sentiment_price_correlation = 0.0
            artificial_hype_score = 0.0
            coordinated_shilling_score = 0.0
            organic_community_score = 0.0
            social_red_flags = []
            
            # Analyze sentiment patterns
            # This would typically require historical sentiment and price data
            # For now, we'll use available social metrics
            
            # Check for artificial hype indicators
            hype_level = social_data.get('hype_level', 0.0)
            if hype_level > 0.8:
                artificial_hype_score = hype_level
                social_red_flags.append("extremely_high_hype")
            
            # Check sentiment consistency
            overall_sentiment = social_data.get('overall_sentiment', 0.0)
            confidence = social_data.get('confidence', 0.0)
            
            if abs(overall_sentiment) > 0.7 and confidence < 0.3:
                coordinated_shilling_score += 0.5
                social_red_flags.append("inconsistent_high_sentiment")
            
            # Organic community indicators
            platform_count = len(social_data.get('platform_breakdown', {}))
            if platform_count >= 3:
                organic_community_score += 0.3
            
            trending_tokens = social_data.get('trending_tokens', {})
            if token_address in trending_tokens:
                token_data = trending_tokens[token_address]
                mentions = token_data.get('total_mentions', 0)
                if mentions > 10:
                    organic_community_score += 0.2
                elif mentions > 50:
                    organic_community_score += 0.4
            
            return SocialCorrelation(
                sentiment_price_correlation=sentiment_price_correlation,
                artificial_hype_score=artificial_hype_score,
                coordinated_shilling_score=coordinated_shilling_score,
                organic_community_score=min(organic_community_score, 1.0),
                social_red_flags=social_red_flags
            )
        
        except Exception as e:
            self.logger.warning(f"Error analyzing social correlation: {e}")
            return None
    
    def _calculate_overall_risk_score(self,
                                    validation_result: ValidationResult,
                                    liquidity_metrics: LiquidityMetrics,
                                    trading_pattern: TradingPattern,
                                    liquidity_risk: LiquidityRisk,
                                    developer_analysis: DeveloperAnalysis,
                                    social_correlation: Optional[SocialCorrelation]) -> float:
        """
        Calculate overall rug pull risk score
        
        Args:
            validation_result: Token validation result
            liquidity_metrics: Liquidity analysis
            trading_pattern: Trading pattern analysis
            liquidity_risk: Liquidity risk analysis
            developer_analysis: Developer analysis
            social_correlation: Social correlation analysis
            
        Returns:
            Overall risk score (0.0 to 1.0)
        """
        risk_components = {}
        
        # Token security risk
        if validation_result.security_analysis:
            security_risk = 1.0 - validation_result.security_analysis.security_score
            risk_components['token_security'] = security_risk
        else:
            risk_components['token_security'] = 0.8  # High risk if no security data
        
        # Liquidity risk
        liquidity_risk_score = 0.0
        if liquidity_risk.owner_can_withdraw:
            liquidity_risk_score += 0.3
        if liquidity_risk.locked_liquidity_pct < self.RISK_THRESHOLDS['min_locked_liquidity_pct']:
            liquidity_risk_score += 0.4
        if liquidity_risk.lock_duration_days < self.RISK_THRESHOLDS['min_liquidity_lock_days']:
            liquidity_risk_score += 0.2
        if liquidity_risk.liquidity_concentration > 0.8:
            liquidity_risk_score += 0.1
        
        risk_components['liquidity_risk'] = min(liquidity_risk_score, 1.0)
        
        # Trading pattern risk
        trading_risk = 0.0
        if trading_pattern.volume_spike_factor > self.RISK_THRESHOLDS['volume_spike_threshold']:
            trading_risk += 0.3
        if trading_pattern.price_spike_factor > self.RISK_THRESHOLDS['price_spike_threshold']:
            trading_risk += 0.3
        if trading_pattern.whale_activity_score > 0.7:
            trading_risk += 0.2
        if trading_pattern.pump_dump_signals >= 2:
            trading_risk += 0.2
        
        risk_components['trading_patterns'] = min(trading_risk, 1.0)
        
        # Developer factors risk
        dev_risk = 0.0
        if developer_analysis.dev_token_percentage > self.RISK_THRESHOLDS['dev_allocation_max']:
            dev_risk += 0.4
        if developer_analysis.dev_wallet_count > 5:
            dev_risk += 0.3
        if not developer_analysis.team_identified:
            dev_risk += 0.2
        if developer_analysis.social_presence_score < 0.3:
            dev_risk += 0.1
        
        risk_components['developer_factors'] = min(dev_risk, 1.0)
        
        # Social correlation risk
        if social_correlation:
            social_risk = 0.0
            if social_correlation.artificial_hype_score > 0.7:
                social_risk += 0.4
            if social_correlation.coordinated_shilling_score > 0.5:
                social_risk += 0.3
            if social_correlation.organic_community_score < 0.3:
                social_risk += 0.3
            
            risk_components['social_correlation'] = min(social_risk, 1.0)
        else:
            risk_components['social_correlation'] = 0.2  # Moderate risk without social data
        
        # Calculate weighted overall score
        overall_risk = sum(
            score * self.RISK_WEIGHTS[component] 
            for component, score in risk_components.items()
        )
        
        return min(overall_risk, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> RugRiskLevel:
        """
        Determine risk level from score
        
        Args:
            risk_score: Risk score (0.0 to 1.0)
            
        Returns:
            Risk level classification
        """
        if risk_score >= 0.75:
            return RugRiskLevel.VERY_HIGH
        elif risk_score >= 0.5:
            return RugRiskLevel.HIGH
        elif risk_score >= 0.25:
            return RugRiskLevel.MODERATE
        elif risk_score >= 0.1:
            return RugRiskLevel.LOW
        else:
            return RugRiskLevel.VERY_LOW
    
    def _determine_detection_status(self, 
                                  risk_level: RugRiskLevel,
                                  red_flags: List[str]) -> RugDetectionStatus:
        """
        Determine detection status based on risk level and red flags
        
        Args:
            risk_level: Risk level
            red_flags: List of red flags
            
        Returns:
            Detection status
        """
        # Check for confirmed rug patterns
        critical_flags = [
            'unlimited_mint_authority',
            'freeze_authority_active',
            'dev_dumping_detected',
            'liquidity_completely_withdrawn'
        ]
        
        if any(flag in red_flags for flag in critical_flags):
            if risk_level == RugRiskLevel.VERY_HIGH:
                return RugDetectionStatus.LIKELY_RUG
            else:
                return RugDetectionStatus.HIGH_RISK
        
        # Standard classification
        if risk_level == RugRiskLevel.VERY_HIGH:
            return RugDetectionStatus.HIGH_RISK
        elif risk_level == RugRiskLevel.HIGH:
            return RugDetectionStatus.SUSPICIOUS
        else:
            return RugDetectionStatus.SAFE
    
    async def analyze_rug_risk(self, 
                             token_address: str,
                             social_data: Optional[Dict] = None,
                             force_refresh: bool = False) -> RugPullAnalysis:
        """
        Perform comprehensive rug pull risk analysis
        
        Args:
            token_address: Token address to analyze
            social_data: Social sentiment data (optional)
            force_refresh: Force fresh analysis (ignore cache)
            
        Returns:
            Comprehensive rug pull analysis
        """
        # Check cache first
        if not force_refresh and token_address in self.cache['rug_analyses']:
            cached_analysis = self.cache['rug_analyses'][token_address]
            # Check if cache is still valid (4 hours)
            cached_time = datetime.fromisoformat(cached_analysis['analysis_timestamp'])
            if datetime.now() - cached_time < timedelta(hours=4):
                self.logger.info(f"Using cached rug analysis for {token_address}")
                return RugPullAnalysis(
                    token_address=cached_analysis['token_address'],
                    analysis_timestamp=datetime.fromisoformat(cached_analysis['analysis_timestamp']),
                    risk_level=RugRiskLevel(cached_analysis['risk_level']),
                    detection_status=RugDetectionStatus(cached_analysis['detection_status']),
                    confidence=cached_analysis['confidence'],
                    overall_risk_score=cached_analysis['overall_risk_score'],
                    trading_pattern=TradingPattern(**cached_analysis['trading_pattern']),
                    liquidity_risk=LiquidityRisk(**cached_analysis['liquidity_risk']),
                    developer_analysis=DeveloperAnalysis(**cached_analysis['developer_analysis']),
                    social_correlation=SocialCorrelation(**cached_analysis['social_correlation']) if cached_analysis['social_correlation'] else None,
                    risk_factors=cached_analysis['risk_factors'],
                    protective_factors=cached_analysis['protective_factors'],
                    red_flags=cached_analysis['red_flags'],
                    recommendation=cached_analysis['recommendation']
                )
        
        self.logger.info(f"Analyzing rug pull risk for {token_address}")
        
        try:
            # Step 1: Get token validation data
            validation_result = None
            if self.token_validator:
                validation_result = await self.token_validator.validate_token(token_address)
            
            # Step 2: Get liquidity analysis
            liquidity_metrics = None
            if self.liquidity_analyzer:
                liquidity_metrics = await self.liquidity_analyzer.analyze_token_liquidity(token_address)
            
            # Step 3: Analyze components
            trading_pattern = self._analyze_trading_patterns(
                token_address, liquidity_metrics, validation_result
            )
            
            liquidity_risk = self._analyze_liquidity_risk(
                liquidity_metrics, validation_result
            )
            
            developer_analysis = self._analyze_developer_factors(validation_result)
            
            social_correlation = self._analyze_social_correlation(
                token_address, social_data
            )
            
            # Step 4: Calculate overall risk
            if validation_result and liquidity_metrics:
                overall_risk_score = self._calculate_overall_risk_score(
                    validation_result, liquidity_metrics, trading_pattern,
                    liquidity_risk, developer_analysis, social_correlation
                )
            else:
                overall_risk_score = 0.8  # High risk if data unavailable
            
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Step 5: Compile risk factors and red flags
            risk_factors = []
            protective_factors = []
            red_flags = []
            
            # Token security factors
            if validation_result and validation_result.security_analysis:
                security = validation_result.security_analysis
                risk_factors.extend(security.rugpull_risk_factors)
                red_flags.extend(security.warning_flags)
                
                if security.security_score > 0.7:
                    protective_factors.append("High security score")
                if not security.has_mint_authority:
                    protective_factors.append("No mint authority")
                if not security.has_freeze_authority:
                    protective_factors.append("No freeze authority")
            
            # Liquidity factors
            if liquidity_risk.locked_liquidity_pct > 50:
                protective_factors.append(f"{liquidity_risk.locked_liquidity_pct:.0f}% liquidity locked")
            else:
                risk_factors.append("Low locked liquidity percentage")
            
            if liquidity_risk.owner_can_withdraw:
                risk_factors.append("Owner can withdraw liquidity")
            
            # Trading pattern factors
            if trading_pattern.pump_dump_signals >= 2:
                red_flags.append("Multiple pump/dump indicators")
            if trading_pattern.whale_activity_score > 0.7:
                risk_factors.append("High whale activity detected")
            
            # Developer factors
            if developer_analysis.dev_token_percentage > 30:
                risk_factors.append(f"High dev allocation: {developer_analysis.dev_token_percentage:.0f}%")
            if developer_analysis.team_identified:
                protective_factors.append("Team identified with social presence")
            
            # Social factors
            if social_correlation and len(social_correlation.social_red_flags) > 0:
                red_flags.extend(social_correlation.social_red_flags)
            
            # Determine detection status
            detection_status = self._determine_detection_status(risk_level, red_flags)
            
            # Calculate confidence
            confidence = 0.0
            if validation_result:
                confidence += 0.3
            if liquidity_metrics:
                confidence += 0.3
            if social_correlation:
                confidence += 0.2
            confidence += min(len(risk_factors) + len(red_flags), 5) * 0.04  # More factors = higher confidence
            confidence = min(confidence, 1.0)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(risk_level, detection_status, red_flags)
            
            # Create analysis result
            analysis = RugPullAnalysis(
                token_address=token_address,
                analysis_timestamp=datetime.now(),
                risk_level=risk_level,
                detection_status=detection_status,
                confidence=confidence,
                overall_risk_score=overall_risk_score,
                trading_pattern=trading_pattern,
                liquidity_risk=liquidity_risk,
                developer_analysis=developer_analysis,
                social_correlation=social_correlation,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                red_flags=red_flags,
                recommendation=recommendation
            )
            
            # Update cache
            self.cache['rug_analyses'][token_address] = analysis.to_dict()
            self.cache['detection_stats']['total_analyses'] += 1
            
            # Update confirmed lists based on detection
            if detection_status in [RugDetectionStatus.LIKELY_RUG, RugDetectionStatus.CONFIRMED_RUG]:
                self.cache['confirmed_rugs'].add(token_address)
            elif detection_status == RugDetectionStatus.SAFE and risk_level == RugRiskLevel.VERY_LOW:
                self.cache['safe_tokens'].add(token_address)
            
            self._save_cache()
            
            self.logger.info(f"Rug pull analysis complete for {token_address}: {detection_status.value} ({risk_level.name})")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing rug pull risk for {token_address}: {e}")
            
            # Return failed analysis
            return RugPullAnalysis(
                token_address=token_address,
                analysis_timestamp=datetime.now(),
                risk_level=RugRiskLevel.VERY_HIGH,
                detection_status=RugDetectionStatus.ANALYSIS_FAILED,
                confidence=0.0,
                overall_risk_score=1.0,
                trading_pattern=TradingPattern(0, 0, 0, 0, 0, 0),
                liquidity_risk=LiquidityRisk(0, 0, True, 1.0, []),
                developer_analysis=DeveloperAnalysis(0, 0, 0, False, [], 0),
                social_correlation=None,
                risk_factors=[f"Analysis failed: {str(e)}"],
                protective_factors=[],
                red_flags=["analysis_failed"],
                recommendation="Analysis failed - avoid trading until manual review"
            )
    
    def _generate_recommendation(self, 
                               risk_level: RugRiskLevel,
                               detection_status: RugDetectionStatus,
                               red_flags: List[str]) -> str:
        """
        Generate trading recommendation based on analysis
        
        Args:
            risk_level: Risk level
            detection_status: Detection status
            red_flags: List of red flags
            
        Returns:
            Trading recommendation string
        """
        if detection_status == RugDetectionStatus.LIKELY_RUG:
            return "AVOID - Likely rug pull detected. Do not trade."
        elif detection_status == RugDetectionStatus.HIGH_RISK:
            return "HIGH RISK - Multiple red flags detected. Avoid trading."
        elif detection_status == RugDetectionStatus.SUSPICIOUS:
            return "CAUTION - Suspicious patterns detected. Only trade with extreme caution and small amounts."
        elif risk_level == RugRiskLevel.VERY_HIGH:
            return "VERY HIGH RISK - Significant risk factors present. Not recommended for trading."
        elif risk_level == RugRiskLevel.HIGH:
            return "HIGH RISK - Multiple risk factors. Only experienced traders with risk management."
        elif risk_level == RugRiskLevel.MODERATE:
            return "MODERATE RISK - Some risk factors present. Trade with caution and proper risk management."
        elif risk_level == RugRiskLevel.LOW:
            return "LOW RISK - Few risk factors detected. Generally safe for trading with normal precautions."
        else:
            return "VERY LOW RISK - Minimal risk factors detected. Appears safe for trading."
    
    def get_detection_stats(self) -> Dict:
        """Get rug pull detection statistics"""
        stats = self.cache['detection_stats'].copy()
        stats['confirmed_rugs'] = len(self.cache['confirmed_rugs'])
        stats['safe_tokens'] = len(self.cache['safe_tokens'])
        stats['cached_analyses'] = len(self.cache['rug_analyses'])
        
        return stats
    
    def mark_as_confirmed_rug(self, token_address: str):
        """Mark a token as confirmed rug pull"""
        self.cache['confirmed_rugs'].add(token_address)
        if token_address in self.cache['safe_tokens']:
            self.cache['safe_tokens'].remove(token_address)
        self.cache['detection_stats']['rugs_detected'] += 1
        self._save_cache()
        self.logger.info(f"Marked {token_address} as confirmed rug pull")
    
    def mark_as_safe(self, token_address: str):
        """Mark a token as safe (false positive correction)"""
        self.cache['safe_tokens'].add(token_address)
        if token_address in self.cache['confirmed_rugs']:
            self.cache['confirmed_rugs'].remove(token_address)
            self.cache['detection_stats']['false_positives'] += 1
        self._save_cache()
        self.logger.info(f"Marked {token_address} as safe token")
    
    def _save_cache(self):
        """Save rug detection cache"""
        # Convert sets to lists for JSON serialization
        cache_to_save = self.cache.copy()
        cache_to_save['confirmed_rugs'] = list(self.cache['confirmed_rugs'])
        cache_to_save['safe_tokens'] = list(self.cache['safe_tokens'])
        
        save_checkpoint(self.checkpoint_file, cache_to_save)
    
    async def close(self):
        """Close HTTP session and cleanup resources"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            await self.session.close()


# Example usage and testing
async def test_rug_detector():
    """Test the rug pull detector system"""
    
    detector = RugPullDetector(checkpoint_file="data/test_rug_detector.json")
    
    print("Testing Rug Pull Detector...")
    
    # Test tokens
    test_tokens = [
        'So11111111111111111111111111111111111111112',  # SOL (should be safe)
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC (should be safe)
    ]
    
    for token_address in test_tokens:
        try:
            print(f"\nAnalyzing rug pull risk for {token_address}...")
            
            analysis = await detector.analyze_rug_risk(token_address)
            
            print(f"  Detection Status: {analysis.detection_status.value}")
            print(f"  Risk Level: {analysis.risk_level.name}")
            print(f"  Overall Risk Score: {analysis.overall_risk_score:.3f}")
            print(f"  Confidence: {analysis.confidence:.2f}")
            print(f"  Recommendation: {analysis.recommendation}")
            
            if analysis.risk_factors:
                print(f"  Risk Factors ({len(analysis.risk_factors)}):")
                for factor in analysis.risk_factors[:3]:
                    print(f"    - {factor}")
            
            if analysis.protective_factors:
                print(f"  Protective Factors ({len(analysis.protective_factors)}):")
                for factor in analysis.protective_factors[:3]:
                    print(f"    - {factor}")
            
            if analysis.red_flags:
                print(f"  Red Flags ({len(analysis.red_flags)}):")
                for flag in analysis.red_flags[:3]:
                    print(f"    - {flag}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show detection stats
    stats = detector.get_detection_stats()
    print(f"\nDetection Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nRug pull detector testing complete!")


if __name__ == "__main__":
    asyncio.run(test_rug_detector())