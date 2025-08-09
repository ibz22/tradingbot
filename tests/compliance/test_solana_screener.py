from solana_trading.compliance.defi_screener import SolanaDeFiScreener

def test_protocol_and_token_screening():
    s = SolanaDeFiScreener()
    proto = s.screen_protocol("StubProtocol")
    token = s.screen_token("StubMint")
    assert proto["allowed"] is True
    assert token["allowed"] is True
