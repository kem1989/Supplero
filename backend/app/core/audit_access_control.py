"""
Audit access control service for implementing role-based access policies.
Provides granular control over who can access what audit data.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.organization import Organization

logger = get_logger(__name__)


class AuditPermission(Enum):
    """Audit permissions that can be granted to users."""
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_AI_REQUESTS = "view_ai_requests"
    VIEW_AUDIT_SUMMARY = "view_audit_summary"
    EXPORT_AUDIT_DATA = "export_audit_data"
    VIEW_RETENTION_STATS = "view_retention_stats"
    MANAGE_RETENTION_POLICIES = "manage_retention_policies"
    DELETE_AUDIT_DATA = "delete_audit_data"
    VIEW_ARCHIVED_DATA = "view_archived_data"
    RESTORE_ARCHIVED_DATA = "restore_archived_data"


class AuditAccessLevel(Enum):
    """Access levels for audit data."""
    OWN_ACTIONS_ONLY = "own_actions_only"  # User can only see their own actions
    ORGANIZATION_WIDE = "organization_wide"  # User can see all actions in their organization
    CROSS_ORGANIZATION = "cross_organization"  # User can see actions across organizations (admin only)
    SYSTEM_WIDE = "system_wide"  # User can see all system actions (super admin only)


class AuditAccessControl:
    """Service for managing audit access control policies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Define role-based permissions
        self.role_permissions = {
            "admin": {
                AuditPermission.VIEW_AUDIT_LOGS,
                AuditPermission.VIEW_AI_REQUESTS,
                AuditPermission.VIEW_AUDIT_SUMMARY,
                AuditPermission.EXPORT_AUDIT_DATA,
                AuditPermission.VIEW_RETENTION_STATS,
                AuditPermission.MANAGE_RETENTION_POLICIES,
                AuditPermission.DELETE_AUDIT_DATA,
                AuditPermission.VIEW_ARCHIVED_DATA,
                AuditPermission.RESTORE_ARCHIVED_DATA
            },
            "auditor": {
                AuditPermission.VIEW_AUDIT_LOGS,
                AuditPermission.VIEW_AI_REQUESTS,
                AuditPermission.VIEW_AUDIT_SUMMARY,
                AuditPermission.EXPORT_AUDIT_DATA,
                AuditPermission.VIEW_RETENTION_STATS,
                AuditPermission.VIEW_ARCHIVED_DATA
            },
            "compliance_officer": {
                AuditPermission.VIEW_AUDIT_LOGS,
                AuditPermission.VIEW_AI_REQUESTS,
                AuditPermission.VIEW_AUDIT_SUMMARY,
                AuditPermission.EXPORT_AUDIT_DATA,
                AuditPermission.VIEW_RETENTION_STATS,
                AuditPermission.VIEW_ARCHIVED_DATA
            },
            "manager": {
                AuditPermission.VIEW_AUDIT_LOGS,
                AuditPermission.VIEW_AI_REQUESTS,
                AuditPermission.VIEW_AUDIT_SUMMARY,
                AuditPermission.EXPORT_AUDIT_DATA
            },
            "viewer": {
                AuditPermission.VIEW_AUDIT_LOGS,
                AuditPermission.VIEW_AUDIT_SUMMARY
            }
        }
        
        # Define access levels for different roles
        self.role_access_levels = {
            "admin": AuditAccessLevel.ORGANIZATION_WIDE,
            "auditor": AuditAccessLevel.ORGANIZATION_WIDE,
            "compliance_officer": AuditAccessLevel.ORGANIZATION_WIDE,
            "manager": AuditAccessLevel.ORGANIZATION_WIDE,
            "viewer": AuditAccessLevel.OWN_ACTIONS_ONLY
        }
    
    def has_permission(self, user: User, permission: AuditPermission) -> bool:
        """
        Check if a user has a specific audit permission.
        
        Args:
            user: User to check permissions for
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            if not user or not user.role:
                return False
            
            user_role = user.role.lower()
            user_permissions = self.role_permissions.get(user_role, set())
            
            has_perm = permission in user_permissions
            
            self.logger.debug(
                "Permission check",
                user_id=str(user.id),
                user_role=user_role,
                permission=permission.value,
                has_permission=has_perm
            )
            
            return has_perm
            
        except Exception as e:
            self.logger.error(
                "Error checking permission",
                user_id=str(user.id) if user else None,
                permission=permission.value,
                error=str(e),
                exc_info=True
            )
            return False
    
    def get_user_permissions(self, user: User) -> Set[AuditPermission]:
        """
        Get all permissions for a user.
        
        Args:
            user: User to get permissions for
            
        Returns:
            Set of permissions the user has
        """
        try:
            if not user or not user.role:
                return set()
            
            user_role = user.role.lower()
            return self.role_permissions.get(user_role, set())
            
        except Exception as e:
            self.logger.error(
                "Error getting user permissions",
                user_id=str(user.id) if user else None,
                error=str(e),
                exc_info=True
            )
            return set()
    
    def get_access_level(self, user: User) -> AuditAccessLevel:
        """
        Get the audit access level for a user.
        
        Args:
            user: User to get access level for
            
        Returns:
            Access level for the user
        """
        try:
            if not user or not user.role:
                return AuditAccessLevel.OWN_ACTIONS_ONLY
            
            user_role = user.role.lower()
            return self.role_access_levels.get(user_role, AuditAccessLevel.OWN_ACTIONS_ONLY)
            
        except Exception as e:
            self.logger.error(
                "Error getting user access level",
                user_id=str(user.id) if user else None,
                error=str(e),
                exc_info=True
            )
            return AuditAccessLevel.OWN_ACTIONS_ONLY
    
    def can_access_organization_data(self, user: User, target_organization_id: int) -> bool:
        """
        Check if a user can access data from a specific organization.
        
        Args:
            user: User requesting access
            target_organization_id: Organization ID to access
            
        Returns:
            True if user can access the organization's data
        """
        try:
            if not user:
                return False
            
            # Super admins can access all organizations
            if user.role and user.role.lower() == "super_admin":
                return True
            
            # Users can only access their own organization
            if user.organization_id == target_organization_id:
                return True
            
            # Cross-organization access is restricted
            return False
            
        except Exception as e:
            self.logger.error(
                "Error checking organization access",
                user_id=str(user.id) if user else None,
                target_organization_id=str(target_organization_id),
                error=str(e),
                exc_info=True
            )
            return False
    
    def can_access_user_data(self, user: User, target_user_id: int) -> bool:
        """
        Check if a user can access data from a specific user.
        
        Args:
            user: User requesting access
            target_user_id: User ID to access
            
        Returns:
            True if user can access the target user's data
        """
        try:
            if not user:
                return False
            
            # Users can always access their own data
            if user.id == target_user_id:
                return True
            
            # Check access level
            access_level = self.get_access_level(user)
            
            if access_level == AuditAccessLevel.OWN_ACTIONS_ONLY:
                return False
            
            if access_level == AuditAccessLevel.ORGANIZATION_WIDE:
                # Need to check if target user is in same organization
                # This would require a database query in practice
                return True  # Simplified for now
            
            if access_level == AuditAccessLevel.CROSS_ORGANIZATION:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Error checking user data access",
                user_id=str(user.id) if user else None,
                target_user_id=str(target_user_id),
                error=str(e),
                exc_info=True
            )
            return False
    
    def validate_audit_query(self, user: User, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize audit query parameters based on user permissions.
        
        Args:
            user: User making the query
            query_params: Original query parameters
            
        Returns:
            Sanitized query parameters
        """
        try:
            sanitized_params = query_params.copy()
            
            # Check if user can access cross-organization data
            if not self.can_access_organization_data(user, user.organization_id):
                # Force organization filter to user's organization
                sanitized_params['organization_id'] = user.organization_id
            
            # Check if user can only see their own actions
            access_level = self.get_access_level(user)
            if access_level == AuditAccessLevel.OWN_ACTIONS_ONLY:
                sanitized_params['user_id'] = user.id
            
            # Remove sensitive parameters if user doesn't have permission
            if not self.has_permission(user, AuditPermission.VIEW_RETENTION_STATS):
                if 'include_retention_stats' in sanitized_params:
                    del sanitized_params['include_retention_stats']
            
            if not self.has_permission(user, AuditPermission.EXPORT_AUDIT_DATA):
                if 'export_format' in sanitized_params:
                    del sanitized_params['export_format']
            
            self.logger.debug(
                "Audit query validation",
                user_id=str(user.id),
                original_params=query_params,
                sanitized_params=sanitized_params
            )
            
            return sanitized_params
            
        except Exception as e:
            self.logger.error(
                "Error validating audit query",
                user_id=str(user.id) if user else None,
                query_params=query_params,
                error=str(e),
                exc_info=True
            )
            return query_params
    
    def get_audit_access_summary(self, user: User) -> Dict[str, Any]:
        """
        Get a summary of the user's audit access capabilities.
        
        Args:
            user: User to get access summary for
            
        Returns:
            Dictionary with access summary
        """
        try:
            if not user:
                return {
                    'has_access': False,
                    'permissions': [],
                    'access_level': 'none',
                    'restrictions': ['User not authenticated']
                }
            
            permissions = self.get_user_permissions(user)
            access_level = self.get_access_level(user)
            
            # Determine restrictions
            restrictions = []
            if access_level == AuditAccessLevel.OWN_ACTIONS_ONLY:
                restrictions.append("Can only view own actions")
            if not self.has_permission(user, AuditPermission.EXPORT_AUDIT_DATA):
                restrictions.append("Cannot export audit data")
            if not self.has_permission(user, AuditPermission.VIEW_RETENTION_STATS):
                restrictions.append("Cannot view retention statistics")
            
            return {
                'has_access': len(permissions) > 0,
                'permissions': [perm.value for perm in permissions],
                'access_level': access_level.value,
                'organization_id': user.organization_id,
                'restrictions': restrictions,
                'can_access_own_data': True,
                'can_access_organization_data': access_level != AuditAccessLevel.OWN_ACTIONS_ONLY,
                'can_access_cross_organization': access_level in [
                    AuditAccessLevel.CROSS_ORGANIZATION,
                    AuditAccessLevel.SYSTEM_WIDE
                ]
            }
            
        except Exception as e:
            self.logger.error(
                "Error getting audit access summary",
                user_id=str(user.id) if user else None,
                error=str(e),
                exc_info=True
            )
            return {
                'has_access': False,
                'permissions': [],
                'access_level': 'error',
                'restrictions': [f'Error: {str(e)}']
            }
    
    def log_access_attempt(self, user: User, action: str, resource: str, success: bool, details: Dict[str, Any] = None):
        """
        Log an audit access attempt for security monitoring.
        
        Args:
            user: User attempting access
            action: Action being attempted
            resource: Resource being accessed
            success: Whether access was successful
            details: Additional details about the attempt
        """
        try:
            log_data = {
                'user_id': user.id if user else None,
                'organization_id': user.organization_id if user else None,
                'action': f"audit_access_{action}",
                'resource_type': 'audit_data',
                'resource_id': resource,
                'details': {
                    'access_successful': success,
                    'user_role': user.role if user else None,
                    'access_timestamp': datetime.utcnow().isoformat(),
                    **(details or {})
                }
            }
            
            # Import here to avoid circular imports
            from app.core.audit import log_system_action
            log_system_action(**log_data)
            
        except Exception as e:
            self.logger.error(
                "Failed to log access attempt",
                user_id=str(user.id) if user else None,
                action=action,
                resource=resource,
                error=str(e),
                exc_info=True
            )


# Global audit access control instance
audit_access_control = AuditAccessControl()


def get_audit_access_control() -> AuditAccessControl:
    """Get the global audit access control instance."""
    return audit_access_control
