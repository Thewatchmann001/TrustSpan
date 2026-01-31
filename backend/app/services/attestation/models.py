"""
Attestation Data Models
"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class AttestationStatus(str, Enum):
    """Attestation verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AttestationType(str, Enum):
    """Types of attestations."""
    BUSINESS_OWNERSHIP = "business_ownership"
    IDENTITY = "identity"
    KYC = "kyc"
    KYB = "kyb"


class AttestationResult(BaseModel):
    """Result from an attestation verification."""
    verified: bool
    attestation_id: str
    issuer: str  # "verify", "civic", "sas"
    status: AttestationStatus
    wallet_address: str
    schema: str
    data: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    on_chain: bool = False  # Whether attestation is on-chain (SAS)
    error: Optional[str] = None

    class Config:
        from_attributes = True


class VerificationRequest(BaseModel):
    """Request for verification."""
    wallet_address: str
    attestation_type: AttestationType
    issuer: str  # "verify", "civic", or "sas"
    business_data: Optional[Dict[str, Any]] = None
    identity_data: Optional[Dict[str, Any]] = None
    documents: Optional[list] = None  # List of document URLs or base64
