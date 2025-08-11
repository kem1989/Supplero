"""
Database initialization script for Supplero application.
"""

from sqlalchemy.orm import Session
import structlog

from app.core.database import engine, SessionLocal
from app.models import Base, User, Organization
from app.core.auth import get_password_hash
from app.models.user import UserRole

logger = structlog.get_logger(__name__)


def init_db():
    """Initialize the database with tables and initial data."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create initial data
        create_initial_data()
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def create_initial_data():
    """Create initial organizations and admin user."""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Organization).first():
            logger.info("Initial data already exists, skipping creation")
            return
        
        # Create default organization
        default_org = Organization(
            name="Supplero Default Organization",
            domain="supplero.local",
            industry="Technology",
            size="medium",
            contact_email="admin@supplero.local",
            is_active=True
        )
        db.add(default_org)
        db.commit()
        db.refresh(default_org)
        
        # Create admin user
        admin_user = User(
            email="admin@supplero.local",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            organization_id=default_org.id
        )
        db.add(admin_user)
        db.commit()
        
        logger.info("Initial data created successfully", 
                   org_id=default_org.id, 
                   admin_user_id=admin_user.id)
        
    except Exception as e:
        logger.error("Failed to create initial data", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db() 