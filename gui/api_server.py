"""
FastAPI Server for Trading Bot GUI
Provides REST API and WebSocket endpoints for bot management
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import uvicorn

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session

from models import (
    BotInstance, BotInstanceCreate, BotInstanceResponse, 
    Trade, TradeCreate, TradeResponse,
    PerformanceLog, PerformanceSnapshot,
    BotStatus, get_db, create_tables
)
from bot_manager import BotManager
from results_exporter import ResultsExporter

# Initialize FastAPI app
app = FastAPI(
    title="Halal Trading Bot GUI",
    description="Web interface for managing multiple trading bot instances",
    version="2.2.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
bot_manager = BotManager()
results_exporter = ResultsExporter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove disconnected clients
                self.disconnect(connection)

websocket_manager = ConnectionManager()

# Create database tables on startup
create_tables()

# Bot Management Endpoints
@app.get("/api/bots", response_model=List[BotInstanceResponse])
async def list_bots(db: Session = Depends(get_db)):
    """List all bot instances"""
    bots = db.query(BotInstance).all()
    return bots

@app.post("/api/bots", response_model=BotInstanceResponse)
async def create_bot(bot_data: BotInstanceCreate, db: Session = Depends(get_db)):
    """Create a new bot instance"""
    try:
        # Create config template
        config_template = {
            "initial_capital": bot_data.initial_capital,
            "max_portfolio_risk": bot_data.max_portfolio_risk,
            "max_position_risk": bot_data.max_position_risk,
            "default_strategy_weights": bot_data.strategy_weights or {
                "momentum_breakout": 0.4,
                "mean_reversion": 0.3,
                "ml_strategy": 0.3
            },
            "stock_universe": bot_data.stock_universe or ["AAPL", "MSFT", "GOOGL"],
            "crypto_universe": bot_data.crypto_universe or ["BTC/USDT", "ETH/USDT"],
            "fmp_api_key": "demo",
            "alpaca_paper_trading": True,
            "binance_testnet": True,
            "max_interest_pct": 0.05,
            "max_debt_ratio": 0.33
        }
        
        bot = bot_manager.create_bot_instance(
            name=bot_data.name,
            config_template=config_template,
            description=bot_data.description or ""
        )
        
        # Broadcast update
        await websocket_manager.broadcast(json.dumps({
            "type": "bot_created",
            "data": {
                "id": bot.id,
                "name": bot.name,
                "status": bot.status
            }
        }))
        
        return bot
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {e}")

@app.get("/api/bots/{bot_id}", response_model=BotInstanceResponse)
async def get_bot(bot_id: int, db: Session = Depends(get_db)):
    """Get detailed bot information"""
    bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@app.post("/api/bots/{bot_id}/start")
async def start_bot(bot_id: int, mode: str = "live", dry_run: bool = True):
    """Start a bot instance"""
    try:
        success = bot_manager.start_bot(bot_id, mode=mode, dry_run=dry_run)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start bot")
        
        # Broadcast update
        await websocket_manager.broadcast(json.dumps({
            "type": "bot_started",
            "data": {"id": bot_id, "mode": mode, "dry_run": dry_run}
        }))
        
        return {"message": f"Bot {bot_id} started successfully", "mode": mode, "dry_run": dry_run}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {e}")

@app.post("/api/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, force: bool = False):
    """Stop a bot instance"""
    try:
        success = bot_manager.stop_bot(bot_id, force=force)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop bot")
        
        # Broadcast update
        await websocket_manager.broadcast(json.dumps({
            "type": "bot_stopped",
            "data": {"id": bot_id, "force": force}
        }))
        
        return {"message": f"Bot {bot_id} stopped successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {e}")

@app.post("/api/bots/{bot_id}/restart")
async def restart_bot(bot_id: int):
    """Restart a bot instance"""
    try:
        success = bot_manager.restart_bot(bot_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to restart bot")
        
        # Broadcast update
        await websocket_manager.broadcast(json.dumps({
            "type": "bot_restarted",
            "data": {"id": bot_id}
        }))
        
        return {"message": f"Bot {bot_id} restarted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart bot: {e}")

@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: int, keep_data: bool = False):
    """Delete a bot instance"""
    try:
        success = bot_manager.delete_bot(bot_id, keep_data=keep_data)
        if not success:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Broadcast update
        await websocket_manager.broadcast(json.dumps({
            "type": "bot_deleted",
            "data": {"id": bot_id}
        }))
        
        return {"message": f"Bot {bot_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete bot: {e}")

# Bot Status and Performance Endpoints
@app.get("/api/bots/{bot_id}/status")
async def get_bot_status(bot_id: int):
    """Get detailed bot status and performance"""
    try:
        status = bot_manager.get_bot_status(bot_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bot status: {e}")

@app.get("/api/bots/{bot_id}/trades", response_model=List[TradeResponse])
async def get_bot_trades(bot_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get bot trades"""
    trades = db.query(Trade).filter(Trade.bot_id == bot_id)\
               .order_by(Trade.entry_time.desc())\
               .limit(limit)\
               .all()
    return trades

@app.get("/api/bots/{bot_id}/performance")
async def get_bot_performance(bot_id: int, hours: int = 24, db: Session = Depends(get_db)):
    """Get bot performance history"""
    from datetime import timedelta
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    performance = db.query(PerformanceLog)\
                   .filter(PerformanceLog.bot_id == bot_id)\
                   .filter(PerformanceLog.timestamp >= cutoff_time)\
                   .order_by(PerformanceLog.timestamp.asc())\
                   .all()
    
    return [{
        "timestamp": perf.timestamp,
        "equity": perf.equity,
        "total_return": perf.total_return,
        "daily_return": perf.daily_return,
        "max_drawdown": perf.max_drawdown,
        "total_trades": perf.total_trades,
        "win_rate": perf.win_rate,
        "sharpe_ratio": perf.sharpe_ratio
    } for perf in performance]

# Export Endpoints
@app.post("/api/bots/{bot_id}/export")
async def export_bot_results(bot_id: int, background_tasks: BackgroundTasks, format: str = "csv"):
    """Export bot results to CSV or Google Sheets"""
    try:
        if format not in ["csv", "google_sheets"]:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'google_sheets'")
        
        # Export in background
        def export_task():
            return bot_manager.export_results(bot_id, format)
        
        background_tasks.add_task(export_task)
        
        return {"message": f"Export started for bot {bot_id}", "format": format}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

@app.get("/api/export/summary")
async def export_all_bots_summary(format: str = "csv"):
    """Export summary of all bots"""
    try:
        file_path = results_exporter.export_all_bots_summary(format)
        return {"message": "Export completed", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

@app.get("/api/export/history")
async def get_export_history():
    """Get export history"""
    try:
        return results_exporter.get_export_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get export history: {e}")

# Dashboard Summary Endpoints
@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get overall dashboard summary"""
    try:
        summary = bot_manager.get_performance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {e}")

@app.get("/api/dashboard/recent-activity")
async def get_recent_activity(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent trading activity across all bots"""
    recent_trades = db.query(Trade)\
                     .order_by(Trade.entry_time.desc())\
                     .limit(limit)\
                     .all()
    
    activities = []
    for trade in recent_trades:
        bot = db.query(BotInstance).filter(BotInstance.id == trade.bot_id).first()
        activities.append({
            "type": "trade",
            "timestamp": trade.entry_time,
            "bot_name": bot.name if bot else "Unknown",
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.entry_price,
            "status": trade.status
        })
    
    return activities

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            summary = bot_manager.get_performance_summary()
            await websocket.send_text(json.dumps({
                "type": "dashboard_update",
                "data": summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            await asyncio.sleep(5)  # More frequent updates for better responsiveness
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "2.2.0"
    }

# Serve static files for frontend
app.mount("/static", StaticFiles(directory="gui/static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Halal Trading Bot Dashboard</title>
        <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel" src="/static/dashboard.js"></script>
    </body>
    </html>
    """)

# Background task to update performance logs
async def update_performance_logs():
    """Background task to periodically update performance logs"""
    while True:
        try:
            with Session(bind=next(get_db()).bind) as db:
                running_bots = db.query(BotInstance)\
                                .filter(BotInstance.status == BotStatus.RUNNING)\
                                .all()
                
                for bot in running_bots:
                    # Create performance snapshot (simplified)
                    # In a real implementation, you'd gather actual performance data
                    perf_log = PerformanceLog(
                        bot_id=bot.id,
                        equity=bot.current_equity,
                        cash=bot.current_equity * 0.1,  # Simplified
                        positions_value=bot.current_equity * 0.9,  # Simplified
                        total_return=bot.total_return,
                        daily_return=0.001,  # Simplified
                        portfolio_risk=bot.max_portfolio_risk,
                        max_drawdown=bot.max_drawdown,
                        total_trades=bot.total_trades,
                        win_rate=bot.win_rate,
                        sharpe_ratio=bot.sharpe_ratio,
                        open_positions=1  # Simplified
                    )
                    
                    db.add(perf_log)
                
                db.commit()
                
        except Exception as e:
            logging.error(f"Error updating performance logs: {e}")
        
        await asyncio.sleep(300)  # Update every 5 minutes

# Start background task
@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(update_performance_logs())

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean shutdown"""
    bot_manager.shutdown()

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=3002,
        reload=True,
        log_level="info"
    )