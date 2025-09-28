"""
ESG Rating model for Environmental, Social, and Governance ratings.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ESGRating(Base):
    """Environmental, Social, and Governance ratings for suppliers."""
    
    __tablename__ = "esg_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Rating provider information
    provider = Column(String(100), nullable=False)  # Rating provider (e.g., MSCI, Sustainalytics)
    rating_period = Column(Date, nullable=False)  # Period for which rating applies
    methodology_version = Column(String(50), nullable=True)  # Version of methodology used
    
    # Overall ESG scores
    overall_score = Column(DECIMAL(5,2), nullable=True)  # Overall ESG score
    overall_rating = Column(String(10), nullable=True)  # Overall ESG rating (A+, A, B+, etc.)
    
    # Individual ESG component scores
    environmental_score = Column(DECIMAL(5,2), nullable=True)  # Environmental score
    social_score = Column(DECIMAL(5,2), nullable=True)  # Social score
    governance_score = Column(DECIMAL(5,2), nullable=True)  # Governance score
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="esg_ratings")
    organization = relationship("Organization", back_populates="esg_ratings")
    
    def __repr__(self):
        return f"<ESGRating(id={self.id}, supplier_id={self.supplier_id}, provider='{self.provider}', overall_rating='{self.overall_rating}')>"
