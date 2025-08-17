#!/usr/bin/env python3
"""
Solsak Trading Platform - FastAPI Backend
==========================================

Integrates with the dual-mode trading bot system for web-based management.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add the parent directory to path to import trading bot
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from bot_manager import BotManager
from database import init_db, get_db
from websocket_manager import WebSocketManager
from models import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers
bot_manager = BotManager()
ws_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Solsak Trading Platform Backend...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down bot manager...")
    await bot_manager.shutdown_all_bots()
    logger.info("Backend shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Solsak Trading Platform API",
    description="Backend API for the Solsak dual-mode trading platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Solsak Trading Platform API", "status": "operational"}

# Portfolio endpoints
@app.get("/api/portfolio/stats")
async def get_portfolio_stats():
    """Get overall portfolio statistics"""
    try:
        stats = await bot_manager.get_portfolio_stats()
        return {"data": stats, "success": True}
    except Exception as e:
        logger.error(f"Failed to get portfolio stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio stats")

@app.get("/api/portfolio/history")
async def get_portfolio_history():
    """Get portfolio performance history"""
    try:
        history = await bot_manager.get_portfolio_history()
        return {"data": history, "success": True}
    except Exception as e:
        logger.error(f"Failed to get portfolio history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio history")

# Bot management endpoints
@app.get("/api/bot/list")
async def list_bots():
    """List all trading bots"""
    try:
        bots = await bot_manager.get_all_bots()
        return {"data": bots, "success": True}
    except Exception as e:
        logger.error(f"Failed to list bots: {e}")
        raise HTTPException(status_code=500, detail="Failed to list bots")

@app.post("/api/bot/create")
async def create_bot(config: BotConfigRequest):
    """Create a new trading bot"""
    try:
        bot = await bot_manager.create_bot(config)
        await ws_manager.broadcast({
            "type": "bot_created",
            "data": bot
        })
        return {"data": bot, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bot")

@app.get("/api/bot/{bot_id}/status")
async def get_bot_status(bot_id: str):
    """Get status of a specific bot"""
    try:
        bot = await bot_manager.get_bot_status(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return {"data": bot, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot status")

@app.post("/api/bot/{bot_id}/control")
async def control_bot(bot_id: str, action: BotControlRequest):
    """Control a bot (start, pause, stop)"""
    try:
        result = await bot_manager.control_bot(bot_id, action.action)
        await ws_manager.broadcast({
            "type": "bot_updated",
            "data": {"bot_id": bot_id, "action": action.action, "result": result}
        })
        return {"data": result, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to control bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to control bot")

@app.delete("/api/bot/{bot_id}")
async def delete_bot(bot_id: str):
    """Delete a trading bot"""
    try:
        result = await bot_manager.delete_bot(bot_id)
        await ws_manager.broadcast({
            "type": "bot_deleted",
            "data": {"bot_id": bot_id}
        })
        return {"data": result, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/live-data")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# Market data endpoints
@app.get("/api/markets/solana")
async def get_solana_markets():
    """Get available Solana trading pairs"""
    markets = [
        "SOL/USDC", "RAY/USDC", "ORCA/USDC", "BONK/USDC", 
        "JUP/USDC", "WIF/USDC", "POPCAT/USDC"
    ]
    return {"data": markets, "success": True}

@app.get("/api/markets/stocks")
async def get_stock_markets():
    """Get available stock symbols"""
    markets = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
        "NVDA", "META", "GLD", "SPY", "QQQ"
    ]
    return {"data": markets, "success": True}


@app.get("/api/markets/stocks")
async def get_stock_prices():
    """Get real-time stock prices from Alpaca"""
    try:
        # This would connect to your Alpaca integration
        # For now, returning mock data that can be replaced with real Alpaca calls
        stocks = [
            {"symbol": "AAPL", "price": 242.84, "change": 1.2, "volume": "52.3M", "high": 244.20, "low": 240.50},
            {"symbol": "TSLA", "price": 412.36, "change": -2.8, "volume": "98.7M", "high": 425.00, "low": 408.00},
            {"symbol": "MSFT", "price": 468.25, "change": 0.8, "volume": "22.1M", "high": 470.00, "low": 465.30},
            {"symbol": "NVDA", "price": 145.62, "change": 4.2, "volume": "284M", "high": 147.00, "low": 140.20},
            {"symbol": "AMD", "price": 182.94, "change": 3.1, "volume": "68.4M", "high": 184.50, "low": 178.20},
        ]
        return stocks
    except Exception as e:
        logger.error(f"Failed to fetch stock prices: {e}")
        return []

@app.get("/api/price/{symbol}")
async def get_symbol_price(symbol: str):
    """Get current price for a symbol"""
    try:
        price = await bot_manager.get_symbol_price(symbol)
        return {"data": {"symbol": symbol, "price": price}, "success": True}
    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get price")

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )