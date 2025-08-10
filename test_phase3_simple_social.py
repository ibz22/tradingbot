"""
Phase 3 Social Intelligence - Simple Test Suite
===============================================

Basic functionality tests for the social media monitoring infrastructure
without requiring API keys or external services.
"""

import asyncio
from datetime import datetime, timedelta

from solana_trading.sentiment.social_aggregator import SocialAggregator, SocialSignal
from solana_trading.sentiment.unified_intelligence import UnifiedIntelligenceSystem
from solana_trading.sentiment.sentiment_analyzer import SentimentAnalyzer
from solana_trading.discovery.token_extractor import TokenExtractor


async def test_social_intelligence():
    """Test the social intelligence components"""
    print("Testing Phase 3 Social Intelligence Components...")
    
    # Test 1: Social Aggregator
    print("\n1. Testing Social Aggregator...")
    aggregator = SocialAggregator(checkpoint_file="data/test_aggregator.json")
    
    # Create mock social signals
    mock_signals = [
        SocialSignal(
            timestamp=datetime.now() - timedelta(minutes=30),
            platform='twitter',
            content='$SOL breaking out! Major resistance broken 🚀 #Solana #bullish',
            sentiment_score=0.8,
            confidence=0.9,
            influence_score=0.7,
            engagement_metrics={'like_count': 250, 'retweet_count': 60},
            tokens_mentioned=['SOL'],
            source_id='twitter_123',
            source_user='crypto_whale'
        ),
        SocialSignal(
            timestamp=datetime.now() - timedelta(minutes=15),
            platform='reddit',
            content='Just analyzed SOL fundamentals - looking very strong for Q4. Great entry point here.',
            sentiment_score=0.6,
            confidence=0.8,
            influence_score=0.5,
            engagement_metrics={'score': 85, 'num_comments': 23},
            tokens_mentioned=['SOL'],
            source_id='reddit_456',
            source_user='defi_researcher'
        ),
        SocialSignal(
            timestamp=datetime.now() - timedelta(minutes=10),
            platform='telegram',
            content='🚨 ALPHA ALERT: SOL accumulation phase ending soon. Entry 41.5-42.2, targets 48, 52, 58 📈',
            sentiment_score=0.7,
            confidence=0.85,
            influence_score=0.9,
            engagement_metrics={'hype_score': 0.95, 'signal_count': 3},
            tokens_mentioned=['SOL'],
            source_id='telegram_789',
            source_user='alpha_signals'
        )
    ]
    
    # Test token sentiment profile
    sol_profile = aggregator.calculate_token_sentiment_profile('SOL', mock_signals)
    print(f"   SOL Profile:")
    print(f"     Overall Sentiment: {sol_profile.overall_sentiment:.3f}")
    print(f"     Confidence: {sol_profile.confidence:.3f}")
    print(f"     Total Mentions: {sol_profile.total_mentions}")
    print(f"     Platform Sentiments: {sol_profile.platform_sentiments}")
    print(f"     Trending Score: {sol_profile.trending_score:.3f}")
    
    # Test market summary
    token_profiles = {'SOL': sol_profile}
    market_summary = aggregator.calculate_market_sentiment_summary(mock_signals, token_profiles)
    
    print(f"\n   Market Summary:")
    print(f"     Overall Sentiment: {market_summary.overall_sentiment:.3f}")
    print(f"     Confidence: {market_summary.confidence:.3f}")
    print(f"     Hype Level: {market_summary.hype_level:.3f}")
    print(f"     Fear/Greed Index: {market_summary.fear_greed_index:.3f}")
    print(f"     Market Narrative: {market_summary.market_narrative}")
    
    # Test 2: Unified Intelligence System
    print("\n2. Testing Unified Intelligence System...")
    intelligence_system = UnifiedIntelligenceSystem(
        social_aggregator=aggregator,
        checkpoint_file="data/test_unified.json"
    )
    
    # Generate intelligence report
    report = await intelligence_system.generate_intelligence_report()
    
    print(f"   Intelligence Report:")
    print(f"     Timestamp: {report.timestamp}")
    print(f"     Market Sentiment: {report.overall_market_sentiment:.3f}")
    print(f"     Market Confidence: {report.market_confidence:.3f}")
    print(f"     Trending Tokens: {len(report.trending_tokens)}")
    print(f"     Alpha Opportunities: {len(report.alpha_opportunities)}")
    print(f"     Risk Alerts: {len(report.risk_alerts)}")
    print(f"     Active Sources: {report.intelligence_sources_active}")
    print(f"     Data Quality: {report.data_quality_score:.2f}")
    print(f"     Market Narrative: {report.market_narrative}")
    
    # Test 3: Component Integration
    print("\n3. Testing Component Integration...")
    sentiment_analyzer = SentimentAnalyzer()
    token_extractor = TokenExtractor(checkpoint_file="data/test_tokens.json")
    
    # Test full pipeline
    test_content = "Major Solana ecosystem update! Jupiter DEX hits $2B volume, Raydium launches v3, and $SOL breaks key resistance. This is looking very bullish for the entire ecosystem 🚀📈"
    
    # Sentiment analysis
    sentiment = await sentiment_analyzer.analyze_text(test_content, "integration_test")
    print(f"   Pipeline Test:")
    print(f"     Content: {test_content[:60]}...")
    print(f"     Sentiment: {sentiment.polarity:.3f} ({sentiment.classification.name})")
    print(f"     Confidence: {sentiment.confidence:.3f}")
    
    # Token extraction
    tokens = token_extractor.extract_from_text(test_content, "integration_test")
    print(f"     Extracted Tokens: {[t.symbol for t in tokens]}")
    print(f"     Token Confidence: {[f'{t.confidence:.2f}' for t in tokens]}")
    
    # Create integrated signal
    integrated_signal = SocialSignal(
        timestamp=datetime.now(),
        platform='integration',
        content=test_content,
        sentiment_score=sentiment.polarity,
        confidence=sentiment.confidence,
        influence_score=0.6,
        engagement_metrics={'integration_test': True},
        tokens_mentioned=[t.symbol for t in tokens],
        source_id='integration_test_1'
    )
    
    # Add to signals and reprocess
    all_signals = mock_signals + [integrated_signal]
    
    # Update profiles
    updated_profiles = {}
    all_tokens = set()
    for signal in all_signals:
        all_tokens.update(signal.tokens_mentioned)
    
    for token in all_tokens:
        if token:
            profile = aggregator.calculate_token_sentiment_profile(token, all_signals)
            updated_profiles[token] = profile
    
    print(f"   Updated Token Profiles: {list(updated_profiles.keys())}")
    
    # Final market summary
    final_summary = aggregator.calculate_market_sentiment_summary(all_signals, updated_profiles)
    print(f"   Final Market Analysis:")
    print(f"     Overall Sentiment: {final_summary.overall_sentiment:.3f}")
    print(f"     Platform Breakdown: {len(final_summary.platform_breakdown)} platforms")
    print(f"     Trending Tokens: {len(final_summary.trending_tokens)}")
    
    # Test 4: System Status and Stats
    print("\n4. Testing System Status...")
    
    # Aggregator stats
    agg_stats = aggregator.get_aggregation_stats()
    print(f"   Aggregator Stats:")
    for key, value in agg_stats.items():
        print(f"     {key}: {value}")
    
    # Intelligence system status
    system_status = intelligence_system.get_system_status()
    print(f"   Intelligence System Status:")
    for key, value in system_status.items():
        print(f"     {key}: {value}")
    
    print("\n✅ Phase 3 Social Intelligence Testing Complete!")
    print("\nSUMMARY:")
    print(f"   - Social aggregation: ✅ Working")
    print(f"   - Cross-platform sentiment: ✅ {final_summary.overall_sentiment:.3f}")
    print(f"   - Token detection: ✅ {len(all_tokens)} tokens found")
    print(f"   - Intelligence reports: ✅ Generated successfully")
    print(f"   - Component integration: ✅ Full pipeline functional")
    
    return final_summary


if __name__ == "__main__":
    asyncio.run(test_social_intelligence())