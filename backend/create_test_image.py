#!/usr/bin/env python3
"""
Create a test image for OCR preprocessing testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """Create a simple test image with text for OCR testing"""
    
    # Create a simple image with text
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fallback to basic if not available
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            # Use default font
            font = ImageFont.load_default()
    
    # Add some test text
    text_lines = [
        "Test Document for OCR Processing",
        "",
        "This is a sample document to test",
        "the enhanced OCR preprocessing capabilities.",
        "",
        "Key Information:",
        "• Document Date: 2025-08-12",
        "• Contract Value: $50,000.00",
        "• Supplier: ABC Corporation",
        "• Project: Data Normalization Layer",
        "",
        "This text should be clearly readable",
        "by the OCR preprocessing system.",
        "",
        "Quality metrics should show:",
        "- High contrast",
        "- Clear text",
        "- Good resolution"
    ]
    
    y_position = 50
    for line in text_lines:
        if line.strip():
            # Calculate text position (center horizontally)
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            
            # Draw text
            draw.text((x_position, y_position), line, fill='black', font=font)
        y_position += 30
    
    # Save the image
    output_path = "uploads/test/test_ocr_image.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path, "PNG")
    
    print(f"✅ Test image created: {output_path}")
    print(f"   Dimensions: {width}x{height}")
    print(f"   Format: PNG")
    print(f"   Content: {len([l for l in text_lines if l.strip()])} text lines")
    
    return output_path

if __name__ == "__main__":
    create_test_image()
