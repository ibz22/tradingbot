"""
Simple script to run the halal trading bot in live (paper) mode.

This script loads configuration from ``config.yaml``, constructs the data
gateway, broker gateway, strategy and position store, then launches the
``TradingEngine`` in live mode. To use the Alpaca paper API you must set
the environment variables ``ALPACA_API_KEY`` and ``ALPACA_SECRET_KEY``.

Updated to use the cleaned halalbot package structure.
"""

import asyncio
import yaml
import logging
from pathlib import Path

# Updated imports using the cleaned halalbot package
from halalbot.core.engine import TradingEngine
from halalbot.core.position_store_sqlite import SQLitePositionStore
from halalbot.broker_gateway import AlpacaBrokerGateway  # Updated path
from halalbot.screening.data_gateway import FMPGateway
from halalbot.strategies.momentum import MomentumStrategy

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file with error handling"""
    config_path = Path(path)
    
    if not config_path.exists():
        logging.warning(f"Config file {path} not found, using defaults")
        return {
            'fmp_api_key': 'demo',
            'initial_capital': 100000,
            'position_db': 'positions.db',
            'poll_interval_seconds': 300,
            'stock_universe': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
            'max_interest_pct': 0.05,
            'max_debt_ratio': 0.33
        }
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # Validate required keys
        if not config:
            raise ValueError("Empty configuration file")
            
        # Set defaults for missing keys
        defaults = {
            'fmp_api_key': 'demo',
            'initial_capital': 100000,
            'position_db': 'positions.db',
            'poll_interval_seconds': 300,
            'stock_universe': ['AAPL', 'MSFT', 'GOOGL'],
            'max_interest_pct': 0.05,
            'max_debt_ratio': 0.33
        }
        
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
                logging.info(f"Using default value for {key}: {default_value}")
        
        return config
        
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        raise


async def main() -> None:
    """Main function to run the trading bot"""
    try:
        logging.info("🕌 Starting Halal Trading Bot")
        
        # Load configuration
        config = load_config()
        
        # Log configuration summary
        logging.info(f"Configuration loaded:")
        logging.info(f"  - FMP API Key: {'Set' if config['fmp_api_key'] != 'demo' else 'Using demo key'}")
        logging.info(f"  - Initial Capital: ${config['initial_capital']:,.2f}")
        logging.info(f"  - Stock Universe: {len(config.get('stock_universe', []))} symbols")
        logging.info(f"  - Poll Interval: {config['poll_interval_seconds']}s")
        
        # Set up gateways and strategy
        data_gateway = FMPGateway(api_key=config.get("fmp_api_key", "demo"))
        logging.info("✅ Data gateway initialized")
        
        # Initialize broker gateway (requires API keys in environment variables)
        try:
            broker_gateway = AlpacaBrokerGateway()
            logging.info("✅ Alpaca broker gateway initialized")
        except ValueError as e:
            logging.warning(f"⚠️ Broker gateway initialization failed: {e}")
            logging.info("Running in simulation mode without real broker connection")
            broker_gateway = None
        
        # Initialize strategy
        strategy = MomentumStrategy(lookback=20)
        logging.info("✅ Momentum strategy initialized")
        
        # Create trading engine
        engine = TradingEngine(
            config=config,
            strategy=strategy,
            data_gateway=data_gateway,
            broker_gateway=broker_gateway,
        )
        
        # Use SQLite for position storage
        engine.position_store = SQLitePositionStore(config.get("position_db", "positions.db"))
        logging.info("✅ Trading engine initialized with SQLite position store")
        
        # Check if we have any symbols to trade
        stock_universe = config.get('stock_universe', [])
        if not stock_universe:
            logging.warning("⚠️ No symbols in stock_universe, please update config.yaml")
            return
        
        logging.info(f"🎯 Trading universe: {', '.join(stock_universe[:5])}"
                     f"{'...' if len(stock_universe) > 5 else ''}")
        
        # Check current positions
        current_positions = engine.position_store.get_open_positions()
        if current_positions:
            logging.info(f"📊 Current open positions: {len(current_positions)}")
            for symbol, pos in current_positions.items():
                logging.info(f"  - {symbol}: {pos['qty']} shares @ ${pos['entry_price']:.2f}")
        else:
            logging.info("📊 No open positions")
        
        # Run live trading
        logging.info("🚀 Starting live trading engine...")
        logging.info("Press Ctrl+C to stop the bot gracefully")
        
        await engine.run_live()
        
    except KeyboardInterrupt:
        logging.info("⚡ Trading bot stopped by user")
    except Exception as e:
        logging.error(f"❌ Trading bot failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Goodbye!")
    except Exception as e:
        logging.critical(f"💥 Critical error: {e}")
        exit(1)
