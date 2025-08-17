# Solsak Trading Platform 🚀

A modern web-based trading platform that integrates with your dual-mode trading bot system. Trade both Solana tokens and traditional stocks through an intuitive dashboard interface.

![Solsak Dashboard](https://via.placeholder.com/800x400/0B1929/5B8DFF?text=Solsak+Trading+Dashboard)

## 🌟 Features

### 🎯 Dual-Mode Trading
- **Solana Trading**: Advanced DeFi strategies with real-time intelligence
- **Stock Trading**: Traditional equity trading with halal compliance
- **Unified Portfolio**: Manage both asset classes from one interface

### 📊 Advanced Dashboard
- Real-time portfolio tracking with interactive charts
- Live P&L monitoring and performance metrics
- Bot management with start/stop/pause controls
- WebSocket-powered real-time updates

### 🤖 Bot Management
- Create and configure trading bots through UI
- Support for multiple strategies (Momentum, Grid, Mean Reversion)
- Paper trading and live trading modes
- API integration with major brokers

### 💡 Intelligence Features
- Integration with your Phase 3 Solana intelligence system
- News and social media sentiment analysis
- Advanced token validation and screening
- Risk management across all positions

## 🏗️ Architecture

```
trading-platform/
├── frontend/          # Next.js 14 with TypeScript
├── backend/           # FastAPI with Python
├── nginx/             # Reverse proxy configuration
└── docker-compose.yml # Container orchestration
```

### Technology Stack

**Frontend:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Recharts for data visualization
- React Hook Form for form management

**Backend:**
- FastAPI for high-performance API
- SQLite database with SQLAlchemy
- WebSocket support for real-time updates
- Integration with your trading bot system

**Deployment:**
- Docker containers for easy deployment
- Nginx reverse proxy
- Redis for caching and sessions

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Your trading bot repository (https://github.com/ibz22/tradingbot)
- API keys for trading platforms

### 1. Clone and Setup
```bash
# Clone your trading bot repo as a submodule
git submodule add https://github.com/ibz22/tradingbot.git trading-bot

# Copy environment files
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# Edit environment files with your API keys
nano backend/.env
```

### 2. Development Setup
```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Run development servers
cd frontend && npm run dev    # Port 3000
cd backend && python main.py  # Port 8000
```

### 3. Production Deployment
```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application
open http://localhost
```

## 🔧 Configuration

### Backend Environment Variables
```bash
# Trading APIs
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
FMP_API_KEY=your_fmp_key

# Solana & Intelligence
SOLANA_RPC_URL=your_solana_rpc
NEWS_API_KEY=your_news_api_key
TWITTER_BEARER_TOKEN=your_twitter_token
```

### Frontend Environment Variables
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 📈 Usage

### Creating Your First Bot

1. **Access Dashboard**: Navigate to http://localhost:3000
2. **Click "New Bot"**: Opens the bot creation sidebar
3. **Configure Bot**:
   - Choose asset type (Solana or Stocks)
   - Select trading pair/symbol
   - Pick strategy and timeframe
   - Set initial balance
   - Enable paper trading for testing

4. **Start Trading**: Bot will begin executing your strategy

### Managing Portfolios

- **Dashboard Overview**: See total portfolio value and P&L
- **Real-time Charts**: Track performance over time
- **Active Bots**: Monitor all running trading strategies
- **Risk Metrics**: View Sharpe ratio, win rate, and drawdown

### Bot Controls

- **▶️ Start**: Begin executing the trading strategy
- **⏸️ Pause**: Temporarily halt trading
- **⏹️ Stop**: Completely stop the bot
- **✏️ Edit**: Modify bot configuration
- **🗑️ Delete**: Remove bot permanently

## 🔌 Integration with Trading Bot

The platform seamlessly integrates with your dual-mode trading bot:

### Solana Mode Integration
```python
# Runs your Solana intelligence system
from main import DualModeTradingSystem
system = DualModeTradingSystem()
await system.run_live_mode(dry_run=True)
```

### Traditional Trading Integration
```python
# Runs your stock trading system
await system.run_traditional_trade(dry_run=True)
```

### Configuration Bridge
- Reads from your `config/trading_config.yaml`
- Supports halal screening preferences
- Maintains risk management settings

## 📊 API Documentation

### Bot Management
- `GET /api/bot/list` - List all bots
- `POST /api/bot/create` - Create new bot
- `POST /api/bot/{id}/control` - Control bot (start/pause/stop)
- `GET /api/bot/{id}/status` - Get bot status

### Portfolio
- `GET /api/portfolio/stats` - Get portfolio statistics
- `GET /api/portfolio/history` - Get performance history

### Real-time Updates
- `WS /ws/live-data` - WebSocket for real-time updates

## 🔒 Security

- Environment-based configuration
- API key management
- CORS protection
- Input validation and sanitization
- Secure WebSocket connections

## 🚦 Deployment to DigitalOcean

### Server Setup (170.64.239.3)
```bash
# SSH to your server
ssh root@170.64.239.3

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone [your-website-repo]
cd trading-platform

# Configure environment
cp backend/.env.example backend/.env
# Edit with your API keys

# Deploy
docker-compose up -d

# Setup SSL (optional)
# Configure SSL certificates in nginx/ssl/
```

### Domain Setup
1. Point your domain to `170.64.239.3`
2. Update nginx configuration with your domain
3. Install SSL certificates (Let's Encrypt recommended)

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check logs
docker-compose logs backend

# Verify trading bot integration
cd trading-bot && python main.py --help
```

**Frontend connection issues:**
```bash
# Check API URL in environment
grep NEXT_PUBLIC_API_URL frontend/.env

# Test backend directly
curl http://localhost:8000/api/portfolio/stats
```

**WebSocket connection failed:**
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/live-data
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of your revolutionary dual-mode trading bot
- Integrates Phase 3 Solana intelligence capabilities
- Designed for institutional-grade performance

---

**Ready to revolutionize your trading experience!** 🚀

For support, please open an issue or contact the development team.