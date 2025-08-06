# 🖥️ Halal Trading Bot GUI System

A comprehensive web-based interface for managing multiple Islamic finance-compliant trading bot instances with real-time monitoring, performance tracking, and results export.

## 🌟 Features

### 📊 **Multi-Bot Management**
- Create, start, stop, and monitor multiple bot instances
- Individual configuration for each bot (capital, risk, strategies)
- Real-time status monitoring and process health checks
- Support for both live and paper trading modes

### 📈 **Performance Tracking**
- Real-time performance metrics and visualizations
- Comprehensive trade history and analytics
- Risk metrics (Sharpe ratio, max drawdown, win rate)
- Portfolio-level overview across all bots

### 📋 **Results Export**
- Export to CSV format with detailed trade data
- Google Sheets integration for cloud-based analysis
- Performance summaries and trade analytics
- Historical performance data export

### 🔄 **Real-time Updates**
- WebSocket-based live updates
- Dashboard auto-refresh every 30 seconds
- Real-time trade notifications
- Bot status change alerts

### 🕌 **Halal Compliance**
- Built-in Islamic finance compliance monitoring
- AAOIFI-standard screening for all trades
- Halal asset universe management
- Compliance reporting and audit trails

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   FastAPI       │    │   Bot Manager   │
│   (React/JS)    │◄──►│   API Server    │◄──►│   Process       │
│   Port 3002     │    │   Port 3002     │    │   Controller    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   SQLite DB     │              │
         │              │   Performance   │              │
         │              │   Tracking      │              │
         │              └─────────────────┘              │
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 │
                ┌─────────────────▼─────────────────┐
                │        Trading Bot Instances      │
                │     (Multiple Processes)          │
                │   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │
                │   │Bot 1│ │Bot 2│ │Bot 3│ │Bot N│ │
                │   └─────┘ └─────┘ └─────┘ └─────┘ │
                └───────────────────────────────────┘
```

## 🚀 Quick Start

### **Option 1: Local Development (Recommended for Testing)**

```bash
# 1. Navigate to your trading bot directory
cd /path/to/tradingbot

# 2. Install GUI dependencies
pip install -r gui/requirements.txt

# 3. Run the deployment script for local setup
python gui/deploy.py --local

# 4. Configure your API keys
nano .env  # Edit with your actual API keys

# 5. Start the GUI server
python gui/api_server.py

# 6. Access the dashboard
# Open browser: http://localhost:3002
```

### **Option 2: Digital Ocean Server Deployment**

```bash
# 1. SSH into your Digital Ocean server
ssh root@your-server-ip

# 2. Clone your repository
git clone https://github.com/yourusername/tradingbot.git
cd tradingbot

# 3. Run server deployment (requires sudo)
sudo python gui/deploy.py --server --domain yourdomain.com --email admin@yourdomain.com

# 4. Configure API keys
nano .env

# 5. Start the service
sudo systemctl start halal-trading-gui

# 6. Access via your domain
# Open browser: https://yourdomain.com
```

### **Option 3: Docker Deployment**

```bash
# 1. Build and start with Docker Compose
cd tradingbot
docker-compose -f gui/docker-compose.yml up -d

# 2. Access the dashboard
# Open browser: http://localhost:3002
```

## 🎛️ Dashboard Usage

### **Creating a New Bot**

1. Click "Create New Bot" button
2. Fill in bot details:
   - **Name**: Unique identifier for your bot
   - **Initial Capital**: Starting capital amount
   - **Risk Parameters**: Portfolio and position risk limits
   - **Stock Universe**: Comma-separated list of stocks to trade
   - **Crypto Universe**: Comma-separated list of cryptocurrencies
3. Click "Create Bot"

### **Managing Bots**

- **Start Bot**: 
  - "Start (Dry)" - Paper trading mode for testing
  - "Start (Live)" - Live trading with real money
- **Stop Bot**: Gracefully stop a running bot
- **View Details**: Click bot name to see detailed performance
- **Export Results**: Download CSV or export to Google Sheets
- **Delete Bot**: Remove bot and optionally keep data

### **Monitoring Performance**

- **Dashboard Overview**: Real-time summary of all bots
- **Individual Bot Metrics**: Detailed performance for each bot
- **Recent Activity**: Latest trades across all bots
- **Real-time Updates**: Automatic refresh via WebSocket

## 📊 Exported Data Format

### **CSV Export Structure**

1. **Summary CSV** - Bot overview and key metrics
2. **Trades CSV** - Detailed trade history
3. **Performance CSV** - Time-series performance data
4. **Analysis CSV** - Trade analytics and statistics

### **Google Sheets Integration**

To enable Google Sheets export:

1. Create Google Service Account
2. Download credentials JSON file
3. Save as `google_sheets_credentials.json` in project root
4. Share target spreadsheet with service account email

## ⚙️ Configuration

### **Environment Variables (.env)**

```env
# Trading API Keys
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
BINANCE_API_KEY=your_binance_key_here
BINANCE_SECRET_KEY=your_binance_secret_here
FMP_API_KEY=your_fmp_key_here

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DATABASE_URL=sqlite:///./trading_bots.db

# Server Configuration
PORT=3002
HOST=0.0.0.0
```

### **Bot Configuration Templates**

Each bot gets its own `config.yaml` with:

```yaml
# Risk Management
initial_capital: 100000
max_portfolio_risk: 0.02
max_position_risk: 0.01

# Strategy Weights
default_strategy_weights:
  momentum_breakout: 0.4
  mean_reversion: 0.3
  ml_strategy: 0.3

# Asset Universes
stock_universe:
  - AAPL
  - MSFT
  - GOOGL

crypto_universe:
  - BTC/USDT
  - ETH/USDT
  - ADA/USDT

# Halal Screening
max_interest_pct: 0.05
max_debt_ratio: 0.33
```

## 🔧 API Endpoints

### **Bot Management**
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create new bot
- `GET /api/bots/{id}` - Get bot details
- `POST /api/bots/{id}/start` - Start bot
- `POST /api/bots/{id}/stop` - Stop bot
- `DELETE /api/bots/{id}` - Delete bot

### **Performance & Data**
- `GET /api/bots/{id}/status` - Bot status and metrics
- `GET /api/bots/{id}/trades` - Bot trade history
- `GET /api/bots/{id}/performance` - Performance time series
- `POST /api/bots/{id}/export` - Export bot results

### **Dashboard**
- `GET /api/dashboard/summary` - Overall portfolio summary
- `GET /api/dashboard/recent-activity` - Recent trades
- `WS /ws` - WebSocket for real-time updates

## 🐳 Docker Deployment

The system includes full Docker support:

```bash
# Start all services
docker-compose -f gui/docker-compose.yml up -d

# View logs
docker-compose -f gui/docker-compose.yml logs -f gui-server

# Stop services
docker-compose -f gui/docker-compose.yml down
```

**Services included:**
- GUI Server (Port 3002)
- Redis for caching
- Nginx reverse proxy
- Prometheus monitoring (Port 9090)
- Grafana dashboards (Port 3001)

## 🔒 Security Considerations

### **Production Deployment**
1. **Use HTTPS**: SSL certificates via Let's Encrypt
2. **Firewall**: UFW configured for necessary ports only
3. **User Permissions**: Non-root user for application
4. **API Keys**: Store securely in environment variables
5. **Database**: Regular backups of SQLite database

### **Access Control**
- Web interface accessible on configured port (default: 3002)
- API endpoints protected by CORS configuration
- WebSocket connections require valid origin

## 🔍 Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Find process using port 3002
   lsof -i :3002
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Dependencies Missing**
   ```bash
   # Reinstall requirements
   pip install -r gui/requirements.txt --force-reinstall
   ```

3. **Database Errors**
   ```bash
   # Recreate database
   python -c "from gui.models import create_tables; create_tables()"
   ```

4. **Bot Won't Start**
   - Check API keys in `.env` file
   - Verify bot configuration file exists
   - Check available capital and risk parameters

### **Logs Location**

- **GUI Server**: `logs/bots/bot_manager.log`
- **Individual Bots**: `logs/bots/{bot_name}_{timestamp}.log`
- **System Service**: `journalctl -u halal-trading-gui -f`

## 📈 Performance Optimization

### **Database Maintenance**
- Automatic cleanup of old performance logs (30+ days)
- Regular SQLite VACUUM for optimization
- Performance log sampling for long-running bots

### **Resource Monitoring**
- Process CPU and memory monitoring
- Bot heartbeat tracking
- Automatic restart on failures

## 🤝 Support & Contributing

### **Getting Help**
1. Check logs for error messages
2. Review configuration files
3. Test with dry-run mode first
4. Monitor system resources

### **Development**
- React frontend with Bootstrap styling
- FastAPI backend with SQLAlchemy ORM
- WebSocket for real-time features
- Modular architecture for easy extension

---

## 🎯 Next Steps

After setting up the GUI:

1. **Configure API Keys** - Add your trading API credentials
2. **Create Test Bot** - Start with dry-run mode
3. **Monitor Performance** - Watch real-time metrics
4. **Export Results** - Download performance data
5. **Scale Up** - Add multiple bot instances

**Your Halal Trading Bot GUI is now ready for professional multi-bot trading operations!** 🚀🕌

---

*Built with ❤️ for the Muslim trading community*