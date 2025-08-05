import pandas as pd
import pytest
from halalbot.backtest.engine import BacktestEngine


class DummyStrategy:
    """A trivial strategy that buys on the first bar and holds until the end."""

    def generate_signal(self, data: pd.DataFrame, index: int) -> str:
        return "buy" if index == 0 else "hold"


def test_backtest_buy_and_hold():
    # Create a simple price series
    df = pd.DataFrame({"close": [10, 11, 12, 13, 14]})
    engine = BacktestEngine(initial_capital=1000, slippage_model="fixed_pct", slippage_value=0)
    results = engine.run_backtest(df, DummyStrategy())
    # Should buy 100 shares at 10 and finish with 100 * 14 = 1400
    assert results["final_equity"] == pytest.approx(1400)
