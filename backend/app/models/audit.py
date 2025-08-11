"""
Audit log models for comprehensive activity tracking and compliance.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """Audit log model for tracking all user and system actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_logs_organization_id', 'organization_id'),
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
    )


class AIRequest(Base):
    """AI request tracking for compliance and cost monitoring."""
    
    __tablename__ = "ai_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_type = Column(String(100), nullable=False)
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(String, nullable=True)  # Redacted prompt length
    completion_tokens = Column(String, nullable=True)  # Redacted response length
    total_tokens = Column(String, nullable=True)  # Redacted total
    processing_time_ms = Column(String, nullable=True)  # Redacted timing
    cost_usd = Column(String, nullable=True)  # Redacted cost
    status = Column(String(50), default="completed")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ai_requests_organization_id', 'organization_id'),
        Index('idx_ai_requests_created_at', 'created_at'),
        Index('idx_ai_requests_request_type', 'request_type'),
        Index('idx_ai_requests_status', 'status'),
    ) 