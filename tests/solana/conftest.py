import pytest

@pytest.fixture
def mock_client():
    class _C:
        async def is_connected(self): return True
        async def get_balance(self, _): return 1_000_000_000
    return _C()

@pytest.fixture
def paper_config():
    return {"initial_sol_balance": 10.0, "max_slippage": 0.005, "supported_tokens": ["SOL","USDC","RAY"]}
