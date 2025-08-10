"""
Liquidity Analyzer - Comprehensive DEX Liquidity Analysis System
===============================================================

Advanced liquidity analysis system for Solana DEXs including:
- DEX liquidity pool analysis across Jupiter, Raydium, Orca
- Trading volume and depth analysis for feasibility assessment
- Price impact calculation for different trade sizes
- Slippage estimation and optimal trade sizing
- Pool health and stability metrics
- Real-time liquidity monitoring and alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

import aiohttp
import requests

from ..utils.checkpoint import load_checkpoint, save_checkpoint


class LiquidityTier(Enum):
    """Liquidity tier classification"""
    VERY_HIGH = "very_high"    # >$1M liquidity
    HIGH = "high"              # >$500K liquidity
    MODERATE = "moderate"      # >$100K liquidity
    LOW = "low"               # >$10K liquidity
    VERY_LOW = "very_low"     # <$10K liquidity


class TradeFeasibility(Enum):
    """Trade feasibility assessment"""
    EXCELLENT = "excellent"    # <1% slippage for target size
    GOOD = "good"             # 1-3% slippage
    FAIR = "fair"             # 3-5% slippage
    POOR = "poor"             # 5-10% slippage
    UNSUITABLE = "unsuitable" # >10% slippage


@dataclass
class LiquidityPool:
    """Liquidity pool information"""
    pool_address: str
    dex: str
    token_a: str
    token_b: str
    token_a_amount: float
    token_b_amount: float
    tvl_usd: float
    volume_24h: float
    fees_24h: float
    apy: float
    price: float
    pool_type: str
    last_updated: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class PriceImpactAnalysis:
    """Price impact analysis for different trade sizes"""
    trade_size_usd: float
    expected_output: float
    price_impact_pct: float
    slippage_pct: float
    minimum_received: float
    route_info: Dict[str, Any]
    execution_time_ms: float
    gas_estimate: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LiquidityMetrics:
    """Comprehensive liquidity metrics"""
    token_address: str
    total_liquidity_usd: float
    largest_pool_liquidity: float
    pool_count: int
    primary_dex: str
    average_daily_volume: float
    volume_to_liquidity_ratio: float
    liquidity_tier: LiquidityTier
    stability_score: float  # 0-1, higher = more stable
    depth_analysis: Dict[str, float]  # Different trade sizes
    best_pools: List[LiquidityPool]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['liquidity_tier'] = self.liquidity_tier.value
        data['best_pools'] = [pool.to_dict() for pool in self.best_pools]
        return data


@dataclass
class TradingRecommendation:
    """Trading recommendation based on liquidity analysis"""
    token_address: str
    feasibility: TradeFeasibility
    max_trade_size_usd: float
    recommended_trade_size_usd: float
    optimal_dex: str
    optimal_pool: str
    expected_slippage_pct: float
    confidence: float
    warnings: List[str]
    analysis_timestamp: datetime
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['feasibility'] = self.feasibility.value
        data['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return data


class LiquidityAnalyzer:
    """
    Comprehensive liquidity analysis system for Solana DEXs
    """
    
    # DEX API endpoints
    DEX_APIS = {
        'jupiter': 'https://quote-api.jup.ag/v6',
        'raydium': 'https://api.raydium.io/v2',
        'orca': 'https://api.orca.so',
        'dexscreener': 'https://api.dexscreener.com/latest/dex'
    }
    
    # Liquidity thresholds (USD)
    LIQUIDITY_THRESHOLDS = {
        LiquidityTier.VERY_HIGH: 1_000_000,
        LiquidityTier.HIGH: 500_000,
        LiquidityTier.MODERATE: 100_000,
        LiquidityTier.LOW: 10_000,
        LiquidityTier.VERY_LOW: 0
    }
    
    # Trade size scenarios for analysis (USD)
    TRADE_SIZES = [100, 500, 1_000, 5_000, 10_000, 25_000, 50_000, 100_000]
    
    # Slippage thresholds for feasibility
    SLIPPAGE_THRESHOLDS = {
        TradeFeasibility.EXCELLENT: 1.0,
        TradeFeasibility.GOOD: 3.0,
        TradeFeasibility.FAIR: 5.0,
        TradeFeasibility.POOR: 10.0,
        TradeFeasibility.UNSUITABLE: float('inf')
    }
    
    def __init__(self, checkpoint_file: str = "data/liquidity_analyzer.json"):
        """
        Initialize Liquidity Analyzer
        
        Args:
            checkpoint_file: File to store liquidity cache
        """
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load liquidity cache
        self.cache = load_checkpoint(checkpoint_file, {
            'liquidity_data': {},
            'pool_data': {},
            'analysis_history': [],
            'performance_stats': {
                'total_analyses': 0,
                'cache_hits': 0,
                'api_calls': 0,
                'avg_analysis_time': 0.0
            }
        })
        
        # Initialize HTTP session
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'SolanaBot/1.0 LiquidityAnalyzer',
                'Accept': 'application/json'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def _fetch_jupiter_quote(self, 
                                 input_mint: str, 
                                 output_mint: str, 
                                 amount: int) -> Optional[Dict]:
        """
        Fetch quote from Jupiter API
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Amount in smallest token unit
            
        Returns:
            Jupiter quote data
        """
        try:
            session = await self._get_session()
            
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': str(amount),
                'slippageBps': 50  # 0.5% slippage
            }
            
            url = f"{self.DEX_APIS['jupiter']}/quote"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"Jupiter API error {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching Jupiter quote: {e}")
            return None
    
    async def _fetch_dexscreener_data(self, token_address: str) -> Optional[Dict]:
        """
        Fetch token data from DexScreener
        
        Args:
            token_address: Token mint address
            
        Returns:
            DexScreener data
        """
        try:
            session = await self._get_session()
            
            url = f"{self.DEX_APIS['dexscreener']}/tokens/{token_address}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"DexScreener API error {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching DexScreener data: {e}")
            return None
    
    async def _analyze_jupiter_liquidity(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze liquidity through Jupiter aggregator
        
        Args:
            token_address: Token to analyze
            
        Returns:
            Jupiter liquidity analysis
        """
        liquidity_data = {
            'total_pools': 0,
            'total_liquidity': 0.0,
            'price_impacts': {},
            'routes': []
        }
        
        try:
            # Use USDC as base for analysis
            usdc_mint = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            
            # Test different trade sizes
            for trade_size in self.TRADE_SIZES:
                # Convert USD to USDC amount (6 decimals)
                usdc_amount = int(trade_size * 1_000_000)  # $1 = 1,000,000 USDC units
                
                # Get quote for USDC -> Token
                buy_quote = await self._fetch_jupiter_quote(usdc_mint, token_address, usdc_amount)
                
                if buy_quote:
                    out_amount = int(buy_quote.get('outAmount', 0))
                    route_plan = buy_quote.get('routePlan', [])
                    
                    # Calculate price impact
                    if out_amount > 0:
                        # Get reverse quote for accurate price impact calculation
                        sell_quote = await self._fetch_jupiter_quote(token_address, usdc_mint, out_amount)
                        
                        if sell_quote:
                            reverse_out = int(sell_quote.get('outAmount', 0))
                            price_impact = max(0, (trade_size * 1_000_000 - reverse_out) / (trade_size * 1_000_000) * 100)
                            
                            liquidity_data['price_impacts'][trade_size] = {
                                'price_impact_pct': price_impact,
                                'output_amount': out_amount,
                                'route_count': len(route_plan),
                                'primary_dex': route_plan[0].get('swapInfo', {}).get('ammKey', '') if route_plan else ''
                            }
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            return liquidity_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing Jupiter liquidity: {e}")
            return liquidity_data
    
    async def _fetch_pool_data(self, token_address: str) -> List[LiquidityPool]:
        """
        Fetch liquidity pool data from multiple sources
        
        Args:
            token_address: Token address
            
        Returns:
            List of liquidity pools
        """
        pools = []
        
        try:
            # Fetch from DexScreener (covers multiple DEXs)
            dex_data = await self._fetch_dexscreener_data(token_address)
            
            if dex_data and 'pairs' in dex_data:
                for pair_data in dex_data['pairs']:
                    try:
                        # Extract pool information
                        pool = LiquidityPool(
                            pool_address=pair_data.get('pairAddress', ''),
                            dex=pair_data.get('dexId', 'unknown'),
                            token_a=pair_data.get('baseToken', {}).get('address', ''),
                            token_b=pair_data.get('quoteToken', {}).get('address', ''),
                            token_a_amount=float(pair_data.get('liquidity', {}).get('base', 0)),
                            token_b_amount=float(pair_data.get('liquidity', {}).get('quote', 0)),
                            tvl_usd=float(pair_data.get('liquidity', {}).get('usd', 0)),
                            volume_24h=float(pair_data.get('volume', {}).get('h24', 0)),
                            fees_24h=float(pair_data.get('volume', {}).get('h24', 0)) * 0.003,  # Estimate 0.3% fee
                            apy=0.0,  # Would need additional calculation
                            price=float(pair_data.get('priceUsd', 0)),
                            pool_type=pair_data.get('labels', [''])[0] if pair_data.get('labels') else 'standard',
                            last_updated=datetime.now()
                        )
                        
                        # Only include pools with significant liquidity
                        if pool.tvl_usd >= 1000:
                            pools.append(pool)
                            
                    except (ValueError, TypeError, KeyError) as e:
                        self.logger.warning(f"Error parsing pool data: {e}")
                        continue
            
            # Sort pools by TVL
            pools.sort(key=lambda x: x.tvl_usd, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching pool data: {e}")
        
        return pools
    
    def _calculate_stability_score(self, pools: List[LiquidityPool]) -> float:
        """
        Calculate liquidity stability score
        
        Args:
            pools: List of liquidity pools
            
        Returns:
            Stability score (0-1)
        """
        if not pools:
            return 0.0
        
        stability_factors = []
        
        # Factor 1: Number of pools (more pools = more stable)
        pool_factor = min(len(pools) / 5.0, 1.0)  # Max at 5 pools
        stability_factors.append(pool_factor)
        
        # Factor 2: TVL distribution (less concentrated = more stable)
        if len(pools) > 1:
            tvls = [pool.tvl_usd for pool in pools]
            total_tvl = sum(tvls)
            if total_tvl > 0:
                # Calculate concentration (Gini coefficient approximation)
                sorted_tvls = sorted(tvls)
                n = len(sorted_tvls)
                gini_sum = sum((2 * i - n - 1) * tvl for i, tvl in enumerate(sorted_tvls, 1))
                gini = gini_sum / (n * total_tvl)
                concentration_factor = 1 - gini  # Invert so lower concentration = higher score
                stability_factors.append(concentration_factor)
        else:
            stability_factors.append(0.3)  # Single pool is less stable
        
        # Factor 3: Volume to liquidity ratio (balanced is better)
        volume_ratios = []
        for pool in pools[:5]:  # Top 5 pools
            if pool.tvl_usd > 0:
                ratio = pool.volume_24h / pool.tvl_usd
                # Optimal ratio is around 0.1-1.0 (10%-100% daily turnover)
                if 0.1 <= ratio <= 1.0:
                    volume_ratios.append(1.0)
                elif ratio < 0.1:
                    volume_ratios.append(ratio / 0.1)  # Penalize low activity
                else:
                    volume_ratios.append(1.0 / min(ratio, 10.0))  # Penalize excessive activity
        
        if volume_ratios:
            volume_factor = sum(volume_ratios) / len(volume_ratios)
            stability_factors.append(volume_factor)
        
        # Factor 4: DEX diversity (multiple DEXs = more stable)
        unique_dexs = set(pool.dex for pool in pools)
        dex_factor = min(len(unique_dexs) / 3.0, 1.0)  # Max at 3 DEXs
        stability_factors.append(dex_factor)
        
        return sum(stability_factors) / len(stability_factors)
    
    def _determine_liquidity_tier(self, total_liquidity: float) -> LiquidityTier:
        """
        Determine liquidity tier based on total liquidity
        
        Args:
            total_liquidity: Total liquidity in USD
            
        Returns:
            Liquidity tier
        """
        if total_liquidity >= self.LIQUIDITY_THRESHOLDS[LiquidityTier.VERY_HIGH]:
            return LiquidityTier.VERY_HIGH
        elif total_liquidity >= self.LIQUIDITY_THRESHOLDS[LiquidityTier.HIGH]:
            return LiquidityTier.HIGH
        elif total_liquidity >= self.LIQUIDITY_THRESHOLDS[LiquidityTier.MODERATE]:
            return LiquidityTier.MODERATE
        elif total_liquidity >= self.LIQUIDITY_THRESHOLDS[LiquidityTier.LOW]:
            return LiquidityTier.LOW
        else:
            return LiquidityTier.VERY_LOW
    
    async def analyze_token_liquidity(self, token_address: str, force_refresh: bool = False) -> LiquidityMetrics:
        """
        Perform comprehensive liquidity analysis for a token
        
        Args:
            token_address: Token mint address
            force_refresh: Force fresh analysis (ignore cache)
            
        Returns:
            Comprehensive liquidity metrics
        """
        # Check cache first
        if not force_refresh and token_address in self.cache['liquidity_data']:
            cached_data = self.cache['liquidity_data'][token_address]
            # Check if cache is still valid (1 hour)
            cached_time = datetime.fromisoformat(cached_data.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time < timedelta(hours=1):
                self.cache['performance_stats']['cache_hits'] += 1
                self.logger.info(f"Using cached liquidity data for {token_address}")
                
                return LiquidityMetrics(
                    token_address=cached_data['token_address'],
                    total_liquidity_usd=cached_data['total_liquidity_usd'],
                    largest_pool_liquidity=cached_data['largest_pool_liquidity'],
                    pool_count=cached_data['pool_count'],
                    primary_dex=cached_data['primary_dex'],
                    average_daily_volume=cached_data['average_daily_volume'],
                    volume_to_liquidity_ratio=cached_data['volume_to_liquidity_ratio'],
                    liquidity_tier=LiquidityTier(cached_data['liquidity_tier']),
                    stability_score=cached_data['stability_score'],
                    depth_analysis=cached_data['depth_analysis'],
                    best_pools=[LiquidityPool(**pool) for pool in cached_data['best_pools']]
                )
        
        start_time = datetime.now()
        self.logger.info(f"Analyzing liquidity for {token_address}")
        
        try:
            # Step 1: Fetch pool data
            pools = await self._fetch_pool_data(token_address)
            
            if not pools:
                # Return minimal metrics for tokens with no liquidity
                return LiquidityMetrics(
                    token_address=token_address,
                    total_liquidity_usd=0.0,
                    largest_pool_liquidity=0.0,
                    pool_count=0,
                    primary_dex='none',
                    average_daily_volume=0.0,
                    volume_to_liquidity_ratio=0.0,
                    liquidity_tier=LiquidityTier.VERY_LOW,
                    stability_score=0.0,
                    depth_analysis={},
                    best_pools=[]
                )
            
            # Step 2: Calculate aggregate metrics
            total_liquidity = sum(pool.tvl_usd for pool in pools)
            total_volume = sum(pool.volume_24h for pool in pools)
            largest_pool_liquidity = pools[0].tvl_usd if pools else 0.0
            
            # Primary DEX is the one with highest liquidity
            primary_dex = pools[0].dex if pools else 'unknown'
            
            # Volume to liquidity ratio
            volume_to_liquidity_ratio = total_volume / total_liquidity if total_liquidity > 0 else 0.0
            
            # Step 3: Perform depth analysis using Jupiter
            jupiter_data = await self._analyze_jupiter_liquidity(token_address)
            depth_analysis = {}
            
            for trade_size, impact_data in jupiter_data.get('price_impacts', {}).items():
                depth_analysis[f"trade_size_{trade_size}"] = {
                    'price_impact_pct': impact_data['price_impact_pct'],
                    'feasible': impact_data['price_impact_pct'] < 10.0  # <10% impact considered feasible
                }
            
            # Step 4: Calculate stability score
            stability_score = self._calculate_stability_score(pools)
            
            # Step 5: Determine liquidity tier
            liquidity_tier = self._determine_liquidity_tier(total_liquidity)
            
            # Step 6: Select best pools (top 5 by TVL)
            best_pools = pools[:5]
            
            # Create metrics object
            metrics = LiquidityMetrics(
                token_address=token_address,
                total_liquidity_usd=total_liquidity,
                largest_pool_liquidity=largest_pool_liquidity,
                pool_count=len(pools),
                primary_dex=primary_dex,
                average_daily_volume=total_volume,
                volume_to_liquidity_ratio=volume_to_liquidity_ratio,
                liquidity_tier=liquidity_tier,
                stability_score=stability_score,
                depth_analysis=depth_analysis,
                best_pools=best_pools
            )
            
            # Update cache
            metrics_dict = metrics.to_dict()
            metrics_dict['timestamp'] = datetime.now().isoformat()
            self.cache['liquidity_data'][token_address] = metrics_dict
            
            # Update performance stats
            analysis_time = (datetime.now() - start_time).total_seconds()
            self.cache['performance_stats']['total_analyses'] += 1
            self.cache['performance_stats']['api_calls'] += 1
            
            # Update average analysis time
            total_analyses = self.cache['performance_stats']['total_analyses']
            current_avg = self.cache['performance_stats']['avg_analysis_time']
            self.cache['performance_stats']['avg_analysis_time'] = (
                (current_avg * (total_analyses - 1) + analysis_time) / total_analyses
            )
            
            self._save_cache()
            
            self.logger.info(f"Liquidity analysis complete for {token_address}: {liquidity_tier.value} tier, ${total_liquidity:,.0f} TVL")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity for {token_address}: {e}")
            # Return error state
            return LiquidityMetrics(
                token_address=token_address,
                total_liquidity_usd=0.0,
                largest_pool_liquidity=0.0,
                pool_count=0,
                primary_dex='error',
                average_daily_volume=0.0,
                volume_to_liquidity_ratio=0.0,
                liquidity_tier=LiquidityTier.VERY_LOW,
                stability_score=0.0,
                depth_analysis={},
                best_pools=[]
            )
    
    def generate_trading_recommendation(self, 
                                      liquidity_metrics: LiquidityMetrics,
                                      target_trade_size: float = 1000.0) -> TradingRecommendation:
        """
        Generate trading recommendation based on liquidity analysis
        
        Args:
            liquidity_metrics: Liquidity analysis results
            target_trade_size: Target trade size in USD
            
        Returns:
            Trading recommendation
        """
        warnings = []
        
        # Determine feasibility based on liquidity tier and depth analysis
        feasibility = TradeFeasibility.UNSUITABLE
        expected_slippage = 100.0  # Default to very high slippage
        
        # Find the closest trade size in depth analysis
        closest_size = min(
            self.TRADE_SIZES,
            key=lambda x: abs(x - target_trade_size)
        ) if self.TRADE_SIZES else target_trade_size
        
        depth_key = f"trade_size_{closest_size}"
        if depth_key in liquidity_metrics.depth_analysis:
            impact_data = liquidity_metrics.depth_analysis[depth_key]
            expected_slippage = impact_data['price_impact_pct']
            
            # Determine feasibility based on slippage
            for tier, threshold in self.SLIPPAGE_THRESHOLDS.items():
                if expected_slippage <= threshold:
                    feasibility = tier
                    break
        
        # Calculate maximum recommended trade size
        max_trade_size = liquidity_metrics.total_liquidity_usd * 0.1  # 10% of liquidity
        recommended_trade_size = min(target_trade_size, max_trade_size)
        
        # Optimal pool selection
        optimal_pool = liquidity_metrics.best_pools[0] if liquidity_metrics.best_pools else None
        optimal_dex = optimal_pool.dex if optimal_pool else liquidity_metrics.primary_dex
        optimal_pool_address = optimal_pool.pool_address if optimal_pool else ''
        
        # Generate warnings
        if liquidity_metrics.liquidity_tier == LiquidityTier.VERY_LOW:
            warnings.append("Very low liquidity - high slippage expected")
        elif liquidity_metrics.liquidity_tier == LiquidityTier.LOW:
            warnings.append("Low liquidity - moderate to high slippage expected")
        
        if liquidity_metrics.stability_score < 0.5:
            warnings.append("Unstable liquidity - price may be volatile")
        
        if liquidity_metrics.volume_to_liquidity_ratio < 0.05:
            warnings.append("Low trading activity - may be difficult to exit position")
        elif liquidity_metrics.volume_to_liquidity_ratio > 2.0:
            warnings.append("Very high trading activity - possible pump/dump scenario")
        
        if liquidity_metrics.pool_count < 2:
            warnings.append("Limited pool diversity - concentrated liquidity risk")
        
        if target_trade_size > max_trade_size:
            warnings.append(f"Trade size exceeds recommended maximum of ${max_trade_size:,.0f}")
        
        # Calculate confidence based on data quality
        confidence = 0.0
        if liquidity_metrics.pool_count > 0:
            confidence += 0.3
        if liquidity_metrics.total_liquidity_usd > 10000:
            confidence += 0.2
        if liquidity_metrics.stability_score > 0.5:
            confidence += 0.2
        if expected_slippage < 10.0:
            confidence += 0.2
        if len(warnings) < 2:
            confidence += 0.1
        
        confidence = min(confidence, 1.0)
        
        return TradingRecommendation(
            token_address=liquidity_metrics.token_address,
            feasibility=feasibility,
            max_trade_size_usd=max_trade_size,
            recommended_trade_size_usd=recommended_trade_size,
            optimal_dex=optimal_dex,
            optimal_pool=optimal_pool_address,
            expected_slippage_pct=expected_slippage,
            confidence=confidence,
            warnings=warnings,
            analysis_timestamp=datetime.now()
        )
    
    async def batch_analyze_liquidity(self, token_addresses: List[str]) -> Dict[str, LiquidityMetrics]:
        """
        Analyze liquidity for multiple tokens
        
        Args:
            token_addresses: List of token addresses
            
        Returns:
            Dictionary of liquidity metrics by token address
        """
        # Analyze in batches to avoid overwhelming APIs
        batch_size = 5
        results = {}
        
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            
            # Run batch analysis
            tasks = [self.analyze_token_liquidity(address) for address in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for address, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error analyzing liquidity for {address}: {result}")
                    # Create minimal error result
                    results[address] = LiquidityMetrics(
                        token_address=address,
                        total_liquidity_usd=0.0,
                        largest_pool_liquidity=0.0,
                        pool_count=0,
                        primary_dex='error',
                        average_daily_volume=0.0,
                        volume_to_liquidity_ratio=0.0,
                        liquidity_tier=LiquidityTier.VERY_LOW,
                        stability_score=0.0,
                        depth_analysis={},
                        best_pools=[]
                    )
                else:
                    results[address] = result
            
            # Delay between batches
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(2)  # 2 second delay between batches
        
        return results
    
    def get_performance_stats(self) -> Dict:
        """Get analyzer performance statistics"""
        stats = self.cache['performance_stats'].copy()
        stats['cached_tokens'] = len(self.cache['liquidity_data'])
        stats['cache_hit_rate'] = (
            stats['cache_hits'] / max(stats['total_analyses'], 1) * 100
        )
        return stats
    
    def _save_cache(self):
        """Save liquidity cache"""
        save_checkpoint(self.checkpoint_file, self.cache)
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


# Example usage and testing
async def test_liquidity_analyzer():
    """Test the liquidity analyzer system"""
    
    analyzer = LiquidityAnalyzer(checkpoint_file="data/test_liquidity_analyzer.json")
    
    print("Testing Liquidity Analyzer...")
    
    # Test tokens (known liquid tokens on Solana)
    test_tokens = [
        'So11111111111111111111111111111111111111112',  # SOL
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    ]
    
    for token_address in test_tokens:
        try:
            print(f"\nAnalyzing liquidity for {token_address}...")
            
            # Analyze liquidity
            metrics = await analyzer.analyze_token_liquidity(token_address)
            
            print(f"  Liquidity Tier: {metrics.liquidity_tier.value}")
            print(f"  Total Liquidity: ${metrics.total_liquidity_usd:,.0f}")
            print(f"  Pool Count: {metrics.pool_count}")
            print(f"  Primary DEX: {metrics.primary_dex}")
            print(f"  Daily Volume: ${metrics.average_daily_volume:,.0f}")
            print(f"  Stability Score: {metrics.stability_score:.2f}")
            
            # Generate trading recommendation
            recommendation = analyzer.generate_trading_recommendation(metrics, 1000.0)
            print(f"  Trading Feasibility: {recommendation.feasibility.value}")
            print(f"  Expected Slippage: {recommendation.expected_slippage_pct:.2f}%")
            print(f"  Max Trade Size: ${recommendation.max_trade_size_usd:,.0f}")
            print(f"  Confidence: {recommendation.confidence:.2f}")
            
            if recommendation.warnings:
                print(f"  Warnings: {len(recommendation.warnings)}")
                for warning in recommendation.warnings[:2]:
                    print(f"    - {warning}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show performance stats
    stats = analyzer.get_performance_stats()
    print(f"\nAnalyzer Performance:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    await analyzer.close()
    print("\nLiquidity analyzer testing complete!")


if __name__ == "__main__":
    asyncio.run(test_liquidity_analyzer())