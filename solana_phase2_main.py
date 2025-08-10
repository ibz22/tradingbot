#!/usr/bin/env python3
"""
Solana Trading Bot Phase 2 - Main Application
Complete automated trading system with strategies, portfolio management, and risk controls
"""

import asyncio
import logging
import sys
import os
import signal
from typing import Dict, Any
from datetime import datetime
import argparse

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports from Phase 1
from solana_trading.config.solana_config import SolanaConfig, SolanaNetwork
from solana_trading.core.client import SolanaClient
from solana_trading.defi.jupiter import JupiterAggregator
from solana_trading.core.transactions import TransactionBuilder

# Phase 2 imports
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
def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('solana_trading_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

class SolanaTradingBot:
    """Main Solana Trading Bot application"""
    
    def __init__(self, args):
        self.args = args
        self.config = None
        self.running = False
        
        # Core components
        self.solana_client = None
        self.jupiter_client = None
        self.transaction_builder = None
        
        # Market data and analysis
        self.price_feed = None
        self.technical_analyzer = None
        
        # Portfolio and risk management
        self.portfolio = None
        self.portfolio_manager = None
        self.risk_manager = None
        
        # Strategies
        self.strategies = []
        
        # Trading engine
        self.trading_engine = None
        
        # Shutdown handling
        self.shutdown_event = asyncio.Event()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self):
        """Initialize all bot components"""
        logger.info("Initializing Solana Trading Bot Phase 2...")
        
        # Load configuration
        if self.args.network == "mainnet":
            self.config = SolanaConfig.for_network(SolanaNetwork.MAINNET)
        elif self.args.network == "testnet":
            self.config = SolanaConfig.for_network(SolanaNetwork.TESTNET)
        else:  # devnet (default)
            self.config = SolanaConfig.for_network(SolanaNetwork.DEVNET)
        
        # Override paper trading mode
        self.config.paper_trading = self.args.paper_trading
        
        logger.info(f"Network: {self.config.network.name}")
        logger.info(f"Paper Trading: {self.config.paper_trading}")
        logger.info(f"RPC Endpoint: {self.config.get_rpc_endpoint()}")
        
        # Initialize Phase 1 components
        await self._initialize_phase1_components()
        
        # Initialize Phase 2 components
        await self._initialize_phase2_components()
        
        # Wire up all dependencies
        self._setup_component_dependencies()
        
        logger.info("All components initialized successfully")
    
    async def _initialize_phase1_components(self):
        """Initialize Phase 1 components (RPC, Jupiter, Transactions)"""
        logger.info("Initializing Phase 1 components...")
        
        # Solana RPC client
        self.solana_client = SolanaClient(
            rpc_endpoint=self.config.get_rpc_endpoint(),
            max_retries=self.config.rpc_max_retries,
            retry_delay=self.config.rpc_retry_delay,
            timeout=self.config.rpc_timeout
        )
        
        # Connect to Solana
        connected = await self.solana_client.connect()
        if not connected:
            raise RuntimeError("Failed to connect to Solana RPC")
        
        # Jupiter aggregator
        self.jupiter_client = JupiterAggregator(
            base_url=self.config.jupiter.base_url,
            timeout=self.config.jupiter.timeout
        )
        
        # Transaction builder
        self.transaction_builder = TransactionBuilder(
            solana_client=self.solana_client,
            jupiter_client=self.jupiter_client
        )
    
    async def _initialize_phase2_components(self):
        """Initialize Phase 2 components"""
        logger.info("Initializing Phase 2 components...")
        
        # Market data feed
        self.price_feed = PriceFeed(
            jupiter_client=self.jupiter_client,
            update_interval=30.0,  # 30 second updates
            max_history=1000
        )
        
        # Technical analyzer
        self.technical_analyzer = TechnicalAnalyzer(
            price_feed=self.price_feed
        )
        
        # Portfolio components
        self.portfolio = VirtualPortfolio(
            initial_sol_balance=self.config.initial_sol_balance
        )
        
        portfolio_config = PortfolioConfig(
            max_positions=10,
            max_position_percent=25.0,
            rebalance_threshold=10.0,
            target_allocations={
                "So11111111111111111111111111111111111111112": 40.0,  # SOL 40%
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 30.0,  # USDC 30%
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 20.0,  # USDT 20%
                "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": 10.0   # RAY 10%
            }
        )
        
        self.portfolio_manager = PortfolioManager(
            config=portfolio_config,
            portfolio=self.portfolio
        )
        
        # Risk management
        risk_config = RiskConfig(
            max_position_size_sol=2.0,
            max_position_percent=30.0,
            max_portfolio_loss_percent=15.0,
            max_daily_loss_percent=5.0,
            enable_stop_losses=True,
            default_stop_loss_percent=5.0
        )
        
        self.risk_manager = RiskManager(risk_config)
        
        # Initialize trading strategies
        await self._initialize_strategies()
        
        # Trading engine
        engine_config = EngineConfig(
            max_concurrent_trades=3,
            strategy_update_interval=60,  # 1 minute
            enable_paper_trading=self.config.paper_trading,
            log_all_signals=True
        )
        
        self.trading_engine = TradingEngine(engine_config)
    
    async def _initialize_strategies(self):
        """Initialize trading strategies"""
        logger.info("Initializing trading strategies...")
        
        # DCA Strategy
        if self.args.enable_dca:
            dca_config = DCAConfig(
                purchase_amount=0.2,  # 0.2 SOL per purchase
                interval_minutes=60,  # Hourly purchases
                max_total_investment=5.0,  # Max 5 SOL per token
                target_tokens=[
                    "So11111111111111111111111111111111111111112",  # SOL
                    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
                ]
            )
            
            dca_strategy = DCAStrategy(dca_config)
            self.strategies.append(dca_strategy)
            logger.info("DCA strategy initialized")
        
        # Momentum Strategy
        if self.args.enable_momentum:
            momentum_config = MomentumConfig(
                strong_momentum_threshold=5.0,
                weak_momentum_threshold=2.0,
                short_window_minutes=15,
                long_window_minutes=60,
                max_momentum_position=1.0
            )
            
            momentum_strategy = MomentumStrategy(momentum_config)
            self.strategies.append(momentum_strategy)
            logger.info("Momentum strategy initialized")
        
        # Arbitrage Strategy
        if self.args.enable_arbitrage:
            arbitrage_config = ArbitrageConfig(
                min_profit_percent=1.0,
                min_profit_absolute_sol=0.01,
                max_single_trade_sol=0.5
            )
            
            arbitrage_strategy = ArbitrageStrategy(arbitrage_config)
            self.strategies.append(arbitrage_strategy)
            logger.info("Arbitrage strategy initialized")
        
        if not self.strategies:
            logger.warning("No strategies enabled! Bot will only monitor.")
    
    def _setup_component_dependencies(self):
        """Set up dependencies between components"""
        logger.info("Setting up component dependencies...")
        
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
        
        # Set up strategy dependencies
        for strategy in self.strategies:
            strategy.set_dependencies(
                price_feed=self.price_feed,
                technical_analyzer=self.technical_analyzer,
                portfolio_manager=self.portfolio_manager,
                risk_manager=self.risk_manager
            )
        
        # Trading engine dependencies and strategies
        self.trading_engine.set_dependencies(
            price_feed=self.price_feed,
            portfolio_manager=self.portfolio_manager,
            risk_manager=self.risk_manager,
            technical_analyzer=self.technical_analyzer,
            jupiter_client=self.jupiter_client,
            transaction_builder=self.transaction_builder
        )
        
        # Add strategies to engine
        for strategy in self.strategies:
            self.trading_engine.add_strategy(strategy)
    
    async def start(self):
        """Start the trading bot"""
        logger.info("Starting Solana Trading Bot...")
        
        try:
            # Start market data feed
            await self.price_feed.start()
            logger.info("Market data feed started")
            
            # Start trading engine
            await self.trading_engine.start()
            logger.info("Trading engine started")
            
            self.running = True
            logger.info("🚀 Solana Trading Bot Phase 2 is now running!")
            
            # Set up event callbacks for monitoring
            self._setup_event_callbacks()
            
            # Print initial status
            await self._print_status()
            
        except Exception as e:
            logger.error(f"Failed to start trading bot: {e}")
            raise
    
    def _setup_event_callbacks(self):
        """Set up event callbacks for monitoring"""
        self.trading_engine.subscribe_to_events("trade_executed", self._on_trade_executed)
        self.trading_engine.subscribe_to_events("trade_failed", self._on_trade_failed)
        self.trading_engine.subscribe_to_events("risk_violation", self._on_risk_violation)
        self.trading_engine.subscribe_to_events("performance_report", self._on_performance_report)
    
    async def _on_trade_executed(self, execution_data):
        """Handle trade execution event"""
        logger.info(f"🎯 Trade executed: {execution_data.side} {execution_data.token_mint[:8]} "
                   f"for {execution_data.size_sol:.3f} SOL")
    
    async def _on_trade_failed(self, execution_data):
        """Handle trade failure event"""
        logger.warning(f"❌ Trade failed: {execution_data.side} {execution_data.token_mint[:8]} "
                      f"- {execution_data.error_message}")
    
    async def _on_risk_violation(self, risk_data):
        """Handle risk violation event"""
        logger.warning(f"⚠️ Risk violation: {risk_data}")
    
    async def _on_performance_report(self, report_data):
        """Handle performance report event"""
        logger.info(f"📊 Performance: {report_data['total_trades_executed']} trades, "
                   f"{report_data['total_volume_traded']:.1f} SOL volume, "
                   f"{report_data['execution_success_rate']:.1f}% success rate")
    
    async def _print_status(self):
        """Print current status"""
        logger.info("="*50)
        logger.info("CURRENT STATUS")
        logger.info("="*50)
        
        # Engine status
        engine_status = self.trading_engine.get_status()
        logger.info(f"Engine State: {engine_status['state']}")
        logger.info(f"Active Strategies: {engine_status['strategies_active']}")
        logger.info(f"Paper Trading: {engine_status['paper_trading_mode']}")
        
        # Portfolio status
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        logger.info(f"Portfolio Value: {portfolio_summary['total_value_sol']:.3f} SOL")
        logger.info(f"SOL Balance: {portfolio_summary['sol_balance']:.3f}")
        logger.info(f"Positions: {portfolio_summary['positions_count']}")
        
        # Risk status
        risk_summary = self.risk_manager.get_risk_summary()
        logger.info(f"Active Alerts: {risk_summary['active_alerts_count']}")
        logger.info(f"Stop Losses: {risk_summary['stop_losses_count']}")
        
        logger.info("="*50)
    
    async def run(self):
        """Main run loop"""
        status_interval = 300  # Print status every 5 minutes
        last_status_print = 0
        
        try:
            while self.running:
                # Wait for shutdown signal or timeout
                try:
                    await asyncio.wait_for(self.shutdown_event.wait(), timeout=10.0)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    pass  # Continue normal operation
                
                # Periodic status printing
                current_time = asyncio.get_event_loop().time()
                if current_time - last_status_print >= status_interval:
                    await self._print_status()
                    last_status_print = current_time
                
        except Exception as e:
            logger.error(f"Error in main run loop: {e}")
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        if not self.running:
            return
        
        logger.info("Shutting down Solana Trading Bot...")
        self.running = False
        
        try:
            # Stop trading engine
            if self.trading_engine:
                await self.trading_engine.stop()
                logger.info("Trading engine stopped")
            
            # Stop market data feed
            if self.price_feed:
                await self.price_feed.stop()
                logger.info("Market data feed stopped")
            
            # Close Solana client
            if self.solana_client:
                await self.solana_client.close()
                logger.info("Solana client closed")
            
            # Close Jupiter client
            if self.jupiter_client:
                await self.jupiter_client.close()
                logger.info("Jupiter client closed")
            
            logger.info("✅ Solana Trading Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def create_arg_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="Solana Trading Bot Phase 2")
    
    parser.add_argument("--network", choices=["mainnet", "testnet", "devnet"], 
                       default="devnet", help="Solana network to use")
    parser.add_argument("--paper-trading", action="store_true", default=True,
                       help="Enable paper trading mode (default)")
    parser.add_argument("--live-trading", action="store_true",
                       help="Enable live trading mode (disables paper trading)")
    
    # Strategy options
    parser.add_argument("--enable-dca", action="store_true", default=True,
                       help="Enable DCA strategy")
    parser.add_argument("--enable-momentum", action="store_true", default=False,
                       help="Enable momentum strategy")
    parser.add_argument("--enable-arbitrage", action="store_true", default=False,
                       help="Enable arbitrage strategy")
    
    # Logging
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="Logging level")
    
    return parser

async def main():
    """Main application entry point"""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    # Override paper trading if live trading is explicitly requested
    if args.live_trading:
        args.paper_trading = False
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(log_level)
    
    # Create and run bot
    bot = SolanaTradingBot(args)
    
    try:
        # Setup signal handlers
        bot.setup_signal_handlers()
        
        # Initialize bot
        await bot.initialize()
        
        # Start bot
        await bot.start()
        
        # Run main loop
        await bot.run()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)