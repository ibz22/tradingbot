"""
Reddit Intelligence - Comprehensive Reddit Monitoring for Solana Trading Bot
===========================================================================

Advanced Reddit monitoring system using PRAW (Python Reddit API Wrapper) for:
- Multi-subreddit monitoring (r/solana, r/CryptoCurrency, r/SolanaNFTs)
- Comment sentiment analysis and upvote correlation
- Hot post detection and community sentiment scoring
- Token mention detection in discussions
- Influencer and community impact tracking
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
import json
import re
import time

import praw
from praw.models import Submission, Comment

from .sentiment_analyzer import SentimentAnalyzer, SentimentScore
from ..discovery.token_extractor import TokenExtractor
from ..utils.checkpoint import load_checkpoint, save_checkpoint


@dataclass
class RedditPost:
    """Represents a Reddit post with metadata"""
    id: str
    title: str
    text: str
    subreddit: str
    author: str
    created_utc: datetime
    score: int
    upvote_ratio: float
    num_comments: int
    url: str
    flair_text: Optional[str] = None
    awards_received: int = 0
    is_stickied: bool = False
    is_locked: bool = False
    sentiment_score: float = 0.0
    confidence: float = 0.0
    tokens_mentioned: List[str] = None
    engagement_score: float = 0.0
    
    def __post_init__(self):
        if self.tokens_mentioned is None:
            self.tokens_mentioned = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_utc'] = self.created_utc.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RedditPost':
        """Create from dictionary"""
        data['created_utc'] = datetime.fromisoformat(data['created_utc'])
        return cls(**data)


@dataclass
class RedditComment:
    """Represents a Reddit comment with metadata"""
    id: str
    body: str
    post_id: str
    subreddit: str
    author: str
    created_utc: datetime
    score: int
    is_root: bool
    parent_id: str
    sentiment_score: float = 0.0
    confidence: float = 0.0
    tokens_mentioned: List[str] = None
    
    def __post_init__(self):
        if self.tokens_mentioned is None:
            self.tokens_mentioned = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_utc'] = self.created_utc.isoformat()
        return data


class RedditMonitor:
    """
    Advanced Reddit monitoring system for crypto community intelligence
    """
    
    # Target subreddits for monitoring
    TARGET_SUBREDDITS = {
        'primary': [
            'solana', 'SolanaTrading', 'SolanaWallet', 'SolanaNFTs',
            'SolanaProjects', 'SolanaApes'
        ],
        'crypto_general': [
            'CryptoCurrency', 'crypto', 'defi', 'ethtrader',
            'Bitcoin', 'Ethereum', 'altcoin'
        ],
        'trading': [
            'CryptoCurrencyTrading', 'CryptoMoonShots', 'CryptoGemDiscovery',
            'satoshistreetbets', 'CryptoMars'
        ]
    }
    
    # Keywords for Solana ecosystem detection
    SOLANA_KEYWORDS = {
        'ecosystem': [
            'solana', 'sol', 'spl', 'jupiter', 'raydium', 'orca', 'serum',
            'phantom', 'solflare', 'step finance', 'marinade', 'lido'
        ],
        'defi': [
            'dex', 'amm', 'yield farming', 'liquidity pool', 'staking',
            'lending protocol', 'derivatives'
        ],
        'nft': [
            'magic eden', 'solanart', 'opensea solana', 'nft collection',
            'pfp', 'generative art'
        ]
    }
    
    # Sentiment indicators specific to Reddit
    REDDIT_SENTIMENT_INDICATORS = {
        'bullish': [
            'moon', 'diamond hands', 'hodl', 'bullish', 'pump', 'surge',
            'breakout', 'rally', 'gem', 'undervalued', 'buy the dip'
        ],
        'bearish': [
            'dump', 'crash', 'bearish', 'sell', 'overvalued', 'bubble',
            'rug pull', 'scam', 'dead coin', 'rekt'
        ],
        'hype': [
            'wen moon', 'lambo', 'to the moon', 'lfg', 'let\'s go',
            'hype train', 'fomo', 'next big thing'
        ]
    }
    
    def __init__(self,
                 client_id: str,
                 client_secret: str, 
                 user_agent: str,
                 sentiment_analyzer: Optional[SentimentAnalyzer] = None,
                 token_extractor: Optional[TokenExtractor] = None,
                 checkpoint_file: str = "data/reddit_monitor.json"):
        """
        Initialize Reddit Monitor
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string for API requests
            sentiment_analyzer: Sentiment analyzer instance
            token_extractor: Token extractor instance
            checkpoint_file: File to store monitoring state
        """
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.token_extractor = token_extractor or TokenExtractor()
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'last_check': datetime.now() - timedelta(hours=1),
            'processed_post_ids': set(),
            'processed_comment_ids': set(),
            'subreddit_stats': {},
            'trending_tokens': {},
            'community_sentiment': {},
            'top_posts_24h': []
        })
        
        # Convert sets and dates back from JSON serialization
        if isinstance(self.state['processed_post_ids'], list):
            self.state['processed_post_ids'] = set(self.state['processed_post_ids'])
        if isinstance(self.state['processed_comment_ids'], list):
            self.state['processed_comment_ids'] = set(self.state['processed_comment_ids'])
        if isinstance(self.state['last_check'], str):
            self.state['last_check'] = datetime.fromisoformat(self.state['last_check'])
    
    def _calculate_engagement_score(self, post: RedditPost) -> float:
        """
        Calculate engagement score for a Reddit post
        
        Args:
            post: Reddit post to score
            
        Returns:
            Engagement score (0.0 to 1.0)
        """
        # Base score from upvotes (logarithmic scale)
        import math
        upvote_score = min(math.log10(max(post.score, 1)) / 4, 1.0)
        
        # Comments engagement
        comment_score = min(post.num_comments / 100, 1.0)
        
        # Upvote ratio bonus
        ratio_bonus = max(0, (post.upvote_ratio - 0.5) * 2) * 0.2
        
        # Awards bonus
        awards_bonus = min(post.awards_received / 10, 0.2)
        
        # Calculate weighted engagement score
        engagement_score = (
            upvote_score * 0.4 +
            comment_score * 0.3 +
            ratio_bonus +
            awards_bonus
        )
        
        return min(engagement_score, 1.0)
    
    def _detect_reddit_sentiment_indicators(self, text: str) -> Dict[str, int]:
        """
        Detect Reddit-specific sentiment indicators
        
        Args:
            text: Text to analyze
            
        Returns:
            Count of sentiment indicators by type
        """
        text_lower = text.lower()
        indicators = {'bullish': 0, 'bearish': 0, 'hype': 0}
        
        for sentiment_type, keywords in self.REDDIT_SENTIMENT_INDICATORS.items():
            for keyword in keywords:
                indicators[sentiment_type] += text_lower.count(keyword)
        
        return indicators
    
    async def fetch_subreddit_posts(self,
                                   subreddit_name: str,
                                   sort_method: str = 'hot',
                                   limit: int = 100,
                                   time_filter: str = '24h') -> List[RedditPost]:
        """
        Fetch posts from a specific subreddit
        
        Args:
            subreddit_name: Name of subreddit
            sort_method: Sort method ('hot', 'new', 'top', 'rising')
            limit: Maximum posts to fetch
            time_filter: Time filter for 'top' sort
            
        Returns:
            List of Reddit posts
        """
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort method
            if sort_method == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_method == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_method == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_method == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)
            
            for submission in submissions:
                # Skip if already processed
                if submission.id in self.state['processed_post_ids']:
                    continue
                
                # Create post object
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    text=submission.selftext or '',
                    subreddit=subreddit_name,
                    author=str(submission.author) if submission.author else '[deleted]',
                    created_utc=datetime.fromtimestamp(submission.created_utc),
                    score=submission.score,
                    upvote_ratio=submission.upvote_ratio,
                    num_comments=submission.num_comments,
                    url=submission.url,
                    flair_text=submission.link_flair_text,
                    awards_received=submission.total_awards_received,
                    is_stickied=submission.stickied,
                    is_locked=submission.locked
                )
                
                # Calculate engagement score
                post.engagement_score = self._calculate_engagement_score(post)
                
                posts.append(post)
                self.state['processed_post_ids'].add(submission.id)
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            self.logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            self.logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
        
        return posts
    
    async def fetch_post_comments(self,
                                 post_id: str,
                                 max_comments: int = 50) -> List[RedditComment]:
        """
        Fetch comments from a specific post
        
        Args:
            post_id: Reddit post ID
            max_comments: Maximum comments to fetch
            
        Returns:
            List of Reddit comments
        """
        comments = []
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments"
            
            comment_count = 0
            for comment in submission.comments.list():
                if comment_count >= max_comments:
                    break
                
                # Skip if already processed or deleted
                if (comment.id in self.state['processed_comment_ids'] or
                    comment.body in ['[deleted]', '[removed]']):
                    continue
                
                reddit_comment = RedditComment(
                    id=comment.id,
                    body=comment.body,
                    post_id=post_id,
                    subreddit=str(comment.subreddit),
                    author=str(comment.author) if comment.author else '[deleted]',
                    created_utc=datetime.fromtimestamp(comment.created_utc),
                    score=comment.score,
                    is_root=comment.parent_id.startswith('t3_'),  # t3_ indicates post parent
                    parent_id=comment.parent_id
                )
                
                comments.append(reddit_comment)
                self.state['processed_comment_ids'].add(comment.id)
                comment_count += 1
                
                # Rate limiting
                await asyncio.sleep(0.05)
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id}: {e}")
        
        return comments
    
    async def analyze_post_sentiment(self, posts: List[RedditPost]) -> List[RedditPost]:
        """
        Analyze sentiment for Reddit posts
        
        Args:
            posts: List of posts to analyze
            
        Returns:
            Posts with updated sentiment scores
        """
        for post in posts:
            try:
                # Combine title and text for analysis
                full_text = f"{post.title}. {post.text}"
                
                # Analyze sentiment
                sentiment = await self.sentiment_analyzer.analyze_text(
                    full_text, context="reddit_post"
                )
                
                post.sentiment_score = sentiment.polarity
                post.confidence = sentiment.confidence
                
                # Extract tokens mentioned
                extracted_tokens = self.token_extractor.extract_from_text(
                    full_text, f"reddit_r_{post.subreddit}"
                )
                post.tokens_mentioned = [token.symbol for token in extracted_tokens[:5]]
                
                # Detect Reddit-specific sentiment indicators
                indicators = self._detect_reddit_sentiment_indicators(full_text)
                
                # Adjust sentiment based on Reddit indicators
                reddit_sentiment_adj = (
                    indicators['bullish'] * 0.1 -
                    indicators['bearish'] * 0.1 +
                    indicators['hype'] * 0.05
                )
                
                post.sentiment_score = max(min(
                    post.sentiment_score + reddit_sentiment_adj, 1.0
                ), -1.0)
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze sentiment for post {post.id}: {e}")
                post.sentiment_score = 0.0
                post.confidence = 0.0
        
        return posts
    
    async def analyze_comment_sentiment(self, comments: List[RedditComment]) -> List[RedditComment]:
        """
        Analyze sentiment for Reddit comments
        
        Args:
            comments: List of comments to analyze
            
        Returns:
            Comments with updated sentiment scores
        """
        for comment in comments:
            try:
                # Skip very short comments
                if len(comment.body) < 10:
                    continue
                
                # Analyze sentiment
                sentiment = await self.sentiment_analyzer.analyze_text(
                    comment.body, context="reddit_comment"
                )
                
                comment.sentiment_score = sentiment.polarity
                comment.confidence = sentiment.confidence
                
                # Extract tokens mentioned
                extracted_tokens = self.token_extractor.extract_from_text(
                    comment.body, f"reddit_r_{comment.subreddit}"
                )
                comment.tokens_mentioned = [token.symbol for token in extracted_tokens[:3]]
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze sentiment for comment {comment.id}: {e}")
                comment.sentiment_score = 0.0
                comment.confidence = 0.0
        
        return comments
    
    def calculate_subreddit_sentiment(self, 
                                    posts: List[RedditPost],
                                    comments: List[RedditComment]) -> Dict[str, float]:
        """
        Calculate overall sentiment for subreddit
        
        Args:
            posts: List of analyzed posts
            comments: List of analyzed comments
            
        Returns:
            Subreddit sentiment metrics
        """
        if not posts and not comments:
            return {'overall_sentiment': 0.0, 'confidence': 0.0}
        
        # Weight posts more heavily than comments
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        
        for post in posts:
            # Weight by engagement score
            weight = post.engagement_score * 2.0  # Posts weighted 2x
            total_weighted_sentiment += post.sentiment_score * weight
            total_weight += weight
        
        for comment in comments:
            # Weight by upvote score (normalized)
            weight = max(min(comment.score / 10, 1.0), 0.1)
            total_weighted_sentiment += comment.sentiment_score * weight
            total_weight += weight
        
        overall_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate confidence based on sample size and score consistency
        sample_size_factor = min(len(posts) + len(comments), 100) / 100
        
        all_scores = [p.sentiment_score for p in posts] + [c.sentiment_score for c in comments]
        score_variance = sum((score - overall_sentiment) ** 2 for score in all_scores) / len(all_scores) if all_scores else 1.0
        consistency_factor = max(0, 1 - score_variance)
        
        confidence = sample_size_factor * consistency_factor
        
        return {
            'overall_sentiment': overall_sentiment,
            'confidence': confidence,
            'post_count': len(posts),
            'comment_count': len(comments),
            'avg_post_engagement': sum(p.engagement_score for p in posts) / len(posts) if posts else 0.0
        }
    
    def extract_trending_tokens(self, posts: List[RedditPost], comments: List[RedditComment]) -> Dict[str, Dict]:
        """
        Extract trending tokens from Reddit discussions
        
        Args:
            posts: List of analyzed posts
            comments: List of analyzed comments
            
        Returns:
            Dictionary of trending tokens with metrics
        """
        token_stats = {}
        
        # Process posts
        for post in posts:
            for token in post.tokens_mentioned:
                if token not in token_stats:
                    token_stats[token] = {
                        'mentions': 0,
                        'total_sentiment': 0.0,
                        'total_engagement': 0.0,
                        'subreddits': set(),
                        'post_mentions': 0,
                        'comment_mentions': 0
                    }
                
                stats = token_stats[token]
                stats['mentions'] += 1
                stats['post_mentions'] += 1
                stats['total_sentiment'] += post.sentiment_score * post.confidence
                stats['total_engagement'] += post.engagement_score
                stats['subreddits'].add(post.subreddit)
        
        # Process comments
        for comment in comments:
            for token in comment.tokens_mentioned:
                if token not in token_stats:
                    token_stats[token] = {
                        'mentions': 0,
                        'total_sentiment': 0.0,
                        'total_engagement': 0.0,
                        'subreddits': set(),
                        'post_mentions': 0,
                        'comment_mentions': 0
                    }
                
                stats = token_stats[token]
                stats['mentions'] += 1
                stats['comment_mentions'] += 1
                stats['total_sentiment'] += comment.sentiment_score * comment.confidence
                stats['total_engagement'] += max(comment.score, 0) / 10  # Normalize comment score
                stats['subreddits'].add(comment.subreddit)
        
        # Calculate trending metrics
        trending_tokens = {}
        for token, stats in token_stats.items():
            if stats['mentions'] >= 3:  # Minimum threshold
                avg_sentiment = stats['total_sentiment'] / stats['mentions']
                avg_engagement = stats['total_engagement'] / stats['mentions']
                subreddit_diversity = len(stats['subreddits'])
                
                # Calculate trend score
                trend_score = (
                    stats['mentions'] * 0.3 +
                    avg_engagement * 0.4 +
                    abs(avg_sentiment) * 0.2 +
                    subreddit_diversity * 0.1
                )
                
                trending_tokens[token] = {
                    'mentions': stats['mentions'],
                    'avg_sentiment': avg_sentiment,
                    'avg_engagement': avg_engagement,
                    'subreddit_count': subreddit_diversity,
                    'post_mentions': stats['post_mentions'],
                    'comment_mentions': stats['comment_mentions'],
                    'trend_score': trend_score
                }
        
        # Sort by trend score
        return dict(sorted(trending_tokens.items(), key=lambda x: x[1]['trend_score'], reverse=True))
    
    async def monitor_subreddits(self, 
                               subreddit_names: List[str],
                               post_limit: int = 50) -> Dict[str, Dict]:
        """
        Monitor multiple subreddits for crypto discussions
        
        Args:
            subreddit_names: List of subreddit names
            post_limit: Posts to fetch per subreddit
            
        Returns:
            Monitoring results by subreddit
        """
        results = {}
        
        for subreddit_name in subreddit_names:
            try:
                self.logger.info(f"Monitoring r/{subreddit_name}...")
                
                # Fetch hot posts
                posts = await self.fetch_subreddit_posts(
                    subreddit_name, 'hot', post_limit
                )
                
                # Analyze post sentiment
                analyzed_posts = await self.analyze_post_sentiment(posts)
                
                # Fetch comments for top engaging posts
                all_comments = []
                top_posts = sorted(analyzed_posts, key=lambda x: x.engagement_score, reverse=True)[:10]
                
                for post in top_posts:
                    comments = await self.fetch_post_comments(post.id, max_comments=20)
                    analyzed_comments = await self.analyze_comment_sentiment(comments)
                    all_comments.extend(analyzed_comments)
                
                # Calculate subreddit sentiment
                subreddit_sentiment = self.calculate_subreddit_sentiment(analyzed_posts, all_comments)
                
                # Extract trending tokens
                trending_tokens = self.extract_trending_tokens(analyzed_posts, all_comments)
                
                results[subreddit_name] = {
                    'sentiment': subreddit_sentiment,
                    'trending_tokens': trending_tokens,
                    'posts_analyzed': len(analyzed_posts),
                    'comments_analyzed': len(all_comments),
                    'top_posts': [
                        {
                            'title': post.title,
                            'sentiment': post.sentiment_score,
                            'engagement': post.engagement_score,
                            'tokens': post.tokens_mentioned
                        }
                        for post in top_posts[:5]
                    ]
                }
                
                await asyncio.sleep(2)  # Rate limiting between subreddits
                
            except Exception as e:
                self.logger.error(f"Error monitoring r/{subreddit_name}: {e}")
                results[subreddit_name] = {
                    'error': str(e),
                    'sentiment': {'overall_sentiment': 0.0, 'confidence': 0.0},
                    'trending_tokens': {}
                }
        
        # Update state
        self.state['community_sentiment'] = results
        self.state['last_check'] = datetime.now()
        self._save_state()
        
        return results
    
    async def start_monitoring(self,
                             callback=None,
                             check_interval_minutes: int = 60):
        """
        Start continuous Reddit monitoring
        
        Args:
            callback: Function to call with new data
            check_interval_minutes: How often to check
        """
        self.logger.info("Starting Reddit monitoring...")
        
        while True:
            try:
                # Monitor primary Solana subreddits
                primary_results = await self.monitor_subreddits(
                    self.TARGET_SUBREDDITS['primary'][:3],  # Limit for rate limiting
                    post_limit=30
                )
                
                # Monitor general crypto subreddits
                crypto_results = await self.monitor_subreddits(
                    self.TARGET_SUBREDDITS['crypto_general'][:2],
                    post_limit=20
                )
                
                combined_results = {**primary_results, **crypto_results}
                
                if callback:
                    await callback({
                        'subreddit_results': combined_results,
                        'timestamp': datetime.now()
                    })
                
                # Wait before next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in Reddit monitoring loop: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    def get_monitoring_stats(self) -> Dict:
        """Get Reddit monitoring statistics"""
        return {
            'processed_posts': len(self.state['processed_post_ids']),
            'processed_comments': len(self.state['processed_comment_ids']),
            'monitored_subreddits': len(self.state['community_sentiment']),
            'trending_tokens_count': sum(
                len(data.get('trending_tokens', {})) 
                for data in self.state['community_sentiment'].values()
            ),
            'last_check': self.state['last_check'].isoformat(),
            'overall_sentiment': sum(
                data.get('sentiment', {}).get('overall_sentiment', 0) 
                for data in self.state['community_sentiment'].values()
            ) / max(len(self.state['community_sentiment']), 1)
        }
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert sets to lists for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['processed_post_ids'] = list(self.state['processed_post_ids'])
        state_to_save['processed_comment_ids'] = list(self.state['processed_comment_ids'])
        state_to_save['last_check'] = self.state['last_check'].isoformat()
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_reddit_monitor():
    """Test the Reddit monitoring system"""
    import os
    
    # You need to set your Reddit API credentials
    client_id = os.getenv('REDDIT_CLIENT_ID', 'your_client_id')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'SolanaBot/1.0 by YourUsername')
    
    if client_id == 'your_client_id':
        print("Please set Reddit API credentials in environment variables")
        return
    
    monitor = RedditMonitor(client_id, client_secret, user_agent)
    
    print("Testing Reddit monitoring...")
    
    # Test subreddit monitoring
    results = await monitor.monitor_subreddits(['solana', 'CryptoCurrency'], post_limit=10)
    
    for subreddit, data in results.items():
        print(f"\nr/{subreddit} Results:")
        sentiment = data.get('sentiment', {})
        print(f"  Overall Sentiment: {sentiment.get('overall_sentiment', 0):.3f}")
        print(f"  Posts Analyzed: {data.get('posts_analyzed', 0)}")
        print(f"  Comments Analyzed: {data.get('comments_analyzed', 0)}")
        
        trending = data.get('trending_tokens', {})
        if trending:
            print(f"  Top Trending Tokens: {list(trending.keys())[:3]}")
    
    # Show stats
    stats = monitor.get_monitoring_stats()
    print(f"\nMonitoring Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(test_reddit_monitor())