#!/usr/bin/env python3
"""
Enhanced Halal Trading Bot v2.2 - Main Application Entry Point

This is the integrated main application that combines all the enhanced features
from the original tradingbotupdated2.py with the cleaned halalbot package structure.

Usage:
    python main.py --mode live                    # Run live trading
    python main.py --mode live --dry-run          # Run dry-run simulation  
    python main.py --mode backtest --symbol AAPL  # Backtest a symbol
    python main.py --mode screen                  # Screen all assets
    python main.py --mode test                    # Run tests
"""

import logging
import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

# Import the cleaned halalbot package
from halalbot.core.engine import TradingEngine
from halalbot.core.risk import RiskManager
from halalbot.core.trade_executor import EnhancedTradeExecutor
from halalbot.screening.advanced_screener import AdvancedHalalScreener
from halalbot.screening.data_gateway import FMPGateway
from halalbot.screening.halal_rules import load_rules
from halalbot.strategies.momentum import MomentumStrategy
from halalbot.strategies.mean_reversion import MeanReversionStrategy
from halalbot.broker_gateway import EnhancedAlpacaBrokerGateway, MockBrokerGateway

# Import configuration and utilities from the original enhanced system
try:
    from tradingbotupdated2 import (
        TradingConfig, setup_logging, print_startup_summary,
        ConnectionManager, NotificationManager, EnhancedTechnicalAnalysis,
        EnhancedMLStrategy, AdvancedTradingStrategies, EnhancedTradeExecutor,
        EnhancedBacktestEngine, EnhancedHalalTradingBot
    )
    ENHANCED_FEATURES_AVAILABLE = True
    logging.info("✅ Enhanced features loaded successfully")
except ImportError as e:
    logging.warning(f"⚠️ Enhanced features not available: {e}")
    logging.info("Using basic halalbot functionality")
    ENHANCED_FEATURES_AVAILABLE = False


def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration from YAML file with error handling"""
    try:
        if ENHANCED_FEATURES_AVAILABLE:
            return TradingConfig.from_yaml(config_file).__dict__
        else:
            # Fallback basic config loading
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {
            'initial_capital': 100000,
            'max_portfolio_risk': 0.02,
            'max_position_risk': 0.01,
            'stock_universe': ['AAPL', 'MSFT', 'GOOGL'],
            'crypto_universe': ['BTC/USDT', 'ETH/USDT'],
            'fmp_api_key': 'demo'
        }


async def run_basic_trading_session(config: dict) -> Dict:
    """Run a basic trading session using the core halalbot package"""
    try:
        logging.info("🚀 Starting basic trading session using halalbot core")
        
        # Initialize components
        data_gateway = FMPGateway(config.get('fmp_api_key', 'demo'))
        strategy = MomentumStrategy(lookback=20)
        
        # Create trading engine
        engine = TradingEngine(
            config=config,
            strategy=strategy,
            data_gateway=data_gateway
        )
        
        # Mock price data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
        mock_data = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 100
        }, index=dates)
        
        # Run backtest as demonstration
        results = engine.run_backtest(mock_data)
        
        logging.info("✅ Basic trading session completed")
        logging.info(f"Initial Capital: ${results['initial_capital']:,.2f}")
        logging.info(f"Final Equity: ${results['final_equity']:,.2f}")
        logging.info(f"Total Return: {results['performance_metrics']['total_return']:.2%}")
        logging.info(f"Total Trades: {results['total_trades']}")
        
        return results
        
    except Exception as e:
        logging.error(f"❌ Basic trading session failed: {e}")
        return {}


async def run_enhanced_trading_session(config_file: str, is_dry_run: bool) -> Dict:
    """Run enhanced trading session if enhanced features are available"""
    if not ENHANCED_FEATURES_AVAILABLE:
        logging.warning("Enhanced features not available, falling back to basic session")
        config = load_config(config_file)
        return await run_basic_trading_session(config)
    
    try:
        # Use the enhanced trading bot
        bot = EnhancedHalalTradingBot(config_file, is_dry_run)
        results = await bot.run_trading_session()
        return results
        
    except Exception as e:
        logging.error(f"❌ Enhanced trading session failed: {e}")
        # Fallback to basic session
        logging.info("Falling back to basic trading session...")
        config = load_config(config_file)
        return await run_basic_trading_session(config)


async def run_basic_backtest(symbol: str, is_crypto: bool, config: dict) -> Dict:
    """Run basic backtest using core halalbot components"""
    try:
        logging.info(f"🔍 Starting basic backtest for {symbol}")
        
        # Create strategy and engine
        strategy = MomentumStrategy(lookback=20)
        
        # Create mock historical data (in real implementation, fetch from API)
        dates = pd.date_range(end=datetime.now(), periods=500, freq='1H')
        price_trend = np.random.randn(500).cumsum() * 0.02 + 100
        
        mock_data = pd.DataFrame({
            'close': price_trend,
            'volume': np.random.randint(1000, 10000, 500)
        }, index=dates)
        
        # Initialize trading engine
        engine = TradingEngine(
            config=config,
            strategy=strategy,
            data_gateway=FMPGateway(config.get('fmp_api_key', 'demo'))
        )
        
        # Run backtest
        results = engine.run_backtest(mock_data)
        
        # Display results
        metrics = results['performance_metrics']
        logging.info(f"\n📈 Backtest Results for {symbol}")
        logging.info(f"{'='*50}")
        logging.info(f"Initial Capital: ${results['initial_capital']:,.2f}")
        logging.info(f"Final Equity: ${results['final_equity']:,.2f}")
        logging.info(f"Total Return: {metrics['total_return']:.2%}")
        logging.info(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
        logging.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logging.info(f"Total Trades: {results['total_trades']}")
        
        return results
        
    except Exception as e:
        logging.error(f"❌ Basic backtest failed for {symbol}: {e}")
        return {}


async def run_basic_screening(symbols: List[str], config: dict) -> Dict:
    """Run basic halal screening using core halalbot components"""
    try:
        logging.info(f"🕌 Starting basic halal screening for {len(symbols)} symbols")
        
        # Initialize screener
        data_gateway = FMPGateway(config.get('fmp_api_key', 'demo'))
        screener_config = {
            'max_interest_pct': config.get('max_interest_pct', 0.05),
            'max_debt_ratio': config.get('max_debt_ratio', 0.33)
        }
        screener = AdvancedHalalScreener(data_gateway, screener_config)
        
        results = {}
        approved_count = 0
        
        logging.info(f"{'Symbol':<12} {'Status':<12} {'Type':<8}")
        logging.info(f"{'-'*35}")
        
        for symbol in symbols:
            try:
                is_crypto = '/' in symbol or symbol.endswith('USDT')
                
                if is_crypto:
                    # Load halal rules and check crypto
                    rules = load_rules(config.get('config_path', 'config.yaml'))
                    is_halal = symbol in rules.get('halal_crypto', {})
                else:
                    # Check stock using financial screening
                    is_halal = await screener.is_halal(symbol)
                
                results[symbol] = {
                    'is_halal': is_halal,
                    'is_crypto': is_crypto,
                    'screened_at': datetime.now()
                }
                
                if is_halal:
                    approved_count += 1
                    status = "✅ APPROVED"
                else:
                    status = "❌ REJECTED"
                
                asset_type = "crypto" if is_crypto else "stock"
                logging.info(f"{symbol:<12} {status:<12} {asset_type:<8}")
                
            except Exception as e:
                logging.error(f"Error screening {symbol}: {e}")
                results[symbol] = {
                    'is_halal': False,
                    'is_crypto': is_crypto,
                    'error': str(e)
                }
        
        logging.info(f"\n📊 Screening Summary:")
        logging.info(f"Total Analyzed: {len(symbols)}")
        logging.info(f"Approved: {approved_count} ({approved_count/len(symbols):.1%})")
        logging.info(f"Rejected: {len(symbols) - approved_count}")
        
        return results
        
    except Exception as e:
        logging.error(f"❌ Basic screening failed: {e}")
        return {}


def main():
    """Main application entry point with integrated functionality"""
    
    parser = argparse.ArgumentParser(
        description="Enhanced Halal Trading Bot v2.2 - Integrated Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode live                    # Run live trading
  python main.py --mode live --dry-run          # Dry run simulation
  python main.py --mode backtest --symbol AAPL  # Backtest Apple stock
  python main.py --mode screen                  # Screen all assets
  python main.py --mode test                    # Run tests
        """
    )
    
    parser.add_argument('--mode', 
                        choices=['live', 'backtest', 'screen', 'test'], 
                        default='live',
                        help='Operation mode')
    parser.add_argument('--symbol', help='Symbol for backtesting or screening')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--crypto', action='store_true', help='Treat symbol as crypto')
    parser.add_argument('--stock', action='store_true', help='Treat symbol as stock')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Simulation mode')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level) if ENHANCED_FEATURES_AVAILABLE else logging.basicConfig(level=log_level)
    
    try:
        config = load_config(args.config)
        
        if ENHANCED_FEATURES_AVAILABLE:
            print_startup_summary(args, TradingConfig.from_yaml(args.config))
        else:
            logging.info("🕌 Halal Trading Bot v2.2 - Basic Mode")
            logging.info(f"Mode: {args.mode}, Config: {args.config}")
        
        if args.mode == 'live':
            if ENHANCED_FEATURES_AVAILABLE:
                asyncio.run(run_enhanced_trading_session(args.config, args.dry_run))
            else:
                asyncio.run(run_basic_trading_session(config))
                
        elif args.mode == 'backtest':
            if not args.symbol:
                logging.error("❌ Symbol required for backtest mode")
                sys.exit(1)
                
            is_crypto = args.crypto or ('/' in args.symbol or args.symbol.endswith('USDT')) if not args.stock else False
            
            if ENHANCED_FEATURES_AVAILABLE:
                from tradingbotupdated2 import run_async_backtest
                asyncio.run(run_async_backtest(args.symbol, is_crypto, args.config))
            else:
                asyncio.run(run_basic_backtest(args.symbol, is_crypto, config))
                
        elif args.mode == 'screen':
            symbols = [args.symbol] if args.symbol else (config.get('stock_universe', []) + config.get('crypto_universe', []))
            
            if ENHANCED_FEATURES_AVAILABLE:
                from tradingbotupdated2 import run_async_halal_screening
                asyncio.run(run_async_halal_screening(symbols, args.config))
            else:
                asyncio.run(run_basic_screening(symbols, config))
                
        elif args.mode == 'test':
            logging.info("🧪 Running Test Suite")
            import unittest
            loader = unittest.TestLoader()
            suite = loader.discover('.', pattern='test_*.py')
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            if not result.wasSuccessful():
                sys.exit(1)
    
    except KeyboardInterrupt:
        logging.warning("⚡ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"❌ Critical error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
