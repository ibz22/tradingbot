"""
Core Trading System Module
==========================

Phase 1: Core Solana Integration (Complete)

This module provides the fundamental infrastructure for Solana blockchain
interaction, trading execution, and risk management. Forms the foundation
for all higher-level intelligence and trading capabilities.

Components:
    client      - Native Solana RPC client integration
    engine      - Main trading engine orchestration
    risk        - Risk management and position controls
    executor    - Enhanced trade execution with order lifecycle management
    order_mgr   - Comprehensive order tracking and management

Key Features:
    " Native Solana RPC client with error handling
    " Jupiter DEX aggregator integration for optimal routing
    " Real-time transaction monitoring and confirmation
    " Comprehensive risk management with portfolio controls
    " Enhanced order execution with lifecycle tracking
    " Position management with persistence

Performance & Reliability:
    " Enterprise-grade async processing architecture
    " Comprehensive error handling and retry logic
    " State persistence with checkpoint management
    " Production-ready monitoring and logging
    " Real-time position reconciliation

Usage Example:
    from solana_trading.core import SolanaClient, TradingEngine
    
    client = SolanaClient(rpc_url="https://api.mainnet-beta.solana.com")
    engine = TradingEngine(client=client, config=config)
    
    # Execute trades with full risk management
    result = await engine.execute_trade(symbol="SOL", action="buy", amount=1.0)
"""

__version__ = "3.0.0"
__phase__ = "Phase 1 Complete"

# Import core components
try:
    from .client import SolanaClient
    from .engine import TradingEngine
    from .risk import RiskManager
    from .trade_executor import EnhancedTradeExecutor
    from .order_manager import OrderManager
    
    CORE_COMPONENTS_AVAILABLE = True
except ImportError:
    CORE_COMPONENTS_AVAILABLE = False

__all__ = [
    "SolanaClient",
    "TradingEngine", 
    "RiskManager",
    "EnhancedTradeExecutor",
    "OrderManager"
]

# Module metadata
MODULE_INFO = {
    "name": "Core Trading System",
    "version": __version__,
    "phase": __phase__,
    "components_available": CORE_COMPONENTS_AVAILABLE,
    "blockchain": "Solana",
    "key_features": {
        "dex_integration": "Jupiter aggregator",
        "risk_management": "Portfolio-level controls", 
        "order_execution": "Enhanced lifecycle tracking",
        "architecture": "Enterprise-grade async",
        "monitoring": "Real-time position reconciliation"
    }
}