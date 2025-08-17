# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation & Setup
```bash
# Install package and dependencies
pip install -e .
pip install -r requirements.txt

# Setup environment (copy and edit with your API keys)
cp .env.example .env
```

### Running the Application
```bash
# Main application entry point with various modes
python main.py --mode live --dry-run        # Live trading simulation
python main.py --mode live                  # Live trading (requires funded account)
python main.py --mode backtest --symbol AAPL  # Backtest specific symbol
python main.py --mode screen                # Screen all assets for halal compliance
python main.py --mode test                  # Run test suite

# Simple bot runner (basic functionality)
python run_bot.py

# Installation helper
python install.py
```

### Testing
```bash
# Run comprehensive test suite
python main.py --mode test

# Run specific test modules
python -m pytest halalbot/tests/ -v

# Test enhanced execution features
python test_enhanced_execution.py

# Integration tests
python test_integration.py

# Configuration tests
python test_config.py
```

## Project Architecture

### Core Package Structure (`halalbot/`)
The main trading system is organized in a clean package structure:

- **`core/`** - Central trading engine and components
  - `engine.py` - Main `TradingEngine` orchestrator that coordinates all subsystems
  - `risk.py` - `RiskManager` for portfolio and position risk controls
  - `trade_executor.py` - Enhanced trade execution with order lifecycle management
  - `order_manager.py` - Comprehensive order tracking and management
  - `order_blotter.py` - Order audit trail and blotter functionality
  - `position_store.py` - JSON-based position persistence
  - `position_store_sqlite.py` - SQLite position storage alternative

- **`strategies/`** - Trading strategy implementations
  - `momentum.py` - Simple moving average crossover strategy
  - `mean_reversion.py` - Z-score based mean reversion strategy
  - `ml.py` - Machine learning strategy template

- **`screening/`** - Halal compliance screening system
  - `advanced_screener.py` - AAOIFI-compliant financial screening using real data
  - `data_gateway.py` - Financial data APIs (FMP, Alpha Vantage)
  - `halal_rules.py` - YAML-based halal rules loading

- **`backtest/`** - Backtesting engine
  - `engine.py` - Historical simulation and performance metrics

- **`tests/`** - Package unit tests
  - `test_backtest.py`, `test_risk.py` - Core functionality tests

### Enhanced System Integration
The system has dual-mode operation:
- **Basic mode**: Uses core `halalbot` package only
- **Enhanced mode**: Integrates with advanced features from `tradingbotupdated2.py` when available

The `main.py` entry point automatically detects available features and provides graceful fallback.

### Broker Integration
- **`broker_gateway.py`** - Enhanced Alpaca broker integration at root level
- Supports both paper trading and live trading modes
- Comprehensive position reconciliation and health monitoring
- Mock gateway for testing and dry-run operations

### Configuration Management
- **`config.yaml`** - Main configuration file with trading parameters, risk settings, and asset universes
- **`.env`** - API keys and sensitive configuration (use `.env.example` as template)
- Configuration supports halal screening thresholds, strategy weights, and risk parameters

## Key Development Guidelines

### Strategy Development
- All strategies must implement `generate_signal(data, index)` method returning "buy", "sell", or "hold"
- Strategies should be stateless and work with pandas DataFrames
- Use the existing momentum and mean reversion strategies as templates

### Halal Compliance
- All assets go through `AdvancedHalalScreener` before trading
- Stock screening uses AAOIFI standards with configurable thresholds for interest income and debt ratios
- Cryptocurrency screening uses pre-approved whitelist defined in `config.yaml`
- Screening results are cached and logged for audit purposes

### Risk Management
- `RiskManager` enforces portfolio-level and position-level risk limits
- Position sizing is calculated based on risk parameters and account value
- All trades go through pre-execution validation including market hours and buying power checks

### Order Execution Flow
1. Strategy generates signal
2. Risk manager calculates position size
3. Halal screener validates compliance
4. `EnhancedTradeExecutor` handles order placement with monitoring
5. `OrderManager` tracks order lifecycle until completion
6. Position is recorded in `PositionStore`

### Testing Approach
- Use `--dry-run` mode for safe testing of live trading logic
- MockBrokerGateway provides realistic simulation without real money
- Integration tests verify end-to-end functionality
- Unit tests cover individual components

### Enhanced Features Integration
The system is designed to work with optional enhanced features:
- If `tradingbotupdated2.py` is available, uses advanced ML strategies, notifications, and analytics
- Falls back gracefully to basic functionality if enhanced features are missing
- Always test both modes when making changes

### Data Sources
- Financial Modeling Prep (FMP) for stock financial data and real-time prices
- Alpaca for brokerage operations and market data
- Configuration supports API key management and fallback to demo modes

## Important Implementation Notes

### Async/Await Pattern
- Live trading uses async/await for concurrent operations
- Data fetching, order execution, and position monitoring are all async
- Use proper exception handling in async contexts

### Error Handling
- System provides comprehensive error handling with fallback mechanisms
- Failed orders trigger retry logic with exponential backoff
- All errors are logged with appropriate context for debugging

### Position Management
- Positions are persisted across sessions using JSON or SQLite storage
- Position reconciliation ensures consistency between local records and broker positions
- Support for both long and short positions with proper risk calculations

## Trading UI Design Review

This project uses automated design review workflows for all trading interface changes.
The review system ensures high standards for financial UX, real-time performance, and regulatory compliance.

### Automated Review Triggers

Automatically review changes to these components:
- `/trading-platform/frontend/app/markets/*` - Market data displays and tickers
- `/trading-platform/frontend/app/strategies/*` - Strategy configuration interfaces  
- `/trading-platform/frontend/app/bots/*` - Bot management and monitoring
- `/trading-platform/frontend/app/analytics/*` - Charts and technical analysis
- `/trading-platform/frontend/app/risk-management/*` - Risk dashboards and alerts
- `/trading-platform/frontend/components/BotCreator/*` - Order placement forms
- `/trading-platform/frontend/components/Dashboard/*` - Portfolio views

### Design Standards

Follow these core principles:

1. **Financial Data Display**
   - Use monospace fonts for numbers: `font-family: 'JetBrains Mono'`
   - Right-align numeric columns in tables
   - Format prices with appropriate decimal places
   - Color code P&L: Green (#22C55E) for profit, Red (#EF4444) for loss

2. **Real-time Updates**
   - Price updates must render within 50ms
   - Use WebSocket for live data, never polling
   - Show connection status indicator at all times
   - Implement graceful reconnection with exponential backoff

3. **Risk Communication**
   - Display leverage and margin prominently
   - Show liquidation price when applicable
   - Require confirmation for orders >10% of portfolio
   - Use progressive color coding for risk levels

4. **Order Placement**
   - Two-step confirmation for market orders
   - Show estimated cost and fees upfront
   - Validate against available balance
   - Display slippage warnings for large orders

5. **Mobile Experience**
   - Minimum 44px touch targets
   - Bottom sheet pattern for order forms
   - Swipe gestures for chart navigation
   - Landscape mode for detailed charts

### Review Commands

Use these commands for different review types:

```bash
# Full trading UI review (use when in the trading-ui-review directory)
/trading-ui-review

# Review with specific focus areas
@agent-trading-ui-review --focus charts
@agent-trading-ui-review --focus orders
@agent-trading-ui-review --mobile
@agent-trading-ui-review --performance
```

### Performance Targets

All trading interfaces must meet these benchmarks:
- Price update latency: <50ms
- Chart render time: <100ms
- Order placement: <200ms
- Memory usage: <500MB
- CPU usage: <30%

### UI Review Resources

- [Trading Design Principles](./trading-ui-review/trading-design-principles.md)
- [Chart Review Checklist](./trading-ui-review/chart-review-checklist.md)
- [Order Flow Checklist](./trading-ui-review/order-flow-checklist.md)
- [Portfolio View Checklist](./trading-ui-review/portfolio-view-checklist.md)
- [Risk Dashboard Checklist](./trading-ui-review/risk-dashboard-checklist.md)
- [Performance Guide](./trading-ui-review/docs/performance-guide.md)
- [Trading UX Guide](./trading-ui-review/docs/trading-ux-guide.md)
- [Regulatory Requirements](./trading-ui-review/docs/regulatory-requirements.md)