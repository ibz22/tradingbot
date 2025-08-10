import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a position in a token"""
    token_mint: str
    symbol: str
    quantity: float
    average_price: float  # Average cost basis
    last_update: float = field(default_factory=time.time)
    realized_pnl: float = 0.0  # Realized P&L from closed portions
    
    def update_buy(self, quantity: float, price: float):
        """Update position with a buy transaction"""
        if self.quantity == 0:
            self.average_price = price
        else:
            total_value = (self.quantity * self.average_price) + (quantity * price)
            total_quantity = self.quantity + quantity
            self.average_price = total_value / total_quantity if total_quantity > 0 else 0
        
        self.quantity += quantity
        self.last_update = time.time()
    
    def update_sell(self, quantity: float, price: float) -> float:
        """Update position with a sell transaction, returns realized P&L"""
        if quantity > self.quantity:
            raise ValueError(f"Cannot sell {quantity}, only have {self.quantity}")
        
        # Calculate realized P&L for sold portion
        realized_pnl = (price - self.average_price) * quantity
        self.realized_pnl += realized_pnl
        
        self.quantity -= quantity
        self.last_update = time.time()
        
        return realized_pnl
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.quantity == 0:
            return 0.0
        return (current_price - self.average_price) * self.quantity
    
    def get_total_pnl(self, current_price: float) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.realized_pnl + self.get_unrealized_pnl(current_price)
    
    def get_market_value(self, current_price: float) -> float:
        """Get current market value of position"""
        return self.quantity * current_price

class VirtualPortfolio:
    """Enhanced virtual portfolio for paper trading"""
    
    def __init__(self, initial_sol_balance: float = 10.0):
        self.initial_balance = initial_sol_balance
        self.sol_balance = initial_sol_balance
        self.positions: Dict[str, Position] = {}
        self.transaction_history: deque = deque(maxlen=10000)
        self.start_time = time.time()
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.largest_win = 0.0
        self.largest_loss = 0.0
        self.total_fees_paid = 0.0
        
        # Legacy holdings for backward compatibility
        self.holdings = {}
    
    def get_sol_balance(self) -> float:
        """Get current SOL balance"""
        return self.sol_balance
    
    def set(self, symbol: str, qty: float):
        """Legacy method for compatibility"""
        self.holdings[symbol] = qty
        if symbol == "SOL":
            self.sol_balance = qty
        else:
            # This is a simplified set - in practice should use buy/sell methods
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    token_mint=symbol,
                    symbol=symbol,
                    quantity=qty,
                    average_price=0.0
                )
            else:
                self.positions[symbol].quantity = qty

    def get(self, symbol: str) -> float:
        """Legacy method for compatibility"""
        if symbol in self.holdings:
            return self.holdings[symbol]
        if symbol == "SOL":
            return self.sol_balance
        return self.positions.get(symbol, Position(symbol, symbol, 0.0, 0.0)).quantity
    
    def buy_token(self, token_mint: str, symbol: str, sol_amount: float, 
                  price: float, fee_percent: float = 0.0) -> bool:
        """Buy tokens with SOL"""
        total_cost = sol_amount * (1 + fee_percent / 100)
        
        if total_cost > self.sol_balance:
            logger.warning(f"Insufficient SOL balance for purchase: need {total_cost}, have {self.sol_balance}")
            return False
        
        # Calculate tokens received
        tokens_received = sol_amount / price
        
        # Update SOL balance
        self.sol_balance -= total_cost
        self.total_fees_paid += (sol_amount * fee_percent / 100)
        
        # Update position
        if token_mint not in self.positions:
            self.positions[token_mint] = Position(
                token_mint=token_mint,
                symbol=symbol,
                quantity=0.0,
                average_price=0.0
            )
        
        self.positions[token_mint].update_buy(tokens_received, price)
        
        # Record transaction
        self._record_transaction({
            'type': 'buy',
            'token_mint': token_mint,
            'symbol': symbol,
            'quantity': tokens_received,
            'price': price,
            'sol_amount': sol_amount,
            'fee': sol_amount * fee_percent / 100,
            'timestamp': time.time()
        })
        
        return True
    
    def sell_token(self, token_mint: str, quantity: float, price: float, 
                   fee_percent: float = 0.0) -> bool:
        """Sell tokens for SOL"""
        if token_mint not in self.positions:
            logger.warning(f"No position in {token_mint} to sell")
            return False
        
        position = self.positions[token_mint]
        if quantity > position.quantity:
            logger.warning(f"Cannot sell {quantity} {position.symbol}, only have {position.quantity}")
            return False
        
        # Calculate SOL received
        gross_sol = quantity * price
        fee_amount = gross_sol * fee_percent / 100
        net_sol = gross_sol - fee_amount
        
        # Update position and get realized P&L
        realized_pnl = position.update_sell(quantity, price)
        
        # Update SOL balance
        self.sol_balance += net_sol
        self.total_fees_paid += fee_amount
        
        # Update trade statistics
        self.total_trades += 1
        if realized_pnl > 0:
            self.winning_trades += 1
            self.largest_win = max(self.largest_win, realized_pnl)
        else:
            self.losing_trades += 1
            self.largest_loss = min(self.largest_loss, realized_pnl)
        
        # Record transaction
        self._record_transaction({
            'type': 'sell',
            'token_mint': token_mint,
            'symbol': position.symbol,
            'quantity': quantity,
            'price': price,
            'sol_amount': gross_sol,
            'fee': fee_amount,
            'realized_pnl': realized_pnl,
            'timestamp': time.time()
        })
        
        # Remove position if quantity is zero
        if position.quantity == 0:
            del self.positions[token_mint]
        
        return True
    
    def _record_transaction(self, transaction: Dict[str, Any]):
        """Record a transaction for history"""
        self.transaction_history.append(transaction)
    
    def get_position(self, token_mint: str) -> Optional[Position]:
        """Get position for a specific token"""
        return self.positions.get(token_mint)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions"""
        return self.positions.copy()
    
    def get_portfolio_value(self, price_feed) -> float:
        """Calculate total portfolio value in SOL"""
        total_value = self.sol_balance
        
        for position in self.positions.values():
            if price_feed:
                price_data = price_feed.get_current_price(position.token_mint)
                current_price = price_data.price if price_data else position.average_price
            else:
                current_price = position.average_price
            
            total_value += position.get_market_value(current_price)
        
        return total_value
    
    def get_total_pnl(self, price_feed) -> float:
        """Calculate total P&L in SOL"""
        current_value = self.get_portfolio_value(price_feed)
        return current_value - self.initial_balance
    
    def get_total_pnl_percent(self, price_feed) -> float:
        """Calculate total P&L percentage"""
        if self.initial_balance == 0:
            return 0.0
        return (self.get_total_pnl(price_feed) / self.initial_balance) * 100
    
    def get_transaction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transaction history"""
        history = list(self.transaction_history)
        if limit:
            return history[-limit:]
        return history
    
    def get_performance_stats(self, price_feed) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        current_value = self.get_portfolio_value(price_feed)
        total_pnl = self.get_total_pnl(price_feed)
        total_pnl_percent = self.get_total_pnl_percent(price_feed)
        
        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        total_realized_pnl = sum(p.realized_pnl for p in self.positions.values())
        
        for position in self.positions.values():
            if price_feed:
                price_data = price_feed.get_current_price(position.token_mint)
                current_price = price_data.price if price_data else position.average_price
            else:
                current_price = position.average_price
            unrealized_pnl += position.get_unrealized_pnl(current_price)
        
        # Calculate win rate
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        # Calculate time-based metrics
        days_active = (time.time() - self.start_time) / 86400
        
        return {
            'initial_balance': self.initial_balance,
            'current_sol_balance': self.sol_balance,
            'current_portfolio_value': current_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'realized_pnl': total_realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate_percent': win_rate,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'total_fees_paid': self.total_fees_paid,
            'days_active': days_active,
            'positions_count': len(self.positions),
            'avg_pnl_per_trade': total_pnl / self.total_trades if self.total_trades > 0 else 0
        }
