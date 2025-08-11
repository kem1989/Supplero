"""
Authentication API endpoints for user registration and login.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.core.auth import (
    authenticate_user, get_password_hash, create_access_token, 
    create_refresh_token, get_current_active_user, verify_token
)
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_current_trace_context
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(
                "Registration failed - email already exists",
                email=user_data.email,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            logger.warning(
                "Registration failed - username already taken",
                username=user_data.username,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Check if organization exists
        organization = db.query(Organization).filter(Organization.id == user_data.organization_id).first()
        if not organization:
            logger.warning(
                "Registration failed - organization not found",
                organization_id=user_data.organization_id,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            organization_id=user_data.organization_id
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(
            "User registered successfully", 
            email=db_user.email,
            organization_id=db_user.organization_id,
            **trace_context
        )
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to register user", 
            error=str(e),
            email=user_data.email,
            username=user_data.username,
            **trace_context,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Authenticate user
        user = authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            logger.warning(
                "Login failed - invalid credentials",
                email=user_credentials.email,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(
                "Login failed - inactive user",
                email=user.email,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Update last login
        user.last_login = func.now()
        db.commit()
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "organization_id": user.organization_id
            },
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "organization_id": user.organization_id
            }
        )
        
        logger.info(
            "User logged in successfully", 
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            **trace_context
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to login user", 
            error=str(e),
            email=user_credentials.email,
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    logger.debug(
        "User info requested",
        email=current_user.email,
        **trace_context
    )
    
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(token_request: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Verify refresh token
        token_data = verify_token(token_request.refresh_token)
        
        # Get user
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user or not user.is_active:
            logger.warning(
                "Token refresh failed - invalid refresh token",
                user_id=token_data.user_id if hasattr(token_data, 'user_id') else 'unknown',
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "organization_id": user.organization_id
            },
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = create_refresh_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "organization_id": user.organization_id
            }
        )
        
        logger.info(
            "Access token refreshed successfully",
            user_id=user.id,
            email=user.email,
            **trace_context
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to refresh token", 
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 