"""
Enhanced Format Detection Engine

This module provides intelligent format detection and analysis for documents,
including confidence scoring, detailed format classification, and conversion
capabilities for the Data Normalization Layer Foundation.
"""

import os
import io
import magic
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

import PyPDF2
from docx import Document as DocxDocument
from PIL import Image
import pytesseract
import numpy as np
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class FormatConfidence(str, Enum):
    """Confidence levels for format detection"""
    HIGH = "high"      # 90-100% confidence
    MEDIUM = "medium"   # 70-89% confidence
    LOW = "low"         # 50-69% confidence
    UNCERTAIN = "uncertain"  # <50% confidence


class DocumentCategory(str, Enum):
    """High-level document categories"""
    CONTRACT = "contract"
    INVOICE = "invoice"
    PROPOSAL = "proposal"
    AGREEMENT = "agreement"
    STATEMENT = "statement"
    REPORT = "report"
    FORM = "form"
    CORRESPONDENCE = "correspondence"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    UNKNOWN = "unknown"


@dataclass
class FormatDetectionResult:
    """Result of format detection analysis"""
    detected_type: str
    detected_format: str
    mime_type: str
    confidence_score: int  # 0-100
    confidence_level: FormatConfidence
    category: DocumentCategory
    subcategory: Optional[str] = None
    features: Dict[str, Any] = None
    conversion_path: Optional[str] = None
    quality_indicators: Dict[str, Any] = None
    processing_recommendations: List[str] = None


class FormatDetectionEngine:
    """Enhanced format detection engine with intelligent analysis"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Enhanced MIME type mappings with confidence scores
        self.mime_type_mappings = {
            'application/pdf': {
                'type': 'pdf',
                'format': 'digital',
                'confidence': 95,
                'category': DocumentCategory.CONTRACT
            },
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
                'type': 'docx',
                'format': 'digital',
                'confidence': 98,
                'category': DocumentCategory.CONTRACT
            },
            'application/msword': {
                'type': 'doc',
                'format': 'legacy',
                'confidence': 90,
                'category': DocumentCategory.CONTRACT
            },
            'image/jpeg': {
                'type': 'image',
                'format': 'scanned',
                'confidence': 85,
                'category': DocumentCategory.UNKNOWN
            },
            'image/png': {
                'type': 'image',
                'format': 'scanned',
                'confidence': 85,
                'category': DocumentCategory.UNKNOWN
            },
            'image/tiff': {
                'type': 'image',
                'format': 'scanned',
                'confidence': 90,
                'category': DocumentCategory.UNKNOWN
            },
            'text/plain': {
                'type': 'txt',
                'format': 'digital',
                'confidence': 95,
                'category': DocumentCategory.CORRESPONDENCE
            },
            'application/rtf': {
                'type': 'rtf',
                'format': 'legacy',
                'confidence': 80,
                'category': DocumentCategory.CORRESPONDENCE
            }
        }
        
        # File signature patterns for binary analysis
        self.file_signatures = {
            b'%PDF': ('pdf', 'digital', 98),
            b'PK\x03\x04': ('docx', 'digital', 98),
            b'\xd0\xcf\x11\xe0': ('doc', 'legacy', 90),
            b'\xff\xd8\xff': ('jpeg', 'scanned', 95),
            b'\x89PNG\r\n\x1a\n': ('png', 'scanned', 95),
            b'II*\x00': ('tiff', 'scanned', 95),
            b'MM\x00*': ('tiff', 'scanned', 95),
            b'{\\rtf': ('rtf', 'legacy', 85),
        }
        
        # Content analysis patterns
        self.content_patterns = {
            'contract_indicators': [
                'agreement', 'contract', 'terms', 'conditions', 'parties',
                'effective date', 'termination', 'liability', 'indemnification'
            ],
            'invoice_indicators': [
                'invoice', 'bill', 'amount due', 'payment terms', 'tax',
                'subtotal', 'total', 'due date', 'account number'
            ],
            'proposal_indicators': [
                'proposal', 'quote', 'estimate', 'scope of work', 'deliverables',
                'timeline', 'cost breakdown', 'terms and conditions'
            ]
        }
    
    async def detect_format(
        self, 
        file_content: bytes, 
        original_filename: str,
        analyze_content: bool = True
    ) -> FormatDetectionResult:
        """
        Comprehensive format detection with confidence scoring
        
        Args:
            file_content: Raw file content bytes
            original_filename: Original filename for context
            analyze_content: Whether to perform deep content analysis
            
        Returns:
            FormatDetectionResult with detailed detection information
        """
        try:
            # Primary detection methods
            primary_result = self._primary_detection(file_content, original_filename)
            
            # Enhanced format determination
            enhanced_format = self._enhance_format_detection(
                primary_result, file_content, original_filename
            )
            
            # Content analysis for categorization
            if analyze_content and enhanced_format.confidence_score > 50:
                enhanced_format = await self._analyze_content_for_category(
                    enhanced_format, file_content
                )
            
            # Generate processing recommendations
            enhanced_format.processing_recommendations = self._generate_recommendations(
                enhanced_format
            )
            
            self.logger.info(
                "Format detection completed",
                filename=original_filename,
                detected_type=enhanced_format.detected_type,
                confidence_score=enhanced_format.confidence_score,
                category=enhanced_format.category.value
            )
            
            return enhanced_format
            
        except Exception as e:
            self.logger.error(
                "Format detection failed",
                filename=original_filename,
                error=str(e)
            )
            # Return fallback result
            return FormatDetectionResult(
                detected_type="unknown",
                detected_format="unknown",
                mime_type="application/octet-stream",
                confidence_score=0,
                confidence_level=FormatConfidence.UNCERTAIN,
                category=DocumentCategory.UNKNOWN,
                features={},
                processing_recommendations=["Manual review required"]
            )
    
    def _primary_detection(
        self, 
        file_content: bytes, 
        original_filename: str
    ) -> FormatDetectionResult:
        """Primary detection using MIME types and file signatures"""
        
        # Method 1: MIME type detection
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type in self.mime_type_mappings:
                mapping = self.mime_type_mappings[mime_type]
                return FormatDetectionResult(
                    detected_type=mapping['type'],
                    detected_format=mapping['format'],
                    mime_type=mime_type,
                    confidence_score=mapping['confidence'],
                    confidence_level=self._score_to_confidence(mapping['confidence']),
                    category=mapping['category'],
                    features={'detection_method': 'mime_type'}
                )
        except Exception as e:
            self.logger.warning(f"MIME type detection failed: {e}")
        
        # Method 2: File signature analysis
        for signature, (doc_type, doc_format, confidence) in self.file_signatures.items():
            if file_content.startswith(signature):
                return FormatDetectionResult(
                    detected_type=doc_type,
                    detected_format=doc_format,
                    mime_type=self._get_mime_from_type(doc_type),
                    confidence_score=confidence,
                    confidence_level=self._score_to_confidence(confidence),
                    category=DocumentCategory.UNKNOWN,
                    features={'detection_method': 'file_signature'}
                )
        
        # Method 3: File extension fallback
        file_extension = Path(original_filename).suffix.lower()
        if file_extension:
            extension_result = self._extension_based_detection(file_extension, file_content)
            if extension_result:
                return extension_result
        
        # Method 4: Content analysis fallback
        return self._content_based_detection(file_content, original_filename)
    
    def _enhance_format_detection(
        self, 
        result: FormatDetectionResult, 
        file_content: bytes, 
        original_filename: str
    ) -> FormatDetectionResult:
        """Enhance format detection with additional analysis"""
        
        enhanced_result = result
        
        # Analyze file structure and quality
        if result.detected_type == 'pdf':
            enhanced_result = self._enhance_pdf_detection(result, file_content)
        elif result.detected_type == 'image':
            enhanced_result = self._enhance_image_detection(result, file_content)
        elif result.detected_type == 'docx':
            enhanced_result = self._enhance_docx_detection(result, file_content)
        
        # Add quality indicators
        enhanced_result.quality_indicators = self._assess_quality(file_content, result)
        
        # Determine conversion path
        enhanced_result.conversion_path = self._determine_conversion_path(result)
        
        return enhanced_result
    
    def _enhance_pdf_detection(
        self, 
        result: FormatDetectionResult, 
        file_content: bytes
    ) -> FormatDetectionResult:
        """Enhanced PDF analysis"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            # Check if PDF contains text
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() or ""
            
            # Determine if scanned or digital
            if text_content.strip():
                result.detected_format = "digital"
                result.confidence_score = min(100, result.confidence_score + 5)
                result.features = {
                    **(result.features or {}),
                    'page_count': len(pdf_reader.pages),
                    'has_text': True,
                    'text_length': len(text_content)
                }
            else:
                result.detected_format = "scanned"
                result.confidence_score = min(100, result.confidence_score + 3)
                result.features = {
                    **(result.features or {}),
                    'page_count': len(pdf_reader.pages),
                    'has_text': False
                }
                
        except Exception as e:
            self.logger.warning(f"PDF enhancement failed: {e}")
            result.confidence_score = max(0, result.confidence_score - 10)
        
        return result
    
    def _enhance_image_detection(
        self, 
        result: FormatDetectionResult, 
        file_content: bytes
    ) -> FormatDetectionResult:
        """Enhanced image analysis"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Check image properties
            width, height = image.size
            mode = image.mode
            
            # Determine if likely scanned document
            if width > 800 and height > 1000:  # Typical document dimensions
                result.confidence_score = min(100, result.confidence_score + 5)
                result.features = {
                    **(result.features or {}),
                    'dimensions': f"{width}x{height}",
                    'mode': mode,
                    'likely_document': True
                }
            else:
                result.features = {
                    **(result.features or {}),
                    'dimensions': f"{width}x{height}",
                    'mode': mode,
                    'likely_document': False
                }
                
        except Exception as e:
            self.logger.warning(f"Image enhancement failed: {e}")
        
        return result
    
    def _enhance_docx_detection(
        self, 
        result: FormatDetectionResult, 
        file_content: bytes
    ) -> FormatDetectionResult:
        """Enhanced DOCX analysis"""
        try:
            doc = DocxDocument(io.BytesIO(file_content))
            
            # Analyze document structure
            paragraph_count = len(doc.paragraphs)
            table_count = len(doc.tables)
            
            result.features = {
                **(result.features or {}),
                'paragraph_count': paragraph_count,
                'table_count': table_count,
                'has_content': paragraph_count > 0 or table_count > 0
            }
            
            if paragraph_count > 0 or table_count > 0:
                result.confidence_score = min(100, result.confidence_score + 3)
                
        except Exception as e:
            self.logger.warning(f"DOCX enhancement failed: {e}")
        
        return result
    
    async def _analyze_content_for_category(
        self, 
        result: FormatDetectionResult, 
        file_content: bytes
    ) -> FormatDetectionResult:
        """Analyze content to determine document category"""
        
        try:
            # Extract text content
            text_content = await self._extract_text_content(file_content, result.detected_type)
            
            if not text_content:
                return result
            
            text_lower = text_content.lower()
            
            # Check for category indicators
            for category, indicators in self.content_patterns.items():
                matches = sum(1 for indicator in indicators if indicator in text_lower)
                if matches >= 2:  # At least 2 indicators to classify
                    if category == 'contract_indicators':
                        result.category = DocumentCategory.CONTRACT
                        result.confidence_score = min(100, result.confidence_score + 10)
                    elif category == 'invoice_indicators':
                        result.category = DocumentCategory.INVOICE
                        result.confidence_score = min(100, result.confidence_score + 10)
                    elif category == 'proposal_indicators':
                        result.category = DocumentCategory.PROPOSAL
                        result.confidence_score = min(100, result.confidence_score + 10)
                    break
            
            # Update confidence level
            result.confidence_level = self._score_to_confidence(result.confidence_score)
            
        except Exception as e:
            self.logger.warning(f"Content analysis failed: {e}")
        
        return result
    
    async def _extract_text_content(
        self, 
        file_content: bytes, 
        document_type: str
    ) -> Optional[str]:
        """Extract text content from document for analysis"""
        
        try:
            if document_type == 'pdf':
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() or ""
                return text_content
                
            elif document_type == 'docx':
                doc = DocxDocument(io.BytesIO(file_content))
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
                return text_content
                
            elif document_type == 'txt':
                return file_content.decode('utf-8', errors='ignore')
                
            elif document_type == 'image':
                # Use OCR for image text extraction
                image = Image.open(io.BytesIO(file_content))
                return pytesseract.image_to_string(image)
                
        except Exception as e:
            self.logger.warning(f"Text extraction failed: {e}")
        
        return None
    
    def _assess_quality(self, file_content: bytes, result: FormatDetectionResult) -> Dict[str, Any]:
        """Assess document quality and provide indicators"""
        
        quality_indicators = {
            'file_size_bytes': len(file_content),
            'file_size_mb': round(len(file_content) / (1024 * 1024), 2),
            'detection_confidence': result.confidence_score,
            'format_quality': 'high' if result.confidence_score >= 80 else 'medium' if result.confidence_score >= 60 else 'low'
        }
        
        # Add format-specific quality indicators
        if result.detected_type == 'pdf':
            quality_indicators.update(self._assess_pdf_quality(file_content))
        elif result.detected_type == 'image':
            quality_indicators.update(self._assess_image_quality(file_content))
        
        return quality_indicators
    
    def _assess_pdf_quality(self, file_content: bytes) -> Dict[str, Any]:
        """Assess PDF-specific quality indicators"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            return {
                'page_count': len(pdf_reader.pages),
                'pdf_version': pdf_reader.pdf_header,
                'is_encrypted': pdf_reader.is_encrypted,
                'has_metadata': bool(pdf_reader.metadata)
            }
        except Exception:
            return {'pdf_quality': 'unknown'}
    
    def _assess_image_quality(self, file_content: bytes) -> Dict[str, Any]:
        """Assess image-specific quality indicators"""
        try:
            image = Image.open(io.BytesIO(file_content))
            return {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'aspect_ratio': round(image.width / image.height, 2)
            }
        except:
            return {'image_quality': 'unknown'}
    
    def _determine_conversion_path(self, result: FormatDetectionResult) -> Optional[str]:
        """Determine the conversion path to standardized format"""
        
        if result.detected_type == 'pdf' and result.detected_format == 'digital':
            return 'pdf_to_standard'  # Already in good format
        elif result.detected_type == 'docx':
            return 'docx_to_standard'  # Convert to standardized structure
        elif result.detected_type == 'image':
            return 'image_to_standard'  # OCR + structure extraction
        elif result.detected_type == 'doc':
            return 'doc_to_standard'  # Legacy conversion
        else:
            return 'unknown_to_standard'  # Generic conversion
    
    def _generate_recommendations(self, result: FormatDetectionResult) -> List[str]:
        """Generate processing recommendations based on detection results"""
        
        recommendations = []
        
        if result.confidence_score < 70:
            recommendations.append("Manual review recommended due to low confidence")
        
        if result.detected_format == 'scanned':
            recommendations.append("OCR processing required for text extraction")
        
        if result.detected_type == 'legacy':
            recommendations.append("Format conversion recommended for compatibility")
        
        if result.category == DocumentCategory.UNKNOWN:
            recommendations.append("Content analysis recommended for categorization")
        
        if result.detected_type == 'image' and result.features and result.features.get('likely_document'):
            recommendations.append("Document structure analysis recommended")
        
        if not recommendations:
            recommendations.append("Standard processing pipeline suitable")
        
        return recommendations
    
    def _extension_based_detection(self, extension: str, file_content: bytes) -> Optional[FormatDetectionResult]:
        """Detect format based on file extension"""
        
        extension_mappings = {
            '.pdf': ('pdf', 'digital', 85),
            '.docx': ('docx', 'digital', 90),
            '.doc': ('doc', 'legacy', 80),
            '.jpg': ('jpeg', 'scanned', 80),
            '.jpeg': ('jpeg', 'scanned', 80),
            '.png': ('png', 'scanned', 80),
            '.tiff': ('tiff', 'scanned', 85),
            '.tif': ('tiff', 'scanned', 85),
            '.txt': ('txt', 'digital', 90),
            '.rtf': ('rtf', 'legacy', 75)
        }
        
        if extension in extension_mappings:
            doc_type, doc_format, confidence = extension_mappings[extension]
            return FormatDetectionResult(
                detected_type=doc_type,
                detected_format=doc_format,
                mime_type=self._get_mime_from_type(doc_type),
                confidence_score=confidence,
                confidence_level=self._score_to_confidence(confidence),
                category=DocumentCategory.UNKNOWN,
                features={'detection_method': 'file_extension'}
            )
        
        return None
    
    def _content_based_detection(self, file_content: bytes, original_filename: str) -> FormatDetectionResult:
        """Fallback content-based detection"""
        
        # Check for common patterns in binary content
        if file_content.startswith(b'%PDF'):
            return FormatDetectionResult(
                detected_type='pdf',
                detected_format='digital',
                mime_type='application/pdf',
                confidence_score=70,
                confidence_level=FormatConfidence.MEDIUM,
                category=DocumentCategory.UNKNOWN,
                features={'detection_method': 'content_analysis'}
            )
        
        # Default to unknown
        return FormatDetectionResult(
            detected_type='unknown',
            detected_format='unknown',
            mime_type='application/octet-stream',
            confidence_score=0,
            confidence_level=FormatConfidence.UNCERTAIN,
            category=DocumentCategory.UNKNOWN,
            features={'detection_method': 'content_analysis'},
            processing_recommendations=["Manual format identification required"]
        )
    
    def _score_to_confidence(self, score: int) -> FormatConfidence:
        """Convert numerical score to confidence level"""
        if score >= 90:
            return FormatConfidence.HIGH
        elif score >= 70:
            return FormatConfidence.MEDIUM
        elif score >= 50:
            return FormatConfidence.LOW
        else:
            return FormatConfidence.UNCERTAIN
    
    def _get_mime_from_type(self, doc_type: str) -> str:
        """Get MIME type from document type"""
        mime_mappings = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tiff': 'image/tiff',
            'txt': 'text/plain',
            'rtf': 'application/rtf'
        }
        return mime_mappings.get(doc_type, 'application/octet-stream')
