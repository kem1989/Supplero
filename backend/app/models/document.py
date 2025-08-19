from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    OCR_PROCESSING = "OCR_PROCESSING"  # Added OCR processing status
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "PDF"
    DOCX = "DOCX"
    IMAGE = "IMAGE"  # For scanned images
    TXT = "TXT"
    LEGACY = "LEGACY"  # Legacy formats that need conversion
    UNKNOWN = "UNKNOWN"


class DocumentFormat(str, Enum):
    """Document format categories"""
    DIGITAL = "DIGITAL"  # Native digital format (PDF, DOCX)
    SCANNED = "SCANNED"  # Scanned images
    LEGACY = "LEGACY"    # Legacy formats that need conversion


class Document(Base):
    """Document model for storing ingested documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Document classification
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_format = Column(SQLEnum(DocumentFormat), nullable=False)
    
    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Content extraction results
    extracted_text = Column(Text, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)  # Dates, amounts, parties, etc.
    confidence_score = Column(Integer, nullable=True)  # 0-100 confidence in extraction
    
    # OCR and processing details
    ocr_required = Column(String(5), default="false")  # SQLite boolean
    ocr_quality_score = Column(Integer, nullable=True)  # 0-100 OCR quality
    
    # Version control
    version = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="documents")
    user = relationship("User", back_populates="documents")
    parent_document = relationship("Document", remote_side=[id])
    child_documents = relationship("Document", back_populates="parent_document")
    versions = relationship("DocumentVersion", back_populates="document")
    processing_jobs = relationship("DocumentProcessingJob", back_populates="document")
    clauses = relationship("ContractClause", back_populates="document")
    
    # Audit trail - TODO: Add proper audit logging relationship when AuditLog model is updated
    # audit_logs = relationship("AuditLog", back_populates="document")


class ContractClause(Base):
    """Model for storing extracted contract clauses"""
    __tablename__ = "contract_clauses"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    clause_type = Column(String(100), nullable=False)  # force_majeure, export_control, etc.
    clause_text = Column(Text, nullable=False)
    extracted_text = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high, critical
    confidence_score = Column(Integer, nullable=True)  # 0-100 confidence
    ai_analysis = Column(JSON, nullable=True)  # AI analysis results
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="clauses")


class DocumentVersion(Base):
    """Document version history for change tracking"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Version-specific data
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)
    
    # Change tracking
    change_summary = Column(Text, nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    changed_by_user = relationship("User", back_populates="document_changes")


class DocumentProcessingJob(Base):
    """Background processing jobs for document ingestion"""
    __tablename__ = "document_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Job details
    job_type = Column(String(100), nullable=False)  # "ocr", "metadata_extraction", "format_conversion"
    status = Column(String(50), default="pending")  # "pending", "running", "completed", "failed"
    priority = Column(Integer, default=1)  # 1=low, 5=high
    
    # Processing details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    organization = relationship("Organization", back_populates="processing_jobs")
