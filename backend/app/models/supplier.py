"""
Supplier model for supplier risk management and profiling.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, DECIMAL
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
    country = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # Business information
    company_size = Column(String(50), nullable=True)  # small, medium, large, enterprise
    revenue_range = Column(String(50), nullable=True)
    employee_count = Column(Integer, nullable=True)
    
    # Risk assessment - Updated to match Schema v2.0
    current_risk_score = Column(DECIMAL(5,2), nullable=False, default=0, index=True)
    current_risk_level = Column(String(20), nullable=False, default='LOW', index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    geopolitical_risk = Column(DECIMAL(5,2), nullable=True)
    financial_risk = Column(DECIMAL(5,2), nullable=True)
    operational_risk = Column(DECIMAL(5,2), nullable=True)
    compliance_risk = Column(DECIMAL(5,2), nullable=True)
    esg_risk = Column(DECIMAL(5,2), nullable=True)
    
    # Integration data
    external_id = Column(String(100), nullable=True, index=True)  # ID from ERP/P2P systems
    source_system = Column(String(100), nullable=True)  # e.g., "SAP Ariba", "Coupa"
    
    # Status and settings
    is_active = Column(Boolean, nullable=False, default=True)
    is_watchlisted = Column(Boolean, nullable=False, default=False, index=True)
    watchlist_reason = Column(Text, nullable=True)
    
    # Organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_risk_assessment = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    contract_parties = relationship("ContractParty", back_populates="supplier")
    esg_ratings = relationship("ESGRating", back_populates="supplier")
    financial_metrics = relationship("FinancialMetric", back_populates="supplier")
    compliance_monitoring = relationship("ComplianceMonitoring", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', current_risk_score={self.current_risk_score})>"





