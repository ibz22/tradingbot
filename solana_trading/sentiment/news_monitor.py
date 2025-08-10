"""
News Monitor - NewsAPI Integration for Solana Trading Bot
========================================================

Real-time news monitoring with intelligent filtering for Solana and crypto markets.
Integrates with NewsAPI to fetch relevant articles and extract actionable insights.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import json

from newsapi import NewsApiClient
import requests
from bs4 import BeautifulSoup

from ..utils.checkpoint import load_checkpoint, save_checkpoint


@dataclass
class NewsArticle:
    """Represents a news article with metadata"""
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: datetime
    relevance_score: float = 0.0
    sentiment_score: float = 0.0
    tokens_mentioned: List[str] = None
    
    def __post_init__(self):
        if self.tokens_mentioned is None:
            self.tokens_mentioned = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['published_at'] = self.published_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsArticle':
        """Create from dictionary"""
        data['published_at'] = datetime.fromisoformat(data['published_at'])
        return cls(**data)


class NewsMonitor:
    """
    Real-time news monitoring system with intelligent filtering
    """
    
    # Solana and crypto keywords for relevance filtering
    CRYPTO_KEYWORDS = {
        'high_priority': {
            'solana', 'sol', 'spl', 'jupiter', 'raydium', 'orca', 'serum',
            'phantom', 'solflare', 'magic eden', 'step finance'
        },
        'crypto_general': {
            'cryptocurrency', 'crypto', 'blockchain', 'defi', 'nft',
            'decentralized', 'token', 'altcoin', 'trading', 'dex'
        },
        'market_signals': {
            'bull', 'bear', 'pump', 'dump', 'breakout', 'rally',
            'surge', 'crash', 'volatile', 'volume', 'liquidity'
        }
    }
    
    # News sources with reliability scores
    TRUSTED_SOURCES = {
        'coindesk.com': 0.9,
        'cointelegraph.com': 0.85,
        'decrypt.co': 0.8,
        'theblock.co': 0.9,
        'bloomberg.com': 0.95,
        'reuters.com': 0.95,
        'cnbc.com': 0.8,
        'forbes.com': 0.75
    }
    
    def __init__(self, api_key: str, checkpoint_file: str = "data/news_monitor.json"):
        """
        Initialize NewsMonitor
        
        Args:
            api_key: NewsAPI key
            checkpoint_file: File to store monitoring state
        """
        self.api_key = api_key
        self.checkpoint_file = checkpoint_file
        self.client = NewsApiClient(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'last_check': datetime.now() - timedelta(hours=1),
            'processed_urls': set(),
            'daily_article_count': 0,
            'last_reset_date': datetime.now().date()
        })
        
        # Convert sets back from lists (JSON serialization)
        if isinstance(self.state['processed_urls'], list):
            self.state['processed_urls'] = set(self.state['processed_urls'])
        
        # Convert datetime strings back to objects
        if isinstance(self.state['last_check'], str):
            self.state['last_check'] = datetime.fromisoformat(self.state['last_check'])
        if isinstance(self.state['last_reset_date'], str):
            self.state['last_reset_date'] = datetime.fromisoformat(self.state['last_reset_date']).date()
    
    def _reset_daily_counters(self):
        """Reset daily counters if new day"""
        today = datetime.now().date()
        if self.state['last_reset_date'] < today:
            self.state['daily_article_count'] = 0
            self.state['last_reset_date'] = today
            self.logger.info("Reset daily article counters")
    
    def _calculate_relevance_score(self, article_data: Dict) -> float:
        """
        Calculate relevance score based on content and source
        
        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0
        text_content = f"{article_data.get('title', '')} {article_data.get('description', '')}".lower()
        
        # High priority Solana keywords
        for keyword in self.CRYPTO_KEYWORDS['high_priority']:
            if keyword in text_content:
                score += 0.3
        
        # General crypto keywords
        for keyword in self.CRYPTO_KEYWORDS['crypto_general']:
            if keyword in text_content:
                score += 0.1
        
        # Market signal keywords
        for keyword in self.CRYPTO_KEYWORDS['market_signals']:
            if keyword in text_content:
                score += 0.05
        
        # Source reliability bonus
        source_url = article_data.get('url', '')
        for trusted_source, reliability in self.TRUSTED_SOURCES.items():
            if trusted_source in source_url:
                score += reliability * 0.2
                break
        
        return min(score, 1.0)
    
    def _fetch_full_content(self, url: str) -> str:
        """
        Fetch full article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Full article text content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find article content in common containers
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.story-body',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    break
            
            # Fallback to body text if no specific content found
            if not content:
                content = soup.get_text(strip=True)
            
            # Clean up content
            content = ' '.join(content.split())
            return content[:5000]  # Limit to 5000 characters
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch full content from {url}: {e}")
            return ""
    
    async def fetch_latest_news(self, 
                               hours_back: int = 1,
                               min_relevance: float = 0.3) -> List[NewsArticle]:
        """
        Fetch latest relevant news articles
        
        Args:
            hours_back: How many hours back to search
            min_relevance: Minimum relevance score to include
            
        Returns:
            List of relevant news articles
        """
        self._reset_daily_counters()
        
        # Check API rate limits (NewsAPI: 1000 requests/day for free tier)
        if self.state['daily_article_count'] >= 900:
            self.logger.warning("Approaching NewsAPI rate limit")
            return []
        
        try:
            # Calculate time window
            from_time = datetime.now() - timedelta(hours=hours_back)
            
            # Search for cryptocurrency and Solana news
            search_queries = [
                'Solana OR SOL OR Jupiter OR Raydium',
                'cryptocurrency trading OR crypto market OR DeFi',
                'blockchain OR token OR altcoin'
            ]
            
            all_articles = []
            
            for query in search_queries:
                try:
                    # Fetch articles from NewsAPI
                    response = self.client.get_everything(
                        q=query,
                        language='en',
                        sort_by='publishedAt',
                        from_param=from_time.strftime('%Y-%m-%d'),
                        page_size=20
                    )
                    
                    self.state['daily_article_count'] += 1
                    
                    if response['status'] == 'ok':
                        for article_data in response['articles']:
                            # Skip if already processed
                            if article_data['url'] in self.state['processed_urls']:
                                continue
                            
                            # Calculate relevance
                            relevance = self._calculate_relevance_score(article_data)
                            if relevance < min_relevance:
                                continue
                            
                            # Fetch full content
                            full_content = self._fetch_full_content(article_data['url'])
                            
                            # Create article object
                            article = NewsArticle(
                                title=article_data.get('title', ''),
                                description=article_data.get('description', ''),
                                content=full_content or article_data.get('content', ''),
                                url=article_data['url'],
                                source=article_data['source']['name'],
                                published_at=datetime.fromisoformat(
                                    article_data['publishedAt'].replace('Z', '+00:00')
                                ),
                                relevance_score=relevance
                            )
                            
                            all_articles.append(article)
                            self.state['processed_urls'].add(article_data['url'])
                    
                    # Rate limiting delay
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error fetching news for query '{query}': {e}")
                    continue
            
            # Sort by relevance and recency
            all_articles.sort(
                key=lambda x: (x.relevance_score, x.published_at), 
                reverse=True
            )
            
            # Update state
            self.state['last_check'] = datetime.now()
            self._save_state()
            
            self.logger.info(f"Fetched {len(all_articles)} relevant articles")
            return all_articles[:50]  # Return top 50 articles
            
        except Exception as e:
            self.logger.error(f"Error in fetch_latest_news: {e}")
            return []
    
    def get_trending_topics(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """
        Extract trending topics from articles
        
        Args:
            articles: List of articles to analyze
            
        Returns:
            Dictionary of topics and their frequency
        """
        topics = {}
        
        for article in articles:
            text = f"{article.title} {article.description}".lower()
            
            # Count keyword occurrences
            all_keywords = (
                self.CRYPTO_KEYWORDS['high_priority'] |
                self.CRYPTO_KEYWORDS['crypto_general'] |
                self.CRYPTO_KEYWORDS['market_signals']
            )
            
            for keyword in all_keywords:
                if keyword in text:
                    topics[keyword] = topics.get(keyword, 0) + 1
        
        # Sort by frequency
        return dict(sorted(topics.items(), key=lambda x: x[1], reverse=True))
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert sets to lists for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['processed_urls'] = list(self.state['processed_urls'])
        state_to_save['last_check'] = self.state['last_check'].isoformat()
        state_to_save['last_reset_date'] = self.state['last_reset_date'].isoformat()
        
        save_checkpoint(self.checkpoint_file, state_to_save)
    
    async def start_monitoring(self, 
                             callback=None,
                             check_interval_minutes: int = 15):
        """
        Start continuous news monitoring
        
        Args:
            callback: Function to call with new articles
            check_interval_minutes: How often to check for news
        """
        self.logger.info("Starting news monitoring...")
        
        while True:
            try:
                articles = await self.fetch_latest_news()
                
                if articles and callback:
                    await callback(articles)
                
                # Wait before next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def get_article_summary(self, article: NewsArticle) -> Dict:
        """
        Get a structured summary of an article
        
        Args:
            article: Article to summarize
            
        Returns:
            Dictionary with key information
        """
        return {
            'title': article.title,
            'source': article.source,
            'published': article.published_at.strftime('%Y-%m-%d %H:%M'),
            'relevance': round(article.relevance_score, 2),
            'sentiment': round(article.sentiment_score, 2),
            'url': article.url,
            'tokens': article.tokens_mentioned
        }


# Example usage and testing
async def test_news_monitor():
    """Test the news monitoring system"""
    import os
    
    # You need to set your NewsAPI key
    api_key = os.getenv('NEWSAPI_KEY', 'your_api_key_here')
    
    if api_key == 'your_api_key_here':
        print("Please set NEWSAPI_KEY environment variable")
        return
    
    monitor = NewsMonitor(api_key)
    
    print("Fetching latest Solana news...")
    articles = await monitor.fetch_latest_news(hours_back=24, min_relevance=0.2)
    
    print(f"\nFound {len(articles)} relevant articles:")
    for article in articles[:5]:  # Show top 5
        summary = monitor.get_article_summary(article)
        print(f"\n📰 {summary['title']}")
        print(f"   Source: {summary['source']} | Relevance: {summary['relevance']}")
        print(f"   Published: {summary['published']}")
        print(f"   URL: {summary['url'][:60]}...")
    
    # Show trending topics
    topics = monitor.get_trending_topics(articles)
    print(f"\n🔥 Trending topics:")
    for topic, count in list(topics.items())[:10]:
        print(f"   {topic}: {count} mentions")


if __name__ == "__main__":
    asyncio.run(test_news_monitor())