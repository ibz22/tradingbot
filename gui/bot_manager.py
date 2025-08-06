"""
Multi-Bot Management System
Handles running multiple trading bot instances with monitoring and control
"""

import asyncio
import json
import logging
import os
import psutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml

from sqlalchemy.orm import Session
from models import BotInstance, Trade, PerformanceLog, BotStatus, get_db, create_tables
from results_exporter import ResultsExporter

@dataclass
class BotProcess:
    """Container for bot process information"""
    instance: BotInstance
    process: Optional[subprocess.Popen] = None
    config_path: Optional[str] = None
    log_file: Optional[str] = None
    heartbeat_thread: Optional[threading.Thread] = None
    is_stopping: bool = False

class BotManager:
    """Manages multiple trading bot instances"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs" / "bots"
        self.configs_dir = self.base_dir / "configs"
        self.processes: Dict[int, BotProcess] = {}
        self.results_exporter = ResultsExporter()
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database tables
        create_tables()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / "bot_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("🤖 Bot Manager initialized")

    def create_bot_instance(self, 
                          name: str, 
                          config_template: Dict[str, Any],
                          description: str = "") -> BotInstance:
        """Create a new bot instance with custom configuration"""
        with Session(bind=next(get_db()).bind) as db:
            # Check if name already exists
            existing = db.query(BotInstance).filter(BotInstance.name == name).first()
            if existing:
                raise ValueError(f"Bot instance '{name}' already exists")
            
            # Create config file
            config_file = self.configs_dir / f"{name}_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_template, f, default_flow_style=False)
            
            # Create bot instance
            bot = BotInstance(
                name=name,
                description=description,
                config_file=str(config_file),
                initial_capital=config_template.get('initial_capital', 100000),
                max_portfolio_risk=config_template.get('max_portfolio_risk', 0.02),
                max_position_risk=config_template.get('max_position_risk', 0.01),
                strategy_weights=config_template.get('default_strategy_weights', {}),
                stock_universe=config_template.get('stock_universe', []),
                crypto_universe=config_template.get('crypto_universe', []),
                current_equity=config_template.get('initial_capital', 100000)
            )
            
            db.add(bot)
            db.commit()
            db.refresh(bot)
            
            self.logger.info(f"✅ Created bot instance: {name}")
            return bot

    def start_bot(self, bot_id: int, mode: str = "live", dry_run: bool = True) -> bool:
        """Start a bot instance"""
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                raise ValueError(f"Bot instance {bot_id} not found")
            
            if bot_id in self.processes and self.processes[bot_id].process:
                if self.processes[bot_id].process.poll() is None:
                    self.logger.warning(f"Bot {bot.name} is already running")
                    return False
            
            # Update status
            bot.status = BotStatus.STARTING
            bot.start_time = datetime.now(timezone.utc)
            bot.error_message = None
            db.commit()
            
            # Setup log file
            log_file = self.logs_dir / f"{bot.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            # Build command
            cmd = [
                "python", str(self.base_dir / "main.py"),
                "--mode", mode,
                "--config", bot.config_file
            ]
            
            if dry_run:
                cmd.append("--dry-run")
            
            try:
                # Start process
                with open(log_file, 'w') as log_f:
                    process = subprocess.Popen(
                        cmd,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        cwd=self.base_dir,
                        env={**os.environ, "BOT_ID": str(bot_id)}
                    )
                
                # Store process info
                bot_process = BotProcess(
                    instance=bot,
                    process=process,
                    config_path=bot.config_file,
                    log_file=str(log_file)
                )
                
                self.processes[bot_id] = bot_process
                
                # Update database
                bot.process_id = process.pid
                bot.status = BotStatus.RUNNING
                bot.last_heartbeat = datetime.now(timezone.utc)
                db.commit()
                
                # Start heartbeat monitoring
                self._start_heartbeat_monitoring(bot_id)
                
                self.logger.info(f"🚀 Started bot {bot.name} (PID: {process.pid})")
                return True
                
            except Exception as e:
                bot.status = BotStatus.ERROR
                bot.error_message = str(e)
                db.commit()
                
                self.logger.error(f"❌ Failed to start bot {bot.name}: {e}")
                return False

    def stop_bot(self, bot_id: int, force: bool = False) -> bool:
        """Stop a bot instance"""
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                raise ValueError(f"Bot instance {bot_id} not found")
            
            if bot_id not in self.processes:
                bot.status = BotStatus.STOPPED
                db.commit()
                return True
            
            bot_process = self.processes[bot_id]
            bot_process.is_stopping = True
            
            if not bot_process.process:
                bot.status = BotStatus.STOPPED
                db.commit()
                return True
            
            # Update status
            bot.status = BotStatus.STOPPING
            db.commit()
            
            try:
                if force:
                    bot_process.process.kill()
                else:
                    bot_process.process.terminate()
                
                # Wait for process to exit
                try:
                    bot_process.process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing bot {bot.name}")
                    bot_process.process.kill()
                    bot_process.process.wait()
                
                # Clean up
                del self.processes[bot_id]
                
                # Update database
                bot.status = BotStatus.STOPPED
                bot.process_id = None
                db.commit()
                
                self.logger.info(f"⏹️ Stopped bot {bot.name}")
                return True
                
            except Exception as e:
                bot.status = BotStatus.ERROR
                bot.error_message = f"Failed to stop: {e}"
                db.commit()
                
                self.logger.error(f"❌ Failed to stop bot {bot.name}: {e}")
                return False

    def restart_bot(self, bot_id: int) -> bool:
        """Restart a bot instance"""
        self.logger.info(f"🔄 Restarting bot {bot_id}")
        
        # Stop first
        if bot_id in self.processes:
            self.stop_bot(bot_id)
            time.sleep(2)  # Brief pause
        
        # Start again
        return self.start_bot(bot_id)

    def get_bot_status(self, bot_id: int) -> Dict[str, Any]:
        """Get detailed status of a bot instance"""
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                return {"error": "Bot not found"}
            
            # Get latest performance
            latest_performance = db.query(PerformanceLog)\
                .filter(PerformanceLog.bot_id == bot_id)\
                .order_by(PerformanceLog.timestamp.desc())\
                .first()
            
            # Get recent trades
            recent_trades = db.query(Trade)\
                .filter(Trade.bot_id == bot_id)\
                .order_by(Trade.entry_time.desc())\
                .limit(10)\
                .all()
            
            # Process information
            process_info = None
            if bot_id in self.processes and self.processes[bot_id].process:
                process = self.processes[bot_id].process
                try:
                    ps_process = psutil.Process(process.pid)
                    process_info = {
                        "pid": process.pid,
                        "cpu_percent": ps_process.cpu_percent(),
                        "memory_mb": ps_process.memory_info().rss / 1024 / 1024,
                        "status": ps_process.status(),
                        "create_time": datetime.fromtimestamp(ps_process.create_time())
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_info = {"error": "Process not accessible"}
            
            return {
                "bot": {
                    "id": bot.id,
                    "name": bot.name,
                    "status": bot.status,
                    "description": bot.description,
                    "created_at": bot.created_at,
                    "start_time": bot.start_time,
                    "last_heartbeat": bot.last_heartbeat,
                    "error_message": bot.error_message,
                    "config_file": bot.config_file
                },
                "performance": {
                    "initial_capital": bot.initial_capital,
                    "current_equity": latest_performance.equity if latest_performance else bot.current_equity,
                    "total_return": latest_performance.total_return if latest_performance else bot.total_return,
                    "total_trades": bot.total_trades,
                    "win_rate": bot.win_rate,
                    "sharpe_ratio": bot.sharpe_ratio,
                    "max_drawdown": bot.max_drawdown
                },
                "recent_trades": [
                    {
                        "symbol": trade.symbol,
                        "side": trade.side,
                        "quantity": trade.quantity,
                        "entry_price": trade.entry_price,
                        "entry_time": trade.entry_time,
                        "pnl": trade.pnl,
                        "status": trade.status
                    } for trade in recent_trades
                ],
                "process": process_info
            }

    def list_bots(self) -> List[Dict[str, Any]]:
        """List all bot instances with summary info"""
        with Session(bind=next(get_db()).bind) as db:
            bots = db.query(BotInstance).all()
            return [
                {
                    "id": bot.id,
                    "name": bot.name,
                    "status": bot.status,
                    "description": bot.description,
                    "created_at": bot.created_at,
                    "total_return": bot.total_return,
                    "total_trades": bot.total_trades,
                    "current_equity": bot.current_equity,
                    "last_heartbeat": bot.last_heartbeat
                } for bot in bots
            ]

    def delete_bot(self, bot_id: int, keep_data: bool = False) -> bool:
        """Delete a bot instance"""
        # Stop first if running
        if bot_id in self.processes:
            self.stop_bot(bot_id, force=True)
        
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                return False
            
            bot_name = bot.name
            
            if not keep_data:
                # Delete all related data
                db.query(Trade).filter(Trade.bot_id == bot_id).delete()
                db.query(PerformanceLog).filter(PerformanceLog.bot_id == bot_id).delete()
            
            # Delete bot instance
            db.delete(bot)
            db.commit()
            
            # Clean up config file
            if bot.config_file and os.path.exists(bot.config_file):
                os.remove(bot.config_file)
            
            self.logger.info(f"🗑️ Deleted bot {bot_name}")
            return True

    def export_results(self, bot_id: int, format: str = "csv", 
                      output_path: Optional[str] = None) -> str:
        """Export bot results to CSV or Google Sheets"""
        return self.results_exporter.export_bot_results(bot_id, format, output_path)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all bots"""
        with Session(bind=next(get_db()).bind) as db:
            bots = db.query(BotInstance).all()
            
            total_equity = sum(bot.current_equity for bot in bots)
            total_initial = sum(bot.initial_capital for bot in bots)
            total_trades = sum(bot.total_trades for bot in bots)
            
            running_bots = len([bot for bot in bots if bot.status == BotStatus.RUNNING])
            
            return {
                "total_bots": len(bots),
                "running_bots": running_bots,
                "stopped_bots": len(bots) - running_bots,
                "total_equity": total_equity,
                "total_initial_capital": total_initial,
                "overall_return": ((total_equity - total_initial) / total_initial) if total_initial > 0 else 0,
                "total_trades": total_trades,
                "avg_return_per_bot": sum(bot.total_return for bot in bots) / len(bots) if bots else 0
            }

    def _start_heartbeat_monitoring(self, bot_id: int):
        """Start heartbeat monitoring for a bot"""
        def heartbeat_worker():
            while bot_id in self.processes and not self.processes[bot_id].is_stopping:
                try:
                    with Session(bind=next(get_db()).bind) as db:
                        bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
                        if bot:
                            bot.last_heartbeat = datetime.now(timezone.utc)
                            db.commit()
                except Exception as e:
                    self.logger.error(f"Heartbeat error for bot {bot_id}: {e}")
                
                time.sleep(60)  # Update every minute
        
        thread = threading.Thread(target=heartbeat_worker, daemon=True)
        thread.start()

    def _monitor_processes(self):
        """Monitor all bot processes for crashes and updates"""
        while self.monitoring_active:
            try:
                for bot_id, bot_process in list(self.processes.items()):
                    if bot_process.process and bot_process.process.poll() is not None:
                        # Process has exited
                        exit_code = bot_process.process.returncode
                        
                        with Session(bind=next(get_db()).bind) as db:
                            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
                            if bot:
                                if exit_code == 0:
                                    bot.status = BotStatus.STOPPED
                                    self.logger.info(f"Bot {bot.name} exited normally")
                                else:
                                    bot.status = BotStatus.ERROR
                                    bot.error_message = f"Process exited with code {exit_code}"
                                    self.logger.error(f"Bot {bot.name} crashed with exit code {exit_code}")
                                
                                bot.process_id = None
                                db.commit()
                        
                        # Clean up
                        del self.processes[bot_id]
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Monitor process error: {e}")
                time.sleep(60)

    def shutdown(self):
        """Shutdown bot manager and all running bots"""
        self.logger.info("🛑 Shutting down Bot Manager...")
        self.monitoring_active = False
        
        # Stop all running bots
        for bot_id in list(self.processes.keys()):
            self.stop_bot(bot_id, force=True)
        
        self.logger.info("Bot Manager shutdown complete")

    def __del__(self):
        self.shutdown()