"""
Twitter/X Monitor - Real-time Social Intelligence for Solana Trading Bot
=======================================================================

Advanced Twitter monitoring system using Twitter API v2 for:
- Real-time tweet sentiment analysis for Solana mentions
- Influencer tracking and impact scoring
- Hashtag trending analysis and momentum detection
- Rate limiting and comprehensive error handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
import json
import re
import time

import tweepy
from tweepy.asynchronous import AsyncClient
import requests

from .sentiment_analyzer import SentimentAnalyzer, SentimentScore
from ..utils.checkpoint import load_checkpoint, save_checkpoint


@dataclass
class Tweet:
    """Represents a tweet with metadata"""
    id: str
    text: str
    author_id: str
    author_username: str
    author_name: str
    created_at: datetime
    public_metrics: Dict[str, int]  # likes, retweets, replies, quotes
    referenced_tweets: List[Dict] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    urls: List[str] = None
    sentiment_score: float = 0.0
    confidence: float = 0.0
    tokens_mentioned: List[str] = None
    influence_score: float = 0.0
    
    def __post_init__(self):
        if self.referenced_tweets is None:
            self.referenced_tweets = []
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if self.urls is None:
            self.urls = []
        if self.tokens_mentioned is None:
            self.tokens_mentioned = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tweet':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class Influencer:
    """Represents a crypto influencer with metrics"""
    user_id: str
    username: str
    name: str
    follower_count: int
    following_count: int
    tweet_count: int
    verified: bool
    description: str
    influence_score: float = 0.0
    engagement_rate: float = 0.0
    crypto_focus_score: float = 0.0
    recent_tweets: List[str] = None
    
    def __post_init__(self):
        if self.recent_tweets is None:
            self.recent_tweets = []


class TwitterMonitor:
    """
    Advanced Twitter monitoring system for crypto social intelligence
    """
    
    # Solana and crypto search terms
    SEARCH_TERMS = {
        'solana_primary': [
            'Solana', 'SOL', '$SOL', '#Solana', '#SOL',
            'Jupiter', 'Raydium', 'Orca', 'Serum', 'Phantom'
        ],
        'solana_ecosystem': [
            'Magic Eden', 'Step Finance', 'Marinade', 'Lido Solana',
            'Mango Markets', 'Drift Protocol', 'Kamino'
        ],
        'defi_general': [
            'DeFi', 'DEX', 'yield farming', 'liquidity mining',
            'staking', 'AMM', 'protocol'
        ],
        'crypto_signals': [
            'bull run', 'bear market', 'pump', 'dump', 'breakout',
            'ATH', 'ATL', 'HODL', 'diamond hands'
        ]
    }
    
    # Known crypto influencers (Twitter usernames)
    CRYPTO_INFLUENCERS = {
        'tier_1': [  # Major influencers
            'elonmusk', 'saylor', 'VitalikButerin', 'cz_binance',
            'aantonop', 'APompliano', 'RyanSAdams'
        ],
        'tier_2': [  # Crypto-focused
            'DeFiPulse', 'DeFiTvl', 'messaricrypto', 'TheCryptoLark',
            'coin_bureau', 'CryptoWendyO', 'BigCheds'
        ],
        'solana_focused': [  # Solana ecosystem
            'steppenwolf_cz', 'toly_solana', 'RajGokal', 'aeyakovenko',
            'SolanaConf', 'SolanaLabs', 'SolanaCompass'
        ]
    }
    
    # Rate limiting configuration
    RATE_LIMITS = {
        'search_tweets': {'requests': 300, 'window': 900},  # 300 requests per 15 min
        'user_tweets': {'requests': 300, 'window': 900},
        'user_lookup': {'requests': 300, 'window': 900}
    }
    
    def __init__(self, 
                 bearer_token: str,
                 sentiment_analyzer: Optional[SentimentAnalyzer] = None,
                 checkpoint_file: str = "data/twitter_monitor.json"):
        """
        Initialize Twitter Monitor
        
        Args:
            bearer_token: Twitter API v2 Bearer Token
            sentiment_analyzer: Sentiment analyzer instance
            checkpoint_file: File to store monitoring state
        """
        self.bearer_token = bearer_token
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Initialize Twitter client
        self.client = AsyncClient(bearer_token=bearer_token)
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'last_check': datetime.now() - timedelta(hours=1),
            'processed_tweet_ids': set(),
            'influencer_metrics': {},
            'hashtag_trends': {},
            'daily_api_calls': {},
            'last_reset_date': datetime.now().date(),
            'top_tweets': []
        })
        
        # Convert sets and dates back from JSON serialization
        if isinstance(self.state['processed_tweet_ids'], list):
            self.state['processed_tweet_ids'] = set(self.state['processed_tweet_ids'])
        if isinstance(self.state['last_check'], str):
            self.state['last_check'] = datetime.fromisoformat(self.state['last_check'])
        if isinstance(self.state['last_reset_date'], str):
            self.state['last_reset_date'] = datetime.fromisoformat(self.state['last_reset_date']).date()
        
        # Rate limiting tracking
        self.api_call_counts = {}
        self._reset_daily_counters()
    
    def _reset_daily_counters(self):
        """Reset daily API call counters if new day"""
        today = datetime.now().date()
        if self.state['last_reset_date'] < today:
            self.state['daily_api_calls'] = {}
            self.state['last_reset_date'] = today
            self.api_call_counts = {}
            self.logger.info("Reset daily API call counters")
    
    def _check_rate_limit(self, endpoint: str) -> bool:
        """
        Check if API call is within rate limits
        
        Args:
            endpoint: API endpoint to check
            
        Returns:
            True if within limits
        """
        if endpoint not in self.RATE_LIMITS:
            return True
        
        current_time = time.time()
        limits = self.RATE_LIMITS[endpoint]
        window_start = current_time - limits['window']
        
        # Initialize tracking for this endpoint
        if endpoint not in self.api_call_counts:
            self.api_call_counts[endpoint] = []
        
        # Remove old calls outside the window
        self.api_call_counts[endpoint] = [
            call_time for call_time in self.api_call_counts[endpoint]
            if call_time > window_start
        ]
        
        # Check if we can make another call
        return len(self.api_call_counts[endpoint]) < limits['requests']
    
    def _record_api_call(self, endpoint: str):
        """Record an API call for rate limiting"""
        current_time = time.time()
        if endpoint not in self.api_call_counts:
            self.api_call_counts[endpoint] = []
        self.api_call_counts[endpoint].append(current_time)
        
        # Update daily counters
        today_str = datetime.now().date().isoformat()
        if today_str not in self.state['daily_api_calls']:
            self.state['daily_api_calls'][today_str] = {}
        if endpoint not in self.state['daily_api_calls'][today_str]:
            self.state['daily_api_calls'][today_str][endpoint] = 0
        self.state['daily_api_calls'][today_str][endpoint] += 1
    
    def _build_search_query(self, terms: List[str], exclude_retweets: bool = True) -> str:
        """
        Build Twitter search query from terms
        
        Args:
            terms: Search terms
            exclude_retweets: Whether to exclude retweets
            
        Returns:
            Formatted search query
        """
        # Combine terms with OR
        query = ' OR '.join(f'"{term}"' if ' ' in term else term for term in terms)
        
        # Add filters
        filters = []
        if exclude_retweets:
            filters.append('-is:retweet')
        
        filters.extend([
            'lang:en',  # English only
            '-is:reply'  # Exclude replies
        ])
        
        if filters:
            query += ' ' + ' '.join(filters)
        
        return query
    
    async def _fetch_user_info(self, user_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch user information for given user IDs
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary of user info by user_id
        """
        if not self._check_rate_limit('user_lookup'):
            self.logger.warning("Rate limit reached for user lookup")
            await asyncio.sleep(60)  # Wait 1 minute
            return {}
        
        try:
            self._record_api_call('user_lookup')
            
            response = await self.client.get_users(
                ids=user_ids,
                user_fields=['public_metrics', 'description', 'verified', 'created_at']
            )
            
            users_info = {}
            if response.data:
                for user in response.data:
                    users_info[user.id] = {
                        'id': user.id,
                        'username': user.username,
                        'name': user.name,
                        'description': user.description or '',
                        'verified': getattr(user, 'verified', False),
                        'public_metrics': user.public_metrics,
                        'created_at': user.created_at
                    }
            
            return users_info
            
        except Exception as e:
            self.logger.error(f"Error fetching user info: {e}")
            return {}
    
    def _calculate_influence_score(self, user_metrics: Dict, tweet_metrics: Dict) -> float:
        """
        Calculate influence score for a user/tweet
        
        Args:
            user_metrics: User's public metrics
            tweet_metrics: Tweet's public metrics
            
        Returns:
            Influence score (0.0 to 1.0)
        """
        # Base score from follower count (normalized)
        follower_score = min(user_metrics.get('followers_count', 0) / 1000000, 1.0)
        
        # Engagement score from tweet metrics
        likes = tweet_metrics.get('like_count', 0)
        retweets = tweet_metrics.get('retweet_count', 0)
        replies = tweet_metrics.get('reply_count', 0)
        
        engagement_score = min((likes + retweets * 2 + replies) / 10000, 1.0)
        
        # Verification bonus
        verification_bonus = 0.1 if user_metrics.get('verified', False) else 0.0
        
        # Calculate weighted influence score
        influence_score = (
            follower_score * 0.4 +
            engagement_score * 0.5 +
            verification_bonus
        )
        
        return min(influence_score, 1.0)
    
    async def search_recent_tweets(self, 
                                 search_terms: List[str],
                                 max_results: int = 100,
                                 hours_back: int = 1) -> List[Tweet]:
        """
        Search for recent tweets matching terms
        
        Args:
            search_terms: Terms to search for
            max_results: Maximum tweets to return
            hours_back: How many hours back to search
            
        Returns:
            List of relevant tweets
        """
        if not self._check_rate_limit('search_tweets'):
            self.logger.warning("Rate limit reached for tweet search")
            return []
        
        try:
            self._record_api_call('search_tweets')
            
            query = self._build_search_query(search_terms)
            start_time = datetime.now() - timedelta(hours=hours_back)
            
            response = await self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit
                start_time=start_time,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'referenced_tweets'],
                expansions=['author_id', 'referenced_tweets.id'],
                user_fields=['username', 'name', 'public_metrics', 'verified', 'description']
            )
            
            tweets = []
            users_info = {}
            
            # Extract user information
            if hasattr(response, 'includes') and response.includes.get('users'):
                for user in response.includes['users']:
                    users_info[user.id] = {
                        'username': user.username,
                        'name': user.name,
                        'public_metrics': user.public_metrics,
                        'verified': getattr(user, 'verified', False),
                        'description': user.description or ''
                    }
            
            if response.data:
                for tweet_data in response.data:
                    # Skip if already processed
                    if tweet_data.id in self.state['processed_tweet_ids']:
                        continue
                    
                    user_info = users_info.get(tweet_data.author_id, {})
                    
                    # Extract hashtags and mentions
                    hashtags = re.findall(r'#(\w+)', tweet_data.text)
                    mentions = re.findall(r'@(\w+)', tweet_data.text)
                    urls = re.findall(r'https?://[^\s]+', tweet_data.text)
                    
                    # Calculate influence score
                    influence_score = self._calculate_influence_score(
                        user_info.get('public_metrics', {}),
                        tweet_data.public_metrics
                    )
                    
                    tweet = Tweet(
                        id=tweet_data.id,
                        text=tweet_data.text,
                        author_id=tweet_data.author_id,
                        author_username=user_info.get('username', ''),
                        author_name=user_info.get('name', ''),
                        created_at=tweet_data.created_at,
                        public_metrics=tweet_data.public_metrics,
                        referenced_tweets=getattr(tweet_data, 'referenced_tweets', []),
                        hashtags=hashtags,
                        mentions=mentions,
                        urls=urls,
                        influence_score=influence_score
                    )
                    
                    tweets.append(tweet)
                    self.state['processed_tweet_ids'].add(tweet_data.id)
            
            self.logger.info(f"Fetched {len(tweets)} new tweets for terms: {search_terms[:3]}")
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
            return []
    
    async def analyze_tweet_sentiment(self, tweets: List[Tweet]) -> List[Tweet]:
        """
        Analyze sentiment for a batch of tweets
        
        Args:
            tweets: List of tweets to analyze
            
        Returns:
            Tweets with updated sentiment scores
        """
        for tweet in tweets:
            try:
                # Use existing sentiment analyzer
                sentiment = await self.sentiment_analyzer.analyze_text(
                    tweet.text, context="social_media_tweet"
                )
                
                tweet.sentiment_score = sentiment.polarity
                tweet.confidence = sentiment.confidence
                tweet.tokens_mentioned = sentiment.keywords_detected
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze sentiment for tweet {tweet.id}: {e}")
                tweet.sentiment_score = 0.0
                tweet.confidence = 0.0
        
        return tweets
    
    async def track_influencer_activity(self, 
                                      usernames: List[str],
                                      max_tweets: int = 50) -> Dict[str, List[Tweet]]:
        """
        Track activity of specific crypto influencers
        
        Args:
            usernames: List of usernames to track
            max_tweets: Max tweets per user
            
        Returns:
            Dictionary of tweets by username
        """
        influencer_tweets = {}
        
        for username in usernames[:10]:  # Limit to prevent rate limiting
            if not self._check_rate_limit('user_tweets'):
                self.logger.warning(f"Rate limit reached for user tweets")
                break
            
            try:
                self._record_api_call('user_tweets')
                
                # Get user by username
                user_response = await self.client.get_user(
                    username=username,
                    user_fields=['public_metrics', 'verified', 'description']
                )
                
                if not user_response.data:
                    continue
                
                user = user_response.data
                
                # Get user's recent tweets
                tweets_response = await self.client.get_users_tweets(
                    id=user.id,
                    max_results=min(max_tweets, 100),
                    tweet_fields=['created_at', 'public_metrics'],
                    exclude=['retweets', 'replies']
                )
                
                tweets = []
                if tweets_response.data:
                    for tweet_data in tweets_response.data:
                        # Skip if already processed
                        if tweet_data.id in self.state['processed_tweet_ids']:
                            continue
                        
                        # Calculate influence score
                        influence_score = self._calculate_influence_score(
                            user.public_metrics,
                            tweet_data.public_metrics
                        )
                        
                        tweet = Tweet(
                            id=tweet_data.id,
                            text=tweet_data.text,
                            author_id=user.id,
                            author_username=user.username,
                            author_name=user.name,
                            created_at=tweet_data.created_at,
                            public_metrics=tweet_data.public_metrics,
                            hashtags=re.findall(r'#(\w+)', tweet_data.text),
                            mentions=re.findall(r'@(\w+)', tweet_data.text),
                            urls=re.findall(r'https?://[^\s]+', tweet_data.text),
                            influence_score=influence_score
                        )
                        
                        tweets.append(tweet)
                        self.state['processed_tweet_ids'].add(tweet_data.id)
                
                influencer_tweets[username] = tweets
                await asyncio.sleep(1)  # Rate limiting delay
                
            except Exception as e:
                self.logger.error(f"Error tracking influencer {username}: {e}")
                continue
        
        self.logger.info(f"Tracked {len(influencer_tweets)} influencers")
        return influencer_tweets
    
    def analyze_hashtag_trends(self, tweets: List[Tweet]) -> Dict[str, Dict]:
        """
        Analyze hashtag trends and momentum
        
        Args:
            tweets: List of tweets to analyze
            
        Returns:
            Hashtag trend analysis
        """
        hashtag_stats = {}
        
        for tweet in tweets:
            for hashtag in tweet.hashtags:
                hashtag_lower = hashtag.lower()
                
                if hashtag_lower not in hashtag_stats:
                    hashtag_stats[hashtag_lower] = {
                        'count': 0,
                        'total_engagement': 0,
                        'total_influence': 0.0,
                        'sentiment_scores': [],
                        'first_seen': tweet.created_at,
                        'last_seen': tweet.created_at
                    }
                
                stats = hashtag_stats[hashtag_lower]
                stats['count'] += 1
                stats['total_engagement'] += (
                    tweet.public_metrics.get('like_count', 0) +
                    tweet.public_metrics.get('retweet_count', 0)
                )
                stats['total_influence'] += tweet.influence_score
                stats['sentiment_scores'].append(tweet.sentiment_score)
                stats['last_seen'] = max(stats['last_seen'], tweet.created_at)
        
        # Calculate trend metrics
        trends = {}
        for hashtag, stats in hashtag_stats.items():
            if stats['count'] >= 3:  # Minimum threshold
                avg_sentiment = sum(stats['sentiment_scores']) / len(stats['sentiment_scores'])
                avg_engagement = stats['total_engagement'] / stats['count']
                avg_influence = stats['total_influence'] / stats['count']
                
                # Calculate momentum (recent activity weight)
                time_span = (stats['last_seen'] - stats['first_seen']).total_seconds()
                momentum = stats['count'] / max(time_span / 3600, 0.1)  # tweets per hour
                
                trends[hashtag] = {
                    'count': stats['count'],
                    'avg_sentiment': avg_sentiment,
                    'avg_engagement': avg_engagement,
                    'avg_influence': avg_influence,
                    'momentum': momentum,
                    'trend_score': momentum * avg_influence * (1 + abs(avg_sentiment))
                }
        
        # Sort by trend score
        return dict(sorted(trends.items(), key=lambda x: x[1]['trend_score'], reverse=True))
    
    async def get_trending_topics(self, hours_back: int = 2) -> Dict[str, float]:
        """
        Get currently trending crypto topics on Twitter
        
        Args:
            hours_back: Hours to look back for trends
            
        Returns:
            Dictionary of trending topics with scores
        """
        all_terms = []
        for category in self.SEARCH_TERMS.values():
            all_terms.extend(category)
        
        # Search for recent tweets
        tweets = await self.search_recent_tweets(
            all_terms[:20],  # Limit search terms
            max_results=300,
            hours_back=hours_back
        )
        
        # Analyze sentiment
        analyzed_tweets = await self.analyze_tweet_sentiment(tweets)
        
        # Get hashtag trends
        hashtag_trends = self.analyze_hashtag_trends(analyzed_tweets)
        
        # Update state
        self.state['hashtag_trends'] = hashtag_trends
        self.state['last_check'] = datetime.now()
        self._save_state()
        
        return hashtag_trends
    
    async def start_monitoring(self, 
                             callback=None,
                             check_interval_minutes: int = 30):
        """
        Start continuous Twitter monitoring
        
        Args:
            callback: Function to call with new data
            check_interval_minutes: How often to check
        """
        self.logger.info("Starting Twitter monitoring...")
        
        while True:
            try:
                # Get trending topics
                trends = await self.get_trending_topics()
                
                # Track influencers
                all_influencers = []
                for tier in self.CRYPTO_INFLUENCERS.values():
                    all_influencers.extend(tier)
                
                influencer_tweets = await self.track_influencer_activity(
                    all_influencers[:20],  # Limit to prevent rate limiting
                    max_tweets=10
                )
                
                if callback:
                    await callback({
                        'trends': trends,
                        'influencer_tweets': influencer_tweets,
                        'timestamp': datetime.now()
                    })
                
                # Wait before next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in Twitter monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics"""
        today_str = datetime.now().date().isoformat()
        today_calls = self.state['daily_api_calls'].get(today_str, {})
        
        return {
            'processed_tweets': len(self.state['processed_tweet_ids']),
            'tracked_hashtags': len(self.state['hashtag_trends']),
            'api_calls_today': sum(today_calls.values()),
            'api_breakdown': today_calls,
            'last_check': self.state['last_check'].isoformat(),
            'top_trends': list(self.state['hashtag_trends'].keys())[:10]
        }
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert sets to lists for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['processed_tweet_ids'] = list(self.state['processed_tweet_ids'])
        state_to_save['last_check'] = self.state['last_check'].isoformat()
        state_to_save['last_reset_date'] = self.state['last_reset_date'].isoformat()
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_twitter_monitor():
    """Test the Twitter monitoring system"""
    import os
    
    # You need to set your Twitter Bearer Token
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN', 'your_bearer_token_here')
    
    if bearer_token == 'your_bearer_token_here':
        print("Please set TWITTER_BEARER_TOKEN environment variable")
        return
    
    monitor = TwitterMonitor(bearer_token)
    
    print("Testing Twitter monitoring...")
    
    # Test trending topics
    trends = await monitor.get_trending_topics(hours_back=24)
    print(f"\nTop trending hashtags:")
    for hashtag, data in list(trends.items())[:5]:
        print(f"  #{hashtag}: {data['trend_score']:.2f} (sentiment: {data['avg_sentiment']:.2f})")
    
    # Test influencer tracking
    influencer_tweets = await monitor.track_influencer_activity(['SolanaLabs'], max_tweets=5)
    if influencer_tweets:
        for username, tweets in influencer_tweets.items():
            print(f"\n@{username} recent tweets: {len(tweets)}")
            for tweet in tweets[:2]:
                print(f"  - {tweet.text[:100]}...")
    
    # Show stats
    stats = monitor.get_monitoring_stats()
    print(f"\nMonitoring stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(test_twitter_monitor())