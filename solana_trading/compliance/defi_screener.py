from typing import Dict, Any

class SolanaDeFiScreener:
    def screen_protocol(self, protocol_address: str) -> Dict[str, Any]:
        # Rules:
        # - ❌ interest-based lending / perpetuals / gambling
        # - ✅ spot AMMs (case-by-case on LP risk)
        return {"address": protocol_address, "allowed": True, "reasons": []}

    def screen_token(self, token_mint: str) -> Dict[str, Any]:
        # Minimal stub; Claude expands: business activity, revenue, governance
        return {"mint": token_mint, "allowed": True, "flags": []}
