"""
Data Normalization Layer Foundation

This module provides the main service for intelligent format detection and
conversion to standardized internal representation, integrating all components
of the data normalization pipeline.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from app.core.logging import get_logger
from app.core.format_detection import FormatDetectionEngine, FormatDetectionResult
from app.core.standardized_representation import StandardizationEngine, StandardizedDocument
from app.core.quality_validation import QualityValidator, ValidationResult
from app.core.document_storage import DocumentStorage

logger = get_logger(__name__)


@dataclass
class NormalizationResult:
    """Result of the complete data normalization process"""
    
    # Document identification
    document_id: str
    original_filename: str
    
    # Format detection results
    format_detection: FormatDetectionResult
    
    # Standardization results
    standardized_document: StandardizedDocument
    
    # Quality validation results
    validation_result: ValidationResult
    
    # Processing metadata
    processing_duration: float  # seconds
    processing_timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            'document_id': self.document_id,
            'original_filename': self.original_filename,
            'format_detection': {
                'detected_type': self.format_detection.detected_type,
                'detected_format': self.format_detection.detected_format,
                'confidence_score': self.format_detection.confidence_score,
                'category': self.format_detection.category.value,
                'features': self.format_detection.features,
                'conversion_path': self.format_detection.conversion_path,
                'quality_indicators': self.format_detection.quality_indicators,
                'processing_recommendations': self.format_detection.processing_recommendations
            },
            'standardized_document': self.standardized_document.to_dict(),
            'validation_result': {
                'is_valid': self.validation_result.is_valid,
                'overall_score': self.validation_result.overall_score,
                'issues_count': len(self.validation_result.issues),
                'critical_issues': self.validation_result.critical_issues,
                'high_issues': self.validation_result.high_issues,
                'medium_issues': self.validation_result.medium_issues,
                'low_issues': self.validation_result.low_issues,
                'info_issues': self.validation_result.info_issues
            },
            'processing_duration': self.processing_duration,
            'processing_timestamp': self.processing_timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message
        }


class DataNormalizationService:
    """
    Main service for intelligent format detection and conversion to
    standardized internal representation
    """
    
    def __init__(self, document_storage: DocumentStorage):
        self.document_storage = document_storage
        self.format_detection_engine = FormatDetectionEngine()
        self.standardization_engine = StandardizationEngine()
        self.quality_validator = QualityValidator()
        self.logger = get_logger(__name__)
    
    async def normalize_document(
        self,
        file_content: bytes,
        original_filename: str,
        organization_id: int,
        user_id: int,
        analyze_content: bool = True,
        validate_quality: bool = True,
        store_result: bool = True
    ) -> NormalizationResult:
        """
        Complete data normalization pipeline for a document
        
        Args:
            file_content: Raw file content bytes
            original_filename: Original filename
            organization_id: Organization ID for storage
            user_id: User ID who uploaded the document
            analyze_content: Whether to perform deep content analysis
            validate_quality: Whether to perform quality validation
            store_result: Whether to store the result in document storage
            
        Returns:
            NormalizationResult with complete processing information
        """
        start_time = datetime.utcnow()
        document_id = str(uuid.uuid4())
        
        try:
            self.logger.info(
                "Starting document normalization",
                document_id=document_id,
                filename=original_filename,
                organization_id=organization_id,
                analyze_content=analyze_content,
                validate_quality=validate_quality
            )
            
            # Step 1: Intelligent Format Detection
            format_result = await self._detect_format(
                file_content, original_filename, analyze_content
            )
            
            # Step 2: Convert to Standardized Internal Representation
            standardized_doc = await self._standardize_document(
                file_content, format_result, original_filename, document_id
            )
            
            # Step 3: Quality Validation
            validation_result = None
            if validate_quality:
                validation_result = await self._validate_quality(standardized_doc)
            else:
                # Create a minimal validation result
                validation_result = self._create_minimal_validation_result(standardized_doc)
            
            # Step 4: Store result if requested
            if store_result:
                await self._store_normalization_result(
                    document_id, organization_id, user_id, format_result, 
                    standardized_doc, validation_result
                )
            
            # Calculate processing duration
            end_time = datetime.utcnow()
            processing_duration = (end_time - start_time).total_seconds()
            
            # Create result
            result = NormalizationResult(
                document_id=document_id,
                original_filename=original_filename,
                format_detection=format_result,
                standardized_document=standardized_doc,
                validation_result=validation_result,
                processing_duration=processing_duration,
                processing_timestamp=end_time,
                success=True
            )
            
            self.logger.info(
                "Document normalization completed successfully",
                document_id=document_id,
                filename=original_filename,
                processing_duration=processing_duration,
                format_detected=format_result.detected_type,
                confidence_score=format_result.confidence_score,
                content_blocks=len(standardized_doc.content_blocks),
                validation_score=validation_result.overall_score if validation_result else None
            )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_duration = (end_time - start_time).total_seconds()
            
            self.logger.error(
                "Document normalization failed",
                document_id=document_id,
                filename=original_filename,
                error=str(e),
                processing_duration=processing_duration
            )
            
            # Create error result
            error_result = NormalizationResult(
                document_id=document_id,
                original_filename=original_filename,
                format_detection=self._create_error_format_result(),
                standardized_document=self._create_error_standardized_doc(document_id, original_filename),
                validation_result=self._create_error_validation_result(),
                processing_duration=processing_duration,
                processing_timestamp=end_time,
                success=False,
                error_message=str(e)
            )
            
            return error_result
    
    async def _detect_format(
        self, 
        file_content: bytes, 
        original_filename: str, 
        analyze_content: bool
    ) -> FormatDetectionResult:
        """Perform intelligent format detection"""
        
        self.logger.debug(
            "Starting format detection",
            filename=original_filename,
            analyze_content=analyze_content
        )
        
        format_result = await self.format_detection_engine.detect_format(
            file_content, original_filename, analyze_content
        )
        
        self.logger.debug(
            "Format detection completed",
            filename=original_filename,
            detected_type=format_result.detected_type,
            confidence_score=format_result.confidence_score
        )
        
        return format_result
    
    async def _standardize_document(
        self, 
        file_content: bytes, 
        format_result: FormatDetectionResult, 
        original_filename: str, 
        document_id: str
    ) -> StandardizedDocument:
        """Convert document to standardized internal representation"""
        
        self.logger.debug(
            "Starting document standardization",
            document_id=document_id,
            filename=original_filename,
            format=format_result.detected_type
        )
        
        standardized_doc = await self.standardization_engine.standardize_document(
            file_content, format_result, original_filename, document_id
        )
        
        self.logger.debug(
            "Document standardization completed",
            document_id=document_id,
            content_blocks=len(standardized_doc.content_blocks),
            overall_confidence=standardized_doc.overall_confidence
        )
        
        return standardized_doc
    
    async def _validate_quality(
        self, 
        standardized_doc: StandardizedDocument
    ) -> ValidationResult:
        """Perform quality validation on standardized document"""
        
        self.logger.debug(
            "Starting quality validation",
            document_id=standardized_doc.document_id
        )
        
        validation_result = await self.quality_validator.validate_document(standardized_doc)
        
        self.logger.debug(
            "Quality validation completed",
            document_id=standardized_doc.document_id,
            is_valid=validation_result.is_valid,
            overall_score=validation_result.overall_score,
            issues_count=len(validation_result.issues)
        )
        
        return validation_result
    
    async def _store_normalization_result(
        self,
        document_id: str,
        organization_id: int,
        user_id: int,
        format_result: FormatDetectionResult,
        standardized_doc: StandardizedDocument,
        validation_result: ValidationResult
    ):
        """Store normalization result in document storage"""
        
        try:
            # Store the standardized document
            await self.document_storage.store_standardized_document(
                document_id=document_id,
                organization_id=organization_id,
                user_id=user_id,
                standardized_document=standardized_doc,
                format_detection=format_result,
                validation_result=validation_result
            )
            
            self.logger.debug(
                "Normalization result stored successfully",
                document_id=document_id
            )
            
        except Exception as e:
            self.logger.warning(
                "Failed to store normalization result",
                document_id=document_id,
                error=str(e)
            )
            # Don't fail the entire process if storage fails
    
    def _create_minimal_validation_result(self, standardized_doc: StandardizedDocument) -> ValidationResult:
        """Create a minimal validation result when validation is disabled"""
        from app.core.quality_validation import ValidationResult, ValidationIssue, ValidationRule, ValidationSeverity
        
        # Create a basic validation result that passes
        result = ValidationResult(
            is_valid=True,
            overall_score=100
        )
        
        # Add informational note
        result.add_issue(ValidationIssue(
            rule=ValidationRule.CONTENT_QUALITY,
            severity=ValidationSeverity.INFO,
            message="Quality validation was disabled for this document",
            field_path="validation_process"
        ))
        
        return result
    
    def _create_error_format_result(self) -> FormatDetectionResult:
        """Create error format detection result"""
        from app.core.format_detection import FormatDetectionResult, FormatConfidence, DocumentCategory
        
        return FormatDetectionResult(
            detected_type="unknown",
            detected_format="unknown",
            mime_type="application/octet-stream",
            confidence_score=0,
            confidence_level=FormatConfidence.UNCERTAIN,
            category=DocumentCategory.UNKNOWN,
            features={'error': True},
            conversion_path=None,
            quality_indicators={'error': True},
            processing_recommendations=["Reprocess document after fixing errors"]
        )
    
    def _create_error_standardized_doc(self, document_id: str, original_filename: str) -> StandardizedDocument:
        """Create error standardized document"""
        from app.core.standardized_representation import StandardizedDocument, ContentBlock, ContentType, ContentQuality
        from app.core.format_detection import FormatDetectionResult, DocumentCategory
        
        # Create error format result
        error_format = FormatDetectionResult(
            detected_type="unknown",
            detected_format="unknown",
            mime_type="application/octet-stream",
            confidence_score=0,
            confidence_level=None,
            category=DocumentCategory.UNKNOWN,
            features={},
            conversion_path=None,
            quality_indicators={},
            processing_recommendations=[]
        )
        
        # Create error document
        error_doc = StandardizedDocument(
            document_id=document_id,
            original_filename=original_filename,
            source_format="unknown",
            source_format_details=error_format
        )
        
        # Add error content block
        error_block = ContentBlock(
            content_type=ContentType.TEXT,
            content="[Document processing failed - error occurred]",
            confidence_score=0,
            quality=ContentQuality.POOR,
            metadata={'error': True}
        )
        error_doc.add_content_block(error_block)
        
        return error_doc
    
    def _create_error_validation_result(self) -> ValidationResult:
        """Create error validation result"""
        from app.core.quality_validation import ValidationResult, ValidationIssue, ValidationRule, ValidationSeverity
        
        result = ValidationResult(
            is_valid=False,
            overall_score=0
        )
        
        result.add_issue(ValidationIssue(
            rule=ValidationRule.CONTENT_QUALITY,
            severity=ValidationSeverity.CRITICAL,
            message="Document processing failed - cannot validate",
            field_path="processing",
            suggestion="Reprocess document after fixing errors"
        ))
        
        return result
    
    async def get_normalization_status(
        self, 
        document_id: str, 
        organization_id: int
    ) -> Optional[NormalizationResult]:
        """Get the status of a normalization process"""
        
        try:
            # Retrieve from document storage
            stored_result = await self.document_storage.get_standardized_document(
                document_id, organization_id
            )
            
            if stored_result:
                # Convert stored result back to NormalizationResult
                return self._reconstruct_normalization_result(stored_result)
            
            return None
            
        except Exception as e:
            self.logger.error(
                "Failed to get normalization status",
                document_id=document_id,
                error=str(e)
            )
            return None
    
    def _reconstruct_normalization_result(self, stored_data: Dict[str, Any]) -> NormalizationResult:
        """Reconstruct NormalizationResult from stored data"""
        
        # This is a simplified reconstruction - in production you'd want more robust parsing
        try:
            return NormalizationResult(
                document_id=stored_data.get('document_id', ''),
                original_filename=stored_data.get('original_filename', ''),
                format_detection=self._reconstruct_format_result(stored_data.get('format_detection', {})),
                standardized_document=StandardizedDocument.from_dict(stored_data.get('standardized_document', {})),
                validation_result=self._reconstruct_validation_result(stored_data.get('validation_result', {})),
                processing_duration=stored_data.get('processing_duration', 0.0),
                processing_timestamp=datetime.fromisoformat(stored_data.get('processing_timestamp', datetime.utcnow().isoformat())),
                success=stored_data.get('success', False),
                error_message=stored_data.get('error_message')
            )
        except Exception as e:
            self.logger.error(f"Failed to reconstruct normalization result: {e}")
            return self._create_error_normalization_result(stored_data.get('document_id', ''), stored_data.get('original_filename', ''))
    
    def _reconstruct_format_result(self, data: Dict[str, Any]) -> FormatDetectionResult:
        """Reconstruct FormatDetectionResult from stored data"""
        from app.core.format_detection import FormatDetectionResult, FormatConfidence, DocumentCategory
        
        return FormatDetectionResult(
            detected_type=data.get('detected_type', 'unknown'),
            detected_format=data.get('detected_format', 'unknown'),
            mime_type=data.get('mime_type', 'application/octet-stream'),
            confidence_score=data.get('confidence_score', 0),
            confidence_level=FormatConfidence(data.get('confidence_level', 'uncertain')),
            category=DocumentCategory(data.get('category', 'unknown')),
            features=data.get('features', {}),
            conversion_path=data.get('conversion_path'),
            quality_indicators=data.get('quality_indicators', {}),
            processing_recommendations=data.get('processing_recommendations', [])
        )
    
    def _reconstruct_validation_result(self, data: Dict[str, Any]) -> ValidationResult:
        """Reconstruct ValidationResult from stored data"""
        from app.core.quality_validation import ValidationResult
        
        result = ValidationResult(
            is_valid=data.get('is_valid', False),
            overall_score=data.get('overall_score', 0)
        )
        
        # Note: Full reconstruction of validation issues would require more complex parsing
        # This is a simplified version
        
        return result
    
    def _create_error_normalization_result(self, document_id: str, original_filename: str) -> NormalizationResult:
        """Create error normalization result when reconstruction fails"""
        return NormalizationResult(
            document_id=document_id,
            original_filename=original_filename,
            format_detection=self._create_error_format_result(),
            standardized_document=self._create_error_standardized_doc(document_id, original_filename),
            validation_result=self._create_error_validation_result(),
            processing_duration=0.0,
            processing_timestamp=datetime.utcnow(),
            success=False,
            error_message="Failed to reconstruct normalization result from storage"
        )
    
    async def reprocess_document(
        self,
        document_id: str,
        organization_id: int,
        user_id: int,
        force_reprocessing: bool = False
    ) -> NormalizationResult:
        """
        Reprocess a previously normalized document
        
        Args:
            document_id: ID of document to reprocess
            organization_id: Organization ID
            user_id: User ID requesting reprocessing
            force_reprocessing: Whether to force reprocessing even if no errors
            
        Returns:
            New NormalizationResult
        """
        
        try:
            # Get original document content
            original_content = await self.document_storage.get_original_document(
                document_id, organization_id
            )
            
            if not original_content:
                raise ValueError(f"Original document content not found for ID: {document_id}")
            
            # Get original filename
            original_filename = await self.document_storage.get_document_filename(
                document_id, organization_id
            )
            
            # Reprocess with new document ID
            new_document_id = f"{document_id}_reprocessed_{int(datetime.utcnow().timestamp())}"
            
            result = await self.normalize_document(
                file_content=original_content,
                original_filename=original_filename,
                organization_id=organization_id,
                user_id=user_id,
                analyze_content=True,
                validate_quality=True,
                store_result=True
            )
            
            self.logger.info(
                "Document reprocessing completed",
                original_document_id=document_id,
                new_document_id=result.document_id,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Document reprocessing failed",
                document_id=document_id,
                error=str(e)
            )
            raise
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics for the normalization service"""
        
        # This would typically query the document storage for statistics
        # For now, return basic service information
        return {
            'service_name': 'DataNormalizationService',
            'components': {
                'format_detection': 'FormatDetectionEngine',
                'standardization': 'StandardizationEngine',
                'quality_validation': 'QualityValidator'
            },
            'capabilities': [
                'Intelligent format detection with confidence scoring',
                'Multi-format standardization to unified representation',
                'Comprehensive quality validation',
                'Error handling and fallback processing',
                'Reprocessing capabilities'
            ],
            'supported_formats': [
                'PDF (digital and scanned)',
                'DOCX',
                'Images (JPEG, PNG, TIFF)',
                'Text files',
                'Legacy formats'
            ]
        }
