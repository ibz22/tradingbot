# Lean Claude Code Prompt – Solana DeFi Integration

## Objective
Integrate full Solana blockchain + DeFi capabilities into my halal trading bot, including paper trading, halal compliance screening, and live trading.

**Repo:** https://github.com/ibz22/tradingbot  
**Current Bot:** Async Python, modular, config-driven. Alpaca/Binance integration, AAOIFI halal screening, backtesting, ML strategies.  
**Compliance:** Islamic finance rules (no interest/gambling/perpetuals, debt/income ratio checks).

---

## Integration Requirements

### 1. Core Infrastructure
```

solana\_trading/
core/{client.py,wallet.py,transactions.py}
defi/{jupiter.py,raydium.py,orca.py,serum.py}
compliance/{defi\_screener.py,token\_validator.py}
paper\_trading/{simulator.py,portfolio.py}

```

### 2. Dependencies (requirements.txt)
```

solana>=0.30.0
solders>=0.18.0
anchorpy>=0.18.0
jupiter-python-sdk>=1.0.0
websockets>=11.0
aiohttp>=3.8.0

````

### 3. Solana Client
- Connect to mainnet/devnet/testnet
- Phantom/Solflare wallet compatibility
- RPC with retries, read-only + signing modes
- Async only, error handling + rate limits

### 4. DeFi Integrations
- **Jupiter**: swaps, price discovery, routing, slippage/MEV protection
- **Raydium**, **Orca**: AMM + liquidity pools
- **Phoenix/Lifinity**: optional DEX support

### 5. Halal Screening
```python
class SolanaDeFiScreener:
    def screen_protocol(self, protocol_address): ...
    def screen_token(self, token_mint): ...
````

✅ Spot swaps / some LPs
⚠️ Native SOL staking (review)
❌ Lending, perpetuals, gambling

### 6. Paper Trading

* Virtual SOL wallet + starting balance
* Real-time DEX price feeds
* Simulated execution (latency, fees, slippage)
* Portfolio + P\&L tracking

### 7. Bot Integration Hooks

1. Extend `halalbot/core/engine.py` → `execute_trade()`
2. Update `halalbot/config/config_loader.py` for `solana:`
3. Use existing notification, logging, risk mgmt.

### 8. Monitoring & Security

* Network health + liquidity tracking
* Private key encryption, multisig
* Transaction preview/approval for live mode
* Emergency stop

### 9. Testing

* Unit + integration (devnet)
* `tests/compliance/test_solana_screener.py` mock data
* Performance benchmarks

---

## Implementation Phases

**Phase 1:** RPC client, wallet, paper sim, Jupiter swap (testnet milestone)
**Phase 2:** Raydium/Orca, halal screening, feeds, portfolio mgmt
**Phase 3:** Cross-DEX arb, advanced screening, perf opt, full tests

---

## Success Criteria

✅ Solana connection + Jupiter paper trades
✅ Halal compliance enforced
✅ Integrated with current bot
✅ All tests pass

---

## Additional Notes

* **Async/await in every I/O** function
* Follow existing style (Black), docstrings + type hints
* Update `PROGRESS.md` + `CHECKPOINT.json` at end of each phase

---

## Continuation Protocol

Before each session:

```bash
python scripts/validate_progress.py 1
cat PROGRESS.md
python -c "from solana_trading.utils.checkpoint import DevelopmentCheckpoint; print(DevelopmentCheckpoint.load_progress())"
```

Then continue from last `PROGRESS.md` tasks.
Reuse boilerplate from earlier phases to save tokens.
