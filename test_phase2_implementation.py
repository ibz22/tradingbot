#!/usr/bin/env python3
"""
Comprehensive test suite for Solana trading bot Phase 2 implementation
Tests all trading strategies, portfolio management, risk management, and automation
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Phase 2 imports
from solana_trading.config.solana_config import SolanaConfig, SolanaNetwork
from solana_trading.core.client import SolanaClient
from solana_trading.defi.jupiter import JupiterAggregator
from solana_trading.core.transactions import TransactionBuilder

from solana_trading.market_data.price_feed import PriceFeed
from solana_trading.market_data.technical_analysis import TechnicalAnalyzer

from solana_trading.strategies.dca_strategy import DCAStrategy, DCAConfig
from solana_trading.strategies.momentum_strategy import MomentumStrategy, MomentumConfig
from solana_trading.strategies.arbitrage_strategy import ArbitrageStrategy, ArbitrageConfig

from solana_trading.paper_trading.portfolio import VirtualPortfolio
from solana_trading.portfolio.portfolio_manager import PortfolioManager, PortfolioConfig

from solana_trading.risk.risk_manager import RiskManager, RiskConfig
from solana_trading.automation.trading_engine import TradingEngine, EngineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2TestSuite:
    """Comprehensive test suite for Phase 2 implementation"""
    
    def __init__(self):
        self.config = SolanaConfig.for_network(SolanaNetwork.DEVNET)
        
        # Core components from Phase 1
        self.solana_client = None
        self.jupiter_client = None
        self.transaction_builder = None
        
        # Phase 2 components
        self.price_feed = None
        self.technical_analyzer = None
        self.portfolio = None
        self.portfolio_manager = None
        self.risk_manager = None
        self.trading_engine = None
        
        # Strategies
        self.dca_strategy = None
        self.momentum_strategy = None
        self.arbitrage_strategy = None
        
        # Test results
        self.test_results = {}
        
    async def setup(self):
        """Set up all components for testing"""
        logger.info("Setting up Phase 2 test environment...")
        
        try:
            # Initialize Phase 1 components
            self.solana_client = SolanaClient(
                rpc_endpoint=self.config.get_rpc_endpoint(),
                max_retries=3,
                retry_delay=1.0,
                timeout=10.0
            )
            
            self.jupiter_client = JupiterAggregator(timeout=30.0)
            
            self.transaction_builder = TransactionBuilder(
                solana_client=self.solana_client,
                jupiter_client=self.jupiter_client
            )
            
            # Initialize Phase 2 market data components
            self.price_feed = PriceFeed(
                jupiter_client=self.jupiter_client,
                update_interval=10.0,  # Faster updates for testing
                max_history=100
            )
            
            self.technical_analyzer = TechnicalAnalyzer(
                price_feed=self.price_feed
            )
            
            # Initialize portfolio components
            self.portfolio = VirtualPortfolio(initial_sol_balance=10.0)
            
            portfolio_config = PortfolioConfig(
                max_positions=5,
                max_position_percent=30.0,
                rebalance_threshold=10.0
            )
            
            self.portfolio_manager = PortfolioManager(
                config=portfolio_config,
                portfolio=self.portfolio
            )
            
            # Initialize risk management
            risk_config = RiskConfig(
                max_position_size_sol=1.0,
                max_portfolio_loss_percent=20.0,
                max_daily_loss_percent=10.0
            )
            
            self.risk_manager = RiskManager(risk_config)
            
            # Initialize strategies
            dca_config = DCAConfig(
                purchase_amount=0.1,
                interval_minutes=1,  # Fast for testing
                max_total_investment=2.0,
                target_tokens=["So11111111111111111111111111111111111111112"]  # SOL
            )
            
            self.dca_strategy = DCAStrategy(dca_config)
            
            momentum_config = MomentumConfig(
                strong_momentum_threshold=3.0,
                weak_momentum_threshold=1.0,
                short_window_minutes=5,
                long_window_minutes=15
            )
            
            self.momentum_strategy = MomentumStrategy(momentum_config)
            
            arbitrage_config = ArbitrageConfig(
                min_profit_percent=0.5,
                min_profit_absolute_sol=0.005
            )
            
            self.arbitrage_strategy = ArbitrageStrategy(arbitrage_config)
            
            # Initialize trading engine
            engine_config = EngineConfig(
                max_concurrent_trades=2,
                strategy_update_interval=5,  # Fast for testing
                enable_paper_trading=True
            )
            
            self.trading_engine = TradingEngine(engine_config)
            
            # Wire up dependencies
            self._setup_dependencies()
            
            logger.info("Phase 2 test environment setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            raise
    
    def _setup_dependencies(self):
        """Set up component dependencies"""
        # Portfolio manager dependencies
        self.portfolio_manager.set_dependencies(
            price_feed=self.price_feed,
            risk_manager=self.risk_manager
        )
        
        # Risk manager dependencies
        self.risk_manager.set_dependencies(
            portfolio=self.portfolio,
            price_feed=self.price_feed,
            technical_analyzer=self.technical_analyzer
        )
        
        # Trading engine dependencies
        self.trading_engine.set_dependencies(
            price_feed=self.price_feed,
            portfolio_manager=self.portfolio_manager,
            risk_manager=self.risk_manager,
            technical_analyzer=self.technical_analyzer,
            jupiter_client=self.jupiter_client,
            transaction_builder=self.transaction_builder
        )
        
        # Add strategies to engine
        self.trading_engine.add_strategy(self.dca_strategy)
        self.trading_engine.add_strategy(self.momentum_strategy)
        self.trading_engine.add_strategy(self.arbitrage_strategy)
    
    async def test_market_data_system(self) -> Dict[str, Any]:
        """Test market data and technical analysis system"""
        logger.info("Testing market data system...")
        
        test_result = {
            "test_name": "market_data_system",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Test price feed
            await self.price_feed.start()
            
            # Wait for some data
            await asyncio.sleep(5)
            
            # Check supported tokens
            supported_tokens = self.price_feed.get_supported_tokens()
            test_result["details"]["supported_tokens_count"] = len(supported_tokens)
            
            if not supported_tokens:
                test_result["errors"].append("No supported tokens loaded")
                return test_result
            
            # Test current price retrieval
            test_token = list(supported_tokens.keys())[0]
            current_price = self.price_feed.get_current_price(test_token)
            
            if current_price:
                test_result["details"]["sample_price"] = {
                    "token": test_token,
                    "price": current_price.price,
                    "volume": current_price.volume_24h
                }
            else:
                test_result["errors"].append("Failed to get current price")
                return test_result
            
            # Test technical analysis
            await asyncio.sleep(5)  # Wait for more data
            
            indicators = await self.technical_analyzer.analyze_token(test_token)
            if indicators:
                test_result["details"]["technical_indicators"] = {
                    "token": test_token,
                    "rsi": indicators.rsi_14,
                    "sma_20": indicators.sma_20,
                    "price_momentum_1h": indicators.price_momentum_1h
                }
                
                # Test signal generation
                signals = self.technical_analyzer.generate_signals(indicators)
                test_result["details"]["signals_generated"] = len(signals)
            else:
                test_result["errors"].append("No technical indicators calculated")
            
            test_result["success"] = len(test_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Market data system test failed: {e}")
            test_result["errors"].append(str(e))
        
        finally:
            await self.price_feed.stop()
        
        return test_result
    
    async def test_trading_strategies(self) -> Dict[str, Any]:
        """Test all trading strategies"""
        logger.info("Testing trading strategies...")
        
        test_result = {
            "test_name": "trading_strategies",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Start price feed for strategy testing
            await self.price_feed.start()
            await asyncio.sleep(5)  # Wait for data
            
            tokens = list(self.price_feed.get_supported_tokens().keys())[:3]  # Test with 3 tokens
            
            if not tokens:
                test_result["errors"].append("No tokens available for testing")
                return test_result
            
            # Test DCA strategy
            try:
                dca_signals = await self.dca_strategy.generate_signals(tokens)
                test_result["details"]["dca_signals"] = len(dca_signals)
                
                # Test DCA status
                dca_status = self.dca_strategy.get_all_dca_status()
                test_result["details"]["dca_status"] = len(dca_status)
                
            except Exception as e:
                test_result["errors"].append(f"DCA strategy test failed: {e}")
            
            # Test Momentum strategy
            try:
                momentum_signals = await self.momentum_strategy.generate_signals(tokens)
                test_result["details"]["momentum_signals"] = len(momentum_signals)
                
                # Test momentum positions
                momentum_positions = self.momentum_strategy.get_open_positions()
                test_result["details"]["momentum_positions"] = len(momentum_positions)
                
            except Exception as e:
                test_result["errors"].append(f"Momentum strategy test failed: {e}")
            
            # Test Arbitrage strategy
            try:
                arbitrage_signals = await self.arbitrage_strategy.generate_signals(tokens)
                test_result["details"]["arbitrage_signals"] = len(arbitrage_signals)
                
                # Test arbitrage opportunities
                opportunities = self.arbitrage_strategy.get_current_opportunities()
                test_result["details"]["arbitrage_opportunities"] = len(opportunities)
                
            except Exception as e:
                test_result["errors"].append(f"Arbitrage strategy test failed: {e}")
            
            test_result["success"] = len(test_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Trading strategies test failed: {e}")
            test_result["errors"].append(str(e))
        
        finally:
            await self.price_feed.stop()
        
        return test_result
    
    async def test_portfolio_management(self) -> Dict[str, Any]:
        """Test portfolio management system"""
        logger.info("Testing portfolio management...")
        
        test_result = {
            "test_name": "portfolio_management",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Test virtual portfolio operations
            initial_balance = self.portfolio.get_sol_balance()
            test_result["details"]["initial_balance"] = initial_balance
            
            # Test buying tokens
            success = self.portfolio.buy_token(
                token_mint="test_token",
                symbol="TEST",
                sol_amount=1.0,
                price=0.5,
                fee_percent=0.1
            )
            
            if not success:
                test_result["errors"].append("Failed to buy tokens")
                return test_result
            
            # Check position
            position = self.portfolio.get_position("test_token")
            if position:
                test_result["details"]["position_created"] = {
                    "quantity": position.quantity,
                    "average_price": position.average_price
                }
            else:
                test_result["errors"].append("Position not created after buy")
            
            # Test selling tokens
            if position:
                sell_success = self.portfolio.sell_token(
                    token_mint="test_token",
                    quantity=position.quantity / 2,  # Sell half
                    price=0.6,  # Profitable sale
                    fee_percent=0.1
                )
                
                if sell_success:
                    test_result["details"]["partial_sell_success"] = True
                else:
                    test_result["errors"].append("Failed to sell tokens")
            
            # Test performance stats
            stats = self.portfolio.get_performance_stats(None)
            test_result["details"]["performance_stats"] = {
                "total_trades": stats["total_trades"],
                "winning_trades": stats["winning_trades"],
                "current_portfolio_value": stats["current_portfolio_value"]
            }
            
            # Test portfolio manager
            await self.price_feed.start()
            await asyncio.sleep(2)
            
            # Test current allocations
            allocations = self.portfolio_manager.get_current_allocations()
            test_result["details"]["current_allocations"] = allocations
            
            # Test portfolio summary
            summary = self.portfolio_manager.get_portfolio_summary()
            test_result["details"]["portfolio_summary_keys"] = list(summary.keys())
            
            test_result["success"] = len(test_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Portfolio management test failed: {e}")
            test_result["errors"].append(str(e))
        
        finally:
            await self.price_feed.stop()
        
        return test_result
    
    async def test_risk_management(self) -> Dict[str, Any]:
        """Test risk management system"""
        logger.info("Testing risk management...")
        
        test_result = {
            "test_name": "risk_management",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            await self.price_feed.start()
            await asyncio.sleep(3)
            
            # Test trade validation
            tokens = list(self.price_feed.get_supported_tokens().keys())
            if not tokens:
                test_result["errors"].append("No tokens for risk testing")
                return test_result
            
            test_token = tokens[0]
            current_price = await self._get_test_price(test_token)
            
            if not current_price:
                test_result["errors"].append("No current price for risk testing")
                return test_result
            
            # Test valid trade
            valid, alerts = await self.risk_manager.validate_trade(
                token_mint=test_token,
                side="buy",
                size_sol=0.1,  # Small, safe size
                current_price=current_price
            )
            
            test_result["details"]["small_trade_approved"] = valid
            test_result["details"]["small_trade_alerts"] = len(alerts)
            
            # Test oversized trade
            oversized, oversized_alerts = await self.risk_manager.validate_trade(
                token_mint=test_token,
                side="buy",
                size_sol=10.0,  # Should exceed limits
                current_price=current_price
            )
            
            test_result["details"]["oversized_trade_rejected"] = not oversized
            test_result["details"]["oversized_trade_alerts"] = len(oversized_alerts)
            
            # Test stop loss creation
            stop_id = self.risk_manager.create_stop_loss(
                token_mint=test_token,
                quantity=100.0,
                stop_price=current_price * 0.95,  # 5% stop loss
                is_trailing=False
            )
            
            if stop_id:
                test_result["details"]["stop_loss_created"] = True
                
                # Test stop loss retrieval
                stop_losses = self.risk_manager.get_stop_losses()
                test_result["details"]["stop_losses_count"] = len(stop_losses)
                
                # Clean up
                self.risk_manager.remove_stop_loss(stop_id)
            else:
                test_result["errors"].append("Failed to create stop loss")
            
            # Test risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            test_result["details"]["risk_summary_keys"] = list(risk_summary.keys())
            
            test_result["success"] = len(test_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Risk management test failed: {e}")
            test_result["errors"].append(str(e))
        
        finally:
            await self.price_feed.stop()
        
        return test_result
    
    async def test_trading_engine(self) -> Dict[str, Any]:
        """Test trading engine automation"""
        logger.info("Testing trading engine...")
        
        test_result = {
            "test_name": "trading_engine",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Test engine startup
            await self.trading_engine.start()
            
            # Check engine status
            status = self.trading_engine.get_status()
            test_result["details"]["engine_status"] = status["state"]
            test_result["details"]["strategies_active"] = status["strategies_active"]
            
            # Let engine run for a short time
            await asyncio.sleep(15)
            
            # Check for activity
            updated_status = self.trading_engine.get_status()
            test_result["details"]["signals_processed"] = updated_status["total_signals_processed"]
            test_result["details"]["trades_executed"] = updated_status["total_trades_executed"]
            
            # Test execution history
            execution_history = self.trading_engine.get_execution_history(10)
            test_result["details"]["execution_history_count"] = len(execution_history)
            
            # Test engine stop
            await self.trading_engine.stop()
            
            final_status = self.trading_engine.get_status()
            test_result["details"]["final_state"] = final_status["state"]
            
            test_result["success"] = len(test_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Trading engine test failed: {e}")
            test_result["errors"].append(str(e))
        
        return test_result
    
    async def _get_test_price(self, token_mint: str) -> float:
        """Get test price for a token"""
        price_data = self.price_feed.get_current_price(token_mint)
        return price_data.price if price_data else 1.0  # Fallback price
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all Phase 2 tests"""
        logger.info("Starting comprehensive Phase 2 tests...")
        
        all_results = {
            "test_suite": "phase_2_comprehensive",
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # Run all test modules
        test_methods = [
            self.test_market_data_system,
            self.test_trading_strategies,
            self.test_portfolio_management,
            self.test_risk_management,
            self.test_trading_engine
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                result = await test_method()
                all_results["tests"][result["test_name"]] = result
                
                if result["success"]:
                    passed_tests += 1
                    logger.info(f"✓ {result['test_name']} PASSED")
                else:
                    logger.error(f"✗ {result['test_name']} FAILED: {result['errors']}")
                    
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} crashed: {e}")
                all_results["tests"][test_method.__name__] = {
                    "test_name": test_method.__name__,
                    "success": False,
                    "errors": [f"Test crashed: {str(e)}"]
                }
        
        # Generate summary
        all_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "end_time": datetime.now().isoformat()
        }
        
        return all_results
    
    async def cleanup(self):
        """Clean up test resources"""
        try:
            if self.price_feed:
                await self.price_feed.stop()
            if self.trading_engine:
                await self.trading_engine.stop()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def main():
    """Main test runner"""
    test_suite = Phase2TestSuite()
    
    try:
        await test_suite.setup()
        results = await test_suite.run_comprehensive_tests()
        
        # Print results summary
        logger.info("\n" + "="*60)
        logger.info("PHASE 2 TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        summary = results["summary"]
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        
        logger.info("\nDetailed Results:")
        for test_name, test_result in results["tests"].items():
            status = "✓ PASS" if test_result["success"] else "✗ FAIL"
            logger.info(f"  {test_name}: {status}")
            
            if not test_result["success"] and test_result.get("errors"):
                for error in test_result["errors"][:2]:  # Show first 2 errors
                    logger.info(f"    - {error}")
        
        logger.info("="*60)
        
        # Return appropriate exit code
        return 0 if summary["failed_tests"] == 0 else 1
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1
    
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)