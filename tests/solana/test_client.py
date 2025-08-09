import pytest
from solana_trading.core.client import SolanaClient

@pytest.mark.asyncio
async def test_connect_and_balance():
    c = SolanaClient("https://api.mainnet-beta.solana.com")
    assert await c.connect() is True
    assert await c.is_connected() is True
    bal = await c.get_balance("StubPubkey")
    assert isinstance(bal, int) and bal > 0
