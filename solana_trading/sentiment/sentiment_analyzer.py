"""
Sentiment Analyzer - Multi-layered AI Sentiment Analysis for Solana Trading Bot
==============================================================================

Advanced sentiment analysis combining multiple AI models and techniques:
- VADER sentiment analysis for crypto-specific content
- TextBlob for general sentiment
- OpenAI GPT for nuanced financial sentiment analysis
- Custom crypto sentiment scoring
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import re

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import openai

from .news_monitor import NewsArticle


class SentimentPolarity(Enum):
    """Sentiment polarity classification"""
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class SentimentScore:
    """Comprehensive sentiment analysis result"""
    polarity: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    classification: SentimentPolarity
    vader_score: Dict[str, float]
    textblob_score: float
    ai_score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    keywords_detected: List[str] = None
    risk_signals: List[str] = None
    
    def __post_init__(self):
        if self.keywords_detected is None:
            self.keywords_detected = []
        if self.risk_signals is None:
            self.risk_signals = []


class SentimentAnalyzer:
    """
    Multi-layered sentiment analysis system optimized for cryptocurrency content
    """
    
    # Crypto-specific sentiment keywords
    BULLISH_KEYWORDS = {
        'strong': {'moon', 'moonshot', 'bullish', 'pump', 'surge', 'rally', 'breakout', 'explosion'},
        'medium': {'rising', 'growth', 'gain', 'up', 'bull', 'positive', 'green', 'buy'},
        'weak': {'recovery', 'potential', 'opportunity', 'support', 'bounce'}
    }
    
    BEARISH_KEYWORDS = {
        'strong': {'crash', 'dump', 'rug', 'scam', 'collapse', 'plummet', 'disaster'},
        'medium': {'bear', 'bearish', 'fall', 'drop', 'decline', 'red', 'sell', 'down'},
        'weak': {'correction', 'pullback', 'dip', 'resistance', 'concern'}
    }
    
    RISK_SIGNALS = {
        'high_risk': {'rug pull', 'exit scam', 'ponzi', 'pump and dump', 'fake', 'scam'},
        'medium_risk': {'volatile', 'risky', 'speculative', 'unaudited', 'experimental'},
        'regulatory': {'sec investigation', 'regulatory', 'banned', 'illegal', 'lawsuit'}
    }
    
    # Financial context keywords
    FINANCIAL_CONTEXTS = {
        'trading': {'volume', 'liquidity', 'market cap', 'trading', 'exchange', 'dex'},
        'adoption': {'partnership', 'integration', 'adoption', 'mainstream', 'institutional'},
        'technical': {'upgrade', 'update', 'fork', 'protocol', 'blockchain', 'smart contract'}
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize sentiment analyzer
        
        Args:
            openai_api_key: OpenAI API key for advanced analysis
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize VADER analyzer
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize OpenAI client if API key provided
        self.openai_client = None
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
            
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for keyword detection"""
        self.bullish_patterns = {}
        self.bearish_patterns = {}
        self.risk_patterns = {}
        
        for strength, keywords in self.BULLISH_KEYWORDS.items():
            pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.bullish_patterns[strength] = re.compile(pattern, re.IGNORECASE)
        
        for strength, keywords in self.BEARISH_KEYWORDS.items():
            pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.bearish_patterns[strength] = re.compile(pattern, re.IGNORECASE)
        
        for risk_type, keywords in self.RISK_SIGNALS.items():
            pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.risk_patterns[risk_type] = re.compile(pattern, re.IGNORECASE)
    
    def _analyze_keywords(self, text: str) -> Tuple[float, List[str], List[str]]:
        """
        Analyze text for crypto-specific sentiment keywords
        
        Args:
            text: Text to analyze
            
        Returns:
            (sentiment_score, detected_keywords, risk_signals)
        """
        text_lower = text.lower()
        sentiment_score = 0.0
        detected_keywords = []
        risk_signals = []
        
        # Check bullish keywords
        for strength, pattern in self.bullish_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_keywords.extend(matches)
                if strength == 'strong':
                    sentiment_score += len(matches) * 0.3
                elif strength == 'medium':
                    sentiment_score += len(matches) * 0.2
                else:
                    sentiment_score += len(matches) * 0.1
        
        # Check bearish keywords
        for strength, pattern in self.bearish_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_keywords.extend(matches)
                if strength == 'strong':
                    sentiment_score -= len(matches) * 0.3
                elif strength == 'medium':
                    sentiment_score -= len(matches) * 0.2
                else:
                    sentiment_score -= len(matches) * 0.1
        
        # Check risk signals
        for risk_type, pattern in self.risk_patterns.items():
            matches = pattern.findall(text)
            if matches:
                risk_signals.extend([f"{risk_type}: {match}" for match in matches])
        
        return sentiment_score, detected_keywords, risk_signals
    
    def _analyze_with_vader(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            VADER sentiment scores
        """
        return self.vader.polarity_scores(text)
    
    def _analyze_with_textblob(self, text: str) -> float:
        """
        Analyze sentiment using TextBlob
        
        Args:
            text: Text to analyze
            
        Returns:
            TextBlob polarity score (-1 to 1)
        """
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception as e:
            self.logger.warning(f"TextBlob analysis failed: {e}")
            return 0.0
    
    async def _analyze_with_ai(self, text: str, context: str = "cryptocurrency") -> Tuple[float, str]:
        """
        Analyze sentiment using OpenAI GPT
        
        Args:
            text: Text to analyze
            context: Context for analysis
            
        Returns:
            (ai_sentiment_score, reasoning)
        """
        if not self.openai_client:
            return None, None
        
        try:
            prompt = f"""
            Analyze the sentiment of the following {context} news/content for trading purposes.
            
            Text: "{text[:1500]}"
            
            Please provide:
            1. Sentiment score from -1.0 (very bearish) to +1.0 (very bullish)
            2. Brief reasoning (2-3 sentences)
            
            Consider:
            - Market impact potential
            - Price movement implications
            - Risk factors
            - Adoption/development news
            
            Respond in JSON format:
            {{"score": 0.0, "reasoning": "explanation"}}
            """
            
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system", 
                    "content": "You are a cryptocurrency market analyst expert in sentiment analysis."
                }, {
                    "role": "user", 
                    "content": prompt
                }],
                max_tokens=200,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = json.loads(content)
            return float(result.get('score', 0.0)), result.get('reasoning', '')
            
        except Exception as e:
            self.logger.warning(f"OpenAI sentiment analysis failed: {e}")
            return None, None
    
    def _classify_sentiment(self, polarity: float) -> SentimentPolarity:
        """
        Classify sentiment polarity into categories
        
        Args:
            polarity: Sentiment polarity score (-1 to 1)
            
        Returns:
            Sentiment classification
        """
        if polarity <= -0.6:
            return SentimentPolarity.VERY_BEARISH
        elif polarity <= -0.2:
            return SentimentPolarity.BEARISH
        elif polarity >= 0.6:
            return SentimentPolarity.VERY_BULLISH
        elif polarity >= 0.2:
            return SentimentPolarity.BULLISH
        else:
            return SentimentPolarity.NEUTRAL
    
    def _calculate_confidence(self, scores: Dict) -> float:
        """
        Calculate confidence in sentiment analysis
        
        Args:
            scores: Dictionary of various sentiment scores
            
        Returns:
            Confidence score (0 to 1)
        """
        # Base confidence from VADER compound score
        base_confidence = abs(scores.get('vader_compound', 0))
        
        # Boost confidence if multiple methods agree
        agreement_bonus = 0.0
        if 'textblob' in scores and 'vader_compound' in scores:
            textblob = scores['textblob']
            vader = scores['vader_compound']
            
            # Check if they agree on direction
            if (textblob > 0 and vader > 0) or (textblob < 0 and vader < 0):
                agreement_bonus += 0.2
        
        # Boost confidence if AI analysis is available and agrees
        if 'ai_score' in scores and scores['ai_score'] is not None:
            ai_score = scores['ai_score']
            vader = scores.get('vader_compound', 0)
            
            if (ai_score > 0 and vader > 0) or (ai_score < 0 and vader < 0):
                agreement_bonus += 0.3
        
        # Boost confidence if crypto keywords are detected
        if scores.get('keyword_sentiment', 0) != 0:
            agreement_bonus += 0.1
        
        return min(base_confidence + agreement_bonus, 1.0)
    
    async def analyze_text(self, text: str, context: str = "cryptocurrency") -> SentimentScore:
        """
        Perform comprehensive sentiment analysis on text
        
        Args:
            text: Text to analyze
            context: Context for analysis
            
        Returns:
            Comprehensive sentiment analysis result
        """
        if not text or len(text.strip()) < 10:
            return SentimentScore(
                polarity=0.0,
                confidence=0.0,
                classification=SentimentPolarity.NEUTRAL,
                vader_score={},
                textblob_score=0.0
            )
        
        # Analyze with different methods
        vader_scores = self._analyze_with_vader(text)
        textblob_score = self._analyze_with_textblob(text)
        keyword_sentiment, keywords, risks = self._analyze_keywords(text)
        ai_score, ai_reasoning = await self._analyze_with_ai(text, context)
        
        # Combine scores with weighted average
        scores = []
        weights = []
        
        # VADER (weight: 0.3)
        scores.append(vader_scores['compound'])
        weights.append(0.3)
        
        # TextBlob (weight: 0.2)
        scores.append(textblob_score)
        weights.append(0.2)
        
        # Keyword sentiment (weight: 0.3)
        scores.append(max(min(keyword_sentiment, 1.0), -1.0))  # Clamp to [-1, 1]
        weights.append(0.3)
        
        # AI sentiment (weight: 0.2 if available)
        if ai_score is not None:
            scores.append(ai_score)
            weights.append(0.2)
        
        # Calculate weighted average
        total_weight = sum(weights)
        combined_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        # Calculate confidence
        score_dict = {
            'vader_compound': vader_scores['compound'],
            'textblob': textblob_score,
            'keyword_sentiment': keyword_sentiment,
            'ai_score': ai_score
        }
        confidence = self._calculate_confidence(score_dict)
        
        # Classify sentiment
        classification = self._classify_sentiment(combined_score)
        
        return SentimentScore(
            polarity=combined_score,
            confidence=confidence,
            classification=classification,
            vader_score=vader_scores,
            textblob_score=textblob_score,
            ai_score=ai_score,
            ai_reasoning=ai_reasoning,
            keywords_detected=keywords,
            risk_signals=risks
        )
    
    async def analyze_article(self, article: NewsArticle) -> NewsArticle:
        """
        Analyze sentiment of a news article
        
        Args:
            article: News article to analyze
            
        Returns:
            Article with updated sentiment score
        """
        # Combine title, description, and content for analysis
        full_text = f"{article.title}. {article.description}. {article.content[:1000]}"
        
        sentiment = await self.analyze_text(full_text, "cryptocurrency news")
        
        # Update article with sentiment data
        article.sentiment_score = sentiment.polarity
        
        # Store additional sentiment data as tokens mentioned for now
        # (in a real implementation, you might want to add sentiment metadata)
        if sentiment.keywords_detected:
            article.tokens_mentioned.extend([
                f"sentiment:{sentiment.classification.name.lower()}",
                f"confidence:{sentiment.confidence:.2f}"
            ])
        
        return article
    
    async def analyze_batch(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Analyze sentiment for a batch of articles
        
        Args:
            articles: List of articles to analyze
            
        Returns:
            Articles with updated sentiment scores
        """
        tasks = [self.analyze_article(article) for article in articles]
        return await asyncio.gather(*tasks)
    
    def get_market_sentiment_summary(self, articles: List[NewsArticle]) -> Dict:
        """
        Get overall market sentiment summary from articles
        
        Args:
            articles: List of analyzed articles
            
        Returns:
            Market sentiment summary
        """
        if not articles:
            return {
                'overall_sentiment': 0.0,
                'sentiment_distribution': {},
                'confidence': 0.0,
                'total_articles': 0
            }
        
        # Calculate weighted average sentiment (weight by relevance and confidence)
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        sentiment_counts = {polarity.name: 0 for polarity in SentimentPolarity}
        
        for article in articles:
            weight = article.relevance_score
            total_weighted_sentiment += article.sentiment_score * weight
            total_weight += weight
            
            # Count sentiment classifications
            classification = self._classify_sentiment(article.sentiment_score)
            sentiment_counts[classification.name] += 1
        
        overall_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate overall confidence
        avg_confidence = sum(abs(a.sentiment_score) for a in articles) / len(articles)
        
        return {
            'overall_sentiment': round(overall_sentiment, 3),
            'sentiment_distribution': sentiment_counts,
            'confidence': round(avg_confidence, 3),
            'total_articles': len(articles),
            'classification': self._classify_sentiment(overall_sentiment).name
        }


# Example usage and testing
async def test_sentiment_analyzer():
    """Test the sentiment analysis system"""
    import os
    
    # Initialize analyzer (OpenAI key optional)
    openai_key = os.getenv('OPENAI_API_KEY')  # Optional
    analyzer = SentimentAnalyzer(openai_key)
    
    # Test texts
    test_texts = [
        "Solana price surges 25% after major Jupiter DEX upgrade announcement!",
        "SOL crashes 15% amid market-wide selloff and regulatory concerns",
        "Raydium protocol launches new liquidity mining program with attractive APY",
        "Warning: New Solana token appears to be a potential rug pull scam",
        "Institutional adoption of Solana continues with major DeFi integration"
    ]
    
    print("🧠 Testing Sentiment Analysis System")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: {text[:60]}...")
        
        sentiment = await analyzer.analyze_text(text)
        
        print(f"   Polarity: {sentiment.polarity:.3f} ({sentiment.classification.name})")
        print(f"   Confidence: {sentiment.confidence:.3f}")
        print(f"   VADER: {sentiment.vader_score['compound']:.3f}")
        print(f"   TextBlob: {sentiment.textblob_score:.3f}")
        
        if sentiment.keywords_detected:
            print(f"   Keywords: {', '.join(sentiment.keywords_detected[:3])}")
        
        if sentiment.risk_signals:
            print(f"   🚨 Risk Signals: {', '.join(sentiment.risk_signals)}")
        
        if sentiment.ai_reasoning:
            print(f"   AI Reasoning: {sentiment.ai_reasoning[:100]}...")
    
    print("\n✅ Sentiment analysis testing complete!")


if __name__ == "__main__":
    asyncio.run(test_sentiment_analyzer())