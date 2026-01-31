from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.base import Base


class CredentialType(str, enum.Enum):
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    SKILL = "skill"
    CERTIFICATION = "certification"
    STARTUP_ROLE = "startup_role"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class CredentialSource(str, enum.Enum):
    USER_INPUT = "user_input"
    SYSTEM_GENERATED = "system_generated"
    THIRD_PARTY = "third_party"


class Credential(Base):
    """Single source of truth for all user credentials."""
    __tablename__ = "credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Credential details
    type = Column(SQLEnum(CredentialType), nullable=False, index=True)
    title = Column(String(255), nullable=False)  # "BSc Computer Science", "CTO", "Backend Engineer"
    organization = Column(String(255), nullable=True)  # University / Company / Startup
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

    # Metadata
    source = Column(SQLEnum(CredentialSource), default=CredentialSource.USER_INPUT)
    verification_status = Column(
        SQLEnum(VerificationStatus),
        default=VerificationStatus.UNVERIFIED,
        index=True
    )
    confidence_score = Column(Float, default=0.0)  # 0.0 - 1.0

    # Additional metadata (for verification documents, etc.)
    # Note: Using 'extra_data' instead of 'metadata' because 'metadata' is reserved by SQLAlchemy
    extra_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="credentials")
    trust_signals = relationship("TrustSignal", back_populates="credential", cascade="all, delete-orphan")
    hashes = relationship("CredentialHash", back_populates="credential", cascade="all, delete-orphan")


class TrustSignalType(str, enum.Enum):
    VERIFIED_DEGREE = "verified_degree"
    VERIFIED_EMPLOYMENT = "verified_employment"
    FOUNDER_VERIFIED = "founder_verified"
    INVESTOR_ACTIVITY = "investor_activity"
    STARTUP_ROLE_VERIFIED = "startup_role_verified"


class TrustSignal(Base):
    """Derived trust signals computed from credentials and activities."""
    __tablename__ = "trust_signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    credential_id = Column(String(36), ForeignKey("credentials.id"), nullable=True, index=True)

    signal_type = Column(SQLEnum(TrustSignalType), nullable=False, index=True)
    weight = Column(Float, default=1.0)  # Signal importance (0.0 - 1.0)
    source = Column(String(100), nullable=True)  # Where signal came from
    extra_data = Column(JSON, nullable=True)  # Additional signal data (renamed from metadata - SQLAlchemy reserved)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="trust_signals")
    credential = relationship("Credential", back_populates="trust_signals")


class CredentialHash(Base):
    """Blockchain hashes of verified credentials (no PII exposure)."""
    __tablename__ = "credential_hashes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("credentials.id"), nullable=False, index=True)

    hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    chain = Column(String(20), default="solana")  # Blockchain name
    tx_signature = Column(String(88), nullable=True)  # Transaction signature
    block_number = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    credential = relationship("Credential", back_populates="hashes")
