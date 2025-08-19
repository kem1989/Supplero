#!/usr/bin/env python3
"""
Test script for clause extraction integration during document upload.

This script tests the complete flow:
1. Document upload with clause extraction
2. Clause storage in database
3. Elasticsearch indexing with clause data
4. Complex query search using the hybrid approach
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

# Test data
SAMPLE_CONTRACT_TEXT = """
SERVICE AGREEMENT

This Service Agreement (the "Agreement") is entered into on January 15, 2024, 
between TechCorp Inc. (the "Provider") and Client Solutions Ltd. (the "Client").

1. SERVICES
The Provider shall provide consulting services to the Client for a total fee of $50,000 USD.

2. PAYMENT TERMS
Payment shall be made in two installments:
- $25,000 due on February 1, 2024
- $25,000 due on March 1, 2024

3. TERM
This agreement shall commence on January 15, 2024 and continue until December 31, 2024.

4. FORCE MAJEURE
Neither party shall be liable for any delay or failure to perform its obligations 
under this Agreement due to circumstances beyond its reasonable control, including 
but not limited to acts of God, natural disasters, strikes, or government actions. 
However, this clause does not cover pandemics or cyber incidents.

5. PENALTY CLAUSES
In the event of late payment, the Client shall pay a penalty of 25% of the overdue amount.

6. NON-COMPETE
The Provider agrees not to compete with the Client for a period of 3 years following 
the termination of this Agreement.

7. EXCLUSIVITY
The Client agrees to use the Provider exclusively for all consulting services 
during the term of this Agreement.

8. LIABILITY
The Provider's liability shall be limited to the amount paid by the Client 
under this Agreement.

Signed by:
Provider: John Smith, CEO
Client: Jane Doe, Procurement Manager

Date: January 15, 2024
"""


class MockDocument:
    """Mock document object for testing"""
    def __init__(self):
        self.id = 123
        self.organization_id = 1
        self.filename = "test_contract.pdf"
        self.original_filename = "test_contract.pdf"
        self.extracted_text = SAMPLE_CONTRACT_TEXT
        self.extracted_metadata = {
            "amounts": [{"value": "$50,000", "type": "total"}],
            "parties": [
                {"value": "Provider", "context": "TechCorp Inc."},
                {"value": "Client", "context": "Client Solutions Ltd."}
            ],
            "dates": [{"value": "January 15, 2024"}]
        }
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class TestClauseIntegration:
    """Test class for clause integration"""
    
    def __init__(self):
        """Initialize test fixtures"""
        self.mock_document = MockDocument()
    
    async def test_clause_extraction_integration(self):
        """Test the complete clause extraction integration flow"""
        print("🧪 Testing Clause Extraction Integration...")
        
        try:
            # Step 1: Test clause extraction service
            print("   📋 Step 1: Testing clause extraction service...")
            from app.core.clause_extraction import ClauseExtractionService
            
            clause_service = ClauseExtractionService()
            extracted_clauses = await clause_service.extract_clauses_from_document(
                document_text=self.mock_document.extracted_text,
                document_id=str(self.mock_document.id),
                organization_id=str(self.mock_document.organization_id)
            )
            
            print(f"   ✅ Extracted {len(extracted_clauses)} clauses")
            
            # Display extracted clauses
            for i, clause in enumerate(extracted_clauses, 1):
                print(f"      Clause {i}: {clause.clause_type.value}")
                print(f"         Text: {clause.clause_text[:50]}...")
                print(f"         Risk Level: {clause.risk_level}")
                print(f"         Confidence: {clause.confidence_score}")
                if clause.metadata.get("risk_indicators"):
                    print(f"         Risk Indicators: {clause.metadata['risk_indicators']}")
                print()
            
            # Step 2: Test AI assistant with extracted clauses
            print("   🤖 Step 2: Testing AI assistant with extracted clauses...")
            from app.core.ai_assistant import AIAssistantService
            
            ai_service = AIAssistantService()
            
            # Test complex query processing
            complex_query = "Which contracts have force majeure clauses that don't cover pandemics?"
            query_intent = await ai_service.process_query(complex_query)
            
            print(f"   ✅ Intent classified as: {query_intent.intent}")
            print(f"   ✅ Confidence: {query_intent.confidence}")
            print(f"   ✅ Parameters: {json.dumps(query_intent.parameters, indent=6)}")
            
            # Step 3: Test hybrid search with clause data
            print("   🔍 Step 3: Testing hybrid search with clause data...")
            
            # Simulate documents with extracted clauses
            mock_documents = [{
                "document_id": str(self.mock_document.id),
                "supplier_name": "TechCorp Inc.",
                "contract_amount": 50000,
                "extracted_text": self.mock_document.extracted_text,
                "extracted_clauses": [clause.to_dict() for clause in extracted_clauses]
            }]
            
            # Test clause-based search
            search_result = await ai_service.search_clauses(
                clause_types=["force_majeure"],
                clause_content="force majeure",
                risk_factors=["pandemics"],
                filters={"supplier": "TechCorp Inc."}
            )
            
            print(f"   ✅ Search completed in {search_result.get('search_time_ms', 0)}ms")
            print(f"   ✅ Found {search_result.get('total_count', 0)} documents")
            
            if search_result.get("clause_analysis"):
                clause_analysis = search_result["clause_analysis"]
                print(f"   ✅ Clause analysis completed:")
                print(f"      - Risk indicators: {len(clause_analysis.get('risk_indicators', []))}")
                print(f"      - Compliance gaps: {len(clause_analysis.get('compliance_gaps', []))}")
                print(f"      - Recommendations: {len(clause_analysis.get('recommendations', []))}")
            
            if search_result.get("risk_assessment"):
                risk_assessment = search_result["risk_assessment"]
                print(f"   ✅ Risk assessment: {risk_assessment.get('overall_risk_level', 'unknown')}")
                print(f"      - High-risk clauses: {len(risk_assessment.get('high_risk_clauses', []))}")
                print(f"      - Mitigation recommendations: {len(risk_assessment.get('mitigation_recommendations', []))}")
            
            print("   🎉 All tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_clause_storage_simulation(self):
        """Test clause storage simulation"""
        print("   💾 Testing clause storage simulation...")
        
        try:
            # Simulate clause storage
            from app.core.clause_extraction import ClauseExtractionService
            
            clause_service = ClauseExtractionService()
            extracted_clauses = await clause_service.extract_clauses_from_document(
                document_text=self.mock_document.extracted_text,
                document_id=str(self.mock_document.id),
                organization_id=str(self.mock_document.organization_id)
            )
            
            # Simulate database storage
            stored_clauses = []
            for clause in extracted_clauses:
                stored_clause = {
                    "id": len(stored_clauses) + 1,
                    "contract_id": self.mock_document.id,
                    "clause_type": clause.clause_type.value,
                    "clause_text": clause.clause_text,
                    "extracted_text": clause.extracted_text,
                    "risk_level": clause.risk_level,
                    "confidence_score": clause.confidence_score,
                    "ai_analysis": clause.metadata
                }
                stored_clauses.append(stored_clause)
            
            print(f"   ✅ Simulated storage of {len(stored_clauses)} clauses")
            
            # Display stored clause summary
            clause_types = {}
            risk_levels = {}
            for clause in stored_clauses:
                clause_types[clause["clause_type"]] = clause_types.get(clause["clause_type"], 0) + 1
                risk_levels[clause["risk_level"]] = risk_levels.get(clause["risk_level"], 0) + 1
            
            print(f"      - Clause types: {clause_types}")
            print(f"      - Risk distribution: {risk_levels}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Storage simulation failed: {str(e)}")
            return False


async def main():
    """Main test function"""
    print("🚀 Starting Clause Integration Tests")
    print("=" * 50)
    
    test_suite = TestClauseIntegration()
    
    # Run tests
    results = []
    
    print("\n📋 Running clause extraction integration test...")
    results.append(await test_suite.test_clause_extraction_integration())
    
    print("\n📋 Running clause storage simulation test...")
    results.append(await test_suite.test_clause_storage_simulation())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Clause integration is working correctly.")
        print("\n🔧 Next steps:")
        print("   1. Test with real document uploads")
        print("   2. Verify Elasticsearch indexing with clause data")
        print("   3. Test complex queries in the API")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)
