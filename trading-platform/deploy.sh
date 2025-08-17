#!/bin/bash

# Solsak Trading Platform Deployment Script
# ===========================================

set -e  # Exit on any error

echo "🚀 Starting Solsak Trading Platform Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p data ssl

# Check if environment files exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Backend .env file not found. Creating from example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your API keys before continuing!${NC}"
    read -p "Press Enter to continue after editing .env file..."
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}⚠️  Frontend .env file not found. Creating from example...${NC}"
    cp frontend/.env.example frontend/.env
fi

# Check if trading bot submodule exists
if [ ! -d "trading-bot" ]; then
    echo -e "${YELLOW}⚠️  Trading bot directory not found. You may need to add it as a submodule:${NC}"
    echo "    git submodule add https://github.com/ibz22/tradingbot.git trading-bot"
fi

# Build and start services
echo -e "${BLUE}🔨 Building Docker containers...${NC}"
docker-compose build

echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"

# Check backend
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend is not responding${NC}"
    echo -e "${YELLOW}📋 Backend logs:${NC}"
    docker-compose logs backend
fi

# Check frontend
if curl -f http://localhost:3000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
    echo -e "${YELLOW}📋 Frontend logs:${NC}"
    docker-compose logs frontend
fi

# Show running containers
echo -e "${BLUE}📊 Running containers:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📱 Access your Solsak Trading Platform:${NC}"
echo -e "   🌐 Web Interface: ${GREEN}http://localhost${NC}"
echo -e "   🔌 API Endpoint: ${GREEN}http://localhost:8000${NC}"
echo -e "   📊 API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo -e "   📊 View logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "   🛑 Stop services: ${YELLOW}docker-compose down${NC}"
echo -e "   🔄 Restart services: ${YELLOW}docker-compose restart${NC}"
echo -e "   📈 View status: ${YELLOW}docker-compose ps${NC}"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Configure your API keys in backend/.env"
echo -e "   2. Create your first trading bot"
echo -e "   3. Enable live trading with proper API connections"
echo -e "   4. Monitor your portfolio performance"
echo ""
echo -e "${GREEN}Happy Trading! 🚀${NC}"