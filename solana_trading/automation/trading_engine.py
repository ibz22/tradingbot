import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger(__name__)

class EngineState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class ExecutionResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RISK_REJECTED = "risk_rejected"

@dataclass
class TradeExecution:
    """Record of a trade execution"""
    execution_id: str
    signal_id: str
    token_mint: str
    side: str
    size_sol: float
    expected_price: float
    actual_price: Optional[float] = None
    quantity_received: Optional[float] = None
    fee_paid: float = 0.0
    result: ExecutionResult = ExecutionResult.FAILED
    error_message: Optional[str] = None
    execution_time: float = field(default_factory=time.time)
    completion_time: Optional[float] = None
    transaction_signature: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.completion_time:
            return self.completion_time - self.execution_time
        return time.time() - self.execution_time

@dataclass
class EngineConfig:
    """Configuration for trading engine"""
    # Execution settings
    max_concurrent_trades: int = 3
    trade_timeout_seconds: int = 60
    retry_failed_trades: bool = True
    max_retries: int = 2
    retry_delay_seconds: int = 5
    
    # Monitoring intervals
    market_data_update_interval: int = 30  # seconds
    portfolio_update_interval: int = 60    # seconds
    risk_check_interval: int = 30          # seconds
    strategy_update_interval: int = 60     # seconds
    
    # Safety settings
    enable_paper_trading: bool = True
    require_manual_approval: bool = False
    emergency_stop_on_error: bool = True
    max_errors_per_hour: int = 10
    
    # Performance settings
    log_all_signals: bool = True
    log_execution_details: bool = True
    performance_report_interval: int = 3600  # seconds

class TradingEngine:
    """Main automated trading engine"""
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.state = EngineState.STOPPED
        
        # Dependencies (injected)
        self.price_feed = None
        self.portfolio_manager = None
        self.risk_manager = None
        self.strategies: List[Any] = []
        self.jupiter_client = None
        self.transaction_builder = None
        
        # Execution state
        self.running_tasks: List[asyncio.Task] = []
        self.active_executions: Dict[str, TradeExecution] = {}
        self.execution_history: List[TradeExecution] = []
        
        # Monitoring state
        self.last_market_update = 0.0
        self.last_portfolio_update = 0.0
        self.last_risk_check = 0.0
        self.last_strategy_update = 0.0
        self.last_performance_report = 0.0
        
        # Error tracking
        self.error_count_hour = 0
        self.last_error_reset = time.time()
        self.critical_errors: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.engine_start_time = 0.0
        self.total_signals_processed = 0
        self.total_trades_executed = 0
        self.total_volume_traded = 0.0
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}
    
    def add_strategy(self, strategy):
        """Add a trading strategy"""
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.get_name()}")
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a trading strategy by name"""
        for i, strategy in enumerate(self.strategies):
            if strategy.get_name() == strategy_name:
                del self.strategies[i]
                logger.info(f"Removed strategy: {strategy_name}")
                return True
        return False
    
    def set_dependencies(self, **kwargs):
        """Inject dependencies"""
        for name, dependency in kwargs.items():
            setattr(self, name, dependency)
            logger.info(f"Injected dependency: {name}")
    
    def subscribe_to_events(self, event_type: str, callback: Callable):
        """Subscribe to engine events"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    async def _emit_event(self, event_type: str, data: Any):
        """Emit an event to subscribers"""
        callbacks = self.event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")
    
    async def start(self):
        """Start the trading engine"""
        if self.state == EngineState.RUNNING:
            logger.warning("Engine is already running")
            return
        
        logger.info("Starting trading engine...")
        self.state = EngineState.STARTING
        
        try:
            # Validate dependencies
            self._validate_dependencies()
            
            # Start market data feed
            if self.price_feed:
                await self.price_feed.start()
            
            # Initialize components
            await self._initialize_components()
            
            # Start main loops
            self.running_tasks = [
                asyncio.create_task(self._main_trading_loop()),
                asyncio.create_task(self._monitoring_loop()),
                asyncio.create_task(self._housekeeping_loop())
            ]
            
            self.state = EngineState.RUNNING
            self.engine_start_time = time.time()
            
            logger.info("Trading engine started successfully")
            await self._emit_event("engine_started", {"timestamp": time.time()})
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            self.state = EngineState.ERROR
            await self._emit_event("engine_error", {"error": str(e), "timestamp": time.time()})
            raise
    
    async def stop(self):
        """Stop the trading engine"""
        if self.state == EngineState.STOPPED:
            logger.warning("Engine is already stopped")
            return
        
        logger.info("Stopping trading engine...")
        self.state = EngineState.STOPPING
        
        try:
            # Cancel all running tasks
            for task in self.running_tasks:
                task.cancel()
            
            # Wait for tasks to complete with timeout
            if self.running_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self.running_tasks, return_exceptions=True),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Some tasks did not complete within timeout")
            
            # Wait for active executions to complete
            await self._wait_for_active_executions()
            
            # Stop market data feed
            if self.price_feed:
                await self.price_feed.stop()
            
            self.state = EngineState.STOPPED
            logger.info("Trading engine stopped")
            await self._emit_event("engine_stopped", {"timestamp": time.time()})
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
            self.state = EngineState.ERROR
            await self._emit_event("engine_error", {"error": str(e), "timestamp": time.time()})
    
    def _validate_dependencies(self):
        """Validate required dependencies"""
        required = ["price_feed", "portfolio_manager", "risk_manager"]
        missing = [dep for dep in required if getattr(self, dep) is None]
        
        if missing:
            raise ValueError(f"Missing required dependencies: {missing}")
        
        if not self.strategies:
            logger.warning("No trading strategies configured")
    
    async def _initialize_components(self):
        """Initialize all components"""
        # Set up dependencies between components
        for strategy in self.strategies:
            strategy.set_dependencies(
                price_feed=self.price_feed,
                technical_analyzer=getattr(self, 'technical_analyzer', None),
                portfolio_manager=self.portfolio_manager,
                risk_manager=self.risk_manager
            )
        
        if self.portfolio_manager:
            self.portfolio_manager.set_dependencies(
                price_feed=self.price_feed,
                risk_manager=self.risk_manager
            )
        
        if self.risk_manager:
            self.risk_manager.set_dependencies(
                portfolio=self.portfolio_manager.portfolio if self.portfolio_manager else None,
                price_feed=self.price_feed,
                technical_analyzer=getattr(self, 'technical_analyzer', None)
            )
    
    async def _main_trading_loop(self):
        """Main trading loop"""
        logger.info("Starting main trading loop")
        
        try:
            while self.state == EngineState.RUNNING:
                try:
                    # Check if we should generate signals
                    if await self._should_update_strategies():
                        await self._process_trading_cycle()
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    await self._handle_error("main_trading_loop", e)
                    await asyncio.sleep(5.0)  # Back off on error
                    
        except asyncio.CancelledError:
            logger.info("Main trading loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in main trading loop: {e}")
            await self._handle_critical_error("main_trading_loop", e)
    
    async def _process_trading_cycle(self):
        """Process one complete trading cycle"""
        cycle_start = time.time()
        
        try:
            # Get supported tokens
            tokens = list(self.price_feed.get_supported_tokens().keys()) if self.price_feed else []
            if not tokens:
                return
            
            # Process each strategy
            all_signals = []
            for strategy in self.strategies:
                if not strategy.is_enabled():
                    continue
                
                try:
                    strategy_signals = await strategy.generate_signals(tokens)
                    if strategy_signals:
                        all_signals.extend(strategy_signals)
                        logger.info(f"Strategy {strategy.get_name()} generated {len(strategy_signals)} signals")
                        
                except Exception as e:
                    logger.error(f"Error in strategy {strategy.get_name()}: {e}")
            
            # Process signals
            if all_signals:
                await self._process_signals(all_signals)
            
            self.last_strategy_update = time.time()
            cycle_duration = time.time() - cycle_start
            
            if cycle_duration > 5.0:  # Warn if cycle takes too long
                logger.warning(f"Trading cycle took {cycle_duration:.1f} seconds")
                
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def _process_signals(self, signals: List[Any]):
        """Process trading signals"""
        self.total_signals_processed += len(signals)
        
        # Sort signals by confidence (highest first)
        signals.sort(key=lambda s: s.confidence, reverse=True)
        
        for signal in signals:
            try:
                # Check if we have capacity for more executions
                if len(self.active_executions) >= self.config.max_concurrent_trades:
                    logger.info("Max concurrent trades reached, skipping remaining signals")
                    break
                
                # Validate signal with risk manager
                risk_approved, risk_alerts = await self.risk_manager.validate_trade(
                    token_mint=signal.token_mint,
                    side=signal.side.value,
                    size_sol=signal.size_sol,
                    current_price=await self._get_current_price(signal.token_mint)
                )
                
                if not risk_approved:
                    logger.info(f"Signal rejected by risk manager: {signal.reason}")
                    if self.config.log_all_signals:
                        await self._log_signal_rejection(signal, "risk_rejected", risk_alerts)
                    continue
                
                # Execute signal
                if self.config.require_manual_approval:
                    await self._request_manual_approval(signal)
                else:
                    await self._execute_signal(signal)
                    
            except Exception as e:
                logger.error(f"Error processing signal {signal.token_mint}: {e}")
    
    async def _execute_signal(self, signal) -> TradeExecution:
        """Execute a trading signal"""
        execution_id = f"exec_{int(time.time())}_{signal.token_mint[:8]}"
        
        # Get current price
        current_price = await self._get_current_price(signal.token_mint)
        if not current_price:
            raise ValueError(f"No current price available for {signal.token_mint}")
        
        # Create execution record
        execution = TradeExecution(
            execution_id=execution_id,
            signal_id=f"{signal.strategy}_{signal.token_mint}_{int(signal.timestamp)}",
            token_mint=signal.token_mint,
            side=signal.side.value,
            size_sol=signal.size_sol,
            expected_price=current_price
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            logger.info(f"Executing {signal.side.value} signal for {signal.token_mint}: {signal.size_sol} SOL")
            
            if self.config.enable_paper_trading:
                # Paper trading execution
                success = await self._execute_paper_trade(execution, signal)
            else:
                # Real trading execution
                success = await self._execute_real_trade(execution, signal)
            
            if success:
                execution.result = ExecutionResult.SUCCESS
                self.total_trades_executed += 1
                self.total_volume_traded += signal.size_sol
                
                # Record trade in strategy
                strategy = next((s for s in self.strategies if s.get_name() == signal.strategy), None)
                if strategy:
                    strategy.record_trade(signal.token_mint)
                
                logger.info(f"Trade executed successfully: {execution_id}")
                await self._emit_event("trade_executed", execution)
            
            execution.completion_time = time.time()
            
        except Exception as e:
            execution.result = ExecutionResult.FAILED
            execution.error_message = str(e)
            execution.completion_time = time.time()
            
            logger.error(f"Trade execution failed: {execution_id} - {e}")
            await self._emit_event("trade_failed", execution)
            
        finally:
            # Move to history and remove from active
            self.execution_history.append(execution)
            del self.active_executions[execution_id]
        
        return execution
    
    async def _execute_paper_trade(self, execution: TradeExecution, signal) -> bool:
        """Execute trade in paper trading mode"""
        try:
            portfolio = self.portfolio_manager.portfolio
            
            if signal.side.value == "buy":
                success = portfolio.buy_token(
                    token_mint=signal.token_mint,
                    symbol=signal.token_mint[:8],  # Use short version as symbol
                    sol_amount=signal.size_sol,
                    price=execution.expected_price,
                    fee_percent=0.1  # Simulate 0.1% fee
                )
                
                if success:
                    execution.quantity_received = signal.size_sol / execution.expected_price
                    execution.fee_paid = signal.size_sol * 0.001  # 0.1% fee
                
            else:  # sell
                # Get position to determine quantity to sell
                position = portfolio.get_position(signal.token_mint)
                if not position:
                    raise ValueError(f"No position to sell for {signal.token_mint}")
                
                quantity_to_sell = min(signal.size_sol / execution.expected_price, position.quantity)
                
                success = portfolio.sell_token(
                    token_mint=signal.token_mint,
                    quantity=quantity_to_sell,
                    price=execution.expected_price,
                    fee_percent=0.1
                )
                
                if success:
                    execution.quantity_received = quantity_to_sell
                    execution.fee_paid = (quantity_to_sell * execution.expected_price) * 0.001
            
            execution.actual_price = execution.expected_price
            return success
            
        except Exception as e:
            logger.error(f"Paper trade execution failed: {e}")
            return False
    
    async def _execute_real_trade(self, execution: TradeExecution, signal) -> bool:
        """Execute real trade (placeholder for real implementation)"""
        # This would implement real trading via Jupiter/DEX
        # For now, just simulate the trade
        await asyncio.sleep(0.1)  # Simulate network delay
        
        logger.warning("Real trading not implemented yet - would execute via Jupiter")
        
        # Simulate success
        execution.actual_price = execution.expected_price
        execution.quantity_received = signal.size_sol / execution.expected_price
        execution.fee_paid = signal.size_sol * 0.001
        execution.transaction_signature = f"sim_{execution.execution_id}"
        
        return True
    
    async def _get_current_price(self, token_mint: str) -> Optional[float]:
        """Get current price for a token"""
        if not self.price_feed:
            return None
        
        price_data = self.price_feed.get_current_price(token_mint)
        return price_data.price if price_data else None
    
    async def _monitoring_loop(self):
        """Monitoring and maintenance loop"""
        logger.info("Starting monitoring loop")
        
        try:
            while self.state == EngineState.RUNNING:
                current_time = time.time()
                
                try:
                    # Update portfolio metrics
                    if current_time - self.last_portfolio_update >= self.config.portfolio_update_interval:
                        if self.portfolio_manager:
                            self.portfolio_manager.record_daily_value()
                        self.last_portfolio_update = current_time
                    
                    # Check risk limits
                    if current_time - self.last_risk_check >= self.config.risk_check_interval:
                        await self._check_risk_limits()
                        self.last_risk_check = current_time
                    
                    # Check stop losses
                    if self.risk_manager:
                        triggered_stops = await self.risk_manager.check_stop_losses()
                        if triggered_stops:
                            await self._process_stop_losses(triggered_stops)
                    
                    # Performance reporting
                    if current_time - self.last_performance_report >= self.config.performance_report_interval:
                        await self._generate_performance_report()
                        self.last_performance_report = current_time
                    
                    await asyncio.sleep(5.0)  # Monitor every 5 seconds
                    
                except Exception as e:
                    await self._handle_error("monitoring_loop", e)
                    await asyncio.sleep(10.0)
                    
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            await self._handle_critical_error("monitoring_loop", e)
    
    async def _housekeeping_loop(self):
        """Housekeeping and cleanup loop"""
        logger.info("Starting housekeeping loop")
        
        try:
            while self.state == EngineState.RUNNING:
                try:
                    # Clean up old execution history (keep last 1000)
                    if len(self.execution_history) > 1000:
                        self.execution_history = self.execution_history[-1000:]
                    
                    # Reset hourly error count
                    if time.time() - self.last_error_reset >= 3600:
                        self.error_count_hour = 0
                        self.last_error_reset = time.time()
                    
                    # Clean up old critical errors (keep last 100)
                    if len(self.critical_errors) > 100:
                        self.critical_errors = self.critical_errors[-100:]
                    
                    await asyncio.sleep(300.0)  # Housekeeping every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in housekeeping loop: {e}")
                    await asyncio.sleep(60.0)
                    
        except asyncio.CancelledError:
            logger.info("Housekeeping loop cancelled")
            raise
    
    async def _should_update_strategies(self) -> bool:
        """Check if strategies should be updated"""
        return time.time() - self.last_strategy_update >= self.config.strategy_update_interval
    
    async def _check_risk_limits(self):
        """Check portfolio risk limits"""
        if self.portfolio_manager:
            risk_status = self.portfolio_manager.check_risk_limits()
            
            if not risk_status['within_limits']:
                logger.warning(f"Risk limits violated: {risk_status['violations']}")
                await self._emit_event("risk_violation", risk_status)
    
    async def _process_stop_losses(self, triggered_stops: List[Dict[str, Any]]):
        """Process triggered stop losses"""
        for stop in triggered_stops:
            logger.warning(f"Processing triggered stop loss: {stop['token_mint']}")
            
            # Create emergency sell signal
            # This would create and execute a sell order for the stopped position
            # Implementation depends on the specific requirements
    
    async def _generate_performance_report(self):
        """Generate and emit performance report"""
        uptime_hours = (time.time() - self.engine_start_time) / 3600
        
        report = {
            'timestamp': time.time(),
            'uptime_hours': uptime_hours,
            'total_signals_processed': self.total_signals_processed,
            'total_trades_executed': self.total_trades_executed,
            'total_volume_traded': self.total_volume_traded,
            'active_executions': len(self.active_executions),
            'error_count_hour': self.error_count_hour,
            'strategies_active': len([s for s in self.strategies if s.is_enabled()]),
            'execution_success_rate': self._calculate_success_rate()
        }
        
        logger.info(f"Performance: {report['total_trades_executed']} trades, "
                   f"{report['total_volume_traded']:.1f} SOL volume, "
                   f"{report['execution_success_rate']:.1f}% success rate")
        
        await self._emit_event("performance_report", report)
    
    def _calculate_success_rate(self) -> float:
        """Calculate execution success rate"""
        if not self.execution_history:
            return 0.0
        
        successful = len([e for e in self.execution_history if e.result == ExecutionResult.SUCCESS])
        return (successful / len(self.execution_history)) * 100
    
    async def _wait_for_active_executions(self):
        """Wait for active executions to complete"""
        timeout = 30.0
        start_time = time.time()
        
        while self.active_executions and (time.time() - start_time) < timeout:
            logger.info(f"Waiting for {len(self.active_executions)} active executions to complete...")
            await asyncio.sleep(1.0)
        
        if self.active_executions:
            logger.warning(f"Timeout waiting for executions: {list(self.active_executions.keys())}")
    
    async def _handle_error(self, source: str, error: Exception):
        """Handle non-critical errors"""
        self.error_count_hour += 1
        
        logger.error(f"Error in {source}: {error}")
        
        if self.error_count_hour >= self.config.max_errors_per_hour:
            if self.config.emergency_stop_on_error:
                logger.critical(f"Too many errors ({self.error_count_hour}/hour), emergency stop triggered")
                await self._handle_critical_error(source, error)
    
    async def _handle_critical_error(self, source: str, error: Exception):
        """Handle critical errors"""
        critical_error = {
            'source': source,
            'error': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': time.time()
        }
        
        self.critical_errors.append(critical_error)
        
        logger.critical(f"Critical error in {source}: {error}")
        
        if self.config.emergency_stop_on_error:
            self.state = EngineState.ERROR
            await self._emit_event("critical_error", critical_error)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status"""
        uptime = time.time() - self.engine_start_time if self.engine_start_time > 0 else 0
        
        return {
            'state': self.state.value,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'strategies_count': len(self.strategies),
            'strategies_active': len([s for s in self.strategies if s.is_enabled()]),
            'active_executions': len(self.active_executions),
            'total_signals_processed': self.total_signals_processed,
            'total_trades_executed': self.total_trades_executed,
            'total_volume_traded': self.total_volume_traded,
            'error_count_hour': self.error_count_hour,
            'execution_success_rate': self._calculate_success_rate(),
            'paper_trading_mode': self.config.enable_paper_trading,
            'last_strategy_update': datetime.fromtimestamp(self.last_strategy_update).isoformat() if self.last_strategy_update else None
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        recent_executions = self.execution_history[-limit:] if self.execution_history else []
        
        return [
            {
                'execution_id': e.execution_id,
                'token_mint': e.token_mint,
                'side': e.side,
                'size_sol': e.size_sol,
                'result': e.result.value,
                'duration_seconds': e.duration_seconds,
                'execution_time': datetime.fromtimestamp(e.execution_time).isoformat(),
                'error_message': e.error_message
            }
            for e in recent_executions
        ]
    
    async def _log_signal_rejection(self, signal, reason: str, alerts: List):
        """Log rejected signal for analysis"""
        rejection = {
            'signal_id': f"{signal.strategy}_{signal.token_mint}_{int(signal.timestamp)}",
            'token_mint': signal.token_mint,
            'strategy': signal.strategy,
            'reason': reason,
            'alerts': [str(alert) for alert in alerts],
            'timestamp': time.time()
        }
        
        logger.info(f"Signal rejected: {rejection['signal_id']} - {reason}")
        await self._emit_event("signal_rejected", rejection)
    
    async def _request_manual_approval(self, signal):
        """Request manual approval for signal (placeholder)"""
        logger.info(f"Manual approval required for signal: {signal.token_mint} {signal.side.value} {signal.size_sol} SOL")
        # In a real implementation, this would integrate with a notification system
        # or web interface for manual approval