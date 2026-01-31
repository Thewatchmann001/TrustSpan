from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Float, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ========== ORIGINAL CV ==========
    original_file_url = Column(String(500), nullable=True)  # URL to uploaded PDF/image
    original_file_name = Column(String(255), nullable=True)  # Original filename
    
    # ========== PARSED DATA ==========
    json_content = Column(JSON, nullable=False)  # Full CV data as JSON (parsed from original)
    
    # ========== ATS ANALYSIS ==========
    ats_score = Column(Float, nullable=True)  # Overall ATS score (0-100)
    ats_grade = Column(String(5), nullable=True)  # Grade (A+, A, B, C, D)
    ats_analysis = Column(JSON, nullable=True)  # Detailed ATS analysis with breakdown
    ats_issues = Column(JSON, nullable=True)  # List of specific ATS issues found
    ats_recommendations = Column(JSON, nullable=True)  # List of recommended improvements
    
    # ========== ATS OPTIMIZATION ==========
    ats_optimized_content = Column(JSON, nullable=True)  # Optimized CV content (separate version)
    ats_changes = Column(JSON, nullable=True)  # Detailed list of changes made [{"before": ..., "after": ..., "reason": ...}]
    ats_optimized_at = Column(DateTime, nullable=True)  # When optimization was applied
    
    # ========== METADATA ==========
    photo_url = Column(String(500), nullable=True)  # URL/path to user photo
    ai_score = Column(Float, nullable=True)  # AI-generated quality score (different from ATS)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cvs")
    applications = relationship("JobApplication", back_populates="cv")

