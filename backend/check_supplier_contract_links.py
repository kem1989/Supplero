#!/usr/bin/env python3
"""
Simple script to check if suppliers in the database are linked to contracts.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

def check_supplier_contract_links():
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
            result = conn.execute(text("""
                SELECT COUNT(*) as supplier_count 
                FROM suppliers
            """))
            supplier_count = result.fetchone()[0]
            print(f"📊 Found {supplier_count} suppliers in database")
            
            # Check if contracts table exists and has data
            result = conn.execute(text("""
                SELECT COUNT(*) as contract_count 
                FROM contracts
            """))
            contract_count = result.fetchone()[0]
            print(f"📄 Found {contract_count} contracts in database")
            
            # Check for direct supplier-contract links (via supplier_id)
            result = conn.execute(text("""
                SELECT COUNT(*) as linked_count 
                FROM contracts 
                WHERE supplier_id IS NOT NULL
            """))
            linked_count = result.fetchone()[0]
            print(f"🔗 Found {linked_count} contracts directly linked to suppliers")
            
            # Check for supplier names in contract metadata
            result = conn.execute(text("""
                SELECT COUNT(*) as metadata_linked_count 
                FROM contracts c
                JOIN suppliers s ON c.extracted_data->>'supplier_name' = s.name
                WHERE c.extracted_data->>'supplier_name' IS NOT NULL
            """))
            metadata_linked_count = result.fetchone()[0]
            print(f"📝 Found {metadata_linked_count} contracts linked via metadata")
            
            # Show detailed supplier-contract relationships
            if linked_count > 0 or metadata_linked_count > 0:
                print("\n🔍 Detailed Supplier-Contract Relationships:")
                print("=" * 60)
                
                # Direct links
                if linked_count > 0:
                    print("\n📋 Direct Links (via supplier_id):")
                    result = conn.execute(text("""
                        SELECT 
                            s.name as supplier_name,
                            s.industry as supplier_industry,
                            c.title as contract_title,
                            c.contract_number,
                            c.total_value,
                            c.status
                        FROM contracts c
                        JOIN suppliers s ON c.supplier_id = s.id
                        WHERE c.supplier_id IS NOT NULL
                        ORDER BY s.name
                    """))
                    
                    for row in result.fetchall():
                        print(f"  • {row.supplier_name} ({row.supplier_industry})")
                        print(f"    Contract: {row.contract_title}")
                        print(f"    Number: {row.contract_number or 'N/A'}")
                        print(f"    Value: ${row.total_value or 'N/A'}")
                        print(f"    Status: {row.status}")
                        print()
                
                # Metadata links
                if metadata_linked_count > 0:
                    print("\n📝 Metadata Links (via extracted supplier name):")
                    result = conn.execute(text("""
                        SELECT 
                            s.name as supplier_name,
                            s.industry as supplier_industry,
                            c.title as contract_title,
                            c.contract_number,
                            c.total_value,
                            c.status,
                            c.extracted_data->>'supplier_name' as extracted_supplier_name
                        FROM contracts c
                        JOIN suppliers s ON c.extracted_data->>'supplier_name' = s.name
                        WHERE c.extracted_data->>'supplier_name' IS NOT NULL
                        ORDER BY s.name
                    """))
                    
                    for row in result.fetchall():
                        print(f"  • {row.supplier_name} ({row.supplier_industry})")
                        print(f"    Contract: {row.contract_title}")
                        print(f"    Number: {row.contract_number or 'N/A'}")
                        print(f"    Value: ${row.total_value or 'N/A'}")
                        print(f"    Status: {row.status}")
                        print(f"    Extracted Name: {row.extracted_supplier_name}")
                        print()
                
                # Summary
                total_linked = linked_count + metadata_linked_count
                print(f"\n📊 Summary:")
                print(f"  Total suppliers: {supplier_count}")
                print(f"  Total contracts: {contract_count}")
                print(f"  Linked contracts: {total_linked}")
                print(f"  Linkage rate: {(total_linked/contract_count*100):.1f}%" if contract_count > 0 else "  Linkage rate: N/A")
                
            else:
                print("\n❌ No supplier-contract relationships found!")
                print("\n💡 This could mean:")
                print("  • No contracts have been uploaded yet")
                print("  • Supplier linking hasn't been run")
                print("  • Contracts and suppliers are in different organizations")
                
                # Show sample data to help debug
                print("\n🔍 Sample Data Check:")
                
                # Show first few suppliers
                result = conn.execute(text("SELECT name, industry FROM suppliers LIMIT 5"))
                suppliers = result.fetchall()
                if suppliers:
                    print("  Suppliers:")
                    for supplier in suppliers:
                        print(f"    • {supplier.name} ({supplier.industry or 'N/A'})")
                
                # Show first few contracts
                result = conn.execute(text("SELECT title, contract_number FROM contracts LIMIT 5"))
                contracts = result.fetchall()
                if contracts:
                    print("  Contracts:")
                    for contract in contracts:
                        print(f"    • {contract.title} ({contract.contract_number or 'N/A'})")
                
                # Check if there are any documents that might be contracts
                result = conn.execute(text("""
                    SELECT COUNT(*) as doc_count 
                    FROM documents 
                    WHERE document_type = 'contract' OR document_type LIKE '%contract%'
                """))
                doc_count = result.fetchone()[0]
                print(f"  Documents marked as contracts: {doc_count}")
                
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("\n💡 Make sure:")
        print("  • Docker containers are running")
        print("  • Database is accessible")
        print("  • Environment variables are set correctly")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking Supplier-Contract Relationships in Database")
    print("=" * 60)
    
    success = check_supplier_contract_links()
    
    if success:
        print("\n✅ Check completed successfully!")
    else:
        print("\n❌ Check failed!")
        sys.exit(1)
