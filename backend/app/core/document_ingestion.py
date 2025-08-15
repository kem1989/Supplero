import os
import io
import magic
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging

import PyPDF2
from docx import Document as DocxDocument
from PIL import Image
import pytesseract
from pydantic import ValidationError

from app.models.document import Document, DocumentType, DocumentFormat, DocumentStatus
from app.schemas.document import ExtractedMetadata
from app.core.document_storage import DocumentStorage
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentIngestionService:
    """Universal document ingestion service supporting multiple formats"""
    
    def __init__(self, document_storage: DocumentStorage):
        self.document_storage = document_storage
        self.supported_mime_types = {
            'application/pdf': DocumentType.PDF,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DocumentType.DOCX,
            'image/jpeg': DocumentType.IMAGE,
            'image/png': DocumentType.IMAGE,
            'image/tiff': DocumentType.IMAGE,
            'text/plain': DocumentType.TXT,
        }
        
        # File extensions for fallback detection
        self.extension_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.LEGACY,
            '.jpg': DocumentType.IMAGE,
            '.jpeg': DocumentType.IMAGE,
            '.png': DocumentType.IMAGE,
            '.tiff': DocumentType.IMAGE,
            '.tif': DocumentType.IMAGE,
            '.txt': DocumentType.TXT,
        }
    
    async def ingest_document(
        self,
        file_content: bytes,
        original_filename: str,
        organization_id: int,
        user_id: int,
        tags: Optional[List[str]] = None
    ) -> Document:
        """Main entry point for document ingestion"""
        
        try:
            # Detect document type and format
            document_type, document_format, mime_type = self._detect_document_type(file_content, original_filename)
            
            # Generate secure filename and store file
            secure_filename = self._generate_secure_filename(original_filename)
            file_path = await self._store_file(file_content, secure_filename, organization_id)
            
            # Create document record
            document = Document(
                organization_id=organization_id,
                user_id=user_id,
                filename=secure_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=len(file_content),
                mime_type=mime_type,
                document_type=document_type,
                document_format=document_format,
                status=DocumentStatus.UPLOADED
            )
            
            # Determine if OCR is needed
            document.ocr_required = self._needs_ocr(document_type, document_format)
            
            logger.info(
                "Document ingested successfully",
                document_id=document.id,
                filename=original_filename,
                document_type=document_type,
                document_format=document_format,
                ocr_required=document.ocr_required,
                organization_id=organization_id
            )
            
            return document
            
        except Exception as e:
            logger.error(
                "Document ingestion failed",
                filename=original_filename,
                error=str(e),
                organization_id=organization_id
            )
            raise
    
    def _detect_document_type(
        self, 
        file_content: bytes, 
        original_filename: str
    ) -> Tuple[DocumentType, DocumentFormat, str]:
        """Detect document type and format using multiple methods"""
        
        # Method 1: MIME type detection using python-magic
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type in self.supported_mime_types:
                document_type = self.supported_mime_types[mime_type]
                document_format = self._determine_format(document_type, file_content)
                return document_type, document_format, mime_type
        except Exception as e:
            logger.warning(f"MIME type detection failed: {e}")
        
        # Method 2: File extension fallback
        file_extension = Path(original_filename).suffix.lower()
        if file_extension in self.extension_mapping:
            document_type = self.extension_mapping[file_extension]
            document_format = self._determine_format(document_type, file_content)
            mime_type = self._get_mime_type_from_extension(file_extension)
            return document_type, document_format, mime_type
        
        # Method 3: Content analysis fallback
        document_type = self._analyze_content(file_content)
        document_format = self._determine_format(document_type, file_content)
        mime_type = "application/octet-stream"
        
        return document_type, document_format, mime_type
    
    def _determine_format(self, document_type: DocumentType, file_content: bytes) -> DocumentFormat:
        """Determine if document is digital, scanned, or legacy"""
        
        if document_type == DocumentType.IMAGE:
            # Check if image contains text (likely scanned)
            try:
                image = Image.open(io.BytesIO(file_content))
                # Use OCR to check if image contains text
                text = pytesseract.image_to_string(image)
                if text.strip():
                    return DocumentFormat.SCANNED
                else:
                    return DocumentFormat.DIGITAL
            except Exception:
                return DocumentFormat.SCANNED
        
        elif document_type == DocumentType.PDF:
            # Check if PDF contains text or is scanned
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() or ""
                
                if text_content.strip():
                    return DocumentFormat.DIGITAL
                else:
                    return DocumentFormat.SCANNED
            except Exception:
                return DocumentFormat.LEGACY
        
        elif document_type == DocumentType.DOCX:
            return DocumentFormat.DIGITAL
        
        elif document_type == DocumentType.LEGACY:
            return DocumentFormat.LEGACY
        
        return DocumentFormat.DIGITAL  # Default to digital for unknown formats
    
    def _analyze_content(self, file_content: bytes) -> DocumentType:
        """Analyze file content to determine document type"""
        
        # Check for PDF signature
        if file_content.startswith(b'%PDF'):
            return DocumentType.PDF
        
        # Check for DOCX signature (ZIP file with specific structure)
        if file_content.startswith(b'PK\x03\x04'):
            return DocumentType.DOCX
        
        # Check for image signatures
        image_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'II*\x00',  # TIFF little-endian
            b'MM\x00*',  # TIFF big-endian
        ]
        
        for signature in image_signatures:
            if file_content.startswith(signature):
                return DocumentType.IMAGE
        
        # Check for text content
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            if text_content.strip():
                return DocumentType.TXT
        except Exception:
            pass
        
        return DocumentType.UNKNOWN
    
    def _needs_ocr(self, document_type: DocumentType, document_format: DocumentFormat) -> bool:
        """Determine if document needs OCR processing"""
        
        if document_format == DocumentFormat.SCANNED:
            return True
        
        if document_type == DocumentType.IMAGE:
            return True
        
        if document_format == DocumentFormat.LEGACY:
            return True
        
        return False
    
    def _generate_secure_filename(self, original_filename: str) -> str:
        """Generate a secure, unique filename"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.sha256(original_filename.encode()).hexdigest()[:16]
        extension = Path(original_filename).suffix
        
        return f"{timestamp}_{file_hash}{extension}"
    
    async def _store_file(
        self, 
        file_content: bytes, 
        filename: str, 
        organization_id: int
    ) -> str:
        """Store file securely and return file path"""
        
        # Create organization-specific directory structure
        org_dir = f"uploads/{organization_id}/documents"
        file_path = f"{org_dir}/{filename}"
        
        # Store file using document storage
        await self.document_storage.store_file(file_path, file_content)
        
        return file_path
    
    def _get_mime_type_from_extension(self, extension: str) -> str:
        """Get MIME type from file extension"""
        
        mime_mapping = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.txt': 'text/plain',
        }
        
        return mime_mapping.get(extension, 'application/octet-stream')
    
    async def extract_text_content(self, document: Document) -> str:
        """Extract text content from document based on type"""
        
        try:
            file_content = await self.document_storage.get_file(document.file_path)
            
            if document.document_type == DocumentType.PDF:
                return self._extract_pdf_text(file_content)
            elif document.document_type == DocumentType.DOCX:
                return self._extract_docx_text(file_content)
            elif document.document_type == DocumentType.IMAGE:
                return self._extract_image_text(file_content)
            elif document.document_type == DocumentType.TXT:
                return self._extract_text_file(file_content)
            else:
                raise ValueError(f"Unsupported document type: {document.document_type}")
                
        except Exception as e:
            logger.error(
                "Text extraction failed",
                document_id=document.id,
                error=str(e)
            )
            raise
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = ""
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        
        try:
            doc = DocxDocument(io.BytesIO(file_content))
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            raise
    
    def _extract_image_text(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        
        try:
            image = Image.open(io.BytesIO(file_content))
            text_content = pytesseract.image_to_string(image)
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            raise
    
    def _extract_text_file(self, file_content: bytes) -> str:
        """Extract text from plain text file"""
        
        try:
            return file_content.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            logger.error(f"Text file extraction failed: {e}")
            raise
    
    async def extract_metadata(self, document: Document, text_content: str) -> ExtractedMetadata:
        """Extract metadata from document content"""
        
        try:
            metadata = ExtractedMetadata(
                dates=self._extract_dates(text_content),
                amounts=self._extract_amounts(text_content),
                parties=self._extract_parties(text_content),
                document_type=self._detect_document_category(text_content),
                language=self._detect_language(text_content),
                confidence_score=self._calculate_confidence_score(text_content)
            )
            
            return metadata
            
        except Exception as e:
            logger.error(
                "Metadata extraction failed",
                document_id=document.id,
                error=str(e)
            )
            raise
    
    def _extract_dates(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract dates from text content"""
        
        # This is a simplified implementation
        # In production, you'd use more sophisticated date parsing libraries
        import re
        
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                dates.append({
                    "value": match.group(),
                    "context": self._get_context(text_content, match.start(), match.end()),
                    "confidence": 80  # Basic confidence for regex matches
                })
        
        return dates
    
    def _extract_amounts(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text content"""
        
        import re
        
        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # $1,234.56
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP)',  # 1,234.56 USD
            r'(?:USD|EUR|GBP)\s*[\d,]+(?:\.\d{2})?',  # USD 1,234.56
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                amounts.append({
                    "value": match.group(),
                    "context": self._get_context(text_content, match.start(), match.end()),
                    "confidence": 85
                })
        
        return amounts
    
    def _extract_parties(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract party names from text content"""
        
        # This is a simplified implementation
        # In production, you'd use NER (Named Entity Recognition) or more sophisticated parsing
        
        parties = []
        
        # Look for common party indicators
        party_indicators = [
            "Party A", "Party B", "Buyer", "Seller", "Vendor", "Supplier",
            "Client", "Customer", "Contractor", "Subcontractor"
        ]
        
        for indicator in party_indicators:
            if indicator.lower() in text_content.lower():
                # Find the context around the indicator
                start_idx = text_content.lower().find(indicator.lower())
                context = self._get_context(text_content, start_idx, start_idx + len(indicator))
                
                parties.append({
                    "value": indicator,
                    "context": context,
                    "confidence": 70
                })
        
        return parties
    
    def _detect_document_category(self, text_content: str) -> Optional[str]:
        """Detect the category of document (contract, invoice, etc.)"""
        
        text_lower = text_content.lower()
        
        # Simple keyword-based detection
        if any(word in text_lower for word in ["contract", "agreement", "terms", "conditions"]):
            return "contract"
        elif any(word in text_lower for word in ["invoice", "bill", "payment", "amount due"]):
            return "invoice"
        elif any(word in text_lower for word in ["proposal", "quote", "estimate"]):
            return "proposal"
        elif any(word in text_lower for word in ["purchase order", "po", "order"]):
            return "purchase_order"
        else:
            return "unknown"
    
    def _detect_language(self, text_content: str) -> Optional[str]:
        """Detect the language of the document"""
        
        # This is a simplified implementation
        # In production, you'd use language detection libraries like langdetect
        
        # Simple heuristics for common languages
        text_lower = text_content.lower()
        
        if any(word in text_lower for word in ["the", "and", "or", "in", "on", "at"]):
            return "en"
        elif any(word in text_lower for word in ["der", "die", "das", "und", "oder"]):
            return "de"
        elif any(word in text_lower for word in ["le", "la", "les", "et", "ou", "dans"]):
            return "fr"
        else:
            return "unknown"
    
    def _calculate_confidence_score(self, text_content: str) -> int:
        """Calculate confidence score for extracted content"""
        
        # Simple confidence calculation based on content quality
        if not text_content.strip():
            return 0
        
        # Higher confidence for longer, well-formatted text
        lines = text_content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if len(non_empty_lines) < 5:
            return 30
        elif len(non_empty_lines) < 20:
            return 60
        else:
            return 85
    
    def _get_context(self, text_content: str, start: int, end: int) -> str:
        """Get context around a matched text"""
        
        context_size = 100
        start_context = max(0, start - context_size)
        end_context = min(len(text_content), end + context_size)
        
        return text_content[start_context:end_context].strip()
