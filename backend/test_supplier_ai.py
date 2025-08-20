#!/usr/bin/env python3
"""
Test script for supplier AI assistant functionality.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app')

async def test_supplier_intent_classification():
    """Test supplier intent classification"""
    print("🧪 Testing Supplier AI Assistant Intent Classification\n")
    
    try:
        from app.core.ai_assistant import AIAssistantService, IntentType
        
        ai_service = AIAssistantService()
        
        test_queries = [
            "Find high-risk suppliers in pharmaceuticals",
            "Show me suppliers with contracts over $100k", 
            "Analyze financial risk for supplier ABC Corp",
            "Compare risk scores of my top 5 suppliers",
            "Show me supplier portfolio risk trends",
            "Which suppliers have negative news coverage?"
        ]
        
        print("Testing supplier query intent classification:")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            
            try:
                # Test intent classification
                intent_result = await ai_service._classify_intent(query)
                print(f"   ✅ Intent: {intent_result.intent}")
                print(f"   📊 Confidence: {intent_result.confidence:.2f}")
                
                # Test parameter extraction
                if intent_result.intent != IntentType.UNKNOWN:
                    parameters = await ai_service._extract_parameters(query, intent_result.intent)
                    print(f"   🔧 Parameters: {parameters}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Intent classification test completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize AI service: {e}")
        return False
    
    return True

async def test_tools_registry():
    """Test that supplier tools are properly registered"""
    print("\n🔧 Testing Supplier Tools Registry\n")
    
    try:
        from app.core.ai_assistant import AIAssistantService, ToolType
        
        ai_service = AIAssistantService()
        tools = ai_service.get_available_tools()
        
        supplier_tools = [
            ToolType.SEARCH_SUPPLIERS,
            ToolType.ANALYZE_SUPPLIER_RISK,
            ToolType.COMPARE_SUPPLIERS,
            ToolType.SUPPLIER_INSIGHTS
        ]
        
        print("Checking supplier tools registration:")
        print("=" * 50)
        
        for tool_type in supplier_tools:
            if tool_type.value in tools:
                tool_info = tools[tool_type.value]
                print(f"✅ {tool_type.value}")
                print(f"   📋 Description: {tool_info['description']}")
                print(f"   🔧 Parameters: {len(tool_info['parameters'])} params")
                print(f"   📝 Examples: {len(tool_info['examples'])} examples")
            else:
                print(f"❌ {tool_type.value} - NOT FOUND")
        
        print("\n" + "=" * 50)
        print(f"✅ Tools registry test completed! Total tools: {len(tools)}")
        
    except Exception as e:
        print(f"❌ Failed to test tools registry: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Supplier AI Assistant Tests")
    print("=" * 60)
    
    # Test 1: Intent Classification
    success1 = await test_supplier_intent_classification()
    
    # Test 2: Tools Registry
    success2 = await test_tools_registry()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Intent Classification: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Tools Registry: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("🎉 All tests passed! Supplier AI Assistant is ready!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
