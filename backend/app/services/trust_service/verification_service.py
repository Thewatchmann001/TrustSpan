"""
Verification Service - Manages credential verification workflows.

Handles:
- Submitting credentials for verification
- Verifying credentials (manual or automated)
- Creating trust signals when credentials are verified
- Blockchain hashing of verified credentials
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import json
from app.db.models import (
    Credential,
    VerificationStatus,
    TrustSignal,
    TrustSignalType,
    CredentialHash,
    CredentialType,
)
from app.utils.logger import logger


class VerificationService:
    """Service for managing credential verification."""

    def submit_for_verification(
        self,
        db: Session,
        credential_id: str,
        verification_data: Optional[Dict[str, Any]] = None,
    ) -> Credential:
        """
        Submit a credential for verification.

        Args:
            db: Database session
            credential_id: Credential to verify
            verification_data: Additional data (documents, references, etc.)

        Returns:
            Updated Credential object

        Raises:
            ValueError: If credential not found
        """
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")

        credential.verification_status = VerificationStatus.SUBMITTED
        if verification_data:
            if credential.extra_data is None:
                credential.extra_data = {}
            credential.extra_data.update(verification_data)

        credential.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(credential)

        logger.info(f"Credential {credential_id} submitted for verification")
        return credential

    def verify_credential(
        self,
        db: Session,
        credential_id: str,
        confidence_score: float = 1.0,
        verified_by: Optional[str] = None,
        verification_metadata: Optional[Dict[str, Any]] = None,
    ) -> Credential:
        """
        Mark a credential as verified.

        Args:
            db: Database session
            credential_id: Credential to verify
            confidence_score: Confidence in verification (0.0 - 1.0)
            verified_by: Who/what verified it (optional)
            verification_metadata: Additional verification data

        Returns:
            Updated Credential object

        Raises:
            ValueError: If credential not found
        """
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")

        credential.verification_status = VerificationStatus.VERIFIED
        credential.confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp to 0-1
        credential.verified_at = datetime.utcnow()

        if verification_metadata:
            if credential.extra_data is None:
                credential.extra_data = {}
            credential.extra_data.update(verification_metadata)
            if verified_by:
                credential.extra_data["verified_by"] = verified_by

        credential.updated_at = datetime.utcnow()
        db.commit()

        # Create trust signal
        self._create_trust_signal(db, credential, confidence_score)

        # Hash for blockchain (only verified credentials)
        self._create_blockchain_hash(db, credential)

        db.refresh(credential)
        logger.info(
            f"Credential {credential_id} verified with confidence {confidence_score}"
        )
        return credential

    def reject_credential(
        self,
        db: Session,
        credential_id: str,
        reason: Optional[str] = None,
    ) -> Credential:
        """Mark a credential as rejected."""
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")

        credential.verification_status = VerificationStatus.REJECTED
        if reason:
            if credential.extra_data is None:
                credential.extra_data = {}
            credential.extra_data["rejection_reason"] = reason

        credential.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(credential)

        logger.info(f"Credential {credential_id} rejected: {reason}")
        return credential

    def _create_trust_signal(
        self,
        db: Session,
        credential: Credential,
        weight: float,
    ):
        """Create a trust signal when credential is verified."""
        signal_type_map = {
            CredentialType.EDUCATION: TrustSignalType.VERIFIED_DEGREE,
            CredentialType.EMPLOYMENT: TrustSignalType.VERIFIED_EMPLOYMENT,
            CredentialType.STARTUP_ROLE: TrustSignalType.STARTUP_ROLE_VERIFIED,
            CredentialType.CERTIFICATION: TrustSignalType.VERIFIED_EMPLOYMENT,  # Treat as employment-like
        }

        signal_type = signal_type_map.get(credential.type)
        if signal_type:
            signal = TrustSignal(
                user_id=credential.user_id,
                credential_id=credential.id,
                signal_type=signal_type,
                weight=weight,
                source="verification_service",
                extra_data={
                    "credential_type": credential.type.value,
                    "title": credential.title,
                    "organization": credential.organization,
                },
            )
            db.add(signal)
            db.commit()
            logger.info(
                f"Created trust signal {signal.id} for verified credential {credential.id}"
            )

    def _create_blockchain_hash(
        self,
        db: Session,
        credential: Credential,
    ):
        """
        Create blockchain hash for verified credential.

        Only hashes: credential_id + key fields + verification_status
        No PII exposure, no CV leakage.
        """
        # Create hash of credential data (no PII)
        hash_data = {
            "credential_id": credential.id,
            "type": credential.type.value,
            "title": credential.title,
            "organization": credential.organization,
            "verification_status": credential.verification_status.value,
            "verified_at": credential.verified_at.isoformat() if credential.verified_at else None,
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        credential_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        # Store hash (blockchain transaction would happen here)
        hash_record = CredentialHash(
            credential_id=credential.id,
            hash=credential_hash,
            chain="solana",
            # tx_signature would be set after blockchain transaction
        )
        db.add(hash_record)
        db.commit()

        logger.info(
            f"Created blockchain hash {credential_hash[:16]}... for credential {credential.id}"
        )

    def get_verification_stats(
        self,
        db: Session,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get verification statistics."""
        query = db.query(Credential)

        if user_id:
            query = query.filter(Credential.user_id == user_id)

        total = query.count()
        verified = query.filter(
            Credential.verification_status == VerificationStatus.VERIFIED
        ).count()
        submitted = query.filter(
            Credential.verification_status == VerificationStatus.SUBMITTED
        ).count()
        unverified = query.filter(
            Credential.verification_status == VerificationStatus.UNVERIFIED
        ).count()
        rejected = query.filter(
            Credential.verification_status == VerificationStatus.REJECTED
        ).count()

        return {
            "total": total,
            "verified": verified,
            "submitted": submitted,
            "unverified": unverified,
            "rejected": rejected,
            "verification_rate": (verified / total * 100) if total > 0 else 0.0,
        }
