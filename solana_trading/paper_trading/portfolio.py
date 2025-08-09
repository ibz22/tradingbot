class VirtualPortfolio:
    def __init__(self):
        self.holdings = {}

    def set(self, symbol: str, qty: float):
        self.holdings[symbol] = qty

    def get(self, symbol: str) -> float:
        return self.holdings.get(symbol, 0.0)
