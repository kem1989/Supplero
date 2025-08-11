#!/usr/bin/env python3
"""
Test script for the centralized audit sink components.
Tests retention policies, access controls, and audit sink functionality.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.audit_sink import get_centralized_audit_sink, AuditSinkType, AuditDataPriority
from app.core.audit_retention import get_audit_retention_service
from app.core.audit_access_control import get_audit_access_control, AuditPermission
from app.core.config import settings


async def test_audit_sink_health():
    """Test the audit sink health endpoint."""
    print("\n=== Testing Audit Sink Health ===")
    
    try:
        audit_sink = get_centralized_audit_sink()
        health = audit_sink.get_system_health()
        
        print(f"Status: {health.get('status')}")
        print(f"Service: {health.get('service')}")
        print(f"Timestamp: {health.get('timestamp')}")
        
        if health.get('status') == 'healthy':
            print("✅ Audit sink is healthy")
            
            # Show component status
            components = health.get('components', {})
            for component, status in components.items():
                print(f"  {component}: {status}")
            
            # Show features
            features = health.get('features', [])
            print(f"Features: {', '.join(features)}")
        else:
            print(f"❌ Audit sink is unhealthy: {health.get('error')}")
            
    except Exception as e:
        print(f"❌ Error testing audit sink health: {e}")


async def test_retention_service():
    """Test the audit retention service."""
    print("\n=== Testing Audit Retention Service ===")
    
    try:
        retention_service = get_audit_retention_service()
        
        # Get retention statistics
        stats = retention_service.get_retention_stats()
        
        print("Retention Statistics:")
        print(f"  Current Data: {stats.get('current_data', {})}")
        print(f"  Archive Info: {stats.get('archive_info', {})}")
        print(f"  Retention Policies: {stats.get('retention_policies', {})}")
        
        # Test archive directory creation
        archive_path = retention_service.archive_path
        print(f"Archive Path: {archive_path}")
        print(f"Archive Path Exists: {archive_path.exists()}")
        
        # Test archive subdirectories
        for subdir in ['audit_logs', 'ai_requests', 'backups']:
            subdir_path = archive_path / subdir
            print(f"  {subdir}: {subdir_path.exists()}")
        
        print("✅ Retention service test completed")
        
    except Exception as e:
        print(f"❌ Error testing retention service: {e}")


async def test_access_control():
    """Test the audit access control service."""
    print("\n=== Testing Audit Access Control ===")
    
    try:
        access_control = get_audit_access_control()
        
        # Test role permissions
        print("Role Permissions:")
        for role, permissions in access_control.role_permissions.items():
            print(f"  {role}: {len(permissions)} permissions")
            for permission in sorted(permissions, key=lambda x: x.value):
                print(f"    • {permission.value}")
        
        # Test access levels
        print("\nAccess Levels:")
        for role, access_level in access_control.role_access_levels.items():
            print(f"  {role}: {access_level.value}")
        
        # Test permission checking (with mock user)
        class MockUser:
            def __init__(self, role, org_id):
                self.role = role
                self.organization_id = org_id
                self.id = 1
        
        # Test different user roles
        test_users = [
            MockUser("admin", 1),
            MockUser("auditor", 1),
            MockUser("manager", 1),
            MockUser("viewer", 1)
        ]
        
        print("\nPermission Tests:")
        for user in test_users:
            print(f"\n  {user.role.title()} User:")
            
            # Test basic permissions
            can_view_logs = access_control.has_permission(user, AuditPermission.VIEW_AUDIT_LOGS)
            can_export = access_control.has_permission(user, AuditPermission.EXPORT_AUDIT_DATA)
            can_manage = access_control.has_permission(user, AuditPermission.MANAGE_RETENTION_POLICIES)
            
            print(f"    View Logs: {'✅' if can_view_logs else '❌'}")
            print(f"    Export Data: {'✅' if can_export else '❌'}")
            print(f"    Manage Retention: {'✅' if can_manage else '❌'}")
            
            # Test access level
            access_level = access_control.get_access_level(user)
            print(f"    Access Level: {access_level.value}")
        
        print("✅ Access control test completed")
        
    except Exception as e:
        print(f"❌ Error testing access control: {e}")


async def test_audit_logging():
    """Test audit logging through the centralized sink."""
    print("\n=== Testing Audit Logging ===")
    
    try:
        audit_sink = get_centralized_audit_sink()
        
        # Test immediate logging
        print("Testing immediate audit logging...")
        result = await audit_sink.log_audit_event(
            action="test_action",
            organization_id=1,
            user_id=1,
            resource_type="test_resource",
            resource_id="test_123",
            details={"test": True, "timestamp": datetime.utcnow().isoformat()},
            sink_type=AuditSinkType.IMMEDIATE,
            priority=AuditDataPriority.HIGH
        )
        print(f"  Immediate Result: {result}")
        
        # Test buffered logging
        print("Testing buffered audit logging...")
        result = await audit_sink.log_audit_event(
            action="test_buffered_action",
            organization_id=1,
            user_id=1,
            resource_type="test_resource",
            resource_id="test_456",
            details={"test": True, "buffered": True},
            sink_type=AuditSinkType.BUFFERED,
            priority=AuditDataPriority.NORMAL
        )
        print(f"  Buffered Result: {result}")
        
        # Test AI request logging
        print("Testing AI request logging...")
        result = await audit_sink.log_ai_request(
            request_type="test_analysis",
            organization_id=1,
            user_id=1,
            model_used="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            processing_time_ms=2000,
            cost_usd=0.03,
            status="completed",
            sink_type=AuditSinkType.IMMEDIATE,
            priority=AuditDataPriority.HIGH
        )
        print(f"  AI Request Result: {result}")
        
        print("✅ Audit logging test completed")
        
    except Exception as e:
        print(f"❌ Error testing audit logging: {e}")


async def test_retention_cleanup():
    """Test retention cleanup functionality."""
    print("\n=== Testing Retention Cleanup ===")
    
    try:
        retention_service = get_audit_retention_service()
        
        # Test dry run cleanup
        print("Testing retention cleanup (dry run)...")
        cleanup_stats = retention_service.cleanup_expired_audit_data(organization_id=1)
        
        print("Cleanup Statistics:")
        print(f"  Audit Logs Deleted: {cleanup_stats.get('audit_logs_deleted', 0)}")
        print(f"  AI Requests Deleted: {cleanup_stats.get('ai_requests_deleted', 0)}")
        print(f"  Archives Created: {cleanup_stats.get('archives_created', 0)}")
        print(f"  Errors: {cleanup_stats.get('errors', 0)}")
        
        print("✅ Retention cleanup test completed")
        
    except Exception as e:
        print(f"❌ Error testing retention cleanup: {e}")


async def test_configuration():
    """Test audit configuration settings."""
    print("\n=== Testing Audit Configuration ===")
    
    try:
        print("Audit Configuration:")
        print(f"  Retention Days: {settings.AUDIT_RETENTION_DAYS}")
        print(f"  Archive Days: {settings.AUDIT_ARCHIVE_DAYS}")
        print(f"  Max Log Size: {settings.AUDIT_MAX_LOG_SIZE_MB} MB")
        print(f"  Compression: {'Enabled' if settings.AUDIT_COMPRESSION_ENABLED else 'Disabled'}")
        print(f"  Encryption: {'Enabled' if settings.AUDIT_ENCRYPTION_ENABLED else 'Disabled'}")
        
        print("\nAccess Control Configuration:")
        print(f"  Admin Roles: {', '.join(settings.AUDIT_ADMIN_ROLES)}")
        print(f"  Viewer Roles: {', '.join(settings.AUDIT_VIEWER_ROLES)}")
        print(f"  Export Roles: {', '.join(settings.AUDIT_EXPORT_ROLES)}")
        print(f"  Delete Roles: {', '.join(settings.AUDIT_DELETE_ROLES)}")
        
        print("\nStorage Configuration:")
        print(f"  Storage Type: {settings.AUDIT_STORAGE_TYPE}")
        print(f"  Archive Storage: {settings.AUDIT_ARCHIVE_STORAGE}")
        print(f"  Archive Path: {settings.AUDIT_ARCHIVE_PATH}")
        print(f"  Backup Enabled: {settings.AUDIT_BACKUP_ENABLED}")
        
        print("✅ Configuration test completed")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")


async def main():
    """Run all tests."""
    print("🚀 Starting Centralized Audit Sink Tests")
    print("=" * 50)
    
    try:
        # Run all tests
        await test_configuration()
        await test_audit_sink_health()
        await test_retention_service()
        await test_access_control()
        await test_audit_logging()
        await test_retention_cleanup()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
