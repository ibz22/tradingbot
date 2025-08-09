from solana_trading.paper_trading.simulator import PaperSimulator

def test_paper_trade_flow():
    sim = PaperSimulator(initial_sol=10.0)
    start = sim.get_balance("SOL")
    res = sim.apply_fill(src="SOL", dst="USDC", src_qty=0.1, dst_qty=20.0, fee_sol=0.000005, slippage_bps=50)
    assert res.ok and sim.get_balance("USDC") == 20.0
    assert sim.get_balance("SOL") == start - 0.100005
