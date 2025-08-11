#!/usr/bin/env python3
"""
Test script for the Universal Document Ingestion Pipeline
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Mock the database and other dependencies for testing
import sys
sys.path.append('app')

from app.core.document_ingestion import DocumentIngestionService
from app.models.document import DocumentType, DocumentFormat


class MockSecureStorage:
    """Mock secure storage for testing"""
    
    def __init__(self):
        self.files = {}
    
    async def store_file(self, file_path: str, file_content: bytes):
        """Store file in memory"""
        self.files[file_path] = file_content
        print(f"Mock stored file: {file_path} ({len(file_content)} bytes)")
    
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve file from memory"""
        if file_path in self.files:
            return self.files[file_path]
        raise FileNotFoundError(f"File not found: {file_path}")


def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 750, "Test PDF Document")
        p.drawString(100, 700, "This is a test PDF for document ingestion")
        p.drawString(100, 650, "Created on: 2024-01-15")
        p.drawString(100, 600, "Amount: $1,234.56")
        p.drawString(100, 550, "Party A: Test Company Inc.")
        p.drawString(100, 500, "Party B: Supplier Corp")
        p.save()
        
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
        
    except ImportError:
        # Fallback: create a simple text file with PDF extension
        content = b"%PDF-1.4\nTest PDF Document\nThis is a test PDF for document ingestion\nCreated on: 2024-01-15\nAmount: $1,234.56\nParty A: Test Company Inc.\nParty B: Supplier Corp"
        return content


def create_test_docx():
    """Create a simple test DOCX file"""
    try:
        from docx import Document
        from io import BytesIO
        
        doc = Document()
        doc.add_heading('Test DOCX Document', 0)
        doc.add_paragraph('This is a test DOCX document for document ingestion.')
        doc.add_paragraph('Created on: 2024-01-15')
        doc.add_paragraph('Amount: $1,234.56')
        doc.add_paragraph('Party A: Test Company Inc.')
        doc.add_paragraph('Party B: Supplier Corp')
        
        buffer = BytesIO()
        doc.save(buffer)
        docx_content = buffer.getvalue()
        buffer.close()
        return docx_content
        
    except ImportError:
        # Fallback: create a simple text file with DOCX extension
        content = b"Test DOCX Document\nThis is a test DOCX document for document ingestion\nCreated on: 2024-01-15\nAmount: $1,234.56\nParty A: Test Company Inc.\nParty B: Supplier Corp"
        return content


def create_test_image():
    """Create a simple test image file"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text to the image
        draw.text((20, 20), "Test Image Document", fill='black')
        draw.text((20, 50), "This is a test image for document ingestion", fill='black')
        draw.text((20, 80), "Created on: 2024-01-15", fill='black')
        draw.text((20, 110), "Amount: $1,234.56", fill='black')
        draw.text((20, 140), "Party A: Test Company Inc.", fill='black')
        draw.text((20, 170), "Party B: Supplier Corp", fill='black')
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_content = buffer.getvalue()
        buffer.close()
        return image_content
        
    except ImportError:
        # Fallback: create a simple text file with PNG extension
        content = b"Test Image Document\nThis is a test image for document ingestion\nCreated on: 2024-01-15\nAmount: $1,234.56\nParty A: Test Company Inc.\nParty B: Supplier Corp"
        return content


def create_test_text():
    """Create a simple test text file"""
    content = """Test Text Document
This is a test text document for document ingestion.
Created on: 2024-01-15
Amount: $1,234.56
Party A: Test Company Inc.
Party B: Supplier Corp

This document contains various types of information that should be extracted:
- Dates: 2024-01-15, 2024-02-01
- Amounts: $1,234.56, $5,000.00
- Parties: Test Company Inc., Supplier Corp
- Document type: contract
- Language: English
"""
    return content.encode('utf-8')


async def test_document_ingestion():
    """Test the document ingestion pipeline with different file types"""
    
    print("🧪 Testing Universal Document Ingestion Pipeline")
    print("=" * 60)
    
    # Initialize services
    mock_storage = MockSecureStorage()
    ingestion_service = DocumentIngestionService(mock_storage)
    
    # Test files
    test_files = [
        ("test.pdf", create_test_pdf(), "PDF document"),
        ("test.docx", create_test_docx(), "DOCX document"),
        ("test.png", create_test_image(), "Image document"),
        ("test.txt", create_test_text(), "Text document"),
    ]
    
    for filename, content, description in test_files:
        print(f"\n📄 Testing {description} ({filename})")
        print("-" * 40)
        
        try:
            # Test document ingestion
            document = await ingestion_service.ingest_document(
                file_content=content,
                original_filename=filename,
                organization_id=1,
                user_id=1,
                tags=["test", "ingestion"]
            )
            
            print(f"✅ Document ingested successfully")
            print(f"   - Detected type: {document.document_type.value}")
            print(f"   - Detected format: {document.document_format.value}")
            print(f"   - OCR required: {document.ocr_required}")
            print(f"   - File size: {document.file_size} bytes")
            print(f"   - MIME type: {document.mime_type}")
            
            # Test text extraction
            try:
                extracted_text = await ingestion_service.extract_text_content(document)
                print(f"   - Text extracted: {len(extracted_text)} characters")
                print(f"   - Preview: {extracted_text[:100]}...")
                
                # Test metadata extraction
                metadata = await ingestion_service.extract_metadata(document, extracted_text)
                print(f"   - Metadata extracted:")
                print(f"     * Dates: {len(metadata.dates)} found")
                print(f"     * Amounts: {len(metadata.amounts)} found")
                print(f"     * Parties: {len(metadata.parties)} found")
                print(f"     * Document category: {metadata.document_type}")
                print(f"     * Language: {metadata.language}")
                print(f"     * Confidence: {metadata.confidence_score}%")
                
            except Exception as e:
                print(f"   - Text/metadata extraction failed: {e}")
            
        except Exception as e:
            print(f"❌ Document ingestion failed: {e}")
        
        print()
    
    print("🎯 Document ingestion pipeline test completed!")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_document_ingestion())
