"""
Contract-related models: contracts, parties, and clauses.
Updated to match Schema v2.0 structure.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    DECIMAL,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Contract(Base):
    """Contract-level entity with consolidated terms information."""

    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Core contract fields - Enhanced with consolidated terms
    title = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default='ACTIVE', index=True)
    contract_value = Column(DECIMAL(15,2), nullable=True)
    currency = Column(String(3), nullable=True, default='USD')
    effective_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    auto_renewal = Column(Boolean, nullable=False, default=False)
    renewal_term_months = Column(Integer, nullable=True)
    governing_law = Column(String(100), nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    
    # Consolidated contract terms
    payment_terms_days = Column(Integer, nullable=True)
    liability_cap_amount = Column(DECIMAL(15,2), nullable=True)
    liability_cap_type = Column(String(50), nullable=True)
    sla_uptime_percent = Column(DECIMAL(5,2), nullable=True)
    termination_notice_days = Column(Integer, nullable=True)
    penalty_rate_percent = Column(DECIMAL(5,2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="contracts")
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("ContractClause", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Contract(id={self.id}, title='{self.title}', status='{self.status}')>"


class ContractParty(Base):
    """Party involved in the contract (buyer/supplier/other)."""

    __tablename__ = "contract_parties"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)

    role = Column(String(50), nullable=False)  # buyer, supplier, etc.
    name = Column(String(255), nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)

    # Relationships
    contract = relationship("Contract", back_populates="parties")
    supplier = relationship("Supplier", back_populates="contract_parties")
    
    def __repr__(self):
        return f"<ContractParty(id={self.id}, role='{self.role}', name='{self.name}')>"


class ContractClause(Base):
    """Contract clause with risk scoring."""

    __tablename__ = "contract_clauses"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)

    clause_type = Column(String(100), nullable=False, index=True)
    risk_level = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(DECIMAL(5,2), nullable=True)
    text_excerpt = Column(Text, nullable=True)
    risk_factors = Column(Text, nullable=True)  # Array of risk factors stored as text
    mitigation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    
    def __repr__(self):
        return f"<ContractClause(id={self.id}, clause_type='{self.clause_type}', risk_level='{self.risk_level}')>"


