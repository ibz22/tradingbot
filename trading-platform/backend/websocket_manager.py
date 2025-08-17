"""
WebSocket Manager for real-time updates
"""

import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial connection message
        await self.send_to_client(websocket, {
            "type": "connection_established",
            "data": {"message": "Connected to Solsak Trading Platform"}
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_portfolio_update(self, stats: Dict[str, Any]):
        """Broadcast portfolio stats update"""
        await self.broadcast({
            "type": "portfolio_update",
            "data": stats
        })
    
    async def broadcast_bot_update(self, bot_data: Dict[str, Any]):
        """Broadcast bot status update"""
        await self.broadcast({
            "type": "bot_update",
            "data": bot_data
        })
    
    async def broadcast_price_update(self, symbol: str, price: float, change_percent: float):
        """Broadcast price update"""
        await self.broadcast({
            "type": "price_update",
            "data": {
                "symbol": symbol,
                "price": price,
                "change_percent": change_percent,
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(1000))}})
            }
        })
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)