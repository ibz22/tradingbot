#!/usr/bin/env python3
# Lean phase validator: fast checks so Claude spends tokens coding, not reading.
import os, sys, importlib

def _exists(path): return os.path.exists(path)

def _can_import(mod):
    try:
        importlib.import_module(mod); return True
    except Exception:
        return False

def validate_phase_1():
    checks = {
        "client_file": _exists("solana_trading/core/client.py"),
        "config_file": _exists("solana_trading/config/solana_config.py"),
        "tests_exist": _exists("tests/solana/test_client.py"),
        "imports_ok": _can_import("solana_trading.core.client")
                     and _can_import("solana_trading.config.solana_config"),
    }
    for k, ok in checks.items():
        if not ok: print(f"❌ {k} missing/failed")
    return all(checks.values())

def validate_phase_2():
    checks = {
        "paper_sim": _exists("solana_trading/paper_trading/simulator.py"),
        "portfolio": _exists("solana_trading/paper_trading/portfolio.py"),
        "jupiter": _exists("solana_trading/defi/jupiter.py"),
        "compliance_tests": _exists("tests/compliance/test_solana_screener.py"),
    }
    for k, ok in checks.items():
        if not ok: print(f"❌ {k} missing/failed")
    return all(checks.values())

def validate_phase_3():
    checks = {
        "raydium": _exists("solana_trading/defi/raydium.py"),
        "orca": _exists("solana_trading/defi/orca.py"),
        "paper_tests": _exists("tests/solana/test_paper_trading.py"),
    }
    for k, ok in checks.items():
        if not ok: print(f"❌ {k} missing/failed")
    return all(checks.values())

if __name__ == "__main__":
    phase = (sys.argv[1] if len(sys.argv) > 1 else "1").strip()
    ok = {"1": validate_phase_1, "2": validate_phase_2, "3": validate_phase_3}.get(phase, validate_phase_1)()
    print(f"✅ Phase {phase}: {\"PASSED\" if ok else \"FAILED\"}")
    sys.exit(0 if ok else 1)
