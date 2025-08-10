"""
Solana Trading Bot - Sentiment Analysis Package
====================================================

This package provides comprehensive sentiment analysis capabilities for Solana tokens,
including news monitoring, social media sentiment, and AI-powered analysis.

Components:
-----------
- news_monitor: NewsAPI integration for real-time news monitoring
- sentiment_analyzer: Multi-layered sentiment analysis with AI/ML models
- social_monitor: Reddit, Twitter, and Telegram social sentiment tracking
- sentiment_aggregator: Combines multiple sentiment sources into unified scores
"""

from .news_monitor import NewsMonitor
from .sentiment_analyzer import SentimentAnalyzer

__all__ = [
    'NewsMonitor',
    'SentimentAnalyzer'
]

__version__ = "3.0.0"