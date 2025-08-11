"""
Authentication and authorization utilities for the Supplero application.
Enhanced for structured logging and audit trail.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.core.logging import get_logger

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Logger
logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning("Authentication failed - user not found", email=email)
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed - invalid password", email=email)
            return None
        
        logger.info("User authenticated successfully", user_id=user.id, email=email)
        return user
        
    except Exception as e:
        logger.error("Authentication error", email=email, error=str(e), exc_info=True)
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    logger.info("Access token created", user_id=data.get("user_id"), expires_at=expire.isoformat())
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    logger.info("Refresh token created", user_id=data.get("user_id"), expires_at=expire.isoformat())
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        # Check if token has required fields
        if not payload.get("user_id") or not payload.get("email"):
            return None
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        
        # Log successful authentication
        logger.info("User authenticated successfully", user_id=user.id, email=user.email)
        return user
        
    except JWTError as e:
        logger.warning("JWT token validation failed", error=str(e))
        raise credentials_exception


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user if available, otherwise return None."""
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return None
        
        # Log successful authentication
        logger.info("User authenticated successfully (optional)", user_id=user.id, email=user.email)
        return user
        
    except JWTError as e:
        logger.debug("JWT token validation failed (optional)", error=str(e))
        return None
    except Exception as e:
        logger.debug("Authentication error (optional)", error=str(e))
        return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        logger.warning("Inactive user attempted access", user_id=current_user.id)
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def extract_user_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token for logging purposes."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return str(payload.get("user_id"))
    except JWTError:
        return None


def log_authentication_event(
    event_type: str,
    username: str = None,
    user_id: int = None,
    ip_address: str = None,
    success: bool = True,
    **kwargs
):
    """Log authentication-related events for audit trail."""
    log_data = {
        "event_type": event_type,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if username:
        log_data["username"] = username
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    
    log_data.update(kwargs)
    
    if success:
        logger.info("Authentication event", **log_data)
    else:
        logger.warning("Authentication event", **log_data)


def log_authorization_event(
    event_type: str,
    user_id: int,
    resource: str,
    action: str,
    allowed: bool,
    **kwargs
):
    """Log authorization events for audit trail."""
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "allowed": allowed,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    log_data.update(kwargs)
    
    if allowed:
        logger.info("Authorization event", **log_data)
    else:
        logger.warning("Authorization denied", **log_data) 