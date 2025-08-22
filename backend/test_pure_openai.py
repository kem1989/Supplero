#!/usr/bin/env python3
"""
Test script for pure OpenAI clause extraction
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.clause_extraction import ClauseExtractionService

async def test_pure_openai_extraction():
    """Test the pure OpenAI clause extraction"""
    
    # Sample contract text
    sample_contract = """
    SUPPLY AGREEMENT
    
    This Supply Agreement (the "Agreement") is entered into on July 1, 2024, between ABC Corp ("Buyer") and XYZ Supplies ("Supplier").
    
    ARTICLE 1: SCOPE OF WORK
    The Supplier shall provide manufacturing services for electronic components as specified in Exhibit A.
    
    ARTICLE 2: PAYMENT TERMS
    Payment is due within 30 days of invoice receipt. Late payments will incur a 2% monthly fee.
    
    ARTICLE 3: DELIVERY SCHEDULE
    Initial Delivery: July 1, 2024
    Monthly Deliveries: First week of each month
    Final Delivery: December 31, 2024
    
    ARTICLE 4: QUALITY STANDARDS
    All products must meet ISO 9001 standards. Supplier shall provide quality certificates.
    
    ARTICLE 5: FORCE MAJEURE
    Neither party shall be liable for delays due to circumstances beyond their control including natural disasters.
    
    ARTICLE 6: TERMINATION
    Either party may terminate this agreement with 30 days written notice for material breach.
    
    ARTICLE 7: LIABILITY
    Supplier's liability shall not exceed the total amount paid under this agreement.
    
    ARTICLE 8: CONFIDENTIALITY
    All technical and business information shared shall remain confidential for 5 years.
    
    ARTICLE 9: GOVERNING LAW
    This agreement shall be governed by the laws of the State of California.
    
    ARTICLE 10: DISPUTE RESOLUTION
    Any disputes shall be resolved through binding arbitration in San Francisco, CA.
    """
    
    print("🧪 Testing Pure OpenAI Clause Extraction")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key and try again")
        return
    
    try:
        # Initialize the service
        clause_service = ClauseExtractionService()
        
        print("📄 Sample Contract Text:")
        print(sample_contract[:200] + "...")
        print()
        
        print("🔍 Extracting clauses using pure OpenAI...")
        
        # Extract clauses
        extracted_clauses = await clause_service.extract_clauses(
            document_text=sample_contract,
            document_id="test_doc_001"
        )
        
        if extracted_clauses:
            print(f"✅ Successfully extracted {len(extracted_clauses)} clauses!")
            print()
            
            print("📋 Extracted Clauses:")
            for i, clause in enumerate(extracted_clauses, 1):
                print(f"{i}. {clause['clause_type'].upper()}")
                print(f"   Text: {clause['clause_text'][:80]}...")
                print(f"   Risk: {clause['risk_level']} (Confidence: {clause['confidence_score']})")
                print(f"   Context: {clause['extracted_text'][:100]}...")
                if clause['metadata'].get('reasoning'):
                    print(f"   Reasoning: {clause['metadata']['reasoning']}")
                print()
        else:
            print("⚠️  No clauses were extracted")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Pure OpenAI Clause Extraction Test...")
    asyncio.run(test_pure_openai_extraction())
    print("✅ Test completed!")
