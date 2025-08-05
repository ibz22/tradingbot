"""
An improved halal screener that leverages real financial data via a ``DataGateway``
and configurable AAOIFI thresholds.

This screener retrieves income statements and balance sheet data through the
``data_gateway`` and applies simple ratios to determine whether a stock passes
the halal financial screening criteria.  Thresholds for interest income
percentage and debt ratio can be supplied via the configuration dictionary.

Example
-------
    from halalbot.screening.data_gateway import FMPGateway
    from halalbot.screening.advanced_screener import AdvancedHalalScreener

    gateway = FMPGateway(api_key="demo")
    cfg = {"max_interest_pct": 0.05, "max_debt_ratio": 0.33}
    screener = AdvancedHalalScreener(gateway, cfg)
    result = await screener.is_halal("AAPL")
    print(result)
"""

from __future__ import annotations

from typing import Any, Dict


class AdvancedHalalScreener:
    """Screen stocks for halal compliance using real financial statements."""

    def __init__(self, data_gateway: Any, config: Dict[str, Any]) -> None:
        self.gateway = data_gateway
        self.max_interest_pct = config.get("max_interest_pct", 0.05)
        self.max_debt_ratio = config.get("max_debt_ratio", 0.33)

    async def is_halal(self, ticker: str) -> bool:
        """Return True if the given ticker passes the halal financial screen."""
        statement = await self.gateway.get_statement(ticker)
        if not statement:
            # if we can't retrieve data, be conservative
            return False
        # Extract relevant fields; fall back to zeros if missing
        revenue = float(statement.get("revenue", 0))
        interest_income = float(statement.get("interestIncome", 0))
        total_debt = float(statement.get("totalDebt", 0))
        total_assets = float(statement.get("totalAssets", 0))
        # Avoid division by zero
        if revenue <= 0 or total_assets <= 0:
            return False
        interest_pct = interest_income / revenue
        debt_ratio = total_debt / total_assets
        return interest_pct <= self.max_interest_pct and debt_ratio <= self.max_debt_ratio
