#!/usr/bin/env python3
"""
Test script to see the exact API response structure
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.ai_assistant import AIAssistantService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_api_response_structure():
    """Test the API response structure"""
    
    try:
        print("🚀 Testing API response structure...")
        
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
        
        print("\n📊 Search Result Structure:")
        print(f"Type: {type(search_result)}")
        print(f"Keys: {list(search_result.keys()) if isinstance(search_result, dict) else 'Not a dict'}")
        
        if isinstance(search_result, dict):
            for key, value in search_result.items():
                if key == 'documents':
                    print(f"\n📄 Documents field:")
                    print(f"  Type: {type(value)}")
                    print(f"  Length: {len(value) if hasattr(value, '__len__') else 'No length'}")
                    if value and len(value) > 0:
                        print(f"  First document keys: {list(value[0].keys()) if isinstance(value[0], dict) else 'Not a dict'}")
                        print(f"  First document: {value[0]}")
                else:
                    print(f"  {key}: {type(value)} - {str(value)[:100]}...")
        
        print("\n✅ API response structure test completed!")
        
    except Exception as e:
        print(f"❌ API response structure test failed: {str(e)}")
        logger.error("API response structure test failed", error=str(e))
        raise

if __name__ == "__main__":
    print("🧪 Starting API Response Structure Test...")
    asyncio.run(test_api_response_structure())
    print("🎉 API response structure test completed!")
