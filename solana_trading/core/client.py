import asyncio

class SolanaClient:
    def __init__(self, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
        self._connected = False

    async def connect(self) -> bool:
        # TODO: implement real RPC health check + retries
        await asyncio.sleep(0)
        self._connected = True
        return self._connected

    async def is_connected(self) -> bool:
        return self._connected

    async def get_balance(self, pubkey: str) -> int:
        # TODO: wire to RPC; return lamports
        await asyncio.sleep(0)
        return 1_000_000_000  # 1 SOL (stub)
