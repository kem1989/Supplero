#!/usr/bin/env python3
"""
Test script for external data aggregation service.
This script tests the basic functionality of the external data aggregation service.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.external_data_aggregation import ExternalDataAggregationService


async def test_external_data_aggregation():
    """Test the external data aggregation service."""
    print("Testing External Data Aggregation Service...")
    print("=" * 50)
    
    # Create service instance
    service = ExternalDataAggregationService()
    
    # Test with a sample supplier
    supplier_name = "Tesla Inc"
    industry = "automotive"
    country = "US"
    
    print(f"Testing with supplier: {supplier_name}")
    print(f"Industry: {industry}")
    print(f"Country: {country}")
    print()
    
    try:
        # Aggregate external data
        print("Aggregating external data...")
        result = await service.aggregate_supplier_risk_data(
            supplier_name=supplier_name,
            industry=industry,
            country=country
        )
        
        print("✅ External data aggregation completed successfully!")
        print()
        
        # Display results
        print("Results Summary:")
        print(f"  - Data sources used: {', '.join(result.get('data_sources', []))}")
        print(f"  - Risk signals found: {len(result.get('risk_signals', []))}")
        print(f"  - Overall risk score: {result.get('risk_indicators', {}).get('overall_risk_score', 'N/A')}")
        print(f"  - Summary: {result.get('summary', 'N/A')}")
        print()
        
        # Display risk signals if any
        risk_signals = result.get('risk_signals', [])
        if risk_signals:
            print("Risk Signals Detected:")
            for i, signal in enumerate(risk_signals[:5], 1):  # Show first 5 signals
                print(f"  {i}. {signal.description}")
                print(f"     Severity: {signal.severity}, Confidence: {signal.confidence_score:.2f}")
                print(f"     Source: {signal.source}, Type: {signal.signal_type}")
                print()
        else:
            print("No risk signals detected.")
            print()
        
        # Display news data if available
        news_data = result.get('news_data', [])
        if news_data:
            print(f"News Articles Found: {len(news_data)}")
            for i, article in enumerate(news_data[:3], 1):  # Show first 3 articles
                print(f"  {i}. {article.title}")
                print(f"     Sentiment: {article.sentiment_score:.2f}, Relevance: {article.relevance_score:.2f}")
                print(f"     Source: {article.source}")
                print()
        else:
            print("No news data available.")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during external data aggregation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_news_api_integration():
    """Test the News API integration specifically."""
    print("\nTesting News API Integration...")
    print("=" * 50)
    
    service = ExternalDataAggregationService()
    
    if not service.news_api_key:
        print("⚠️  News API key not configured - using placeholder data")
        return True
    
    try:
        # Test news fetching
        print("Fetching news data...")
        news_data = await service._fetch_news_data("Apple Inc", "technology")
        
        if news_data:
            print(f"✅ News API integration working! Found {len(news_data)} articles")
            for article in news_data[:2]:
                print(f"  - {article.title}")
                print(f"    Sentiment: {article.sentiment_score:.2f}")
        else:
            print("⚠️  News API returned no results (this might be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ News API integration error: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("External Data Aggregation Service Test")
    print("=" * 50)
    print()
    
    # Test basic functionality
    success1 = await test_external_data_aggregation()
    
    # Test News API integration
    success2 = await test_news_api_integration()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    print("\nNote: If you see 'News API key not configured' messages,")
    print("you can add NEWS_API_KEY to your environment variables")
    print("to test with real news data.")


if __name__ == "__main__":
    asyncio.run(main())





