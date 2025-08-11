"""
Configuration management for the Supplero application.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Supplero"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Allowed hosts and origins
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # Database
    POSTGRES_DB: str = "supplero"
    POSTGRES_USER: str = "supplero"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_VISION_MODEL: str = "gpt-4-vision-preview"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.1
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # File Storage
    STORAGE_TYPE: str = "local"  # local, s3, azure, gcp
    STORAGE_PATH: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "image/jpeg",
        "image/png",
        "image/tiff"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None
    DATADOG_API_KEY: Optional[str] = None
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@supplero.com"
    
    # External APIs
    DUN_BRADSTREET_API_KEY: Optional[str] = None
    REFINITIV_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # AI Processing
    MAX_CONCURRENT_AI_REQUESTS: int = 10
    AI_REQUEST_TIMEOUT: int = 300  # 5 minutes
    
    # Audit & Retention Policies
    AUDIT_RETENTION_DAYS: int = 2555  # 7 years for compliance
    AUDIT_ARCHIVE_DAYS: int = 365  # Archive after 1 year
    AUDIT_MAX_LOG_SIZE_MB: int = 100  # Max size for individual audit logs
    AUDIT_COMPRESSION_ENABLED: bool = True  # Enable compression for archived logs
    AUDIT_ENCRYPTION_ENABLED: bool = True  # Enable encryption for archived logs
    
    # Audit Access Controls
    AUDIT_ADMIN_ROLES: List[str] = ["admin", "auditor", "compliance_officer"]
    AUDIT_VIEWER_ROLES: List[str] = ["manager", "viewer"]
    AUDIT_EXPORT_ROLES: List[str] = ["admin", "auditor", "compliance_officer"]
    AUDIT_DELETE_ROLES: List[str] = ["admin"]  # Only admins can delete audit data
    
    # Audit Storage
    AUDIT_STORAGE_TYPE: str = "database"  # database, file, s3, elasticsearch
    AUDIT_ARCHIVE_STORAGE: str = "file"  # file, s3, elasticsearch
    AUDIT_ARCHIVE_PATH: str = "./uploads/audit/archive"
    AUDIT_BACKUP_ENABLED: bool = True
    AUDIT_BACKUP_RETENTION_DAYS: int = 3650  # 10 years for backups
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Override settings for testing if needed
if os.getenv("TESTING"):
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = True
    settings.DATABASE_URL = "sqlite:///./test.db" 