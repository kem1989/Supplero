import os
import io
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.document_ingestion import DocumentIngestionService
from app.core.document_storage import DocumentStorage
from app.core.document_processing import document_processing_service
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
        # Validate that user belongs to the specified organization
        if current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only upload documents to your own organization"
            )
        
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
        
        # Create document object in memory (not saved to DB yet)
        document = Document(
            original_filename=file.filename,
            organization_id=organization_id,
            user_id=current_user.id,
            tags=tag_list,
            priority=priority,
            status=DocumentStatus.UPLOADED,
            document_type=DocumentType.UNKNOWN,  # Will be detected during processing
            document_format=DocumentFormat.UNKNOWN,  # Will be detected during processing
            file_size=len(file_content),
            upload_date=datetime.utcnow()
        )
        
        # Process document completely before storing in database
        logger.info(f"Processing document {file.filename} before database storage...")
        
        # Process the document through the complete pipeline
        success = document_processing_service.process_document_in_memory(
            document, file_content, db
        )
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Document processing failed. Please try again."
            )
        
        # Only now save the processed document to database
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
            organization_id=organization_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document status and processing information"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_user.organization_id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentStatusResponse(
            document_id=document.id,
            filename=document.original_filename,
            status=document.status,
            document_type=document.document_type,
            document_format=document.document_format,
            upload_timestamp=document.created_at,
            processing_started_at=document.processing_started_at,
            processing_completed_at=document.processing_completed_at,
            error_message=document.error_message,
            extracted_text_length=len(document.extracted_text) if document.extracted_text else 0,
            metadata_count=len(document.extracted_metadata) if document.extracted_metadata else 0
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
    status: Optional[str] = Query(None),  # Changed from DocumentStatus to str to handle comma-separated values
    document_type: Optional[DocumentType] = Query(None),
    tags: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with pagination and filtering"""
    
    try:
        # Build query with organization filtering
        query = db.query(Document).filter(
            Document.organization_id == current_user.organization_id
        ).filter(
            Document.status != DocumentStatus.ARCHIVED.value  # Exclude archived documents
        )
        
        # Apply filters
        if status:
            # Handle comma-separated status values
            status_list = [s.strip() for s in status.split(",") if s.strip()]
            if status_list:
                # Validate status values against the enum
                valid_statuses = []
                for status_val in status_list:
                    # Check if the status value exists in the enum values
                    if status_val in [status.value for status in DocumentStatus]:
                        valid_statuses.append(status_val)
                    else:
                        # Skip invalid status values
                        logger.warning(f"Invalid status value: {status_val}")
                        continue
                
                if valid_statuses:
                    # Filter by any of the valid statuses
                    query = query.filter(Document.status.in_(valid_statuses))
        if document_type:
            query = query.filter(Document.document_type == document_type)
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            # TODO: Implement tag-based filtering
        
        # Get total count (excluding archived documents)
        total_count = query.count()
        
        # Apply pagination and ordering
        documents = query.order_by(desc(Document.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return DocumentListResponse(
            documents=[
                DocumentStatusResponse(
                    document_id=doc.id,
                    filename=doc.original_filename,
                    status=doc.status,
                    document_type=doc.document_type,
                    document_format=doc.document_format,
                    upload_timestamp=doc.created_at,
                    processing_started_at=doc.processing_started_at,
                    processing_completed_at=doc.processing_completed_at,
                    error_message=doc.error_message,
                    extracted_text_length=len(doc.extracted_text) if doc.extracted_text else 0,
                    metadata_count=len(doc.extracted_metadata) if doc.extracted_metadata else 0
                ) for doc in documents
            ],
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list documents",
            error=str(e)
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
                Document.organization_id == current_user.organization_id
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


@router.post("/process-pending")
async def process_pending_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process all pending documents for the user's organization"""
    
    try:
        # Get count of pending documents
        pending_count = db.query(Document).filter(
            and_(
                Document.organization_id == current_user.organization_id,
                Document.status == DocumentStatus.UPLOADED
            )
        ).count()
        
        if pending_count == 0:
            return {"message": "No pending documents to process", "pending_count": 0}
        
        # Start processing in background
        # Process synchronously to avoid async task issues
        # In production, you'd use a proper task queue like Celery
        processed_count = document_processing_service.process_pending_documents(db)
        
        logger.info(
            "Started processing pending documents",
            user_id=current_user.id,
            pending_count=pending_count
        )
        
        return {
            "message": f"Successfully processed {processed_count} out of {pending_count} pending documents",
            "pending_count": pending_count,
            "processed_count": processed_count
        }
        
    except Exception as e:
        logger.error(
            "Failed to start pending document processing",
            error=str(e),
            user_id=current_user.id
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
                Document.organization_id == current_user.organization_id
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
                Document.organization_id == current_user.organization_id
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # TODO: Implement version history
        # For now, return basic info
        return DocumentVersionHistory(
            document_id=document_id,
            versions=[
                {
                    "version": 1,
                    "created_at": document.created_at,
                    "status": document.status,
                    "user_id": document.user_id
                }
            ],
            total_versions=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document versions",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve document versions")


@router.get("/stats/ingestion", response_model=DocumentIngestionStats)
async def get_ingestion_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document ingestion statistics"""
    
    try:
        # Get total documents for user's organization (excluding archived)
        total_documents = db.query(Document).filter(
            and_(
                Document.organization_id == current_user.organization_id,
                Document.status != DocumentStatus.ARCHIVED.value
            )
        ).count()
        
        # Get documents by status for user's organization (excluding archived)
        documents_by_status = {}
        for status in DocumentStatus:
            if status != DocumentStatus.ARCHIVED:  # Skip archived status
                count = db.query(Document).filter(
                    and_(
                        Document.status == status,
                        Document.organization_id == current_user.organization_id
                    )
                ).count()
                documents_by_status[status] = count
        
        # Get documents by type for user's organization (excluding archived)
        documents_by_type = {}
        for doc_type in DocumentType:
            count = db.query(Document).filter(
                and_(
                    Document.document_type == doc_type,
                    Document.organization_id == current_user.organization_id
                )
            ).count()
            documents_by_type[doc_type] = count
        
        # Get documents by format for user's organization (excluding archived)
        documents_by_format = {}
        for format_type in DocumentFormat:
            count = db.query(Document).filter(
                and_(
                    Document.document_format == format_type,
                    Document.organization_id == current_user.organization_id
                )
            ).count()
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
    """Delete document (soft delete - mark as archived)
    
    Note: This performs a soft delete by marking the document as archived.
    Archived documents are excluded from all list queries and statistics.
    """
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_user.organization_id
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


@router.post("/{document_id}/restore")
async def restore_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore an archived document"""
    
    try:
        document = db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == current_user.organization_id,
                Document.status == DocumentStatus.ARCHIVED
            )
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Archived document not found")
        
        # Restore to uploaded status
        document.status = DocumentStatus.UPLOADED
        db.commit()
        
        logger.info(
            "Document restored from archive",
            document_id=document_id,
            user_id=current_user.id
        )
        
        return {"message": "Document restored successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to restore document",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to restore document")
