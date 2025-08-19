#!/usr/bin/env python3
"""
Test script to see exactly what document content is being sent to OpenAI
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import get_db
from app.models.document import Document

def test_document_content():
    """Test what document content is being sent to OpenAI"""
    
    try:
        print("🔍 Testing document content being sent to OpenAI...")
        
        # Get database session
        db = next(get_db())
        documents = db.query(Document).filter(
            Document.organization_id == 1  # Default organization
        ).limit(3).all()
        
        print(f"Found {len(documents)} documents")
        
        for i, doc in enumerate(documents):
            print(f"\n📄 DOCUMENT {i+1}: ID={doc.id}, Filename={doc.filename}")
            print(f"Text length: {len(doc.extracted_text) if doc.extracted_text else 0} characters")
            
            if doc.extracted_text:
                # Show the first 500 characters
                print("First 500 characters:")
                print(doc.extracted_text[:500])
                print("...")
                
                # Look for early termination content
                if "early" in doc.extracted_text.lower() or "termination" in doc.extracted_text.lower():
                    print("\n🔍 EARLY TERMINATION CONTENT FOUND:")
                    # Find the section with early termination
                    lines = doc.extracted_text.split('\n')
                    for j, line in enumerate(lines):
                        if "early" in line.lower() or "termination" in line.lower():
                            print(f"Line {j+1}: {line}")
                            # Show a few lines around it
                            start = max(0, j-2)
                            end = min(len(lines), j+3)
                            for k in range(start, end):
                                marker = ">>> " if k == j else "    "
                                print(f"{marker}{lines[k]}")
                            break
                else:
                    print("❌ No early termination content found in text")
                
                # Show the last 500 characters
                print("\nLast 500 characters:")
                print(doc.extracted_text[-500:])
            else:
                print("❌ No extracted text")
            
            print("\n" + "="*80)
        
        print("\n✅ Document content test completed!")
        
    except Exception as e:
        print(f"❌ Document content test failed: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Starting Document Content Test...")
    test_document_content()
    print("🎉 Document content test completed!")
