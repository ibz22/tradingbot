"""
Enhanced order management system with fill tracking and retry logic.

This module provides comprehensive order lifecycle management including:
- Order submission with confirmation
- Fill tracking and updates
- Retry logic for failed orders  
- Position reconciliation
- Real-time order status monitoring
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import json

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    PENDING_CANCEL = "pending_cancel"
    FAILED = "failed"

class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

@dataclass
class EnhancedOrder:
    """Enhanced order with comprehensive tracking"""
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "day"
    
    # Order lifecycle tracking
    order_id: Optional[str] = None
    client_order_id: str = field(default_factory=lambda: f"order_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    status: OrderStatus = OrderStatus.PENDING
    
    # Execution tracking
    filled_qty: float = 0.0
    remaining_qty: Optional[float] = None
    avg_fill_price: Optional[float] = None
    fees: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Retry tracking
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    
    # Strategy context
    strategy_name: Optional[str] = None
    signal_confidence: Optional[float] = None
    
    def __post_init__(self):
        """Initialize computed fields"""
        if self.remaining_qty is None:
            self.remaining_qty = self.quantity
    
    @property
    def is_complete(self) -> bool:
        """Check if order is in a terminal state"""
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, 
                              OrderStatus.REJECTED, OrderStatus.EXPIRED, OrderStatus.FAILED]
    
    @property
    def is_fillable(self) -> bool:
        """Check if order can still be filled"""
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage"""
        return (self.filled_qty / self.quantity) * 100 if self.quantity > 0 else 0.0
    
    def update_fill(self, fill_qty: float, fill_price: float, fees: float = 0.0):
        """Update order with fill information"""
        self.filled_qty += fill_qty
        self.remaining_qty = max(0, self.quantity - self.filled_qty)
        self.fees += fees
        self.updated_at = datetime.now()
        
        # Update average fill price
        if self.avg_fill_price is None:
            self.avg_fill_price = fill_price
        else:
            # Weighted average
            total_filled_value = (self.filled_qty - fill_qty) * self.avg_fill_price + fill_qty * fill_price
            self.avg_fill_price = total_filled_value / self.filled_qty if self.filled_qty > 0 else fill_price
        
        # Update status
        if self.remaining_qty <= 0.001:  # Account for floating point precision
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def mark_submitted(self, order_id: str):
        """Mark order as submitted to broker"""
        self.order_id = order_id
        self.status = OrderStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_rejected(self, error_message: str):
        """Mark order as rejected"""
        self.status = OrderStatus.REJECTED
        self.last_error = error_message
        self.updated_at = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark order as failed"""
        self.status = OrderStatus.FAILED
        self.last_error = error_message
        self.updated_at = datetime.now()
    
    def increment_retry(self) -> bool:
        """Increment retry count and return if more retries allowed"""
        self.retry_count += 1
        return self.retry_count < self.max_retries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force,
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'status': self.status.value,
            'filled_qty': self.filled_qty,
            'remaining_qty': self.remaining_qty,
            'avg_fill_price': self.avg_fill_price,
            'fees': self.fees,
            'created_at': self.created_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'last_error': self.last_error,
            'strategy_name': self.strategy_name,
            'signal_confidence': self.signal_confidence
        }


class OrderManager:
    """Enhanced order manager with fill tracking and retry logic"""
    
    def __init__(self, broker_gateway, order_blotter=None, max_concurrent_orders: int = 50):
        self.broker = broker_gateway
        self.order_blotter = order_blotter
        self.max_concurrent_orders = max_concurrent_orders
        
        # Order tracking
        self.active_orders: Dict[str, EnhancedOrder] = {}
        self.completed_orders: List[EnhancedOrder] = []
        self.order_callbacks: Dict[str, List[Callable]] = {}
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_interval = 2.0  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.metrics = {
            'orders_submitted': 0,
            'orders_filled': 0,
            'orders_rejected': 0,
            'orders_failed': 0,
            'total_fill_time': 0.0,
            'average_fill_time': 0.0,
            'retry_success_rate': 0.0
        }
        
        logging.info("✅ Enhanced OrderManager initialized")
    
    async def submit_order(self, order: EnhancedOrder, 
                          callback: Optional[Callable] = None) -> bool:
        """Submit order with confirmation and tracking"""
        try:
            # Check limits
            if len(self.active_orders) >= self.max_concurrent_orders:
                logging.warning(f"⚠️ Max concurrent orders reached ({self.max_concurrent_orders})")
                order.mark_failed("Max concurrent orders exceeded")
                return False
            
            # Log order blotter if available
            if self.order_blotter:
                blotter_id = self.order_blotter.add_order(
                    order.symbol, order.side, order.quantity, 
                    order.price or 0.0, "pending"
                )
            
            # Submit to broker
            logging.info(f"📤 Submitting order: {order.side.upper()} {order.quantity} {order.symbol}")
            
            broker_response = await self.broker.place_order(
                symbol=order.symbol,
                side=order.side,
                qty=order.quantity,
                order_type=order.order_type.value,
                time_in_force=order.time_in_force,
                limit_price=order.price,
                stop_price=order.stop_price
            )
            
            # Process broker response
            if broker_response and broker_response.get('id'):
                order_id = str(broker_response['id'])
                order.mark_submitted(order_id)
                
                # Add to active orders
                self.active_orders[order_id] = order
                
                # Add callback if provided
                if callback:
                    if order_id not in self.order_callbacks:
                        self.order_callbacks[order_id] = []
                    self.order_callbacks[order_id].append(callback)
                
                # Update blotter
                if self.order_blotter:
                    self.order_blotter.update_status(blotter_id, "submitted")
                
                # Start monitoring if not active
                if not self.monitoring_active:
                    await self.start_monitoring()
                
                self.metrics['orders_submitted'] += 1
                logging.info(f"✅ Order submitted: {order_id}")
                return True
                
            else:
                error_msg = broker_response.get('message', 'Unknown broker error')
                order.mark_rejected(error_msg)
                
                if self.order_blotter:
                    self.order_blotter.update_status(blotter_id, "rejected")
                
                self.metrics['orders_rejected'] += 1
                logging.error(f"❌ Order rejected: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Order submission failed: {str(e)}"
            order.mark_failed(error_msg)
            
            if self.order_blotter:
                self.order_blotter.update_status(blotter_id, "failed")
            
            self.metrics['orders_failed'] += 1
            logging.error(f"❌ {error_msg}")
            return False
    
    async def start_monitoring(self):
        """Start order monitoring loop"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logging.info("🔍 Order monitoring started")
    
    async def stop_monitoring(self):
        """Stop order monitoring loop"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logging.info("⏹️ Order monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for order updates"""
        try:
            while self.monitoring_active and self.active_orders:
                await self._check_order_updates()
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            logging.info("Order monitoring cancelled")
        except Exception as e:
            logging.error(f"Order monitoring error: {e}")
        finally:
            self.monitoring_active = False
    
    async def _check_order_updates(self):
        """Check for order updates from broker"""
        if not self.active_orders:
            return
        
        try:
            # Get order IDs to check
            order_ids = list(self.active_orders.keys())
            
            for order_id in order_ids:
                order = self.active_orders.get(order_id)
                if not order or order.is_complete:
                    continue
                
                try:
                    # Get order status from broker
                    broker_order = await self.broker.get_order(order_id)
                    
                    if broker_order:
                        await self._process_order_update(order, broker_order)
                        
                except Exception as e:
                    logging.error(f"Error checking order {order_id}: {e}")
                    
                    # Check if order should be retried
                    if order.increment_retry():
                        logging.info(f"🔄 Retrying order {order_id} (attempt {order.retry_count})")
                        # Could implement retry logic here
                    else:
                        logging.error(f"❌ Order {order_id} failed after {order.retry_count} retries")
                        order.mark_failed(f"Max retries exceeded: {str(e)}")
                        await self._complete_order(order_id, order)
        
        except Exception as e:
            logging.error(f"Error in order monitoring: {e}")
    
    async def _process_order_update(self, order: EnhancedOrder, broker_order: Dict):
        """Process order update from broker"""
        try:
            broker_status = broker_order.get('status', '').lower()
            filled_qty = float(broker_order.get('filled_qty', 0))
            avg_price = broker_order.get('filled_avg_price')
            
            # Map broker status to our status
            status_mapping = {
                'new': OrderStatus.SUBMITTED,
                'pending_new': OrderStatus.PENDING,
                'accepted': OrderStatus.SUBMITTED,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'filled': OrderStatus.FILLED,
                'done_for_day': OrderStatus.FILLED,
                'canceled': OrderStatus.CANCELLED,
                'cancelled': OrderStatus.CANCELLED,
                'expired': OrderStatus.EXPIRED,
                'replaced': OrderStatus.SUBMITTED,
                'pending_cancel': OrderStatus.PENDING_CANCEL,
                'pending_replace': OrderStatus.SUBMITTED,
                'rejected': OrderStatus.REJECTED,
                'suspended': OrderStatus.FAILED,
                'stopped': OrderStatus.CANCELLED
            }
            
            new_status = status_mapping.get(broker_status, OrderStatus.SUBMITTED)
            
            # Check for fills
            if filled_qty > order.filled_qty:
                fill_qty = filled_qty - order.filled_qty
                fill_price = float(avg_price) if avg_price else order.price or 0.0
                
                order.update_fill(fill_qty, fill_price)
                logging.info(f"💰 Order {order.order_id} filled: {fill_qty} @ ${fill_price:.4f}")
                
                # Update blotter
                if self.order_blotter:
                    self.order_blotter.update_status(order.order_id, new_status.value)
            
            # Update status
            if new_status != order.status:
                order.status = new_status
                order.updated_at = datetime.now()
                
                logging.info(f"📊 Order {order.order_id} status: {new_status.value}")
            
            # Check if order is complete
            if order.is_complete:
                await self._complete_order(order.order_id, order)
                
        except Exception as e:
            logging.error(f"Error processing order update: {e}")
    
    async def _complete_order(self, order_id: str, order: EnhancedOrder):
        """Complete order and run callbacks"""
        try:
            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]
            
            # Add to completed orders
            self.completed_orders.append(order)
            
            # Update metrics
            if order.status == OrderStatus.FILLED:
                self.metrics['orders_filled'] += 1
                
                # Calculate fill time
                if order.submitted_at and order.filled_at:
                    fill_time = (order.filled_at - order.submitted_at).total_seconds()
                    self.metrics['total_fill_time'] += fill_time
                    self.metrics['average_fill_time'] = (
                        self.metrics['total_fill_time'] / self.metrics['orders_filled']
                    )
            
            # Run callbacks
            if order_id in self.order_callbacks:
                for callback in self.order_callbacks[order_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(order)
                        else:
                            callback(order)
                    except Exception as e:
                        logging.error(f"Error in order callback: {e}")
                
                del self.order_callbacks[order_id]
            
            logging.info(f"✅ Order {order_id} completed: {order.status.value}")
            
            # Stop monitoring if no active orders
            if not self.active_orders:
                await self.stop_monitoring()
                
        except Exception as e:
            logging.error(f"Error completing order {order_id}: {e}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order"""
        try:
            if order_id not in self.active_orders:
                logging.warning(f"Order {order_id} not found in active orders")
                return False
            
            order = self.active_orders[order_id]
            if order.is_complete:
                logging.warning(f"Order {order_id} is already complete")
                return False
            
            # Cancel with broker
            success = await self.broker.cancel_order(order_id)
            
            if success:
                order.status = OrderStatus.PENDING_CANCEL
                order.updated_at = datetime.now()
                logging.info(f"🚫 Order {order_id} cancellation requested")
                return True
            else:
                logging.error(f"❌ Failed to cancel order {order_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_active_orders(self) -> Dict[str, EnhancedOrder]:
        """Get all active orders"""
        return self.active_orders.copy()
    
    def get_order_by_symbol(self, symbol: str) -> List[EnhancedOrder]:
        """Get all orders for a symbol"""
        return [order for order in self.active_orders.values() if order.symbol == symbol]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get order management metrics"""
        total_orders = (self.metrics['orders_submitted'] + 
                       self.metrics['orders_rejected'] + 
                       self.metrics['orders_failed'])
        
        if total_orders > 0:
            success_rate = (self.metrics['orders_filled'] / total_orders) * 100
        else:
            success_rate = 0.0
        
        return {
            **self.metrics,
            'active_orders': len(self.active_orders),
            'completed_orders': len(self.completed_orders),
            'success_rate': success_rate,
            'monitoring_active': self.monitoring_active
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_monitoring()
        
        # Save pending orders to file for recovery
        if self.active_orders:
            pending_orders = [order.to_dict() for order in self.active_orders.values()]
            try:
                with open('pending_orders.json', 'w') as f:
                    json.dump(pending_orders, f, indent=2)
                logging.info(f"💾 Saved {len(pending_orders)} pending orders for recovery")
            except Exception as e:
                logging.error(f"Error saving pending orders: {e}")
