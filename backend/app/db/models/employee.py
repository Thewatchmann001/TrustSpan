from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    wallet_address = Column(String(88), nullable=True)  # Solana wallet address
    certificate_id = Column(String(100), nullable=True)  # Certificate ID if verified
    verified_on_chain = Column(Boolean, default=False)  # Whether verified on blockchain
    transaction_signature = Column(String(88), nullable=True)  # Blockchain transaction signature
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="employees")
