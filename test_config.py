import unittest
import os
import sys
import yaml

# Add the parent directory to the path to import the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingbotupdated import TradingConfig, setup_logging

# Configure logging for the test suite
setup_logging(log_level="CRITICAL")

class TestTradingConfig(unittest.TestCase):
    """Test suite for the TradingConfig dataclass."""

    def test_default_config_is_valid(self):
        """Test if the default configuration is valid upon creation."""
        config = TradingConfig()
        self.assertIsInstance(config, TradingConfig)
        self.assertEqual(config.max_portfolio_risk, 0.02)
        self.assertAlmostEqual(sum(config.default_strategy_weights.values()), 1.0)
    
    def test_validation_failure_on_invalid_risk(self):
        """Test if validation correctly raises ValueError for invalid risk parameters."""
        with self.assertRaises(ValueError):
            TradingConfig(max_portfolio_risk=1.5)
            
    def test_validation_failure_on_invalid_strategy_weights(self):
        """Test if validation correctly raises ValueError for invalid strategy weights."""
        with self.assertRaises(ValueError):
            TradingConfig(default_strategy_weights={'momentum': 0.5, 'mean_reversion': 0.6})
            
    def test_load_from_yaml_success(self):
        """Test loading a valid config from a mock YAML file."""
        mock_yaml_content = """
max_portfolio_risk: 0.03
max_position_risk: 0.015
stock_universe:
- MSFT
- GOOG
"""
        with open('test_config.yaml', 'w') as f:
            f.write(mock_yaml_content)
        
        config = TradingConfig.from_yaml('test_config.yaml')
        self.assertEqual(config.max_portfolio_risk, 0.03)
        self.assertIn('MSFT', config.stock_universe)
        
        os.remove('test_config.yaml')
        
    def test_load_from_yaml_nonexistent_file(self):
        """Test that a nonexistent file creates a default config."""
        if os.path.exists('nonexistent_config.yaml'):
            os.remove('nonexistent_config.yaml')
            
        config = TradingConfig.from_yaml('nonexistent_config.yaml')
        self.assertIsInstance(config, TradingConfig)
        self.assertEqual(config.max_portfolio_risk, 0.02)
        
        # Clean up the created default file
        os.remove('nonexistent_config.yaml')

if __name__ == '__main__':
    unittest.main()