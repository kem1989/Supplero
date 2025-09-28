"""
Financial Metric model for financial performance and health metrics.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FinancialMetric(Base):
    """Financial performance and health metrics for suppliers."""
    
    __tablename__ = "financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Period information
    period_start = Column(Date, nullable=False)  # Period start date
    period_end = Column(Date, nullable=False)  # Period end date
    currency = Column(String(3), nullable=False, default='USD')  # Currency code
    
    # Financial performance metrics
    revenue = Column(DECIMAL(15,2), nullable=True)  # Revenue amount
    profit_margin = Column(DECIMAL(5,2), nullable=True)  # Profit margin percentage
    
    # Financial health ratios
    debt_to_equity = Column(DECIMAL(5,2), nullable=True)  # Debt to equity ratio
    current_ratio = Column(DECIMAL(5,2), nullable=True)  # Current ratio
    quick_ratio = Column(DECIMAL(5,2), nullable=True)  # Quick ratio
    
    # Credit and health scores
    credit_rating = Column(String(10), nullable=True)  # Credit rating (e.g., AAA, AA+, etc.)
    financial_health_score = Column(DECIMAL(5,2), nullable=True)  # Overall financial health score
    
    # Data source information
    source = Column(String(100), nullable=True)  # Data source (e.g., "SEC Filings", "Annual Report")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="financial_metrics")
    organization = relationship("Organization", back_populates="financial_metrics")
    
    def __repr__(self):
        return f"<FinancialMetric(id={self.id}, supplier_id={self.supplier_id}, period_end='{self.period_end}', revenue={self.revenue})>"
