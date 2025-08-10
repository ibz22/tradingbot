from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
from enum import Enum

class SolanaNetwork(Enum):
    MAINNET = "mainnet-beta"
    TESTNET = "testnet" 
    DEVNET = "devnet"
    LOCALNET = "localnet"

@dataclass
class NetworkConfig:
    """Configuration for different Solana networks"""
    name: str
    rpc_endpoint: str
    websocket_endpoint: Optional[str] = None
    faucet_endpoint: Optional[str] = None
    explorer_url: str = "https://explorer.solana.com"
    
    @classmethod
    def mainnet(cls):
        return cls(
            name="mainnet-beta",
            rpc_endpoint="https://api.mainnet-beta.solana.com",
            websocket_endpoint="wss://api.mainnet-beta.solana.com",
            explorer_url="https://explorer.solana.com"
        )
    
    @classmethod
    def devnet(cls):
        return cls(
            name="devnet", 
            rpc_endpoint="https://api.devnet.solana.com",
            websocket_endpoint="wss://api.devnet.solana.com",
            faucet_endpoint="https://faucet.solana.com",
            explorer_url="https://explorer.solana.com?cluster=devnet"
        )
    
    @classmethod
    def testnet(cls):
        return cls(
            name="testnet",
            rpc_endpoint="https://api.testnet.solana.com", 
            websocket_endpoint="wss://api.testnet.solana.com",
            faucet_endpoint="https://faucet.solana.com",
            explorer_url="https://explorer.solana.com?cluster=testnet"
        )
    
    @classmethod
    def localnet(cls):
        return cls(
            name="localnet",
            rpc_endpoint="http://127.0.0.1:8899",
            websocket_endpoint="ws://127.0.0.1:8900",
            explorer_url="https://explorer.solana.com?cluster=custom&customUrl=http%3A//127.0.0.1%3A8899"
        )

@dataclass
class JupiterConfig:
    """Configuration for Jupiter API"""
    base_url: str = "https://quote-api.jup.ag/v6"
    timeout: float = 30.0
    default_slippage_bps: int = 50
    max_slippage_bps: int = 1000
    enable_wrap_unwrap_sol: bool = True

@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    max_position_size_sol: float = 1.0
    min_trade_amount_sol: float = 0.01
    max_slippage: float = 0.005
    transaction_timeout: float = 60.0
    confirmation_timeout: float = 60.0
    max_retries: int = 3
    priority_fee_lamports: int = 5000

@dataclass
class SolanaConfig:
    # Network settings
    network: NetworkConfig = field(default_factory=NetworkConfig.devnet)
    paper_trading: bool = True
    
    # Wallet settings
    wallet_path: Optional[str] = None
    initial_sol_balance: float = 10.0
    
    # Trading settings  
    trading: TradingConfig = field(default_factory=TradingConfig)
    jupiter: JupiterConfig = field(default_factory=JupiterConfig)
    
    # Token configuration
    supported_tokens: List[str] = field(default_factory=lambda: [
        "So11111111111111111111111111111111111111112",  # SOL (wrapped)
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
        "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  # RAY
        "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE"   # ORCA
    ])
    
    # DeFi protocol configuration
    defi_protocols: Dict[str, bool] = field(default_factory=lambda: {
        "jupiter": True, 
        "raydium": True, 
        "orca": True,
        "serum": False  # Disabled by default
    })
    
    # Compliance and risk settings
    compliance: Dict[str, Any] = field(default_factory=lambda: {
        "enable_defi_screening": True, 
        "max_protocol_risk": 0.02,
        "require_halal_compliance": True,
        "max_leverage": 1.0
    })
    
    # RPC settings
    rpc_timeout: float = 10.0
    rpc_max_retries: int = 3
    rpc_retry_delay: float = 1.0
    
    @classmethod
    def for_network(cls, network: SolanaNetwork, **kwargs):
        """Create config for specific network"""
        network_configs = {
            SolanaNetwork.MAINNET: NetworkConfig.mainnet(),
            SolanaNetwork.DEVNET: NetworkConfig.devnet(), 
            SolanaNetwork.TESTNET: NetworkConfig.testnet(),
            SolanaNetwork.LOCALNET: NetworkConfig.localnet()
        }
        
        config = cls(**kwargs)
        config.network = network_configs[network]
        return config
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        network_name = os.getenv("SOLANA_NETWORK", "devnet").lower()
        paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
        wallet_path = os.getenv("SOLANA_WALLET_PATH")
        
        # Map network name to enum
        network_map = {
            "mainnet": SolanaNetwork.MAINNET,
            "mainnet-beta": SolanaNetwork.MAINNET,
            "devnet": SolanaNetwork.DEVNET,
            "testnet": SolanaNetwork.TESTNET, 
            "localnet": SolanaNetwork.LOCALNET
        }
        
        network = network_map.get(network_name, SolanaNetwork.DEVNET)
        
        config = cls.for_network(
            network=network,
            paper_trading=paper_trading,
            wallet_path=wallet_path
        )
        
        return config
    
    def get_rpc_endpoint(self) -> str:
        """Get the RPC endpoint URL"""
        return self.network.rpc_endpoint
    
    def get_explorer_url(self, signature: Optional[str] = None) -> str:
        """Get explorer URL, optionally for a specific transaction"""
        base_url = self.network.explorer_url
        if signature:
            return f"{base_url}/tx/{signature}"
        return base_url
    
    def is_testnet(self) -> bool:
        """Check if using testnet/devnet"""
        return self.network.name in ["devnet", "testnet", "localnet"]
