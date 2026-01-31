"""
Base Adapter Interface for Attestation Providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .models import AttestationResult, AttestationType


class BaseAttestationAdapter(ABC):
    """Base class for attestation provider adapters."""
    
    def __init__(self, issuer_name: str):
        self.issuer_name = issuer_name
    
    @abstractmethod
    async def verify_business(
        self,
        wallet_address: str,
        business_data: Dict[str, Any]
    ) -> AttestationResult:
        """Verify business ownership."""
        pass
    
    @abstractmethod
    async def verify_identity(
        self,
        wallet_address: str,
        identity_data: Dict[str, Any]
    ) -> AttestationResult:
        """Verify identity/KYC."""
        pass
    
    @abstractmethod
    async def get_attestation_status(
        self,
        attestation_id: str
    ) -> AttestationResult:
        """Get status of an existing attestation."""
        pass
    
    @abstractmethod
    async def revoke_attestation(
        self,
        attestation_id: str
    ) -> bool:
        """Revoke an attestation."""
        pass
