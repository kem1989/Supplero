#!/usr/bin/env python3
"""
Script to manually extract clauses from existing documents and store them in the database.
This will fix the RAG system by ensuring all documents have extracted clauses for Elasticsearch search.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import get_db
from app.core.clause_extraction import ClauseExtractionService
from app.models.document import Document
from app.core.logging import get_logger

logger = get_logger(__name__)

async def extract_clauses_for_existing_documents():
    """Extract clauses from all existing documents and store them in the database"""
    
    try:
        # Get database session
        db = next(get_db())
        
        # Get all documents that don't have extracted clauses
        documents = db.query(Document).filter(
            Document.organization_id == 1  # Default organization
        ).all()
        
        print(f"Found {len(documents)} documents to process")
        
        if not documents:
            print("No documents found")
            return
        
        # Initialize clause extraction service
        clause_service = ClauseExtractionService()
        
        total_clauses = 0
        
        for i, document in enumerate(documents, 1):
            print(f"\nProcessing document {i}/{len(documents)}: {document.filename}")
            
            if not document.extracted_text:
                print(f"  ⚠️  No extracted text for document {document.id}, skipping")
                continue
            
            try:
                # Extract clauses from the document
                extracted_clauses = await clause_service.extract_clauses_from_document(
                    document_text=document.extracted_text,
                    document_id=str(document.id),
                    organization_id=str(document.organization_id)
                )
                
                if extracted_clauses:
                    print(f"  ✅ Extracted {len(extracted_clauses)} clauses")
                    
                    # Store clauses in the database
                    from app.api.v1.documents import store_clauses_in_database
                    await store_clauses_in_database(extracted_clauses, document.id, db)
                    
                    total_clauses += len(extracted_clauses)
                    
                    # Print some details about the extracted clauses
                    for clause in extracted_clauses[:3]:  # Show first 3 clauses
                        print(f"    - {clause.clause_type}: {clause.clause_text[:50]}...")
                    
                    if len(extracted_clauses) > 3:
                        print(f"    ... and {len(extracted_clauses) - 3} more clauses")
                else:
                    print(f"  ⚠️  No clauses extracted from document {document.id}")
                    
            except Exception as e:
                print(f"  ❌ Error processing document {document.id}: {str(e)}")
                logger.error(f"Failed to extract clauses from document {document.id}", error=str(e))
                continue
        
        print(f"\n🎉 Clause extraction completed!")
        print(f"Total clauses extracted: {total_clauses}")
        print(f"Documents processed: {len(documents)}")
        
        # Verify the results
        clause_count = db.execute("SELECT COUNT(*) FROM contract_clauses").scalar()
        print(f"Total clauses in database: {clause_count}")
        
        # Check for early termination clauses specifically
        termination_clauses = db.execute(
            "SELECT clause_type, clause_text FROM contract_clauses WHERE clause_type ILIKE '%termination%' OR clause_text ILIKE '%termination%'"
        ).fetchall()
        
        if termination_clauses:
            print(f"\n✅ Found {len(termination_clauses)} termination-related clauses:")
            for clause in termination_clauses:
                print(f"  - {clause[0]}: {clause[1]}")
        else:
            print("\n⚠️  No termination-related clauses found")
        
    except Exception as e:
        print(f"❌ Failed to extract clauses: {str(e)}")
        logger.error("Clause extraction failed", error=str(e))
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting clause extraction for existing documents...")
    asyncio.run(extract_clauses_for_existing_documents())
    print("✅ Clause extraction script completed!")
