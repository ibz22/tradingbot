"""
Phase 3 News Monitoring Infrastructure Test
==========================================

Comprehensive testing of the news monitoring foundation:
- NewsAPI integration
- Sentiment analysis system  
- Token extraction from articles
- End-to-end pipeline validation
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List

from solana_trading.sentiment.news_monitor import NewsMonitor, NewsArticle
from solana_trading.sentiment.sentiment_analyzer import SentimentAnalyzer
from solana_trading.discovery.token_extractor import TokenExtractor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3TestSuite:
    """Comprehensive test suite for Phase 3 news monitoring infrastructure"""
    
    def __init__(self):
        """Initialize test suite"""
        self.results = {
            'news_monitor': {'passed': 0, 'failed': 0, 'errors': []},
            'sentiment_analyzer': {'passed': 0, 'failed': 0, 'errors': []},
            'token_extractor': {'passed': 0, 'failed': 0, 'errors': []},
            'integration': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def _log_result(self, component: str, test_name: str, passed: bool, error: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {component}: {test_name}")
        
        if passed:
            self.results[component]['passed'] += 1
        else:
            self.results[component]['failed'] += 1
            if error:
                self.results[component]['errors'].append(f"{test_name}: {error}")
                logger.error(f"Error in {test_name}: {error}")
    
    async def test_news_monitor(self):
        """Test NewsAPI integration and news monitoring"""
        logger.info("\n🧪 Testing News Monitor...")
        
        # Test 1: Initialize NewsMonitor
        try:
            # Use dummy API key for testing
            api_key = os.getenv('NEWSAPI_KEY', 'dummy_key_for_testing')
            monitor = NewsMonitor(api_key, checkpoint_file="test_data/news_monitor_test.json")
            self._log_result('news_monitor', 'Initialize NewsMonitor', True)
        except Exception as e:
            self._log_result('news_monitor', 'Initialize NewsMonitor', False, str(e))
            return
        
        # Test 2: Test relevance scoring
        try:
            test_article = {
                'title': 'Solana price surges 25% after Jupiter DEX upgrade',
                'description': 'SOL token rallies amid DeFi adoption news',
                'url': 'https://example.com/test-article'
            }
            
            relevance_score = monitor._calculate_relevance_score(test_article)
            passed = 0.0 <= relevance_score <= 1.0 and relevance_score > 0.3
            self._log_result('news_monitor', 'Relevance scoring', passed, 
                           f"Score: {relevance_score}" if not passed else "")
        except Exception as e:
            self._log_result('news_monitor', 'Relevance scoring', False, str(e))
        
        # Test 3: Test trending topics extraction
        try:
            mock_articles = [
                NewsArticle(
                    title="Solana ecosystem grows with new DEX launch",
                    description="DeFi protocol announces Solana integration",
                    content="The new decentralized exchange built on Solana blockchain...",
                    url="https://example.com/1",
                    source="TestSource",
                    published_at=datetime.now()
                ),
                NewsArticle(
                    title="SOL token breaks resistance level",
                    description="Bullish momentum continues for Solana",
                    content="Technical analysis shows SOL breaking key levels...",
                    url="https://example.com/2", 
                    source="TestSource",
                    published_at=datetime.now()
                )
            ]
            
            topics = monitor.get_trending_topics(mock_articles)
            passed = isinstance(topics, dict) and len(topics) > 0
            self._log_result('news_monitor', 'Trending topics extraction', passed,
                           f"Topics: {list(topics.keys())[:3]}" if not passed else "")
        except Exception as e:
            self._log_result('news_monitor', 'Trending topics extraction', False, str(e))
        
        # Test 4: Test article summary
        try:
            test_article = NewsArticle(
                title="Test Article",
                description="Test description",
                content="Test content",
                url="https://example.com/test",
                source="TestSource",
                published_at=datetime.now(),
                relevance_score=0.8,
                sentiment_score=0.5
            )
            
            summary = monitor.get_article_summary(test_article)
            required_keys = ['title', 'source', 'published', 'relevance', 'sentiment', 'url']
            passed = all(key in summary for key in required_keys)
            self._log_result('news_monitor', 'Article summary generation', passed,
                           f"Missing keys: {[k for k in required_keys if k not in summary]}" if not passed else "")
        except Exception as e:
            self._log_result('news_monitor', 'Article summary generation', False, str(e))
    
    async def test_sentiment_analyzer(self):
        """Test AI sentiment analysis system"""
        logger.info("\n🧠 Testing Sentiment Analyzer...")
        
        # Test 1: Initialize SentimentAnalyzer
        try:
            openai_key = os.getenv('OPENAI_API_KEY')  # Optional for testing
            analyzer = SentimentAnalyzer(openai_key)
            self._log_result('sentiment_analyzer', 'Initialize SentimentAnalyzer', True)
        except Exception as e:
            self._log_result('sentiment_analyzer', 'Initialize SentimentAnalyzer', False, str(e))
            return
        
        # Test 2: Test sentiment analysis on bullish text
        try:
            bullish_text = "Solana price surges 25% after major Jupiter DEX upgrade announcement! SOL token rallies amid increasing adoption."
            sentiment = await analyzer.analyze_text(bullish_text)
            
            passed = (sentiment.polarity > 0 and 
                     sentiment.classification.name in ['BULLISH', 'VERY_BULLISH'] and
                     sentiment.confidence > 0.3)
            
            self._log_result('sentiment_analyzer', 'Bullish sentiment detection', passed,
                           f"Polarity: {sentiment.polarity:.3f}, Classification: {sentiment.classification.name}" if not passed else "")
        except Exception as e:
            self._log_result('sentiment_analyzer', 'Bullish sentiment detection', False, str(e))
        
        # Test 3: Test sentiment analysis on bearish text
        try:
            bearish_text = "SOL token crashes 15% amid market selloff and regulatory concerns. Investors fear further downside."
            sentiment = await analyzer.analyze_text(bearish_text)
            
            passed = (sentiment.polarity < 0 and 
                     sentiment.classification.name in ['BEARISH', 'VERY_BEARISH'] and
                     sentiment.confidence > 0.3)
            
            self._log_result('sentiment_analyzer', 'Bearish sentiment detection', passed,
                           f"Polarity: {sentiment.polarity:.3f}, Classification: {sentiment.classification.name}" if not passed else "")
        except Exception as e:
            self._log_result('sentiment_analyzer', 'Bearish sentiment detection', False, str(e))
        
        # Test 4: Test risk signal detection
        try:
            risky_text = "Warning: New Solana token appears to be potential rug pull scam according to analysts"
            sentiment = await analyzer.analyze_text(risky_text)
            
            passed = len(sentiment.risk_signals) > 0
            self._log_result('sentiment_analyzer', 'Risk signal detection', passed,
                           f"Risk signals: {sentiment.risk_signals}" if not passed else "")
        except Exception as e:
            self._log_result('sentiment_analyzer', 'Risk signal detection', False, str(e))
        
        # Test 5: Test batch analysis
        try:
            test_articles = [
                NewsArticle(
                    title="Solana ecosystem booms with new protocols",
                    description="DeFi growth continues on Solana",
                    content="Multiple new protocols launching...",
                    url="https://example.com/1",
                    source="TestSource",
                    published_at=datetime.now()
                ),
                NewsArticle(
                    title="SOL price correction continues",
                    description="Technical indicators suggest further decline",
                    content="Chart analysis shows bearish pattern...",
                    url="https://example.com/2",
                    source="TestSource", 
                    published_at=datetime.now()
                )
            ]
            
            analyzed_articles = await analyzer.analyze_batch(test_articles)
            passed = (len(analyzed_articles) == 2 and 
                     all(abs(article.sentiment_score) <= 1.0 for article in analyzed_articles))
            
            self._log_result('sentiment_analyzer', 'Batch analysis', passed,
                           f"Sentiment scores: {[a.sentiment_score for a in analyzed_articles]}" if not passed else "")
        except Exception as e:
            self._log_result('sentiment_analyzer', 'Batch analysis', False, str(e))
    
    async def test_token_extractor(self):
        """Test token discovery and extraction"""
        logger.info("\n🔍 Testing Token Extractor...")
        
        # Test 1: Initialize TokenExtractor
        try:
            extractor = TokenExtractor(checkpoint_file="test_data/token_extractor_test.json")
            self._log_result('token_extractor', 'Initialize TokenExtractor', True)
        except Exception as e:
            self._log_result('token_extractor', 'Initialize TokenExtractor', False, str(e))
            return
        
        # Test 2: Test token symbol extraction
        try:
            test_text = "$BONK surges 50% after major exchange listing. Jupiter (JUP) token airdrop creates buzz."
            tokens = extractor.extract_from_text(test_text, "test_source")
            
            extracted_symbols = [token.symbol for token in tokens]
            passed = 'BONK' in extracted_symbols and 'JUP' in extracted_symbols
            
            self._log_result('token_extractor', 'Token symbol extraction', passed,
                           f"Extracted: {extracted_symbols}" if not passed else "")
        except Exception as e:
            self._log_result('token_extractor', 'Token symbol extraction', False, str(e))
        
        # Test 3: Test Solana address extraction
        try:
            test_text = "New token at address 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU shows promise"
            tokens = extractor.extract_from_text(test_text, "test_source")
            
            has_address = any(token.address for token in tokens)
            self._log_result('token_extractor', 'Solana address extraction', has_address,
                           f"Tokens found: {len(tokens)}" if not has_address else "")
        except Exception as e:
            self._log_result('token_extractor', 'Solana address extraction', False, str(e))
        
        # Test 4: Test false positive filtering
        try:
            false_positive_text = "The SEC announced new USA regulations for crypto. FBI investigates scam."
            tokens = extractor.extract_from_text(false_positive_text, "test_source")
            
            # Should not extract SEC, USA, FBI as tokens
            extracted_symbols = [token.symbol for token in tokens if token.confidence > 0.3]
            false_positives = {'SEC', 'USA', 'FBI'} & set(extracted_symbols)
            
            passed = len(false_positives) == 0
            self._log_result('token_extractor', 'False positive filtering', passed,
                           f"False positives detected: {list(false_positives)}" if not passed else "")
        except Exception as e:
            self._log_result('token_extractor', 'False positive filtering', False, str(e))
        
        # Test 5: Test confidence scoring
        try:
            high_confidence_text = "$BONK token launches on Jupiter DEX with high trading volume"
            low_confidence_text = "The word MOON appears in this sentence"
            
            high_conf_tokens = extractor.extract_from_text(high_confidence_text, "test")
            low_conf_tokens = extractor.extract_from_text(low_confidence_text, "test")
            
            high_conf_avg = sum(t.confidence for t in high_conf_tokens) / len(high_conf_tokens) if high_conf_tokens else 0
            low_conf_avg = sum(t.confidence for t in low_conf_tokens) / len(low_conf_tokens) if low_conf_tokens else 0
            
            passed = high_conf_avg > low_conf_avg or (high_conf_avg > 0.5 and low_conf_avg < 0.3)
            self._log_result('token_extractor', 'Confidence scoring', passed,
                           f"High: {high_conf_avg:.3f}, Low: {low_conf_avg:.3f}" if not passed else "")
        except Exception as e:
            self._log_result('token_extractor', 'Confidence scoring', False, str(e))
    
    async def test_integration(self):
        """Test end-to-end integration"""
        logger.info("\n🔄 Testing End-to-End Integration...")
        
        try:
            # Initialize all components
            api_key = os.getenv('NEWSAPI_KEY', 'dummy_key_for_testing')  
            openai_key = os.getenv('OPENAI_API_KEY')
            
            monitor = NewsMonitor(api_key, checkpoint_file="test_data/integration_news.json")
            analyzer = SentimentAnalyzer(openai_key)
            extractor = TokenExtractor(checkpoint_file="test_data/integration_tokens.json")
            
            # Create mock news articles
            mock_articles = [
                NewsArticle(
                    title="$BONK Token Explodes 200% After Major Partnership Announcement",
                    description="BONK token sees massive rally following Jupiter DEX integration news",
                    content="The BONK ecosystem continues to grow with significant partnerships. Jupiter protocol announced deep integration with BONK token for trading pairs. Market analysts expect continued bullish momentum for SOL ecosystem tokens.",
                    url="https://example.com/bonk-rally",
                    source="CryptoNews",
                    published_at=datetime.now(),
                    relevance_score=0.9
                ),
                NewsArticle(
                    title="Solana Network Congestion Causes Token Trading Issues",
                    description="SOL network experiences slowdown affecting DEX operations",
                    content="Solana blockchain faced congestion issues today, impacting trading on Raydium and Orca protocols. Users report failed transactions and slower confirmation times. Network developers are working on optimization.",
                    url="https://example.com/sol-congestion", 
                    source="BlockchainToday",
                    published_at=datetime.now(),
                    relevance_score=0.7
                )
            ]
            
            self._log_result('integration', 'Component initialization', True)
        except Exception as e:
            self._log_result('integration', 'Component initialization', False, str(e))
            return
        
        # Test 1: Full pipeline processing
        try:
            # Process articles through sentiment analysis
            analyzed_articles = await analyzer.analyze_batch(mock_articles)
            
            # Extract tokens from articles
            all_extracted_tokens = []
            for article in analyzed_articles:
                full_text = f"{article.title}. {article.description}. {article.content}"
                tokens = extractor.extract_from_text(full_text, article.source)
                all_extracted_tokens.extend(tokens)
            
            # Generate market sentiment summary
            sentiment_summary = analyzer.get_market_sentiment_summary(analyzed_articles)
            
            # Validate results
            pipeline_passed = (
                len(analyzed_articles) == 2 and
                all(abs(article.sentiment_score) <= 1.0 for article in analyzed_articles) and
                len(all_extracted_tokens) > 0 and
                'overall_sentiment' in sentiment_summary
            )
            
            self._log_result('integration', 'Full pipeline processing', pipeline_passed,
                           f"Articles: {len(analyzed_articles)}, Tokens: {len(all_extracted_tokens)}" if not pipeline_passed else "")
            
            # Log detailed results
            logger.info(f"\n📊 Integration Results:")
            logger.info(f"   Articles processed: {len(analyzed_articles)}")
            logger.info(f"   Average sentiment: {sentiment_summary.get('overall_sentiment', 0):.3f}")
            logger.info(f"   Tokens extracted: {len(all_extracted_tokens)}")
            logger.info(f"   Top tokens: {[t.symbol for t in all_extracted_tokens[:3]]}")
            
        except Exception as e:
            self._log_result('integration', 'Full pipeline processing', False, str(e))
        
        # Test 2: Data persistence and state management
        try:
            # Test state saving and loading
            extraction_stats = extractor.get_extraction_stats()
            monitor._save_state()
            
            passed = isinstance(extraction_stats, dict) and 'total_extractions' in extraction_stats
            self._log_result('integration', 'Data persistence', passed,
                           f"Stats keys: {list(extraction_stats.keys())}" if not passed else "")
        except Exception as e:
            self._log_result('integration', 'Data persistence', False, str(e))
    
    def print_summary(self):
        """Print test results summary"""
        print(f"\n" + "="*60)
        print(f"📋 PHASE 3 NEWS MONITORING TEST SUMMARY")
        print(f"="*60)
        
        total_passed = sum(component['passed'] for component in self.results.values())
        total_failed = sum(component['failed'] for component in self.results.values())
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed} ✅")
        print(f"   Failed: {total_failed} ❌") 
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n📈 Component Breakdown:")
        for component, results in self.results.items():
            total = results['passed'] + results['failed']
            rate = (results['passed'] / total * 100) if total > 0 else 0
            status = "✅" if results['failed'] == 0 else "❌" if results['passed'] == 0 else "⚠️"
            
            print(f"   {component:20} {status} {results['passed']}/{total} ({rate:5.1f}%)")
        
        # Print errors if any
        all_errors = []
        for component, results in self.results.items():
            if results['errors']:
                all_errors.extend([f"{component}: {error}" for error in results['errors']])
        
        if all_errors:
            print(f"\n🔍 Error Details:")
            for error in all_errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(all_errors) > 5:
                print(f"   ... and {len(all_errors) - 5} more errors")
        
        # Status message
        if success_rate >= 90:
            print(f"\n🚀 Excellent! Phase 3 foundation is ready for production!")
        elif success_rate >= 75:
            print(f"\n✨ Good! Minor issues to address before full deployment.")
        elif success_rate >= 50:
            print(f"\n⚠️  Moderate success. Several issues need attention.")
        else:
            print(f"\n🔧 Needs work. Significant issues require debugging.")
        
        print(f"\n🎉 Phase 3 Session 1: News Monitoring Foundation - Complete!")


async def main():
    """Run the complete Phase 3 test suite"""
    print("Starting Phase 3 News Monitoring Infrastructure Tests")
    print("Building the future of alpha generation...")
    
    # Create test data directory
    os.makedirs("test_data", exist_ok=True)
    
    # Initialize and run test suite
    test_suite = Phase3TestSuite()
    
    await test_suite.test_news_monitor()
    await test_suite.test_sentiment_analyzer()
    await test_suite.test_token_extractor()
    await test_suite.test_integration()
    
    test_suite.print_summary()


if __name__ == "__main__":
    asyncio.run(main())