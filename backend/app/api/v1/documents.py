import os
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.document_ingestion import DocumentIngestionService
from app.core.document_storage import DocumentStorage
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus, DocumentType, DocumentFormat
from app.models.user import User
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentListResponse,
    DocumentSearchRequest,
    DocumentProcessingResult,
    DocumentVersionHistory,
    ProcessingJobStatus,
    DocumentFeedbackRequest,
    DocumentFeedbackResponse,
    DocumentIngestionStats
)

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    organization_id: int = Form(...),
    tags: Optional[str] = Form(None),
    priority: Optional[int] = Form(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for ingestion and processing"""
    
    try:
        # For now, allow any organization_id (will be enhanced with proper org validation later)
        # TODO: Implement proper organization access validation
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Read file content
        file_content = await file.read()
        
        # Initialize services
        document_storage = DocumentStorage()
        ingestion_service = DocumentIngestionService(document_storage)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Ingest document
        document = await ingestion_service.ingest_document(
            file_content=file_content,
            original_filename=file.filename,
            organization_id=organization_id,
            user_id=current_user.id,
            tags=tag_list
        )
        
        # Save to database
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(
            "Document uploaded successfully",
            document_id=document.id,
            filename=file.filename,
            organization_id=organization_id,
            user_id=current_user.id
        )
        
        return DocumentUploadResponse(
            document_id=document.id,
            filename=file.filename,
            status=document.status,
            message="Document uploaded successfully",
            upload_timestamp=document.created_at
        )
        
    except Exception as e:
        logger.error(
            "Document upload failed",
            filename=file.filename if file else "unknown",
            error=str(e),
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document processing status"""
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentStatusResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            document_type=document.document_type,
            document_format=document.document_format,
            progress_percentage=None,  # TODO: Implement progress tracking
            estimated_completion=None,  # TODO: Implement ETA calculation
            processing_error=document.processing_error,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document status",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve document status")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with pagination and filtering"""
    
    try:
        # Build query
        query = db.query(Document)  # TODO: Add organization filtering when org validation is implemented
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        if status:
            query = query.filter(Document.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        documents = query.order_by(desc(Document.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # Convert to response models
        document_responses = []
        for doc in documents:
            doc_response = DocumentStatusResponse(
                document_id=doc.id,
                filename=doc.filename,
                status=doc.status,
                document_type=doc.document_type,
                document_format=doc.document_format,
                progress_percentage=None,
                estimated_completion=None,
                processing_error=doc.processing_error,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            document_responses.append(doc_response)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return DocumentListResponse(
            documents=document_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list documents",
            error=str(e),
            organization_id=current_org.id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.post("/{document_id}/process")
async def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger document processing"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_org.id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.status == DocumentStatus.PROCESSED:
            raise HTTPException(status_code=400, detail="Document already processed")
        
        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        # TODO: Queue processing job in background worker
        
        logger.info(
            "Document processing triggered",
            document_id=document_id,
            user_id=current_user.id
        )
        
        return {"message": "Document processing started", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to trigger document processing",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to start processing")


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download document file"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_org.id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file from document storage
        document_storage = DocumentStorage()
        file_content = await document_storage.get_file(document.file_path)
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=document.mime_type,
            headers={"Content-Disposition": f"attachment; filename={document.original_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to download document",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to download document")


@router.get("/{document_id}/versions", response_model=DocumentVersionHistory)
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document version history"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_org.id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # TODO: Implement version history retrieval
        # For now, return basic document info
        
        return DocumentVersionHistory(
            document_id=document.id,
            filename=document.filename,
            current_version=document.version,
            versions=[]  # TODO: Populate with actual versions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document versions",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve version history")


@router.get("/stats/ingestion", response_model=DocumentIngestionStats)
async def get_ingestion_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document ingestion statistics"""
    
    try:
        # Get total documents
        total_documents = db.query(Document).count()  # TODO: Add organization filtering
        
        # Get documents by status
        documents_by_status = {}
        for status in DocumentStatus:
            count = db.query(Document).filter(Document.status == status).count()
            documents_by_status[status] = count
        
        # Get documents by type
        documents_by_type = {}
        for doc_type in DocumentType:
            count = db.query(Document).filter(Document.document_type == doc_type).count()
            documents_by_type[doc_type] = count
        
        # Get documents by format
        documents_by_format = {}
        for format_type in DocumentFormat:
            count = db.query(Document).filter(Document.document_format == format_type).count()
            documents_by_format[format_type] = count
        
        # Calculate success rate
        processed_count = documents_by_status.get(DocumentStatus.PROCESSED, 0)
        failed_count = documents_by_status.get(DocumentStatus.FAILED, 0)
        total_processed = processed_count + failed_count
        success_rate = (processed_count / total_processed * 100) if total_processed > 0 else 0
        
        # TODO: Implement more sophisticated statistics
        
        return DocumentIngestionStats(
            total_documents=total_documents,
            documents_by_status=documents_by_status,
            documents_by_type=documents_by_type,
            documents_by_format=documents_by_format,
            average_processing_time=None,  # TODO: Calculate from processing logs
            success_rate=success_rate,
            last_24_hours_uploaded=0,  # TODO: Calculate from timestamps
            last_24_hours_processed=0   # TODO: Calculate from timestamps
        )
        
    except Exception as e:
        logger.error(
            "Failed to get ingestion stats",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document (soft delete - mark as archived)"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_org.id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Soft delete - mark as archived
        document.status = DocumentStatus.ARCHIVED
        db.commit()
        
        logger.info(
            "Document archived",
            document_id=document_id,
            user_id=current_user.id
        )
        
        return {"message": "Document archived successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to archive document",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to archive document")
