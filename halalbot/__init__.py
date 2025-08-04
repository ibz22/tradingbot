"""
Halalbot package initialization.

This package provides modules for halal-compliant trading automation.  It is
split into logical subpackages such as ``core`` for the event loop and risk
management, ``screening`` for halal rules and data retrieval, ``backtest`` for
historical simulation, and ``strategies`` for various trading strategies.  See
submodules for details.
"""

__all__ = [
    "core",
    "screening",
    "backtest",
    "strategies",
]
