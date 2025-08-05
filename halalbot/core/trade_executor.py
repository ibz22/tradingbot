_execution_metrics(self) -> Dict[str, Any]:
        """Get execution performance metrics"""
        
        order_metrics = self.order_manager.get_metrics()
        
        return {
            **self.metrics,
            'order_manager': order_metrics,
            'position_cache_size': len(self.position_cache),
            'last_position_sync': self.last_position_sync.isoformat(),
            'execution_history_size': len(self.execution_history),
            'market_conditions': self.market_conditions
        }
    
    def get_position_summary(self) -> Dict[str, float]:
        """Get current position summary"""
        return self.position_cache.copy()
    
    async def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        
        recent = self.execution_history[-limit:] if self.execution_history else []
        
        return [
            {
                'success': exec.success,
                'order_id': exec.order_id,
                'filled_quantity': exec.filled_quantity,
                'avg_fill_price': exec.avg_fill_price,
                'execution_time': exec.execution_time,
                'slippage': exec.slippage,
                'fees': exec.fees,
                'partial_fill': exec.partial_fill,
                'error_message': exec.error_message
            }
            for exec in reversed(recent)
        ]
    
    async def update_market_conditions(self):
        """Update market condition tracking"""
        
        try:
            # Check market hours
            market_open = await self.broker.is_market_open()
            
            if market_open:
                self.market_conditions['market_hours'] = 'regular'
            else:
                # Could add logic to detect pre/post market hours
                self.market_conditions['market_hours'] = 'closed'
            
            # Could add volatility detection based on recent price movements
            # self.market_conditions['volatility_regime'] = self._detect_volatility()
            
            # Could add liquidity assessment based on bid-ask spreads
            # self.market_conditions['liquidity_conditions'] = self._assess_liquidity()
            
        except Exception as e:
            logging.error(f"Error updating market conditions: {e}")
    
    async def cleanup(self):
        """Cleanup resources and save state"""
        
        try:
            # Cancel any remaining orders
            await self.cancel_all_orders()
            
            # Cleanup order manager
            await self.order_manager.cleanup()
            
            # Save execution history
            if self.execution_history:
                import json
                from pathlib import Path
                
                history_data = []
                for exec in self.execution_history[-100:]:  # Save last 100
                    history_data.append({
                        'timestamp': datetime.now().isoformat(),
                        'success': exec.success,
                        'order_id': exec.order_id,
                        'filled_quantity': exec.filled_quantity,
                        'avg_fill_price': exec.avg_fill_price,
                        'execution_time': exec.execution_time,
                        'slippage': exec.slippage,
                        'fees': exec.fees,
                        'error_message': exec.error_message
                    })
                
                try:
                    Path('logs').mkdir(exist_ok=True)
                    with open('logs/execution_history.json', 'w') as f:
                        json.dump(history_data, f, indent=2)
                    logging.info("💾 Execution history saved")
                except Exception as e:
                    logging.error(f"Error saving execution history: {e}")
            
            # Final position reconciliation
            await self.reconcile_positions()
            
            logging.info("✅ TradeExecutor cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during TradeExecutor cleanup: {e}")
