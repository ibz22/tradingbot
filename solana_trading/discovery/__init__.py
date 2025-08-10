"""
Solana Trading Bot - Token Discovery Package
============================================

This package handles intelligent token discovery from multiple sources,
including news articles, social media, and blockchain analysis.

Components:
-----------
- token_extractor: Extract token addresses and symbols from text sources
- trend_detector: Identify trending tokens across platforms
- discovery_engine: Orchestrates multi-source token discovery
"""

from .token_extractor import TokenExtractor

__all__ = [
    'TokenExtractor'
]

__version__ = "3.0.0"