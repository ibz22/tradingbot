"""
Collection of trading strategies for the halalbot trading system.

Each strategy implements a ``generate_signal`` method used by the backtest
engine and live trading engine to decide when to buy, sell or hold.  This
subpackage includes a basic momentum strategy, a simple mean reversion
strategy and a placeholder for machine learning driven approaches.
"""

from .momentum import MomentumStrategy  # noqa: F401
from .mean_reversion import MeanReversionStrategy  # noqa: F401
from .ml import MLStrategy  # noqa: F401
