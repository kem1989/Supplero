"""
Database configuration and session management for the Supplero application.
Enhanced with structured logging for observability.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import time
from typing import Generator

from app.core.config import settings
from app.core.logging import get_logger, log_database_operation

# Logger
logger = get_logger(__name__)

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,  # SQL logging in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as a context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables."""
    try:
        logger.info("Initializing database")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e), exc_info=True)
        raise


def check_db_health() -> bool:
    """Check if database is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e), exc_info=True)
        return False


# Database event listeners for logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connection events."""
    logger.info("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout events."""
    logger.debug("Database connection checked out")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin events."""
    logger.debug("Database connection checked in")


# SQL query logging for performance monitoring
if settings.DEBUG:
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log SQL queries before execution."""
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug(
            "SQL query starting",
            statement=statement[:200] + "..." if len(statement) > 200 else statement,
            parameters=str(parameters)[:200] if parameters else None
        )

    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log SQL queries after execution."""
        total = time.time() - conn.info['query_start_time'].pop()
        logger.debug(
            "SQL query completed",
            execution_time=total,
            row_count=cursor.rowcount if cursor.rowcount is not None else 0
        )


def log_db_operation(operation: str, table: str, record_id: str = None, user_id: str = None, **kwargs):
    """Log database operations for audit trail."""
    log_database_operation(
        operation=operation,
        table=table,
        record_id=record_id,
        user_id=user_id,
        **kwargs
    )


class DatabaseSession:
    """Database session wrapper with logging capabilities."""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                logger.error(
                    "Database session error",
                    error_type=exc_type.__name__,
                    error=str(exc_val),
                    exc_info=True
                )
            self.session.close()
    
    def commit(self):
        """Commit the session with logging."""
        if self.session:
            try:
                self.session.commit()
                logger.debug("Database transaction committed")
            except Exception as e:
                logger.error("Database commit failed", error=str(e), exc_info=True)
                raise
    
    def rollback(self):
        """Rollback the session with logging."""
        if self.session:
            try:
                self.session.rollback()
                logger.debug("Database transaction rolled back")
            except Exception as e:
                logger.error("Database rollback failed", error=str(e), exc_info=True)
                raise 