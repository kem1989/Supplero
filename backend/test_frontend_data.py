#!/usr/bin/env python3
"""
Test script to simulate exactly what the frontend receives from the backend API
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.ai_assistant import AIAssistantService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_frontend_data_structure():
    """Test the exact data structure that the frontend receives"""
    
    try:
        print("🚀 Testing frontend data structure...")
        
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Test the search_clauses method directly
        clause_types = ["early termination"]
        clause_conditions = {"duration": "over 3 months", "amounts": "order value"}
        risk_factors = []
        filters = {"organization_id": 1}
        
        print(f"🔍 Testing search_clauses for: {clause_types}")
        
        # Call the search_clauses method directly
        search_result = await ai_service.search_clauses(
            clause_types=clause_types,
            clause_conditions=clause_conditions,
            risk_factors=risk_factors,
            filters=filters,
            page=1,
            page_size=20
        )
        
        # Simulate the exact structure that the frontend receives
        frontend_response = {
            "query_id": "exec_12_7626",
            "original_query": "Show contracts with early termination fees over 3 months of order value",
            "intent": "SEARCH_CLAUSES",
            "confidence": 0.98,
            "tool_executed": "SEARCH_CLAUSES",
            "execution_result": {
                "message": "Clause-based search executed successfully",
                "parameters_used": {
                    "clause_types": clause_types,
                    "clause_content": "fees",
                    "clause_conditions": clause_conditions,
                    "risk_factors": None,
                    "supplier": None,
                    "date_from": None,
                    "date_to": None,
                    "exclude_patterns": None
                },
                "search_results": search_result,
                "search_criteria": {
                    "clause_types": clause_types,
                    "risk_factors": risk_factors,
                    "filters": filters
                }
            },
            "execution_time_ms": 23043.72,
            "success": True,
            "error_message": None
        }
        
        print("\n📊 Frontend Response Structure:")
        print(f"Type: {type(frontend_response)}")
        print(f"Keys: {list(frontend_response.keys())}")
        
        print(f"\n🔍 Execution Result Keys: {list(frontend_response['execution_result'].keys())}")
        print(f"📄 Search Results Keys: {list(frontend_response['execution_result']['search_results'].keys())}")
        
        # Check the documents field specifically
        documents = frontend_response['execution_result']['search_results'].get('documents', [])
        print(f"\n📄 Documents Field:")
        print(f"  Type: {type(documents)}")
        print(f"  Length: {len(documents)}")
        print(f"  Is Array: {isinstance(documents, list)}")
        
        if documents and len(documents) > 0:
            print(f"  First document type: {type(documents[0])}")
            print(f"  First document keys: {list(documents[0].keys()) if isinstance(documents[0], dict) else 'Not a dict'}")
            
            # Check if the document has the expected structure
            first_doc = documents[0]
            if isinstance(first_doc, dict):
                expected_keys = ['document_id', 'filename', 'supplier_name', 'contract_amount', 'extracted_text', 'relevance_score']
                missing_keys = [key for key in expected_keys if key not in first_doc]
                if missing_keys:
                    print(f"  ⚠️  Missing keys: {missing_keys}")
                else:
                    print(f"  ✅ All expected keys present")
        
        # Test the frontend data access patterns
        print(f"\n🧪 Testing Frontend Data Access:")
        
        # Pattern 1: data.execution_result?.result?.search_results?.documents
        pattern1 = frontend_response.get('execution_result', {}).get('result', {}).get('search_results', {}).get('documents', [])
        print(f"  Pattern 1 (result.search_results.documents): {len(pattern1)} documents")
        
        # Pattern 2: data.execution_result?.search_results?.documents
        pattern2 = frontend_response.get('execution_result', {}).get('search_results', {}).get('documents', [])
        print(f"  Pattern 2 (search_results.documents): {len(pattern2)} documents")
        
        # Pattern 3: data.execution_result?.search_results?.total_count
        total_count = frontend_response.get('execution_result', {}).get('search_results', {}).get('total_count', 0)
        print(f"  Pattern 3 (search_results.total_count): {total_count}")
        
        print("\n✅ Frontend data structure test completed!")
        
    except Exception as e:
        print(f"❌ Frontend data structure test failed: {str(e)}")
        logger.error("Frontend data structure test failed", error=str(e))
        raise

if __name__ == "__main__":
    print("🧪 Starting Frontend Data Structure Test...")
    asyncio.run(test_frontend_data_structure())
    print("🎉 Frontend data structure test completed!")
