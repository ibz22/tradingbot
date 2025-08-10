"""
Telegram Monitor - Real-time Telegram Intelligence for Solana Trading Bot
========================================================================

Advanced Telegram monitoring system using Telegram Bot API for:
- Official Solana channels and alpha groups monitoring
- Message sentiment analysis and hype detection
- Channel member growth and engagement metrics
- Real-time message processing with context awareness
- Forward tracking and viral content detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
import json
import re
import time

from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters
from telegram.error import TelegramError

from .sentiment_analyzer import SentimentAnalyzer, SentimentScore
from ..discovery.token_extractor import TokenExtractor
from ..utils.checkpoint import load_checkpoint, save_checkpoint


@dataclass
class TelegramMessage:
    """Represents a Telegram message with metadata"""
    message_id: int
    chat_id: int
    chat_title: str
    chat_username: Optional[str]
    user_id: Optional[int]
    username: Optional[str] 
    first_name: Optional[str]
    text: str
    date: datetime
    forward_from_chat_id: Optional[int] = None
    forward_from_chat_title: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    entities: List[Dict] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    sentiment_score: float = 0.0
    confidence: float = 0.0
    tokens_mentioned: List[str] = None
    hype_score: float = 0.0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.tokens_mentioned is None:
            self.tokens_mentioned = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TelegramMessage':
        """Create from dictionary"""
        data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)


@dataclass
class TelegramChannel:
    """Represents a Telegram channel with metrics"""
    chat_id: int
    title: str
    username: Optional[str]
    description: Optional[str]
    member_count: Optional[int]
    type: str  # 'channel', 'group', 'supergroup'
    is_verified: bool = False
    is_scam: bool = False
    is_fake: bool = False
    recent_activity_score: float = 0.0
    avg_sentiment: float = 0.0
    message_count_24h: int = 0


class TelegramMonitor:
    """
    Advanced Telegram monitoring system for crypto alpha intelligence
    """
    
    # Target Telegram channels/groups
    TARGET_CHANNELS = {
        'official_solana': [
            '@SolanaLabs',
            '@SolanaOfficial', 
            '@SolanaFoundation',
            '@JupiterExchange',
            '@RaydiumProtocol'
        ],
        'alpha_groups': [
            '@SolanaAlpha',
            '@SolanaGems',
            '@SolanaMoonshots',
            '@CryptoAlphaChat',
            '@DeFiSignals'
        ],
        'news_channels': [
            '@SolanaNews',
            '@CryptoNews',
            '@DeFiPulse',
            '@CoinDesk',
            '@CoinTelegraph'
        ]
    }
    
    # Hype and alpha signal keywords
    HYPE_KEYWORDS = {
        'high_hype': [
            'moon', 'moonshot', 'gem', 'hidden gem', 'next 100x',
            'early alpha', 'insider', 'ape in', 'send it'
        ],
        'moderate_hype': [
            'bullish', 'pump', 'rally', 'breakout', 'surge',
            'opportunity', 'buy signal', 'long'
        ],
        'fomo_indicators': [
            'fomo', 'dont miss', 'last chance', 'going parabolic',
            'euphoria', 'mania', 'retail fomo'
        ]
    }
    
    # Alpha signal patterns
    ALPHA_PATTERNS = [
        re.compile(r'\b(\$[A-Z]{2,10})\s+(?:calls?|targets?|entry)\b', re.IGNORECASE),
        re.compile(r'\b(?:entry|buy)\s+(?:at|@|:)\s*([\d.]+)', re.IGNORECASE),
        re.compile(r'\btargets?\s*:?\s*([\d.]+(?:\s*[-,]\s*[\d.]+)*)', re.IGNORECASE),
        re.compile(r'\b(?:sl|stop\s*loss)\s*:?\s*([\d.]+)', re.IGNORECASE)
    ]
    
    def __init__(self,
                 bot_token: str,
                 sentiment_analyzer: Optional[SentimentAnalyzer] = None,
                 token_extractor: Optional[TokenExtractor] = None,
                 checkpoint_file: str = "data/telegram_monitor.json"):
        """
        Initialize Telegram Monitor
        
        Args:
            bot_token: Telegram Bot Token
            sentiment_analyzer: Sentiment analyzer instance
            token_extractor: Token extractor instance
            checkpoint_file: File to store monitoring state
        """
        self.bot_token = bot_token
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.token_extractor = token_extractor or TokenExtractor()
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Initialize Telegram bot
        self.bot = Bot(token=bot_token)
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'last_check': datetime.now() - timedelta(hours=1),
            'processed_message_ids': set(),
            'channel_metrics': {},
            'trending_messages': [],
            'alpha_signals': [],
            'daily_stats': {},
            'last_reset_date': datetime.now().date()
        })
        
        # Convert sets and dates back from JSON serialization
        if isinstance(self.state['processed_message_ids'], list):
            self.state['processed_message_ids'] = set(self.state['processed_message_ids'])
        if isinstance(self.state['last_check'], str):
            self.state['last_check'] = datetime.fromisoformat(self.state['last_check'])
        if isinstance(self.state['last_reset_date'], str):
            self.state['last_reset_date'] = datetime.fromisoformat(self.state['last_reset_date']).date()
        
        self._reset_daily_counters()
    
    def _reset_daily_counters(self):
        """Reset daily counters if new day"""
        today = datetime.now().date()
        if self.state['last_reset_date'] < today:
            self.state['daily_stats'] = {}
            self.state['last_reset_date'] = today
            self.logger.info("Reset daily Telegram counters")
    
    def _calculate_hype_score(self, text: str) -> float:
        """
        Calculate hype score for message content
        
        Args:
            text: Message text to analyze
            
        Returns:
            Hype score (0.0 to 1.0)
        """
        text_lower = text.lower()
        hype_score = 0.0
        
        # Count hype keywords
        for level, keywords in self.HYPE_KEYWORDS.items():
            multiplier = {'high_hype': 0.3, 'moderate_hype': 0.1, 'fomo_indicators': 0.2}.get(level, 0.1)
            for keyword in keywords:
                hype_score += text_lower.count(keyword) * multiplier
        
        # Detect excessive punctuation (hype indicator)
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        hype_score += min(exclamation_count * 0.05, 0.2)
        hype_score += min(caps_ratio * 0.3, 0.2)
        
        # Detect emoji usage (engagement indicator)
        emoji_count = len(re.findall(r'[🚀💎🌙📈💰🔥⚡]', text))
        hype_score += min(emoji_count * 0.02, 0.1)
        
        return min(hype_score, 1.0)
    
    def _detect_alpha_signals(self, text: str) -> List[Dict]:
        """
        Detect trading alpha signals in message
        
        Args:
            text: Message text to analyze
            
        Returns:
            List of detected alpha signals
        """
        signals = []
        
        for pattern in self.ALPHA_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                if 'entry' in match.group().lower() or 'buy' in match.group().lower():
                    signals.append({
                        'type': 'entry_signal',
                        'text': match.group(),
                        'position': match.span()
                    })
                elif 'target' in match.group().lower():
                    signals.append({
                        'type': 'target',
                        'text': match.group(),
                        'position': match.span()
                    })
                elif 'sl' in match.group().lower() or 'stop' in match.group().lower():
                    signals.append({
                        'type': 'stop_loss',
                        'text': match.group(),
                        'position': match.span()
                    })
        
        return signals
    
    async def get_channel_info(self, chat_identifier: Union[str, int]) -> Optional[TelegramChannel]:
        """
        Get information about a Telegram channel/group
        
        Args:
            chat_identifier: Channel username or chat ID
            
        Returns:
            Channel information if accessible
        """
        try:
            chat = await self.bot.get_chat(chat_identifier)
            
            # Get member count if possible
            member_count = None
            try:
                member_count = await self.bot.get_chat_member_count(chat.id)
            except TelegramError:
                pass  # Not accessible for some chats
            
            channel = TelegramChannel(
                chat_id=chat.id,
                title=chat.title or chat.first_name or 'Unknown',
                username=chat.username,
                description=chat.description,
                member_count=member_count,
                type=chat.type,
                is_verified=getattr(chat, 'is_verified', False),
                is_scam=getattr(chat, 'is_scam', False),
                is_fake=getattr(chat, 'is_fake', False)
            )
            
            return channel
            
        except TelegramError as e:
            self.logger.error(f"Error getting channel info for {chat_identifier}: {e}")
            return None
    
    async def fetch_channel_messages(self,
                                   chat_identifier: Union[str, int],
                                   limit: int = 100,
                                   offset_date: Optional[datetime] = None) -> List[TelegramMessage]:
        """
        Fetch recent messages from a channel (requires channel history access)
        
        Note: This method requires special permissions and may not work for all channels.
        In production, you'd typically use Telegram's MTProto API or run a user bot.
        
        Args:
            chat_identifier: Channel username or chat ID
            limit: Maximum messages to fetch
            offset_date: Date to start fetching from
            
        Returns:
            List of messages (may be empty if no access)
        """
        messages = []
        
        try:
            # Note: Bot API has limited history access
            # This is a placeholder for demonstration
            # In practice, you'd use telegram client library (pyrogram/telethon)
            
            self.logger.warning(
                f"Limited history access via Bot API for {chat_identifier}. "
                "Consider using MTProto client for full message history."
            )
            
            return messages
            
        except TelegramError as e:
            self.logger.error(f"Error fetching messages from {chat_identifier}: {e}")
            return messages
    
    async def process_message(self, update: Update, context=None) -> Optional[TelegramMessage]:
        """
        Process incoming Telegram message
        
        Args:
            update: Telegram update object
            context: Bot context (unused)
            
        Returns:
            Processed message object
        """
        if not update.message:
            return None
        
        message = update.message
        
        # Skip if already processed
        message_key = f"{message.chat_id}_{message.message_id}"
        if message_key in self.state['processed_message_ids']:
            return None
        
        try:
            # Extract entities (mentions, hashtags, URLs)
            entities = []
            if message.entities:
                for entity in message.entities:
                    entities.append({
                        'type': entity.type,
                        'offset': entity.offset,
                        'length': entity.length,
                        'url': getattr(entity, 'url', None)
                    })
            
            # Create message object
            telegram_msg = TelegramMessage(
                message_id=message.message_id,
                chat_id=message.chat_id,
                chat_title=message.chat.title or 'Private',
                chat_username=message.chat.username,
                user_id=message.from_user.id if message.from_user else None,
                username=message.from_user.username if message.from_user else None,
                first_name=message.from_user.first_name if message.from_user else None,
                text=message.text or message.caption or '',
                date=message.date,
                forward_from_chat_id=message.forward_from_chat.id if message.forward_from_chat else None,
                forward_from_chat_title=message.forward_from_chat.title if message.forward_from_chat else None,
                reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
                entities=entities
            )
            
            # Calculate hype score
            telegram_msg.hype_score = self._calculate_hype_score(telegram_msg.text)
            
            # Analyze sentiment
            if telegram_msg.text:
                sentiment = await self.sentiment_analyzer.analyze_text(
                    telegram_msg.text, context="telegram_message"
                )
                
                telegram_msg.sentiment_score = sentiment.polarity
                telegram_msg.confidence = sentiment.confidence
                
                # Extract tokens mentioned
                extracted_tokens = self.token_extractor.extract_from_text(
                    telegram_msg.text, f"telegram_{message.chat.username or 'group'}"
                )
                telegram_msg.tokens_mentioned = [token.symbol for token in extracted_tokens[:5]]
            
            # Detect alpha signals
            alpha_signals = self._detect_alpha_signals(telegram_msg.text)
            if alpha_signals:
                self.state['alpha_signals'].extend([{
                    'message_id': telegram_msg.message_id,
                    'chat_id': telegram_msg.chat_id,
                    'chat_title': telegram_msg.chat_title,
                    'signals': alpha_signals,
                    'timestamp': telegram_msg.date.isoformat(),
                    'hype_score': telegram_msg.hype_score
                }])
            
            self.state['processed_message_ids'].add(message_key)
            
            # Update daily stats
            today_str = datetime.now().date().isoformat()
            if today_str not in self.state['daily_stats']:
                self.state['daily_stats'][today_str] = {
                    'messages_processed': 0,
                    'channels_monitored': set(),
                    'alpha_signals_detected': 0,
                    'avg_hype_score': 0.0,
                    'avg_sentiment': 0.0
                }
            
            stats = self.state['daily_stats'][today_str]
            stats['messages_processed'] += 1
            stats['channels_monitored'].add(telegram_msg.chat_id)
            if alpha_signals:
                stats['alpha_signals_detected'] += len(alpha_signals)
            
            return telegram_msg
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return None
    
    async def analyze_channel_activity(self, 
                                     chat_identifiers: List[Union[str, int]]) -> Dict[str, Dict]:
        """
        Analyze activity across multiple channels
        
        Args:
            chat_identifiers: List of channel usernames or chat IDs
            
        Returns:
            Analysis results by channel
        """
        results = {}
        
        for chat_id in chat_identifiers:
            try:
                # Get channel info
                channel_info = await self.get_channel_info(chat_id)
                if not channel_info:
                    continue
                
                # Calculate activity metrics from processed messages
                channel_messages = [
                    msg for msg in self.state.get('trending_messages', [])
                    if msg.get('chat_id') == channel_info.chat_id
                ]
                
                if channel_messages:
                    avg_sentiment = sum(msg.get('sentiment_score', 0) for msg in channel_messages) / len(channel_messages)
                    avg_hype = sum(msg.get('hype_score', 0) for msg in channel_messages) / len(channel_messages)
                else:
                    avg_sentiment = 0.0
                    avg_hype = 0.0
                
                results[chat_id] = {
                    'channel_info': {
                        'title': channel_info.title,
                        'username': channel_info.username,
                        'member_count': channel_info.member_count,
                        'type': channel_info.type
                    },
                    'activity_metrics': {
                        'message_count_24h': len(channel_messages),
                        'avg_sentiment': avg_sentiment,
                        'avg_hype_score': avg_hype,
                        'alpha_signals': len([
                            signal for signal in self.state.get('alpha_signals', [])
                            if signal.get('chat_id') == channel_info.chat_id
                        ])
                    }
                }
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error analyzing channel {chat_id}: {e}")
        
        return results
    
    def get_trending_signals(self, hours_back: int = 24, min_hype_score: float = 0.3) -> List[Dict]:
        """
        Get trending alpha signals from recent messages
        
        Args:
            hours_back: Hours to look back for signals
            min_hype_score: Minimum hype score threshold
            
        Returns:
            List of trending alpha signals
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        trending_signals = []
        for signal in self.state.get('alpha_signals', []):
            signal_time = datetime.fromisoformat(signal['timestamp'])
            if signal_time > cutoff_time and signal.get('hype_score', 0) >= min_hype_score:
                trending_signals.append(signal)
        
        # Sort by hype score and recency
        trending_signals.sort(
            key=lambda x: (x.get('hype_score', 0), datetime.fromisoformat(x['timestamp'])),
            reverse=True
        )
        
        return trending_signals[:20]  # Return top 20
    
    async def start_monitoring(self,
                             target_channels: List[str] = None,
                             callback=None):
        """
        Start continuous Telegram monitoring
        
        Args:
            target_channels: List of channels to monitor (if supported)
            callback: Function to call with new data
        """
        self.logger.info("Starting Telegram monitoring...")
        
        try:
            # Create application
            application = Application.builder().token(self.bot_token).build()
            
            # Add message handler
            message_handler = MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                self.process_message
            )
            application.add_handler(message_handler)
            
            # Start monitoring
            await application.run_polling()
            
        except Exception as e:
            self.logger.error(f"Error in Telegram monitoring: {e}")
    
    def get_monitoring_stats(self) -> Dict:
        """Get Telegram monitoring statistics"""
        today_str = datetime.now().date().isoformat()
        today_stats = self.state['daily_stats'].get(today_str, {})
        
        return {
            'processed_messages': len(self.state['processed_message_ids']),
            'alpha_signals_total': len(self.state['alpha_signals']),
            'trending_messages': len(self.state['trending_messages']),
            'messages_today': today_stats.get('messages_processed', 0),
            'alpha_signals_today': today_stats.get('alpha_signals_detected', 0),
            'channels_monitored_today': len(today_stats.get('channels_monitored', set())),
            'last_check': self.state['last_check'].isoformat()
        }
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert sets to lists for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['processed_message_ids'] = list(self.state['processed_message_ids'])
        state_to_save['last_check'] = self.state['last_check'].isoformat()
        state_to_save['last_reset_date'] = self.state['last_reset_date'].isoformat()
        
        # Convert sets in daily stats
        for date_str, stats in state_to_save['daily_stats'].items():
            if 'channels_monitored' in stats and isinstance(stats['channels_monitored'], set):
                stats['channels_monitored'] = list(stats['channels_monitored'])
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_telegram_monitor():
    """Test the Telegram monitoring system"""
    import os
    
    # You need to set your Telegram Bot Token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
    
    if bot_token == 'your_bot_token_here':
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    monitor = TelegramMonitor(bot_token)
    
    print("Testing Telegram monitoring...")
    
    # Test channel analysis
    test_channels = ['@SolanaLabs', '@CryptoNews']  # Public channels
    results = await monitor.analyze_channel_activity(test_channels)
    
    for channel, data in results.items():
        print(f"\nChannel: {channel}")
        info = data.get('channel_info', {})
        metrics = data.get('activity_metrics', {})
        
        print(f"  Title: {info.get('title')}")
        print(f"  Members: {info.get('member_count', 'Unknown')}")
        print(f"  Avg Sentiment: {metrics.get('avg_sentiment', 0):.3f}")
        print(f"  Alpha Signals: {metrics.get('alpha_signals', 0)}")
    
    # Get trending signals
    trending = monitor.get_trending_signals()
    print(f"\nTrending Alpha Signals: {len(trending)}")
    for signal in trending[:3]:
        print(f"  - {signal.get('chat_title')}: Hype {signal.get('hype_score', 0):.2f}")
    
    # Show stats
    stats = monitor.get_monitoring_stats()
    print(f"\nMonitoring Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nNote: Full message monitoring requires running the bot and having users/channels send messages")


if __name__ == "__main__":
    asyncio.run(test_telegram_monitor())