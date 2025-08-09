from typing import Dict, Any

class JupiterAggregator:
    async def quote(self, src_mint: str, dst_mint: str, amount: int) -> Dict[str, Any]:
        # TODO: call Jupiter API/SDK
        return {"in": amount, "out": int(amount*0.99), "route": []}

    async def swap(self, route: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: build+simulate tx; execute in paper mode
        return {"ok": True, "tx_sig": "stub"}
