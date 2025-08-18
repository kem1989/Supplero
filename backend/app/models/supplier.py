"""
Supplier model for supplier risk management and profiling.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Supplier(Base):
    """Supplier model for supplier risk management and profiling."""
    
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic supplier information
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # Business information
    company_size = Column(String(50), nullable=True)  # small, medium, large, enterprise
    revenue_range = Column(String(100), nullable=True)
    employee_count = Column(Integer, nullable=True)
    
    # Risk assessment
    risk_score = Column(Float, default=0.0, nullable=False, index=True)
    risk_level = Column(String(20), default="LOW", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSON, nullable=True)  # JSON object storing risk factor details
    
    # Integration data
    external_id = Column(String(255), nullable=True, index=True)  # ID from ERP/P2P systems
    source_system = Column(String(100), nullable=True)  # e.g., "SAP Ariba", "Coupa"
    
    # Status and settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_watchlisted = Column(Boolean, default=False, nullable=False, index=True)
    watchlist_reason = Column(Text, nullable=True)
    
    # Organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_risk_assessment = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    risk_assessments = relationship("SupplierRiskAssessment", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', risk_score={self.risk_score})>"


class SupplierRiskAssessment(Base):
    """Model for tracking supplier risk assessment history."""
    
    __tablename__ = "supplier_risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Assessment details
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_factors = Column(JSON, nullable=True)
    assessment_method = Column(String(100), nullable=False)  # e.g., "rule_based", "ml_model", "manual"
    
    # Data sources used
    data_sources = Column(JSON, nullable=True)  # List of data sources used
    news_sentiment = Column(Float, nullable=True)
    financial_health = Column(String(50), nullable=True)
    compliance_status = Column(String(50), nullable=True)
    
    # Assessment metadata
    assessed_by = Column(String(100), nullable=True)  # User or system that performed assessment
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="risk_assessments")
    
    def __repr__(self):
        return f"<SupplierRiskAssessment(id={self.id}, supplier_id={self.supplier_id}, risk_score={self.risk_score})>"

