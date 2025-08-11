"""
Enhanced Token Discovery System - Complete Token Discovery & Validation Pipeline
================================================================================

Advanced token discovery system integrating:
- Intelligent token extraction from news and social media
- Real-time token validation and legitimacy verification
- Comprehensive rug pull detection and risk assessment
- Liquidity analysis and trading feasibility evaluation
- Integration with sentiment analysis for confidence scoring
- Complete validation pipeline for discovered tokens
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import requests
from bs4 import BeautifulSoup

# Optional import - SolanaClient may not be available in all environments
try:
    from ..core.client import SolanaClient
except ImportError:
    SolanaClient = None
from ..utils.checkpoint import load_checkpoint, save_checkpoint


@dataclass
class ValidatedToken:
    """Represents a fully validated token with comprehensive analysis"""
    symbol: str
    address: Optional[str] = None
    name: Optional[str] = None
    source_text: str = ""
    extraction_confidence: float = 0.0
    context: str = ""
    extraction_method: str = ""
    
    # Validation results
    is_validated: bool = False
    validation_status: str = "unknown"  # from TokenValidator
    security_score: float = 0.0
    
    # Liquidity analysis
    liquidity_tier: str = "unknown"
    total_liquidity_usd: float = 0.0
    trading_feasibility: str = "unknown"
    
    # Rug pull analysis
    rug_risk_level: str = "unknown"
    rug_detection_status: str = "unknown"
    overall_risk_score: float = 1.0  # Default to high risk
    
    # Market data
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price: Optional[float] = None
    
    # Final assessment
    trading_recommendation: str = "avoid"
    final_confidence: float = 0.0
    warnings: List[str] = None
    last_validated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.last_validated is None:
            self.last_validated = datetime.now()


@dataclass  
class ExtractedToken:
    """Represents an extracted token with metadata (legacy for compatibility)"""
    symbol: str
    address: Optional[str] = None
    name: Optional[str] = None
    source_text: str = ""
    confidence: float = 0.0
    context: str = ""
    extraction_method: str = ""
    verified: bool = False
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'address': self.address,
            'name': self.name,
            'source_text': self.source_text[:200],  # Truncate for storage
            'confidence': self.confidence,
            'context': self.context,
            'extraction_method': self.extraction_method,
            'verified': self.verified,
            'market_cap': self.market_cap,
            'volume_24h': self.volume_24h,
            'price': self.price
        }


class TokenExtractor:
    """
    Intelligent token extraction and discovery system
    """
    
    # Known Solana token patterns
    SOLANA_ADDRESS_PATTERN = re.compile(
        r'\b[A-Za-z0-9]{43,44}\b'  # Solana addresses are typically 43-44 characters
    )
    
    # Token symbol patterns
    TOKEN_SYMBOL_PATTERNS = [
        re.compile(r'\$([A-Z]{2,10})\b'),  # $SYMBOL format
        re.compile(r'\b([A-Z]{2,10})\s+token\b', re.IGNORECASE),  # SYMBOL token
        re.compile(r'\b([A-Z]{2,10})\s+coin\b', re.IGNORECASE),   # SYMBOL coin
        re.compile(r'\b([A-Z]{2,10})\s+(?:price|trading|launch)\b', re.IGNORECASE)
    ]
    
    # Context indicators for better extraction
    CRYPTO_CONTEXTS = {
        'trading': [
            'trading', 'buy', 'sell', 'price', 'pump', 'dump', 'volume',
            'market cap', 'liquidity', 'dex', 'exchange'
        ],
        'launch': [
            'launch', 'airdrop', 'presale', 'ico', 'ido', 'mint', 'release',
            'debut', 'new token', 'listing'
        ],
        'news': [
            'announces', 'partnership', 'integration', 'upgrade', 'development',
            'milestone', 'adoption', 'investment'
        ],
        'defi': [
            'yield', 'farming', 'staking', 'liquidity pool', 'amm', 'dex',
            'defi', 'protocol', 'tvl'
        ]
    }
    
    # Known major tokens to avoid false positives
    MAJOR_TOKENS = {
        'BTC', 'ETH', 'SOL', 'USDC', 'USDT', 'BNB', 'ADA', 'DOT', 'AVAX',
        'MATIC', 'LINK', 'UNI', 'ATOM', 'XRP', 'LUNA', 'NEAR', 'FTT'
    }
    
    # Common false positive patterns
    FALSE_POSITIVE_PATTERNS = [
        re.compile(r'\b(?:USD|EUR|GBP|JPY|CAD|AUD)\b'),  # Fiat currencies
        re.compile(r'\b(?:AM|PM|EST|PST|GMT|UTC)\b'),     # Time zones
        re.compile(r'\b(?:CEO|CTO|CMO|COO|CFO)\b'),       # Job titles
        re.compile(r'\b(?:API|URL|HTML|JSON|XML)\b'),     # Technical terms
    ]
    
    def __init__(self, 
                 solana_client: Optional[object] = None,
                 token_validator: Optional[object] = None,
                 liquidity_analyzer: Optional[object] = None,  
                 rug_detector: Optional[object] = None,
                 checkpoint_file: str = "data/token_extractor.json"):
        """
        Initialize Enhanced Token Discovery System
        
        Args:
            solana_client: Solana client for address validation
            token_validator: Token validator for legitimacy verification
            liquidity_analyzer: Liquidity analyzer for trading feasibility
            rug_detector: Rug pull detector for risk assessment
            checkpoint_file: File to store extraction state
        """
        self.solana_client = solana_client
        self.token_validator = token_validator
        self.liquidity_analyzer = liquidity_analyzer
        self.rug_detector = rug_detector
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load previous state
        self.state = load_checkpoint(checkpoint_file, {
            'known_tokens': {},
            'verified_addresses': set(),
            'false_positives': set(),
            'extraction_stats': {
                'total_extractions': 0,
                'verified_tokens': 0,
                'false_positives': 0
            }
        })
        
        # Convert sets back from lists (JSON serialization)
        if isinstance(self.state['verified_addresses'], list):
            self.state['verified_addresses'] = set(self.state['verified_addresses'])
        if isinstance(self.state['false_positives'], list):
            self.state['false_positives'] = set(self.state['false_positives'])
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """
        Validate if string is a valid Solana address format
        
        Args:
            address: Potential Solana address
            
        Returns:
            True if valid format
        """
        if len(address) < 32 or len(address) > 44:
            return False
        
        # Check for valid base58 characters only
        valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
        return all(c in valid_chars for c in address)
    
    def _detect_context(self, text: str) -> List[str]:
        """
        Detect crypto/trading context in text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected contexts
        """
        text_lower = text.lower()
        detected_contexts = []
        
        for context_type, keywords in self.CRYPTO_CONTEXTS.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_contexts.append(context_type)
        
        return detected_contexts
    
    def _calculate_confidence(self, 
                            symbol: str, 
                            context: List[str], 
                            source_indicators: Dict) -> float:
        """
        Calculate confidence score for extracted token
        
        Args:
            symbol: Token symbol
            context: Detected contexts
            source_indicators: Additional indicators
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.0
        
        # Base confidence from symbol length and format
        if 2 <= len(symbol) <= 6:
            confidence += 0.3
        elif len(symbol) <= 10:
            confidence += 0.2
        
        # Context bonuses
        context_bonus = {
            'trading': 0.3,
            'launch': 0.4,
            'defi': 0.3,
            'news': 0.2
        }
        
        for ctx in context:
            confidence += context_bonus.get(ctx, 0.1)
        
        # Symbol format bonuses
        if source_indicators.get('dollar_sign'):
            confidence += 0.2  # $SYMBOL format
        
        if source_indicators.get('explicit_token_mention'):
            confidence += 0.2  # "SYMBOL token" format
        
        # Penalty for major tokens (likely not new opportunities)
        if symbol in self.MAJOR_TOKENS:
            confidence *= 0.3
        
        # Penalty for known false positives
        if symbol in self.state['false_positives']:
            confidence *= 0.1
        
        # Bonus for previously verified tokens
        if symbol in self.state['known_tokens']:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _is_false_positive(self, symbol: str, context_text: str) -> bool:
        """
        Check if extracted symbol is likely a false positive
        
        Args:
            symbol: Token symbol to check
            context_text: Surrounding text context
            
        Returns:
            True if likely false positive
        """
        # Check against false positive patterns
        for pattern in self.FALSE_POSITIVE_PATTERNS:
            if pattern.search(context_text):
                return True
        
        # Common non-crypto abbreviations
        non_crypto_terms = {
            'USA', 'UK', 'EU', 'AI', 'ML', 'DL', 'AR', 'VR', 'IoT', 'SaaS',
            'B2B', 'B2C', 'P2P', 'KYC', 'AML', 'SEC', 'FDA', 'FBI', 'CIA'
        }
        
        if symbol in non_crypto_terms:
            return True
        
        # Check if appears in non-crypto context
        context_lower = context_text.lower()
        non_crypto_contexts = [
            'government', 'politics', 'election', 'military', 'weather',
            'sports', 'entertainment', 'movie', 'book', 'music'
        ]
        
        if any(ctx in context_lower for ctx in non_crypto_contexts):
            return True
        
        return False
    
    def extract_from_text(self, text: str, source: str = "unknown") -> List[ExtractedToken]:
        """
        Extract token symbols and addresses from text
        
        Args:
            text: Text to extract tokens from
            source: Source of the text for context
            
        Returns:
            List of extracted tokens
        """
        if not text or len(text.strip()) < 20:
            return []
        
        extracted_tokens = []
        text_lower = text.lower()
        
        # Detect overall context
        contexts = self._detect_context(text)
        
        # Extract Solana addresses
        potential_addresses = self.SOLANA_ADDRESS_PATTERN.findall(text)
        for address in potential_addresses:
            if self._is_valid_solana_address(address):
                # Get context around the address
                start = max(0, text.find(address) - 50)
                end = min(len(text), text.find(address) + len(address) + 50)
                context_text = text[start:end]
                
                token = ExtractedToken(
                    symbol=address[:8] + "...",  # Shortened display
                    address=address,
                    source_text=context_text,
                    confidence=0.8,  # High confidence for addresses
                    context=", ".join(contexts),
                    extraction_method="address_pattern",
                    verified=address in self.state['verified_addresses']
                )
                
                extracted_tokens.append(token)
        
        # Extract token symbols using various patterns
        for i, pattern in enumerate(self.TOKEN_SYMBOL_PATTERNS):
            matches = pattern.finditer(text)
            
            for match in matches:
                symbol = match.group(1).upper()
                
                # Get context around the match
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context_text = text[start:end]
                
                # Skip if likely false positive
                if self._is_false_positive(symbol, context_text):
                    continue
                
                # Skip very short or very long symbols
                if len(symbol) < 2 or len(symbol) > 10:
                    continue
                
                # Determine source indicators
                source_indicators = {
                    'dollar_sign': i == 0,  # First pattern is $SYMBOL
                    'explicit_token_mention': 'token' in match.group(0).lower() or 'coin' in match.group(0).lower()
                }
                
                confidence = self._calculate_confidence(symbol, contexts, source_indicators)
                
                # Skip low confidence extractions
                if confidence < 0.2:
                    continue
                
                # Check if already extracted
                if any(t.symbol == symbol for t in extracted_tokens):
                    continue
                
                token = ExtractedToken(
                    symbol=symbol,
                    source_text=context_text,
                    confidence=confidence,
                    context=", ".join(contexts),
                    extraction_method=f"pattern_{i}",
                    verified=symbol in self.state['known_tokens']
                )
                
                # Add known token info if available
                if symbol in self.state['known_tokens']:
                    known_info = self.state['known_tokens'][symbol]
                    token.address = known_info.get('address')
                    token.name = known_info.get('name')
                
                extracted_tokens.append(token)
        
        # Sort by confidence
        extracted_tokens.sort(key=lambda x: x.confidence, reverse=True)
        
        # Update stats
        self.state['extraction_stats']['total_extractions'] += len(extracted_tokens)
        
        self.logger.info(f"Extracted {len(extracted_tokens)} tokens from {source}")
        
        return extracted_tokens[:20]  # Return top 20 tokens
    
    async def validate_extracted_token(self, token: ExtractedToken, social_data: Optional[Dict] = None) -> ValidatedToken:
        """
        Perform comprehensive validation on an extracted token
        
        Args:
            token: Extracted token to validate
            social_data: Optional social sentiment data for correlation analysis
            
        Returns:
            Fully validated token with comprehensive analysis
        """
        self.logger.info(f"Validating extracted token: {token.symbol}")
        
        # Initialize validated token with extracted data
        validated_token = ValidatedToken(
            symbol=token.symbol,
            address=token.address,
            name=token.name,
            source_text=token.source_text,
            extraction_confidence=token.confidence,
            context=token.context,
            extraction_method=token.extraction_method,
        )
        
        warnings = []
        
        try:
            # Step 1: Token legitimacy validation
            if self.token_validator and token.address:
                try:
                    validation_result = await self.token_validator.validate_token(token.address)
                    
                    validated_token.is_validated = True
                    validated_token.validation_status = validation_result.status.value
                    
                    if validation_result.security_analysis:
                        validated_token.security_score = validation_result.security_analysis.security_score
                    
                    if validation_result.metadata:
                        validated_token.name = validated_token.name or validation_result.metadata.name
                        validated_token.address = validated_token.address or validation_result.metadata.address
                    
                    # Collect validation warnings
                    if validation_result.validation_warnings:
                        warnings.extend(validation_result.validation_warnings)
                    
                    self.logger.info(f"Token validation complete: {validation_result.status.value}")
                    
                except Exception as e:
                    self.logger.error(f"Token validation failed: {e}")
                    warnings.append(f"Token validation failed: {str(e)}")
                    validated_token.validation_status = "failed"
            else:
                warnings.append("Token validation not available")
            
            # Step 2: Liquidity analysis
            if self.liquidity_analyzer and token.address:
                try:
                    liquidity_metrics = await self.liquidity_analyzer.analyze_token_liquidity(token.address)
                    
                    validated_token.liquidity_tier = liquidity_metrics.liquidity_tier.value
                    validated_token.total_liquidity_usd = liquidity_metrics.total_liquidity_usd
                    
                    # Generate trading recommendation
                    trading_rec = self.liquidity_analyzer.generate_trading_recommendation(liquidity_metrics)
                    validated_token.trading_feasibility = trading_rec.feasibility.value
                    
                    # Update market data
                    if liquidity_metrics.best_pools:
                        best_pool = liquidity_metrics.best_pools[0]
                        validated_token.volume_24h = best_pool.volume_24h
                        validated_token.price = best_pool.price
                        validated_token.market_cap = best_pool.tvl_usd * 10  # Rough estimate
                    
                    # Collect liquidity warnings
                    warnings.extend(trading_rec.warnings)
                    
                    self.logger.info(f"Liquidity analysis complete: {liquidity_metrics.liquidity_tier.value}")
                    
                except Exception as e:
                    self.logger.error(f"Liquidity analysis failed: {e}")
                    warnings.append(f"Liquidity analysis failed: {str(e)}")
                    validated_token.liquidity_tier = "unknown"
            else:
                warnings.append("Liquidity analysis not available")
            
            # Step 3: Rug pull risk analysis
            if self.rug_detector and token.address:
                try:
                    rug_analysis = await self.rug_detector.analyze_rug_risk(token.address, social_data)
                    
                    validated_token.rug_risk_level = rug_analysis.risk_level.name
                    validated_token.rug_detection_status = rug_analysis.detection_status.value
                    validated_token.overall_risk_score = rug_analysis.overall_risk_score
                    
                    # Collect rug pull warnings
                    warnings.extend(rug_analysis.red_flags)
                    
                    self.logger.info(f"Rug pull analysis complete: {rug_analysis.detection_status.value}")
                    
                except Exception as e:
                    self.logger.error(f"Rug pull analysis failed: {e}")
                    warnings.append(f"Rug pull analysis failed: {str(e)}")
                    validated_token.rug_risk_level = "VERY_HIGH"
                    validated_token.rug_detection_status = "analysis_failed"
            else:
                warnings.append("Rug pull analysis not available")
                validated_token.overall_risk_score = 0.8  # High risk without analysis
            
            # Step 4: Generate final trading recommendation
            validated_token.trading_recommendation = self._generate_final_recommendation(validated_token)
            
            # Step 5: Calculate final confidence score
            validated_token.final_confidence = self._calculate_final_confidence(validated_token)
            
            # Step 6: Set warnings
            validated_token.warnings = warnings[:10]  # Limit to top 10 warnings
            
            validated_token.last_validated = datetime.now()
            
            self.logger.info(f"Token validation pipeline complete for {token.symbol}: {validated_token.trading_recommendation}")
            
            return validated_token
            
        except Exception as e:
            self.logger.error(f"Error in validation pipeline for {token.symbol}: {e}")
            
            # Return failed validation
            validated_token.warnings = [f"Validation pipeline failed: {str(e)}"]
            validated_token.trading_recommendation = "avoid"
            validated_token.final_confidence = 0.0
            validated_token.overall_risk_score = 1.0
            
            return validated_token
    
    def _generate_final_recommendation(self, token: ValidatedToken) -> str:
        """
        Generate final trading recommendation based on all analyses
        
        Args:
            token: Validated token with all analysis results
            
        Returns:
            Final trading recommendation
        """
        # High-level risk check
        if token.rug_detection_status in ["likely_rug", "confirmed_rug"]:
            return "avoid_rug_detected"
        elif token.rug_detection_status == "high_risk":
            return "avoid_high_risk"
        elif token.validation_status == "invalid":
            return "avoid_invalid_token"
        
        # Risk-based assessment
        risk_score = token.overall_risk_score
        
        if risk_score >= 0.8:
            return "avoid_very_high_risk"
        elif risk_score >= 0.6:
            return "avoid_high_risk"
        elif risk_score >= 0.4:
            # Check liquidity for moderate risk tokens
            if token.liquidity_tier in ["very_high", "high"]:
                return "caution_moderate_risk_good_liquidity"
            elif token.liquidity_tier == "moderate":
                return "caution_moderate_risk"
            else:
                return "avoid_poor_liquidity"
        elif risk_score >= 0.2:
            # Low risk - check liquidity and feasibility
            if token.trading_feasibility in ["excellent", "good"]:
                return "trade_low_risk_good_liquidity"
            elif token.trading_feasibility == "fair":
                return "trade_low_risk_fair_liquidity"
            else:
                return "caution_poor_liquidity"
        else:
            # Very low risk - generally good to trade
            if token.trading_feasibility in ["excellent", "good", "fair"]:
                return "trade_very_low_risk"
            else:
                return "caution_liquidity_check_needed"
    
    def _calculate_final_confidence(self, token: ValidatedToken) -> float:
        """
        Calculate final confidence score based on all analyses
        
        Args:
            token: Validated token
            
        Returns:
            Final confidence score (0.0 to 1.0)
        """
        confidence = 0.0
        
        # Base extraction confidence
        confidence += token.extraction_confidence * 0.2
        
        # Validation confidence
        if token.is_validated:
            confidence += 0.2
            if token.validation_status == "verified":
                confidence += 0.1
        
        # Security score contribution
        confidence += token.security_score * 0.2
        
        # Liquidity analysis contribution
        if token.liquidity_tier != "unknown":
            confidence += 0.1
            liquidity_bonus = {
                "very_high": 0.2,
                "high": 0.15,
                "moderate": 0.1,
                "low": 0.05,
                "very_low": 0.0
            }
            confidence += liquidity_bonus.get(token.liquidity_tier, 0.0)
        
        # Rug analysis contribution
        if token.rug_detection_status != "unknown":
            confidence += 0.1
            # Bonus for completed analysis
            if token.rug_detection_status not in ["analysis_failed", "unknown"]:
                confidence += 0.05
        
        # Penalty for warnings
        warning_penalty = min(len(token.warnings) * 0.02, 0.2)  # Max 20% penalty
        confidence -= warning_penalty
        
        return max(0.0, min(confidence, 1.0))
    
    async def discover_and_validate_tokens(self, 
                                         text: str, 
                                         source: str = "unknown",
                                         social_data: Optional[Dict] = None,
                                         validation_enabled: bool = True) -> List[ValidatedToken]:
        """
        Complete token discovery and validation pipeline
        
        Args:
            text: Text to extract tokens from
            source: Source of the text
            social_data: Optional social sentiment data
            validation_enabled: Whether to run full validation pipeline
            
        Returns:
            List of fully validated tokens
        """
        self.logger.info(f"Starting token discovery and validation for source: {source}")
        
        # Step 1: Extract tokens
        extracted_tokens = self.extract_from_text(text, source)
        
        if not extracted_tokens:
            self.logger.info("No tokens extracted")
            return []
        
        # Step 2: Validate tokens if enabled
        if validation_enabled:
            validated_tokens = []
            
            for token in extracted_tokens[:5]:  # Limit to top 5 for performance
                try:
                    validated_token = await self.validate_extracted_token(token, social_data)
                    validated_tokens.append(validated_token)
                    
                    # Small delay to avoid overwhelming APIs
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error validating token {token.symbol}: {e}")
                    continue
            
            # Sort by final confidence
            validated_tokens.sort(key=lambda x: x.final_confidence, reverse=True)
            
            self.logger.info(f"Validation complete: {len(validated_tokens)} tokens validated")
            return validated_tokens
        
        else:
            # Convert ExtractedTokens to ValidatedTokens without validation
            validated_tokens = []
            for token in extracted_tokens:
                validated_token = ValidatedToken(
                    symbol=token.symbol,
                    address=token.address,
                    name=token.name,
                    source_text=token.source_text,
                    extraction_confidence=token.confidence,
                    context=token.context,
                    extraction_method=token.extraction_method,
                    final_confidence=token.confidence,
                    trading_recommendation="validation_disabled",
                    warnings=["Validation pipeline disabled"]
                )
                validated_tokens.append(validated_token)
            
            return validated_tokens
    
    async def batch_validate_tokens(self, tokens: List[ExtractedToken]) -> List[ValidatedToken]:
        """
        Validate multiple tokens in batch
        
        Args:
            tokens: List of extracted tokens to validate
            
        Returns:
            List of validated tokens
        """
        validated_tokens = []
        
        # Process in smaller batches to manage API rate limits
        batch_size = 3
        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i + batch_size]
            
            tasks = [self.validate_extracted_token(token) for token in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for token, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error validating {token.symbol}: {result}")
                    # Create failed validation
                    failed_token = ValidatedToken(
                        symbol=token.symbol,
                        address=token.address,
                        extraction_confidence=token.confidence,
                        trading_recommendation="validation_failed",
                        final_confidence=0.0,
                        warnings=[f"Validation failed: {str(result)}"]
                    )
                    validated_tokens.append(failed_token)
                else:
                    validated_tokens.append(result)
            
            # Delay between batches
            if i + batch_size < len(tokens):
                await asyncio.sleep(2)
        
        return validated_tokens
    
    async def verify_token_address(self, address: str) -> Optional[Dict]:
        """
        Verify token address on Solana blockchain
        
        Args:
            address: Token address to verify
            
        Returns:
            Token metadata if valid, None otherwise
        """
        if not self.solana_client or not address:
            return None
        
        try:
            # This would use the Solana client to get token metadata
            # For now, we'll simulate the verification
            
            # In a real implementation, you would:
            # 1. Check if address exists on blockchain
            # 2. Get token metadata (name, symbol, supply)
            # 3. Check if it's a valid SPL token
            
            # Simulated response
            if self._is_valid_solana_address(address):
                return {
                    'address': address,
                    'name': f"Token_{address[:8]}",
                    'symbol': f"TK{address[:4]}",
                    'decimals': 6,
                    'supply': 1000000,
                    'verified': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error verifying token address {address}: {e}")
            return None
    
    async def enrich_tokens_with_market_data(self, tokens: List[ExtractedToken]) -> List[ExtractedToken]:
        """
        Enrich extracted tokens with market data
        
        Args:
            tokens: List of extracted tokens
            
        Returns:
            Tokens with market data
        """
        # This would integrate with price APIs like Jupiter, Birdeye, etc.
        # For now, we'll simulate market data enrichment
        
        for token in tokens:
            try:
                if token.address:
                    # Simulate market data fetch
                    # In reality, you'd call Jupiter API or similar
                    token.market_cap = 1000000.0  # Simulated
                    token.volume_24h = 50000.0    # Simulated
                    token.price = 0.001           # Simulated
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                self.logger.warning(f"Failed to get market data for {token.symbol}: {e}")
        
        return tokens
    
    def update_token_database(self, tokens: List[ExtractedToken]):
        """
        Update internal token database with extracted tokens
        
        Args:
            tokens: List of verified tokens
        """
        for token in tokens:
            if token.verified and token.confidence > 0.5:
                self.state['known_tokens'][token.symbol] = {
                    'address': token.address,
                    'name': token.name,
                    'last_seen': datetime.now().isoformat(),
                    'confidence': token.confidence
                }
                
                if token.address:
                    self.state['verified_addresses'].add(token.address)
                
                self.state['extraction_stats']['verified_tokens'] += 1
        
        self._save_state()
    
    def mark_false_positive(self, symbol: str):
        """
        Mark a symbol as false positive
        
        Args:
            symbol: Symbol to mark as false positive
        """
        self.state['false_positives'].add(symbol.upper())
        self.state['extraction_stats']['false_positives'] += 1
        self._save_state()
        
        self.logger.info(f"Marked {symbol} as false positive")
    
    def get_extraction_stats(self) -> Dict:
        """
        Get extraction statistics
        
        Returns:
            Statistics dictionary
        """
        stats = self.state['extraction_stats'].copy()
        stats['known_tokens'] = len(self.state['known_tokens'])
        stats['verified_addresses'] = len(self.state['verified_addresses'])
        stats['false_positives'] = len(self.state['false_positives'])
        
        if stats['total_extractions'] > 0:
            stats['accuracy'] = stats['verified_tokens'] / stats['total_extractions']
        else:
            stats['accuracy'] = 0.0
        
        return stats
    
    def _save_state(self):
        """Save current state to checkpoint"""
        # Convert sets to lists for JSON serialization
        state_to_save = self.state.copy()
        state_to_save['verified_addresses'] = list(self.state['verified_addresses'])
        state_to_save['false_positives'] = list(self.state['false_positives'])
        
        save_checkpoint(self.checkpoint_file, state_to_save)


# Example usage and testing
async def test_token_extractor():
    """Test the token extraction system"""
    
    extractor = TokenExtractor()
    
    # Test texts
    test_texts = [
        "$BONK surges 50% after major exchange listing announcement on Solana",
        "New DeFi protocol ORCA launches liquidity mining with 200% APY",
        "Jupiter (JUP) token airdrop creates buzz in Solana ecosystem",
        "Warning: SCAM token at address 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU might be rug pull",
        "Raydium protocol TVL reaches $500M milestone amid SOL rally",
        "The SEC announced new regulations for crypto trading in USA",  # Should detect false positive
    ]
    
    print("🔍 Testing Token Extraction System")
    print("=" * 50)
    
    all_tokens = []
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: {text[:60]}...")
        
        tokens = extractor.extract_from_text(text, f"test_source_{i}")
        
        if tokens:
            for token in tokens:
                print(f"   🪙 {token.symbol}")
                print(f"      Confidence: {token.confidence:.3f}")
                print(f"      Context: {token.context}")
                print(f"      Method: {token.extraction_method}")
                if token.address:
                    print(f"      Address: {token.address[:20]}...")
                all_tokens.append(token)
        else:
            print("   No tokens extracted")
    
    print(f"\n📊 Extraction Summary:")
    stats = extractor.get_extraction_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Token extraction testing complete!")
    
    return all_tokens


if __name__ == "__main__":
    asyncio.run(test_token_extractor())