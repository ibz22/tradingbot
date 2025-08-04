"""
Basic risk management utilities for the halalbot trading system.

The ``RiskManager`` class encapsulates logic for calculating how many units
of an asset to trade based on the account value, the maximum risk per trade
and the distance to the stop loss.  It also includes helper functions to
aggregate risk across a portfolio of positions.
"""

from __future__ import annotations

from typing import Dict, Optional


class RiskManager:
    """Calculate position sizes and portfolio risk metrics."""

    def __init__(
        self,
        max_portfolio_risk: float = 0.02,
        max_position_risk: float = 0.01,
        max_position_pct: float = 0.1,
    ) -> None:
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_risk = max_position_risk
        self.max_position_pct = max_position_pct

    def calculate_position_size(
        self,
        account_value: float,
        current_price: float,
        stop_price: Optional[float],
    ) -> float:
        """Return the number of units to trade based on risk constraints.

        The position sizing algorithm uses the dollar risk per trade (account
        value multiplied by ``max_position_risk``) divided by the per-share risk
        (the distance between the entry price and the stop loss).  If no stop
        loss is provided the per-share risk defaults to the asset price.
        """
        if account_value <= 0 or current_price <= 0:
            return 0.0
        # Dollar risk allowed for this trade
        risk_amount = account_value * self.max_position_risk
        per_share_risk = (
            abs(current_price - stop_price)
            if stop_price is not None and stop_price > 0
            else current_price
        )
        if per_share_risk <= 0:
            return 0.0
        raw_size = risk_amount / per_share_risk
        # Never allow a position greater than max_position_pct of the account
        max_size = (account_value * self.max_position_pct) / current_price
        return min(raw_size, max_size)

    def calculate_portfolio_risk(self, positions: Dict[str, Dict]) -> Dict[str, float]:
        """Aggregate simple risk metrics across current positions.

        For each position we assume that the dollar value at risk is the
        quantity multiplied by the entry price multiplied by ``max_position_risk``.  The
        concentration risk is measured as the sum of squared weights.  This
        implementation is deliberately straightforward; more sophisticated
        estimators (e.g. VaR, CVaR or correlations) can be plugged in later.
        """
        if not positions:
            return {
                "portfolio_value": 0.0,
                "risk_at_risk": 0.0,
                "concentration_risk": 0.0,
                "number_of_positions": 0,
            }
        total_value = 0.0
        total_risk = 0.0
        weights = {}
        for sym, pos in positions.items():
            value = pos.get("qty", 0) * pos.get("entry_price", 0)
            total_value += value
            total_risk += value * self.max_position_risk
            weights[sym] = value
        # Normalize weights and compute concentration risk
        for sym in weights:
            weights[sym] /= total_value
        concentration_risk = sum(w ** 2 for w in weights.values())
        return {
            "portfolio_value": total_value,
            "risk_at_risk": total_risk,
            "concentration_risk": concentration_risk,
            "number_of_positions": len(positions),
        }
