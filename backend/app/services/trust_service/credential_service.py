"""
Credential Service - Manages the single source of truth for all user credentials.

CV sections = views over credentials
Startup team = credentials
Founder role = credential
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import (
    Credential,
    CredentialType,
    VerificationStatus,
    CredentialSource,
    User,
)
from app.utils.logger import logger


class CredentialService:
    """Service for managing credentials - the single source of truth."""

    def create_credential(
        self,
        db: Session,
        user_id: int,
        credential_type: CredentialType,
        title: str,
        organization: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        description: Optional[str] = None,
        source: CredentialSource = CredentialSource.USER_INPUT,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Credential:
        """
        Create a new credential.

        Args:
            db: Database session
            user_id: User who owns this credential
            credential_type: Type of credential (education, employment, etc.)
            title: Credential title (e.g., "BSc Computer Science", "CTO")
            organization: Organization name (university, company, startup)
            start_date: When credential started
            end_date: When credential ended (None for current)
            description: Additional details
            source: How credential was created
            metadata: Additional metadata (for verification docs, etc.)

        Returns:
            Created Credential object
        """
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        credential = Credential(
            user_id=user_id,
            type=credential_type,
            title=title,
            organization=organization,
            start_date=start_date,
            end_date=end_date,
            description=description,
            source=source,
            verification_status=VerificationStatus.UNVERIFIED,
            extra_data=extra_data or {},
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
        logger.info(
            f"Created credential {credential.id} (type: {credential_type.value}, title: {title}) for user {user_id}"
        )
        return credential

    def get_user_credentials(
        self,
        db: Session,
        user_id: int,
        credential_type: Optional[CredentialType] = None,
        verification_status: Optional[VerificationStatus] = None,
        limit: Optional[int] = None,
    ) -> List[Credential]:
        """
        Get all credentials for a user, optionally filtered.

        Args:
            db: Database session
            user_id: User ID
            credential_type: Filter by type (optional)
            verification_status: Filter by verification status (optional)
            limit: Maximum number of results (optional)

        Returns:
            List of Credential objects, ordered by start_date descending
        """
        query = db.query(Credential).filter(Credential.user_id == user_id)

        if credential_type:
            query = query.filter(Credential.type == credential_type)
        if verification_status:
            query = query.filter(Credential.verification_status == verification_status)

        query = query.order_by(Credential.start_date.desc() if Credential.start_date else Credential.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_credential(self, db: Session, credential_id: str) -> Optional[Credential]:
        """Get a single credential by ID."""
        return db.query(Credential).filter(Credential.id == credential_id).first()

    def update_credential(
        self,
        db: Session,
        credential_id: str,
        **updates: Any,
    ) -> Optional[Credential]:
        """
        Update a credential.

        Args:
            db: Database session
            credential_id: Credential ID to update
            **updates: Fields to update (title, organization, description, etc.)

        Returns:
            Updated Credential object, or None if not found
        """
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        if not credential:
            logger.warning(f"Credential {credential_id} not found for update")
            return None

        for key, value in updates.items():
            if hasattr(credential, key) and value is not None:
                setattr(credential, key, value)

        credential.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(credential)
        logger.info(f"Updated credential {credential_id}")
        return credential

    def delete_credential(self, db: Session, credential_id: str) -> bool:
        """Delete a credential."""
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        if not credential:
            return False

        db.delete(credential)
        db.commit()
        logger.info(f"Deleted credential {credential_id}")
        return True

    def get_credentials_by_organization(
        self,
        db: Session,
        organization: str,
        credential_type: Optional[CredentialType] = None,
    ) -> List[Credential]:
        """Get all credentials for a specific organization (useful for verification)."""
        query = db.query(Credential).filter(Credential.organization == organization)

        if credential_type:
            query = query.filter(Credential.type == credential_type)

        return query.all()
