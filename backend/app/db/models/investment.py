from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=False)
    investor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Total invested USDC amount
    escrow_balance = Column(Float, default=0.0)  # Amount currently held in escrow
    released_amount = Column(Float, default=0.0)  # Amount already released to startup
    tx_signature = Column(String(88), nullable=False)  # Solana transaction signature
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="investments")
    investor = relationship("User", back_populates="investments")


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=True)  # Null if investor request
    investor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null if startup request
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=True)  # Relevant for investor reclaim
    request_type = Column(String(20), nullable=False)  # startup_withdrawal, investor_reclaim
    amount = Column(Float, nullable=False)  # Requested amount to withdraw
    reason = Column(String(1000), nullable=False)  # Reason for withdrawal
    status = Column(String(20), default="pending")  # pending, approved, rejected
    admin_feedback = Column(String(1000), nullable=True)  # Admin feedback on rejection/approval
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="withdrawal_requests")
