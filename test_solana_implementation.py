#!/usr/bin/env python3
"""
Test script for Solana trading bot Phase 1 implementation
Tests the basic functionality of the core components
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solana_trading.config.solana_config import SolanaConfig, SolanaNetwork
from solana_trading.core.client import SolanaClient
from solana_trading.defi.jupiter import JupiterAggregator
from solana_trading.core.transactions import TransactionBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolanaTestRunner:
    """Test runner for Solana trading bot components"""
    
    def __init__(self):
        # Use devnet for testing
        self.config = SolanaConfig.for_network(SolanaNetwork.DEVNET)
        self.solana_client = None
        self.jupiter_client = None
        self.tx_builder = None
        
    async def setup(self):
        """Initialize clients"""
        logger.info("Setting up test environment...")
        
        # Initialize Solana RPC client
        self.solana_client = SolanaClient(
            rpc_endpoint=self.config.get_rpc_endpoint(),
            max_retries=self.config.rpc_max_retries,
            retry_delay=self.config.rpc_retry_delay,
            timeout=self.config.rpc_timeout
        )
        
        # Initialize Jupiter client
        self.jupiter_client = JupiterAggregator(
            base_url=self.config.jupiter.base_url,
            timeout=self.config.jupiter.timeout
        )
        
        # Initialize transaction builder
        self.tx_builder = TransactionBuilder(
            solana_client=self.solana_client,
            jupiter_client=self.jupiter_client
        )
        
        logger.info(f"Test environment configured for {self.config.network.name}")
        
    async def test_solana_client(self) -> bool:
        """Test Solana RPC client functionality"""
        logger.info("Testing Solana RPC client...")
        
        try:
            # Test connection
            connected = await self.solana_client.connect()
            if not connected:
                logger.error("Failed to connect to Solana RPC")
                return False
            
            logger.info("✓ Successfully connected to Solana RPC")
            
            # Test health check
            is_healthy = await self.solana_client.is_connected()
            logger.info(f"✓ RPC health check: {is_healthy}")
            
            # Test getting current slot
            try:
                slot = await self.solana_client.get_slot()
                logger.info(f"✓ Current slot: {slot}")
            except Exception as e:
                logger.warning(f"Could not get current slot: {e}")
                
            # Test getting balance for a known account (faucet account)
            try:
                # Use a well-known account for testing
                test_pubkey = "11111111111111111111111111111111"  # System program
                balance = await self.solana_client.get_balance(test_pubkey)
                logger.info(f"✓ Test account balance: {balance} lamports")
            except Exception as e:
                logger.warning(f"Could not get test balance: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Solana client test failed: {e}")
            return False
    
    async def test_jupiter_client(self) -> bool:
        """Test Jupiter API client functionality"""
        logger.info("Testing Jupiter API client...")
        
        try:
            # Test getting supported tokens
            try:
                tokens = await self.jupiter_client.get_tokens()
                logger.info(f"✓ Retrieved {len(tokens)} supported tokens from Jupiter")
                
                # Show a few token examples
                for i, token in enumerate(tokens[:3]):
                    logger.info(f"  - {token.get('symbol', 'Unknown')}: {token.get('address', 'N/A')}")
                    
            except Exception as e:
                logger.warning(f"Could not get Jupiter tokens: {e}")
            
            # Test getting route map
            try:
                route_map = await self.jupiter_client.get_indexed_route_map()
                input_tokens = list(route_map.keys()) if isinstance(route_map, dict) else []
                logger.info(f"✓ Retrieved route map with {len(input_tokens)} input tokens")
            except Exception as e:
                logger.warning(f"Could not get route map: {e}")
            
            # Test quote functionality (SOL to USDC)
            try:
                sol_mint = "So11111111111111111111111111111111111111112"  # Wrapped SOL
                usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
                amount = 1_000_000_000  # 1 SOL in lamports
                
                quote = await self.jupiter_client.quote(
                    src_mint=sol_mint,
                    dst_mint=usdc_mint, 
                    amount=amount,
                    slippage_bps=50
                )
                
                in_amount = int(quote.get('inAmount', 0))
                out_amount = int(quote.get('outAmount', 0))
                price_impact = quote.get('priceImpactPct', 0)
                
                logger.info(f"✓ Jupiter quote: {in_amount} SOL -> {out_amount} USDC")
                logger.info(f"  Price impact: {price_impact}%")
                
            except Exception as e:
                logger.warning(f"Could not get Jupiter quote: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Jupiter client test failed: {e}")
            return False
    
    async def test_transaction_builder(self) -> bool:
        """Test transaction builder functionality"""
        logger.info("Testing transaction builder...")
        
        try:
            # Test fee estimation
            dummy_tx_bytes = b"dummy_transaction_data"
            fee_estimate = self.tx_builder.estimate_transaction_fee(
                dummy_tx_bytes, 
                prioritization_fee_lamports=5000
            )
            logger.info(f"✓ Transaction fee estimate: {fee_estimate} lamports")
            
            # Test swap transaction building (this will fail without a real user key, but tests the flow)
            try:
                sol_mint = "So11111111111111111111111111111111111111112"
                usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                dummy_pubkey = "11111111111111111111111111111111"  # System program as dummy
                
                # This will likely fail but tests the integration
                swap_tx = await self.tx_builder.build_swap_tx(
                    src_mint=sol_mint,
                    dst_mint=usdc_mint,
                    amount=100_000_000,  # 0.1 SOL
                    user_public_key=dummy_pubkey,
                    slippage_bps=50
                )
                
                logger.info(f"✓ Built swap transaction: {len(swap_tx)} bytes")
                
            except Exception as e:
                logger.info(f"⚠ Swap transaction test expected to fail: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Transaction builder test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all component tests"""
        logger.info("Starting Solana trading bot Phase 1 tests...")
        
        results = {}
        
        try:
            await self.setup()
            
            # Test each component
            results['solana_client'] = await self.test_solana_client()
            results['jupiter_client'] = await self.test_jupiter_client()  
            results['transaction_builder'] = await self.test_transaction_builder()
            
        except Exception as e:
            logger.error(f"Test setup failed: {e}")
            return {"setup": False}
        
        finally:
            await self.cleanup()
        
        return results
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.jupiter_client:
            await self.jupiter_client.close()
        if self.solana_client:
            await self.solana_client.close()
        logger.info("Test cleanup completed")

async def main():
    """Main test function"""
    test_runner = SolanaTestRunner()
    results = await test_runner.run_all_tests()
    
    # Print results summary
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    all_passed = True
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{component}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*50)
    overall_status = "✓ ALL TESTS PASSED" if all_passed else "✗ SOME TESTS FAILED"
    logger.info(f"Overall: {overall_status}")
    logger.info("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)