#!/usr/bin/env python3
"""
Test script for structured logging implementation.
Run this to verify that all logging features are working correctly.
"""

import os
import sys
import time
import uuid

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.logging import (
    setup_logging, 
    get_logger, 
    generate_trace_id, 
    set_request_context, 
    clear_request_context,
    log_database_operation,
    log_integration_call,
    log_security_event
)
from app.core.config import settings


def test_basic_logging():
    """Test basic structured logging functionality."""
    print("🧪 Testing basic structured logging...")
    
    # Setup logging
    setup_logging()
    logger = get_logger("test_logging")
    
    # Test basic log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✅ Basic logging test completed")


def test_request_context():
    """Test request context and trace IDs functionality."""
    print("🧪 Testing request context and trace IDs...")
    
    logger = get_logger("test_request_context")
    
    # Generate trace ID
    trace_id = generate_trace_id()
    print(f"Generated trace ID: {trace_id}")
    
    # Set request context
    set_request_context(request_id=trace_id, user_id="test_user_123")
    
    # Log with context
    logger.info("Request processing started")
    logger.info("Processing user data")
    logger.info("Request completed")
    
    # Clear context
    clear_request_context()
    
    # Log without context
    logger.info("Context cleared, this log should not have request_id")
    
    print("✅ Request context test completed")


def test_specialized_logging():
    """Test specialized logging functions."""
    print("🧪 Testing specialized logging functions...")
    
    logger = get_logger("test_specialized")
    
    # Test database operation logging
    log_database_operation(
        operation="INSERT",
        table="users",
        record_id="user_456",
        user_id="admin_123",
        data_size=1024
    )
    
    # Test integration call logging
    log_integration_call(
        integration_name="OpenAI API",
        endpoint="/v1/chat/completions",
        status_code=200,
        response_time=1.25,
        user_id="user_789",
        tokens_used=150
    )
    
    # Test security event logging
    log_security_event(
        event_type="login_attempt",
        severity="info",
        user_id="user_123",
        ip_address="192.168.1.100",
        success=True,
        user_agent="Mozilla/5.0..."
    )
    
    print("✅ Specialized logging test completed")


def test_performance_logging():
    """Test performance-related logging."""
    print("🧪 Testing performance logging...")
    
    logger = get_logger("test_performance")
    
    # Simulate a slow operation
    start_time = time.time()
    time.sleep(0.1)  # Simulate 100ms operation
    process_time = time.time() - start_time
    
    logger.info(
        "Operation completed",
        operation="data_processing",
        process_time=process_time,
        records_processed=1000,
        memory_usage="256MB"
    )
    
    print("✅ Performance logging test completed")


def test_error_logging():
    """Test error logging with stack traces."""
    print("🧪 Testing error logging...")
    
    logger = get_logger("test_error")
    
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.error(
            "Division by zero error",
            operation="calculation",
            dividend=1,
            divisor=0,
            exc_info=True
        )
    
    print("✅ Error logging test completed")


def main():
    """Run all logging tests."""
    print("🚀 Starting structured logging tests...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Log level: {settings.LOG_LEVEL}")
    print("=" * 50)
    
    try:
        test_basic_logging()
        print()
        
        test_request_context()
        print()
        
        test_specialized_logging()
        print()
        
        test_performance_logging()
        print()
        
        test_error_logging()
        print()
        
        print("🎉 All tests completed successfully!")
        print("\n📝 Check the console output above to see structured JSON logs.")
        print("Each log entry should include:")
        print("  - timestamp")
        print("  - log level")
        print("  - logger name")
        print("  - service and environment")
        print("  - request_id and user_id (when context is set)")
        print("  - structured data fields")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 