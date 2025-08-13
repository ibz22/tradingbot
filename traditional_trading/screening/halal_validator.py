"""
Halal Compliance Validator
==========================

Validates stocks for Shariah compliance based on AAOIFI standards.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class HalalValidator:
    """Validates stocks for halal compliance"""
    
    # Prohibited business activities
    HARAM_INDUSTRIES = {
        'Alcoholic Beverages', 'Tobacco', 'Gambling', 'Adult Entertainment',
        'Pork Products', 'Weapons & Defense', 'Conventional Banking',
        'Conventional Insurance', 'Entertainment (Haram)', 'Cannabis'
    }
    
    # Industries requiring careful review
    QUESTIONABLE_INDUSTRIES = {
        'Hotels & Resorts', 'Restaurants', 'Media', 'Entertainment',
        'Financial Services', 'Real Estate'
    }
    
    def __init__(self):
        """Initialize halal validator with AAOIFI standards"""
        # AAOIFI Financial Screening Thresholds
        self.thresholds = {
            'interest_income_ratio': 0.05,  # Max 5% of total income
            'interest_bearing_debt_ratio': 0.30,  # Max 30% of market cap
            'interest_bearing_deposits_ratio': 0.30,  # Max 30% of market cap
            'impure_income_ratio': 0.05,  # Max 5% of total income
            'total_debt_ratio': 0.33,  # Max 33% of total assets
            'liquid_assets_ratio': 0.70,  # Max 70% liquid assets
            'receivables_ratio': 0.49  # Max 49% accounts receivables
        }
    
    async def validate_stock(
        self, 
        symbol: str, 
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate stock for halal compliance
        
        Args:
            symbol: Stock ticker symbol
            financial_data: Financial data from screening
            
        Returns:
            Validation results with compliance status
        """
        results = {
            'symbol': symbol,
            'compliant': True,
            'business_screening': {},
            'financial_screening': {},
            'issues': [],
            'purification_required': False,
            'purification_percentage': 0.0
        }
        
        # Business activity screening
        business_result = self._screen_business_activity(financial_data)
        results['business_screening'] = business_result
        
        if not business_result['passed']:
            results['compliant'] = False
            results['issues'].extend(business_result['issues'])
        
        # Financial ratios screening
        financial_result = self._screen_financial_ratios(financial_data)
        results['financial_screening'] = financial_result
        
        if not financial_result['passed']:
            results['compliant'] = False
            results['issues'].extend(financial_result['issues'])
        
        # Calculate purification if needed
        if results['compliant'] and financial_result.get('interest_income_ratio', 0) > 0:
            results['purification_required'] = True
            results['purification_percentage'] = financial_result['interest_income_ratio'] * 100
        
        return results
    
    def _screen_business_activity(self, financial_data: Dict) -> Dict[str, Any]:
        """Screen for prohibited business activities"""
        result = {
            'passed': True,
            'industry': '',
            'sector': '',
            'issues': []
        }
        
        profile = financial_data.get('profile', {})
        industry = profile.get('industry', 'Unknown')
        sector = profile.get('sector', 'Unknown')
        
        result['industry'] = industry
        result['sector'] = sector
        
        # Check for explicitly haram industries
        if industry in self.HARAM_INDUSTRIES:
            result['passed'] = False
            result['issues'].append(f"Prohibited industry: {industry}")
        
        # Check for questionable industries that need deeper review
        if industry in self.QUESTIONABLE_INDUSTRIES:
            result['issues'].append(f"Industry requires detailed review: {industry}")
            # Would need more detailed analysis of revenue sources
        
        # Special cases
        if 'bank' in industry.lower() or 'insurance' in industry.lower():
            if 'islamic' not in profile.get('companyName', '').lower():
                result['passed'] = False
                result['issues'].append(f"Conventional financial services: {industry}")
        
        return result
    
    def _screen_financial_ratios(self, financial_data: Dict) -> Dict[str, Any]:
        """Screen financial ratios for compliance"""
        result = {
            'passed': True,
            'ratios': {},
            'issues': []
        }
        
        income = financial_data.get('income_statement', {})
        balance = financial_data.get('balance_sheet', {})
        profile = financial_data.get('profile', {})
        
        # Get financial values
        total_revenue = income.get('revenue', 0)
        interest_income = income.get('interestIncome', 0) + income.get('interestExpense', 0)
        total_assets = balance.get('totalAssets', 1)  # Avoid division by zero
        total_debt = balance.get('totalDebt', 0)
        cash = balance.get('cashAndCashEquivalents', 0)
        short_term_investments = balance.get('shortTermInvestments', 0)
        receivables = balance.get('netReceivables', 0)
        
        # Calculate market cap (rough estimate)
        price = profile.get('price', 0)
        shares = balance.get('commonStock', 0) / max(price, 1) if price > 0 else 0
        market_cap = price * shares if shares > 0 else total_assets
        
        # 1. Interest Income Ratio
        if total_revenue > 0:
            interest_income_ratio = abs(interest_income) / total_revenue
            result['ratios']['interest_income_ratio'] = interest_income_ratio
            result['interest_income_ratio'] = interest_income_ratio
            
            if interest_income_ratio > self.thresholds['interest_income_ratio']:
                result['passed'] = False
                result['issues'].append(
                    f"Interest income ratio {interest_income_ratio:.1%} exceeds {self.thresholds['interest_income_ratio']:.0%}"
                )
        
        # 2. Debt Ratio
        debt_ratio = total_debt / total_assets if total_assets > 0 else 0
        result['ratios']['debt_ratio'] = debt_ratio
        
        if debt_ratio > self.thresholds['total_debt_ratio']:
            result['passed'] = False
            result['issues'].append(
                f"Debt ratio {debt_ratio:.1%} exceeds {self.thresholds['total_debt_ratio']:.0%}"
            )
        
        # 3. Liquid Assets Ratio
        liquid_assets = cash + short_term_investments
        liquid_ratio = liquid_assets / total_assets if total_assets > 0 else 0
        result['ratios']['liquid_ratio'] = liquid_ratio
        
        if liquid_ratio > self.thresholds['liquid_assets_ratio']:
            result['issues'].append(
                f"High liquid assets ratio {liquid_ratio:.1%} may indicate interest-bearing deposits"
            )
        
        # 4. Receivables Ratio
        receivables_ratio = receivables / total_assets if total_assets > 0 else 0
        result['ratios']['receivables_ratio'] = receivables_ratio
        
        if receivables_ratio > self.thresholds['receivables_ratio']:
            result['issues'].append(
                f"Receivables ratio {receivables_ratio:.1%} exceeds {self.thresholds['receivables_ratio']:.0%}"
            )
        
        return result
    
    def is_halal_etf(self, symbol: str) -> bool:
        """Check if ETF is halal compliant"""
        # Known halal ETFs
        halal_etfs = {
            'SPUS',  # SP Funds S&P 500 Sharia Industry Exclusions ETF
            'SPRE',  # SP Funds S&P Global REIT Sharia ETF
            'SPSK',  # SP Funds Dow Jones Global Sukuk ETF
            'HLAL',  # Wahed FTSE USA Shariah ETF
            'UMMA',  # Wahed Dow Jones Islamic World ETF
            'WSHR',  # Wahed S&P Sharia ETF
        }
        
        return symbol in halal_etfs
    
    def get_halal_universe(self) -> List[str]:
        """Get list of commonly halal-compliant stocks"""
        # This is a sample list - in production, this would be dynamically maintained
        return [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC',
            # Healthcare
            'JNJ', 'PFE', 'ABBV', 'TMO', 'ABT', 'MDT',
            # Consumer
            'PG', 'KO', 'PEP', 'NKE', 'SBUX', 'MCD',
            # Industrial
            'CAT', 'BA', 'HON', 'MMM', 'GE',
            # Commodities
            'GLD', 'SLV', 'USO', 'GDX',
            # Retail
            'WMT', 'COST', 'TGT', 'HD', 'LOW'
        ]