"""
Mock Adapters for Development
Simulates verification without real API calls or costs.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_adapter import BaseAttestationAdapter
from .models import AttestationResult, AttestationStatus


class MockVerifyAdapter(BaseAttestationAdapter):
    """Mock Verify adapter - simulates business verification."""
    
    def __init__(self):
        super().__init__("verify")
        self.attestations = {}  # In-memory storage
    
    async def verify_business(
        self,
        wallet_address: str,
        business_data: Dict[str, Any]
    ) -> AttestationResult:
        """Simulate business verification."""
        # Simulate API delay (2-3 seconds)
        await asyncio.sleep(2)
        
        # Simple validation
        required_fields = ['business_name', 'registration_number']
        is_valid = all(field in business_data for field in required_fields)
        
        if not is_valid:
            return AttestationResult(
                verified=False,
                attestation_id="",
                issuer="verify",
                status=AttestationStatus.REJECTED,
                wallet_address=wallet_address,
                schema="business_ownership",
                data=business_data,
                timestamp=datetime.utcnow(),
                error="Missing required fields: business_name, registration_number"
            )
        
        # Generate mock attestation
        attestation_id = f"verify_{uuid.uuid4().hex[:16]}"
        
        result = AttestationResult(
            verified=True,
            attestation_id=attestation_id,
            issuer="verify",
            status=AttestationStatus.VERIFIED,
            wallet_address=wallet_address,
            schema="business_ownership",
            data={
                **business_data,
                "verified_by": "Verify (Mock)",
                "verification_date": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            on_chain=False
        )
        
        self.attestations[attestation_id] = result
        return result
    
    async def verify_identity(
        self,
        wallet_address: str,
        identity_data: Dict[str, Any]
    ) -> AttestationResult:
        """Simulate identity verification."""
        await asyncio.sleep(2)
        
        required_fields = ['full_name', 'date_of_birth', 'nationality']
        is_valid = all(field in identity_data for field in required_fields)
        
        if not is_valid:
            return AttestationResult(
                verified=False,
                attestation_id="",
                issuer="verify",
                status=AttestationStatus.REJECTED,
                wallet_address=wallet_address,
                schema="identity",
                data=identity_data,
                timestamp=datetime.utcnow(),
                error="Missing required identity fields"
            )
        
        attestation_id = f"verify_id_{uuid.uuid4().hex[:16]}"
        
        return AttestationResult(
            verified=True,
            attestation_id=attestation_id,
            issuer="verify",
            status=AttestationStatus.VERIFIED,
            wallet_address=wallet_address,
            schema="identity",
            data={
                **identity_data,
                "verified_by": "Verify (Mock)",
                "verification_date": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            on_chain=False
        )
    
    async def get_attestation_status(
        self,
        attestation_id: str
    ) -> AttestationResult:
        """Get attestation status."""
        await asyncio.sleep(0.5)
        
        if attestation_id in self.attestations:
            return self.attestations[attestation_id]
        
        return AttestationResult(
            verified=False,
            attestation_id=attestation_id,
            issuer="verify",
            status=AttestationStatus.REJECTED,
            wallet_address="",
            schema="unknown",
            data={},
            timestamp=datetime.utcnow(),
            error="Attestation not found"
        )
    
    async def revoke_attestation(self, attestation_id: str) -> bool:
        """Revoke attestation."""
        if attestation_id in self.attestations:
            del self.attestations[attestation_id]
            return True
        return False


class MockCivicAdapter(BaseAttestationAdapter):
    """Mock Civic adapter - simulates identity verification."""
    
    def __init__(self):
        super().__init__("civic")
        self.attestations = {}
    
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
        """Simulate identity verification."""
        await asyncio.sleep(2.5)
        
        required_fields = ['full_name', 'email']
        is_valid = all(field in identity_data for field in required_fields)
        
        if not is_valid:
            return AttestationResult(
                verified=False,
                attestation_id="",
                issuer="civic",
                status=AttestationStatus.REJECTED,
                wallet_address=wallet_address,
                schema="identity",
                data=identity_data,
                timestamp=datetime.utcnow(),
                error="Missing required identity fields"
            )
        
        attestation_id = f"civic_{uuid.uuid4().hex[:16]}"
        
        result = AttestationResult(
            verified=True,
            attestation_id=attestation_id,
            issuer="civic",
            status=AttestationStatus.VERIFIED,
            wallet_address=wallet_address,
            schema="identity",
            data={
                **identity_data,
                "verified_by": "Civic (Mock)",
                "verification_date": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            on_chain=False
        )
        
        self.attestations[attestation_id] = result
        return result
    
    async def get_attestation_status(
        self,
        attestation_id: str
    ) -> AttestationResult:
        """Get attestation status."""
        await asyncio.sleep(0.5)
        
        if attestation_id in self.attestations:
            return self.attestations[attestation_id]
        
        return AttestationResult(
            verified=False,
            attestation_id=attestation_id,
            issuer="civic",
            status=AttestationStatus.REJECTED,
            wallet_address="",
            schema="unknown",
            data={},
            timestamp=datetime.utcnow(),
            error="Attestation not found"
        )
    
    async def revoke_attestation(self, attestation_id: str) -> bool:
        """Revoke attestation."""
        if attestation_id in self.attestations:
            del self.attestations[attestation_id]
            return True
        return False


class MockSASClient:
    """Mock Solana Attestation Service client."""
    
    def __init__(self):
        self.attestations = {}  # In-memory storage
    
    async def get_attestation(
        self,
        wallet_address: str,
        schema: str
    ) -> Optional[AttestationResult]:
        """Get on-chain attestation."""
        await asyncio.sleep(0.3)
        
        key = f"{wallet_address}:{schema}"
        return self.attestations.get(key)
    
    async def create_attestation(
        self,
        wallet_address: str,
        schema: str,
        data: Dict[str, Any],
        issuer_attestation_id: str
    ) -> AttestationResult:
        """Create on-chain attestation (mock)."""
        await asyncio.sleep(1)
        
        attestation_id = f"sas_{uuid.uuid4().hex[:16]}"
        key = f"{wallet_address}:{schema}"
        
        result = AttestationResult(
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
                "network": "devnet"
            },
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            on_chain=True
        )
        
        self.attestations[key] = result
        return result
    
    async def verify_attestation(
        self,
        wallet_address: str,
        schema: str
    ) -> bool:
        """Verify attestation exists on-chain."""
        await asyncio.sleep(0.3)
        
        key = f"{wallet_address}:{schema}"
        return key in self.attestations
