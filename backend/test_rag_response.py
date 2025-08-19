#!/usr/bin/env python3
"""
Test script to debug RAG response structure and see what's actually being returned
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.ai_assistant import AIAssistantService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_rag_response():
    """Test the RAG response structure"""
    
    try:
        print("🚀 Testing RAG response structure...")
        
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Test the RAG search directly
        clause_types = ["early termination"]
        clause_conditions = {"duration": "over 3 months", "amounts": "order value"}
        risk_factors = []
        filters = {"organization_id": 1}
        
        print(f"🔍 Testing RAG search for: {clause_types}")
        print(f"📋 Conditions: {clause_conditions}")
        
        # Call the RAG search method directly
        rag_results = await ai_service._rag_search_through_documents(
            clause_types=clause_types,
            clause_conditions=clause_conditions,
            risk_factors=risk_factors,
            filters=filters
        )
        
        print("\n📊 RAG Results Structure:")
        print(f"Keys: {list(rag_results.keys())}")
        
        if 'matching_documents' in rag_results:
            print(f"\n📄 Matching Documents: {len(rag_results['matching_documents'])}")
            for i, doc in enumerate(rag_results['matching_documents']):
                print(f"  Document {i+1}:")
                print(f"    ID: {doc.get('document_id')}")
                print(f"    Filename: {doc.get('filename')}")
                print(f"    Supplier: {doc.get('supplier_name')}")
                print(f"    Score: {doc.get('relevance_score')}")
        else:
            print("❌ No matching_documents in RAG results")
        
        if 'clause_findings' in rag_results:
            print(f"\n🔍 Clause Findings: {len(rag_results['clause_findings'])}")
            for finding in rag_results['clause_findings']:
                print(f"  - {finding}")
        
        if 'risk_indicators' in rag_results:
            print(f"\n⚠️ Risk Indicators: {len(rag_results['risk_indicators'])}")
            for risk in rag_results['risk_indicators']:
                print(f"  - {risk}")
        
        if 'recommendations' in rag_results:
            print(f"\n💡 Recommendations: {len(rag_results['recommendations'])}")
            for rec in rag_results['recommendations']:
                print(f"  - {rec}")
        
        print("\n✅ RAG test completed!")
        
    except Exception as e:
        print(f"❌ RAG test failed: {str(e)}")
        logger.error("RAG test failed", error=str(e))
        raise

if __name__ == "__main__":
    print("🧪 Starting RAG Response Structure Test...")
    asyncio.run(test_rag_response())
    print("🎉 RAG test completed!")
