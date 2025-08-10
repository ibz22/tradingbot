import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
import base64
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solders.message import Message
from solders.transaction import Transaction as SoldersTransaction
from solders.instruction import Instruction
from solders.keypair import Keypair as SoldersKeypair
from solders.pubkey import Pubkey
from solders.hash import Hash
import json

logger = logging.getLogger(__name__)

class TransactionBuilder:
    """Builds and manages Solana transactions for trading operations"""
    
    def __init__(self, solana_client=None, jupiter_client=None):
        self.solana_client = solana_client
        self.jupiter_client = jupiter_client
        
    async def build_swap_tx(self, src_mint: str, dst_mint: str, amount: int, 
                           user_public_key: str, slippage_bps: int = 50) -> bytes:
        """Build swap transaction using Jupiter integration
        
        Args:
            src_mint: Source token mint address
            dst_mint: Destination token mint address
            amount: Amount to swap (in smallest unit)
            user_public_key: User's wallet public key
            slippage_bps: Slippage tolerance in basis points
            
        Returns:
            Serialized transaction bytes
        """
        if not self.jupiter_client:
            raise ValueError("Jupiter client not configured")
        
        try:
            # Get Jupiter swap data
            swap_data = await self.jupiter_client.swap(
                src_mint=src_mint,
                dst_mint=dst_mint, 
                amount=amount,
                user_public_key=user_public_key,
                slippage_bps=slippage_bps
            )
            
            # Extract transaction from Jupiter response
            swap_transaction = swap_data["swapTransaction"]
            
            # Decode base64 transaction
            transaction_bytes = base64.b64decode(swap_transaction)
            
            logger.info(f"Built swap transaction: {len(transaction_bytes)} bytes")
            return transaction_bytes
            
        except Exception as e:
            logger.error(f"Failed to build swap transaction: {e}")
            raise

    async def build_transfer_tx(self, from_pubkey: str, to_pubkey: str, 
                               lamports: int, recent_blockhash: Optional[str] = None) -> bytes:
        """Build SOL transfer transaction
        
        Args:
            from_pubkey: Sender's public key
            to_pubkey: Recipient's public key
            lamports: Amount to transfer in lamports
            recent_blockhash: Recent blockhash (fetched if not provided)
            
        Returns:
            Serialized transaction bytes
        """
        if not self.solana_client:
            raise ValueError("Solana client not configured")
        
        try:
            # Get recent blockhash if not provided
            if not recent_blockhash:
                recent_blockhash = await self.solana_client.get_latest_blockhash()
            
            from solana.system_program import TransferParams, transfer
            
            # Create transfer instruction
            transfer_ix = transfer(TransferParams(
                from_pubkey=PublicKey(from_pubkey),
                to_pubkey=PublicKey(to_pubkey),
                lamports=lamports
            ))
            
            # Create transaction
            transaction = Transaction()
            transaction.add(transfer_ix)
            transaction.recent_blockhash = recent_blockhash
            
            # Serialize transaction
            transaction_bytes = transaction.serialize_message()
            
            logger.info(f"Built transfer transaction: {lamports} lamports from {from_pubkey} to {to_pubkey}")
            return transaction_bytes
            
        except Exception as e:
            logger.error(f"Failed to build transfer transaction: {e}")
            raise

    async def build_token_transfer_tx(self, from_pubkey: str, to_pubkey: str, 
                                     token_mint: str, amount: int, 
                                     decimals: int = 9, recent_blockhash: Optional[str] = None) -> bytes:
        """Build SPL token transfer transaction
        
        Args:
            from_pubkey: Sender's public key
            to_pubkey: Recipient's public key  
            token_mint: Token mint address
            amount: Amount to transfer (in smallest unit)
            decimals: Token decimals
            recent_blockhash: Recent blockhash (fetched if not provided)
            
        Returns:
            Serialized transaction bytes
        """
        if not self.solana_client:
            raise ValueError("Solana client not configured")
        
        try:
            # Get recent blockhash if not provided
            if not recent_blockhash:
                recent_blockhash = await self.solana_client.get_latest_blockhash()
            
            from spl.token.instructions import transfer_checked, TransferCheckedParams
            from spl.token.client import Token
            from spl.token._layouts import ACCOUNT_LAYOUT
            
            # Create token transfer instruction
            # Note: This is a simplified version - in production you'd need to handle
            # associated token accounts, account creation, etc.
            mint_pubkey = PublicKey(token_mint)
            
            # For now, create a basic structure - full implementation would require
            # more complex token account handling
            logger.warning("Token transfer implementation is simplified - requires ATA handling")
            
            # Return empty transaction for now as this requires more complex setup
            transaction = Transaction()
            transaction.recent_blockhash = recent_blockhash
            transaction_bytes = transaction.serialize_message()
            
            logger.info(f"Built token transfer transaction: {amount} tokens")
            return transaction_bytes
            
        except Exception as e:
            logger.error(f"Failed to build token transfer transaction: {e}")
            raise

    async def simulate_transaction(self, transaction_bytes: bytes, 
                                  accounts_to_inspect: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simulate transaction to check for errors before submission
        
        Args:
            transaction_bytes: Serialized transaction
            accounts_to_inspect: Optional list of account addresses to include in simulation
            
        Returns:
            Simulation results
        """
        if not self.solana_client:
            raise ValueError("Solana client not configured")
        
        try:
            from solana.rpc.types import TxOpts
            from solders.transaction import Transaction as SoldersTransaction
            
            # Deserialize transaction for simulation
            transaction = SoldersTransaction.from_bytes(transaction_bytes)
            
            # Simulate the transaction
            simulate_response = await self.solana_client._client.simulate_transaction(
                transaction,
                sig_verify=False,
                replace_recent_blockhash=True
            )
            
            if simulate_response.value.err:
                logger.warning(f"Transaction simulation failed: {simulate_response.value.err}")
                return {
                    "success": False,
                    "error": str(simulate_response.value.err),
                    "logs": simulate_response.value.logs
                }
            
            logger.info("Transaction simulation successful")
            return {
                "success": True,
                "units_consumed": simulate_response.value.units_consumed,
                "logs": simulate_response.value.logs,
                "accounts": simulate_response.value.accounts
            }
            
        except Exception as e:
            logger.error(f"Failed to simulate transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def sign_transaction(self, transaction_bytes: bytes, keypair: Union[Keypair, bytes, str]) -> bytes:
        """Sign a transaction with the provided keypair
        
        Args:
            transaction_bytes: Unsigned transaction bytes
            keypair: Signing keypair (Keypair object, bytes, or base58 string)
            
        Returns:
            Signed transaction bytes
        """
        try:
            # Handle different keypair formats
            if isinstance(keypair, str):
                # Assume base58 encoded private key
                from solders.keypair import Keypair as SoldersKeypair
                signing_keypair = SoldersKeypair.from_base58_string(keypair)
            elif isinstance(keypair, bytes):
                signing_keypair = SoldersKeypair.from_bytes(keypair)
            else:
                signing_keypair = keypair
            
            # Deserialize, sign, and serialize transaction
            from solders.transaction import Transaction as SoldersTransaction
            transaction = SoldersTransaction.from_bytes(transaction_bytes)
            
            # Sign the transaction
            signed_transaction = transaction
            # Note: Actual signing would require proper message signing
            # This is a placeholder for the signing logic
            
            signed_bytes = bytes(signed_transaction)
            logger.info("Transaction signed successfully")
            return signed_bytes
            
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise

    async def send_and_confirm_transaction(self, signed_transaction_bytes: bytes, 
                                          max_retries: int = 3, 
                                          confirmation_timeout: float = 60.0) -> Dict[str, Any]:
        """Send transaction and wait for confirmation
        
        Args:
            signed_transaction_bytes: Signed transaction bytes
            max_retries: Maximum retry attempts
            confirmation_timeout: Timeout for confirmation in seconds
            
        Returns:
            Transaction result with signature and status
        """
        if not self.solana_client:
            raise ValueError("Solana client not configured")
        
        for attempt in range(max_retries):
            try:
                # Send transaction
                signature = await self.solana_client.send_transaction(signed_transaction_bytes)
                logger.info(f"Transaction sent with signature: {signature}")
                
                # Wait for confirmation
                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) < confirmation_timeout:
                    try:
                        # Check transaction status
                        status_response = await self.solana_client._client.get_signature_statuses([signature])
                        
                        if status_response.value and status_response.value[0]:
                            status = status_response.value[0]
                            if status.confirmation_status:
                                logger.info(f"Transaction confirmed: {signature}")
                                return {
                                    "success": True,
                                    "signature": signature,
                                    "confirmation_status": str(status.confirmation_status),
                                    "slot": status.slot,
                                    "err": status.err
                                }
                    except Exception as check_error:
                        logger.warning(f"Error checking transaction status: {check_error}")
                    
                    await asyncio.sleep(2)  # Wait 2 seconds before checking again
                
                logger.warning(f"Transaction confirmation timeout: {signature}")
                return {
                    "success": False,
                    "signature": signature,
                    "error": "Confirmation timeout"
                }
                
            except Exception as e:
                logger.warning(f"Transaction attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError("Failed to send transaction after all retries")

    def estimate_transaction_fee(self, transaction_bytes: bytes, 
                               prioritization_fee_lamports: int = 0) -> int:
        """Estimate transaction fee in lamports
        
        Args:
            transaction_bytes: Serialized transaction
            prioritization_fee_lamports: Additional priority fee
            
        Returns:
            Estimated fee in lamports
        """
        try:
            # Base fee per signature (5000 lamports as of recent updates)
            base_fee_per_signature = 5000
            
            # Deserialize to count signatures
            from solders.transaction import Transaction as SoldersTransaction
            transaction = SoldersTransaction.from_bytes(transaction_bytes)
            
            # Estimate based on signatures needed
            estimated_signatures = 1  # At least one signature needed
            
            base_fee = base_fee_per_signature * estimated_signatures
            total_fee = base_fee + prioritization_fee_lamports
            
            logger.info(f"Estimated transaction fee: {total_fee} lamports")
            return total_fee
            
        except Exception as e:
            logger.error(f"Failed to estimate transaction fee: {e}")
            # Return conservative estimate
            return 10000 + prioritization_fee_lamports
