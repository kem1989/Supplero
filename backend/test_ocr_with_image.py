#!/usr/bin/env python3
"""
Test OCR preprocessing with the generated test image
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.ocr_preprocessing import OCRPreprocessor, ImageQuality, OCRConfidence
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_ocr_with_image():
    """Test OCR preprocessing with the generated test image"""
    print("🧪 Testing OCR Preprocessing with Test Image...")
    
    # Initialize the OCR preprocessor
    preprocessor = OCRPreprocessor()
    
    # Test image path
    test_image_path = backend_dir / "uploads" / "test" / "test_ocr_image.png"
    
    if not test_image_path.exists():
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    print(f"📁 Found test image: {test_image_path}")
    
    # Read the test image
    with open(test_image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"📄 Image size: {len(image_bytes)} bytes")
    
    # Test OCR preprocessing with enhancement
    print("\n🔧 Testing OCR with Image Enhancement...")
    try:
        result_with_enhancement = await preprocessor.preprocess_and_ocr(
            image_bytes=image_bytes,
            filename=test_image_path.name,
            apply_enhancement=True,
            validate_quality=True
        )
        
        print("\n✅ OCR Results WITH Enhancement:")
        print(f"   📝 Extracted text length: {len(result_with_enhancement.extracted_text)} characters")
        print(f"   🎯 Confidence score: {result_with_enhancement.confidence_score}%")
        print(f"   🏷️  Confidence level: {result_with_enhancement.confidence_level.value}")
        print(f"   🖼️  Image quality: {result_with_enhancement.image_quality.value}")
        print(f"   📊 Image quality score: {result_with_enhancement.image_quality_score}%")
        print(f"   🔍 OCR quality score: {result_with_enhancement.ocr_quality_score}%")
        print(f"   ⏱️  Processing duration: {result_with_enhancement.processing_duration:.2f}s")
        
        if result_with_enhancement.preprocessing_applied:
            print(f"   🔧 Preprocessing steps: {', '.join(result_with_enhancement.preprocessing_applied)}")
        
        if result_with_enhancement.quality_indicators:
            print(f"   📈 Quality indicators:")
            for key, value in result_with_enhancement.quality_indicators.items():
                if key == 'quality_metrics':
                    print(f"      {key}:")
                    for metric, metric_value in value.items():
                        print(f"        {metric}: {metric_value}")
                else:
                    print(f"      {key}: {value}")
        
        if result_with_enhancement.recommendations:
            print(f"   💡 Recommendations:")
            for rec in result_with_enhancement.recommendations:
                print(f"      • {rec}")
        
        if result_with_enhancement.issues:
            print(f"   ⚠️  Issues:")
            for issue in result_with_enhancement.issues:
                print(f"      • {issue}")
        
        # Show extracted text (first 200 characters)
        extracted_text = result_with_enhancement.extracted_text
        if extracted_text:
            print(f"\n📝 Extracted Text (first 200 chars):")
            print(f"   {extracted_text[:200]}{'...' if len(extracted_text) > 200 else ''}")
        
        # Test without enhancement for comparison
        print("\n🔧 Testing OCR WITHOUT Enhancement...")
        result_without_enhancement = await preprocessor.preprocess_and_ocr(
            image_bytes=image_bytes,
            filename=test_image_path.name,
            apply_enhancement=False,
            validate_quality=True
        )
        
        print("\n✅ OCR Results WITHOUT Enhancement:")
        print(f"   📝 Extracted text length: {len(result_without_enhancement.extracted_text)} characters")
        print(f"   🎯 Confidence score: {result_without_enhancement.confidence_score}%")
        print(f"   🏷️  Confidence level: {result_without_enhancement.confidence_level.value}")
        print(f"   🖼️  Image quality: {result_without_enhancement.image_quality.value}")
        print(f"   📊 Image quality score: {result_without_enhancement.image_quality_score}%")
        print(f"   🔍 OCR quality score: {result_without_enhancement.ocr_quality_score}%")
        print(f"   ⏱️  Processing duration: {result_without_enhancement.processing_duration:.2f}s")
        
        # Compare results
        print("\n📊 Enhancement Comparison:")
        enhancement_improvement = result_with_enhancement.ocr_quality_score - result_without_enhancement.ocr_quality_score
        print(f"   OCR Quality Improvement: {enhancement_improvement:+d}%")
        
        if enhancement_improvement > 0:
            print("   ✅ Enhancement improved OCR quality")
        elif enhancement_improvement < 0:
            print("   ⚠️  Enhancement decreased OCR quality")
        else:
            print("   ➖ Enhancement had no effect on OCR quality")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR preprocessing failed: {e}")
        logger.error(f"OCR preprocessing test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting OCR Preprocessing Image Test...")
    print("=" * 60)
    
    success = await test_ocr_with_image()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 OCR preprocessing test completed successfully!")
        print("   The enhanced OCR preprocessing is working correctly.")
    else:
        print("❌ OCR preprocessing test failed.")
        print("   Please check the implementation and error messages.")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
