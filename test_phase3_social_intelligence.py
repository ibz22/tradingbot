"""
Phase 3 Social Intelligence Test Suite
=====================================

Comprehensive testing of the social media monitoring infrastructure:
- Twitter/X monitoring and influencer tracking
- Reddit intelligence and community sentiment  
- Telegram alpha signal detection
- Cross-platform sentiment aggregation
- Integration with news monitoring from Session 1
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict

from solana_trading.sentiment.twitter_monitor import TwitterMonitor, Tweet
from solana_trading.sentiment.reddit_monitor import RedditMonitor, RedditPost
from solana_trading.sentiment.telegram_monitor import TelegramMonitor, TelegramMessage
from solana_trading.sentiment.social_aggregator import SocialAggregator, SocialSignal
from solana_trading.sentiment.sentiment_analyzer import SentimentAnalyzer
from solana_trading.discovery.token_extractor import TokenExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3SocialTestSuite:
    """Comprehensive test suite for Phase 3 social intelligence"""
    
    def __init__(self):
        """Initialize test suite"""
        self.results = {
            'twitter_monitor': {'passed': 0, 'failed': 0, 'errors': []},
            'reddit_monitor': {'passed': 0, 'failed': 0, 'errors': []},
            'telegram_monitor': {'passed': 0, 'failed': 0, 'errors': []},
            'social_aggregator': {'passed': 0, 'failed': 0, 'errors': []},
            'integration': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def _log_result(self, component: str, test_name: str, passed: bool, error: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        logger.info(f"{status} - {component}: {test_name}")
        
        if passed:
            self.results[component]['passed'] += 1
        else:
            self.results[component]['failed'] += 1
            if error:
                self.results[component]['errors'].append(f"{test_name}: {error}")
                logger.error(f"Error in {test_name}: {error}")
    
    async def test_twitter_monitor(self):
        """Test Twitter monitoring functionality"""
        logger.info("\nTesting Twitter Monitor...")
        
        # Test 1: Initialize TwitterMonitor
        try:
            # Use dummy token for testing
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN', 'dummy_token_for_testing')
            monitor = TwitterMonitor(bearer_token, checkpoint_file="test_data/twitter_test.json")
            self._log_result('twitter_monitor', 'Initialize TwitterMonitor', True)
        except Exception as e:
            self._log_result('twitter_monitor', 'Initialize TwitterMonitor', False, str(e))
            return
        
        # Test 2: Test influence score calculation
        try:
            user_metrics = {'followers_count': 10000, 'verified': True}
            tweet_metrics = {'like_count': 100, 'retweet_count': 25, 'reply_count': 15}
            
            influence_score = monitor._calculate_influence_score(user_metrics, tweet_metrics)
            passed = 0.0 <= influence_score <= 1.0
            self._log_result('twitter_monitor', 'Influence score calculation', passed,
                           f"Score: {influence_score}" if not passed else "")
        except Exception as e:
            self._log_result('twitter_monitor', 'Influence score calculation', False, str(e))
        
        # Test 3: Test search query building
        try:
            terms = ['Solana', 'SOL', 'Jupiter']
            query = monitor._build_search_query(terms)
            passed = all(term in query for term in terms) and '-is:retweet' in query
            self._log_result('twitter_monitor', 'Search query building', passed,
                           f"Query: {query}" if not passed else "")
        except Exception as e:
            self._log_result('twitter_monitor', 'Search query building', False, str(e))
        
        # Test 4: Test hashtag trend analysis
        try:
            # Create mock tweets
            mock_tweets = [
                Tweet(
                    id="1", text="#Solana breaking out! #bullish #moon",
                    author_id="123", author_username="trader1", author_name="Trader",
                    created_at=datetime.now(), public_metrics={'like_count': 50, 'retweet_count': 10},
                    hashtags=['Solana', 'bullish', 'moon'], sentiment_score=0.8, influence_score=0.6
                ),
                Tweet(
                    id="2", text="$SOL looking strong #Solana #crypto",
                    author_id="124", author_username="trader2", author_name="Trader2",
                    created_at=datetime.now(), public_metrics={'like_count': 30, 'retweet_count': 5},
                    hashtags=['Solana', 'crypto'], sentiment_score=0.6, influence_score=0.4
                )
            ]
            
            trends = monitor.analyze_hashtag_trends(mock_tweets)
            passed = 'solana' in trends and trends['solana']['count'] >= 2
            self._log_result('twitter_monitor', 'Hashtag trend analysis', passed,
                           f"Trends: {list(trends.keys())}" if not passed else "")
        except Exception as e:
            self._log_result('twitter_monitor', 'Hashtag trend analysis', False, str(e))
        
        # Test 5: Test monitoring stats
        try:
            stats = monitor.get_monitoring_stats()
            required_keys = ['processed_tweets', 'tracked_hashtags', 'api_calls_today', 'last_check']
            passed = all(key in stats for key in required_keys)
            self._log_result('twitter_monitor', 'Monitoring stats generation', passed,
                           f"Missing keys: {[k for k in required_keys if k not in stats]}" if not passed else "")
        except Exception as e:
            self._log_result('twitter_monitor', 'Monitoring stats generation', False, str(e))
    
    async def test_reddit_monitor(self):
        """Test Reddit monitoring functionality"""
        logger.info("\nTesting Reddit Monitor...")
        
        # Test 1: Initialize RedditMonitor  
        try:
            # Use dummy credentials for testing
            client_id = os.getenv('REDDIT_CLIENT_ID', 'dummy_id')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET', 'dummy_secret')
            user_agent = 'SolanaBot/1.0 Test'
            
            monitor = RedditMonitor(client_id, client_secret, user_agent, 
                                  checkpoint_file="test_data/reddit_test.json")
            self._log_result('reddit_monitor', 'Initialize RedditMonitor', True)
        except Exception as e:
            self._log_result('reddit_monitor', 'Initialize RedditMonitor', False, str(e))
            return
        
        # Test 2: Test engagement score calculation
        try:
            mock_post = RedditPost(
                id="abc123", title="Solana ecosystem update", text="Great progress on Jupiter DEX",
                subreddit="solana", author="solana_fan", created_utc=datetime.now(),
                score=150, upvote_ratio=0.9, num_comments=25, url="https://reddit.com/test",
                awards_received=2
            )
            
            engagement_score = monitor._calculate_engagement_score(mock_post)
            passed = 0.0 <= engagement_score <= 1.0
            self._log_result('reddit_monitor', 'Engagement score calculation', passed,
                           f"Score: {engagement_score}" if not passed else "")
        except Exception as e:
            self._log_result('reddit_monitor', 'Engagement score calculation', False, str(e))
        
        # Test 3: Test Reddit sentiment indicators
        try:
            test_text = "SOL to the moon! Diamond hands, this is going to pump hard!"
            indicators = monitor._detect_reddit_sentiment_indicators(test_text)
            
            passed = (indicators['bullish'] > 0 and indicators['hype'] > 0 and
                     sum(indicators.values()) > 2)
            self._log_result('reddit_monitor', 'Reddit sentiment indicators', passed,
                           f"Indicators: {indicators}" if not passed else "")
        except Exception as e:
            self._log_result('reddit_monitor', 'Reddit sentiment indicators', False, str(e))
        
        # Test 4: Test subreddit sentiment calculation
        try:
            mock_posts = [
                RedditPost("1", "Bullish on SOL", "Great fundamentals", "solana", "user1",
                          datetime.now(), 100, 0.8, 10, "url1", engagement_score=0.7, sentiment_score=0.6),
                RedditPost("2", "SOL bearish", "Concerns about adoption", "solana", "user2", 
                          datetime.now(), 50, 0.6, 5, "url2", engagement_score=0.3, sentiment_score=-0.4)
            ]
            mock_comments = []
            
            sentiment = monitor.calculate_subreddit_sentiment(mock_posts, mock_comments)
            passed = -1.0 <= sentiment['overall_sentiment'] <= 1.0 and 'confidence' in sentiment
            self._log_result('reddit_monitor', 'Subreddit sentiment calculation', passed,
                           f"Sentiment: {sentiment}" if not passed else "")
        except Exception as e:
            self._log_result('reddit_monitor', 'Subreddit sentiment calculation', False, str(e))
        
        # Test 5: Test trending token extraction
        try:
            mock_posts[0].tokens_mentioned = ['SOL', 'BONK']
            mock_posts[1].tokens_mentioned = ['SOL']
            
            trending = monitor.extract_trending_tokens(mock_posts, [])
            passed = 'SOL' in trending and trending['SOL']['mentions'] >= 2
            self._log_result('reddit_monitor', 'Trending token extraction', passed,
                           f"Trending: {list(trending.keys())}" if not passed else "")
        except Exception as e:
            self._log_result('reddit_monitor', 'Trending token extraction', False, str(e))
    
    async def test_telegram_monitor(self):
        """Test Telegram monitoring functionality"""
        logger.info("\nTesting Telegram Monitor...")
        
        # Test 1: Initialize TelegramMonitor
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token')
            monitor = TelegramMonitor(bot_token, checkpoint_file="test_data/telegram_test.json")
            self._log_result('telegram_monitor', 'Initialize TelegramMonitor', True)
        except Exception as e:
            self._log_result('telegram_monitor', 'Initialize TelegramMonitor', False, str(e))
            return
        
        # Test 2: Test hype score calculation
        try:
            hype_text = "SOL MOON SHOT!!! 🚀🚀🚀 This is going PARABOLIC! Don't miss out!!!"
            hype_score = monitor._calculate_hype_score(hype_text)
            
            passed = hype_score > 0.3  # Should detect high hype
            self._log_result('telegram_monitor', 'Hype score calculation', passed,
                           f"Hype score: {hype_score}" if not passed else "")
        except Exception as e:
            self._log_result('telegram_monitor', 'Hype score calculation', False, str(e))
        
        # Test 3: Test alpha signal detection
        try:
            alpha_text = "$SOL entry at 45.2, targets: 50, 55, 60. SL: 42"
            signals = monitor._detect_alpha_signals(alpha_text)
            
            passed = len(signals) >= 2  # Should detect entry and target signals
            self._log_result('telegram_monitor', 'Alpha signal detection', passed,
                           f"Signals: {[s['type'] for s in signals]}" if not passed else "")
        except Exception as e:
            self._log_result('telegram_monitor', 'Alpha signal detection', False, str(e))
        
        # Test 4: Test trending signals retrieval
        try:
            # Add mock signals to state
            monitor.state['alpha_signals'] = [
                {
                    'message_id': 1,
                    'chat_id': 123,
                    'chat_title': 'Alpha Group',
                    'signals': [{'type': 'entry_signal'}],
                    'timestamp': datetime.now().isoformat(),
                    'hype_score': 0.8
                },
                {
                    'message_id': 2, 
                    'chat_id': 124,
                    'chat_title': 'Crypto Signals',
                    'signals': [{'type': 'target'}],
                    'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'hype_score': 0.6
                }
            ]
            
            trending = monitor.get_trending_signals(hours_back=24, min_hype_score=0.5)
            passed = len(trending) == 2
            self._log_result('telegram_monitor', 'Trending signals retrieval', passed,
                           f"Found {len(trending)} signals" if not passed else "")
        except Exception as e:
            self._log_result('telegram_monitor', 'Trending signals retrieval', False, str(e))
        
        # Test 5: Test monitoring stats
        try:
            stats = monitor.get_monitoring_stats()
            required_keys = ['processed_messages', 'alpha_signals_total', 'messages_today']
            passed = all(key in stats for key in required_keys)
            self._log_result('telegram_monitor', 'Monitoring stats generation', passed,
                           f"Stats: {list(stats.keys())}" if not passed else "")
        except Exception as e:
            self._log_result('telegram_monitor', 'Monitoring stats generation', False, str(e))
    
    async def test_social_aggregator(self):
        """Test social media aggregation functionality"""
        logger.info("\nTesting Social Aggregator...")
        
        # Test 1: Initialize SocialAggregator
        try:
            aggregator = SocialAggregator(checkpoint_file="test_data/aggregator_test.json")
            self._log_result('social_aggregator', 'Initialize SocialAggregator', True)
        except Exception as e:
            self._log_result('social_aggregator', 'Initialize SocialAggregator', False, str(e))
            return
        
        # Test 2: Test sentiment score normalization
        try:
            twitter_score = aggregator._normalize_sentiment_score(0.8, 'twitter')
            reddit_score = aggregator._normalize_sentiment_score(0.8, 'reddit')
            
            passed = twitter_score != reddit_score  # Should be different due to platform adjustments
            self._log_result('social_aggregator', 'Sentiment normalization', passed,
                           f"Twitter: {twitter_score}, Reddit: {reddit_score}" if not passed else "")
        except Exception as e:
            self._log_result('social_aggregator', 'Sentiment normalization', False, str(e))
        
        # Test 3: Test influence weight calculation
        try:
            mock_signal = SocialSignal(
                timestamp=datetime.now(),
                platform='twitter',
                content='Test content',
                sentiment_score=0.5,
                confidence=0.8,
                influence_score=0.7,
                engagement_metrics={'like_count': 100, 'retweet_count': 20},
                tokens_mentioned=['SOL'],
                source_id='test_123'
            )
            
            weight = aggregator._calculate_influence_weight(mock_signal)
            passed = 0.0 <= weight <= 1.0
            self._log_result('social_aggregator', 'Influence weight calculation', passed,
                           f"Weight: {weight}" if not passed else "")
        except Exception as e:
            self._log_result('social_aggregator', 'Influence weight calculation', False, str(e))
        
        # Test 4: Test token sentiment profile calculation
        try:
            mock_signals = [
                SocialSignal(
                    timestamp=datetime.now() - timedelta(minutes=30),
                    platform='twitter', content='SOL bullish!', sentiment_score=0.7,
                    confidence=0.8, influence_score=0.6, engagement_metrics={'like_count': 50},
                    tokens_mentioned=['SOL'], source_id='twitter_1'
                ),
                SocialSignal(
                    timestamp=datetime.now() - timedelta(minutes=15),
                    platform='reddit', content='SOL looks good', sentiment_score=0.5,
                    confidence=0.7, influence_score=0.4, engagement_metrics={'score': 25},
                    tokens_mentioned=['SOL'], source_id='reddit_1'
                )
            ]
            
            profile = aggregator.calculate_token_sentiment_profile('SOL', mock_signals)
            passed = (profile.total_mentions == 2 and 
                     -1.0 <= profile.overall_sentiment <= 1.0 and
                     len(profile.platform_sentiments) == 2)
            
            self._log_result('social_aggregator', 'Token sentiment profile', passed,
                           f"Profile: mentions={profile.total_mentions}, sentiment={profile.overall_sentiment:.3f}" if not passed else "")
        except Exception as e:
            self._log_result('social_aggregator', 'Token sentiment profile', False, str(e))
        
        # Test 5: Test market sentiment summary
        try:
            token_profiles = {'SOL': profile}
            market_summary = aggregator.calculate_market_sentiment_summary(mock_signals, token_profiles)
            
            passed = (hasattr(market_summary, 'overall_sentiment') and
                     hasattr(market_summary, 'confidence') and
                     hasattr(market_summary, 'market_narrative') and
                     len(market_summary.platform_breakdown) > 0)
            
            self._log_result('social_aggregator', 'Market sentiment summary', passed,
                           f"Summary: {market_summary.market_narrative}" if not passed else "")
        except Exception as e:
            self._log_result('social_aggregator', 'Market sentiment summary', False, str(e))
    
    async def test_integration(self):
        """Test end-to-end social intelligence integration"""
        logger.info("\nTesting Social Intelligence Integration...")
        
        try:
            # Initialize all components
            sentiment_analyzer = SentimentAnalyzer()
            token_extractor = TokenExtractor(checkpoint_file="test_data/integration_tokens.json")
            aggregator = SocialAggregator(checkpoint_file="test_data/integration_aggregator.json")
            
            self._log_result('integration', 'Component initialization', True)
        except Exception as e:
            self._log_result('integration', 'Component initialization', False, str(e))
            return
        
        # Test 1: Cross-platform sentiment analysis
        try:
            test_content = "Solana ecosystem is booming! Jupiter DEX volume through the roof. $SOL looking bullish 🚀"
            
            # Analyze with sentiment analyzer
            sentiment = await sentiment_analyzer.analyze_text(test_content, "social_media")
            
            # Extract tokens
            extracted_tokens = token_extractor.extract_from_text(test_content, "integration_test")
            
            # Create social signal
            signal = SocialSignal(
                timestamp=datetime.now(),
                platform='integration_test',
                content=test_content,
                sentiment_score=sentiment.polarity,
                confidence=sentiment.confidence,
                influence_score=0.5,
                engagement_metrics={'test_metric': 1},
                tokens_mentioned=[t.symbol for t in extracted_tokens],
                source_id='integration_test_1'
            )
            
            passed = (abs(signal.sentiment_score) <= 1.0 and 
                     signal.confidence > 0.0 and
                     len(signal.tokens_mentioned) > 0)
            
            self._log_result('integration', 'Cross-platform sentiment analysis', passed,
                           f"Sentiment: {signal.sentiment_score:.3f}, Tokens: {signal.tokens_mentioned}" if not passed else "")
        except Exception as e:
            self._log_result('integration', 'Cross-platform sentiment analysis', False, str(e))
        
        # Test 2: Multi-platform aggregation simulation
        try:
            # Simulate signals from different platforms
            multi_platform_signals = [
                SocialSignal(
                    datetime.now() - timedelta(minutes=45), 'twitter',
                    '$SOL breaking resistance! Target $55', 0.8, 0.9, 0.7,
                    {'like_count': 200, 'retweet_count': 50}, ['SOL'], 'twitter_multi_1'
                ),
                SocialSignal(
                    datetime.now() - timedelta(minutes=30), 'reddit',
                    'SOL fundamentals remain strong despite market volatility', 0.4, 0.8, 0.5,
                    {'score': 75, 'num_comments': 15}, ['SOL'], 'reddit_multi_1'
                ),
                SocialSignal(
                    datetime.now() - timedelta(minutes=15), 'telegram',
                    'Alpha alert: SOL accumulation phase ending soon 🚀', 0.9, 0.7, 0.8,
                    {'hype_score': 0.9}, ['SOL'], 'telegram_multi_1'
                )
            ]
            
            # Calculate comprehensive token profile
            sol_profile = aggregator.calculate_token_sentiment_profile('SOL', multi_platform_signals)
            
            # Calculate market summary
            market_summary = aggregator.calculate_market_sentiment_summary(
                multi_platform_signals, {'SOL': sol_profile}
            )
            
            passed = (sol_profile.total_mentions == 3 and
                     len(sol_profile.platform_sentiments) == 3 and
                     market_summary.overall_sentiment != 0.0)
            
            self._log_result('integration', 'Multi-platform aggregation', passed,
                           f"Platforms: {list(sol_profile.platform_sentiments.keys())}, Overall: {market_summary.overall_sentiment:.3f}" if not passed else "")
        except Exception as e:
            self._log_result('integration', 'Multi-platform aggregation', False, str(e))
        
        # Test 3: Real-time signal processing pipeline
        try:
            # Simulate real-time pipeline
            pipeline_results = []
            
            test_messages = [
                ("twitter", "Breaking: Major Solana partnership announced! #SOL #bullish"),
                ("reddit", "Analysis: Why SOL is undervalued compared to competitors"),
                ("telegram", "🚨 ALPHA: SOL entry 42.5, target 48-52 📈")
            ]
            
            for platform, content in test_messages:
                # Step 1: Sentiment analysis
                sentiment = await sentiment_analyzer.analyze_text(content, f"{platform}_message")
                
                # Step 2: Token extraction
                tokens = token_extractor.extract_from_text(content, platform)
                
                # Step 3: Create signal
                signal = SocialSignal(
                    datetime.now(), platform, content, sentiment.polarity,
                    sentiment.confidence, 0.5, {'engagement': 1},
                    [t.symbol for t in tokens], f"{platform}_pipeline_test"
                )
                
                pipeline_results.append(signal)
            
            # Step 4: Aggregate results
            final_profile = aggregator.calculate_token_sentiment_profile('SOL', pipeline_results)
            
            passed = (len(pipeline_results) == 3 and
                     final_profile.total_mentions >= len([s for s in pipeline_results if 'SOL' in s.tokens_mentioned]))
            
            self._log_result('integration', 'Real-time processing pipeline', passed,
                           f"Processed {len(pipeline_results)} signals, SOL mentions: {final_profile.total_mentions}" if not passed else "")
        except Exception as e:
            self._log_result('integration', 'Real-time processing pipeline', False, str(e))
    
    def print_summary(self):
        """Print comprehensive test results summary"""
        print(f"\n" + "="*70)
        print(f"PHASE 3 SOCIAL INTELLIGENCE TEST SUMMARY")
        print(f"="*70)
        
        total_passed = sum(component['passed'] for component in self.results.values())
        total_failed = sum(component['failed'] for component in self.results.values())
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nOverall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\nComponent Breakdown:")
        components = {
            'twitter_monitor': 'Twitter/X Monitoring',
            'reddit_monitor': 'Reddit Intelligence',
            'telegram_monitor': 'Telegram Monitoring', 
            'social_aggregator': 'Social Aggregator',
            'integration': 'Cross-platform Integration'
        }
        
        for component, name in components.items():
            results = self.results[component]
            total = results['passed'] + results['failed']
            rate = (results['passed'] / total * 100) if total > 0 else 0
            status = "✅" if results['failed'] == 0 else "❌" if results['passed'] == 0 else "⚠️"
            
            print(f"   {name:25} {status} {results['passed']}/{total} ({rate:5.1f}%)")
        
        # Print errors if any
        all_errors = []
        for component, results in self.results.items():
            if results['errors']:
                all_errors.extend([f"{component}: {error}" for error in results['errors']])
        
        if all_errors:
            print(f"\nError Details:")
            for error in all_errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(all_errors) > 5:
                print(f"   ... and {len(all_errors) - 5} more errors")
        
        # Status message
        if success_rate >= 90:
            print(f"\n🚀 Excellent! Social intelligence system is production-ready!")
        elif success_rate >= 75:
            print(f"\n✨ Good! Minor issues to address before deployment.")
        elif success_rate >= 50:
            print(f"\n⚠️  Moderate success. Several components need attention.")
        else:
            print(f"\n🔧 Needs work. Significant issues require debugging.")
        
        print(f"\n🎉 Phase 3 Session 2: Social Media Intelligence - Complete!")


async def main():
    """Run the complete Phase 3 social intelligence test suite"""
    print("Starting Phase 3 Social Intelligence Test Suite")
    print("Testing multi-platform social media monitoring...")
    
    # Create test data directory
    os.makedirs("test_data", exist_ok=True)
    
    # Initialize and run test suite
    test_suite = Phase3SocialTestSuite()
    
    await test_suite.test_twitter_monitor()
    await test_suite.test_reddit_monitor()  
    await test_suite.test_telegram_monitor()
    await test_suite.test_social_aggregator()
    await test_suite.test_integration()
    
    test_suite.print_summary()


if __name__ == "__main__":
    asyncio.run(main())