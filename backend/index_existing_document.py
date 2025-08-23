#!/usr/bin/env python3
"""
Script to manually index existing processed documents into Elasticsearch.
This is useful for documents that were processed before Elasticsearch indexing was implemented.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.core.elasticsearch_service import ElasticsearchService
from app.models.document import Document
from app.models.user import User
from app.models.organization import Organization
from sqlalchemy.orm import Session

async def index_existing_documents():
    """Index all existing processed documents into Elasticsearch"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all processed documents
        processed_documents = db.query(Document).filter(
            Document.status == "PROCESSED"
        ).all()
        
        print(f"Found {len(processed_documents)} processed documents")
        
        if not processed_documents:
            print("No processed documents found")
            return
        
        # Initialize Elasticsearch service
        es_service = ElasticsearchService()
        
        # Ensure index exists
        es_service.ensure_index_exists()
        
        indexed_count = 0
        failed_count = 0
        
        for doc in processed_documents:
            try:
                print(f"Indexing document {doc.id}: {doc.filename}")
                
                # Prepare document data for indexing
                document_data = {
                    "document_id": str(doc.id),
                    "organization_id": doc.organization_id,
                    "filename": doc.filename,
                    "original_filename": doc.original_filename,
                    "extracted_text": doc.extracted_text,
                    "extracted_metadata": doc.extracted_metadata,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "tags": []
                }
                
                # Index the document
                index_success = await es_service.index_contract_document(document_data)
                
                if index_success:
                    print(f"✅ Successfully indexed document {doc.id}")
                    indexed_count += 1
                else:
                    print(f"❌ Failed to index document {doc.id}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error indexing document {doc.id}: {e}")
                failed_count += 1
        
        print(f"\nIndexing completed:")
        print(f"✅ Successfully indexed: {indexed_count}")
        print(f"❌ Failed: {failed_count}")
        
        # Show what's now in Elasticsearch
        print("\nChecking Elasticsearch index...")
        try:
            result = await es_service.search_contracts(query="*", page_size=10)
            print(f"Documents in Elasticsearch: {result.total_count}")
            for doc in result.documents:
                print(f"  - {doc.get('filename')}: ${doc.get('contract_amount', 'N/A')} - {doc.get('supplier_name', 'N/A')}")
        except Exception as e:
            print(f"Error checking Elasticsearch: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(index_existing_documents())















