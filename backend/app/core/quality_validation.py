"""
Quality Validation System

This module provides comprehensive quality validation for standardized documents,
ensuring data consistency, accuracy, and reliability across the Data Normalization
Layer Foundation.
"""

import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

from app.core.logging import get_logger
from app.core.standardized_representation import StandardizedDocument, ContentBlock, ContentType, ContentQuality

logger = get_logger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"    # Data unusable
    HIGH = "high"           # Significant quality issues
    MEDIUM = "medium"       # Moderate quality issues
    LOW = "low"             # Minor quality issues
    INFO = "info"           # Informational notes


class ValidationRule(str, Enum):
    """Types of validation rules"""
    CONTENT_QUALITY = "content_quality"
    FORMAT_CONSISTENCY = "format_consistency"
    METADATA_COMPLETENESS = "metadata_completeness"
    STRUCTURE_VALIDITY = "structure_validity"
    BUSINESS_LOGIC = "business_logic"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during quality checks"""
    rule: ValidationRule
    severity: ValidationSeverity
    message: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ValidationResult:
    """Result of quality validation"""
    is_valid: bool
    overall_score: int  # 0-100
    issues: List[ValidationIssue] = None
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Count issues by severity
        self.critical_issues = len([i for i in self.issues if i.severity == ValidationSeverity.CRITICAL])
        self.high_issues = len([i for i in self.issues if i.severity == ValidationSeverity.HIGH])
        self.medium_issues = len([i for i in self.issues if i.severity == ValidationSeverity.MEDIUM])
        self.low_issues = len([i for i in self.issues if i.severity == ValidationSeverity.LOW])
        self.info_issues = len([i for i in self.issues if i.severity == ValidationSeverity.INFO])
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue"""
        self.issues.append(issue)
        self._update_metrics()
    
    def _update_metrics(self):
        """Update validation metrics based on issues"""
        if not self.issues:
            self.is_valid = True
            self.overall_score = 100
            return
        
        # Calculate score based on severity weights
        total_weight = 0
        weighted_score = 0
        
        for issue in self.issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                weight = 10
                weighted_score += 0
            elif issue.severity == ValidationSeverity.HIGH:
                weight = 5
                weighted_score += 20
            elif issue.severity == ValidationSeverity.MEDIUM:
                weight = 3
                weighted_score += 50
            elif issue.severity == ValidationSeverity.LOW:
                weight = 1
                weighted_score += 80
            else:  # INFO
                weight = 0
                weighted_score += 100
            
            total_weight += weight
        
        if total_weight > 0:
            self.overall_score = max(0, min(100, int(weighted_score / total_weight)))
        else:
            self.overall_score = 100
        
        # Determine if overall validation passed
        self.is_valid = self.critical_issues == 0 and self.high_issues == 0
        
        # Count checks
        self.failed_checks = self.critical_issues + self.high_issues + self.medium_issues
        self.warnings = self.low_issues
        self.passed_checks = len(self.issues) - self.failed_checks - self.warnings


class QualityValidator:
    """Comprehensive quality validator for standardized documents"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Common validation patterns
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9][\d]{0,15}$',
            'date': r'^\d{4}-\d{2}-\d{2}$',
            'currency': r'^\$?[\d,]+(\.\d{2})?$',
            'percentage': r'^\d+(\.\d+)?%?$',
            'postal_code': r'^\d{5}(-\d{4})?$',
            'ssn': r'^\d{3}-\d{2}-\d{4}$'
        }
        
        # Business logic validation rules
        self.business_rules = {
            'contract': {
                'required_fields': ['parties', 'effective_date', 'terms'],
                'date_validation': True,
                'amount_validation': True
            },
            'invoice': {
                'required_fields': ['invoice_number', 'amount', 'due_date'],
                'date_validation': True,
                'amount_validation': True
            },
            'proposal': {
                'required_fields': ['scope', 'timeline', 'cost'],
                'date_validation': True,
                'amount_validation': True
            }
        }
    
    async def validate_document(
        self, 
        std_doc: StandardizedDocument
    ) -> ValidationResult:
        """
        Perform comprehensive quality validation on standardized document
        
        Args:
            std_doc: Standardized document to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        validation_result = ValidationResult(
            is_valid=True,
            overall_score=100
        )
        
        try:
            # Run all validation checks
            await self._validate_content_quality(std_doc, validation_result)
            await self._validate_format_consistency(std_doc, validation_result)
            await self._validate_metadata_completeness(std_doc, validation_result)
            await self._validate_structure_validity(std_doc, validation_result)
            await self._validate_business_logic(std_doc, validation_result)
            
            # Update final metrics
            validation_result._update_metrics()
            
            self.logger.info(
                "Document validation completed",
                document_id=std_doc.document_id,
                filename=std_doc.original_filename,
                is_valid=validation_result.is_valid,
                overall_score=validation_result.overall_score,
                issues_count=len(validation_result.issues)
            )
            
        except Exception as e:
            self.logger.error(
                "Document validation failed",
                document_id=std_doc.document_id,
                error=str(e)
            )
            validation_result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation process failed: {str(e)}",
                field_path="validation_process"
            ))
            validation_result._update_metrics()
        
        return validation_result
    
    async def _validate_content_quality(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate content quality and consistency"""
        
        # Check if document has content
        if not std_doc.content_blocks:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.CRITICAL,
                message="Document has no content blocks",
                field_path="content_blocks",
                suggestion="Check if document processing completed successfully"
            ))
            return
        
        # Validate individual content blocks
        for i, block in enumerate(std_doc.content_blocks):
            block_path = f"content_blocks[{i}]"
            
            # Check content is not empty
            if not block.content or not block.content.strip():
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.CONTENT_QUALITY,
                    severity=ValidationSeverity.HIGH,
                    message="Content block is empty",
                    field_path=f"{block_path}.content",
                    suggestion="Remove empty content blocks or investigate processing issues"
                ))
            
            # Check confidence score is reasonable
            if block.confidence_score < 0 or block.confidence_score > 100:
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.CONTENT_QUALITY,
                    severity=ValidationSeverity.MEDIUM,
                    message="Confidence score out of valid range (0-100)",
                    field_path=f"{block_path}.confidence_score",
                    expected_value="0-100",
                    actual_value=block.confidence_score
                ))
            
            # Check quality assessment consistency
            expected_quality = self._score_to_quality(block.confidence_score)
            if block.quality != expected_quality:
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.CONTENT_QUALITY,
                    severity=ValidationSeverity.LOW,
                    message="Quality assessment inconsistent with confidence score",
                    field_path=f"{block_path}.quality",
                    expected_value=expected_quality.value,
                    actual_value=block.quality.value
                ))
        
        # Check overall content distribution
        text_blocks = std_doc.get_content_by_type(ContentType.TEXT)
        if not text_blocks:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.HIGH,
                message="Document has no text content",
                field_path="content_blocks",
                suggestion="Check if text extraction or OCR processing failed"
            ))
        
        # Validate text content quality
        for i, block in enumerate(text_blocks):
            if block.content_type == ContentType.TEXT:
                await self._validate_text_content(block, f"content_blocks[{i}]", result)
    
    async def _validate_format_consistency(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate format consistency across the document"""
        
        # Check if source format details are consistent
        if std_doc.source_format != std_doc.source_format_details.detected_type:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.FORMAT_CONSISTENCY,
                severity=ValidationSeverity.MEDIUM,
                message="Source format mismatch between document and detection result",
                field_path="source_format",
                expected_value=std_doc.source_format_details.detected_type,
                actual_value=std_doc.source_format
            ))
        
        # Check if processing pipeline is specified
        if not std_doc.processing_pipeline:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.FORMAT_CONSISTENCY,
                severity=ValidationSeverity.LOW,
                message="Processing pipeline not specified",
                field_path="processing_pipeline",
                suggestion="Specify the processing pipeline used for standardization"
            ))
        
        # Validate timestamp consistency
        if std_doc.processed_at and std_doc.processed_at > datetime.utcnow():
            result.add_issue(ValidationIssue(
                rule=ValidationRule.FORMAT_CONSISTENCY,
                severity=ValidationSeverity.MEDIUM,
                message="Processing timestamp is in the future",
                field_path="processed_at",
                actual_value=std_doc.processed_at.isoformat(),
                suggestion="Check system clock and processing timestamps"
            ))
    
    async def _validate_metadata_completeness(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate metadata completeness and accuracy"""
        
        # Check required fields
        required_fields = ['document_id', 'original_filename', 'source_format']
        for field in required_fields:
            if not getattr(std_doc, field, None):
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.METADATA_COMPLETENESS,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Required field '{field}' is missing",
                    field_path=field,
                    suggestion=f"Ensure {field} is populated during document processing"
                ))
        
        # Check source format details
        if not std_doc.source_format_details:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.METADATA_COMPLETENESS,
                severity=ValidationSeverity.CRITICAL,
                message="Source format details are missing",
                field_path="source_format_details",
                suggestion="Ensure format detection results are properly stored"
            ))
        else:
            # Validate format detection confidence
            if std_doc.source_format_details.confidence_score < 50:
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.METADATA_COMPLETENESS,
                    severity=ValidationSeverity.MEDIUM,
                    message="Format detection confidence is low",
                    field_path="source_format_details.confidence_score",
                    actual_value=std_doc.source_format_details.confidence_score,
                    suggestion="Consider manual review or reprocessing with different parameters"
                ))
        
        # Check processing duration is reasonable
        if std_doc.processing_duration < 0:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.METADATA_COMPLETENESS,
                severity=ValidationSeverity.MEDIUM,
                message="Processing duration is negative",
                field_path="processing_duration",
                actual_value=std_doc.processing_duration,
                suggestion="Check processing timestamp calculations"
            ))
        elif std_doc.processing_duration > 3600:  # More than 1 hour
            result.add_issue(ValidationIssue(
                rule=ValidationRule.METADATA_COMPLETENESS,
                severity=ValidationSeverity.LOW,
                message="Processing duration is unusually long",
                field_path="processing_duration",
                actual_value=std_doc.processing_duration,
                suggestion="Investigate potential performance issues"
            ))
    
    async def _validate_structure_validity(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate document structure and organization"""
        
        # Check content block organization
        if std_doc.content_blocks:
            # Validate block positions
            for i, block in enumerate(std_doc.content_blocks):
                if not block.position:
                    result.add_issue(ValidationIssue(
                        rule=ValidationRule.STRUCTURE_VALIDITY,
                        severity=ValidationSeverity.LOW,
                        message="Content block missing position information",
                        field_path=f"content_blocks[{i}].position",
                        suggestion="Include position metadata for better document structure understanding"
                    ))
                
                # Check for duplicate content blocks
                for j, other_block in enumerate(std_doc.content_blocks[i+1:], i+1):
                    if (block.content == other_block.content and 
                        block.content_type == other_block.content_type):
                        result.add_issue(ValidationIssue(
                            rule=ValidationRule.STRUCTURE_VALIDITY,
                            severity=ValidationSeverity.MEDIUM,
                            message="Duplicate content block detected",
                            field_path=f"content_blocks[{i}] and content_blocks[{j}]",
                            suggestion="Remove duplicate content blocks or merge them"
                        ))
        
        # Check version information
        if std_doc.version < 1:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.STRUCTURE_VALIDITY,
                severity=ValidationSeverity.MEDIUM,
                message="Document version must be at least 1",
                field_path="version",
                actual_value=std_doc.version,
                expected_value=">= 1"
            ))
    
    async def _validate_business_logic(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate business logic and domain-specific rules"""
        
        document_category = std_doc.source_format_details.category.value
        
        # Get business rules for this document type
        business_rules = self.business_rules.get(document_category, {})
        
        if business_rules:
            # Check required fields based on document type
            required_fields = business_rules.get('required_fields', [])
            text_content = std_doc.get_text_content().lower()
            
            for field in required_fields:
                if field not in text_content:
                    result.add_issue(ValidationIssue(
                        rule=ValidationRule.BUSINESS_LOGIC,
                        severity=ValidationSeverity.HIGH,
                        message=f"Required field '{field}' not found in {document_category}",
                        field_path="content",
                        suggestion=f"Ensure {document_category} contains {field} information"
                    ))
            
            # Validate dates if required
            if business_rules.get('date_validation', False):
                await self._validate_dates_in_content(std_doc, result)
            
            # Validate amounts if required
            if business_rules.get('amount_validation', False):
                await self._validate_amounts_in_content(std_doc, result)
        
        # Check for suspicious patterns
        await self._validate_suspicious_patterns(std_doc, result)
    
    async def _validate_text_content(
        self, 
        block: ContentBlock, 
        field_path: str, 
        result: ValidationResult
    ):
        """Validate individual text content blocks"""
        
        content = block.content
        
        # Check for extremely long content blocks
        if len(content) > 10000:  # 10KB limit
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.MEDIUM,
                message="Content block is extremely long",
                field_path=f"{field_path}.content",
                actual_value=f"{len(content)} characters",
                suggestion="Consider splitting long content blocks for better processing"
            ))
        
        # Check for encoding issues
        if '' in content or '\x00' in content:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.MEDIUM,
                message="Content contains encoding artifacts",
                field_path=f"{field_path}.content",
                suggestion="Check text encoding and processing pipeline"
            ))
        
        # Check for excessive whitespace
        if len(content.strip()) < len(content) * 0.8:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.LOW,
                message="Content contains excessive whitespace",
                field_path=f"{field_path}.content",
                suggestion="Clean up excessive whitespace for better readability"
            ))
    
    async def _validate_dates_in_content(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate date information in document content"""
        
        text_content = std_doc.get_text_content()
        
        # Look for date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Month DD, YYYY
        ]
        
        dates_found = []
        for pattern in date_patterns:
            dates_found.extend(re.findall(pattern, text_content, re.IGNORECASE))
        
        if not dates_found:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.BUSINESS_LOGIC,
                severity=ValidationSeverity.MEDIUM,
                message="No dates found in document content",
                field_path="content",
                suggestion="Check if date extraction is working properly"
            ))
        else:
            # Validate date formats
            for date_str in dates_found[:5]:  # Check first 5 dates
                try:
                    # Try to parse the date
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        datetime.strptime(date_str, '%Y-%m-%d')
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', date_str):
                        # Handle MM/DD/YYYY format
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            if len(parts[2]) == 2:
                                parts[2] = '20' + parts[2]
                            datetime.strptime(f"{parts[2]}-{parts[0]}-{parts[1]}", '%Y-%m-%d')
                except ValueError:
                    result.add_issue(ValidationIssue(
                        rule=ValidationRule.BUSINESS_LOGIC,
                        severity=ValidationSeverity.LOW,
                        message=f"Invalid date format: {date_str}",
                        field_path="content",
                        actual_value=date_str,
                        suggestion="Ensure dates are in valid format (YYYY-MM-DD recommended)"
                    ))
    
    async def _validate_amounts_in_content(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Validate monetary amounts in document content"""
        
        text_content = std_doc.get_text_content()
        
        # Look for currency patterns
        currency_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*dollars?',  # 1,234.56 dollars
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*USD',  # 1,234.56 USD
        ]
        
        amounts_found = []
        for pattern in currency_patterns:
            amounts_found.extend(re.findall(pattern, text_content, re.IGNORECASE))
        
        if not amounts_found:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.BUSINESS_LOGIC,
                severity=ValidationSeverity.LOW,
                message="No monetary amounts found in document content",
                field_path="content",
                suggestion="Check if amount extraction is working properly"
            ))
    
    async def _validate_suspicious_patterns(
        self, 
        std_doc: StandardizedDocument, 
        result: ValidationResult
    ):
        """Check for suspicious or potentially problematic patterns"""
        
        text_content = std_doc.get_text_content()
        
        # Check for potential PII
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, text_content):
            result.add_issue(ValidationIssue(
                rule=ValidationRule.BUSINESS_LOGIC,
                severity=ValidationSeverity.HIGH,
                message="Potential SSN pattern detected in content",
                field_path="content",
                suggestion="Review content for PII and ensure proper handling"
            ))
        
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text_content)) / len(text_content) if text_content else 0
        if special_char_ratio > 0.3:  # More than 30% special characters
            result.add_issue(ValidationIssue(
                rule=ValidationRule.CONTENT_QUALITY,
                severity=ValidationSeverity.LOW,
                message="High ratio of special characters in content",
                field_path="content",
                actual_value=f"{special_char_ratio:.2%}",
                suggestion="Check if content extraction is working properly"
            ))
    
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
    
    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Get a summary of validation results"""
        return {
            'is_valid': result.is_valid,
            'overall_score': result.overall_score,
            'summary': {
                'total_checks': len(result.issues),
                'passed': result.passed_checks,
                'failed': result.failed_checks,
                'warnings': result.warnings
            },
            'severity_breakdown': {
                'critical': result.critical_issues,
                'high': result.high_issues,
                'medium': result.medium_issues,
                'low': result.low_issues,
                'info': result.info_issues
            },
            'recommendations': [
                issue.suggestion for issue in result.issues 
                if issue.suggestion and issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]
            ]
        }
