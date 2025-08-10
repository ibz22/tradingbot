import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import time
from datetime import datetime

from .base_strategy import BaseStrategy, TradeSignal, OrderSide, StrategyConfig

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between DEXes"""
    token_mint: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    profit_percent: float
    volume_available: float
    timestamp: float
    
    @property
    def is_valid(self) -> bool:
        """Check if opportunity is still valid"""
        return (
            self.profit_percent > 0 and
            time.time() - self.timestamp < 30  # Valid for 30 seconds
        )

@dataclass
class ArbitrageConfig(StrategyConfig):
    """Configuration for arbitrage strategy"""
    min_profit_percent: float = 1.0  # Minimum profit % to consider
    min_profit_absolute_sol: float = 0.01  # Minimum absolute profit in SOL
    max_slippage_percent: float = 0.5  # Maximum acceptable slippage
    opportunity_timeout_seconds: int = 30  # How long opportunities are valid
    
    # DEX priorities (higher number = more trusted/liquid)
    dex_priorities: Dict[str, int] = field(default_factory=lambda: {
        "jupiter": 10,
        "raydium": 8,
        "orca": 7,
        "serum": 6
    })
    
    # Gas estimation and fees
    estimated_gas_sol: float = 0.01  # Estimated gas cost per transaction
    jupiter_fee_percent: float = 0.1  # Jupiter fee percentage
    
    # Risk management
    max_single_trade_sol: float = 1.0  # Maximum SOL per arbitrage trade
    min_liquidity_multiple: float = 2.0  # Trade size must be < liquidity / this
    
    # Execution settings
    simultaneous_execution: bool = False  # Execute both legs simultaneously (risky)
    max_execution_time_seconds: int = 60  # Max time to complete arbitrage

class ArbitrageStrategy(BaseStrategy):
    """Arbitrage strategy for Solana DEXes"""
    
    def __init__(self, config: ArbitrageConfig):
        super().__init__("Arbitrage_Strategy", config)
        self.arb_config = config
        
        # Track opportunities and executions
        self.current_opportunities: Dict[str, ArbitrageOpportunity] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # DEX clients (to be injected)
        self.dex_clients: Dict[str, Any] = {}
        
    def add_dex_client(self, dex_name: str, client):
        """Add a DEX client for price discovery"""
        self.dex_clients[dex_name] = client
        logger.info(f"Added {dex_name} client for arbitrage")
    
    async def generate_signals(self, tokens: List[str]) -> List[TradeSignal]:
        """Generate arbitrage signals for given tokens"""
        signals = []
        
        if not self.enabled:
            return signals
        
        # Update opportunities for all tokens
        await self._scan_arbitrage_opportunities(tokens)
        
        # Generate signals from valid opportunities
        for token_mint, opportunity in self.current_opportunities.items():
            if opportunity.is_valid and opportunity.profit_percent >= self.arb_config.min_profit_percent:
                signal = await self._create_arbitrage_signal(opportunity)
                if signal:
                    signals.append(signal)
        
        return signals
    
    async def _scan_arbitrage_opportunities(self, tokens: List[str]):
        """Scan for arbitrage opportunities across DEXes"""
        for token_mint in tokens:
            try:
                # Get prices from all available DEXes
                dex_prices = await self._get_prices_across_dexes(token_mint)
                
                if len(dex_prices) < 2:
                    continue  # Need at least 2 DEXes
                
                # Find best arbitrage opportunity
                opportunity = self._find_best_arbitrage(token_mint, dex_prices)
                
                if opportunity and opportunity.profit_percent >= self.arb_config.min_profit_percent:
                    self.current_opportunities[token_mint] = opportunity
                elif token_mint in self.current_opportunities:
                    # Remove expired/invalid opportunities
                    del self.current_opportunities[token_mint]
                    
            except Exception as e:
                logger.error(f"Error scanning arbitrage for {token_mint}: {e}")
    
    async def _get_prices_across_dexes(self, token_mint: str) -> Dict[str, Dict[str, float]]:
        """Get prices for a token across all DEXes"""
        dex_prices = {}
        
        # Get price from Jupiter (aggregator)
        if "jupiter" in self.dex_clients:
            try:
                jupiter_price = await self._get_jupiter_price(token_mint)
                if jupiter_price:
                    dex_prices["jupiter"] = jupiter_price
            except Exception as e:
                logger.warning(f"Failed to get Jupiter price for {token_mint}: {e}")
        
        # Get prices from individual DEXes
        for dex_name, client in self.dex_clients.items():
            if dex_name == "jupiter":
                continue  # Already handled above
            
            try:
                price_data = await self._get_dex_price(dex_name, client, token_mint)
                if price_data:
                    dex_prices[dex_name] = price_data
            except Exception as e:
                logger.warning(f"Failed to get {dex_name} price for {token_mint}: {e}")
        
        return dex_prices
    
    async def _get_jupiter_price(self, token_mint: str) -> Optional[Dict[str, float]]:
        """Get price data from Jupiter"""
        if not self.jupiter_client:
            return None
        
        try:
            # Use SOL as base currency for comparison
            sol_mint = "So11111111111111111111111111111111111111112"
            amount = 1_000_000_000  # 1 SOL worth
            
            # Get quote for buying the token with SOL
            buy_quote = await self.jupiter_client.quote(sol_mint, token_mint, amount)
            buy_price = float(buy_quote['inAmount']) / float(buy_quote['outAmount'])
            
            # Get quote for selling the token for SOL
            token_amount = int(float(buy_quote['outAmount']))
            sell_quote = await self.jupiter_client.quote(token_mint, sol_mint, token_amount)
            sell_price = float(sell_quote['outAmount']) / float(sell_quote['inAmount'])
            
            return {
                "buy_price": buy_price,
                "sell_price": sell_price,
                "spread": abs(buy_price - sell_price) / min(buy_price, sell_price) * 100,
                "liquidity": min(float(buy_quote['outAmount']), float(sell_quote['inAmount']))
            }
            
        except Exception as e:
            logger.error(f"Error getting Jupiter price for {token_mint}: {e}")
            return None
    
    async def _get_dex_price(self, dex_name: str, client, token_mint: str) -> Optional[Dict[str, float]]:
        """Get price data from a specific DEX"""
        try:
            # This is a placeholder - actual implementation would depend on DEX-specific APIs
            # For now, return None to indicate no price available
            logger.debug(f"Price lookup for {dex_name} not implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"Error getting {dex_name} price for {token_mint}: {e}")
            return None
    
    def _find_best_arbitrage(self, token_mint: str, dex_prices: Dict[str, Dict[str, float]]) -> Optional[ArbitrageOpportunity]:
        """Find the best arbitrage opportunity from price data"""
        if len(dex_prices) < 2:
            return None
        
        best_opportunity = None
        max_profit = 0.0
        
        # Compare all pairs of DEXes
        dex_list = list(dex_prices.keys())
        for i in range(len(dex_list)):
            for j in range(i + 1, len(dex_list)):
                dex_a = dex_list[i]
                dex_b = dex_list[j]
                
                # Try both directions
                opportunities = [
                    self._calculate_arbitrage(token_mint, dex_a, dex_b, dex_prices),
                    self._calculate_arbitrage(token_mint, dex_b, dex_a, dex_prices)
                ]
                
                for opp in opportunities:
                    if opp and opp.profit_percent > max_profit:
                        max_profit = opp.profit_percent
                        best_opportunity = opp
        
        return best_opportunity
    
    def _calculate_arbitrage(self, token_mint: str, buy_dex: str, sell_dex: str, 
                           dex_prices: Dict[str, Dict[str, float]]) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity between two DEXes"""
        try:
            buy_data = dex_prices.get(buy_dex)
            sell_data = dex_prices.get(sell_dex)
            
            if not buy_data or not sell_data:
                return None
            
            buy_price = buy_data.get('buy_price')
            sell_price = sell_data.get('sell_price')
            
            if not buy_price or not sell_price:
                return None
            
            # Calculate gross profit
            if sell_price <= buy_price:
                return None  # No profit opportunity
            
            gross_profit_percent = ((sell_price - buy_price) / buy_price) * 100
            
            # Account for fees and gas
            total_fees_percent = (
                self.arb_config.jupiter_fee_percent +  # Jupiter fee
                (self.arb_config.estimated_gas_sol / buy_price) * 100  # Gas cost as %
            )
            
            net_profit_percent = gross_profit_percent - total_fees_percent
            
            if net_profit_percent < self.arb_config.min_profit_percent:
                return None
            
            # Estimate available volume
            buy_liquidity = buy_data.get('liquidity', 0)
            sell_liquidity = sell_data.get('liquidity', 0)
            volume_available = min(buy_liquidity, sell_liquidity) / self.arb_config.min_liquidity_multiple
            
            return ArbitrageOpportunity(
                token_mint=token_mint,
                buy_dex=buy_dex,
                sell_dex=sell_dex,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_percent=net_profit_percent,
                volume_available=volume_available,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error calculating arbitrage between {buy_dex} and {sell_dex}: {e}")
            return None
    
    async def _create_arbitrage_signal(self, opportunity: ArbitrageOpportunity) -> Optional[TradeSignal]:
        """Create trading signal from arbitrage opportunity"""
        
        # Calculate trade size
        max_size_by_config = self.arb_config.max_single_trade_sol
        max_size_by_liquidity = opportunity.volume_available
        
        trade_size = min(max_size_by_config, max_size_by_liquidity)
        
        if trade_size < self.config.min_trade_size:
            return None
        
        # Calculate expected profit
        expected_profit_sol = trade_size * (opportunity.profit_percent / 100)
        
        if expected_profit_sol < self.arb_config.min_profit_absolute_sol:
            return None
        
        # Create signal for the buy side (first leg)
        signal = TradeSignal(
            token_mint=opportunity.token_mint,
            side=OrderSide.BUY,
            size_sol=trade_size,
            confidence=min(0.9, 0.5 + (opportunity.profit_percent / 10)),  # Higher confidence for more profitable opportunities
            strategy=self.name,
            reason=f"Arbitrage: Buy on {opportunity.buy_dex}, sell on {opportunity.sell_dex} (+{opportunity.profit_percent:.2f}%)",
            metadata={
                'arbitrage_type': 'cross_dex',
                'buy_dex': opportunity.buy_dex,
                'sell_dex': opportunity.sell_dex,
                'buy_price': opportunity.buy_price,
                'sell_price': opportunity.sell_price,
                'expected_profit_percent': opportunity.profit_percent,
                'expected_profit_sol': expected_profit_sol,
                'volume_available': opportunity.volume_available,
                'opportunity_timestamp': opportunity.timestamp
            }
        )
        
        return signal
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity, trade_size: float) -> Dict[str, Any]:
        """Execute an arbitrage opportunity"""
        execution_id = f"arb_{int(time.time())}_{opportunity.token_mint[:8]}"
        
        execution_result = {
            'execution_id': execution_id,
            'token_mint': opportunity.token_mint,
            'trade_size': trade_size,
            'expected_profit': opportunity.profit_percent,
            'start_time': time.time(),
            'status': 'started',
            'legs': []
        }
        
        try:
            if self.arb_config.simultaneous_execution:
                # Execute both legs simultaneously (higher risk)
                result = await self._execute_simultaneous_arbitrage(opportunity, trade_size)
            else:
                # Execute legs sequentially (lower risk)
                result = await self._execute_sequential_arbitrage(opportunity, trade_size)
            
            execution_result.update(result)
            execution_result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            execution_result['status'] = 'failed'
            execution_result['error'] = str(e)
        
        finally:
            execution_result['end_time'] = time.time()
            execution_result['duration_seconds'] = execution_result['end_time'] - execution_result['start_time']
            self.execution_history.append(execution_result)
        
        return execution_result
    
    async def _execute_sequential_arbitrage(self, opportunity: ArbitrageOpportunity, trade_size: float) -> Dict[str, Any]:
        """Execute arbitrage legs sequentially"""
        legs = []
        
        # First leg: Buy on cheaper DEX
        buy_result = await self._execute_arbitrage_leg(
            "buy", 
            opportunity.buy_dex, 
            opportunity.token_mint, 
            trade_size,
            opportunity.buy_price
        )
        legs.append(buy_result)
        
        if not buy_result.get('success'):
            raise Exception(f"Buy leg failed: {buy_result.get('error')}")
        
        # Second leg: Sell on more expensive DEX
        tokens_received = buy_result.get('tokens_received', 0)
        if tokens_received == 0:
            raise Exception("No tokens received from buy leg")
        
        sell_result = await self._execute_arbitrage_leg(
            "sell", 
            opportunity.sell_dex, 
            opportunity.token_mint, 
            tokens_received,
            opportunity.sell_price
        )
        legs.append(sell_result)
        
        if not sell_result.get('success'):
            raise Exception(f"Sell leg failed: {sell_result.get('error')}")
        
        # Calculate actual profit
        sol_spent = buy_result.get('sol_amount', trade_size)
        sol_received = sell_result.get('sol_received', 0)
        actual_profit = sol_received - sol_spent
        actual_profit_percent = (actual_profit / sol_spent) * 100 if sol_spent > 0 else 0
        
        return {
            'legs': legs,
            'sol_spent': sol_spent,
            'sol_received': sol_received,
            'actual_profit_sol': actual_profit,
            'actual_profit_percent': actual_profit_percent,
            'success': actual_profit > 0
        }
    
    async def _execute_simultaneous_arbitrage(self, opportunity: ArbitrageOpportunity, trade_size: float) -> Dict[str, Any]:
        """Execute arbitrage legs simultaneously (not recommended for beginners)"""
        # This would require more sophisticated coordination and is riskier
        # For now, fall back to sequential execution
        logger.warning("Simultaneous arbitrage execution not yet implemented, falling back to sequential")
        return await self._execute_sequential_arbitrage(opportunity, trade_size)
    
    async def _execute_arbitrage_leg(self, side: str, dex: str, token_mint: str, 
                                   amount: float, expected_price: float) -> Dict[str, Any]:
        """Execute one leg of an arbitrage trade"""
        leg_result = {
            'side': side,
            'dex': dex,
            'token_mint': token_mint,
            'amount': amount,
            'expected_price': expected_price,
            'timestamp': time.time(),
            'success': False
        }
        
        try:
            # This is a placeholder for actual execution
            # In reality, you would use the specific DEX APIs or Jupiter
            logger.info(f"Executing {side} on {dex} for {token_mint}: {amount}")
            
            # Simulate execution (replace with actual trading logic)
            await asyncio.sleep(0.1)  # Simulate network latency
            
            if side == "buy":
                # Simulate buying tokens with SOL
                tokens_received = amount / expected_price
                leg_result.update({
                    'success': True,
                    'sol_amount': amount,
                    'tokens_received': tokens_received,
                    'actual_price': expected_price
                })
            else:  # sell
                # Simulate selling tokens for SOL
                sol_received = amount * expected_price
                leg_result.update({
                    'success': True,
                    'tokens_sold': amount,
                    'sol_received': sol_received,
                    'actual_price': expected_price
                })
            
        except Exception as e:
            logger.error(f"Arbitrage leg execution failed: {e}")
            leg_result['error'] = str(e)
        
        return leg_result
    
    def get_current_opportunities(self) -> Dict[str, Dict[str, Any]]:
        """Get current arbitrage opportunities"""
        return {
            token: {
                'token_mint': opp.token_mint,
                'buy_dex': opp.buy_dex,
                'sell_dex': opp.sell_dex,
                'buy_price': opp.buy_price,
                'sell_price': opp.sell_price,
                'profit_percent': opp.profit_percent,
                'volume_available': opp.volume_available,
                'age_seconds': time.time() - opp.timestamp,
                'is_valid': opp.is_valid
            }
            for token, opp in self.current_opportunities.items()
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent arbitrage execution history"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get arbitrage performance statistics"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        successful_executions = [e for e in self.execution_history if e.get('status') == 'completed']
        profitable_executions = [e for e in successful_executions if e.get('actual_profit_sol', 0) > 0]
        
        total_profit = sum(e.get('actual_profit_sol', 0) for e in successful_executions)
        total_volume = sum(e.get('trade_size', 0) for e in successful_executions)
        
        return {
            'total_executions': len(self.execution_history),
            'successful_executions': len(successful_executions),
            'profitable_executions': len(profitable_executions),
            'success_rate': len(successful_executions) / len(self.execution_history) * 100,
            'profit_rate': len(profitable_executions) / len(successful_executions) * 100 if successful_executions else 0,
            'total_profit_sol': total_profit,
            'total_volume_sol': total_volume,
            'average_profit_per_trade': total_profit / len(successful_executions) if successful_executions else 0,
            'roi_percent': (total_profit / total_volume * 100) if total_volume > 0 else 0
        }