import pytest

from halalbot.core.risk import RiskManager


def test_calculate_position_size():
    rm = RiskManager(max_position_risk=0.02, max_position_pct=0.1)
    # Account value 1000, price 10, stop at 9 (risk per share = 1)
    size = rm.calculate_position_size(1000, 10, 9)
    # Risk amount = 1000 * 0.02 = 20; per‑share risk = 1; so raw size = 20 shares
    # Max position pct = 0.1 * 1000 / 10 = 10 shares
    assert pytest.approx(size) == 10