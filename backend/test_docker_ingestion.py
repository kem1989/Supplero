#!/usr/bin/env python3
"""
Simple test script for document ingestion pipeline
This can be run inside the Docker container
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append('/app')

from app.core.document_storage import DocumentStorage
from app.core.document_ingestion import DocumentIngestionService


async def test_basic_functionality():
    """Test basic document ingestion functionality"""
    
    print("🧪 Testing Document Ingestion Pipeline")
    print("=" * 50)
    
    try:
        # Initialize services
        storage = DocumentStorage()
        ingestion = DocumentIngestionService(storage)
        
        print("✅ Services initialized successfully")
        
        # Test file storage
        test_content = b"This is a test document content for ingestion testing."
        test_filename = "test_document.txt"
        
        # Test storage
        stored_path = await storage.store_file(f"test/{test_filename}", test_content)
        print(f"✅ File stored at: {stored_path}")
        
        # Test retrieval
        retrieved_content = await storage.get_file(f"test/{test_filename}")
        print(f"✅ File retrieved: {len(retrieved_content)} bytes")
        
        # Test document ingestion
        document = await ingestion.ingest_document(
            file_content=test_content,
            original_filename=test_filename,
            organization_id=1,
            user_id=1,
            tags=["test", "ingestion"]
        )
        
        print(f"✅ Document ingested successfully")
        print(f"   - ID: {document.id if hasattr(document, 'id') else 'N/A'}")
        print(f"   - Type: {document.document_type.value}")
        print(f"   - Format: {document.document_format.value}")
        print(f"   - Status: {document.status.value}")
        print(f"   - OCR Required: {document.ocr_required}")
        
        # Test text extraction
        extracted_text = await ingestion.extract_text_content(document)
        print(f"✅ Text extracted: {len(extracted_text)} characters")
        print(f"   Preview: {extracted_text[:100]}...")
        
        # Test metadata extraction
        metadata = await ingestion.extract_metadata(document, extracted_text)
        print(f"✅ Metadata extracted:")
        print(f"   - Dates: {len(metadata.dates)} found")
        print(f"   - Amounts: {len(metadata.amounts)} found")
        print(f"   - Parties: {len(metadata.parties)} found")
        print(f"   - Document category: {metadata.document_type}")
        print(f"   - Language: {metadata.language}")
        print(f"   - Confidence: {metadata.confidence_score}%")
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting document ingestion pipeline test...")
    success = asyncio.run(test_basic_functionality())
    
    if success:
        print("\n✅ Document ingestion pipeline is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Document ingestion pipeline has issues!")
        sys.exit(1)
