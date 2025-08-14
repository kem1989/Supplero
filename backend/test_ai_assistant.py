#!/usr/bin/env python3
"""
Simple test script for the AI Assistant service.
Run this to verify the basic functionality works.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.ai_assistant import AIAssistantService, IntentType


async def test_ai_assistant():
    """Test the AI Assistant service with sample queries"""
    
    print("🧪 Testing AI Assistant Service")
    print("=" * 50)
    
    # Initialize the service
    try:
        ai_service = AIAssistantService()
        print("✅ AI Assistant service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Assistant service: {e}")
        return
    
    # Test queries
    test_queries = [
        "Find contracts with supplier ABC Corp",
        "Show me details for contract ABC-123",
        "Export all contracts to CSV",
        "What's the weather like today?",
        "Search for high-value contracts over $100,000"
    ]
    
    print(f"\n📝 Testing {len(test_queries)} sample queries...")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        
        try:
            # Process the query
            query_intent = await ai_service.process_query(query)
            
            print(f"   Intent: {query_intent.intent.value}")
            print(f"   Confidence: {query_intent.confidence:.2f}")
            print(f"   Parameters: {query_intent.parameters}")
            
            # Check confidence threshold
            confidence_met = ai_service.validate_intent_confidence(query_intent)
            print(f"   Meets 90% threshold: {'✅' if confidence_met else '❌'}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test available tools
    print(f"\n🛠️  Available Tools")
    print("-" * 50)
    
    try:
        tools = ai_service.get_available_tools()
        for tool_name, tool_info in tools.items():
            print(f"   {tool_name}: {tool_info['description']}")
            print(f"      Parameters: {list(tool_info['parameters'].keys())}")
            print(f"      Examples: {tool_info['examples'][:2]}")  # Show first 2 examples
            print()
    except Exception as e:
        print(f"   ❌ Error getting tools: {e}")
    
    print("🎯 Testing completed!")


if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set it before running this test.")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_ai_assistant())





