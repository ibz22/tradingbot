class Wallet:
    def __init__(self, secret: str | None = None):
        self.secret = secret  # TODO: load keypair securely
        self.pubkey = "StubPubkey"  # TODO: derive from keypair

    async def sign(self, tx_bytes: bytes) -> bytes:
        # TODO: real signing
        return tx_bytes
