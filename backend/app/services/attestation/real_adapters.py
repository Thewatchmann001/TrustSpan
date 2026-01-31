"""
Real Adapter Interfaces for Production
Implement these with actual API integrations when ready.
"""
from typing import Dict, Any, Optional
from app.utils.logger import logger
from app.core.config import settings
from .base_adapter import BaseAttestationAdapter
from .models import AttestationResult, AttestationStatus
from datetime import datetime, timedelta
import subprocess
import json
from pathlib import Path


class VerifyAdapter(BaseAttestationAdapter):
    """
    Real Verify adapter for business verification.
    
    TODO: Implement actual Verify API integration
    - Sign up at https://verify.com
    - Get API keys
    - Implement API calls
    """
    
    def __init__(self):
        super().__init__("verify")
        # TODO: Initialize with API keys from settings
        # self.api_key = settings.VERIFY_API_KEY
        # self.api_url = settings.VERIFY_API_URL
        logger.warning("VerifyAdapter: Real implementation not yet configured")
    
    async def verify_business(
        self,
        wallet_address: str,
        business_data: Dict[str, Any]
    ) -> AttestationResult:
        """Verify business with real Verify API."""
        # TODO: Implement real Verify API call
        raise NotImplementedError("Real Verify API integration not yet implemented")
    
    async def verify_identity(
        self,
        wallet_address: str,
        identity_data: Dict[str, Any]
    ) -> AttestationResult:
        """Verify identity with real Verify API."""
        raise NotImplementedError("Real Verify API integration not yet implemented")
    
    async def get_attestation_status(
        self,
        attestation_id: str
    ) -> AttestationResult:
        """Get attestation status from Verify API."""
        raise NotImplementedError("Real Verify API integration not yet implemented")
    
    async def revoke_attestation(self, attestation_id: str) -> bool:
        """Revoke attestation via Verify API."""
        raise NotImplementedError("Real Verify API integration not yet implemented")


class CivicAdapter(BaseAttestationAdapter):
    """
    Real Civic adapter for identity verification.
    
    TODO: Implement actual Civic API integration
    - Sign up at https://www.civic.com
    - Get API keys
    - Implement API calls
    """
    
    def __init__(self):
        super().__init__("civic")
        # TODO: Initialize with API keys from settings
        # self.api_key = settings.CIVIC_API_KEY
        # self.api_url = settings.CIVIC_API_URL
        logger.warning("CivicAdapter: Real implementation not yet configured")
    
    async def verify_business(
        self,
        wallet_address: str,
        business_data: Dict[str, Any]
    ) -> AttestationResult:
        """Civic doesn't do business verification."""
        return AttestationResult(
            verified=False,
            attestation_id="",
            issuer="civic",
            status=AttestationStatus.REJECTED,
            wallet_address=wallet_address,
            schema="business_ownership",
            data=business_data,
            timestamp=datetime.utcnow(),
            error="Civic does not provide business verification"
        )
    
    async def verify_identity(
        self,
        wallet_address: str,
        identity_data: Dict[str, Any]
    ) -> AttestationResult:
        """Verify identity with real Civic API."""
        raise NotImplementedError("Real Civic API integration not yet implemented")
    
    async def get_attestation_status(
        self,
        attestation_id: str
    ) -> AttestationResult:
        """Get attestation status from Civic API."""
        raise NotImplementedError("Real Civic API integration not yet implemented")
    
    async def revoke_attestation(self, attestation_id: str) -> bool:
        """Revoke attestation via Civic API."""
        raise NotImplementedError("Real Civic API integration not yet implemented")


class RealSASAdapter:
    """
    Real Solana Attestation Service adapter for devnet.
    
    Creates on-chain attestations using real Solana transactions.
    Writes attestations directly to Solana devnet blockchain.
    
    This adapter implements the same interface as MockSASClient for consistency.
    """
    
    def __init__(self):
        import os
        
        self.rpc_url = settings.SOLANA_RPC_URL
        self.cluster = settings.SOLANA_CLUSTER
        self.wallet_path = os.path.expanduser(settings.WALLET_PATH)
        
        # Safety check: Never allow mainnet in development
        if self.cluster == "mainnet" and settings.DEBUG:
            raise ValueError("Mainnet is not allowed in development mode. Use devnet only.")
        
        # Check if wallet exists
        if os.path.exists(self.wallet_path):
            logger.info(f"RealSASAdapter initialized with wallet: {self.wallet_path}, cluster: {self.cluster}")
        else:
            logger.warning(f"Wallet not found at {self.wallet_path}. On-chain attestations may fail.")
    
    async def get_attestation(
        self,
        wallet_address: str,
        schema: str
    ) -> Optional[AttestationResult]:
        """Query on-chain attestation from Solana."""
        try:
            # TODO: Implement RPC query to check if account exists
            # For now, return None (not found)
            logger.debug(f"Querying attestation for {wallet_address}:{schema}")
            return None
        except Exception as e:
            logger.error(f"Error querying attestation: {e}")
            return None
    
    async def create_attestation(
        self,
        wallet_address: str,
        schema: str,
        data: Dict[str, Any],
        issuer_attestation_id: str
    ) -> AttestationResult:
        """
        Create on-chain attestation on Solana devnet.
        
        Uses the dev attestation schema:
        {
          "schema": "kyb0 | kyc0",
          "subject_wallet": "<wallet_address>",
          "issuer": "mock_civic | mock_verify",
          "environment": "dev",
          "data_hash": "<sha256 hash>",
          "timestamp": "<unix timestamp>"
        }
        """
        import uuid
        import hashlib
        
        logger.info(f"Creating REAL on-chain attestation for {wallet_address}:{schema} on {self.cluster}")
        
        try:
            # Map schema to SAS schema format
            sas_schema = "kyb0" if schema == "business_ownership" else "kyc0"
            
            # Map issuer to mock issuer name
            issuer_name = data.get("issuer", "unknown")
            mock_issuer = f"mock_{issuer_name}"
            
            # Create attestation payload (no PII on-chain)
            attestation_payload = {
                "schema": sas_schema,
                "subject_wallet": wallet_address,
                "issuer": mock_issuer,
                "environment": "dev",
                "issuer_attestation_id": issuer_attestation_id,
                "timestamp": int(datetime.utcnow().timestamp())
            }
            
            # Hash the payload for data integrity
            payload_json = json.dumps(attestation_payload, sort_keys=True)
            data_hash = hashlib.sha256(payload_json.encode()).hexdigest()
            attestation_payload["data_hash"] = data_hash
            
            # Create via Node.js script
            result = await self._create_on_chain_attestation_via_node(
                wallet_address, schema, attestation_payload
            )
            
            if result and result.get("success"):
                # Success - attestation created on-chain
                attestation_id = result.get("attestation_id") or f"sas_{uuid.uuid4().hex[:16]}"
                tx_signature = result.get("transaction_signature")
                
                return AttestationResult(
                    verified=True,
                    attestation_id=attestation_id,
                    issuer="sas",
                    status=AttestationStatus.VERIFIED,
                    wallet_address=wallet_address,
                    schema=schema,
                    data={
                        **data,
                        "issuer_attestation_id": issuer_attestation_id,
                        "on_chain": True,
                        "blockchain": "solana",
                        "network": self.cluster,
                        "environment": "dev",
                        "sas_schema": sas_schema,
                        "mock_issuer": mock_issuer,
                        "data_hash": data_hash,
                        "account_address": result.get("account_address"),
                        "transaction_signature": tx_signature,
                        "explorer_url": result.get("explorer_url"),
                        "account_explorer_url": result.get("account_explorer_url"),
                        "created_via": "real_solana_adapter"
                    },
                    timestamp=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=365),
                    on_chain=True
                )
            else:
                error_msg = result.get("error") if result else "Unknown error"
                logger.error(f"Failed to create on-chain attestation: {error_msg}")
                
                return AttestationResult(
                    verified=False,
                    attestation_id="",
                    issuer="sas",
                    status=AttestationStatus.REJECTED,
                    wallet_address=wallet_address,
                    schema=schema,
                    data=data,
                    timestamp=datetime.utcnow(),
                    error=f"Failed to create on-chain attestation: {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"Error creating on-chain attestation: {e}")
            return AttestationResult(
                verified=False,
                attestation_id="",
                issuer="sas",
                status=AttestationStatus.REJECTED,
                wallet_address=wallet_address,
                schema=schema,
                data=data,
                timestamp=datetime.utcnow(),
                error=f"Failed to create on-chain attestation: {str(e)}"
            )
    
    async def verify_attestation(
        self,
        wallet_address: str,
        schema: str
    ) -> bool:
        """Verify attestation exists on-chain."""
        try:
            attestation = await self.get_attestation(wallet_address, schema)
            return attestation is not None and attestation.verified
        except Exception as e:
            logger.error(f"Error verifying attestation: {e}")
            return False
    
    async def _create_on_chain_attestation_via_node(
        self,
        wallet_address: str,
        schema: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create on-chain attestation using Node.js script.
        This uses the existing blockchain scripts infrastructure.
        """
        # Use the createAttestation.js script
        backend_dir = Path(__file__).parent.parent.parent.parent  # backend/
        project_root = backend_dir.parent  # project root
        script_path = project_root / "blockchain" / "scripts" / "createAttestation.js"
        
        if not script_path.exists():
            script_path = (backend_dir / ".." / "blockchain" / "scripts" / "createAttestation.js").resolve()
        
        if not script_path.exists():
            logger.error(f"Attestation script not found at {script_path}")
            return None
        
        try:
            # Prepare data as JSON string
            data_json = json.dumps(data)
            
            # Set environment variables for the script
            import os
            env = os.environ.copy()
            env["SOLANA_RPC_URL"] = self.rpc_url
            env["WALLET_PATH"] = self.wallet_path
            env["SOLANA_CLUSTER"] = self.cluster
            
            # Run Node.js script
            result = subprocess.run(
                ["node", str(script_path), wallet_address, schema, data_json],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(script_path.parent),
                env=env
            )
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout.strip())
                    if output.get("success"):
                        logger.info(f"On-chain attestation created: {output.get('attestation_id')}")
                        return output
                    else:
                        logger.error(f"Attestation creation failed: {output.get('error')}")
                        return None
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON output: {result.stdout}")
                    return None
            else:
                logger.error(f"Node script failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Attestation creation timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to create attestation via Node: {e}")
            return None


# Legacy alias for backward compatibility
SASClient = RealSASAdapter
