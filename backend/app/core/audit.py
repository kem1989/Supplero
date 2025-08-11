"""
Centralized audit service for comprehensive activity tracking and compliance.
Implements enterprise-grade audit logging with retention and access policies.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.redaction import redact_for_audit, RedactionLevel
from app.models.audit import AuditLog, AIRequest
from app.models.user import User
from app.models.organization import Organization
from app.core.database import get_db

logger = get_logger(__name__)


class AuditService:
    """Centralized audit service for comprehensive activity tracking."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.retention_days = 2555  # 7 years for compliance
    
    def log_action(
        self,
        action: str,
        organization_id: int,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        redact_level: RedactionLevel = RedactionLevel.MEDIUM
    ) -> str:
        """
        Log a user or system action for audit purposes.
        
        Args:
            action: Description of the action performed
            organization_id: ID of the organization
            user_id: ID of the user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            details: Additional details about the action
            ip_address: IP address of the request
            user_agent: User agent string
            redact_level: Level of redaction to apply to details
            
        Returns:
            Audit log ID
        """
        # Redact sensitive information from details
        redacted_details = None
        if details:
            redacted_details = redact_for_audit(details, redact_level)
        
        audit_data = {
            'organization_id': organization_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': redacted_details,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }
        
        # Log immediately for now (can be enhanced with queuing later)
        try:
            with next(get_db()) as db:
                audit_log = AuditLog(**audit_data)
                db.add(audit_log)
                db.commit()
                
                self.logger.info(
                    "Audit log created successfully",
                    audit_id=audit_log.id,
                    action=action,
                    user_id=str(user_id) if user_id else None,
                    organization_id=str(organization_id)
                )
        except Exception as e:
            self.logger.error(
                "Failed to create audit log",
                error=str(e),
                exc_info=True
            )
            return None
        
        # Also log immediately for critical actions
        if self._is_critical_action(action):
            self.logger.warning(
                "Critical action logged",
                audit_id=audit_log.id,
                action=action,
                user_id=str(user_id) if user_id else None,
                organization_id=str(organization_id)
            )
        
        return audit_log.id
    
    def _is_critical_action(self, action: str) -> bool:
        """Determine if an action is critical and requires immediate logging."""
        critical_actions = [
            'user_login', 'user_logout', 'password_change', 'role_change',
            'organization_delete', 'user_delete', 'contract_delete',
            'supplier_delete', 'api_key_generated', 'api_key_revoked'
        ]
        return any(critical in action.lower() for critical in critical_actions)
    
    def log_ai_request(
        self,
        request_type: str,
        organization_id: int,
        user_id: Optional[int] = None,
        model_used: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        cost_usd: Optional[float] = None,
        status: str = "completed",
        error_message: Optional[str] = None,
        redact_level: RedactionLevel = RedactionLevel.HIGH
    ) -> str:
        """
        Log an AI request for compliance and cost monitoring.
        
        Args:
            request_type: Type of AI request (e.g., contract_analysis)
            organization_id: ID of the organization
            user_id: ID of the user who made the request
            model_used: AI model used for the request
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the response
            total_tokens: Total tokens used
            processing_time_ms: Processing time in milliseconds
            cost_usd: Cost in USD
            status: Request status
            error_message: Error message if failed
            redact_level: Level of redaction to apply
            
        Returns:
            AI request log ID
        """
        # Redact sensitive information
        redacted_prompt_tokens = self._redact_numeric_value(prompt_tokens, redact_level)
        redacted_completion_tokens = self._redact_numeric_value(completion_tokens, redact_level)
        redacted_total_tokens = self._redact_numeric_value(total_tokens, redact_level)
        redacted_processing_time = self._redact_numeric_value(processing_time_ms, redact_level)
        redacted_cost = self._redact_numeric_value(cost_usd, redact_level)
        
        ai_request_data = {
            'organization_id': organization_id,
            'user_id': user_id,
            'request_type': request_type,
            'model_used': model_used,
            'prompt_tokens': redacted_prompt_tokens,
            'completion_tokens': redacted_completion_tokens,
            'total_tokens': redacted_total_tokens,
            'processing_time_ms': redacted_processing_time,
            'cost_usd': redacted_cost,
            'status': status,
            'error_message': error_message,
        }
        
        # Log immediately
        try:
            with next(get_db()) as db:
                ai_request = AIRequest(**ai_request_data)
                db.add(ai_request)
                db.commit()
                
                self.logger.info(
                    "AI request logged successfully",
                    request_id=ai_request.id,
                    request_type=request_type,
                    model_used=model_used,
                    status=status,
                    user_id=str(user_id) if user_id else None,
                    organization_id=str(organization_id)
                )
        except Exception as e:
            self.logger.error(
                "Failed to log AI request",
                error=str(e),
                exc_info=True
            )
            return None
        
        return ai_request.id
    
    def _redact_numeric_value(
        self, 
        value: Optional[Union[int, float]], 
        level: RedactionLevel
    ) -> Optional[str]:
        """Redact numeric values based on sensitivity level."""
        if value is None:
            return None
        
        if level == RedactionLevel.CRITICAL:
            return '[CRITICAL_VALUE_REDACTED]'
        elif level == RedactionLevel.HIGH:
            return '[HIGH_VALUE_REDACTED]'
        elif level == RedactionLevel.MEDIUM:
            # Show range for medium sensitivity
            if isinstance(value, (int, float)):
                if value < 100:
                    return '[SMALL_VALUE_REDACTED]'
                elif value < 10000:
                    return '[MEDIUM_VALUE_REDACTED]'
                else:
                    return '[LARGE_VALUE_REDACTED]'
            return '[MEDIUM_VALUE_REDACTED]'
        else:
            return str(value)
    
    def get_audit_logs(
        self,
        organization_id: int,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Retrieve audit logs with filtering and pagination.
        
        Args:
            organization_id: Organization ID to filter by
            user_id: User ID to filter by
            action: Action to filter by
            resource_type: Resource type to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of audit log entries
        """
        try:
            with next(get_db()) as db:
                # Build query with filters
                query = db.query(AuditLog).filter(
                    AuditLog.organization_id == organization_id
                )
                
                if user_id:
                    query = query.filter(AuditLog.user_id == user_id)
                if action:
                    query = query.filter(AuditLog.action == action)
                if resource_type:
                    query = query.filter(AuditLog.resource_type == resource_type)
                if start_date:
                    query = query.filter(AuditLog.created_at >= start_date)
                if end_date:
                    query = query.filter(AuditLog.created_at <= end_date)
                
                # Order by creation date (newest first)
                query = query.order_by(AuditLog.created_at.desc())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Execute query
                audit_logs = query.all()
                
                return audit_logs
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve audit logs",
                error=str(e),
                organization_id=str(organization_id),
                exc_info=True
            )
            return []
    
    def get_ai_requests(
        self,
        organization_id: int,
        user_id: Optional[int] = None,
        request_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AIRequest]:
        """
        Retrieve AI request logs with filtering and pagination.
        
        Args:
            organization_id: Organization ID to filter by
            user_id: User ID to filter by
            request_type: Request type to filter by
            status: Status to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of AI request log entries
        """
        try:
            with next(get_db()) as db:
                # Build query with filters
                query = db.query(AIRequest).filter(
                    AIRequest.organization_id == organization_id
                )
                
                if user_id:
                    query = query.filter(AIRequest.user_id == user_id)
                if request_type:
                    query = query.filter(AIRequest.request_type == request_type)
                if status:
                    query = query.filter(AIRequest.status == status)
                if start_date:
                    query = query.filter(AIRequest.created_at >= start_date)
                if end_date:
                    query = query.filter(AIRequest.created_at <= end_date)
                
                # Order by creation date (newest first)
                query = query.order_by(AIRequest.created_at.desc())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Execute query
                ai_requests = query.all()
                
                return ai_requests
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve AI request logs",
                error=str(e),
                organization_id=str(organization_id),
                exc_info=True
            )
            return []
    
    def get_audit_summary(
        self,
        organization_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get audit log summary statistics for an organization.
        
        Args:
            organization_id: Organization ID
            days: Number of days to include in summary
            
        Returns:
            Summary statistics
        """
        try:
            with next(get_db()) as db:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Get total actions
                total_actions = db.query(AuditLog).filter(
                    and_(
                        AuditLog.organization_id == organization_id,
                        AuditLog.created_at >= start_date
                    )
                ).count()
                
                # Get actions by type
                actions_by_type_result = db.query(
                    AuditLog.action,
                    func.count(AuditLog.id)
                ).filter(
                    and_(
                        AuditLog.organization_id == organization_id,
                        AuditLog.created_at >= start_date
                    )
                ).group_by(AuditLog.action).all()
                
                actions_by_type = dict(actions_by_type_result)
                
                # Get actions by user
                actions_by_user_result = db.query(
                    AuditLog.user_id,
                    func.count(AuditLog.id)
                ).filter(
                    and_(
                        AuditLog.organization_id == organization_id,
                        AuditLog.created_at >= start_date,
                        AuditLog.user_id.isnot(None)
                    )
                ).group_by(AuditLog.user_id).all()
                
                actions_by_user = {
                    str(user_id): count 
                    for user_id, count in actions_by_user_result
                }
                
                # Get recent activity
                recent_activity = db.query(AuditLog).filter(
                    and_(
                        AuditLog.organization_id == organization_id,
                        AuditLog.created_at >= start_date
                    )
                ).order_by(AuditLog.created_at.desc()).limit(10).all()
                
                return {
                    'total_actions': total_actions,
                    'actions_by_type': actions_by_type,
                    'actions_by_user': actions_by_user,
                    'recent_activity': recent_activity,
                    'summary_period_days': days,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(
                "Failed to generate audit summary",
                error=str(e),
                organization_id=str(organization_id),
                exc_info=True
            )
            return {
                'total_actions': 0,
                'actions_by_type': {},
                'actions_by_user': {},
                'recent_activity': [],
                'summary_period_days': days,
                'generated_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }


# Global audit service instance
audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Get the global audit service instance."""
    return audit_service


# Convenience functions for common audit operations
def log_user_action(
    action: str,
    organization_id: int,
    user_id: int,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """Log a user action for audit purposes."""
    return audit_service.log_action(
        action=action,
        organization_id=organization_id,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_system_action(
    action: str,
    organization_id: int,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Log a system action for audit purposes."""
    return audit_service.log_action(
        action=action,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details
    )


def log_ai_interaction(
    request_type: str,
    organization_id: int,
    user_id: Optional[int] = None,
    model_used: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    processing_time_ms: Optional[int] = None,
    cost_usd: Optional[float] = None,
    status: str = "completed",
    error_message: Optional[str] = None
) -> str:
    """Log an AI interaction for compliance and cost monitoring."""
    return audit_service.log_ai_request(
        request_type=request_type,
        organization_id=organization_id,
        user_id=user_id,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        processing_time_ms=processing_time_ms,
        cost_usd=cost_usd,
        status=status,
        error_message=error_message
    ) 