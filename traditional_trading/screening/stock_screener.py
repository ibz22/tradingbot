"""
Stock Screening System
=====================

Advanced stock screening with fundamental analysis and halal compliance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import os

from .halal_validator import HalalValidator

logger = logging.getLogger(__name__)


class StockScreener:
    """Advanced stock screening system with halal compliance"""
    
    def __init__(
        self,
        fmp_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None
    ):
        """
        Initialize stock screener
        
        Args:
            fmp_api_key: Financial Modeling Prep API key
            alpha_vantage_key: Alpha Vantage API key
        """
        self.fmp_api_key = fmp_api_key or os.getenv('FMP_API_KEY')
        self.alpha_vantage_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.halal_validator = HalalValidator()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Cache for screening results
        self.cache: Dict[str, Tuple[Dict, datetime]] = {}
        self.cache_ttl = timedelta(hours=1)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _fetch_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch financial data from FMP"""
        if not self.fmp_api_key:
            logger.warning("FMP API key not configured, using mock data")
            return self._get_mock_financial_data(symbol)
        
        # Check cache
        if symbol in self.cache:
            data, timestamp = self.cache[symbol]
            if datetime.now() - timestamp < self.cache_ttl:
                return data
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Fetch income statement
            income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?apikey={self.fmp_api_key}"
            async with self.session.get(income_url) as response:
                income_data = await response.json() if response.status == 200 else []
            
            # Fetch balance sheet
            balance_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={self.fmp_api_key}"
            async with self.session.get(balance_url) as response:
                balance_data = await response.json() if response.status == 200 else []
            
            # Fetch company profile
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.fmp_api_key}"
            async with self.session.get(profile_url) as response:
                profile_data = await response.json() if response.status == 200 else []
            
            # Fetch key metrics
            metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?apikey={self.fmp_api_key}"
            async with self.session.get(metrics_url) as response:
                metrics_data = await response.json() if response.status == 200 else []
            
            financial_data = {
                'income_statement': income_data[0] if income_data else {},
                'balance_sheet': balance_data[0] if balance_data else {},
                'profile': profile_data[0] if profile_data else {},
                'metrics': metrics_data[0] if metrics_data else {}
            }
            
            # Cache the results
            self.cache[symbol] = (financial_data, datetime.now())
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error fetching financial data for {symbol}: {e}")
            return self._get_mock_financial_data(symbol)
    
    def _get_mock_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Get mock financial data for testing"""
        # Popular stocks with known halal status
        mock_data = {
            'AAPL': {
                'income_statement': {
                    'revenue': 365817000000,
                    'interestIncome': 2825000000,  # ~0.77% of revenue
                    'netIncome': 94680000000
                },
                'balance_sheet': {
                    'totalAssets': 352755000000,
                    'totalDebt': 111088000000,  # ~31.5% debt ratio
                    'cashAndCashEquivalents': 29965000000
                },
                'profile': {
                    'companyName': 'Apple Inc.',
                    'industry': 'Consumer Electronics',
                    'sector': 'Technology',
                    'price': 175.43
                },
                'metrics': {
                    'peRatio': 28.5,
                    'priceToBookRatio': 45.2,
                    'debtToEquity': 1.95
                }
            },
            'MSFT': {
                'income_statement': {
                    'revenue': 211915000000,
                    'interestIncome': 2953000000,  # ~1.4% of revenue
                    'netIncome': 72738000000
                },
                'balance_sheet': {
                    'totalAssets': 411976000000,
                    'totalDebt': 47032000000,  # ~11.4% debt ratio
                    'cashAndCashEquivalents': 111262000000
                },
                'profile': {
                    'companyName': 'Microsoft Corporation',
                    'industry': 'Software',
                    'sector': 'Technology',
                    'price': 380.52
                },
                'metrics': {
                    'peRatio': 35.2,
                    'priceToBookRatio': 15.8,
                    'debtToEquity': 0.47
                }
            },
            'GLD': {
                'income_statement': {'revenue': 0, 'interestIncome': 0, 'netIncome': 0},
                'balance_sheet': {
                    'totalAssets': 65000000000,
                    'totalDebt': 0,
                    'cashAndCashEquivalents': 100000000
                },
                'profile': {
                    'companyName': 'SPDR Gold Shares',
                    'industry': 'Gold ETF',
                    'sector': 'Commodities',
                    'price': 185.20
                },
                'metrics': {'peRatio': 0, 'priceToBookRatio': 1.0, 'debtToEquity': 0}
            }
        }
        
        return mock_data.get(symbol, {
            'income_statement': {},
            'balance_sheet': {},
            'profile': {'companyName': symbol, 'industry': 'Unknown', 'sector': 'Unknown'},
            'metrics': {}
        })
    
    async def screen_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Screen a single stock for trading suitability and halal compliance
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Screening results including halal compliance status
        """
        logger.info(f"Screening {symbol}...")
        
        # Fetch financial data
        financial_data = await self._fetch_financial_data(symbol)
        
        # Perform halal compliance check
        halal_result = await self.halal_validator.validate_stock(symbol, financial_data)
        
        # Calculate fundamental metrics
        metrics = self._calculate_metrics(financial_data)
        
        # Generate screening score
        score = self._calculate_screening_score(metrics, halal_result)
        
        return {
            'symbol': symbol,
            'company_name': financial_data['profile'].get('companyName', symbol),
            'sector': financial_data['profile'].get('sector', 'Unknown'),
            'industry': financial_data['profile'].get('industry', 'Unknown'),
            'halal_compliant': halal_result['compliant'],
            'halal_details': halal_result,
            'metrics': metrics,
            'score': score,
            'recommendation': self._get_recommendation(score, halal_result['compliant']),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_metrics(self, financial_data: Dict) -> Dict[str, Any]:
        """Calculate fundamental metrics"""
        metrics = {}
        
        # Extract data
        income = financial_data.get('income_statement', {})
        balance = financial_data.get('balance_sheet', {})
        key_metrics = financial_data.get('metrics', {})
        
        # Revenue and profitability
        metrics['revenue'] = income.get('revenue', 0)
        metrics['net_income'] = income.get('netIncome', 0)
        metrics['profit_margin'] = (
            metrics['net_income'] / metrics['revenue'] * 100 
            if metrics['revenue'] > 0 else 0
        )
        
        # Balance sheet metrics
        metrics['total_assets'] = balance.get('totalAssets', 0)
        metrics['total_debt'] = balance.get('totalDebt', 0)
        metrics['cash'] = balance.get('cashAndCashEquivalents', 0)
        
        # Valuation metrics
        metrics['pe_ratio'] = key_metrics.get('peRatio', 0)
        metrics['pb_ratio'] = key_metrics.get('priceToBookRatio', 0)
        metrics['debt_to_equity'] = key_metrics.get('debtToEquity', 0)
        
        # Debt ratio for halal screening
        metrics['debt_ratio'] = (
            metrics['total_debt'] / metrics['total_assets'] * 100
            if metrics['total_assets'] > 0 else 0
        )
        
        return metrics
    
    def _calculate_screening_score(self, metrics: Dict, halal_result: Dict) -> float:
        """Calculate overall screening score (0-100)"""
        score = 0.0
        
        # Halal compliance (40% weight)
        if halal_result['compliant']:
            score += 40
        
        # Profitability (20% weight)
        if metrics['profit_margin'] > 10:
            score += 20
        elif metrics['profit_margin'] > 5:
            score += 10
        elif metrics['profit_margin'] > 0:
            score += 5
        
        # Debt levels (20% weight)
        if metrics['debt_ratio'] < 30:
            score += 20
        elif metrics['debt_ratio'] < 50:
            score += 10
        elif metrics['debt_ratio'] < 70:
            score += 5
        
        # Valuation (20% weight)
        if 0 < metrics['pe_ratio'] < 20:
            score += 20
        elif 20 <= metrics['pe_ratio'] < 30:
            score += 10
        elif 30 <= metrics['pe_ratio'] < 40:
            score += 5
        
        return min(100, score)
    
    def _get_recommendation(self, score: float, halal_compliant: bool) -> str:
        """Generate investment recommendation"""
        if not halal_compliant:
            return "NOT_RECOMMENDED_HALAL"
        
        if score >= 70:
            return "STRONG_BUY"
        elif score >= 50:
            return "BUY"
        elif score >= 30:
            return "HOLD"
        else:
            return "AVOID"
    
    async def screen_multiple(
        self, 
        symbols: List[str],
        halal_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Screen multiple stocks
        
        Args:
            symbols: List of stock symbols
            halal_only: Filter for halal compliant stocks only
            
        Returns:
            List of screening results
        """
        tasks = [self.screen_stock(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = [
            r for r in results 
            if not isinstance(r, Exception)
        ]
        
        # Filter for halal if requested
        if halal_only:
            valid_results = [
                r for r in valid_results
                if r['halal_compliant']
            ]
        
        # Sort by score
        valid_results.sort(key=lambda x: x['score'], reverse=True)
        
        return valid_results
    
    async def find_halal_stocks(
        self,
        sector: Optional[str] = None,
        min_score: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Find halal compliant stocks
        
        Args:
            sector: Filter by sector
            min_score: Minimum screening score
            
        Returns:
            List of halal compliant stocks
        """
        # Common halal-friendly stocks to screen
        universe = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN',  # Tech
            'JNJ', 'PFE', 'UNH',  # Healthcare
            'PG', 'KO', 'PEP',  # Consumer
            'GLD', 'SLV',  # Commodities
            'TSLA', 'F', 'GM',  # Auto
            'WMT', 'TGT', 'COST'  # Retail
        ]
        
        results = await self.screen_multiple(universe, halal_only=True)
        
        # Filter by sector if specified
        if sector:
            results = [r for r in results if r['sector'] == sector]
        
        # Filter by minimum score
        results = [r for r in results if r['score'] >= min_score]
        
        return results