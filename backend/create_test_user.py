#!/usr/bin/env python3
"""
Script to create a test user for testing the contract search endpoint.
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import get_db, init_db
from app.models.user import User
from app.core.auth import get_password_hash
from app.models.organization import Organization

async def create_test_user():
    """Create a test user for testing"""
    
    try:
        # Initialize database
        await init_db()
        
        # Get database session
        db = next(get_db())
        
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@supplero.com").first()
        
        if existing_user:
            print("✅ Test user already exists")
            return existing_user
        
        # Create organization if it doesn't exist
        org = db.query(Organization).filter(Organization.id == 1).first()
        if not org:
            org = Organization(
                id=1,
                name="Test Organization",
                domain="test.com"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
        
        # Create test user
        test_user = User(
            email="test@supplero.com",
            username="testuser2",
            hashed_password=get_password_hash("test123"),
            role="admin",
            organization_id=1,
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ Test user created successfully")
        print(f"   Email: {test_user.email}")
        print(f"   Password: test123")
        print(f"   Role: {test_user.role}")
        print(f"   Organization ID: {test_user.organization_id}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        return None

if __name__ == "__main__":
    print("👤 Creating Test User for Contract Search Testing")
    print("=" * 50)
    
    asyncio.run(create_test_user())
