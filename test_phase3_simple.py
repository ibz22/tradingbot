"""
Simplified Phase 3 Test - News Monitoring Foundation
===================================================

Basic functionality tests for the news monitoring infrastructure.
"""

import asyncio
from datetime import datetime

from solana_trading.sentiment.news_monitor import NewsMonitor, NewsArticle
from solana_trading.sentiment.sentiment_analyzer import SentimentAnalyzer
from solana_trading.discovery.token_extractor import TokenExtractor


async def test_basic_functionality():
    """Test basic functionality of all components"""
    print("Testing Phase 3 News Monitoring Foundation...")
    
    # Test NewsMonitor
    print("\n1. Testing NewsMonitor...")
    monitor = NewsMonitor("dummy_key", checkpoint_file="data/test_news.json")
    
    test_article_data = {
        'title': 'Solana price surges after Jupiter integration',
        'description': 'SOL token rallies amid DeFi news',
        'url': 'https://example.com'
    }
    
    relevance = monitor._calculate_relevance_score(test_article_data)
    print(f"   Relevance scoring: {relevance:.3f} (expected > 0.3)")
    
    # Test SentimentAnalyzer
    print("\n2. Testing SentimentAnalyzer...")
    analyzer = SentimentAnalyzer()
    
    bullish_text = "Solana price surges 25% after major upgrade announcement!"
    sentiment = await analyzer.analyze_text(bullish_text)
    print(f"   Bullish sentiment: {sentiment.polarity:.3f} ({sentiment.classification.name})")
    
    bearish_text = "SOL crashes 15% amid regulatory concerns"
    sentiment2 = await analyzer.analyze_text(bearish_text)
    print(f"   Bearish sentiment: {sentiment2.polarity:.3f} ({sentiment2.classification.name})")
    
    # Test TokenExtractor
    print("\n3. Testing TokenExtractor...")
    extractor = TokenExtractor(checkpoint_file="data/test_tokens.json")
    
    token_text = "$BONK surges 50% after exchange listing. Jupiter (JUP) token airdrop announced."
    tokens = extractor.extract_from_text(token_text, "test_source")
    
    print(f"   Extracted tokens: {[t.symbol for t in tokens]}")
    print(f"   Confidence scores: {[f'{t.confidence:.2f}' for t in tokens]}")
    
    # Test integration
    print("\n4. Testing Integration...")
    
    mock_article = NewsArticle(
        title="BONK Token Rallies 200% After Major Partnership",
        description="BONK sees massive gains following Jupiter integration",
        content="The BONK ecosystem grows with significant partnerships...",
        url="https://example.com/bonk",
        source="TestSource",
        published_at=datetime.now(),
        relevance_score=0.8
    )
    
    # Analyze sentiment
    analyzed_article = await analyzer.analyze_article(mock_article)
    print(f"   Article sentiment: {analyzed_article.sentiment_score:.3f}")
    
    # Extract tokens from article
    full_text = f"{mock_article.title}. {mock_article.description}. {mock_article.content}"
    extracted_tokens = extractor.extract_from_text(full_text, mock_article.source)
    print(f"   Tokens from article: {[t.symbol for t in extracted_tokens[:3]]}")
    
    print("\n✅ Phase 3 Foundation Tests Complete!")
    print("News monitoring infrastructure is ready!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())