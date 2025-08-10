import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class JupiterQuote:
    input_mint: str
    in_amount: str
    output_mint: str
    out_amount: str
    other_amount_threshold: str
    swap_mode: str
    slippage_bps: int
    price_impact_pct: float
    route_plan: List[Dict[str, Any]]

@dataclass
class JupiterSwapResult:
    transaction: str
    last_valid_block_height: int

class JupiterAggregator:
    """Jupiter DEX Aggregator client for Solana token swaps"""
    
    def __init__(self, base_url: str = "https://quote-api.jup.ag/v6", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def quote(self, src_mint: str, dst_mint: str, amount: int, slippage_bps: int = 50) -> Dict[str, Any]:
        """Get quote for token swap from Jupiter API
        
        Args:
            src_mint: Source token mint address
            dst_mint: Destination token mint address  
            amount: Amount to swap (in smallest unit)
            slippage_bps: Slippage tolerance in basis points (default 50 = 0.5%)
            
        Returns:
            Dict containing quote data including route, amounts, and price impact
        """
        session = await self._get_session()
        
        params = {
            "inputMint": src_mint,
            "outputMint": dst_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
            "swapMode": "ExactIn"
        }
        
        try:
            async with session.get(f"{self.base_url}/quote", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Jupiter quote failed with status {response.status}: {error_text}")
                
                data = await response.json()
                
                # Parse and validate the quote response
                if "outAmount" not in data:
                    raise ValueError("Invalid quote response: missing outAmount")
                
                logger.info(f"Jupiter quote: {amount} {src_mint} -> {data['outAmount']} {dst_mint}")
                
                return {
                    "inputMint": data["inputMint"],
                    "inAmount": data["inAmount"], 
                    "outputMint": data["outputMint"],
                    "outAmount": data["outAmount"],
                    "otherAmountThreshold": data["otherAmountThreshold"],
                    "swapMode": data["swapMode"],
                    "slippageBps": data["slippageBps"],
                    "priceImpactPct": float(data.get("priceImpactPct", 0)),
                    "routePlan": data["routePlan"],
                    "contextSlot": data.get("contextSlot"),
                    "timeTaken": data.get("timeTaken")
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting Jupiter quote: {e}")
            raise ConnectionError(f"Failed to get Jupiter quote: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Jupiter: {e}")
            raise ValueError(f"Invalid response from Jupiter API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter quote: {e}")
            raise

    async def get_swap_transaction(self, quote: Dict[str, Any], user_public_key: str, 
                                   wrap_unwrap_sol: bool = True, 
                                   compute_unit_price_micro_lamports: Optional[int] = None) -> Dict[str, Any]:
        """Get swap transaction from Jupiter API
        
        Args:
            quote: Quote object from quote() method
            user_public_key: User's wallet public key
            wrap_unwrap_sol: Whether to wrap/unwrap SOL automatically
            compute_unit_price_micro_lamports: Compute unit price for priority fees
            
        Returns:
            Dict containing serialized transaction and metadata
        """
        session = await self._get_session()
        
        request_body = {
            "quoteResponse": quote,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": wrap_unwrap_sol
        }
        
        if compute_unit_price_micro_lamports is not None:
            request_body["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
        
        try:
            async with session.post(f"{self.base_url}/swap", json=request_body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Jupiter swap transaction failed with status {response.status}: {error_text}")
                
                data = await response.json()
                
                if "swapTransaction" not in data:
                    raise ValueError("Invalid swap response: missing swapTransaction")
                
                logger.info("Successfully created Jupiter swap transaction")
                
                return {
                    "swapTransaction": data["swapTransaction"],
                    "lastValidBlockHeight": data.get("lastValidBlockHeight"),
                    "prioritizationFeeLamports": data.get("prioritizationFeeLamports")
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting Jupiter swap transaction: {e}")
            raise ConnectionError(f"Failed to get Jupiter swap transaction: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Jupiter swap: {e}")
            raise ValueError(f"Invalid response from Jupiter swap API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter swap transaction: {e}")
            raise

    async def swap(self, src_mint: str, dst_mint: str, amount: int, user_public_key: str, 
                   slippage_bps: int = 50) -> Dict[str, Any]:
        """Complete swap flow: get quote and create transaction
        
        Args:
            src_mint: Source token mint address
            dst_mint: Destination token mint address
            amount: Amount to swap (in smallest unit)
            user_public_key: User's wallet public key
            slippage_bps: Slippage tolerance in basis points
            
        Returns:
            Dict containing quote data and serialized transaction
        """
        try:
            # Get quote first
            quote = await self.quote(src_mint, dst_mint, amount, slippage_bps)
            
            # Get swap transaction
            swap_data = await self.get_swap_transaction(quote, user_public_key)
            
            return {
                "quote": quote,
                "swapTransaction": swap_data["swapTransaction"],
                "lastValidBlockHeight": swap_data.get("lastValidBlockHeight"),
                "prioritizationFeeLamports": swap_data.get("prioritizationFeeLamports")
            }
            
        except Exception as e:
            logger.error(f"Jupiter swap failed: {e}")
            raise

    async def get_tokens(self) -> List[Dict[str, Any]]:
        """Get list of tokens supported by Jupiter
        
        Returns:
            List of token metadata
        """
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/tokens") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Failed to get Jupiter tokens with status {response.status}: {error_text}")
                
                tokens = await response.json()
                logger.info(f"Retrieved {len(tokens)} tokens from Jupiter")
                return tokens
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting Jupiter tokens: {e}")
            raise ConnectionError(f"Failed to get Jupiter tokens: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Jupiter tokens: {e}")
            raise ValueError(f"Invalid response from Jupiter tokens API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter tokens: {e}")
            raise

    async def get_indexed_route_map(self) -> Dict[str, Any]:
        """Get indexed route map showing available trading pairs
        
        Returns:
            Dict mapping input tokens to list of possible output tokens
        """
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/indexed-route-map") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Failed to get route map with status {response.status}: {error_text}")
                
                route_map = await response.json()
                logger.info("Retrieved Jupiter indexed route map")
                return route_map
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting Jupiter route map: {e}")
            raise ConnectionError(f"Failed to get Jupiter route map: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Jupiter route map: {e}")
            raise ValueError(f"Invalid response from Jupiter route map API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter route map: {e}")
            raise

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Jupiter client session closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
