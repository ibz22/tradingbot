"""
Bot Manager - Manages trading bot instances and integrates with the dual-mode trading system
"""

import os
import sys
import asyncio
import threading
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Import the trading bot system
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import BotRepository, PortfolioRepository
from models import BotConfigRequest, BotResponse, PortfolioStats

logger = logging.getLogger(__name__)


class BotInstance:
    """Wrapper for a trading bot instance"""
    
    def __init__(self, bot_id: str, config: Dict[str, Any]):
        self.id = bot_id
        self.config = config
        self.status = "stopped"
        self.thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.start_time: Optional[datetime] = None
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.balance = config.get("initial_balance", 5000)
    
    async def start(self):
        """Start the bot"""
        if self.status == "running":
            return False
        
        try:
            # Import and initialize the trading bot
            if self.config["asset_type"] == "Solana":
                await self._start_solana_bot()
            else:
                await self._start_traditional_bot()
            
            self.status = "running"
            self.start_time = datetime.now()
            logger.info(f"Started bot {self.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot {self.id}: {e}")
            return False
    
    async def pause(self):
        """Pause the bot"""
        self.status = "paused"
        if self.thread:
            self.should_stop.set()
        logger.info(f"Paused bot {self.id}")
        return True
    
    async def stop(self):
        """Stop the bot"""
        self.status = "stopped"
        if self.thread:
            self.should_stop.set()
            self.thread.join(timeout=10)
        self.start_time = None
        logger.info(f"Stopped bot {self.id}")
        return True
    
    def get_runtime(self) -> str:
        """Get formatted runtime"""
        if not self.start_time or self.status == "stopped":
            return "00:00:00"
        
        runtime = datetime.now() - self.start_time
        hours, remainder = divmod(int(runtime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    async def _start_solana_bot(self):
        """Start Solana trading bot"""
        def run_solana_bot():
            try:
                # Import the dual-mode trading system
                from main import DualModeTradingSystem
                
                system = DualModeTradingSystem()
                
                # Run in simulation mode
                asyncio.run(system.run_live_mode(dry_run=True))
                
            except Exception as e:
                logger.error(f"Solana bot {self.id} error: {e}")
        
        self.thread = threading.Thread(target=run_solana_bot, daemon=True)
        self.thread.start()
    
    async def _start_traditional_bot(self):
        """Start traditional stock trading bot"""
        def run_traditional_bot():
            try:
                # Import the dual-mode trading system
                from main import DualModeTradingSystem
                
                system = DualModeTradingSystem()
                
                # Run traditional trading mode
                asyncio.run(system.run_traditional_trade(dry_run=True))
                
            except Exception as e:
                logger.error(f"Traditional bot {self.id} error: {e}")
        
        self.thread = threading.Thread(target=run_traditional_bot, daemon=True)
        self.thread.start()


class BotManager:
    """Manages all trading bot instances"""
    
    def __init__(self):
        self.bots: Dict[str, BotInstance] = {}
        self._background_task = None
    
    async def create_bot(self, config: BotConfigRequest) -> Dict[str, Any]:
        """Create a new trading bot"""
        bot_id = str(uuid.uuid4())
        
        # Convert config to dict
        bot_data = {
            "id": bot_id,
            "name": config.name,
            "asset_type": config.asset_type,
            "market": config.market,
            "strategy": config.strategy,
            "timeframe": config.timeframe,
            "paper_trading": config.paper_trading,
            "connect_api": config.connect_api,
            "initial_balance": config.initial_balance,
            "created_at": datetime.now().isoformat(),
            "config": config.dict()
        }
        
        # Save to database
        await BotRepository.create_bot(bot_data)
        
        # Create bot instance
        bot_instance = BotInstance(bot_id, bot_data)
        self.bots[bot_id] = bot_instance
        
        logger.info(f"Created bot {bot_id}: {config.name}")
        
        return self._format_bot_response(bot_instance, bot_data)
    
    async def get_bot_status(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific bot"""
        if bot_id not in self.bots:
            # Try to load from database
            bot_data = await BotRepository.get_bot(bot_id)
            if not bot_data:
                return None
            
            # Recreate bot instance
            bot_instance = BotInstance(bot_id, bot_data)
            self.bots[bot_id] = bot_instance
        else:
            bot_data = await BotRepository.get_bot(bot_id)
        
        return self._format_bot_response(self.bots[bot_id], bot_data)
    
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        """Get all bots"""
        bot_data_list = await BotRepository.get_all_bots()
        result = []
        
        for bot_data in bot_data_list:
            bot_id = bot_data["id"]
            
            # Ensure bot instance exists
            if bot_id not in self.bots:
                bot_instance = BotInstance(bot_id, bot_data)
                self.bots[bot_id] = bot_instance
            
            result.append(self._format_bot_response(self.bots[bot_id], bot_data))
        
        return result
    
    async def control_bot(self, bot_id: str, action: str) -> Dict[str, Any]:
        """Control a bot (start, pause, stop)"""
        if bot_id not in self.bots:
            raise ValueError(f"Bot {bot_id} not found")
        
        bot = self.bots[bot_id]
        
        if action == "start":
            success = await bot.start()
        elif action == "pause":
            success = await bot.pause()
        elif action == "stop":
            success = await bot.stop()
        else:
            raise ValueError(f"Invalid action: {action}")
        
        if success:
            # Update database
            await BotRepository.update_bot(bot_id, {"status": bot.status})
        
        return {"success": success, "status": bot.status}
    
    async def delete_bot(self, bot_id: str) -> Dict[str, Any]:
        """Delete a bot"""
        if bot_id in self.bots:
            await self.bots[bot_id].stop()
            del self.bots[bot_id]
        
        await BotRepository.delete_bot(bot_id)
        
        return {"success": True}
    
    async def get_portfolio_stats(self) -> PortfolioStats:
        """Get overall portfolio statistics"""
        all_bots = await self.get_all_bots()
        
        active_bots = len([bot for bot in all_bots if bot["status"] == "running"])
        new_bots = len([bot for bot in all_bots if 
                       datetime.fromisoformat(bot["createdAt"]).date() == datetime.now().date()])
        
        total_pnl = sum(bot["dailyPnl"] for bot in all_bots)
        total_value = 125000 + total_pnl  # Base portfolio value
        
        return {
            "totalValue": total_value,
            "pnl": total_pnl,
            "pnlPercent": (total_pnl / 125000) * 100,
            "activeBots": active_bots,
            "newBots": new_bots,
            "winRate": 58,  # Mock data
            "totalTrades": 200,  # Mock data
            "volume24h": 182000,  # Mock data
            "sharpeRatio": 1.42  # Mock data
        }
    
    async def get_portfolio_history(self) -> List[Dict[str, Any]]:
        """Get portfolio history"""
        # Mock portfolio history data
        history = []
        base_value = 125000
        
        for i in range(30):
            date = datetime.now() - timedelta(days=29-i)
            value = base_value + (i * 500) + (random.random() * 1000 - 500)
            pnl = value - base_value
            
            history.append({
                "timestamp": date.isoformat(),
                "value": value,
                "pnl": pnl
            })
        
        return history
    
    async def get_symbol_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        # Mock price data
        mock_prices = {
            "SOL": 159.23,
            "AAPL": 175.43,
            "MSFT": 380.52,
            "GOOGL": 142.65,
            "AMZN": 155.20
        }
        
        return mock_prices.get(symbol, 100.0)
    
    async def shutdown_all_bots(self):
        """Shutdown all bots"""
        for bot in self.bots.values():
            await bot.stop()
        
        self.bots.clear()
        logger.info("All bots shut down")
    
    def _format_bot_response(self, bot_instance: BotInstance, bot_data: Dict) -> Dict[str, Any]:
        """Format bot data for API response"""
        return {
            "id": bot_data["id"],
            "name": bot_data["name"],
            "strategy": f"{bot_data['strategy']} + TF {bot_data['timeframe']}",
            "type": bot_data["asset_type"],
            "market": bot_data["market"],
            "mode": "Paper" if bot_data["paper_trading"] else "Live",
            "isConnected": bot_data["connect_api"],
            "runtime": bot_instance.get_runtime(),
            "dailyPnl": round(bot_instance.daily_pnl + (random.random() * 100 - 50), 2),
            "status": bot_instance.status,
            "createdAt": bot_data["created_at"].split("T")[0]
        }


# Mock random for P&L simulation
import random