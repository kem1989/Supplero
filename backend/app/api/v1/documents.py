import os
import io
from datetime import datetime
from typing import List, Optional, Any
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
        
        # Use the ingestion service to properly detect document type and format
        document = await ingestion_service.ingest_document(
            file_content=file_content,
            original_filename=file.filename or "unknown",
            organization_id=organization_id,
            user_id=current_user.id
        )
        
        # Save document to database
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process the document immediately to extract text and metadata
        try:
            logger.info(f"Starting immediate processing for document {document.id}")
            
            # Update status to PROCESSING
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.now()
            db.commit()
            
            # Extract text content
            text_content = await ingestion_service.extract_text_content(document)
            document.extracted_text = text_content
            
            # Extract metadata
            metadata = await ingestion_service.extract_metadata(document, text_content)
            document.extracted_metadata = metadata.dict()
            
            # Update status to PROCESSED
            document.status = DocumentStatus.PROCESSED
            document.processing_completed_at = datetime.now()
            document.processed_at = datetime.now()
            db.commit()
            
            # Extract clauses from the document using AI-powered analysis
            extracted_clauses = []
            try:
                from app.core.clause_extraction import ClauseExtractionService
                clause_service = ClauseExtractionService()
                
                logger.info(f"Starting clause extraction for document {document.id}")
                
                # Extract clauses using AI-powered analysis
                extracted_clauses = await clause_service.extract_clauses_from_document(
                    document_text=document.extracted_text,
                    document_id=str(document.id),
                    organization_id=str(document.organization_id)
                )
                
                logger.info(f"Clause extraction completed for document {document.id}: {len(extracted_clauses)} clauses found")
                
                # Store clauses in database (contract_clauses table)
                await store_clauses_in_database(extracted_clauses, document.id, db)
                
            except Exception as clause_error:
                logger.error(f"Clause extraction failed for document {document.id}: {clause_error}")
                # Don't fail the upload if clause extraction fails
                extracted_clauses = []
            
            # Index document in Elasticsearch for search (with clause data)
            try:
                from app.core.elasticsearch_service import ElasticsearchService
                es_service = ElasticsearchService()
                
                # Prepare document data for indexing with extracted clauses
                document_data = {
                    "document_id": str(document.id),
                    "organization_id": document.organization_id,
                    "filename": document.filename,
                    "original_filename": document.original_filename,
                    "extracted_text": document.extracted_text,
                    "extracted_metadata": document.extracted_metadata,
                    "extracted_clauses": [clause.to_dict() for clause in extracted_clauses],  # Add extracted clauses
                    "created_at": document.created_at.isoformat() if document.created_at else None,
                    "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                    "tags": []
                }
                
                # Index the document with clause data
                index_success = await es_service.index_contract_document(document_data)
                if index_success:
                    logger.info(f"Document {document.id} indexed in Elasticsearch with {len(extracted_clauses)} clauses successfully")
                else:
                    logger.warning(f"Failed to index document {document.id} in Elasticsearch")
                    
            except Exception as indexing_error:
                logger.error(f"Elasticsearch indexing failed for document {document.id}: {indexing_error}")
                # Don't fail the upload if indexing fails
            
            logger.info(f"Document {document.id} processed successfully")
            
        except Exception as processing_error:
            logger.error(f"Document processing failed for {document.id}: {processing_error}")
            document.status = DocumentStatus.FAILED
            document.processing_error = str(processing_error)
            document.error_message = str(processing_error)
            db.commit()
        
        logger.info(f"Document {file.filename} processed and saved to database with ID {document.id}")
        
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
            error=str(e),
            error_type=type(e).__name__
        )
        # Return more specific error details for debugging
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Document with this name already exists")
        elif "NOT NULL constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Missing required document information")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


async def store_clauses_in_database(
    extracted_clauses: List,
    document_id: int,
    db: Session
) -> bool:
    """Store extracted clauses in the contract_clauses table"""
    try:
        if not extracted_clauses:
            return True
        
        # Import the ContractClause model
        from app.models.document import ContractClause
        
        # Store each extracted clause
        for clause in extracted_clauses:
            clause_record = ContractClause(
                contract_id=document_id,
                clause_type=clause.clause_type.value,
                clause_text=clause.clause_text,
                extracted_text=clause.extracted_text,
                risk_level=clause.risk_level,
                confidence_score=clause.confidence_score,
                ai_analysis=clause.metadata
            )
            db.add(clause_record)
        
        # Commit all clauses
        db.commit()
        logger.info(f"Stored {len(extracted_clauses)} clauses in database for document {document_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store clauses in database for document {document_id}: {str(e)}")
        db.rollback()
        return False


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
            Document.status != DocumentStatus.ARCHIVED  # Exclude archived documents
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
                Document.status != DocumentStatus.ARCHIVED
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
    """Delete document (hard delete - permanently remove)
    
    Note: This performs a hard delete and permanently removes the document
    from both the database and Elasticsearch. This action cannot be undone.
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
        
        # Get document ID for Elasticsearch deletion before removing from database
        document_id_str = str(document_id)
        
        # Remove document from Elasticsearch search index first
        try:
            from app.core.elasticsearch_service import ElasticsearchService
            es_service = ElasticsearchService()
            
            # Check if document exists in Elasticsearch before deletion
            try:
                doc_exists = es_service.client.exists(
                    index=es_service.index_name,
                    id=document_id_str
                )
                logger.info(f"Document {document_id} exists in Elasticsearch: {doc_exists}")
                
                if doc_exists:
                    # Delete from Elasticsearch
                    delete_success = await es_service.delete_contract_document(document_id_str)
                    if delete_success:
                        logger.info(f"Document {document_id} removed from Elasticsearch successfully")
                    else:
                        logger.warning(f"Failed to remove document {document_id} from Elasticsearch")
                else:
                    logger.info(f"Document {document_id} not found in Elasticsearch, skipping deletion")
                    
            except Exception as es_check_error:
                logger.error(f"Failed to check if document {document_id} exists in Elasticsearch: {es_check_error}")
                
        except Exception as indexing_error:
            logger.error(f"Elasticsearch cleanup failed for document {document_id}: {indexing_error}")
            # Don't fail the delete operation if Elasticsearch cleanup fails
        
        # Hard delete from database - delete related data first due to foreign key constraints
        try:
            # Delete related contract clauses first
            from app.models.document import ContractClause
            clauses_deleted = db.query(ContractClause).filter(
                ContractClause.contract_id == document_id
            ).delete(synchronize_session=False)
            
            # Delete document versions
            from app.models.document import DocumentVersion
            versions_deleted = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).delete(synchronize_session=False)
            
            # Delete document processing jobs
            from app.models.document import DocumentProcessingJob
            jobs_deleted = db.query(DocumentProcessingJob).filter(
                DocumentProcessingJob.document_id == document_id
            ).delete(synchronize_session=False)
            
            # Finally delete the document itself
            db.delete(document)
            db.commit()
            
            logger.info(
                "Document permanently deleted",
                document_id=document_id,
                clauses_deleted=clauses_deleted,
                versions_deleted=versions_deleted,
                jobs_deleted=jobs_deleted,
                user_id=current_user.id
            )
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database deletion failed for document {document_id}: {db_error}")
            raise HTTPException(status_code=500, detail="Failed to delete document from database")
        
        return {"message": "Document permanently deleted successfully", "document_id": document_id}

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
        
        # Re-index document in Elasticsearch for search
        try:
            from app.core.elasticsearch_service import ElasticsearchService
            es_service = ElasticsearchService()
            
            # Prepare document data for indexing
            document_data = {
                "document_id": str(document.id),
                "organization_id": document.organization_id,
                "filename": document.filename,
                "original_filename": document.original_filename,
                "extracted_text": document.extracted_text,
                "extracted_metadata": document.extracted_metadata,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "tags": []
            }
            
            # Index the document
            index_success = await es_service.index_contract_document(document_data)
            if index_success:
                logger.info(f"Document {document.id} re-indexed in Elasticsearch successfully")
            else:
                logger.warning(f"Failed to re-index document {document.id} in Elasticsearch")
                
        except Exception as indexing_error:
            logger.error(f"Elasticsearch re-indexing failed for document {document.id}: {indexing_error}")
            # Don't fail the restore operation if indexing fails
        
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
