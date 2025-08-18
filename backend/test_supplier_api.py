#!/usr/bin/env python3
"""
Test script for supplier API endpoints.
Run this to verify the supplier functionality works correctly.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_supplier_profile_creation():
    """Test creating a supplier profile."""
    print("Testing supplier profile creation...")
    
    # Test data for supplier creation
    supplier_data = {
        "name": f"Test Supplier {datetime.now().strftime('%H%M%S')}",
        "industry": "manufacturing",
        "location": "Detroit, MI",
        "country": "US",
        "contact_email": "contact@testmanufacturing.com",
        "contact_phone": "+1-555-0123",
        "website": "https://testmanufacturing.com",
        "address": "123 Industrial Blvd, Detroit, MI 48201",
        "company_size": "medium",
        "revenue_range": "10-50 million",
        "employee_count": 250,
        "organization_id": 1  # Assuming organization 1 exists
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/suppliers/profile",
            json=supplier_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            supplier = response.json()
            print(f"✅ Supplier created successfully!")
            print(f"   ID: {supplier['id']}")
            print(f"   Name: {supplier['name']}")
            print(f"   Risk Score: {supplier['risk_score']}")
            print(f"   Risk Level: {supplier['risk_level']}")
            print(f"   Risk Factors: {json.dumps(supplier['risk_factors'], indent=2)}")
            return supplier['id']
        else:
            print(f"❌ Failed to create supplier: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_supplier_risk_retrieval(supplier_id):
    """Test retrieving supplier risk assessment."""
    if not supplier_id:
        print("❌ No supplier ID to test risk retrieval")
        return
    
    print(f"\nTesting supplier risk retrieval for ID {supplier_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/suppliers/{supplier_id}/risk")
        
        if response.status_code == 200:
            risk_data = response.json()
            print(f"✅ Risk assessment retrieved successfully!")
            print(f"   Supplier: {risk_data['supplier_name']}")
            print(f"   Risk Score: {risk_data['risk_score']}")
            print(f"   Risk Level: {risk_data['risk_level']}")
            print(f"   Alert Level: {risk_data['alert_level']}")
            print(f"   Watchlist Status: {risk_data['watchlist_status']}")
            print(f"   Recommendations:")
            for rec in risk_data['recommendations']:
                print(f"     - {rec}")
        else:
            print(f"❌ Failed to retrieve risk assessment: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_supplier_listing():
    """Test listing suppliers."""
    print(f"\nTesting supplier listing...")
    
    try:
        response = requests.get(f"{API_BASE}/suppliers/")
        
        if response.status_code == 200:
            suppliers_data = response.json()
            print(f"✅ Suppliers list retrieved successfully!")
            print(f"   Total Count: {suppliers_data['total_count']}")
            print(f"   Page: {suppliers_data['page']}")
            print(f"   Page Size: {suppliers_data['page_size']}")
            print(f"   Total Pages: {suppliers_data['total_pages']}")
            
            if suppliers_data['suppliers']:
                print(f"   Sample suppliers:")
                for supplier in suppliers_data['suppliers'][:3]:  # Show first 3
                    print(f"     - {supplier['name']} (Risk: {supplier['risk_score']})")
            else:
                print(f"   No suppliers found")
        else:
            print(f"❌ Failed to retrieve suppliers list: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_supplier_retrieval(supplier_id):
    """Test retrieving a specific supplier."""
    if not supplier_id:
        print("❌ No supplier ID to test retrieval")
        return
    
    print(f"\nTesting supplier retrieval for ID {supplier_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/suppliers/{supplier_id}")
        
        if response.status_code == 200:
            supplier = response.json()
            print(f"✅ Supplier retrieved successfully!")
            print(f"   Name: {supplier['name']}")
            print(f"   Industry: {supplier['industry']}")
            print(f"   Location: {supplier['location']}")
            print(f"   Company Size: {supplier['company_size']}")
            print(f"   Created: {supplier['created_at']}")
        else:
            print(f"❌ Failed to retrieve supplier: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def main():
    """Main test function."""
    print("🚀 Starting Supplier API Tests")
    print("=" * 50)
    
    # Test 1: Create supplier profile
    supplier_id = test_supplier_profile_creation()
    
    # Test 2: Retrieve supplier risk assessment
    test_supplier_risk_retrieval(supplier_id)
    
    # Test 3: List suppliers
    test_supplier_listing()
    
    # Test 4: Retrieve specific supplier
    test_supplier_retrieval(supplier_id)
    
    print("\n" + "=" * 50)
    print("🏁 Supplier API Tests Completed")
    
    if supplier_id:
        print(f"\nTest supplier created with ID: {supplier_id}")
        print("You can use this ID for further testing or cleanup.")

if __name__ == "__main__":
    main()
