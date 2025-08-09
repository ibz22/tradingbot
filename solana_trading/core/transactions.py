class TransactionBuilder:
    async def build_swap_tx(self, src_mint: str, dst_mint: str, amount: int, slippage_bps: int) -> bytes:
        # TODO: integrate with Jupiter route quote
        return b"TX_STUB"
