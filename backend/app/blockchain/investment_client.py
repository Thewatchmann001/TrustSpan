import subprocess
import json
import os
from typing import Dict, Any, List
from pathlib import Path
from app.core.config import settings
from app.utils.logger import logger
from app.utils.helpers import parse_json_response
from app.core.exceptions import BlockchainError


class InvestmentClient:
    """Python wrapper for Solana investment ledger scripts."""
    
    def __init__(self):
        # Resolve path relative to backend directory
        backend_dir = Path(__file__).parent.parent.parent
        scripts_path = (backend_dir / settings.BLOCKCHAIN_SCRIPTS_PATH).resolve()
        self.invest_script = scripts_path / "investUSDC.js"
    
    def invest_in_startup(
        self,
        investor_address: str,
        founder_address: str,  # NEW parameter for USDC transfer destination
        startup_id: str,
        amount_usdc: float
    ) -> Dict[str, Any]:
        """
        Transfer USDC and record an investment in a startup on-chain.
        
        Args:
            investor_address: Investor's wallet address (sends USDC)
            founder_address: Founder's wallet address (receives USDC)
            startup_id: Startup ID (on-chain)
            amount_usdc: Amount in USDC
        
        Returns:
            {
                "investment_id": str,
                "transaction_signature": str,
                "confirmation_url": str,
                "blockchain_proof": dict,
                "timestamp": str
            }
        """
        try:
            logger.info(f"Transferring {amount_usdc} USDC from {investor_address} to {founder_address} for startup {startup_id}")
            
            # Call Node.js script
            # Use absolute path and set working directory to script's parent
            script_path = str(self.invest_script.resolve())
            script_dir = str(self.invest_script.parent.resolve())
            
            # Pass environment variables (including DEVNET_USDC_MINT)
            env = os.environ.copy()
            if hasattr(settings, 'DEVNET_USDC_MINT') and settings.DEVNET_USDC_MINT:
                env['DEVNET_USDC_MINT'] = settings.DEVNET_USDC_MINT
            
            result = subprocess.run(
                [
                    "node",
                    script_path,
                    investor_address,
                    founder_address,  # NEW: Pass founder address
                    startup_id,
                    str(amount_usdc)
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=script_dir,
                env=env  # Pass environment variables
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Investment recording failed: {error_msg}")
                raise BlockchainError(f"Failed to record investment: {error_msg}")
            
            # Parse JSON response
            response_data = parse_json_response(result.stdout)
            
            # Normalize keys from camelCase to snake_case
            normalized_response = {
                "investment_id": response_data.get("investmentId"),
                "transaction_signature": response_data.get("transactionSignature"),
                "confirmation_url": response_data.get("confirmationUrl"),
                "blockchain_proof": response_data.get("blockchainProof"),
                "timestamp": response_data.get("timestamp"),
            }
            
            logger.info(f"Investment recorded: {normalized_response.get('investment_id')}")
            
            return normalized_response
            
        except subprocess.TimeoutExpired:
            raise BlockchainError("Investment recording timed out")
        except Exception as e:
            logger.error(f"Error recording investment: {str(e)}")
            raise BlockchainError(f"Investment recording error: {str(e)}")
    
    def fetch_investment_proof(self, startup_id: str) -> List[Dict[str, Any]]:
        """
        Fetch investment proofs for a startup.
        Note: This would require querying on-chain accounts.
        For now, returns empty list as placeholder.
        """
        # In a full implementation, you'd query all investment accounts
        # associated with the startup_id PDA
        logger.info(f"Fetching investment proofs for startup: {startup_id}")
        return []

