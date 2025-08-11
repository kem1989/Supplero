"""
Audit management script for administrative tasks.
Provides command-line tools for managing audit retention, cleanup, and maintenance.
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from typing import Optional

from app.core.audit_retention import get_audit_retention_service
from app.core.audit_access_control import get_audit_access_control
from app.core.audit_sink import get_centralized_audit_sink
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditManager:
    """Command-line audit management tool."""
    
    def __init__(self):
        self.retention_service = get_audit_retention_service()
        self.access_control = get_audit_access_control()
        self.audit_sink = get_centralized_audit_sink()
    
    async def show_retention_stats(self, organization_id: Optional[int] = None):
        """Display retention policy statistics."""
        try:
            stats = self.retention_service.get_retention_stats(organization_id)
            
            print("\n=== Audit Retention Statistics ===")
            print(f"Organization ID: {organization_id or 'All'}")
            print(f"Generated at: {stats.get('generated_at', 'N/A')}")
            
            print("\n--- Current Data ---")
            current_data = stats.get('current_data', {})
            print(f"Audit Logs: {current_data.get('audit_logs', 0):,}")
            print(f"AI Requests: {current_data.get('ai_requests', 0):,}")
            print(f"Total: {current_data.get('total', 0):,}")
            
            print("\n--- Data Age ---")
            data_age = stats.get('data_age', {})
            for data_type, age_info in data_age.items():
                oldest = age_info.get('oldest', 'N/A')
                newest = age_info.get('newest', 'N/A')
                print(f"{data_type.replace('_', ' ').title()}:")
                print(f"  Oldest: {oldest}")
                print(f"  Newest: {newest}")
            
            print("\n--- Archive Information ---")
            archive_info = stats.get('archive_info', {})
            print(f"Audit Logs Archive: {archive_info.get('audit_logs_size_mb', 0):.2f} MB")
            print(f"AI Requests Archive: {archive_info.get('ai_requests_size_mb', 0):.2f} MB")
            print(f"Total Archive Size: {archive_info.get('total_size_mb', 0):.2f} MB")
            
            print("\n--- Retention Policies ---")
            policies = stats.get('retention_policies', {})
            print(f"Retention Days: {policies.get('retention_days', 'N/A')}")
            print(f"Archive Days: {policies.get('archive_days', 'N/A')}")
            print(f"Compression: {'Enabled' if policies.get('compression_enabled') else 'Disabled'}")
            print(f"Encryption: {'Enabled' if policies.get('encryption_enabled') else 'Disabled'}")
            
            print("\n--- Next Cleanup ---")
            next_cleanup = stats.get('next_cleanup', {})
            retention_cutoff = next_cleanup.get('retention_cutoff', 'N/A')
            archive_cutoff = next_cleanup.get('archive_cutoff', 'N/A')
            print(f"Retention Cutoff: {retention_cutoff}")
            print(f"Archive Cutoff: {archive_cutoff}")
            
        except Exception as e:
            logger.error(f"Failed to show retention stats: {e}")
            print(f"Error: {e}")
    
    async def run_cleanup(self, organization_id: Optional[int] = None, dry_run: bool = False):
        """Run retention cleanup."""
        try:
            if dry_run:
                print(f"\n=== DRY RUN: Retention Cleanup ===")
                print(f"Organization ID: {organization_id or 'All'}")
                print("This would perform the following actions:")
                print("1. Archive old audit data")
                print("2. Delete expired audit data")
                print("3. Clean up old archives")
                print("\nNo actual changes would be made.")
                return
            
            print(f"\n=== Running Retention Cleanup ===")
            print(f"Organization ID: {organization_id or 'All'}")
            print("Starting cleanup process...")
            
            cleanup_stats = self.retention_service.cleanup_expired_audit_data(organization_id)
            
            print("\n--- Cleanup Results ---")
            print(f"Audit Logs Deleted: {cleanup_stats.get('audit_logs_deleted', 0):,}")
            print(f"AI Requests Deleted: {cleanup_stats.get('ai_requests_deleted', 0):,}")
            print(f"Archives Created: {cleanup_stats.get('archives_created', 0):,}")
            print(f"Errors: {cleanup_stats.get('errors', 0):,}")
            
            if cleanup_stats.get('errors', 0) > 0:
                print("\n⚠️  Some errors occurred during cleanup. Check logs for details.")
            else:
                print("\n✅ Cleanup completed successfully!")
                
        except Exception as e:
            logger.error(f"Failed to run cleanup: {e}")
            print(f"Error: {e}")
    
    async def show_system_health(self):
        """Display audit system health information."""
        try:
            health = self.audit_sink.get_system_health()
            
            print("\n=== Audit System Health ===")
            print(f"Status: {health.get('status', 'Unknown')}")
            print(f"Service: {health.get('service', 'Unknown')}")
            print(f"Timestamp: {health.get('timestamp', 'N/A')}")
            
            if health.get('status') == 'healthy':
                print("\n--- Component Status ---")
                components = health.get('components', {})
                for component, status in components.items():
                    status_icon = "✅" if status == "operational" else "❌"
                    print(f"{component}: {status_icon} {status}")
                
                print("\n--- Buffer Status ---")
                buffer_status = health.get('buffer_status', {})
                print(f"Current Size: {buffer_status.get('current_size', 0)}")
                print(f"Max Size: {buffer_status.get('max_size', 0)}")
                print(f"Flush Timeout: {buffer_status.get('flush_timeout', 0)} seconds")
                
                print("\n--- Features ---")
                features = health.get('features', [])
                for feature in features:
                    print(f"  • {feature}")
            else:
                print(f"\n❌ System is unhealthy: {health.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to show system health: {e}")
            print(f"Error: {e}")
    
    async def show_access_control_info(self):
        """Display access control information."""
        try:
            print("\n=== Audit Access Control Information ===")
            
            # Show role permissions
            print("\n--- Role Permissions ---")
            role_permissions = self.access_control.role_permissions
            for role, permissions in role_permissions.items():
                print(f"\n{role.title()}:")
                for permission in sorted(permissions, key=lambda x: x.value):
                    print(f"  • {permission.value}")
            
            # Show access levels
            print("\n--- Access Levels ---")
            role_access_levels = self.access_control.role_access_levels
            for role, access_level in role_access_levels.items():
                print(f"{role.title()}: {access_level.value}")
                
        except Exception as e:
            logger.error(f"Failed to show access control info: {e}")
            print(f"Error: {e}")


async def main():
    """Main entry point for the audit management script."""
    parser = argparse.ArgumentParser(description="Audit Management Tool")
    parser.add_argument("--organization-id", type=int, help="Organization ID to operate on")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Retention stats command
    stats_parser = subparsers.add_parser("stats", help="Show retention statistics")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Run retention cleanup")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Show system health")
    
    # Access control command
    access_parser = subparsers.add_parser("access", help="Show access control information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = AuditManager()
        
        if args.command == "stats":
            await manager.show_retention_stats(args.organization_id)
        elif args.command == "cleanup":
            await manager.run_cleanup(args.organization_id, args.dry_run)
        elif args.command == "health":
            await manager.show_system_health()
        elif args.command == "access":
            await manager.show_access_control_info()
        else:
            print(f"Unknown command: {args.command}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
