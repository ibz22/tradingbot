"""
Social Aggregator - Cross-platform Sentiment Correlation for Solana Trading Bot
==============================================================================

Advanced social intelligence aggregator that combines sentiment from:
- News monitoring (Session 1)
- Twitter/X monitoring  
- Reddit intelligence
- Telegram channels

Features:
- Cross-platform sentiment correlation
- Weighted sentiment scoring based on platform credibility
- Influencer impact calculation across platforms
- Social momentum tracking and trend prediction
- Unified social intelligence scoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

from .news_monitor import NewsMonitor, NewsArticle
from .twitter_monitor import TwitterMonitor, Tweet
from .reddit_monitor import RedditMonitor, RedditPost, RedditComment  
from .telegram_monitor import TelegramMonitor, TelegramMessage
from .sentiment_analyzer import SentimentAnalyzer, SentimentPolarity
from ..utils.checkpoint import load_checkpoint, save_checkpoint


class PlatformWeight(Enum):
    """Platform credibility weights for sentiment aggregation"""
    NEWS = 1.0        # Highest credibility - professional journalism
    TWITTER = 0.7     # Medium-high - real-time but noisy
    REDDIT = 0.6      # Medium - community driven, vote-weighted
    TELEGRAM = 0.5    # Medium-low - often hype-driven


@dataclass
class SocialSignal:
    """Unified social media signal across platforms"""
    timestamp: datetime
    platform: str
    content: str
    sentiment_score: float
    confidence: float
    influence_score: float
    engagement_metrics: Dict[str, Union[int, float]]
    tokens_mentioned: List[str]
    source_id: str  # Message/tweet/post ID
    source_user: str = ""
    platform_specific_data: Dict = None
    
    def __post_init__(self):
        if self.platform_specific_data is None:
            self.platform_specific_data = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class TokenSentimentProfile:
    """Comprehensive sentiment profile for a token across platforms"""
    symbol: str
    overall_sentiment: float
    confidence: float
    platform_sentiments: Dict[str, float]
    total_mentions: int
    platform_mentions: Dict[str, int]
    trending_score: float
    momentum_score: float
    risk_signals: List[str]
    alpha_signals: List[str]
    last_updated: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class MarketSentimentSummary:
    """Overall market sentiment summary across all platforms"""
    overall_sentiment: float
    confidence: float
    platform_breakdown: Dict[str, Dict[str, float]]
    trending_tokens: Dict[str, TokenSentimentProfile]
    sentiment_momentum: float  # Rate of change
    hype_level: float
    fear_greed_index: float
    market_narrative: str
    last_updated: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        # Convert TokenSentimentProfile objects to dicts
        data['trending_tokens'] = {
            k: v.to_dict() if hasattr(v, 'to_dict') else v 
            for k, v in self.trending_tokens.items()
        }
        return data


class SocialAggregator:
    """
    Advanced social intelligence aggregation system
    """
    
    # Platform credibility and weight configuration
    PLATFORM_WEIGHTS = {
        'news': PlatformWeight.NEWS.value,
        'twitter': PlatformWeight.TWITTER.value,
        'reddit': PlatformWeight.REDDIT.value,
        'telegram': PlatformWeight.TELEGRAM.value
    }
    
    # Time windows for different analysis types
    TIME_WINDOWS = {
        'realtime': timedelta(minutes=15),
        'short_term': timedelta(hours=4),
        'medium_term': timedelta(hours=24),
        'long_term': timedelta(days=7)
    }
    
    # Minimum thresholds for signal validity
    SIGNAL_THRESHOLDS = {
        'min_mentions': 3,
        'min_platforms': 2,
        'min_confidence': 0.3,
        'min_influence': 0.1
    }
    
    def __init__(self,
                 news_monitor: Optional[NewsMonitor] = None,
                 twitter_monitor: Optional[TwitterMonitor] = None,
                 reddit_monitor: Optional[RedditMonitor] = None,
                 telegram_monitor: Optional[TelegramMonitor] = None,
                 checkpoint_file: str = "data/social_aggregator.json"):
        """
        Initialize Social Aggregator
        
        Args:
            news_monitor: News monitoring instance
            twitter_monitor: Twitter monitoring instance  
            reddit_monitor: Reddit monitoring instance
            telegram_monitor: Telegram monitoring instance
            checkpoint_file: File to store aggregation state
        """
        self.news_monitor = news_monitor
        self.twitter_monitor = twitter_monitor
        self.reddit_monitor = reddit_monitor
        self.telegram_monitor = telegram_monitor
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'last_aggregation': datetime.now() - timedelta(hours=1),
            'social_signals': [],
            'token_profiles': {},
            'market_history': [],
            'platform_stats': {},
            'correlation_data': {}
        })
        
        # Convert datetime strings back to objects
        if isinstance(self.state['last_aggregation'], str):
            self.state['last_aggregation'] = datetime.fromisoformat(self.state['last_aggregation'])
    
    def _normalize_sentiment_score(self, score: float, platform: str) -> float:
        """
        Normalize sentiment scores across different platforms
        
        Args:
            score: Raw sentiment score
            platform: Source platform
            
        Returns:
            Normalized sentiment score
        """
        # Platform-specific normalization adjustments
        platform_adjustments = {
            'twitter': 0.9,    # Twitter tends to be more extreme
            'reddit': 1.0,     # Reddit scores are well-balanced
            'telegram': 0.8,   # Telegram can be very hype-driven
            'news': 1.1        # News sentiment is often understated
        }
        
        adjustment = platform_adjustments.get(platform, 1.0)
        normalized_score = score * adjustment
        
        # Ensure bounds [-1.0, 1.0]
        return max(min(normalized_score, 1.0), -1.0)
    
    def _calculate_influence_weight(self, signal: SocialSignal) -> float:
        """
        Calculate influence weight for a social signal
        
        Args:
            signal: Social signal to weight
            
        Returns:
            Influence weight (0.0 to 1.0)
        """
        base_weight = self.PLATFORM_WEIGHTS.get(signal.platform, 0.5)
        
        # Adjust for signal confidence
        confidence_adjustment = signal.confidence
        
        # Adjust for influence score
        influence_adjustment = signal.influence_score
        
        # Adjust for engagement
        engagement_metrics = signal.engagement_metrics
        engagement_score = 0.0
        
        if signal.platform == 'twitter':
            likes = engagement_metrics.get('like_count', 0)
            retweets = engagement_metrics.get('retweet_count', 0)
            engagement_score = min((likes + retweets * 2) / 1000, 1.0)
        elif signal.platform == 'reddit':
            upvotes = engagement_metrics.get('score', 0)
            comments = engagement_metrics.get('num_comments', 0)
            engagement_score = min((upvotes + comments * 3) / 100, 1.0)
        elif signal.platform == 'telegram':
            hype_score = engagement_metrics.get('hype_score', 0)
            engagement_score = hype_score
        elif signal.platform == 'news':
            relevance = engagement_metrics.get('relevance_score', 0.5)
            engagement_score = relevance
        
        # Calculate final weight
        final_weight = (
            base_weight * 0.4 +
            confidence_adjustment * 0.3 +
            influence_adjustment * 0.2 +
            engagement_score * 0.1
        )
        
        return min(final_weight, 1.0)
    
    async def collect_social_signals(self, time_window: timedelta = None) -> List[SocialSignal]:
        """
        Collect social signals from all available platforms
        
        Args:
            time_window: Time window to collect signals from
            
        Returns:
            List of social signals
        """
        if time_window is None:
            time_window = self.TIME_WINDOWS['short_term']
        
        cutoff_time = datetime.now() - time_window
        signals = []
        
        # Collect news signals
        if self.news_monitor:
            try:
                # This would get recent analyzed articles
                # For now, we'll simulate based on existing state
                self.logger.info("Collecting news signals...")
                # In production, you'd fetch actual recent articles
            except Exception as e:
                self.logger.error(f"Error collecting news signals: {e}")
        
        # Collect Twitter signals
        if self.twitter_monitor:
            try:
                self.logger.info("Collecting Twitter signals...")
                # Get recent trending topics and influencer tweets
                trends = self.twitter_monitor.state.get('hashtag_trends', {})
                
                for hashtag, trend_data in trends.items():
                    if datetime.now() - timedelta(hours=4) < cutoff_time:  # Recent trends
                        signal = SocialSignal(
                            timestamp=datetime.now(),
                            platform='twitter',
                            content=f"#{hashtag}",
                            sentiment_score=trend_data.get('avg_sentiment', 0.0),
                            confidence=min(trend_data.get('count', 0) / 10, 1.0),
                            influence_score=trend_data.get('avg_influence', 0.0),
                            engagement_metrics={
                                'mention_count': trend_data.get('count', 0),
                                'avg_engagement': trend_data.get('avg_engagement', 0),
                                'trend_score': trend_data.get('trend_score', 0)
                            },
                            tokens_mentioned=[hashtag.upper()],
                            source_id=f"twitter_trend_{hashtag}",
                            platform_specific_data=trend_data
                        )
                        signals.append(signal)
                        
            except Exception as e:
                self.logger.error(f"Error collecting Twitter signals: {e}")
        
        # Collect Reddit signals
        if self.reddit_monitor:
            try:
                self.logger.info("Collecting Reddit signals...")
                community_sentiment = self.reddit_monitor.state.get('community_sentiment', {})
                
                for subreddit, data in community_sentiment.items():
                    sentiment_data = data.get('sentiment', {})
                    trending_tokens = data.get('trending_tokens', {})
                    
                    # Create signals for trending tokens
                    for token, token_data in trending_tokens.items():
                        signal = SocialSignal(
                            timestamp=datetime.now(),
                            platform='reddit',
                            content=f"r/{subreddit} discussion about {token}",
                            sentiment_score=token_data.get('avg_sentiment', 0.0),
                            confidence=min(token_data.get('mentions', 0) / 20, 1.0),
                            influence_score=token_data.get('avg_engagement', 0.0),
                            engagement_metrics={
                                'mentions': token_data.get('mentions', 0),
                                'avg_engagement': token_data.get('avg_engagement', 0),
                                'subreddit_count': token_data.get('subreddit_count', 1)
                            },
                            tokens_mentioned=[token],
                            source_id=f"reddit_{subreddit}_{token}",
                            platform_specific_data=token_data
                        )
                        signals.append(signal)
                        
            except Exception as e:
                self.logger.error(f"Error collecting Reddit signals: {e}")
        
        # Collect Telegram signals
        if self.telegram_monitor:
            try:
                self.logger.info("Collecting Telegram signals...")
                alpha_signals = self.telegram_monitor.state.get('alpha_signals', [])
                
                for alpha_signal in alpha_signals[-50:]:  # Recent alpha signals
                    signal_time = datetime.fromisoformat(alpha_signal['timestamp'])
                    if signal_time > cutoff_time:
                        signal = SocialSignal(
                            timestamp=signal_time,
                            platform='telegram',
                            content=f"Alpha signal from {alpha_signal.get('chat_title', 'Unknown')}",
                            sentiment_score=0.5,  # Neutral but notable
                            confidence=0.8,       # High confidence for alpha signals
                            influence_score=alpha_signal.get('hype_score', 0.0),
                            engagement_metrics={
                                'hype_score': alpha_signal.get('hype_score', 0.0),
                                'signal_count': len(alpha_signal.get('signals', []))
                            },
                            tokens_mentioned=[],  # Would extract from signal text
                            source_id=f"telegram_alpha_{alpha_signal.get('message_id')}",
                            platform_specific_data=alpha_signal
                        )
                        signals.append(signal)
                        
            except Exception as e:
                self.logger.error(f"Error collecting Telegram signals: {e}")
        
        self.logger.info(f"Collected {len(signals)} social signals")
        return signals
    
    def calculate_token_sentiment_profile(self, 
                                        token: str,
                                        signals: List[SocialSignal],
                                        time_window: timedelta = None) -> TokenSentimentProfile:
        """
        Calculate comprehensive sentiment profile for a token
        
        Args:
            token: Token symbol to analyze
            signals: List of social signals
            time_window: Time window for analysis
            
        Returns:
            Token sentiment profile
        """
        if time_window is None:
            time_window = self.TIME_WINDOWS['medium_term']
        
        cutoff_time = datetime.now() - time_window
        
        # Filter signals for this token
        token_signals = [
            signal for signal in signals
            if (token.upper() in [t.upper() for t in signal.tokens_mentioned] and
                signal.timestamp > cutoff_time)
        ]
        
        if not token_signals:
            return TokenSentimentProfile(
                symbol=token,
                overall_sentiment=0.0,
                confidence=0.0,
                platform_sentiments={},
                total_mentions=0,
                platform_mentions={},
                trending_score=0.0,
                momentum_score=0.0,
                risk_signals=[],
                alpha_signals=[],
                last_updated=datetime.now()
            )
        
        # Calculate weighted sentiment by platform
        platform_sentiments = {}
        platform_mentions = {}
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        
        for signal in token_signals:
            platform = signal.platform
            
            # Normalize sentiment score
            normalized_sentiment = self._normalize_sentiment_score(
                signal.sentiment_score, platform
            )
            
            # Calculate influence weight
            weight = self._calculate_influence_weight(signal)
            
            # Update platform aggregations
            if platform not in platform_sentiments:
                platform_sentiments[platform] = []
                platform_mentions[platform] = 0
            
            platform_sentiments[platform].append(normalized_sentiment)
            platform_mentions[platform] += 1
            
            # Update overall aggregations
            total_weighted_sentiment += normalized_sentiment * weight
            total_weight += weight
        
        # Calculate overall sentiment
        overall_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate platform averages
        platform_avg_sentiments = {
            platform: sum(sentiments) / len(sentiments)
            for platform, sentiments in platform_sentiments.items()
        }
        
        # Calculate confidence based on signal consistency and volume
        sentiment_values = [signal.sentiment_score for signal in token_signals]
        sentiment_std = statistics.stdev(sentiment_values) if len(sentiment_values) > 1 else 0.5
        consistency_factor = max(0, 1 - sentiment_std)
        volume_factor = min(len(token_signals) / 20, 1.0)
        platform_diversity = len(platform_sentiments) / len(self.PLATFORM_WEIGHTS)
        
        confidence = (consistency_factor * 0.4 + volume_factor * 0.3 + platform_diversity * 0.3)
        
        # Calculate trending score
        recent_signals = [
            s for s in token_signals
            if s.timestamp > datetime.now() - self.TIME_WINDOWS['short_term']
        ]
        trending_score = len(recent_signals) / max(len(token_signals), 1)
        
        # Calculate momentum (sentiment change over time)
        momentum_score = 0.0
        if len(token_signals) >= 2:
            sorted_signals = sorted(token_signals, key=lambda x: x.timestamp)
            early_sentiment = sum(s.sentiment_score for s in sorted_signals[:len(sorted_signals)//2])
            recent_sentiment = sum(s.sentiment_score for s in sorted_signals[len(sorted_signals)//2:])
            early_count = len(sorted_signals[:len(sorted_signals)//2])
            recent_count = len(sorted_signals[len(sorted_signals)//2:])
            
            if early_count > 0 and recent_count > 0:
                momentum_score = (recent_sentiment/recent_count) - (early_sentiment/early_count)
        
        # Detect risk and alpha signals
        risk_signals = []
        alpha_signals = []
        
        for signal in token_signals:
            if signal.platform == 'telegram':
                # Telegram alpha signals
                if signal.engagement_metrics.get('hype_score', 0) > 0.5:
                    alpha_signals.append(f"High hype on Telegram: {signal.content[:50]}")
            
            if abs(signal.sentiment_score) > 0.8 and signal.confidence > 0.7:
                if signal.sentiment_score > 0:
                    alpha_signals.append(f"Strong positive sentiment on {signal.platform}")
                else:
                    risk_signals.append(f"Strong negative sentiment on {signal.platform}")
        
        return TokenSentimentProfile(
            symbol=token,
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            platform_sentiments=platform_avg_sentiments,
            total_mentions=len(token_signals),
            platform_mentions=platform_mentions,
            trending_score=trending_score,
            momentum_score=momentum_score,
            risk_signals=risk_signals,
            alpha_signals=alpha_signals,
            last_updated=datetime.now()
        )
    
    def calculate_market_sentiment_summary(self, 
                                         signals: List[SocialSignal],
                                         token_profiles: Dict[str, TokenSentimentProfile]) -> MarketSentimentSummary:
        """
        Calculate overall market sentiment summary
        
        Args:
            signals: All social signals
            token_profiles: Token sentiment profiles
            
        Returns:
            Market sentiment summary
        """
        if not signals:
            return MarketSentimentSummary(
                overall_sentiment=0.0,
                confidence=0.0,
                platform_breakdown={},
                trending_tokens={},
                sentiment_momentum=0.0,
                hype_level=0.0,
                fear_greed_index=0.5,
                market_narrative="Insufficient data",
                last_updated=datetime.now()
            )
        
        # Calculate overall sentiment
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        
        platform_breakdown = {}
        
        for signal in signals:
            weight = self._calculate_influence_weight(signal)
            normalized_sentiment = self._normalize_sentiment_score(
                signal.sentiment_score, signal.platform
            )
            
            total_weighted_sentiment += normalized_sentiment * weight
            total_weight += weight
            
            # Platform breakdown
            platform = signal.platform
            if platform not in platform_breakdown:
                platform_breakdown[platform] = {
                    'sentiment': 0.0,
                    'weight': 0.0,
                    'signal_count': 0
                }
            
            platform_data = platform_breakdown[platform]
            platform_data['sentiment'] += normalized_sentiment * weight
            platform_data['weight'] += weight
            platform_data['signal_count'] += 1
        
        # Finalize platform breakdown
        for platform, data in platform_breakdown.items():
            if data['weight'] > 0:
                data['sentiment'] = data['sentiment'] / data['weight']
            data['confidence'] = min(data['signal_count'] / 10, 1.0)
        
        overall_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate confidence
        sentiment_values = [signal.sentiment_score for signal in signals]
        overall_confidence = min(len(signals) / 50, 1.0) * (1 - statistics.stdev(sentiment_values) if len(sentiment_values) > 1 else 0.5)
        
        # Calculate momentum (recent vs historical sentiment)
        recent_cutoff = datetime.now() - self.TIME_WINDOWS['realtime']
        recent_signals = [s for s in signals if s.timestamp > recent_cutoff]
        
        if recent_signals and len(signals) > len(recent_signals):
            recent_sentiment = sum(s.sentiment_score for s in recent_signals) / len(recent_signals)
            historical_sentiment = sum(s.sentiment_score for s in signals if s.timestamp <= recent_cutoff)
            historical_count = len(signals) - len(recent_signals)
            historical_sentiment = historical_sentiment / historical_count if historical_count > 0 else 0
            
            sentiment_momentum = recent_sentiment - historical_sentiment
        else:
            sentiment_momentum = 0.0
        
        # Calculate hype level (based on extreme sentiment and engagement)
        hype_signals = [
            s for s in signals
            if abs(s.sentiment_score) > 0.6 and s.influence_score > 0.5
        ]
        hype_level = min(len(hype_signals) / max(len(signals), 1), 1.0)
        
        # Calculate Fear & Greed Index (inverted from traditional)
        # 0 = Extreme Fear, 1 = Extreme Greed
        fear_greed_index = (overall_sentiment + 1) / 2  # Convert [-1,1] to [0,1]
        
        # Generate market narrative
        if overall_sentiment > 0.4:
            if hype_level > 0.6:
                market_narrative = "Extreme bullish sentiment with high hype levels"
            else:
                market_narrative = "Positive market sentiment with steady optimism"
        elif overall_sentiment < -0.4:
            if hype_level > 0.4:
                market_narrative = "Bearish sentiment with panic signals"
            else:
                market_narrative = "Negative market sentiment with caution"
        else:
            if hype_level > 0.5:
                market_narrative = "Neutral sentiment with elevated excitement"
            else:
                market_narrative = "Balanced market sentiment with low volatility"
        
        # Get top trending tokens
        trending_tokens = dict(sorted(
            token_profiles.items(),
            key=lambda x: x[1].trending_score * (1 + abs(x[1].overall_sentiment)),
            reverse=True
        )[:10])
        
        return MarketSentimentSummary(
            overall_sentiment=overall_sentiment,
            confidence=overall_confidence,
            platform_breakdown=platform_breakdown,
            trending_tokens=trending_tokens,
            sentiment_momentum=sentiment_momentum,
            hype_level=hype_level,
            fear_greed_index=fear_greed_index,
            market_narrative=market_narrative,
            last_updated=datetime.now()
        )
    
    async def run_aggregation(self, 
                            time_window: timedelta = None) -> MarketSentimentSummary:
        """
        Run complete social sentiment aggregation
        
        Args:
            time_window: Time window for analysis
            
        Returns:
            Market sentiment summary
        """
        self.logger.info("Running social sentiment aggregation...")
        
        # Collect signals from all platforms
        signals = await self.collect_social_signals(time_window)
        
        # Extract all mentioned tokens
        all_tokens = set()
        for signal in signals:
            all_tokens.update(signal.tokens_mentioned)
        
        # Calculate token profiles
        token_profiles = {}
        for token in all_tokens:
            if token and len(token) >= 2:  # Valid token symbols
                profile = self.calculate_token_sentiment_profile(token, signals, time_window)
                if profile.total_mentions >= self.SIGNAL_THRESHOLDS['min_mentions']:
                    token_profiles[token] = profile
        
        # Calculate market summary
        market_summary = self.calculate_market_sentiment_summary(signals, token_profiles)
        
        # Update state
        self.state['social_signals'] = [signal.to_dict() for signal in signals[-1000:]]  # Keep last 1000
        self.state['token_profiles'] = {k: v.to_dict() for k, v in token_profiles.items()}
        self.state['market_history'].append(market_summary.to_dict())
        self.state['market_history'] = self.state['market_history'][-100:]  # Keep last 100
        self.state['last_aggregation'] = datetime.now()
        
        self._save_state()
        
        self.logger.info(f"Aggregation complete: {market_summary.overall_sentiment:.3f} sentiment across {len(signals)} signals")
        
        return market_summary
    
    async def start_continuous_aggregation(self, 
                                         callback=None,
                                         interval_minutes: int = 30):
        """
        Start continuous social sentiment aggregation
        
        Args:
            callback: Function to call with results
            interval_minutes: Aggregation interval
        """
        self.logger.info("Starting continuous social aggregation...")
        
        while True:
            try:
                market_summary = await self.run_aggregation()
                
                if callback:
                    await callback(market_summary)
                
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in aggregation loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def get_aggregation_stats(self) -> Dict:
        """Get aggregation statistics"""
        return {
            'total_signals': len(self.state.get('social_signals', [])),
            'tracked_tokens': len(self.state.get('token_profiles', {})),
            'market_history_length': len(self.state.get('market_history', [])),
            'last_aggregation': self.state['last_aggregation'].isoformat(),
            'platform_stats': self.state.get('platform_stats', {}),
            'top_tokens': list(self.state.get('token_profiles', {}).keys())[:10]
        }
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert datetime objects to strings for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['last_aggregation'] = self.state['last_aggregation'].isoformat()
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_social_aggregator():
    """Test the social aggregation system"""
    
    # Initialize aggregator (monitors would be None for testing)
    aggregator = SocialAggregator()
    
    print("Testing Social Aggregator...")
    
    # Create mock signals for testing
    mock_signals = [
        SocialSignal(
            timestamp=datetime.now() - timedelta(minutes=30),
            platform='twitter',
            content='$SOL is breaking out! #Solana #bullish',
            sentiment_score=0.8,
            confidence=0.9,
            influence_score=0.7,
            engagement_metrics={'like_count': 150, 'retweet_count': 45},
            tokens_mentioned=['SOL'],
            source_id='twitter_123',
            source_user='crypto_trader'
        ),
        SocialSignal(
            timestamp=datetime.now() - timedelta(minutes=15),
            platform='reddit',
            content='Just bought more SOL, fundamentals are strong',
            sentiment_score=0.6,
            confidence=0.8,
            influence_score=0.4,
            engagement_metrics={'score': 25, 'num_comments': 8},
            tokens_mentioned=['SOL'],
            source_id='reddit_456',
            source_user='hodler123'
        )
    ]
    
    # Calculate token profile
    sol_profile = aggregator.calculate_token_sentiment_profile('SOL', mock_signals)
    print(f"\nSOL Sentiment Profile:")
    print(f"  Overall Sentiment: {sol_profile.overall_sentiment:.3f}")
    print(f"  Confidence: {sol_profile.confidence:.3f}")
    print(f"  Total Mentions: {sol_profile.total_mentions}")
    print(f"  Platform Sentiments: {sol_profile.platform_sentiments}")
    
    # Calculate market summary
    token_profiles = {'SOL': sol_profile}
    market_summary = aggregator.calculate_market_sentiment_summary(mock_signals, token_profiles)
    
    print(f"\nMarket Summary:")
    print(f"  Overall Sentiment: {market_summary.overall_sentiment:.3f}")
    print(f"  Confidence: {market_summary.confidence:.3f}")
    print(f"  Hype Level: {market_summary.hype_level:.3f}")
    print(f"  Market Narrative: {market_summary.market_narrative}")
    print(f"  Platform Breakdown: {market_summary.platform_breakdown}")
    
    # Show stats
    stats = aggregator.get_aggregation_stats()
    print(f"\nAggregation Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nSocial Aggregator testing complete!")


if __name__ == "__main__":
    asyncio.run(test_social_aggregator())