"""
Attestation Service Module
Hybrid attestation system supporting SAS, Civic, and Verify.
"""
from .attestation_service import AttestationService
from .models import AttestationResult, AttestationStatus, AttestationType

__all__ = [
    "AttestationService",
    "AttestationResult",
    "AttestationStatus",
    "AttestationType",
]
