"""
Document Processing Service

This service orchestrates the document processing pipeline, moving documents
through different statuses and coordinating various processing steps.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus, DocumentType, DocumentFormat
from app.core.ocr_preprocessing import OCRPreprocessor

logger = get_logger(__name__)


class DocumentProcessingService:
    """Service to orchestrate document processing pipeline"""
    
    def __init__(self):
        self.ocr_preprocessor = OCRPreprocessor()
    
    def _detect_document_type(self, filename: str, content: bytes) -> DocumentType:
        """Detect document type based on filename and content"""
        # Simple detection based on file extension
        if filename.lower().endswith('.pdf'):
            return DocumentType.PDF
        elif filename.lower().endswith('.txt'):
            return DocumentType.TXT
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return DocumentType.IMAGE
        else:
            return DocumentType.UNKNOWN
    
    def _detect_document_format(self, filename: str) -> DocumentFormat:
        """Detect document format based on filename"""
        if filename.lower().endswith('.pdf'):
            return DocumentFormat.DIGITAL
        elif filename.lower().endswith('.txt'):
            return DocumentFormat.DIGITAL
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return DocumentFormat.SCANNED
        else:
            return DocumentFormat.UNKNOWN
    
    def process_document_in_memory(self, document: Document, file_content: bytes, db: Session) -> bool:
        """Process a document completely in memory before database storage"""
        try:
            logger.info(f"Processing document in memory: {document.original_filename}")
            
            # Step 1: Detect document type and format
            document.document_type = self._detect_document_type(document.original_filename, file_content)
            document.document_format = self._detect_document_format(document.original_filename)
            
            # Step 2: Move to PROCESSING status
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.now(timezone.utc)
            logger.info(f"Document {document.original_filename} moved to PROCESSING status")
            
            # Simulate processing time
            time.sleep(2)
            
            # Step 3: Move to OCR_PROCESSING (simulate OCR requirement)
            document.status = DocumentStatus.OCR_PROCESSING
            document.ocr_required = "true"
            logger.info(f"Document {document.original_filename} moved to OCR_PROCESSING status")
            
            # Simulate OCR processing time
            time.sleep(3)
            
            # Step 4: Move to PROCESSED status
            document.status = DocumentStatus.PROCESSED
            document.processing_completed_at = datetime.now(timezone.utc)
            document.processed_at = datetime.now(timezone.utc)
            
            logger.info(f"Document {document.original_filename} processing completed successfully in memory")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document.original_filename} in memory: {str(e)}")
            
            # Mark as failed
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            document.processing_completed_at = datetime.now(timezone.utc)
            return False
    
    async def process_document(self, document_id: int, db: Session) -> bool:
        """Process a document through the complete pipeline"""
        try:
            # Get the document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return False
            
            logger.info(f"Starting processing for document {document_id}: {document.original_filename}")
            
            # Step 1: Move to PROCESSING status
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Document {document_id} moved to PROCESSING status")
            
            # Simulate processing time
            time.sleep(2)
            
            # Step 2: Move to OCR_PROCESSING if OCR is needed
            if document.ocr_required == "true":
                document.status = DocumentStatus.OCR_PROCESSING
                db.commit()
                logger.info(f"Document {document_id} moved to OCR_PROCESSING status")
                
                # Simulate OCR processing time
                time.sleep(3)
            
            # Step 3: Move to PROCESSED status
            document.status = DocumentStatus.PROCESSED
            document.processing_completed_at = datetime.now(timezone.utc)
            document.processed_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Document {document_id} processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Mark as failed
            try:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                document.processing_completed_at = datetime.utcnow()
                db.commit()
            except:
                pass
            
            return False
    
    def process_pending_documents(self, db: Session) -> int:
        """Process all documents that are in UPLOADED status"""
        try:
            # Get all documents in UPLOADED status
            pending_documents = db.query(Document).filter(
                Document.status == DocumentStatus.UPLOADED
            ).all()
            
            logger.info(f"Found {len(pending_documents)} pending documents to process")
            
            if not pending_documents:
                logger.info("No pending documents found")
                return 0
            
            processed_count = 0
            for document in pending_documents:
                logger.info(f"Processing document {document.id}: {document.original_filename}")
                # Note: process_document is async, but we're calling it synchronously here
                # In production, you'd use a proper task queue
                try:
                    success = asyncio.run(self.process_document(document.id, db))
                    if success:
                        processed_count += 1
                        logger.info(f"Document {document.id} processed successfully")
                    else:
                        logger.error(f"Document {document.id} processing failed")
                except Exception as e:
                    logger.error(f"Failed to process document {document.id}: {e}")
                
                # Small delay between documents
                time.sleep(1)
            
            logger.info(f"Successfully processed {processed_count} out of {len(pending_documents)} documents")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return 0


# Global instance
document_processing_service = DocumentProcessingService()
