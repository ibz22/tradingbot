# 🕌 Enhanced Halal Trading Bot v2.2

**Islamic Finance Compliant Automated Trading System**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive, Sharia-compliant algorithmic trading system that integrates real-time market data, advanced technical analysis, machine learning strategies, and robust halal screening based on AAOIFI standards.

## 🌟 **Key Features**

### **📊 Trading Capabilities**
- **Multi-Asset Support**: Stocks, cryptocurrencies, and other financial instruments
- **Advanced Strategies**: Momentum, mean reversion, and ML-based trading algorithms
- **Risk Management**: Portfolio-level risk controls with Islamic finance principles
- **Backtesting Engine**: Comprehensive historical performance analysis
- **Live Trading**: Real-time execution via Alpaca (paper/live) and Binance APIs

### **🕌 Halal Compliance**
- **AAOIFI Standards**: Automated screening based on Islamic finance guidelines
- **Real-time Screening**: Debt ratio, interest income, and business activity analysis
- **Crypto Compliance**: Pre-approved list of Sharia-compliant cryptocurrencies
- **Continuous Monitoring**: Ongoing compliance verification for all positions

### **🤖 Advanced Features**
- **Machine Learning**: Ensemble models with feature engineering and cross-validation
- **Technical Analysis**: 20+ indicators with TA-Lib integration
- **Notifications**: Multi-channel alerts (Telegram, Email) with rate limiting
- **Performance Analytics**: Comprehensive metrics and reporting
- **Async Architecture**: High-performance concurrent processing

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Clone the repository
git clone https://github.com/ibz22/tradingbot.git
cd tradingbot

# Install dependencies
pip install -r requirements.txt

# Optional: Install TA-Lib for advanced technical analysis
# pip install TA-Lib  # Requires compilation, see TA-Lib docs

# Install the halalbot package in development mode
pip install -e .
```

### **2. Configuration**

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Review and customize configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your preferences
```

### **3. Basic Usage**

```bash
# Run live trading (dry-run mode)
python main.py --mode live --dry-run

# Run a backtest
python main.py --mode backtest --symbol AAPL

# Screen assets for halal compliance
python main.py --mode screen

# Run the test suite
python main.py --mode test
```

## 📋 **Detailed Setup**

### **Environment Variables**

Create a `.env` file with your API credentials:

```env
# Trading APIs
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
BINANCE_API_KEY=your_binance_key_here
BINANCE_SECRET_KEY=your_binance_secret_here

# Data Provider
FMP_API_KEY=your_fmp_key_here

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
NOTIFICATION_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### **Configuration File**

The `config.yaml` file controls all trading parameters:

```yaml
# Risk Management
max_portfolio_risk: 0.02      # Max 2% portfolio risk
max_position_risk: 0.01       # Max 1% per position
max_position_pct: 0.1         # Max 10% per position

# Halal Screening Thresholds
max_interest_pct: 0.05        # Max 5% interest income
max_debt_ratio: 0.33          # Max 33% debt ratio

# Asset Universe
stock_universe:
  - AAPL
  - MSFT
  - GOOGL
  - AMZN
  - TSLA

crypto_universe:
  - BTC/USDT
  - ETH/USDT
  - ADA/USDT
  - SOL/USDT

# Strategy Weights
default_strategy_weights:
  momentum_breakout: 0.4
  mean_reversion: 0.3
  ml_strategy: 0.3
```

## 🔧 **Usage Examples**

### **Live Trading**

```bash
# Paper trading (recommended for testing)
python main.py --mode live --dry-run

# Live trading (requires funded account)
python main.py --mode live

# With custom configuration
python main.py --mode live --config my_config.yaml
```

### **Backtesting**

```bash
# Backtest a stock
python main.py --mode backtest --symbol AAPL

# Backtest a cryptocurrency
python main.py --mode backtest --symbol BTC/USDT

# Enhanced backtest with verbose logging
python main.py --mode backtest --symbol TSLA --verbose
```

### **Halal Screening**

```bash
# Screen all configured assets
python main.py --mode screen

# Screen a specific symbol
python main.py --mode screen --symbol JPM

# Screen with detailed output
python main.py --mode screen --verbose
```

### **Using the Core Package**

```python
import asyncio
from halalbot.core.engine import TradingEngine
from halalbot.strategies.momentum import MomentumStrategy
from halalbot.screening.data_gateway import FMPGateway

async def simple_example():
    # Configuration
    config = {
        'fmp_api_key': 'your_key_here',
        'initial_capital': 10000,
        'max_interest_pct': 0.05,
        'max_debt_ratio': 0.33
    }
    
    # Initialize components
    strategy = MomentumStrategy(lookback=20)
    data_gateway = FMPGateway(config['fmp_api_key'])
    
    # Create trading engine
    engine = TradingEngine(
        config=config,
        strategy=strategy,  
        data_gateway=data_gateway
    )
    
    # Use the engine for backtesting or live trading
    # results = engine.run_backtest(historical_data)

# Run the example
asyncio.run(simple_example())
```

## 📊 **Performance Metrics**

The system tracks comprehensive performance metrics:

- **Returns**: Total, annualized, risk-adjusted returns
- **Risk Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Trade Statistics**: Win rate, profit factor, average trade P&L
- **Compliance Metrics**: Halal compliance rate, screening accuracy
- **Execution Metrics**: Slippage, trade execution time, API response times

## 🕌 **Halal Compliance Framework**

### **Stock Screening Criteria**

Based on AAOIFI standards:

1. **Business Activity**: No involvement in prohibited industries (alcohol, gambling, tobacco, etc.)
2. **Financial Ratios**:
   - Interest income < 5% of total revenue
   - Total debt < 33% of total assets  
   - Liquid assets < 70% of total assets
3. **Revenue Sources**: < 5% from prohibited activities

### **Cryptocurrency Screening**

Pre-approved cryptocurrencies based on:

- **Utility**: Clear use case and technological innovation
- **Decentralization**: Avoid centralized control mechanisms
- **Compliance**: No gambling, lending, or interest-based features
- **Transparency**: Open-source and auditable protocols

**Approved Cryptocurrencies**:
- Bitcoin (BTC) - Digital store of value
- Ethereum (ETH) - Smart contract platform  
- Cardano (ADA) - Research-driven blockchain
- Solana (SOL) - High-performance blockchain
- Polkadot (DOT) - Interoperability protocol
- Avalanche (AVAX) - Decentralized platform
- Algorand (ALGO) - Pure proof-of-stake blockchain

## 🔬 **Testing**

Run the comprehensive test suite:

```bash
# Run all tests
python main.py --mode test

# Run specific test modules
python -m pytest halalbot/tests/ -v

# Run with coverage
python -m pytest halalbot/tests/ --cov=halalbot --cov-report=html
```

## 🔍 **Monitoring & Logging**

The system provides detailed logging and monitoring:

```bash
# Enable debug logging
python main.py --mode live --verbose

# Monitor log files
tail -f logs/trading_bot.log

# Check API health
python main.py --mode health
```

## ⚙️ **Advanced Configuration**

### **Strategy Customization**

```python
# Custom strategy weights per asset
asset_config = {
    'AAPL': {
        'strategy_weights': {
            'momentum_breakout': 0.5,
            'mean_reversion': 0.3,
            'ml_strategy': 0.2
        }
    },
    'BTC/USDT': {
        'strategy_weights': {
            'momentum_breakout': 0.6,
            'ml_strategy': 0.4
        }
    }
}
```

### **Risk Model Selection**

```yaml
# Risk models: conservative, moderate, aggressive
risk_model: moderate

# Custom risk parameters
risk_models:
  conservative:
    portfolio_risk: 0.01
    position_risk: 0.005
    max_positions: 5
  aggressive:
    portfolio_risk: 0.03
    position_risk: 0.015
    max_positions: 15
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Setup**

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run code formatting
black halalbot/
flake8 halalbot/
```

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ **Disclaimer**

**This software is for educational and research purposes only. It is not financial advice.**

- **No Investment Advice**: This system does not provide investment recommendations
- **Use at Your Own Risk**: Trading involves substantial risk of loss
- **Halal Compliance**: Consult qualified Islamic scholars for religious guidance
- **Testing Required**: Thoroughly test all strategies before live trading
- **API Risks**: External API failures may affect system performance

## 📞 **Support**

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions and ideas
- **Email**: Contact the maintainers for critical issues

## 🙏 **Acknowledgments**

- Islamic finance scholars for AAOIFI guidance
- Open-source trading and ML libraries
- Financial data providers (Alpha Vantage, FMP, Binance)
- The Python trading community

---

**Built with ❤️ for the Muslim trading community**

*"And Allah has permitted trade and has forbidden interest." - Quran 2:275*
