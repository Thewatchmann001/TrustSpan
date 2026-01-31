from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    JOB_SEEKER = "student"  # Database value remains "student" for backward compatibility
    STARTUP = "founder"  # Database value remains "founder" for backward compatibility
    INVESTOR = "investor"
    ADMIN = "admin"
    USER = "user"
    EMPLOYER = "employer"
    ENUMERATOR = "enumerator"
    VENDOR = "vendor"
    
    # Aliases for backward compatibility
    STUDENT = "student"  # Deprecated: use JOB_SEEKER
    FOUNDER = "founder"  # Deprecated: use STARTUP


class AuthProvider(str, enum.Enum):
    """Authentication provider types."""
    LOCAL = "local"
    GOOGLE = "google"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    wallet_address = Column(String(44), unique=True, index=True, nullable=True)
    university = Column(String(255), nullable=True)  # University for job seekers
    company_name = Column(String(255), nullable=True)  # Company name for startups
    verified_on_chain = Column(String(20), default="pending")  # verified, pending, not_verified
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # OAuth fields
    auth_provider = Column(String(20), default="local", nullable=False)  # local, google, linkedin, facebook
    provider_id = Column(String(255), nullable=True, index=True)  # OAuth provider's user ID
    failed_login_attempts = Column(Integer, default=0, nullable=False)  # For account locking
    locked_until = Column(DateTime, nullable=True)  # Account lock expiration
    last_login = Column(DateTime, nullable=True)

    # Relationships
    # certificates removed - not part of core solutions
    startups = relationship("Startup", back_populates="founder")
    investments = relationship("Investment", back_populates="investor")
    cvs = relationship("CV", back_populates="user")
    job_matches = relationship("JobMatch", back_populates="user")
    job_applications = relationship("JobApplication", back_populates="user")
    # Trust infrastructure relationships
    credentials = relationship("Credential", back_populates="user", cascade="all, delete-orphan")
    trust_signals = relationship("TrustSignal", back_populates="user", cascade="all, delete-orphan")
    attestations = relationship("Attestation", back_populates="user", cascade="all, delete-orphan")

