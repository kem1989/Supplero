#!/usr/bin/env python3
"""
Test script for enhanced supplier-contract relationship queries.
Tests the new natural language query capabilities for supplier-contract relationships.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db, init_db
from app.api.v1.ai_assistant_utils.intent_classifier import IntentClassifier, IntentType
from app.api.v1.ai_assistant_utils.parameter_extractor import ParameterExtractor
from app.api.v1.handlers.cross_system_handlers import (
    execute_suppliers_by_contract_value,
    execute_suppliers_with_contract_criteria,
    execute_supplier_contract_portfolio
)
from app.models.user import User
from app.core.logging import setup_logging

# Test queries for supplier-contract relationships
TEST_QUERIES = [
    "Show me suppliers with contracts over $5 million",
    "Find suppliers with service contracts in technology",
    "Suppliers with contracts expiring in 30 days",
    "High-value contract suppliers in manufacturing",
    "Suppliers with payment terms net 60",
    "Contracts with suppliers in the healthcare industry",
    "Suppliers with multiple contracts over $1M",
    "Find suppliers with contracts in Europe over $500k"
]

async def test_intent_classification():
    """Test intent classification for supplier-contract relationship queries."""
    print("🔍 Testing Intent Classification...")
    print("=" * 50)
    
    classifier = IntentClassifier()
    
    for query in TEST_QUERIES:
        try:
            result = await classifier.classify_intent(query)
            print(f"Query: {query}")
            print(f"  Intent: {result.intent.value}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Reasoning: {result.reasoning}")
            print()
        except Exception as e:
            print(f"❌ Failed to classify: {query}")
            print(f"  Error: {e}")
            print()

async def test_parameter_extraction():
    """Test parameter extraction for supplier-contract relationship queries."""
    print("🔧 Testing Parameter Extraction...")
    print("=" * 50)
    
    extractor = ParameterExtractor()
    
    # Test with specific intents
    test_cases = [
        (IntentType.SUPPLIERS_BY_CONTRACT_VALUE, "Show me suppliers with contracts over $5 million"),
        (IntentType.SUPPLIERS_WITH_CONTRACT_CRITERIA, "Find suppliers with service contracts in technology"),
        (IntentType.SUPPLIER_CONTRACT_PORTFOLIO, "Suppliers with contracts in Europe over $500k")
    ]
    
    for intent, query in test_cases:
        try:
            parameters = await extractor.extract_parameters(query, intent)
            print(f"Query: {query}")
            print(f"  Intent: {intent.value}")
            print(f"  Parameters: {parameters}")
            print()
        except Exception as e:
            print(f"❌ Failed to extract parameters: {query}")
            print(f"  Error: {e}")
            print()

async def test_handler_execution():
    """Test handler execution for supplier-contract relationship queries."""
    print("⚡ Testing Handler Execution...")
    print("=" * 50)
    
    # Create a dummy user for testing
    test_user = User(
        id=1,
        email="test@example.com",
        organization_id=1
    )
    
    # Test parameters
    test_parameters = {
        "contract_value_min": 5000000,  # $5M
        "supplier_industry": "technology",
        "supplier_country": "United States"
    }
    
    try:
        # Get database session
        db = next(get_db())
        
        print("Testing suppliers by contract value handler...")
        result = await execute_suppliers_by_contract_value(test_parameters, db, test_user)
        print(f"  Success: {result.get('success', False)}")
        print(f"  Message: {result.get('message', 'No message')}")
        print(f"  Data keys: {list(result.get('data', {}).keys())}")
        print()
        
        print("Testing suppliers with contract criteria handler...")
        result = await execute_suppliers_with_contract_criteria(test_parameters, db, test_user)
        print(f"  Success: {result.get('success', False)}")
        print(f"  Message: {result.get('message', 'No message')}")
        print(f"  Data keys: {list(result.get('data', {}).keys())}")
        print()
        
        print("Testing supplier contract portfolio handler...")
        result = await execute_supplier_contract_portfolio(test_parameters, db, test_user)
        print(f"  Success: {result.get('success', False)}")
        print(f"  Message: {result.get('message', 'No message')}")
        print(f"  Data keys: {list(result.get('data', {}).keys())}")
        print()
        
    except Exception as e:
        print(f"❌ Handler execution failed: {e}")
        print()

async def test_ai_assistant_integration():
    """Test the complete AI assistant integration."""
    print("🤖 Testing AI Assistant Integration...")
    print("=" * 50)
    
    try:
        from app.api.v1.ai_assistant import AIAssistantService
        
        ai_service = AIAssistantService()
        
        # Test a natural language query
        test_query = "Show me suppliers with contracts over $5 million"
        
        print(f"Testing query: {test_query}")
        
        # Get database session
        db = next(get_db())
        
        # Create a dummy user for testing
        test_user = User(
            id=1,
            email="test@example.com",
            organization_id=1
        )
        
        # Process the query
        result = await ai_service.process_query(test_query, db, test_user)
        
        print(f"  Success: {result.get('success', False)}")
        print(f"  Intent: {result.get('intent_classification', {}).get('intent', 'Unknown')}")
        print(f"  Confidence: {result.get('intent_classification', {}).get('confidence', 0):.2f}")
        print(f"  Message: {result.get('message', 'No message')}")
        print(f"  Data keys: {list(result.get('data', {}).keys())}")
        print()
        
    except Exception as e:
        print(f"❌ AI Assistant integration failed: {e}")
        print()

async def main():
    """Main test function."""
    print("🚀 Testing Enhanced Supplier-Contract Relationship Feature")
    print("=" * 70)
    print()
    
    # Setup logging
    setup_logging()
    
    # Initialize database
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    print()
    
    # Run tests
    await test_intent_classification()
    await test_parameter_extraction()
    await test_handler_execution()
    await test_ai_assistant_integration()
    
    print("🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())

