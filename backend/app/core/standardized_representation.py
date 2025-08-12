"""
Standardized Internal Representation System

This module provides a unified data structure for representing documents
regardless of their original format, enabling consistent processing and
analysis across the Data Normalization Layer Foundation.
"""

import io
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import PyPDF2
from docx import Document as DocxDocument
from PIL import Image
import pytesseract

from app.core.logging import get_logger
from app.core.format_detection import FormatDetectionResult, DocumentCategory

logger = get_logger(__name__)


class ContentType(str, Enum):
    """Types of content in standardized representation"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    HEADER = "header"
    FOOTER = "footer"
    SIGNATURE = "signature"
    METADATA = "metadata"


class ContentQuality(str, Enum):
    """Quality assessment of extracted content"""
    EXCELLENT = "excellent"  # 90-100% confidence
    GOOD = "good"           # 70-89% confidence
    FAIR = "fair"           # 50-69% confidence
    POOR = "poor"           # <50% confidence


@dataclass
class ContentBlock:
    """Represents a block of content in the standardized format"""
    content_type: ContentType
    content: str
    confidence_score: int  # 0-100
    quality: ContentQuality
    position: Dict[str, Any] = field(default_factory=dict)  # Page, coordinates, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional properties
    extracted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StandardizedDocument:
    """Standardized internal representation of any document"""
    
    # Document identification
    document_id: str
    original_filename: str
    source_format: str
    source_format_details: FormatDetectionResult
    
    # Content structure
    content_blocks: List[ContentBlock] = field(default_factory=list)
    
    # Extracted metadata
    extracted_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Quality metrics
    overall_confidence: int = 0  # 0-100
    processing_quality: ContentQuality = ContentQuality.POOR
    
    # Processing information
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_duration: float = 0.0  # seconds
    
    # Version and tracking
    version: int = 1
    processing_pipeline: str = "standard"
    
    def add_content_block(self, block: ContentBlock):
        """Add a content block to the document"""
        self.content_blocks.append(block)
        self._update_quality_metrics()
    
    def get_content_by_type(self, content_type: ContentType) -> List[ContentBlock]:
        """Get all content blocks of a specific type"""
        return [block for block in self.content_blocks if block.content_type == content_type]
    
    def get_text_content(self) -> str:
        """Get all text content concatenated"""
        text_blocks = self.get_content_by_type(ContentType.TEXT)
        return "\n".join([block.content for block in text_blocks])
    
    def get_tables(self) -> List[ContentBlock]:
        """Get all table content blocks"""
        return self.get_content_by_type(ContentType.TABLE)
    
    def _update_quality_metrics(self):
        """Update overall quality metrics based on content blocks"""
        if not self.content_blocks:
            return
        
        total_confidence = sum(block.confidence_score for block in self.content_blocks)
        avg_confidence = total_confidence / len(self.content_blocks)
        
        self.overall_confidence = int(avg_confidence)
        self.processing_quality = self._score_to_quality(self.overall_confidence)
    
    def _score_to_quality(self, score: int) -> ContentQuality:
        """Convert numerical score to quality level"""
        if score >= 90:
            return ContentQuality.EXCELLENT
        elif score >= 70:
            return ContentQuality.GOOD
        elif score >= 50:
            return ContentQuality.FAIR
        else:
            return ContentQuality.POOR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            'document_id': self.document_id,
            'original_filename': self.original_filename,
            'source_format': self.source_format,
            'source_format_details': {
                'detected_type': self.source_format_details.detected_type,
                'detected_format': self.source_format_details.detected_format,
                'confidence_score': self.source_format_details.confidence_score,
                'category': self.source_format_details.category.value
            },
            'content_blocks': [
                {
                    'content_type': block.content_type.value,
                    'content': block.content,
                    'confidence_score': block.confidence_score,
                    'quality': block.quality.value,
                    'position': block.position,
                    'metadata': block.metadata,
                    'extracted_at': block.extracted_at.isoformat()
                }
                for block in self.content_blocks
            ],
            'extracted_metadata': self.extracted_metadata,
            'overall_confidence': self.overall_confidence,
            'processing_quality': self.processing_quality.value,
            'processed_at': self.processed_at.isoformat(),
            'processing_duration': self.processing_duration,
            'version': self.version,
            'processing_pipeline': self.processing_pipeline
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardizedDocument':
        """Create instance from dictionary"""
        # This is a simplified version - in production you'd want more robust parsing
        return cls(
            document_id=data['document_id'],
            original_filename=data['original_filename'],
            source_format=data['source_format'],
            source_format_details=FormatDetectionResult(
                detected_type=data['source_format_details']['detected_type'],
                detected_format=data['source_format_details']['detected_format'],
                mime_type="",  # Not stored in this format
                confidence_score=data['source_format_details']['confidence_score'],
                confidence_level=None,  # Will be computed
                category=DocumentCategory(data['source_format_details']['category']),
                features={},
                conversion_path=None,
                quality_indicators={},
                processing_recommendations=[]
            ),
            content_blocks=[],  # Would need to parse content blocks
            extracted_metadata=data.get('extracted_metadata', {}),
            overall_confidence=data.get('overall_confidence', 0),
            processing_quality=ContentQuality(data.get('processing_quality', 'poor')),
            processed_at=datetime.fromisoformat(data['processed_at']),
            processing_duration=data.get('processing_duration', 0.0),
            version=data.get('version', 1),
            processing_pipeline=data.get('processing_pipeline', 'standard')
        )


class StandardizationEngine:
    """Engine for converting various document formats to standardized representation"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def standardize_document(
        self,
        file_content: bytes,
        format_result: FormatDetectionResult,
        original_filename: str,
        document_id: str
    ) -> StandardizedDocument:
        """
        Convert document to standardized internal representation
        
        Args:
            file_content: Raw file content
            format_result: Result from format detection
            original_filename: Original filename
            document_id: Unique document identifier
            
        Returns:
            StandardizedDocument instance
        """
        start_time = datetime.utcnow()
        
        try:
            # Create standardized document
            std_doc = StandardizedDocument(
                document_id=document_id,
                original_filename=original_filename,
                source_format=format_result.detected_type,
                source_format_details=format_result
            )
            
            # Convert based on format
            if format_result.detected_type == 'pdf':
                await self._standardize_pdf(file_content, std_doc, format_result)
            elif format_result.detected_type == 'docx':
                await self._standardize_docx(file_content, std_doc, format_result)
            elif format_result.detected_type == 'image':
                await self._standardize_image(file_content, std_doc, format_result)
            elif format_result.detected_type == 'txt':
                await self._standardize_text(file_content, std_doc, format_result)
            else:
                await self._standardize_generic(file_content, std_doc, format_result)
            
            # Calculate processing duration
            end_time = datetime.utcnow()
            std_doc.processing_duration = (end_time - start_time).total_seconds()
            std_doc.processed_at = end_time
            
            # Update quality metrics
            std_doc._update_quality_metrics()
            
            self.logger.info(
                "Document standardization completed",
                document_id=document_id,
                filename=original_filename,
                format=format_result.detected_type,
                content_blocks=len(std_doc.content_blocks),
                overall_confidence=std_doc.overall_confidence,
                processing_duration=std_doc.processing_duration
            )
            
            return std_doc
            
        except Exception as e:
            self.logger.error(
                "Document standardization failed",
                document_id=document_id,
                filename=original_filename,
                error=str(e)
            )
            raise
    
    async def _standardize_pdf(
        self, 
        file_content: bytes, 
        std_doc: StandardizedDocument,
        format_result: FormatDetectionResult
    ):
        """Standardize PDF document"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            for page_num, page in enumerate(pdf_reader.pages):
                # Extract text content
                text_content = page.extract_text()
                if text_content and text_content.strip():
                    # Create text content block
                    text_block = ContentBlock(
                        content_type=ContentType.TEXT,
                        content=text_content.strip(),
                        confidence_score=85 if format_result.detected_format == 'digital' else 70,
                        quality=ContentQuality.GOOD if format_result.detected_format == 'digital' else ContentQuality.FAIR,
                        position={'page': page_num + 1, 'type': 'full_page'},
                        metadata={'page_number': page_num + 1}
                    )
                    std_doc.add_content_block(text_block)
                
                # Extract tables if present (simplified - would need more sophisticated table detection)
                # This is a placeholder for actual table extraction logic
                
                # Extract headers/footers if detectable
                # This would require more sophisticated PDF analysis
                
        except Exception as e:
            self.logger.warning(f"PDF standardization failed: {e}")
            # Add fallback content block
            fallback_block = ContentBlock(
                content_type=ContentType.TEXT,
                content="[PDF content extraction failed]",
                confidence_score=0,
                quality=ContentQuality.POOR,
                metadata={'error': str(e)}
            )
            std_doc.add_content_block(fallback_block)
    
    async def _standardize_docx(
        self, 
        file_content: bytes, 
        std_doc: StandardizedDocument,
        format_result: FormatDetectionResult
    ):
        """Standardize DOCX document"""
        try:
            doc = DocxDocument(io.BytesIO(file_content))
            
            # Extract paragraphs
            for para_num, paragraph in enumerate(doc.paragraphs):
                if paragraph.text.strip():
                    # Determine if this is a header
                    content_type = ContentType.HEADER if paragraph.style.name.startswith('Heading') else ContentType.TEXT
                    
                    text_block = ContentBlock(
                        content_type=content_type,
                        content=paragraph.text.strip(),
                        confidence_score=90,
                        quality=ContentQuality.EXCELLENT,
                        position={'paragraph': para_num + 1, 'style': paragraph.style.name},
                        metadata={'style': paragraph.style.name, 'paragraph_number': para_num + 1}
                    )
                    std_doc.add_content_block(text_block)
            
            # Extract tables
            for table_num, table in enumerate(doc.tables):
                table_content = []
                for row in table.rows:
                    row_content = []
                    for cell in row.cells:
                        row_content.append(cell.text.strip())
                    table_content.append(" | ".join(row_content))
                
                if table_content:
                    table_block = ContentBlock(
                        content_type=ContentType.TABLE,
                        content="\n".join(table_content),
                        confidence_score=85,
                        quality=ContentQuality.GOOD,
                        position={'table': table_num + 1},
                        metadata={'table_number': table_num + 1, 'rows': len(table_content)}
                    )
                    std_doc.add_content_block(table_block)
                    
        except Exception as e:
            self.logger.warning(f"DOCX standardization failed: {e}")
            fallback_block = ContentBlock(
                content_type=ContentType.TEXT,
                content="[DOCX content extraction failed]",
                confidence_score=0,
                quality=ContentQuality.POOR,
                metadata={'error': str(e)}
            )
            std_doc.add_content_block(fallback_block)
    
    async def _standardize_image(
        self, 
        file_content: bytes, 
        std_doc: StandardizedDocument,
        format_result: FormatDetectionResult
    ):
        """Standardize image document using OCR"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Perform OCR
            text_content = pytesseract.image_to_string(image)
            
            if text_content and text_content.strip():
                # Create text content block from OCR
                text_block = ContentBlock(
                    content_type=ContentType.TEXT,
                    content=text_content.strip(),
                    confidence_score=75,  # OCR typically has lower confidence
                    quality=ContentQuality.FAIR,
                    position={'type': 'full_image'},
                    metadata={
                        'ocr_engine': 'pytesseract',
                        'image_dimensions': f"{image.width}x{image.height}",
                        'image_mode': image.mode
                    }
                )
                std_doc.add_content_block(text_block)
            else:
                # No text detected
                no_text_block = ContentBlock(
                    content_type=ContentType.TEXT,
                    content="[No text detected in image]",
                    confidence_score=0,
                    quality=ContentQuality.POOR,
                    position={'type': 'full_image'},
                    metadata={
                        'ocr_engine': 'pytesseract',
                        'image_dimensions': f"{image.width}x{image.height}",
                        'image_mode': image.mode,
                        'no_text_detected': True
                    }
                )
                std_doc.add_content_block(no_text_block)
                
        except Exception as e:
            self.logger.warning(f"Image standardization failed: {e}")
            fallback_block = ContentBlock(
                content_type=ContentType.TEXT,
                content="[Image processing failed]",
                confidence_score=0,
                quality=ContentQuality.POOR,
                metadata={'error': str(e)}
            )
            std_doc.add_content_block(fallback_block)
    
    async def _standardize_text(
        self, 
        file_content: bytes, 
        std_doc: StandardizedDocument,
        format_result: FormatDetectionResult
    ):
        """Standardize plain text document"""
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
            
            for para_num, paragraph in enumerate(paragraphs):
                text_block = ContentBlock(
                    content_type=ContentType.TEXT,
                    content=paragraph,
                    confidence_score=95,
                    quality=ContentQuality.EXCELLENT,
                    position={'paragraph': para_num + 1},
                    metadata={'paragraph_number': para_num + 1}
                )
                std_doc.add_content_block(text_block)
                
        except Exception as e:
            self.logger.warning(f"Text standardization failed: {e}")
            fallback_block = ContentBlock(
                content_type=ContentType.TEXT,
                content="[Text processing failed]",
                confidence_score=0,
                quality=ContentQuality.POOR,
                metadata={'error': str(e)}
            )
            std_doc.add_content_block(fallback_block)
    
    async def _standardize_generic(
        self, 
        file_content: bytes, 
        std_doc: StandardizedDocument,
        format_result: FormatDetectionResult
    ):
        """Standardize generic/unknown format document"""
        try:
            # Try to extract any readable content
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Look for readable text patterns
            readable_chars = sum(1 for c in text_content if c.isprintable() and not c.isspace())
            total_chars = len(text_content)
            
            if readable_chars > total_chars * 0.7:  # More than 70% readable
                # Likely text content
                await self._standardize_text(file_content, std_doc, format_result)
            else:
                # Binary or encoded content
                fallback_block = ContentBlock(
                    content_type=ContentType.TEXT,
                    content="[Binary content - manual review required]",
                    confidence_score=0,
                    quality=ContentQuality.POOR,
                    position={'type': 'binary_content'},
                    metadata={
                        'file_size': len(file_content),
                        'readable_ratio': readable_chars / total_chars if total_chars > 0 else 0
                    }
                )
                std_doc.add_content_block(fallback_block)
                
        except Exception as e:
            self.logger.warning(f"Generic standardization failed: {e}")
            fallback_block = ContentBlock(
                content_type=ContentType.TEXT,
                content="[Generic processing failed]",
                confidence_score=0,
                quality=ContentQuality.POOR,
                metadata={'error': str(e)}
            )
            std_doc.add_content_block(fallback_block)
    
    def extract_metadata_from_standardized(
        self, 
        std_doc: StandardizedDocument
    ) -> Dict[str, Any]:
        """Extract metadata from standardized document"""
        
        metadata = {
            'document_type': std_doc.source_format_details.category.value,
            'content_blocks_count': len(std_doc.content_blocks),
            'text_blocks_count': len(std_doc.get_content_by_type(ContentType.TEXT)),
            'table_blocks_count': len(std_doc.get_content_by_type(ContentType.TABLE)),
            'overall_confidence': std_doc.overall_confidence,
            'processing_quality': std_doc.processing_quality.value,
            'processing_duration': std_doc.processing_duration,
            'total_text_length': len(std_doc.get_text_content())
        }
        
        # Add format-specific metadata
        if std_doc.source_format == 'pdf':
            pdf_blocks = [b for b in std_doc.content_blocks if b.metadata.get('page_number')]
            if pdf_blocks:
                metadata['page_count'] = max(b.metadata['page_number'] for b in pdf_blocks)
        
        return metadata
