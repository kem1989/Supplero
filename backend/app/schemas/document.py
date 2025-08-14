from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.document import DocumentStatus, DocumentType, DocumentFormat


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload"""
    filename: str = Field(..., description="Original filename")
    document_type: Optional[DocumentType] = Field(None, description="Document type (auto-detected if not provided)")
    organization_id: int = Field(..., description="Organization ID")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags for categorization")
    priority: Optional[int] = Field(default=1, ge=1, le=5, description="Processing priority (1=low, 5=high)")


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    document_id: int
    filename: str
    status: DocumentStatus
    message: str
    upload_timestamp: datetime


class DocumentStatusResponse(BaseModel):
    """Response schema for document processing status"""
    document_id: int
    filename: str
    status: DocumentStatus
    document_type: DocumentType
    document_format: DocumentFormat
    upload_timestamp: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    extracted_text_length: int = 0
    metadata_count: int = 0


class ExtractedMetadata(BaseModel):
    """Schema for extracted document metadata"""
    dates: List[Dict[str, Any]] = Field(default=[], description="Extracted dates with context")
    amounts: List[Dict[str, Any]] = Field(default=[], description="Extracted monetary amounts")
    parties: List[Dict[str, Any]] = Field(default=[], description="Extracted party names and roles")
    document_type: Optional[str] = Field(None, description="Detected document type (contract, invoice, etc.)")
    language: Optional[str] = Field(None, description="Detected document language")
    confidence_score: int = Field(..., ge=0, le=100, description="Overall confidence in extraction")


class DocumentProcessingResult(BaseModel):
    """Response schema for completed document processing"""
    document_id: int
    filename: str
    status: DocumentStatus
    document_type: DocumentType
    document_format: DocumentFormat
    
    # Content extraction
    extracted_text: Optional[str] = None
    extracted_metadata: Optional[ExtractedMetadata] = None
    confidence_score: Optional[int] = None
    
    # OCR details
    ocr_required: bool = False
    ocr_quality_score: Optional[int] = None
    
    # Processing details
    processing_duration_seconds: Optional[float] = None
    processed_at: datetime
    
    # File information
    file_size: int
    mime_type: str


class DocumentListResponse(BaseModel):
    """Response schema for document listing"""
    documents: List[DocumentStatusResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class DocumentSearchRequest(BaseModel):
    """Request schema for document search"""
    query: Optional[str] = Field(None, description="Search query (text or metadata)")
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DocumentVersionInfo(BaseModel):
    """Schema for document version information"""
    version_number: int
    file_path: str
    file_size: int
    change_summary: Optional[str] = None
    changed_by_user: str
    created_at: datetime


class DocumentVersionHistory(BaseModel):
    """Response schema for document version history"""
    document_id: int
    versions: List[Dict[str, Any]]
    total_versions: int


class ProcessingJobStatus(BaseModel):
    """Schema for processing job status"""
    job_id: int
    document_id: int
    job_type: str
    status: str
    priority: int
    progress_percentage: Optional[int] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    created_at: datetime


class DocumentFeedbackRequest(BaseModel):
    """Request schema for document processing feedback"""
    feedback_type: str = Field(..., description="Type of feedback (correction, confirmation, quality)")
    feedback_data: Dict[str, Any] = Field(..., description="Feedback-specific data")
    confidence_rating: Optional[int] = Field(None, ge=1, le=5, description="User confidence rating")
    notes: Optional[str] = Field(None, description="Additional notes or comments")


class DocumentFeedbackResponse(BaseModel):
    """Response schema for document feedback submission"""
    feedback_id: int
    document_id: int
    feedback_type: str
    status: str
    message: str
    submitted_at: datetime


class DocumentIngestionStats(BaseModel):
    """Schema for document ingestion statistics"""
    total_documents: int
    documents_by_status: Dict[DocumentStatus, int]
    documents_by_type: Dict[DocumentType, int]
    documents_by_format: Dict[DocumentFormat, int]
    average_processing_time: Optional[float] = None
    success_rate: float
    last_24_hours_uploaded: int
    last_24_hours_processed: int
