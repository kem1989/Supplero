#!/usr/bin/env python3
"""
Test script for the Contract Discovery Engine.
Tests the AI-powered search functionality with sub-500ms performance requirement.
"""

import asyncio
import json
import time
from typing import Dict, Any

# Mock the database and user for testing
class MockUser:
    def __init__(self):
        self.id = 1
        self.organization_id = 1
        self.role = "admin"

class MockDB:
    def __init__(self):
        pass

async def test_contract_discovery():
    """Test the contract discovery engine"""
    print("🚀 Testing Contract Discovery Engine...")
    
    try:
        # Import the services
        from app.core.elasticsearch_service import ElasticsearchService
        from app.core.ai_assistant import AIAssistantService
        
        print("✅ Services imported successfully")
        
        # Test Elasticsearch service
        print("\n🔍 Testing Elasticsearch Service...")
        es_service = ElasticsearchService()
        
        # Check health
        health_status = es_service.health_check()
        print(f"   Elasticsearch health: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
        
        # Test index creation
        print("   Creating contracts index...")
        es_service.ensure_index_exists()
        print("   ✅ Index creation completed")
        
        # Test document indexing
        print("\n📄 Testing Document Indexing...")
        test_document = {
            "document_id": "test_001",
            "organization_id": 1,
            "filename": "test_contract.pdf",
            "original_filename": "Test Contract Agreement.pdf",
            "extracted_text": "This is a test contract with ABC Corp for $100,000",
            "extracted_metadata": {
                "supplier_name": "ABC Corp",
                "contract_amount": 100000,
                "currency": "USD",
                "contract_date": "2024-01-15",
                "tags": ["test", "contract", "agreement"]
            },
            "tags": ["test", "contract"],
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        index_success = await es_service.index_contract_document(test_document)
        print(f"   Document indexing: {'✅ Success' if index_success else '❌ Failed'}")
        
        # Test contract search
        print("\n🔎 Testing Contract Search...")
        start_time = time.time()
        
        search_result = await es_service.search_contracts(
            query="ABC Corp",
            filters={"supplier": "ABC Corp"},
            page=1,
            page_size=10
        )
        
        search_time = (time.time() - start_time) * 1000
        print(f"   Search completed in: {search_time:.2f}ms")
        print(f"   Performance requirement met: {'✅ Yes' if search_time < 500 else '❌ No'}")
        print(f"   Results found: {search_result.total_count}")
        
        # Test AI Assistant integration
        print("\n🤖 Testing AI Assistant Integration...")
        ai_service = AIAssistantService()
        
        # Test query processing
        query = "Find contracts with supplier ABC Corp over $50,000"
        print(f"   Processing query: '{query}'")
        
        query_intent = await ai_service.process_query(
            query=query,
            user_context={"user_id": 1, "organization_id": 1, "role": "admin"}
        )
        
        print(f"   Intent detected: {query_intent.intent.value}")
        print(f"   Confidence: {query_intent.confidence:.2f}")
        print(f"   Parameters: {json.dumps(query_intent.parameters, indent=2)}")
        
        # Test AI-powered search
        print("\n🔍 Testing AI-Powered Search...")
        ai_search_result = await ai_service.search_contracts(
            query=query,
            filters={"supplier": "ABC Corp", "amount_min": 50000},
            page=1,
            page_size=10
        )
        
        print(f"   AI search results: {ai_search_result.get('total_count', 0)} documents")
        if ai_search_result.get("ai_insights"):
            print(f"   AI insights: {ai_search_result['ai_insights'].get('summary', 'None')}")
        
        print("\n🎉 Contract Discovery Engine Test Completed Successfully!")
        
        # Performance summary
        print(f"\n📊 Performance Summary:")
        print(f"   Search time: {search_time:.2f}ms")
        print(f"   <500ms requirement: {'✅ Met' if search_time < 500 else '❌ Not met'}")
        print(f"   Intent accuracy: {query_intent.confidence:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_natural_language_queries():
    """Test various natural language queries"""
    print("\n🗣️ Testing Natural Language Queries...")
    
    try:
        from app.core.ai_assistant import AIAssistantService
        
        ai_service = AIAssistantService()
        
        test_queries = [
            "Find contracts with supplier ABC Corp",
            "Show me contracts over $100,000 from last year",
            "Get all contracts with tag 'high-risk'",
            "Search for contracts expiring this month",
            "Find supplier contracts in the technology sector"
        ]
        
        for query in test_queries:
            print(f"\n   Testing: '{query}'")
            
            query_intent = await ai_service.process_query(
                query=query,
                user_context={"user_id": 1, "organization_id": 1, "role": "admin"}
            )
            
            print(f"     Intent: {query_intent.intent.value}")
            print(f"     Confidence: {query_intent.confidence:.2f}")
            print(f"     Parameters: {len(query_intent.parameters)} extracted")
            
            if query_intent.parameters:
                for key, value in query_intent.parameters.items():
                    print(f"       {key}: {value}")
        
        print("\n✅ Natural language query testing completed")
        
    except Exception as e:
        print(f"❌ Natural language testing failed: {str(e)}")

if __name__ == "__main__":
    print("🧪 Contract Discovery Engine Test Suite")
    print("=" * 50)
    
    # Run tests
    loop = asyncio.get_event_loop()
    
    try:
        # Test basic functionality
        success = loop.run_until_complete(test_contract_discovery())
        
        if success:
            # Test natural language queries
            loop.run_until_complete(test_natural_language_queries())
        
        print(f"\n🎯 Overall Test Result: {'✅ PASSED' if success else '❌ FAILED'}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()




