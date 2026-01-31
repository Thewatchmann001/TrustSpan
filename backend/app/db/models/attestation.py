"""
Attestation Database Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Attestation(Base):
    """Stored attestation records."""
    __tablename__ = "attestations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wallet_address = Column(String(44), nullable=False, index=True)
    
    # Attestation details
    attestation_id = Column(String(255), unique=True, nullable=False, index=True)
    issuer = Column(String(50), nullable=False)  # "verify", "civic", "sas"
    schema = Column(String(100), nullable=False)  # "business_ownership", "identity"
    status = Column(String(20), nullable=False, default="pending")  # pending, verified, rejected, expired
    
    # Attestation data
    data = Column(JSON, nullable=True)  # Stored attestation data
    on_chain = Column(Boolean, default=False)  # Whether on-chain via SAS
    sas_attestation_id = Column(String(255), nullable=True)  # SAS attestation ID if on-chain
    
    # On-chain transaction details
    transaction_signature = Column(String(255), nullable=True, index=True)  # Solana transaction signature
    cluster = Column(String(20), nullable=True, default="devnet")  # "devnet" or "mainnet"
    account_address = Column(String(44), nullable=True)  # On-chain account address
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="attestations")
    
    def __repr__(self):
        return f"<Attestation(id={self.id}, issuer={self.issuer}, schema={self.schema}, status={self.status})>"


# Add relationship to User model
# This will be imported in user.py or added via migration
