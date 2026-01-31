"""
Trust Service - Shared Infrastructure for Identity, Credentials, and Trust Signals

This service provides the foundation that all products consume:
- Credential management (single source of truth)
- Verification workflows
- Trust score calculation

Products (CV Builder, Startup Platform) consume this service but do not mix concerns.
"""
from .credential_service import CredentialService
from .verification_service import VerificationService
from .trust_score_service import TrustScoreService

__all__ = [
    "CredentialService",
    "VerificationService",
    "TrustScoreService",
]
