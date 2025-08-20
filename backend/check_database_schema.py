#!/usr/bin/env python3
"""
Script to check the actual database schema and see what tables exist.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, inspect

def check_database_schema():
    """Check what tables exist in the database and their structure."""
    
    # Database connection for Docker setup
    database_url = "postgresql://supplero:supplero_dev@supplero-postgres:5432/supplero"
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Successfully connected to database")
            
            # Get list of all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 Found {len(tables)} tables in database:")
            for table in tables:
                print(f"  • {table}")
            
            # Check suppliers table structure
            if 'suppliers' in tables:
                print(f"\n🔍 Suppliers table structure:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'suppliers'
                    ORDER BY ordinal_position
                """))
                
                for row in result.fetchall():
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {row[3]}" if row[3] else ""
                    print(f"  • {row[0]}: {row[1]} {nullable}{default}")
                
                # Check suppliers data
                result = conn.execute(text("SELECT COUNT(*) FROM suppliers"))
                supplier_count = result.fetchone()[0]
                print(f"\n📊 Suppliers table has {supplier_count} records")
                
                if supplier_count > 0:
                    result = conn.execute(text("""
                        SELECT name, industry, location, risk_score, created_at 
                        FROM suppliers 
                        LIMIT 5
                    """))
                    print("  Sample suppliers:")
                    for row in result.fetchall():
                        print(f"    • {row[0]} ({row[1] or 'N/A'}) - {row[2] or 'N/A'} - Risk: {row[3]}")
            
            # Check documents table structure (if it exists)
            if 'documents' in tables:
                print(f"\n🔍 Documents table structure:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'documents'
                    ORDER BY ordinal_position
                """))
                
                for row in result.fetchall():
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {row[3]}" if row[3] else ""
                    print(f"  • {row[0]}: {row[1]} {nullable}{default}")
                
                                    # Check documents data
                    result = conn.execute(text("SELECT COUNT(*) FROM documents"))
                    doc_count = result.fetchone()[0]
                    print(f"\n📄 Documents table has {doc_count} records")
                    
                    if doc_count > 0:
                        result = conn.execute(text("""
                            SELECT filename, document_type, status, created_at 
                            FROM documents 
                            LIMIT 5
                        """))
                        print("  Sample documents:")
                        for row in result.fetchall():
                            print(f"    • {row[0]} - Type: {row[1] or 'N/A'} - Status: {row[2] or 'N/A'}")
                    
                    # Check for contract-related documents
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM documents 
                        WHERE filename LIKE '%contract%'
                    """))
                    contract_docs = result.fetchone()[0]
                    print(f"  Documents with 'contract' in filename: {contract_docs}")
                    
                    # Check for supplier names in document metadata
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM documents 
                        WHERE extracted_metadata IS NOT NULL 
                          AND extracted_metadata::text LIKE '%supplier%'
                    """))
                    supplier_metadata_docs = result.fetchone()[0]
                    print(f"  Documents with supplier metadata: {supplier_metadata_docs}")
                    
                    # Check what document types exist
                    result = conn.execute(text("""
                        SELECT DISTINCT document_type 
                        FROM documents
                    """))
                    doc_types = [row[0] for row in result.fetchall()]
                    print(f"  Available document types: {doc_types}")
                    
                    # Check document metadata for supplier information
                    if doc_count > 0:
                        result = conn.execute(text("""
                            SELECT filename, document_type, extracted_metadata
                            FROM documents 
                            WHERE extracted_metadata IS NOT NULL
                            LIMIT 3
                        """))
                        print("  Sample documents with metadata:")
                        for row in result.fetchall():
                            print(f"    • {row[0]} - Type: {row[1]}")
                            if row[2]:
                                metadata_str = str(row[2])[:200] + "..." if len(str(row[2])) > 200 else str(row[2])
                                print(f"      Metadata: {metadata_str}")
            
            # Check for any other relevant tables
            relevant_tables = ['contracts', 'contract_clauses', 'organizations', 'users']
            for table in relevant_tables:
                if table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"\n📊 {table} table has {count} records")
            
            # Check for foreign key relationships
            print(f"\n🔗 Foreign Key Relationships:")
            result = conn.execute(text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name, kcu.column_name
            """))
            
            fks = result.fetchall()
            if fks:
                for fk in fks:
                    print(f"  • {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
            else:
                print("  No foreign key relationships found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking Database Schema and Structure")
    print("=" * 60)
    
    success = check_database_schema()
    
    if success:
        print("\n✅ Schema check completed successfully!")
    else:
        print("\n❌ Schema check failed!")
        sys.exit(1)
