"""
Performance Monitoring and Visualization System
Handles real-time performance tracking and chart generation
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import threading
import time

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from models import BotInstance, Trade, PerformanceLog, BotStatus, get_db

class PerformanceMonitor:
    """Real-time performance monitoring and analytics"""
    
    def __init__(self, update_interval: int = 60):
        self.update_interval = update_interval
        self.monitoring_active = False
        self.monitor_thread = None
        self.performance_cache = {}
        self.metrics_cache = {}
        
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self):
        """Start the performance monitoring thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("📊 Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop the performance monitoring thread"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._update_all_bot_performance()
                self._calculate_portfolio_metrics()
                self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(self.update_interval)
    
    def _update_all_bot_performance(self):
        """Update performance metrics for all active bots"""
        with Session(bind=next(get_db()).bind) as db:
            active_bots = db.query(BotInstance)\
                           .filter(BotInstance.status.in_([BotStatus.RUNNING, BotStatus.BACKTESTING]))\
                           .all()
            
            for bot in active_bots:
                try:
                    self._update_bot_performance(bot, db)
                except Exception as e:
                    self.logger.error(f"Error updating performance for bot {bot.name}: {e}")
    
    def _update_bot_performance(self, bot: BotInstance, db: Session):
        """Update performance metrics for a specific bot"""
        # Get recent trades
        trades = db.query(Trade)\
                   .filter(Trade.bot_id == bot.id)\
                   .order_by(Trade.entry_time.desc())\
                   .all()
        
        # Calculate current metrics
        metrics = self._calculate_bot_metrics(bot, trades)
        
        # Update bot instance
        bot.current_equity = metrics['current_equity']
        bot.total_return = metrics['total_return']
        bot.total_trades = metrics['total_trades']
        bot.win_rate = metrics['win_rate']
        bot.sharpe_ratio = metrics['sharpe_ratio']
        bot.max_drawdown = metrics['max_drawdown']
        bot.updated_at = datetime.now(timezone.utc)
        
        # Create performance log entry
        perf_log = PerformanceLog(
            bot_id=bot.id,
            timestamp=datetime.now(timezone.utc),
            equity=metrics['current_equity'],
            cash=metrics['cash'],
            positions_value=metrics['positions_value'],
            total_return=metrics['total_return'],
            daily_return=metrics['daily_return'],
            portfolio_risk=metrics['portfolio_risk'],
            var_95=metrics.get('var_95'),
            max_drawdown=metrics['max_drawdown'],
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            win_rate=metrics['win_rate'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics.get('sortino_ratio'),
            calmar_ratio=metrics.get('calmar_ratio'),
            open_positions=metrics['open_positions'],
            avg_trade_duration=metrics.get('avg_trade_duration'),
            total_fees=metrics['total_fees']
        )
        
        db.add(perf_log)
        db.commit()
        
        # Cache metrics for quick access
        self.performance_cache[bot.id] = metrics
    
    def _calculate_bot_metrics(self, bot: BotInstance, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics for a bot"""
        initial_capital = bot.initial_capital
        
        # Basic trade statistics
        closed_trades = [t for t in trades if t.status == 'closed' and t.pnl is not None]
        open_trades = [t for t in trades if t.status == 'open']
        
        total_pnl = sum(t.pnl for t in closed_trades)
        total_fees = sum(t.fees or 0 for t in trades)
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]
        
        # Portfolio values
        current_equity = initial_capital + total_pnl - total_fees
        positions_value = sum(t.quantity * t.entry_price for t in open_trades)
        cash = current_equity - positions_value
        
        # Returns
        total_return = (current_equity - initial_capital) / initial_capital if initial_capital > 0 else 0
        
        # Daily return (simplified - would need actual daily data)
        daily_return = 0.001 if total_return > 0 else -0.001  # Placeholder
        
        # Risk metrics
        portfolio_risk = bot.max_portfolio_risk
        
        # Trade statistics
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Performance ratios
        returns = [t.pnl_pct for t in closed_trades if t.pnl_pct is not None]
        
        if len(returns) > 1:
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(closed_trades, initial_capital)
        else:
            sharpe_ratio = 0.0
            sortino_ratio = None
            max_drawdown = 0.0
        
        # Average trade duration
        completed_trades_with_duration = [
            t for t in closed_trades 
            if t.exit_time and t.entry_time
        ]
        
        if completed_trades_with_duration:
            durations = [
                (t.exit_time - t.entry_time).total_seconds() / 3600  # in hours
                for t in completed_trades_with_duration
            ]
            avg_trade_duration = np.mean(durations)
        else:
            avg_trade_duration = None
        
        return {
            'current_equity': current_equity,
            'cash': cash,
            'positions_value': positions_value,
            'total_return': total_return,
            'daily_return': daily_return,
            'portfolio_risk': portfolio_risk,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'open_positions': len(open_trades),
            'avg_trade_duration': avg_trade_duration,
            'total_fees': total_fees,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        }
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)  # Annualized
    
    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sortino ratio (Sharpe ratio using downside deviation)"""
        if not returns or len(returns) < 2:
            return None
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)
        
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return None
        
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return None
        
        return np.mean(excess_returns) / downside_deviation * np.sqrt(252)
    
    def _calculate_max_drawdown(self, trades: List[Trade], initial_capital: float) -> float:
        """Calculate maximum drawdown"""
        if not trades:
            return 0.0
        
        # Sort trades by exit time
        sorted_trades = sorted([t for t in trades if t.exit_time], key=lambda x: x.exit_time)
        
        if not sorted_trades:
            return 0.0
        
        # Calculate cumulative returns
        cumulative_pnl = 0
        peak = initial_capital
        max_drawdown = 0.0
        
        for trade in sorted_trades:
            cumulative_pnl += trade.pnl or 0
            current_equity = initial_capital + cumulative_pnl
            
            if current_equity > peak:
                peak = current_equity
            
            drawdown = (peak - current_equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_portfolio_metrics(self):
        """Calculate portfolio-level metrics across all bots"""
        with Session(bind=next(get_db()).bind) as db:
            bots = db.query(BotInstance).all()
            
            total_initial = sum(bot.initial_capital for bot in bots)
            total_equity = sum(bot.current_equity for bot in bots)
            total_trades = sum(bot.total_trades for bot in bots)
            
            if total_initial > 0:
                overall_return = (total_equity - total_initial) / total_initial
            else:
                overall_return = 0.0
            
            running_bots = len([bot for bot in bots if bot.status == BotStatus.RUNNING])
            
            portfolio_metrics = {
                'total_bots': len(bots),
                'running_bots': running_bots,
                'total_initial_capital': total_initial,
                'total_equity': total_equity,
                'overall_return': overall_return,
                'total_trades': total_trades,
                'timestamp': datetime.now(timezone.utc)
            }
            
            self.metrics_cache['portfolio'] = portfolio_metrics
    
    def _cleanup_old_data(self):
        """Clean up old performance logs to prevent database bloat"""
        with Session(bind=next(get_db()).bind) as db:
            # Keep last 30 days of detailed logs
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Delete old performance logs
            deleted = db.query(PerformanceLog)\
                       .filter(PerformanceLog.timestamp < cutoff_date)\
                       .delete()
            
            if deleted > 0:
                db.commit()
                self.logger.info(f"🧹 Cleaned up {deleted} old performance log entries")
    
    def get_bot_performance_chart_data(self, bot_id: int, hours: int = 24) -> Dict[str, Any]:
        """Get performance data formatted for chart visualization"""
        with Session(bind=next(get_db()).bind) as db:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            performance_logs = db.query(PerformanceLog)\
                                .filter(PerformanceLog.bot_id == bot_id)\
                                .filter(PerformanceLog.timestamp >= cutoff_time)\
                                .order_by(PerformanceLog.timestamp.asc())\
                                .all()
            
            if not performance_logs:
                return {"labels": [], "datasets": []}
            
            timestamps = [log.timestamp.strftime('%H:%M') for log in performance_logs]
            equity_data = [log.equity for log in performance_logs]
            return_data = [log.total_return * 100 for log in performance_logs]
            drawdown_data = [log.max_drawdown * 100 for log in performance_logs]
            
            return {
                "labels": timestamps,
                "datasets": [
                    {
                        "label": "Equity ($)",
                        "data": equity_data,
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "yAxisID": "y"
                    },
                    {
                        "label": "Return (%)",
                        "data": return_data,
                        "borderColor": "rgb(54, 162, 235)",
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "yAxisID": "y1"
                    },
                    {
                        "label": "Drawdown (%)",
                        "data": drawdown_data,
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "yAxisID": "y1"
                    }
                ],
                "options": {
                    "responsive": True,
                    "scales": {
                        "y": {
                            "type": "linear",
                            "display": True,
                            "position": "left"
                        },
                        "y1": {
                            "type": "linear",
                            "display": True,
                            "position": "right",
                            "grid": {
                                "drawOnChartArea": False
                            }
                        }
                    }
                }
            }
    
    def get_portfolio_overview(self) -> Dict[str, Any]:
        """Get portfolio-level overview with key metrics"""
        if 'portfolio' in self.metrics_cache:
            base_metrics = self.metrics_cache['portfolio'].copy()
        else:
            base_metrics = {
                'total_bots': 0,
                'running_bots': 0,
                'total_initial_capital': 0,
                'total_equity': 0,
                'overall_return': 0,
                'total_trades': 0,
                'timestamp': datetime.now(timezone.utc)
            }
        
        # Add performance breakdown by status
        with Session(bind=next(get_db()).bind) as db:
            bots_by_status = {}
            for status in BotStatus:
                count = db.query(BotInstance)\
                         .filter(BotInstance.status == status)\
                         .count()
                bots_by_status[status.value] = count
            
            # Top performing bots
            top_performers = db.query(BotInstance)\
                              .order_by(BotInstance.total_return.desc())\
                              .limit(5)\
                              .all()
            
            base_metrics.update({
                'bots_by_status': bots_by_status,
                'top_performers': [
                    {
                        'id': bot.id,
                        'name': bot.name,
                        'total_return': bot.total_return,
                        'current_equity': bot.current_equity,
                        'total_trades': bot.total_trades,
                        'win_rate': bot.win_rate
                    } for bot in top_performers
                ]
            })
        
        return base_metrics
    
    def get_cached_metrics(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get cached performance metrics for a bot"""
        return self.performance_cache.get(bot_id)
    
    def force_update_bot(self, bot_id: int) -> Dict[str, Any]:
        """Force update metrics for a specific bot"""
        with Session(bind=next(get_db()).bind) as db:
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")
            
            self._update_bot_performance(bot, db)
            return self.performance_cache.get(bot_id, {})