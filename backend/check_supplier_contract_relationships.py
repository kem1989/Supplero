#!/usr/bin/env python3
"""
Script to check if suppliers in the database are linked to contracts.
Based on the actual database schema where contracts are stored in the documents table.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text

def check_supplier_contract_relationships():
    """Check if suppliers are linked to contracts in the database."""
    
    # Database connection for Docker setup
    database_url = "postgresql://supplero:supplero_dev@supplero-postgres:5432/supplero"
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Successfully connected to database")
            
            # Check if suppliers table exists and has data
            result = conn.execute(text("SELECT COUNT(*) as supplier_count FROM suppliers"))
            supplier_count = result.fetchone()[0]
            print(f"📊 Found {supplier_count} suppliers in database")
            
            # Check if documents table exists and has data
            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            document_count = result.fetchone()[0]
            print(f"📄 Found {document_count} documents in database")
            
            # Check for contract-related documents
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM documents 
                WHERE extracted_metadata IS NOT NULL 
                  AND (extracted_metadata::text LIKE '%contract%' 
                       OR extracted_metadata::text LIKE '%agreement%'
                       OR extracted_metadata::text LIKE '%SUPPL%')
            """))
            contract_docs = result.fetchone()[0]
            print(f"🔍 Found {contract_docs} documents that appear to be contracts")
            
            # Check for supplier names in document metadata
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM documents 
                WHERE extracted_metadata IS NOT NULL 
                  AND extracted_metadata::text LIKE '%supplier%'
            """))
            supplier_metadata_docs = result.fetchone()[0]
            print(f"📝 Found {supplier_metadata_docs} documents with supplier metadata")
            
            # Show detailed supplier-contract relationships
            if contract_docs > 0:
                print("\n🔍 Detailed Supplier-Contract Relationships:")
                print("=" * 60)
                
                # Get all documents with contract-like metadata
                result = conn.execute(text("""
                    SELECT 
                        id,
                        filename,
                        extracted_metadata,
                        created_at
                    FROM documents 
                    WHERE extracted_metadata IS NOT NULL 
                      AND (extracted_metadata::text LIKE '%contract%' 
                           OR extracted_metadata::text LIKE '%agreement%'
                           OR extracted_metadata::text LIKE '%SUPPL%')
                    ORDER BY created_at DESC
                """))
                
                contract_documents = result.fetchall()
                
                for doc in contract_documents:
                    print(f"\n📋 Document: {doc.filename}")
                    print(f"  ID: {doc.id}")
                    print(f"  Created: {doc.created_at}")
                    
                    if doc.extracted_metadata:
                        metadata = doc.extracted_metadata
                        
                        # Extract supplier information
                        supplier_name = None
                        contract_number = None
                        contract_value = None
                        contract_dates = []
                        
                        # Look for supplier name in various fields
                        if 'supplier_name' in metadata:
                            supplier_name = metadata['supplier_name']
                        elif 'parties' in metadata:
                            # Check if parties contain supplier info
                            parties = metadata['parties']
                            if isinstance(parties, list):
                                for party in parties:
                                    if 'supplier' in str(party).lower() or 'vendor' in str(party).lower():
                                        supplier_name = str(party)
                                        break
                        
                        # Look for contract number
                        if 'contract_number' in metadata:
                            contract_number = metadata['contract_number']
                        elif 'contract_id' in metadata:
                            contract_number = metadata['contract_id']
                        
                        # Look for contract value
                        if 'total_value' in metadata:
                            contract_value = metadata['total_value']
                        elif 'contract_amount' in metadata:
                            contract_value = metadata['contract_amount']
                        elif 'value' in metadata:
                            contract_value = metadata['value']
                        
                        # Look for dates
                        if 'dates' in metadata:
                            dates = metadata['dates']
                            if isinstance(dates, list):
                                for date_info in dates:
                                    if 'value' in date_info:
                                        contract_dates.append(date_info['value'])
                        
                        # Display extracted information
                        if supplier_name:
                            print(f"  Supplier: {supplier_name}")
                            
                            # Check if this supplier exists in the database
                            supplier_result = conn.execute(text("""
                                SELECT id, name, industry, risk_score, risk_level
                                FROM suppliers 
                                WHERE name ILIKE :supplier_name
                                   OR name ILIKE :supplier_name_alt
                            """), {
                                'supplier_name': f"%{supplier_name}%",
                                'supplier_name_alt': f"%{supplier_name.split()[0]}%"
                            })
                            
                            matching_suppliers = supplier_result.fetchall()
                            if matching_suppliers:
                                print(f"  ✅ Linked to database supplier(s):")
                                for supplier in matching_suppliers:
                                    print(f"    • {supplier.name} ({supplier.industry}) - Risk: {supplier.risk_score} ({supplier.risk_level})")
                            else:
                                print(f"  ❌ No matching supplier found in database")
                        else:
                            print(f"  ❌ No supplier name extracted")
                        
                        if contract_number:
                            print(f"  Contract Number: {contract_number}")
                        
                        if contract_value:
                            print(f"  Contract Value: ${contract_value}")
                        
                        if contract_dates:
                            print(f"  Contract Dates: {', '.join(contract_dates)}")
                        
                        # Show a snippet of the metadata
                        metadata_str = str(metadata)[:300] + "..." if len(str(metadata)) > 300 else str(metadata)
                        print(f"  Metadata Preview: {metadata_str}")
                
                # Summary
                print(f"\n📊 Summary:")
                print(f"  Total suppliers: {supplier_count}")
                print(f"  Total documents: {document_count}")
                print(f"  Contract-like documents: {contract_docs}")
                print(f"  Documents with supplier metadata: {supplier_metadata_docs}")
                
                # Check linkage rate
                if contract_docs > 0:
                    # Count how many contract documents have supplier information
                    result = conn.execute(text("""
                        SELECT COUNT(DISTINCT d.id)
                        FROM documents d
                        WHERE d.extracted_metadata IS NOT NULL 
                          AND (d.extracted_metadata::text LIKE '%contract%' 
                               OR d.extracted_metadata::text LIKE '%agreement%'
                               OR d.extracted_metadata::text LIKE '%SUPPL%')
                          AND d.extracted_metadata::text LIKE '%supplier%'
                    """))
                    linked_contracts = result.fetchone()[0]
                    print(f"  Contract documents with supplier info: {linked_contracts}")
                    print(f"  Linkage rate: {(linked_contracts/contract_docs*100):.1f}%")
                
            else:
                print("\n❌ No contract documents found!")
                print("\n💡 This could mean:")
                print("  • No contracts have been uploaded yet")
                print("  • Document processing hasn't extracted contract metadata")
                print("  • Documents are not being classified as contracts")
                
                # Show sample data to help debug
                print("\n🔍 Sample Data Check:")
                
                # Show first few suppliers
                result = conn.execute(text("SELECT name, industry FROM suppliers LIMIT 5"))
                suppliers = result.fetchall()
                if suppliers:
                    print("  Suppliers:")
                    for supplier in suppliers:
                        print(f"    • {supplier.name} ({supplier.industry or 'N/A'})")
                
                # Show first few documents
                result = conn.execute(text("SELECT filename, document_type FROM documents LIMIT 5"))
                documents = result.fetchall()
                if documents:
                    print("  Documents:")
                    for doc in documents:
                        print(f"    • {doc.filename} - Type: {doc.document_type or 'N/A'}")
                
                # Check if there are any documents with metadata
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM documents 
                    WHERE extracted_metadata IS NOT NULL
                """))
                metadata_docs = result.fetchone()[0]
                print(f"  Documents with metadata: {metadata_docs}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure:")
        print("  • Docker containers are running")
        print("  • Database is accessible")
        print("  • Environment variables are set correctly")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking Supplier-Contract Relationships in Database")
    print("=" * 60)
    
    success = check_supplier_contract_relationships()
    
    if success:
        print("\n✅ Check completed successfully!")
    else:
        print("\n❌ Check failed!")
        sys.exit(1)
