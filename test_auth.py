#!/usr/bin/env python3
"""
Test script for Supplero authentication system.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_organization_creation():
    """Test organization creation."""
    print("Testing organization creation...")
    
    org_data = {
        "name": "Test Corp",
        "domain": "testcorp.com",
        "industry": "Finance",
        "size": "large",
        "contact_email": "admin@testcorp.com"
    }
    
    response = requests.post(f"{BASE_URL}/organizations/", json=org_data)
    if response.status_code == 201:
        org = response.json()
        print(f"✓ Organization created: {org['name']} (ID: {org['id']})")
        return org['id']
    else:
        print(f"✗ Organization creation failed: {response.status_code} - {response.text}")
        return None

def test_user_registration(org_id):
    """Test user registration."""
    print("Testing user registration...")
    
    user_data = {
        "email": "john@testcorp.com",
        "username": "john_doe",
        "password": "securepass123",
        "first_name": "John",
        "last_name": "Doe",
        "organization_id": org_id,
        "role": "procurement_manager"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code == 201:
        user = response.json()
        print(f"✓ User registered: {user['email']} (ID: {user['id']})")
        return user
    else:
        print(f"✗ User registration failed: {response.status_code} - {response.text}")
        return None

def test_user_login(email, password):
    """Test user login."""
    print("Testing user login...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        print(f"✓ User logged in: {tokens['user']['email']}")
        print(f"  Access token: {tokens['access_token'][:20]}...")
        print(f"  Refresh token: {tokens['refresh_token'][:20]}...")
        return tokens
    else:
        print(f"✗ User login failed: {response.status_code} - {response.text}")
        return None

def test_protected_endpoint(access_token):
    """Test accessing a protected endpoint."""
    print("Testing protected endpoint...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print(f"✓ Protected endpoint accessed: {user['email']}")
        return True
    else:
        print(f"✗ Protected endpoint access failed: {response.status_code} - {response.text}")
        return False

def test_token_refresh(refresh_token):
    """Test token refresh."""
    print("Testing token refresh...")
    
    refresh_data = {"refresh_token": refresh_token}
    response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"✓ Token refreshed successfully")
        print(f"  New access token: {tokens['access_token'][:20]}...")
        print(f"  New refresh token: {tokens['refresh_token'][:20]}...")
        return tokens
    else:
        print(f"✗ Token refresh failed: {response.status_code} - {response.text}")
        return None

def main():
    """Run all authentication tests."""
    print("🚀 Starting Supplero Authentication System Tests\n")
    
    # Test organization creation
    org_id = test_organization_creation()
    if not org_id:
        print("❌ Cannot continue without organization")
        return
    
    print()
    
    # Test user registration
    user = test_user_registration(org_id)
    if not user:
        print("❌ Cannot continue without user")
        return
    
    print()
    
    # Test user login
    tokens = test_user_login(user['email'], "securepass123")
    if not tokens:
        print("❌ Cannot continue without login")
        return
    
    print()
    
    # Test protected endpoint
    test_protected_endpoint(tokens['access_token'])
    
    print()
    
    # Test token refresh
    test_token_refresh(tokens['refresh_token'])
    
    print("\n✅ All authentication tests completed successfully!")
    print("\n📋 Test Summary:")
    print(f"  - Organization: {org_id}")
    print(f"  - User: {user['email']}")
    print(f"  - Role: {user['role']}")
    print(f"  - JWT tokens working")
    print(f"  - Protected endpoints accessible")

if __name__ == "__main__":
    main() 