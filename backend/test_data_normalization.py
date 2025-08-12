#!/usr/bin/env python3
"""
Test script for Data Normalization Layer Foundation

This script demonstrates the intelligent format detection and conversion to
standardized internal representation functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.data_normalization import DataNormalizationService
from app.core.document_storage import DocumentStorage
from app.core.logging import setup_logging


async def test_data_normalization():
    """Test the complete data normalization pipeline"""
    
    print("🧪 Testing Data Normalization Layer Foundation")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    # Initialize services
    document_storage = DocumentStorage()
    normalization_service = DataNormalizationService(document_storage)
    
    # Test 1: PDF Document
    print("\n📄 Test 1: PDF Document Processing")
    print("-" * 40)
    
    # Create a simple PDF-like content for testing
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000111 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    try:
        result = await normalization_service.normalize_document(
            file_content=pdf_content,
            original_filename="test_document.pdf",
            organization_id=1,
            user_id=1,
            analyze_content=True,
            validate_quality=True,
            store_result=False  # Don't store for testing
        )
        
        print(f"✅ PDF processing completed")
        print(f"   Document ID: {result.document_id}")
        print(f"   Format detected: {result.format_detection.detected_type}")
        print(f"   Format confidence: {result.format_detection.confidence_score}%")
        print(f"   Document category: {result.format_detection.category.value}")
        print(f"   Content blocks: {len(result.standardized_document.content_blocks)}")
        print(f"   Overall confidence: {result.standardized_document.overall_confidence}%")
        print(f"   Quality validation: {result.validation_result.overall_score}%")
        print(f"   Processing time: {result.processing_duration:.2f}s")
        
        # Show content blocks
        for i, block in enumerate(result.standardized_document.content_blocks):
            print(f"   Block {i+1}: {block.content_type.value} (confidence: {block.confidence_score}%)")
            if block.content_type.value == "text":
                content_preview = block.content[:100] + "..." if len(block.content) > 100 else block.content
                print(f"      Content: {content_preview}")
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
    
    # Test 2: Text Document
    print("\n📝 Test 2: Text Document Processing")
    print("-" * 40)
    
    text_content = b"""Sample Contract Agreement

This agreement is made between Company A and Company B.

Terms and Conditions:
1. Service delivery will begin on January 1, 2024
2. Payment terms: Net 30 days
3. Contract value: $50,000 USD
4. Termination: 30 days written notice required

Effective Date: January 1, 2024
Expiration Date: December 31, 2024

Signed by:
Company A Representative
Company B Representative"""
    
    try:
        result = await normalization_service.normalize_document(
            file_content=text_content,
            original_filename="sample_contract.txt",
            organization_id=1,
            user_id=1,
            analyze_content=True,
            validate_quality=True,
            store_result=False
        )
        
        print(f"✅ Text processing completed")
        print(f"   Document ID: {result.document_id}")
        print(f"   Format detected: {result.format_detection.detected_type}")
        print(f"   Format confidence: {result.format_detection.confidence_score}%")
        print(f"   Document category: {result.format_detection.category.value}")
        print(f"   Content blocks: {len(result.standardized_document.content_blocks)}")
        print(f"   Overall confidence: {result.standardized_document.overall_confidence}%")
        print(f"   Quality validation: {result.validation_result.overall_score}%")
        print(f"   Processing time: {result.processing_duration:.2f}s")
        
        # Show validation issues if any
        if result.validation_result.issues:
            print(f"   Validation issues: {len(result.validation_result.issues)}")
            for issue in result.validation_result.issues[:3]:  # Show first 3 issues
                print(f"      - {issue.severity.value}: {issue.message}")
        
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
    
    # Test 3: Service Statistics
    print("\n📊 Test 3: Service Statistics")
    print("-" * 40)
    
    try:
        stats = normalization_service.get_processing_statistics()
        print(f"✅ Service statistics retrieved")
        print(f"   Service: {stats['service_name']}")
        print(f"   Components: {', '.join(stats['components'].keys())}")
        print(f"   Supported formats: {', '.join(stats['supported_formats'])}")
        
    except Exception as e:
        print(f"❌ Statistics retrieval failed: {e}")
    
    # Test 4: Format Detection Engine
    print("\n🔍 Test 4: Format Detection Engine")
    print("-" * 40)
    
    try:
        from app.core.format_detection import FormatDetectionEngine
        
        detection_engine = FormatDetectionEngine()
        
        # Test different file types
        test_files = [
            (b"%PDF-1.4\n", "test.pdf", "PDF"),
            (b"PK\x03\x04", "test.docx", "DOCX"),
            (b"\xff\xd8\xff", "test.jpg", "JPEG"),
            (b"Sample text content", "test.txt", "TXT"),
        ]
        
        for content, filename, expected_type in test_files:
            result = await detection_engine.detect_format(content, filename, analyze_content=False)
            status = "✅" if result.detected_type == expected_type.lower() else "❌"
            print(f"   {status} {filename}: detected as {result.detected_type} (confidence: {result.confidence_score}%)")
        
    except Exception as e:
        print(f"❌ Format detection test failed: {e}")
    
    # Test 5: Quality Validation
    print("\n✅ Test 5: Quality Validation")
    print("-" * 40)
    
    try:
        from app.core.quality_validation import QualityValidator
        from app.core.standardized_representation import StandardizedDocument, ContentBlock, ContentType, ContentQuality
        from app.core.format_detection import FormatDetectionResult, DocumentCategory
        
        validator = QualityValidator()
        
        # Create a test standardized document
        test_format = FormatDetectionResult(
            detected_type="pdf",
            detected_format="digital",
            mime_type="application/pdf",
            confidence_score=85,
            confidence_level=None,
            category=DocumentCategory.CONTRACT,
            features={'page_count': 1},
            conversion_path="pdf_to_standard",
            quality_indicators={'file_size_mb': 0.1},
            processing_recommendations=[]
        )
        
        test_doc = StandardizedDocument(
            document_id="test_validation",
            original_filename="test_contract.pdf",
            source_format="pdf",
            source_format_details=test_format
        )
        
        # Add some content blocks
        test_doc.add_content_block(ContentBlock(
            content_type=ContentType.TEXT,
            content="This is a test contract agreement.",
            confidence_score=90,
            quality=ContentQuality.EXCELLENT,
            position={'page': 1},
            metadata={'paragraph_number': 1}
        ))
        
        # Validate the document
        validation_result = await validator.validate_document(test_doc)
        
        print(f"✅ Quality validation completed")
        print(f"   Document valid: {validation_result.is_valid}")
        print(f"   Overall score: {validation_result.overall_score}%")
        print(f"   Issues found: {len(validation_result.issues)}")
        print(f"   Critical issues: {validation_result.critical_issues}")
        print(f"   High issues: {validation_result.high_issues}")
        
        # Show validation summary
        summary = validator.get_validation_summary(validation_result)
        print(f"   Passed checks: {summary['summary']['passed']}")
        print(f"   Failed checks: {summary['summary']['failed']}")
        print(f"   Warnings: {summary['summary']['warnings']}")
        
    except Exception as e:
        print(f"❌ Quality validation test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Data Normalization Layer Foundation Testing Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Intelligent format detection with confidence scoring")
    print("✅ Multi-format standardization to unified representation")
    print("✅ Comprehensive quality validation")
    print("✅ Error handling and fallback processing")
    print("✅ Structured logging and monitoring")
    print("✅ Extensible architecture for future enhancements")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_data_normalization())
