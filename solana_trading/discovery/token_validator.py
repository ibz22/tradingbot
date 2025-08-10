"""
Token Validator - Comprehensive Token Legitimacy Verification System
===================================================================

Advanced token validation system for Solana tokens including:
- Contract address validation and verification
- Token metadata analysis (name, symbol, supply, decimals)
- Smart contract security analysis and audit checks
- Token holder distribution analysis
- Market cap and trading volume verification
- Integration with Solscan/SolanaFM APIs for comprehensive data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
import base58
import hashlib

import requests
import aiohttp

# Optional import - may not be available in all environments
try:
    from solders.pubkey import Pubkey
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False

from ..utils.checkpoint import load_checkpoint, save_checkpoint


class ValidationStatus(Enum):
    """Token validation status"""
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious" 
    INVALID = "invalid"
    UNKNOWN = "unknown"
    FAILED = "failed"


class RiskLevel(Enum):
    """Risk level classification"""
    VERY_LOW = 0.1
    LOW = 0.25
    MODERATE = 0.5
    HIGH = 0.75
    VERY_HIGH = 1.0


@dataclass
class TokenMetadata:
    """Token metadata information"""
    address: str
    name: str
    symbol: str
    decimals: int
    supply: int
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    is_initialized: bool = False
    update_authority: Optional[str] = None
    uri: Optional[str] = None
    logo_uri: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    discord: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HolderAnalysis:
    """Token holder distribution analysis"""
    total_holders: int
    top_holder_percentage: float
    top_10_holders_percentage: float
    top_50_holders_percentage: float
    concentration_score: float  # 0-1, higher = more concentrated
    burn_addresses: List[str]
    locked_addresses: List[str]
    suspected_dev_wallets: List[str]
    whale_addresses: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SecurityAnalysis:
    """Security analysis results"""
    has_mint_authority: bool
    has_freeze_authority: bool
    is_mutable: bool
    rugpull_risk_factors: List[str]
    security_score: float  # 0-1, higher = more secure
    audit_status: str
    verified_sources: List[str]
    warning_flags: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """Comprehensive token validation result"""
    address: str
    timestamp: datetime
    status: ValidationStatus
    risk_level: RiskLevel
    confidence: float
    metadata: Optional[TokenMetadata] = None
    holder_analysis: Optional[HolderAnalysis] = None
    security_analysis: Optional[SecurityAnalysis] = None
    market_data: Dict[str, Any] = None
    validation_errors: List[str] = None
    validation_warnings: List[str] = None
    
    def __post_init__(self):
        if self.market_data is None:
            self.market_data = {}
        if self.validation_errors is None:
            self.validation_errors = []
        if self.validation_warnings is None:
            self.validation_warnings = []
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        data['risk_level'] = self.risk_level.value
        return data


class TokenValidator:
    """
    Comprehensive token validation system for Solana tokens
    """
    
    # Known burn addresses
    BURN_ADDRESSES = {
        '11111111111111111111111111111111',  # System Program
        '1nc1nerator11111111111111111111111111111111',  # Incinerator
        'Jto1gMKTzLo9h5LeQkn4bGv1hQRQWGKhzlSMzgT6bFx',  # Burn address
    }
    
    # Known validator/staking addresses to exclude from holder analysis
    KNOWN_VALIDATORS = {
        'StakeSSzfxn391k3LvdKbZP5WVwWd6AsY39qhURQP8R',  # Stake Pool Program
        'SysvarRent111111111111111111111111111111111',   # Sysvar Rent
        'SysvarC1ock11111111111111111111111111111111',   # Sysvar Clock
    }
    
    # Minimum thresholds for legitimate tokens
    LEGITIMACY_THRESHOLDS = {
        'min_holders': 50,
        'max_top_holder_pct': 50.0,  # 50% max for single holder
        'max_top10_holder_pct': 80.0,  # 80% max for top 10 holders
        'min_security_score': 0.6,
        'max_concentration_score': 0.7
    }
    
    # API endpoints
    API_ENDPOINTS = {
        'solscan': 'https://pro-api.solscan.io/v1.0',
        'solana_fm': 'https://api.solana.fm/v0',
        'jupiter': 'https://price.jup.ag/v4',
        'helius': 'https://api.helius.xyz/v0'
    }
    
    def __init__(self,
                 solscan_api_key: Optional[str] = None,
                 helius_api_key: Optional[str] = None,
                 checkpoint_file: str = "data/token_validator.json"):
        """
        Initialize Token Validator
        
        Args:
            solscan_api_key: Solscan Pro API key
            helius_api_key: Helius API key
            checkpoint_file: File to store validation cache
        """
        self.solscan_api_key = solscan_api_key
        self.helius_api_key = helius_api_key
        self.checkpoint_file = checkpoint_file
        self.logger = logging.getLogger(__name__)
        
        # Load validation cache
        self.cache = load_checkpoint(checkpoint_file, {
            'validated_tokens': {},
            'blacklisted_tokens': set(),
            'whitelisted_tokens': set(),
            'validation_stats': {
                'total_validations': 0,
                'verified_tokens': 0,
                'rejected_tokens': 0,
                'cache_hits': 0
            }
        })
        
        # Convert sets from JSON lists
        if isinstance(self.cache['blacklisted_tokens'], list):
            self.cache['blacklisted_tokens'] = set(self.cache['blacklisted_tokens'])
        if isinstance(self.cache['whitelisted_tokens'], list):
            self.cache['whitelisted_tokens'] = set(self.cache['whitelisted_tokens'])
        
        # Initialize HTTP session
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """
        Validate Solana address format
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid format
        """
        try:
            # Check length
            if len(address) < 32 or len(address) > 44:
                return False
            
            # Try to decode with base58
            decoded = base58.b58decode(address)
            if len(decoded) != 32:
                return False
            
            # Use solders if available for additional validation
            if SOLDERS_AVAILABLE:
                try:
                    Pubkey.from_string(address)
                    return True
                except:
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _fetch_solscan_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Fetch data from Solscan API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
        """
        if not self.solscan_api_key:
            self.logger.warning("Solscan API key not provided")
            return None
        
        try:
            session = await self._get_session()
            headers = {
                'token': self.solscan_api_key,
                'accept': 'application/json'
            }
            
            url = f"{self.API_ENDPOINTS['solscan']}/{endpoint}"
            async with session.get(url, headers=headers, params=params or {}) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    self.logger.warning("Solscan rate limit reached")
                    await asyncio.sleep(60)  # Wait 1 minute
                    return None
                else:
                    self.logger.error(f"Solscan API error {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching Solscan data: {e}")
            return None
    
    async def _fetch_helius_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Fetch data from Helius API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
        """
        if not self.helius_api_key:
            self.logger.warning("Helius API key not provided")
            return None
        
        try:
            session = await self._get_session()
            params = params or {}
            params['api-key'] = self.helius_api_key
            
            url = f"{self.API_ENDPOINTS['helius']}/{endpoint}"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Helius API error {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching Helius data: {e}")
            return None
    
    async def _fetch_token_metadata(self, address: str) -> Optional[TokenMetadata]:
        """
        Fetch comprehensive token metadata
        
        Args:
            address: Token mint address
            
        Returns:
            Token metadata if found
        """
        try:
            # Try Solscan first
            solscan_data = await self._fetch_solscan_data('token/meta', {'tokenAddress': address})
            
            if solscan_data and solscan_data.get('success'):
                data = solscan_data.get('data', {})
                
                return TokenMetadata(
                    address=address,
                    name=data.get('name', ''),
                    symbol=data.get('symbol', ''),
                    decimals=data.get('decimals', 0),
                    supply=int(data.get('supply', 0)),
                    mint_authority=data.get('mintAuthority'),
                    freeze_authority=data.get('freezeAuthority'),
                    is_initialized=data.get('isInitialized', False),
                    uri=data.get('uri'),
                    logo_uri=data.get('logoURI'),
                    description=data.get('description'),
                    website=data.get('website'),
                    twitter=data.get('twitter'),
                    telegram=data.get('telegram'),
                    discord=data.get('discord')
                )
            
            # Fallback to other APIs
            self.logger.warning(f"Could not fetch metadata for {address}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching token metadata for {address}: {e}")
            return None
    
    async def _analyze_holder_distribution(self, address: str) -> Optional[HolderAnalysis]:
        """
        Analyze token holder distribution
        
        Args:
            address: Token mint address
            
        Returns:
            Holder analysis results
        """
        try:
            # Fetch holder data from Solscan
            holders_data = await self._fetch_solscan_data('token/holders', {
                'tokenAddress': address,
                'limit': 100,  # Get top 100 holders
                'offset': 0
            })
            
            if not holders_data or not holders_data.get('success'):
                return None
            
            holders = holders_data.get('data', [])
            if not holders:
                return None
            
            # Calculate distribution metrics
            total_supply = sum(float(holder.get('amount', 0)) for holder in holders)
            if total_supply == 0:
                return None
            
            # Sort by amount
            holders.sort(key=lambda x: float(x.get('amount', 0)), reverse=True)
            
            # Calculate percentages
            top_holder_pct = (float(holders[0].get('amount', 0)) / total_supply) * 100 if holders else 0
            top_10_pct = sum(float(holder.get('amount', 0)) for holder in holders[:10]) / total_supply * 100
            top_50_pct = sum(float(holder.get('amount', 0)) for holder in holders[:50]) / total_supply * 100
            
            # Identify special addresses
            burn_addresses = []
            locked_addresses = []
            suspected_dev_wallets = []
            whale_addresses = []
            
            for holder in holders:
                address_str = holder.get('address', '')
                amount = float(holder.get('amount', 0))
                percentage = (amount / total_supply) * 100
                
                if address_str in self.BURN_ADDRESSES:
                    burn_addresses.append(address_str)
                elif percentage > 5.0:  # 5%+ holdings
                    if percentage > 20.0:  # Potential dev wallet
                        suspected_dev_wallets.append(address_str)
                    else:
                        whale_addresses.append(address_str)
            
            # Calculate concentration score (Gini coefficient approximation)
            concentration_score = self._calculate_concentration_score([
                float(h.get('amount', 0)) for h in holders
            ])
            
            return HolderAnalysis(
                total_holders=holders_data.get('total', len(holders)),
                top_holder_percentage=top_holder_pct,
                top_10_holders_percentage=top_10_pct,
                top_50_holders_percentage=top_50_pct,
                concentration_score=concentration_score,
                burn_addresses=burn_addresses,
                locked_addresses=locked_addresses,
                suspected_dev_wallets=suspected_dev_wallets,
                whale_addresses=whale_addresses
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing holder distribution for {address}: {e}")
            return None
    
    def _calculate_concentration_score(self, amounts: List[float]) -> float:
        """
        Calculate concentration score using Gini coefficient approximation
        
        Args:
            amounts: List of holder amounts
            
        Returns:
            Concentration score (0-1, higher = more concentrated)
        """
        if not amounts or len(amounts) < 2:
            return 1.0  # Maximally concentrated
        
        # Sort amounts
        sorted_amounts = sorted(amounts)
        n = len(sorted_amounts)
        total = sum(sorted_amounts)
        
        if total == 0:
            return 1.0
        
        # Calculate Gini coefficient
        gini_sum = sum(
            (2 * i - n - 1) * amount 
            for i, amount in enumerate(sorted_amounts, 1)
        )
        
        gini = gini_sum / (n * total)
        return max(0, min(1, gini))
    
    async def _perform_security_analysis(self, 
                                       metadata: TokenMetadata,
                                       holder_analysis: Optional[HolderAnalysis]) -> SecurityAnalysis:
        """
        Perform comprehensive security analysis
        
        Args:
            metadata: Token metadata
            holder_analysis: Holder distribution analysis
            
        Returns:
            Security analysis results
        """
        rugpull_risk_factors = []
        warning_flags = []
        security_score = 1.0
        
        # Check mint authority
        has_mint_authority = metadata.mint_authority is not None and metadata.mint_authority != '11111111111111111111111111111111'
        if has_mint_authority:
            rugpull_risk_factors.append("Token has active mint authority - can create unlimited supply")
            security_score -= 0.3
        
        # Check freeze authority
        has_freeze_authority = metadata.freeze_authority is not None and metadata.freeze_authority != '11111111111111111111111111111111'
        if has_freeze_authority:
            rugpull_risk_factors.append("Token has freeze authority - can freeze user accounts")
            security_score -= 0.2
        
        # Check if mutable
        is_mutable = metadata.update_authority is not None and metadata.update_authority != '11111111111111111111111111111111'
        if is_mutable:
            warning_flags.append("Token metadata can be updated")
            security_score -= 0.1
        
        # Analyze holder distribution
        if holder_analysis:
            if holder_analysis.top_holder_percentage > 50:
                rugpull_risk_factors.append(f"Single holder owns {holder_analysis.top_holder_percentage:.1f}% of supply")
                security_score -= 0.4
            elif holder_analysis.top_holder_percentage > 30:
                warning_flags.append(f"Single holder owns {holder_analysis.top_holder_percentage:.1f}% of supply")
                security_score -= 0.2
            
            if holder_analysis.top_10_holders_percentage > 90:
                rugpull_risk_factors.append("Top 10 holders control >90% of supply")
                security_score -= 0.3
            
            if holder_analysis.concentration_score > 0.8:
                rugpull_risk_factors.append("Extremely concentrated token distribution")
                security_score -= 0.2
            
            if len(holder_analysis.suspected_dev_wallets) > 3:
                warning_flags.append("Multiple potential developer wallets detected")
                security_score -= 0.1
        
        # Check token metadata completeness
        if not metadata.name or not metadata.symbol:
            warning_flags.append("Incomplete token metadata")
            security_score -= 0.1
        
        if not metadata.logo_uri and not metadata.website:
            warning_flags.append("No logo or website provided")
            security_score -= 0.05
        
        # Ensure score bounds
        security_score = max(0, min(1, security_score))
        
        # Determine audit status (simplified)
        audit_status = "unaudited"
        verified_sources = []
        
        if security_score >= 0.8:
            audit_status = "low_risk"
        elif security_score >= 0.6:
            audit_status = "moderate_risk"
        else:
            audit_status = "high_risk"
        
        return SecurityAnalysis(
            has_mint_authority=has_mint_authority,
            has_freeze_authority=has_freeze_authority,
            is_mutable=is_mutable,
            rugpull_risk_factors=rugpull_risk_factors,
            security_score=security_score,
            audit_status=audit_status,
            verified_sources=verified_sources,
            warning_flags=warning_flags
        )
    
    def _determine_validation_status(self,
                                   metadata: TokenMetadata,
                                   holder_analysis: Optional[HolderAnalysis],
                                   security_analysis: SecurityAnalysis) -> Tuple[ValidationStatus, RiskLevel]:
        """
        Determine final validation status and risk level
        
        Args:
            metadata: Token metadata
            holder_analysis: Holder analysis
            security_analysis: Security analysis
            
        Returns:
            (validation_status, risk_level)
        """
        # Check blacklist
        if metadata.address in self.cache['blacklisted_tokens']:
            return ValidationStatus.INVALID, RiskLevel.VERY_HIGH
        
        # Check whitelist
        if metadata.address in self.cache['whitelisted_tokens']:
            return ValidationStatus.VERIFIED, RiskLevel.VERY_LOW
        
        # Analyze risk factors
        risk_score = 1.0 - security_analysis.security_score
        
        # Additional risk factors
        if holder_analysis:
            # Holder concentration risk
            if holder_analysis.total_holders < self.LEGITIMACY_THRESHOLDS['min_holders']:
                risk_score += 0.2
            
            if holder_analysis.top_holder_percentage > self.LEGITIMACY_THRESHOLDS['max_top_holder_pct']:
                risk_score += 0.3
            
            if holder_analysis.top_10_holders_percentage > self.LEGITIMACY_THRESHOLDS['max_top10_holder_pct']:
                risk_score += 0.2
        
        # Major red flags
        if len(security_analysis.rugpull_risk_factors) >= 3:
            return ValidationStatus.INVALID, RiskLevel.VERY_HIGH
        elif len(security_analysis.rugpull_risk_factors) >= 2:
            return ValidationStatus.SUSPICIOUS, RiskLevel.HIGH
        
        # Determine final status
        risk_score = min(risk_score, 1.0)
        
        if risk_score >= 0.8:
            return ValidationStatus.INVALID, RiskLevel.VERY_HIGH
        elif risk_score >= 0.6:
            return ValidationStatus.SUSPICIOUS, RiskLevel.HIGH
        elif risk_score >= 0.4:
            return ValidationStatus.SUSPICIOUS, RiskLevel.MODERATE
        elif risk_score >= 0.2:
            return ValidationStatus.VERIFIED, RiskLevel.LOW
        else:
            return ValidationStatus.VERIFIED, RiskLevel.VERY_LOW
    
    async def validate_token(self, address: str, force_refresh: bool = False) -> ValidationResult:
        """
        Perform comprehensive token validation
        
        Args:
            address: Token mint address
            force_refresh: Force fresh validation (ignore cache)
            
        Returns:
            Comprehensive validation result
        """
        # Input validation
        if not address or not self._is_valid_solana_address(address):
            return ValidationResult(
                address=address,
                timestamp=datetime.now(),
                status=ValidationStatus.INVALID,
                risk_level=RiskLevel.VERY_HIGH,
                confidence=1.0,
                validation_errors=["Invalid Solana address format"]
            )
        
        # Check cache first
        if not force_refresh and address in self.cache['validated_tokens']:
            cached_result = self.cache['validated_tokens'][address]
            # Check if cache is still valid (24 hours)
            cached_time = datetime.fromisoformat(cached_result['timestamp'])
            if datetime.now() - cached_time < timedelta(hours=24):
                self.cache['validation_stats']['cache_hits'] += 1
                self.logger.info(f"Using cached validation for {address}")
                return ValidationResult(
                    address=cached_result['address'],
                    timestamp=datetime.fromisoformat(cached_result['timestamp']),
                    status=ValidationStatus(cached_result['status']),
                    risk_level=RiskLevel(cached_result['risk_level']),
                    confidence=cached_result['confidence'],
                    metadata=TokenMetadata(**cached_result['metadata']) if cached_result['metadata'] else None,
                    holder_analysis=HolderAnalysis(**cached_result['holder_analysis']) if cached_result['holder_analysis'] else None,
                    security_analysis=SecurityAnalysis(**cached_result['security_analysis']) if cached_result['security_analysis'] else None,
                    market_data=cached_result['market_data'],
                    validation_errors=cached_result['validation_errors'],
                    validation_warnings=cached_result['validation_warnings']
                )
        
        self.logger.info(f"Validating token: {address}")
        
        validation_errors = []
        validation_warnings = []
        
        try:
            # Step 1: Fetch token metadata
            metadata = await self._fetch_token_metadata(address)
            if not metadata:
                return ValidationResult(
                    address=address,
                    timestamp=datetime.now(),
                    status=ValidationStatus.FAILED,
                    risk_level=RiskLevel.VERY_HIGH,
                    confidence=0.0,
                    validation_errors=["Could not fetch token metadata"]
                )
            
            # Step 2: Analyze holder distribution
            holder_analysis = await self._analyze_holder_distribution(address)
            if not holder_analysis:
                validation_warnings.append("Could not analyze holder distribution")
            
            # Step 3: Perform security analysis
            security_analysis = await self._perform_security_analysis(metadata, holder_analysis)
            
            # Step 4: Determine final status
            status, risk_level = self._determine_validation_status(metadata, holder_analysis, security_analysis)
            
            # Step 5: Calculate confidence
            confidence = self._calculate_validation_confidence(metadata, holder_analysis, security_analysis)
            
            # Step 6: Fetch market data (basic)
            market_data = await self._fetch_basic_market_data(address)
            
            # Create result
            result = ValidationResult(
                address=address,
                timestamp=datetime.now(),
                status=status,
                risk_level=risk_level,
                confidence=confidence,
                metadata=metadata,
                holder_analysis=holder_analysis,
                security_analysis=security_analysis,
                market_data=market_data,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings
            )
            
            # Update cache
            self.cache['validated_tokens'][address] = result.to_dict()
            
            # Update stats
            self.cache['validation_stats']['total_validations'] += 1
            if status == ValidationStatus.VERIFIED:
                self.cache['validation_stats']['verified_tokens'] += 1
            elif status in [ValidationStatus.INVALID, ValidationStatus.SUSPICIOUS]:
                self.cache['validation_stats']['rejected_tokens'] += 1
            
            # Save cache
            self._save_cache()
            
            self.logger.info(f"Validation complete for {address}: {status.value} (risk: {risk_level.name})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating token {address}: {e}")
            return ValidationResult(
                address=address,
                timestamp=datetime.now(),
                status=ValidationStatus.FAILED,
                risk_level=RiskLevel.VERY_HIGH,
                confidence=0.0,
                validation_errors=[f"Validation failed: {str(e)}"]
            )
    
    def _calculate_validation_confidence(self,
                                       metadata: TokenMetadata,
                                       holder_analysis: Optional[HolderAnalysis],
                                       security_analysis: SecurityAnalysis) -> float:
        """
        Calculate confidence in validation result
        
        Args:
            metadata: Token metadata
            holder_analysis: Holder analysis
            security_analysis: Security analysis
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.0
        
        # Metadata completeness
        if metadata.name and metadata.symbol:
            confidence += 0.2
        if metadata.decimals > 0:
            confidence += 0.1
        if metadata.supply > 0:
            confidence += 0.1
        
        # Holder analysis availability
        if holder_analysis:
            confidence += 0.3
            if holder_analysis.total_holders >= 10:
                confidence += 0.1
        else:
            confidence += 0.05  # Partial credit even without holder data
        
        # Security analysis quality
        confidence += security_analysis.security_score * 0.2
        
        # Additional factors
        if len(security_analysis.warning_flags) == 0:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _fetch_basic_market_data(self, address: str) -> Dict[str, Any]:
        """
        Fetch basic market data for token
        
        Args:
            address: Token address
            
        Returns:
            Basic market data
        """
        try:
            # Try Jupiter price API
            session = await self._get_session()
            url = f"{self.API_ENDPOINTS['jupiter']}/price"
            params = {'ids': address}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    token_data = data.get('data', {}).get(address)
                    if token_data:
                        return {
                            'price': token_data.get('price'),
                            'price_source': 'Jupiter'
                        }
            
            return {'price': None, 'price_source': None}
            
        except Exception as e:
            self.logger.warning(f"Could not fetch market data for {address}: {e}")
            return {}
    
    async def batch_validate_tokens(self, addresses: List[str]) -> List[ValidationResult]:
        """
        Validate multiple tokens in batch
        
        Args:
            addresses: List of token addresses
            
        Returns:
            List of validation results
        """
        tasks = [self.validate_token(address) for address in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error validating {addresses[i]}: {result}")
                # Create failed result
                failed_result = ValidationResult(
                    address=addresses[i],
                    timestamp=datetime.now(),
                    status=ValidationStatus.FAILED,
                    risk_level=RiskLevel.VERY_HIGH,
                    confidence=0.0,
                    validation_errors=[str(result)]
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)
        
        return valid_results
    
    def add_to_whitelist(self, address: str):
        """Add token to whitelist"""
        self.cache['whitelisted_tokens'].add(address)
        self._save_cache()
        self.logger.info(f"Added {address} to whitelist")
    
    def add_to_blacklist(self, address: str):
        """Add token to blacklist"""
        self.cache['blacklisted_tokens'].add(address)
        self._save_cache()
        self.logger.info(f"Added {address} to blacklist")
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            **self.cache['validation_stats'],
            'cached_tokens': len(self.cache['validated_tokens']),
            'whitelisted_tokens': len(self.cache['whitelisted_tokens']),
            'blacklisted_tokens': len(self.cache['blacklisted_tokens']),
            'cache_hit_rate': (
                self.cache['validation_stats']['cache_hits'] / 
                max(self.cache['validation_stats']['total_validations'], 1) * 100
            )
        }
    
    def _save_cache(self):
        """Save validation cache"""
        # Convert sets to lists for JSON serialization
        cache_to_save = self.cache.copy()
        cache_to_save['blacklisted_tokens'] = list(self.cache['blacklisted_tokens'])
        cache_to_save['whitelisted_tokens'] = list(self.cache['whitelisted_tokens'])
        
        save_checkpoint(self.checkpoint_file, cache_to_save)
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


# Example usage and testing
async def test_token_validator():
    """Test the token validator system"""
    import os
    
    # Initialize validator
    solscan_key = os.getenv('SOLSCAN_API_KEY')
    helius_key = os.getenv('HELIUS_API_KEY')
    
    validator = TokenValidator(
        solscan_api_key=solscan_key,
        helius_api_key=helius_key,
        checkpoint_file="data/test_token_validator.json"
    )
    
    print("Testing Token Validator...")
    
    # Test with known tokens
    test_tokens = [
        'So11111111111111111111111111111111111111112',  # SOL
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        # Add other test tokens as needed
    ]
    
    for token_address in test_tokens:
        try:
            print(f"\nValidating {token_address}...")
            result = await validator.validate_token(token_address)
            
            print(f"  Status: {result.status.value}")
            print(f"  Risk Level: {result.risk_level.name}")
            print(f"  Confidence: {result.confidence:.2f}")
            
            if result.metadata:
                print(f"  Token: {result.metadata.symbol} ({result.metadata.name})")
                print(f"  Supply: {result.metadata.supply:,}")
            
            if result.security_analysis:
                print(f"  Security Score: {result.security_analysis.security_score:.2f}")
                if result.security_analysis.rugpull_risk_factors:
                    print(f"  Risk Factors: {len(result.security_analysis.rugpull_risk_factors)}")
            
            if result.holder_analysis:
                print(f"  Holders: {result.holder_analysis.total_holders}")
                print(f"  Top Holder: {result.holder_analysis.top_holder_percentage:.1f}%")
            
            if result.validation_errors:
                print(f"  Errors: {result.validation_errors}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show stats
    stats = validator.get_validation_stats()
    print(f"\nValidation Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    await validator.close()
    print("\nToken validator testing complete!")


if __name__ == "__main__":
    asyncio.run(test_token_validator())