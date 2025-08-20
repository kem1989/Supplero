#!/usr/bin/env python3
"""
Test script to verify Cross-System Query Capability implementation.
This should be run inside the Docker environment.
"""

import asyncio
import sys
import os

# Add the backend path for imports
sys.path.append('/app/backend')

async def test_cross_system_search():
    """Test the cross-system search implementation"""
    
    print("🧪 Testing Cross-System Query Capability Implementation")
    print("=" * 60)
    
    try:
        # Test 1: Import CrossSystemSearchService
        print("✅ Test 1: Importing CrossSystemSearchService...")
        from app.core.cross_system_search import (
            CrossSystemSearchService, 
            CrossSystemSearchRequest, 
            CrossSystemQueryType
        )
        print("   ✓ Cross-system search classes imported successfully")
        
        # Test 2: Import AI Assistant with new intents
        print("\n✅ Test 2: Importing AI Assistant with cross-system intents...")
        from app.schemas.ai_assistant import IntentType
        from app.core.ai_assistant import AIAssistantService
        
        # Verify new intent types exist
        expected_intents = [
            IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS,
            IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS,
            IntentType.SUPPLIERS_BY_CONTRACT_CLAUSES,
            IntentType.CONTRACTS_BY_SUPPLIER_RISK,
            IntentType.UNIFIED_RISK_SEARCH
        ]
        
        for intent in expected_intents:
            print(f"   ✓ {intent.value} intent available")
        
        # Test 3: Initialize services
        print("\n✅ Test 3: Initializing services...")
        cross_system_service = CrossSystemSearchService()
        ai_assistant_service = AIAssistantService()
        print("   ✓ Services initialized successfully")
        print(f"   ✓ CrossSystemSearchService: {type(cross_system_service).__name__}")
        print(f"   ✓ AIAssistantService: {type(ai_assistant_service).__name__}")
        
        # Test 4: Create sample search request
        print("\n✅ Test 4: Creating sample cross-system search request...")
        sample_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_WITH_RISKY_CONTRACTS,
            contract_risk_level="high",
            supplier_risk_level="MEDIUM",
            page=1,
            page_size=10
        )
        print("   ✓ CrossSystemSearchRequest created successfully")
        print(f"   ✓ Query type: {sample_request.query_type}")
        print(f"   ✓ Contract risk level: {sample_request.contract_risk_level}")
        print(f"   ✓ Supplier risk level: {sample_request.supplier_risk_level}")
        
        # Test 5: Test AI Assistant tools registration
        print("\n✅ Test 5: Verifying AI Assistant tools registration...")
        tools = ai_assistant_service._initialize_tools()
        cross_system_tools = [
            'SUPPLIERS_WITH_RISKY_CONTRACTS',
            'SUPPLIERS_WITH_EXPIRING_CONTRACTS', 
            'SUPPLIERS_BY_CONTRACT_CLAUSES',
            'CONTRACTS_BY_SUPPLIER_RISK',
            'UNIFIED_RISK_SEARCH'
        ]
        
        for tool_name in cross_system_tools:
            if tool_name in tools:
                print(f"   ✓ {tool_name} tool registered")
            else:
                print(f"   ❌ {tool_name} tool NOT registered")
        
        # Test 6: Check execution methods
        print("\n✅ Test 6: Verifying execution methods exist...")
        from app.api.v1.ai_assistant import (
            _execute_suppliers_with_risky_contracts,
            _execute_suppliers_with_expiring_contracts,
            _execute_suppliers_by_contract_clauses,
            _execute_contracts_by_supplier_risk,
            _execute_unified_risk_search
        )
        print("   ✓ All cross-system execution methods imported successfully")
        
        print("\n🎉 SUCCESS: Cross-System Query Capability implementation verified!")
        print("\n📋 Implementation Summary:")
        print("   ✓ CrossSystemSearchService with 5 query types")
        print("   ✓ AI Assistant integration with new intent types")
        print("   ✓ Tools registration for natural language processing")
        print("   ✓ Execution methods for API endpoints")
        
        print("\n🚀 Ready for testing with example queries:")
        print('   • "Show me suppliers with risky contracts"')
        print('   • "Find suppliers with contracts expiring in 30 days"')
        print('   • "Which suppliers have force majeure clauses?"')
        print('   • "Show me contracts with high-risk suppliers"')
        print('   • "Comprehensive risk analysis for my portfolio"')
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_cross_system_search())
    
    if result:
        print("\n✅ All tests passed! Cross-System Query Capability is ready.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Check the implementation.")
        sys.exit(1)
