from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SolanaConfig:
    rpc_endpoint: str = "https://api.mainnet-beta.solana.com"
    paper_trading: bool = True
    initial_sol_balance: float = 10.0
    max_slippage: float = 0.005
    supported_tokens: List[str] = field(default_factory=lambda: ["SOL", "USDC", "USDT", "RAY", "ORCA"])
    defi_protocols: Dict[str, bool] = field(default_factory=lambda: {"jupiter": True, "raydium": True, "orca": True})
    compliance: Dict[str, Any] = field(default_factory=lambda: {"enable_defi_screening": True, "max_protocol_risk": 0.02})
