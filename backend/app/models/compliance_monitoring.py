"""
Compliance Monitoring model for consolidated compliance, sanctions, and news monitoring.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ComplianceMonitoring(Base):
    """Consolidated compliance, sanctions, and news monitoring for suppliers."""
    
    __tablename__ = "compliance_monitoring"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Monitoring type and source
    monitoring_type = Column(String(50), nullable=False)  # SANCTIONS, NEWS, COMPLIANCE
    source = Column(String(100), nullable=False)  # Data source
    
    # Content information
    title = Column(String(500), nullable=False)  # Title/headline
    description = Column(Text, nullable=True)  # Description content
    url = Column(String(500), nullable=True)  # URL if applicable
    
    # Risk assessment
    severity_level = Column(String(20), nullable=True)  # Severity level
    risk_score = Column(DECIMAL(5,2), nullable=True)  # Risk impact score
    sentiment_score = Column(DECIMAL(4,2), nullable=True)  # Sentiment score (-1 to 1)
    match_confidence = Column(DECIMAL(4,2), nullable=True)  # Match confidence (0 to 1)
    
    # Status and management
    status = Column(String(50), nullable=False, default='ACTIVE')  # Status
    adjudication = Column(String(50), nullable=True)  # Review status
    
    # Keywords and metadata
    keywords = Column(Text, nullable=True)  # Array of keywords as text
    
    # Publication and creation timestamps
    published_at = Column(DateTime(timezone=True), nullable=True)  # Publication date
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="compliance_monitoring")
    organization = relationship("Organization", back_populates="compliance_monitoring")
    
    def __repr__(self):
        return f"<ComplianceMonitoring(id={self.id}, supplier_id={self.supplier_id}, monitoring_type='{self.monitoring_type}', title='{self.title[:50]}...')>"
