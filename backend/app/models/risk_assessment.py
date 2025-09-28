"""
Risk Assessment model for unified risk assessments across all entities.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RiskAssessment(Base):
    """Unified risk assessments for all entities (suppliers, contracts, etc.)."""
    
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # supplier, contract, etc.
    entity_id = Column(Integer, nullable=False)  # ID of the entity being assessed
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # initial, periodic, triggered, etc.
    
    # Overall assessment scores
    overall_score = Column(DECIMAL(5,2), nullable=False)
    overall_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Detailed risk scores
    geopolitical_score = Column(DECIMAL(5,2), nullable=True)
    financial_score = Column(DECIMAL(5,2), nullable=True)
    operational_score = Column(DECIMAL(5,2), nullable=True)
    compliance_score = Column(DECIMAL(5,2), nullable=True)
    esg_score = Column(DECIMAL(5,2), nullable=True)
    
    # Assessment metadata
    methodology = Column(String(100), nullable=True)  # Assessment methodology used
    data_sources = Column(Text, nullable=True)  # Array of data sources as text
    key_factors = Column(Text, nullable=True)  # Array of key risk factors as text
    reasoning = Column(Text, nullable=True)  # Assessment reasoning and notes
    assessor = Column(String(100), nullable=True)  # Who performed the assessment
    
    # Timestamps
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="risk_assessments")
    
    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, overall_score={self.overall_score})>"
