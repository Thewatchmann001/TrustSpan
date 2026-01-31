"""
Unified Attestation Service
Hybrid system supporting SAS, Civic, and Verify with configurable mock/real adapters.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from app.utils.logger import logger
from .models import AttestationResult, AttestationStatus, AttestationType, VerificationRequest
from .base_adapter import BaseAttestationAdapter
from .mock_adapters import MockVerifyAdapter, MockCivicAdapter, MockSASClient


class AttestationService:
    """
    Unified attestation service supporting multiple issuers.
    
    Behavior controlled by environment flags:
    - USE_REAL_SOLANA: Use real Solana devnet transactions (default: true)
    - USE_REAL_VERIFIERS: Use real Civic/Verify APIs (default: false)
    - SOLANA_CLUSTER: "devnet" or "mainnet" (mainnet NOT allowed in dev mode)
    """
    
    def __init__(self, mode: Optional[str] = None):
        """
        Initialize attestation service.
        
        Args:
            mode: "development" or "production" (defaults to DEBUG setting)
        """
        self.mode = mode or ("development" if settings.DEBUG else "production")
        logger.info(f"Initializing AttestationService in {self.mode} mode")
        
        # Initialize issuers (Civic/Verify) based on USE_REAL_VERIFIERS flag
        if settings.USE_REAL_VERIFIERS:
            # Use real verifiers (when implemented)
            try:
                from .real_adapters import VerifyAdapter, CivicAdapter
                self.issuers = {
                    "verify": VerifyAdapter(),
                    "civic": CivicAdapter(),
                }
                logger.info("Using REAL verifier adapters (Civic/Verify)")
            except (ImportError, NotImplementedError):
                logger.warning("Real verifiers not available, falling back to mocks")
                self.issuers = {
                    "verify": MockVerifyAdapter(),
                    "civic": MockCivicAdapter(),
                }
        else:
            # Always use mocks for verifiers (default)
            self.issuers = {
                "verify": MockVerifyAdapter(),
                "civic": MockCivicAdapter(),
            }
            logger.info("Using MOCK verifier adapters (Civic/Verify) - USE_REAL_VERIFIERS=false")
        
        # Initialize SAS client based on USE_REAL_SOLANA flag
        if settings.USE_REAL_SOLANA:
            # Use real Solana adapter for on-chain transactions
            try:
                from .real_adapters import RealSASAdapter
                self.sas_client = RealSASAdapter()
                logger.info(f"Using REAL Solana adapter (cluster: {settings.SOLANA_CLUSTER})")
            except Exception as e:
                logger.warning(f"Failed to initialize real Solana adapter: {e}, using mock")
                self.sas_client = MockSASClient()
        else:
            # Use mock SAS adapter
            self.sas_client = MockSASClient()
            logger.info("Using MOCK Solana adapter - USE_REAL_SOLANA=false")
    
    async def verify_business_ownership(
        self,
        wallet_address: str,
        business_data: Dict[str, Any],
        issuer: str = "verify",
        create_sas_attestation: bool = True
    ) -> AttestationResult:
        """
        Verify business ownership using specified issuer.
        
        Args:
            wallet_address: User's Solana wallet address
            business_data: Business information (name, registration number, etc.)
            issuer: "verify" or "civic" (civic doesn't do business verification)
            create_sas_attestation: Whether to create on-chain attestation via SAS
        
        Returns:
            AttestationResult with verification status
        """
        logger.info(f"Verifying business ownership for {wallet_address} via {issuer}")
        
        # Get issuer adapter
        adapter = self.issuers.get(issuer)
        if not adapter:
            raise ValueError(f"Unknown issuer: {issuer}. Available: {list(self.issuers.keys())}")
        
        # Verify with issuer
        issuer_result = await adapter.verify_business(wallet_address, business_data)
        
        if not issuer_result.verified:
            logger.warning(f"Business verification failed: {issuer_result.error}")
            return issuer_result
        
        # If verification successful and SAS enabled, create on-chain attestation
        if create_sas_attestation and issuer_result.verified:
            try:
                sas_result = await self.sas_client.create_attestation(
                    wallet_address=wallet_address,
                    schema="business_ownership",
                    data={
                        "business_name": business_data.get("business_name"),
                        "registration_number": business_data.get("registration_number"),
                        "issuer": issuer,
                        "issuer_attestation_id": issuer_result.attestation_id
                    },
                    issuer_attestation_id=issuer_result.attestation_id
                )
                
                # Combine results - attach SAS transaction details
                if sas_result.verified and sas_result.on_chain:
                    issuer_result.on_chain = True
                    issuer_result.data["sas_attestation_id"] = sas_result.attestation_id
                    issuer_result.data["transaction_signature"] = sas_result.data.get("transaction_signature")
                    issuer_result.data["cluster"] = sas_result.data.get("network", settings.SOLANA_CLUSTER)
                    issuer_result.data["explorer_url"] = sas_result.data.get("explorer_url")
                    issuer_result.data["account_address"] = sas_result.data.get("account_address")
                    logger.info(f"Created SAS attestation: {sas_result.attestation_id}, tx: {sas_result.data.get('transaction_signature')}")
                else:
                    logger.warning(f"SAS attestation creation failed: {sas_result.error}")
                
            except Exception as e:
                logger.error(f"Failed to create SAS attestation: {e}")
                # Continue with issuer result even if SAS fails
        
        return issuer_result
    
    async def verify_identity(
        self,
        wallet_address: str,
        identity_data: Dict[str, Any],
        issuer: str = "civic",
        create_sas_attestation: bool = True
    ) -> AttestationResult:
        """
        Verify identity/KYC using specified issuer.
        
        Args:
            wallet_address: User's Solana wallet address
            identity_data: Identity information (name, DOB, etc.)
            issuer: "civic" or "verify"
            create_sas_attestation: Whether to create on-chain attestation via SAS
        
        Returns:
            AttestationResult with verification status
        """
        logger.info(f"Verifying identity for {wallet_address} via {issuer}")
        
        adapter = self.issuers.get(issuer)
        if not adapter:
            raise ValueError(f"Unknown issuer: {issuer}")
        
        # Verify with issuer
        issuer_result = await adapter.verify_identity(wallet_address, identity_data)
        
        if not issuer_result.verified:
            return issuer_result
        
        # Create SAS attestation if enabled
        if create_sas_attestation and issuer_result.verified:
            try:
                sas_result = await self.sas_client.create_attestation(
                    wallet_address=wallet_address,
                    schema="identity",
                    data={
                        "full_name": identity_data.get("full_name"),
                        "issuer": issuer,
                        "issuer_attestation_id": issuer_result.attestation_id
                    },
                    issuer_attestation_id=issuer_result.attestation_id
                )
                
                # Combine results - attach SAS transaction details
                if sas_result.verified and sas_result.on_chain:
                    issuer_result.on_chain = True
                    issuer_result.data["sas_attestation_id"] = sas_result.attestation_id
                    issuer_result.data["transaction_signature"] = sas_result.data.get("transaction_signature")
                    issuer_result.data["cluster"] = sas_result.data.get("network", settings.SOLANA_CLUSTER)
                    issuer_result.data["explorer_url"] = sas_result.data.get("explorer_url")
                    issuer_result.data["account_address"] = sas_result.data.get("account_address")
                    logger.info(f"Created SAS attestation: {sas_result.attestation_id}, tx: {sas_result.data.get('transaction_signature')}")
                else:
                    logger.warning(f"SAS attestation creation failed: {sas_result.error}")
                
            except Exception as e:
                logger.error(f"Failed to create SAS attestation: {e}")
        
        return issuer_result
    
    async def get_attestation_status(
        self,
        wallet_address: str,
        schema: str,
        issuer: Optional[str] = None
    ) -> Optional[AttestationResult]:
        """
        Get attestation status for a wallet.
        
        Args:
            wallet_address: User's Solana wallet address
            schema: "business_ownership" or "identity"
            issuer: Optional issuer filter
        
        Returns:
            AttestationResult if found, None otherwise
        """
        # First check SAS (on-chain)
        sas_result = await self.sas_client.get_attestation(wallet_address, schema)
        
        if sas_result:
            return sas_result
        
        # If no SAS attestation, check issuer-specific attestations
        if issuer:
            adapter = self.issuers.get(issuer)
            if adapter:
                # This would require storing attestation IDs somewhere
                # For now, return SAS result or None
                pass
        
        return None
    
    async def verify_attestation_on_chain(
        self,
        wallet_address: str,
        schema: str
    ) -> bool:
        """Check if attestation exists on-chain (SAS)."""
        return await self.sas_client.verify_attestation(wallet_address, schema)
    
    async def get_all_attestations(
        self,
        wallet_address: str
    ) -> List[AttestationResult]:
        """
        Get all attestations for a wallet.
        
        Returns:
            List of all attestations (business, identity, etc.)
        """
        results = []
        
        # Check business ownership
        business_attestation = await self.get_attestation_status(
            wallet_address, "business_ownership"
        )
        if business_attestation:
            results.append(business_attestation)
        
        # Check identity
        identity_attestation = await self.get_attestation_status(
            wallet_address, "identity"
        )
        if identity_attestation:
            results.append(identity_attestation)
        
        return results
    
    def get_badge_type(self, issuer: str, schema: str, on_chain: bool = False, cluster: str = None) -> str:
        """
        Get badge type for issuer and schema.
        
        Badge logic:
        - Mock verifier + no on-chain: ❌ Unverified (not shown, only verified shown)
        - Mock verifier + devnet tx: 🧪 Test Verified
        - Real verifier + mainnet tx (future): ✅ Verified
        """
        # Determine if this is a test/dev attestation
        is_test = not settings.USE_REAL_VERIFIERS or (cluster == "devnet")
        
        if is_test and on_chain:
            # Test verified with on-chain transaction
            if schema == "business_ownership":
                return "🧪 Test Verified Business (Devnet)"
            elif schema == "identity":
                return "🧪 Test Verified Identity (Devnet)"
            else:
                return f"🧪 Test Verified ({schema})"
        elif is_test and not on_chain:
            # Mock verification only (no on-chain)
            if issuer == "verify" and schema == "business_ownership":
                return "🏢 Mock Verified Business"
            elif issuer == "verify" and schema == "identity":
                return "🛡️ Mock Verify Verified Identity"
            elif issuer == "civic" and schema == "identity":
                return "🛡️ Mock Civic Verified Founder"
            else:
                return f"🧪 Mock {issuer.title()} Verified"
        else:
            # Production verified (future)
            badges = {
                ("verify", "business_ownership"): "🏢 Verified Business",
                ("verify", "identity"): "🛡️ Verify Verified Identity",
                ("civic", "identity"): "🛡️ Civic Verified Founder",
            }
            return badges.get((issuer, schema), f"✅ {issuer.title()} Verified")
