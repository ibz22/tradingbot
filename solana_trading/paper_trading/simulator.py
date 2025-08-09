from dataclasses import dataclass
from typing import Dict

@dataclass
class PaperTradeResult:
    ok: bool
    fill_price: float
    fee_lamports: int
    slippage_bps: int

class PaperSimulator:
    def __init__(self, initial_sol: float = 10.0):
        self.balances: Dict[str, float] = {"SOL": initial_sol}

    def get_balance(self, symbol: str) -> float:
        return self.balances.get(symbol, 0.0)

    def apply_fill(self, src: str, dst: str, src_qty: float, dst_qty: float, fee_sol: float, slippage_bps: int) -> PaperTradeResult:
        self.balances[src] = self.get_balance(src) - src_qty - fee_sol
        self.balances[dst] = self.get_balance(dst) + dst_qty
        return PaperTradeResult(True, dst_qty/src_qty if src_qty else 0.0, int(fee_sol*1e9), slippage_bps)
