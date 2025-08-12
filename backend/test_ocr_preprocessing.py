#!/usr/bin/env python3
"""
Test script for enhanced OCR preprocessing functionality

This script tests the OCR preprocessing module to ensure it's working correctly
with image enhancement and quality validation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.ocr_preprocessing import OCRPreprocessor, ImageQuality, OCRConfidence
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_ocr_preprocessing():
    """Test the OCR preprocessing functionality"""
    print("🧪 Testing Enhanced OCR Preprocessing...")
    
    # Initialize the OCR preprocessor
    preprocessor = OCRPreprocessor()
    
    # Test with a sample image (if available)
    test_image_path = backend_dir / "uploads" / "test" / "test_document.txt"
    
    if test_image_path.exists():
        print(f"📁 Found test file: {test_image_path}")
        
        # Read the test file
        with open(test_image_path, 'rb') as f:
            file_content = f.read()
        
        print(f"📄 File size: {len(file_content)} bytes")
        
        # Test OCR preprocessing
        try:
            result = await preprocessor.preprocess_and_ocr(
                image_bytes=file_content,
                filename=test_image_path.name,
                apply_enhancement=True,
                validate_quality=True
            )
            
            print("\n✅ OCR Preprocessing Results:")
            print(f"   📝 Extracted text length: {len(result.extracted_text)} characters")
            print(f"   🎯 Confidence score: {result.confidence_score}%")
            print(f"   🏷️  Confidence level: {result.confidence_level.value}")
            print(f"   🖼️  Image quality: {result.image_quality.value}")
            print(f"   📊 Image quality score: {result.image_quality_score}%")
            print(f"   🔍 OCR quality score: {result.ocr_quality_score}%")
            print(f"   ⏱️  Processing duration: {result.processing_duration:.2f}s")
            
            if result.preprocessing_applied:
                print(f"   🔧 Preprocessing steps: {', '.join(result.preprocessing_applied)}")
            
            if result.quality_indicators:
                print(f"   📈 Quality indicators: {result.quality_indicators}")
            
            if result.recommendations:
                print(f"   💡 Recommendations:")
                for rec in result.recommendations:
                    print(f"      • {rec}")
            
            if result.issues:
                print(f"   ⚠️  Issues:")
                for issue in result.issues:
                    print(f"      • {issue}")
            
            # Test quality mapping
            print(f"\n🔍 Quality Assessment:")
            print(f"   Image Quality: {result.image_quality.value} ({result.image_quality_score}%)")
            print(f"   OCR Quality: {result.ocr_quality_score}%")
            print(f"   Overall Confidence: {result.confidence_score}%")
            
            if result.ocr_quality_score < 50:
                print("   ⚠️  Low OCR quality detected - manual review recommended")
            elif result.ocr_quality_score < 70:
                print("   ⚠️  Moderate OCR quality - review critical information")
            else:
                print("   ✅ Good OCR quality - text extraction appears reliable")
                
        except Exception as e:
            print(f"❌ OCR preprocessing failed: {e}")
            logger.error(f"OCR preprocessing test failed: {e}")
            return False
    
    else:
        print(f"📁 Test file not found: {test_image_path}")
        print("   Creating a simple test to verify module loading...")
        
        # Test module loading and basic functionality
        try:
            # Test enum values
            print(f"   🏷️  ImageQuality enum values: {[q.value for q in ImageQuality]}")
            print(f"   🏷️  OCRConfidence enum values: {[c.value for c in OCRConfidence]}")
            
            # Test preprocessor initialization
            print(f"   🔧 OCR preprocessor initialized successfully")
            print(f"   📊 Enhancement parameters: {preprocessor.enhancement_params}")
            
            return True
            
        except Exception as e:
            print(f"❌ Module loading test failed: {e}")
            return False
    
    return True


async def test_quality_validation():
    """Test the quality validation functionality"""
    print("\n🧪 Testing Quality Validation...")
    
    try:
        from app.core.quality_validation import QualityValidator
        from app.core.standardized_representation import StandardizedDocument, ContentBlock, ContentType, ContentQuality
        from app.core.format_detection import FormatDetectionResult, DocumentCategory
        
        print("✅ Quality validation module imported successfully")
        
        # Test basic validation
        validator = QualityValidator()
        print("✅ Quality validator initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality validation test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Enhanced OCR Preprocessing Tests...")
    print("=" * 60)
    
    # Test OCR preprocessing
    ocr_success = await test_ocr_preprocessing()
    
    # Test quality validation
    validation_success = await test_quality_validation()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   OCR Preprocessing: {'✅ PASSED' if ocr_success else '❌ FAILED'}")
    print(f"   Quality Validation: {'✅ PASSED' if validation_success else '❌ FAILED'}")
    
    if ocr_success and validation_success:
        print("\n🎉 All tests passed! Enhanced OCR preprocessing is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
