"""
Unified Intelligence System - Complete Social & News Intelligence Integration
===========================================================================

Master intelligence system that unifies:
- News monitoring (Session 1)
- Twitter/X social intelligence
- Reddit community sentiment
- Telegram alpha signals
- Cross-platform sentiment correlation
- Unified trading intelligence scoring

This system provides the complete social intelligence brain for trading decisions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

from .news_monitor import NewsMonitor, NewsArticle
from .twitter_monitor import TwitterMonitor, Tweet
from .reddit_monitor import RedditMonitor, RedditPost
from .telegram_monitor import TelegramMonitor, TelegramMessage
from .social_aggregator import SocialAggregator, SocialSignal, TokenSentimentProfile, MarketSentimentSummary
from .sentiment_analyzer import SentimentAnalyzer
from ..discovery.token_extractor import TokenExtractor
from ..utils.checkpoint import load_checkpoint, save_checkpoint


class SignalStrength(Enum):
    """Signal strength classification"""
    WEAK = 0.25
    MODERATE = 0.5  
    STRONG = 0.75
    EXTREME = 1.0


class SignalType(Enum):
    """Type of intelligence signal"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    ALPHA = "alpha"
    RISK = "risk"
    HYPE = "hype"


@dataclass
class UnifiedIntelligenceSignal:
    """Unified intelligence signal combining all data sources"""
    timestamp: datetime
    token_symbol: str
    signal_type: SignalType
    signal_strength: SignalStrength
    confidence: float
    supporting_platforms: List[str]
    news_sentiment: float
    social_sentiment: float
    technical_indicators: Dict[str, float]
    risk_level: float
    alpha_score: float
    narrative: str
    sources: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['signal_type'] = self.signal_type.value
        data['signal_strength'] = self.signal_strength.value
        return data


@dataclass
class TradingIntelligenceReport:
    """Comprehensive trading intelligence report"""
    timestamp: datetime
    overall_market_sentiment: float
    market_confidence: float
    trending_tokens: Dict[str, UnifiedIntelligenceSignal]
    alpha_opportunities: List[UnifiedIntelligenceSignal]
    risk_alerts: List[UnifiedIntelligenceSignal]
    market_narrative: str
    intelligence_sources_active: List[str]
    data_quality_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['trending_tokens'] = {k: v.to_dict() for k, v in self.trending_tokens.items()}
        data['alpha_opportunities'] = [signal.to_dict() for signal in self.alpha_opportunities]
        data['risk_alerts'] = [signal.to_dict() for signal in self.risk_alerts]
        return data


class UnifiedIntelligenceSystem:
    """
    Master intelligence system combining all social and news monitoring
    """
    
    # Signal strength thresholds
    STRENGTH_THRESHOLDS = {
        SignalStrength.WEAK: 0.3,
        SignalStrength.MODERATE: 0.5,
        SignalStrength.STRONG: 0.7,
        SignalStrength.EXTREME: 0.85
    }
    
    # Platform reliability weights
    PLATFORM_RELIABILITY = {
        'news': 1.0,      # Highest - professional journalism
        'twitter': 0.75,  # High - real-time but can be noisy
        'reddit': 0.7,    # Good - community consensus
        'telegram': 0.6   # Moderate - often hype-driven
    }
    
    # Time decay factors for signals
    TIME_DECAY = {
        'realtime': 1.0,     # < 15 minutes
        'recent': 0.9,       # < 1 hour
        'moderate': 0.7,     # < 4 hours
        'old': 0.5           # < 24 hours
    }
    
    def __init__(self,
                 news_monitor: Optional[NewsMonitor] = None,
                 twitter_monitor: Optional[TwitterMonitor] = None,
                 reddit_monitor: Optional[RedditMonitor] = None,
                 telegram_monitor: Optional[TelegramMonitor] = None,
                 social_aggregator: Optional[SocialAggregator] = None,
                 sentiment_analyzer: Optional[SentimentAnalyzer] = None,
                 token_extractor: Optional[TokenExtractor] = None,
                 checkpoint_file: str = "data/unified_intelligence.json"):
        """
        Initialize Unified Intelligence System
        
        Args:
            news_monitor: News monitoring component
            twitter_monitor: Twitter monitoring component
            reddit_monitor: Reddit monitoring component
            telegram_monitor: Telegram monitoring component
            social_aggregator: Social media aggregator
            sentiment_analyzer: Sentiment analysis component
            token_extractor: Token extraction component
            checkpoint_file: File to store system state
        """
        self.news_monitor = news_monitor
        self.twitter_monitor = twitter_monitor
        self.reddit_monitor = reddit_monitor
        self.telegram_monitor = telegram_monitor
        self.social_aggregator = social_aggregator or SocialAggregator()
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.token_extractor = token_extractor or TokenExtractor()
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load system state
        self.state = load_checkpoint(checkpoint_file, {
            'last_intelligence_update': datetime.now() - timedelta(hours=1),
            'unified_signals': [],
            'intelligence_reports': [],
            'system_performance': {
                'signals_processed': 0,
                'accuracy_score': 0.0,
                'uptime_percentage': 100.0
            },
            'active_monitors': []
        })
        
        # Convert datetime strings
        if isinstance(self.state['last_intelligence_update'], str):
            self.state['last_intelligence_update'] = datetime.fromisoformat(self.state['last_intelligence_update'])
    
    def _calculate_time_decay_factor(self, signal_time: datetime) -> float:
        """
        Calculate time decay factor for signal relevance
        
        Args:
            signal_time: When the signal was generated
            
        Returns:
            Decay factor (0.0 to 1.0)
        """
        age = datetime.now() - signal_time
        
        if age < timedelta(minutes=15):
            return self.TIME_DECAY['realtime']
        elif age < timedelta(hours=1):
            return self.TIME_DECAY['recent']
        elif age < timedelta(hours=4):
            return self.TIME_DECAY['moderate']
        else:
            return self.TIME_DECAY['old']
    
    def _determine_signal_strength(self, combined_score: float, confidence: float) -> SignalStrength:
        """
        Determine signal strength based on score and confidence
        
        Args:
            combined_score: Combined sentiment/alpha score
            confidence: Signal confidence
            
        Returns:
            Signal strength classification
        """
        adjusted_score = abs(combined_score) * confidence
        
        if adjusted_score >= self.STRENGTH_THRESHOLDS[SignalStrength.EXTREME]:
            return SignalStrength.EXTREME
        elif adjusted_score >= self.STRENGTH_THRESHOLDS[SignalStrength.STRONG]:
            return SignalStrength.STRONG
        elif adjusted_score >= self.STRENGTH_THRESHOLDS[SignalStrength.MODERATE]:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _classify_signal_type(self, 
                            sentiment_score: float, 
                            alpha_score: float,
                            risk_score: float,
                            hype_score: float = 0.0) -> SignalType:
        """
        Classify the type of intelligence signal
        
        Args:
            sentiment_score: Overall sentiment (-1 to 1)
            alpha_score: Alpha opportunity score (0 to 1)
            risk_score: Risk level score (0 to 1)  
            hype_score: Hype level score (0 to 1)
            
        Returns:
            Signal type classification
        """
        if risk_score > 0.6:
            return SignalType.RISK
        elif alpha_score > 0.7:
            return SignalType.ALPHA
        elif hype_score > 0.8:
            return SignalType.HYPE
        elif sentiment_score > 0.3:
            return SignalType.BULLISH
        elif sentiment_score < -0.3:
            return SignalType.BEARISH
        else:
            return SignalType.NEUTRAL
    
    async def collect_news_intelligence(self, time_window: timedelta = None) -> List[Dict]:
        """
        Collect intelligence signals from news monitoring
        
        Args:
            time_window: Time window to collect from
            
        Returns:
            List of news-based intelligence data
        """
        if not self.news_monitor:
            return []
        
        if time_window is None:
            time_window = timedelta(hours=4)
        
        news_intelligence = []
        
        try:
            # Get recent news articles (this would be from actual news monitor state)
            # For now, we'll simulate based on potential NewsMonitor usage
            
            self.logger.info("Collecting news intelligence...")
            
            # In production, this would fetch actual analyzed articles:
            # recent_articles = await self.news_monitor.fetch_latest_news(
            #     hours_back=int(time_window.total_seconds() / 3600)
            # )
            
            # For demonstration, we'll return empty list
            # In real implementation, you'd process articles into intelligence signals
            
        except Exception as e:
            self.logger.error(f"Error collecting news intelligence: {e}")
        
        return news_intelligence
    
    async def collect_social_intelligence(self, time_window: timedelta = None) -> Dict[str, Any]:
        """
        Collect intelligence from all social media platforms
        
        Args:
            time_window: Time window to collect from
            
        Returns:
            Combined social intelligence data
        """
        if time_window is None:
            time_window = timedelta(hours=2)
        
        social_data = {
            'twitter': {},
            'reddit': {},
            'telegram': {},
            'aggregated': {}
        }
        
        # Collect Twitter intelligence
        if self.twitter_monitor:
            try:
                twitter_trends = self.twitter_monitor.state.get('hashtag_trends', {})
                social_data['twitter'] = {
                    'trending_hashtags': twitter_trends,
                    'sentiment_avg': sum(data.get('avg_sentiment', 0) for data in twitter_trends.values()) / len(twitter_trends) if twitter_trends else 0.0,
                    'total_mentions': sum(data.get('count', 0) for data in twitter_trends.values())
                }
            except Exception as e:
                self.logger.error(f"Error collecting Twitter intelligence: {e}")
        
        # Collect Reddit intelligence
        if self.reddit_monitor:
            try:
                reddit_sentiment = self.reddit_monitor.state.get('community_sentiment', {})
                social_data['reddit'] = {
                    'subreddit_sentiments': reddit_sentiment,
                    'overall_sentiment': sum(
                        data.get('sentiment', {}).get('overall_sentiment', 0) 
                        for data in reddit_sentiment.values()
                    ) / len(reddit_sentiment) if reddit_sentiment else 0.0,
                    'total_discussions': sum(
                        data.get('sentiment', {}).get('post_count', 0) + data.get('sentiment', {}).get('comment_count', 0)
                        for data in reddit_sentiment.values()
                    )
                }
            except Exception as e:
                self.logger.error(f"Error collecting Reddit intelligence: {e}")
        
        # Collect Telegram intelligence
        if self.telegram_monitor:
            try:
                alpha_signals = self.telegram_monitor.state.get('alpha_signals', [])
                recent_signals = [
                    signal for signal in alpha_signals
                    if datetime.fromisoformat(signal['timestamp']) > datetime.now() - time_window
                ]
                
                social_data['telegram'] = {
                    'alpha_signals': recent_signals,
                    'alpha_count': len(recent_signals),
                    'avg_hype_score': sum(signal.get('hype_score', 0) for signal in recent_signals) / len(recent_signals) if recent_signals else 0.0
                }
            except Exception as e:
                self.logger.error(f"Error collecting Telegram intelligence: {e}")
        
        # Run social aggregation if available
        if self.social_aggregator:
            try:
                aggregated_summary = await self.social_aggregator.run_aggregation(time_window)
                social_data['aggregated'] = {
                    'market_sentiment': aggregated_summary.overall_sentiment,
                    'confidence': aggregated_summary.confidence,
                    'trending_tokens': {k: v.to_dict() for k, v in aggregated_summary.trending_tokens.items()},
                    'hype_level': aggregated_summary.hype_level,
                    'market_narrative': aggregated_summary.market_narrative
                }
            except Exception as e:
                self.logger.error(f"Error running social aggregation: {e}")
        
        return social_data
    
    def create_unified_signal(self,
                            token_symbol: str,
                            news_data: Dict,
                            social_data: Dict,
                            timestamp: datetime = None) -> UnifiedIntelligenceSignal:
        """
        Create unified intelligence signal from news and social data
        
        Args:
            token_symbol: Token symbol
            news_data: News-based intelligence data
            social_data: Social media intelligence data
            timestamp: Signal timestamp
            
        Returns:
            Unified intelligence signal
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Extract sentiment scores
        news_sentiment = news_data.get('sentiment', 0.0)
        
        # Get social sentiment from aggregated data
        aggregated_data = social_data.get('aggregated', {})
        social_sentiment = aggregated_data.get('market_sentiment', 0.0)
        
        # Calculate platform-specific sentiments
        twitter_sentiment = social_data.get('twitter', {}).get('sentiment_avg', 0.0)
        reddit_sentiment = social_data.get('reddit', {}).get('overall_sentiment', 0.0)
        telegram_hype = social_data.get('telegram', {}).get('avg_hype_score', 0.0)
        
        # Determine supporting platforms
        supporting_platforms = []
        if abs(news_sentiment) > 0.2:
            supporting_platforms.append('news')
        if abs(twitter_sentiment) > 0.2:
            supporting_platforms.append('twitter')
        if abs(reddit_sentiment) > 0.2:
            supporting_platforms.append('reddit')
        if telegram_hype > 0.3:
            supporting_platforms.append('telegram')
        
        # Calculate combined sentiment with platform weights
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        
        for platform, sentiment in [
            ('news', news_sentiment),
            ('twitter', twitter_sentiment),
            ('reddit', reddit_sentiment)
        ]:
            if platform in supporting_platforms:
                weight = self.PLATFORM_RELIABILITY[platform]
                total_weighted_sentiment += sentiment * weight
                total_weight += weight
        
        combined_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate alpha score
        alpha_score = 0.0
        if 'telegram' in supporting_platforms:
            alpha_count = social_data.get('telegram', {}).get('alpha_count', 0)
            alpha_score = min(alpha_count / 5.0, 1.0)  # Normalize to 0-1
        
        # Calculate risk level
        risk_level = 0.0
        if combined_sentiment < -0.5:
            risk_level = abs(combined_sentiment)
        
        # Calculate confidence
        platform_agreement = len(supporting_platforms) / 4.0  # Max 4 platforms
        sentiment_magnitude = abs(combined_sentiment)
        confidence = (platform_agreement + sentiment_magnitude) / 2.0
        
        # Apply time decay
        time_decay = self._calculate_time_decay_factor(timestamp)
        confidence *= time_decay
        
        # Determine signal type and strength
        signal_type = self._classify_signal_type(
            combined_sentiment, alpha_score, risk_level, telegram_hype
        )
        signal_strength = self._determine_signal_strength(combined_sentiment, confidence)
        
        # Generate narrative
        narrative = self._generate_signal_narrative(
            token_symbol, signal_type, signal_strength, supporting_platforms, combined_sentiment
        )
        
        # Technical indicators (placeholder for future integration)
        technical_indicators = {
            'rsi': 50.0,  # Neutral default
            'volume_surge': 0.0,
            'price_momentum': combined_sentiment * 0.5
        }
        
        # Create sources list
        sources = [f"{platform}_monitor" for platform in supporting_platforms]
        
        return UnifiedIntelligenceSignal(
            timestamp=timestamp,
            token_symbol=token_symbol,
            signal_type=signal_type,
            signal_strength=signal_strength,
            confidence=confidence,
            supporting_platforms=supporting_platforms,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            technical_indicators=technical_indicators,
            risk_level=risk_level,
            alpha_score=alpha_score,
            narrative=narrative,
            sources=sources
        )
    
    def _generate_signal_narrative(self,
                                 token: str,
                                 signal_type: SignalType,
                                 strength: SignalStrength,
                                 platforms: List[str],
                                 sentiment: float) -> str:
        """
        Generate human-readable narrative for signal
        
        Args:
            token: Token symbol
            signal_type: Type of signal
            strength: Signal strength
            platforms: Supporting platforms
            sentiment: Combined sentiment score
            
        Returns:
            Narrative description
        """
        strength_words = {
            SignalStrength.WEAK: "mild",
            SignalStrength.MODERATE: "moderate", 
            SignalStrength.STRONG: "strong",
            SignalStrength.EXTREME: "extreme"
        }
        
        platform_text = f"{len(platforms)} platform{'s' if len(platforms) > 1 else ''}"
        strength_word = strength_words[strength]
        
        if signal_type == SignalType.BULLISH:
            return f"{strength_word.title()} bullish sentiment for {token} across {platform_text} (sentiment: {sentiment:.2f})"
        elif signal_type == SignalType.BEARISH:
            return f"{strength_word.title()} bearish sentiment for {token} across {platform_text} (sentiment: {sentiment:.2f})"
        elif signal_type == SignalType.ALPHA:
            return f"Alpha opportunity detected for {token} with {strength_word} conviction from {platform_text}"
        elif signal_type == SignalType.RISK:
            return f"Risk alert for {token} - {strength_word} negative signals from {platform_text}"
        elif signal_type == SignalType.HYPE:
            return f"High hype levels detected for {token} across {platform_text}"
        else:
            return f"Neutral sentiment for {token} across {platform_text}"
    
    async def generate_intelligence_report(self, time_window: timedelta = None) -> TradingIntelligenceReport:
        """
        Generate comprehensive trading intelligence report
        
        Args:
            time_window: Time window for analysis
            
        Returns:
            Complete trading intelligence report
        """
        if time_window is None:
            time_window = timedelta(hours=4)
        
        self.logger.info("Generating unified intelligence report...")
        
        # Collect all intelligence data
        news_intelligence = await self.collect_news_intelligence(time_window)
        social_intelligence = await self.collect_social_intelligence(time_window)
        
        # Extract trending tokens from social data
        trending_tokens_data = social_intelligence.get('aggregated', {}).get('trending_tokens', {})
        
        # Generate unified signals for trending tokens
        unified_signals = {}
        alpha_opportunities = []
        risk_alerts = []
        
        for token, token_data in trending_tokens_data.items():
            try:
                # Create token-specific news data (simplified)
                token_news_data = {
                    'sentiment': 0.0,  # Would be extracted from actual news about this token
                    'relevance': 0.5,
                    'source_count': 0
                }
                
                # Create unified signal
                unified_signal = self.create_unified_signal(
                    token, token_news_data, social_intelligence
                )
                
                unified_signals[token] = unified_signal
                
                # Categorize signals
                if unified_signal.signal_type == SignalType.ALPHA:
                    alpha_opportunities.append(unified_signal)
                elif unified_signal.signal_type == SignalType.RISK:
                    risk_alerts.append(unified_signal)
                    
            except Exception as e:
                self.logger.error(f"Error creating unified signal for {token}: {e}")
        
        # Calculate overall market sentiment
        aggregated_data = social_intelligence.get('aggregated', {})
        overall_market_sentiment = aggregated_data.get('market_sentiment', 0.0)
        market_confidence = aggregated_data.get('confidence', 0.0)
        
        # Generate market narrative
        market_narrative = aggregated_data.get('market_narrative', 'Insufficient data for market analysis')
        
        # Determine active intelligence sources
        intelligence_sources_active = []
        if self.news_monitor:
            intelligence_sources_active.append('news_monitor')
        if self.twitter_monitor:
            intelligence_sources_active.append('twitter_monitor')
        if self.reddit_monitor:
            intelligence_sources_active.append('reddit_monitor')
        if self.telegram_monitor:
            intelligence_sources_active.append('telegram_monitor')
        
        # Calculate data quality score
        platform_count = len(intelligence_sources_active)
        signal_count = len(unified_signals)
        confidence_avg = sum(signal.confidence for signal in unified_signals.values()) / len(unified_signals) if unified_signals else 0.0
        
        data_quality_score = (platform_count / 4.0 * 0.4 + min(signal_count / 10.0, 1.0) * 0.3 + confidence_avg * 0.3)
        
        # Sort opportunities and risks by strength and confidence
        alpha_opportunities.sort(key=lambda x: x.signal_strength.value * x.confidence, reverse=True)
        risk_alerts.sort(key=lambda x: x.risk_level * x.confidence, reverse=True)
        
        report = TradingIntelligenceReport(
            timestamp=datetime.now(),
            overall_market_sentiment=overall_market_sentiment,
            market_confidence=market_confidence,
            trending_tokens=unified_signals,
            alpha_opportunities=alpha_opportunities[:10],  # Top 10
            risk_alerts=risk_alerts[:5],  # Top 5 risks
            market_narrative=market_narrative,
            intelligence_sources_active=intelligence_sources_active,
            data_quality_score=data_quality_score
        )
        
        # Update system state
        self.state['unified_signals'].extend([signal.to_dict() for signal in unified_signals.values()])
        self.state['unified_signals'] = self.state['unified_signals'][-500:]  # Keep last 500
        
        self.state['intelligence_reports'].append(report.to_dict())
        self.state['intelligence_reports'] = self.state['intelligence_reports'][-50:]  # Keep last 50
        
        self.state['last_intelligence_update'] = datetime.now()
        self.state['active_monitors'] = intelligence_sources_active
        
        self._save_state()
        
        self.logger.info(f"Intelligence report generated: {len(unified_signals)} signals, quality score: {data_quality_score:.2f}")
        
        return report
    
    async def start_continuous_intelligence(self,
                                          callback: Optional[Callable] = None,
                                          interval_minutes: int = 30):
        """
        Start continuous intelligence generation
        
        Args:
            callback: Function to call with new reports
            interval_minutes: Update interval
        """
        self.logger.info("Starting continuous unified intelligence system...")
        
        while True:
            try:
                report = await self.generate_intelligence_report()
                
                if callback:
                    await callback(report)
                
                # Update performance metrics
                self.state['system_performance']['signals_processed'] += len(report.trending_tokens)
                
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in intelligence loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def get_system_status(self) -> Dict:
        """Get unified intelligence system status"""
        return {
            'active_monitors': self.state.get('active_monitors', []),
            'last_update': self.state['last_intelligence_update'].isoformat(),
            'total_signals_generated': len(self.state.get('unified_signals', [])),
            'reports_generated': len(self.state.get('intelligence_reports', [])),
            'system_performance': self.state.get('system_performance', {}),
            'data_quality_score': self.state.get('intelligence_reports', [{}])[-1].get('data_quality_score', 0.0) if self.state.get('intelligence_reports') else 0.0
        }
    
    def _save_state(self):
        """Save system state to checkpoint"""
        # Convert datetime objects for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['last_intelligence_update'] = self.state['last_intelligence_update'].isoformat()
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_unified_intelligence():
    """Test the unified intelligence system"""
    
    # Initialize unified system (all monitors would be None for testing)
    system = UnifiedIntelligenceSystem()
    
    print("Testing Unified Intelligence System...")
    
    # Generate a test report
    report = await system.generate_intelligence_report()
    
    print(f"\nIntelligence Report Generated:")
    print(f"  Timestamp: {report.timestamp}")
    print(f"  Overall Market Sentiment: {report.overall_market_sentiment:.3f}")
    print(f"  Market Confidence: {report.market_confidence:.3f}")
    print(f"  Trending Tokens: {len(report.trending_tokens)}")
    print(f"  Alpha Opportunities: {len(report.alpha_opportunities)}")
    print(f"  Risk Alerts: {len(report.risk_alerts)}")
    print(f"  Market Narrative: {report.market_narrative}")
    print(f"  Active Sources: {report.intelligence_sources_active}")
    print(f"  Data Quality Score: {report.data_quality_score:.2f}")
    
    # Show system status
    status = system.get_system_status()
    print(f"\nSystem Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nUnified Intelligence System testing complete!")


if __name__ == "__main__":
    asyncio.run(test_unified_intelligence())