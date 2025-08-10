import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import RPCResponse
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solders.rpc.responses import GetBalanceResp, GetAccountInfoResp
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class RpcHealth:
    is_healthy: bool
    slot_behind: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None

class SolanaClient:
    def __init__(self, rpc_endpoint: str, max_retries: int = 3, retry_delay: float = 1.0, timeout: float = 10.0):
        self.rpc_endpoint = rpc_endpoint
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._client: Optional[AsyncClient] = None
        self._connected = False
        self._health_check_cache: Optional[RpcHealth] = None
        self._last_health_check = 0.0

    async def connect(self) -> bool:
        """Initialize connection and perform health check with retries"""
        for attempt in range(self.max_retries):
            try:
                if self._client:
                    await self._client.close()
                
                self._client = AsyncClient(
                    self.rpc_endpoint,
                    timeout=self.timeout,
                    commitment=Commitment("confirmed")
                )
                
                # Perform health check
                health = await self._check_rpc_health()
                if health.is_healthy:
                    self._connected = True
                    logger.info(f"Connected to Solana RPC: {self.rpc_endpoint}")
                    return True
                
                logger.warning(f"RPC health check failed (attempt {attempt + 1}/{self.max_retries}): {health.error}")
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        self._connected = False
        return False

    async def is_connected(self) -> bool:
        """Check if client is connected and healthy"""
        if not self._connected or not self._client:
            return False
        
        # Perform periodic health checks (cache for 30 seconds)
        current_time = asyncio.get_event_loop().time()
        if current_time - self._last_health_check > 30.0:
            health = await self._check_rpc_health()
            self._connected = health.is_healthy
        
        return self._connected

    async def get_balance(self, pubkey: str) -> int:
        """Get account balance in lamports with retry logic"""
        if not await self.is_connected():
            raise ConnectionError("RPC client not connected")
        
        for attempt in range(self.max_retries):
            try:
                public_key = PublicKey(pubkey)
                response: RPCResponse[GetBalanceResp] = await self._client.get_balance(public_key)
                
                if response.value is not None:
                    return response.value.value
                else:
                    raise ValueError(f"Failed to get balance for {pubkey}: {response}")
                    
            except Exception as e:
                logger.warning(f"Balance request attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)
        
        raise RuntimeError("Failed to get balance after all retries")

    async def get_account_info(self, pubkey: str) -> Optional[Dict[str, Any]]:
        """Get account info with retry logic"""
        if not await self.is_connected():
            raise ConnectionError("RPC client not connected")
        
        for attempt in range(self.max_retries):
            try:
                public_key = PublicKey(pubkey)
                response: RPCResponse[GetAccountInfoResp] = await self._client.get_account_info(public_key)
                
                if response.value:
                    return {
                        "lamports": response.value.lamports,
                        "owner": str(response.value.owner),
                        "executable": response.value.executable,
                        "rent_epoch": response.value.rent_epoch,
                        "data": response.value.data
                    }
                return None
                    
            except Exception as e:
                logger.warning(f"Account info request attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)
        
        raise RuntimeError("Failed to get account info after all retries")

    async def get_latest_blockhash(self) -> str:
        """Get latest blockhash with retry logic"""
        if not await self.is_connected():
            raise ConnectionError("RPC client not connected")
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.get_latest_blockhash()
                if response.value:
                    return str(response.value.blockhash)
                raise ValueError("Failed to get latest blockhash")
                    
            except Exception as e:
                logger.warning(f"Blockhash request attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)
        
        raise RuntimeError("Failed to get latest blockhash after all retries")

    async def send_transaction(self, transaction_bytes: bytes) -> str:
        """Send transaction with retry logic"""
        if not await self.is_connected():
            raise ConnectionError("RPC client not connected")
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.send_raw_transaction(transaction_bytes)
                if response.value:
                    return str(response.value)
                raise ValueError("Failed to send transaction")
                    
            except Exception as e:
                logger.warning(f"Transaction send attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)
        
        raise RuntimeError("Failed to send transaction after all retries")

    async def get_slot(self) -> int:
        """Get current slot number"""
        if not await self.is_connected():
            raise ConnectionError("RPC client not connected")
        
        response = await self._client.get_slot()
        if response.value is not None:
            return response.value
        raise ValueError("Failed to get current slot")

    async def _check_rpc_health(self) -> RpcHealth:
        """Perform comprehensive RPC health check"""
        import time
        start_time = time.time()
        
        try:
            # Test basic connectivity with getHealth endpoint
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                health_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                async with session.post(self.rpc_endpoint, json=health_payload) as response:
                    if response.status != 200:
                        return RpcHealth(False, error=f"HTTP {response.status}")
                    
                    result = await response.json()
                    if "error" in result:
                        return RpcHealth(False, error=result["error"]["message"])
            
            # Test slot retrieval to ensure RPC is responding properly
            if self._client:
                slot_response = await self._client.get_slot()
                if slot_response.value is None:
                    return RpcHealth(False, error="Failed to get current slot")
            
            response_time = (time.time() - start_time) * 1000
            self._last_health_check = asyncio.get_event_loop().time()
            
            return RpcHealth(
                is_healthy=True,
                response_time_ms=response_time
            )
            
        except asyncio.TimeoutError:
            return RpcHealth(False, error="Request timeout")
        except Exception as e:
            return RpcHealth(False, error=str(e))

    async def close(self):
        """Close the RPC connection"""
        if self._client:
            await self._client.close()
            self._client = None
        self._connected = False
        logger.info("Solana RPC client closed")

    def __del__(self):
        """Cleanup on deletion"""
        if self._client and not self._client.is_closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except:
                pass
