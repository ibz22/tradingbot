import unittest
import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import from the integrated main application
try:
    from main import load_config
    MAIN_AVAILABLE = True
except ImportError:
    MAIN_AVAILABLE = False

# Import from halalbot package
from halalbot.core.risk import RiskManager
from halalbot.screening.halal_rules import load_rules
from halalbot.strategies.momentum import MomentumStrategy

class TestIntegratedSystem(unittest.TestCase):
    """Test suite for the integrated halalbot system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'max_portfolio_risk': 0.02,
            'max_position_risk': 0.01,
            'max_position_pct': 0.1,
            'fmp_api_key': 'demo',
            'initial_capital': 100000,
            'stock_universe': ['AAPL', 'MSFT'],
            'crypto_universe': ['BTC/USDT', 'ETH/USDT']
        }
    
    def test_risk_manager_integration(self):
        """Test risk manager with realistic parameters."""
        rm = RiskManager(
            max_portfolio_risk=0.02,
            max_position_risk=0.01
        )
        
        # Test position size calculation
        account_value = 100000
        current_price = 150.0
        stop_price = 140.0
        
        # This should not raise an exception
        position_size = rm.calculate_position_size(
            account_value, 
            None,  # confidence parameter not in core class
            None,  # asset_config parameter not in core class  
            current_price,
            stop_price
        )
        
        # Should return a reasonable position size
        self.assertGreater(position_size, 0)
        self.assertLess(position_size * current_price, account_value * 0.1)
    
    def test_momentum_strategy(self):
        """Test momentum strategy initialization."""
        strategy = MomentumStrategy(lookback=20)
        
        self.assertEqual(strategy.lookback, 20)
        self.assertIsInstance(strategy, MomentumStrategy)
    
    def test_halal_rules_loading(self):
        """Test halal rules loading with temporary config."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            test_rules = {
                'halal_crypto': {
                    'BTC/USDT': {
                        'reason': 'Digital store of value',
                        'risk_level': 'medium'
                    }
                },
                'prohibited_features': {
                    'GAMBLING': 'Gambling activities are prohibited'
                }
            }
            yaml.dump(test_rules, f)
            temp_file = f.name
        
        try:
            # Load rules
            rules = load_rules(temp_file)
            
            # Verify structure
            self.assertIn('halal_crypto', rules)
            self.assertIn('prohibited_features', rules)
            self.assertIn('BTC/USDT', rules['halal_crypto'])
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    @unittest.skipUnless(MAIN_AVAILABLE, "Main module not available")
    def test_config_loading(self):
        """Test configuration loading from main module."""
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_config, f)
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            
            # Verify required keys
            self.assertIn('max_portfolio_risk', config)
            self.assertIn('stock_universe', config)
            self.assertEqual(config['max_portfolio_risk'], 0.02)
            
        finally:
            os.unlink(temp_file)
    
    def test_package_structure(self):
        """Test that halalbot package structure is correct."""
        # Test core imports
        from halalbot.core.engine import TradingEngine
        from halalbot.core.position_store import PositionStore
        
        # Test screening imports  
        from halalbot.screening.data_gateway import DataGateway, FMPGateway
        from halalbot.screening.advanced_screener import AdvancedHalalScreener
        
        # Test strategy imports
        from halalbot.strategies.momentum import MomentumStrategy
        from halalbot.strategies.mean_reversion import MeanReversionStrategy
        
        # Test broker import
        from halalbot.broker_gateway import AlpacaBrokerGateway
        
        # If we get here without ImportError, the structure is correct
        self.assertTrue(True)
    
    def test_portfolio_risk_calculation(self):
        """Test portfolio risk calculation with mock positions."""
        rm = RiskManager()
        
        # Mock positions
        positions = {
            'AAPL': {'value': 10000},
            'MSFT': {'value': 15000}, 
            'GOOGL': {'value': 5000}
        }
        
        risk_metrics = rm.calculate_portfolio_risk(positions)
        
        # Verify risk metrics structure
        self.assertIn('total_risk', risk_metrics)
        self.assertIn('concentration_risk', risk_metrics)
        self.assertIn('number_of_positions', risk_metrics)
        
        # Verify calculations
        self.assertEqual(risk_metrics['number_of_positions'], 3)
        self.assertGreater(risk_metrics['concentration_risk'], 0)


class TestHalalCompliance(unittest.TestCase):
    """Test halal compliance functionality."""
    
    def test_halal_crypto_rules(self):
        """Test halal crypto rules loading."""
        # Test with config.yaml if it exists
        if Path('config.yaml').exists():
            rules = load_rules('config.yaml')
            
            # Should have both sections
            self.assertIn('halal_crypto', rules)
            self.assertIn('prohibited_features', rules)
            
            # Test approved cryptos
            halal_crypto = rules.get('halal_crypto', {})
            if halal_crypto:
                for crypto, info in halal_crypto.items():
                    self.assertIsInstance(info, dict)
                    # Should have required fields
                    self.assertIn('reason', info)
    
    def test_empty_config_handling(self):
        """Test handling of missing config files."""
        # Should return empty structure for non-existent file
        rules = load_rules('non_existent_file.yaml')
        
        self.assertEqual(rules['halal_crypto'], {})
        self.assertEqual(rules['prohibited_features'], {})


if __name__ == '__main__':
    # Setup logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)
