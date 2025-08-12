#!/usr/bin/env python3
"""
Test script to generate an authentication token and test the contract search endpoint.
"""

import asyncio
import requests
import json

async def test_contract_search_with_auth():
    """Test the contract search endpoint with proper authentication"""
    
    # Base URL
    base_url = "http://localhost:8000"
    
    # First, try to login to get a token
    print("🔐 Attempting to login...")
    
    login_data = {
        "email": "test@supplero.com",
        "password": "test123"
    }
    
    try:
        # Try to login
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Login successful! Token: {access_token[:20]}...")
            
            # Now test the contract search endpoint
            print("\n🔍 Testing contract search endpoint...")
            
            search_data = {
                "query": "Find contracts with supplier ABC Corp",
                "user_context": None
            }
            
            search_response = requests.post(
                f"{base_url}/api/v1/ai-assistant/search-contracts",
                json=search_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            print(f"Search response status: {search_response.status_code}")
            
            if search_response.status_code == 200:
                result = search_response.json()
                print("✅ Contract search successful!")
                print(f"Results: {result.get('total_count', 0)} contracts found")
                print(f"Search time: {result.get('search_time_ms', 0)}ms")
                if result.get('ai_insights'):
                    print(f"AI Insights: {result['ai_insights'].get('summary', 'None')}")
            else:
                print(f"❌ Contract search failed: {search_response.status_code}")
                print(f"Error: {search_response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Error: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing Contract Search with Authentication")
    print("=" * 50)
    
    asyncio.run(test_contract_search_with_auth())
