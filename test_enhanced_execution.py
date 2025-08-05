    
    def test_order_manager_basic_functionality(self):
        """Test basic order manager functionality"""
        
        async def test_order_submission():
            order_manager = OrderManager(self.broker, self.order_blotter)
            
            order = EnhancedOrder(
                symbol="MSFT",
                side="buy", 
                quantity=50.0,
                strategy_name="test_strategy"
            )
            
            # Submit order
            success = await order_manager.submit_order(order)
            self.assertTrue(success)
            self.assertIsNotNone(order.order_id)
            self.assertEqual(order.status, OrderStatus.SUBMITTED)
            
            # Check active orders
            active_orders = order_manager.get_active_orders()
            self.assertEqual(len(active_orders), 1)
            self.assertIn(order.order_id, active_orders)
            
            # Wait for mock completion
            await asyncio.sleep(0.1)
            
            # Check metrics
            metrics = order_manager.get_metrics()
            self.assertEqual(metrics['orders_submitted'], 1)
            
            await order_manager.cleanup()
        
        self.loop.run_until_complete(test_order_submission())
    
    def test_trade_executor_validation(self):
        """Test trade executor validation logic"""
        
        async def test_validation():
            # Create mock signal
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            # Test valid execution
            valid_signal = MockSignal("buy", 0.8)
            result = await self.trade_executor._validate_execution(
                "AAPL", valid_signal, 10.0, False
            )
            self.assertTrue(result.success)
            
            # Test invalid position size
            invalid_signal = MockSignal("buy", 0.8)
            result = await self.trade_executor._validate_execution(
                "AAPL", invalid_signal, 0.0, False
            )
            self.assertFalse(result.success)
            self.assertIn("Invalid position size", result.error_message)
            
            # Test invalid action
            invalid_action_signal = MockSignal("invalid_action", 0.8)
            result = await self.trade_executor._validate_execution(
                "AAPL", invalid_action_signal, 10.0, False
            )
            self.assertFalse(result.success)
            self.assertIn("Invalid signal action", result.error_message)
        
        self.loop.run_until_complete(test_validation())
    
    def test_dry_run_execution(self):
        """Test dry-run execution simulation"""
        
        async def test_simulation():
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            signal = MockSignal("buy", 0.85)
            
            result = await self.trade_executor.execute_trade(
                symbol="GOOGL",
                signal=signal,
                position_size=5.0,
                is_crypto=False,
                strategy_name="test_strategy"
            )
            
            self.assertIsNotNone(result)
            self.assertTrue(result.success)
            self.assertEqual(result.filled_quantity, 5.0)
            self.assertIsNotNone(result.avg_fill_price)
            self.assertGreater(result.avg_fill_price, 0)
            self.assertGreaterEqual(result.fees, 0)
            self.assertIsNotNone(result.order_id)
        
        self.loop.run_until_complete(test_simulation())
    
    def test_position_reconciliation(self):
        """Test position reconciliation functionality"""
        
        async def test_reconciliation():
            # Set up expected positions
            expected_positions = {
                "AAPL": 100.0,
                "MSFT": 50.0,
                "GOOGL": 25.0
            }
            
            # Mock broker positions (with discrepancy)
            self.broker.positions = {
                "AAPL": 100.0,  # Match
                "MSFT": 45.0,   # Discrepancy
                "TSLA": 10.0    # Unexpected position
            }
            
            # Run reconciliation
            result = await self.trade_executor.reconcile_positions()
            
            # Should find discrepancies
            self.assertFalse(result.get('reconciled', True))
            discrepancies = result.get('discrepancies', {})
            
            # Check specific discrepancies
            self.assertIn("MSFT", discrepancies)
            self.assertIn("GOOGL", discrepancies)
            self.assertIn("TSLA", discrepancies)
            
            # MSFT should show difference
            msft_disc = discrepancies["MSFT"]
            self.assertEqual(msft_disc['expected'], 50.0)
            self.assertEqual(msft_disc['actual'], 45.0)
            self.assertEqual(msft_disc['difference'], -5.0)
            
            # GOOGL should show as missing position
            googl_disc = discrepancies["GOOGL"]
            self.assertEqual(googl_disc['expected'], 25.0)
            self.assertEqual(googl_disc['actual'], 0.0)
            
            # TSLA should show as unexpected
            tsla_disc = discrepancies["TSLA"]
            self.assertEqual(tsla_disc['expected'], 0.0)
            self.assertEqual(tsla_disc['actual'], 10.0)
            self.assertTrue(tsla_disc.get('unexpected', False))
        
        self.loop.run_until_complete(test_reconciliation())
    
    def test_execution_metrics_tracking(self):
        """Test execution metrics tracking"""
        
        async def test_metrics():
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            # Execute multiple trades
            signals = [
                MockSignal("buy", 0.9),
                MockSignal("buy", 0.7),
                MockSignal("sell", 0.8)
            ]
            
            symbols = ["AAPL", "MSFT", "GOOGL"]
            
            for i, signal in enumerate(signals):
                result = await self.trade_executor.execute_trade(
                    symbol=symbols[i],
                    signal=signal,
                    position_size=10.0,
                    is_crypto=False,
                    strategy_name="metrics_test"
                )
                self.assertTrue(result.success)
            
            # Check metrics
            metrics = self.trade_executor.get_execution_metrics()
            
            self.assertEqual(metrics['total_executions'], 3)
            self.assertEqual(metrics['successful_executions'], 3)
            self.assertEqual(metrics['failed_executions'], 0)
            self.assertEqual(metrics['success_rate'], 100.0)
            self.assertGreater(metrics['average_execution_time'], 0)
            self.assertGreaterEqual(metrics['total_fees'], 0)
        
        self.loop.run_until_complete(test_metrics())
    
    def test_order_blotter_integration(self):
        """Test integration with order blotter"""
        
        async def test_blotter():
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            signal = MockSignal("buy", 0.85)
            
            # Execute trade (should log to blotter)
            result = await self.trade_executor.execute_trade(
                symbol="NVDA",
                signal=signal,
                position_size=15.0,
                is_crypto=False,
                strategy_name="blotter_test"
            )
            
            self.assertTrue(result.success)
            
            # Check order blotter
            orders = self.order_blotter.list_orders()
            self.assertGreater(len(orders), 0)
            
            # Find our order
            nvda_orders = [
                order for order in orders.values()
                if order['symbol'] == 'NVDA'
            ]
            
            self.assertGreater(len(nvda_orders), 0)
            
            order = nvda_orders[0]
            self.assertEqual(order['side'], 'buy')
            self.assertEqual(order['qty'], 15.0)
        
        self.loop.run_until_complete(test_blotter())
    
    def test_concurrent_executions(self):
        """Test concurrent order execution"""
        
        async def test_concurrent():
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            # Create multiple concurrent orders
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
            tasks = []
            
            for symbol in symbols:
                signal = MockSignal("buy", 0.8)
                task = self.trade_executor.execute_trade(
                    symbol=symbol,
                    signal=signal,
                    position_size=5.0,
                    is_crypto=False,
                    strategy_name="concurrent_test"
                )
                tasks.append(task)
            
            # Execute all concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            successful = 0
            for result in results:
                if isinstance(result, Exception):
                    self.fail(f"Concurrent execution failed with exception: {result}")
                elif result and result.success:
                    successful += 1
            
            self.assertEqual(successful, len(symbols))
            
            # Check final metrics
            metrics = self.trade_executor.get_execution_metrics()
            self.assertEqual(metrics['successful_executions'], len(symbols))
        
        self.loop.run_until_complete(test_concurrent())
    
    def test_error_handling(self):
        """Test error handling in execution"""
        
        async def test_errors():
            # Create a broker that will fail
            class FailingBroker:
                async def place_order(self, *args, **kwargs):
                    raise Exception("Simulated broker failure")
                
                async def is_market_open(self):
                    return True
                
                async def get_buying_power(self):
                    return 10000.0
                
                async def get_position(self, symbol):
                    return None
            
            failing_executor = EnhancedTradeExecutor(
                broker_gateway=FailingBroker(),
                order_blotter=self.order_blotter,
                is_dry_run=False  # Force real execution
            )
            
            class MockSignal:
                def __init__(self, action, confidence=0.8):
                    self.action = action
                    self.confidence = confidence
                    self.price_target = 105.0
                    self.stop_loss = 95.0
            
            signal = MockSignal("buy", 0.85)
            
            # This should fail gracefully
            result = await failing_executor.execute_trade(
                symbol="FAIL",
                signal=signal,
                position_size=10.0,
                is_crypto=False,
                strategy_name="error_test"
            )
            
            self.assertIsNotNone(result)
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("failed", result.error_message.lower())
        
        self.loop.run_until_complete(test_errors())


class TestMockBrokerGateway(unittest.TestCase):
    """Test suite for mock broker gateway"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.broker = MockBrokerGateway()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.loop.close()
    
    def test_mock_order_placement(self):
        """Test mock order placement"""
        
        async def test_placement():
            # Place a buy order
            order = await self.broker.place_order(
                symbol="AAPL",
                side="buy",
                qty=100.0
            )
            
            self.assertIsNotNone(order)
            self.assertEqual(order['symbol'], "AAPL")
            self.assertEqual(order['side'], "buy")
            self.assertEqual(order['qty'], "100.0")
            self.assertEqual(order['status'], "filled")
            
            # Check position was updated
            positions = await self.broker.get_positions()
            aapl_positions = [p for p in positions if p['symbol'] == 'AAPL']
            
            self.assertEqual(len(aapl_positions), 1)
            self.assertEqual(float(aapl_positions[0]['qty']), 100.0)
        
        self.loop.run_until_complete(test_placement())
    
    def test_mock_position_tracking(self):
        """Test mock position tracking"""
        
        async def test_positions():
            # Execute several trades
            await self.broker.place_order("AAPL", "buy", 100.0)
            await self.broker.place_order("AAPL", "buy", 50.0)
            await self.broker.place_order("AAPL", "sell", 25.0)
            await self.broker.place_order("MSFT", "buy", 75.0)
            
            # Check final positions
            positions = await self.broker.get_positions()
            
            # Should have AAPL (125 shares) and MSFT (75 shares)
            self.assertEqual(len(positions), 2)
            
            aapl_pos = next(p for p in positions if p['symbol'] == 'AAPL')
            msft_pos = next(p for p in positions if p['symbol'] == 'MSFT')
            
            self.assertEqual(float(aapl_pos['qty']), 125.0)
            self.assertEqual(float(msft_pos['qty']), 75.0)
        
        self.loop.run_until_complete(test_positions())


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
