"""
Centralized audit sink service for unified audit data management.
Provides a single point of entry for all audit operations and data flow management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json

from app.core.logging import get_logger
from app.core.audit import AuditService, get_audit_service
from app.core.audit_retention import AuditRetentionService, get_audit_retention_service
from app.core.audit_access_control import AuditAccessControl, get_audit_access_control, AuditPermission
from app.core.config import settings
from app.models.user import User

logger = get_logger(__name__)


class AuditSinkType(Enum):
    """Types of audit sinks for different data flows."""
    IMMEDIATE = "immediate"  # Immediate database write
    BUFFERED = "buffered"    # Buffered with periodic flush
    ASYNC = "async"          # Asynchronous processing
    ARCHIVE = "archive"      # Direct to archive


class AuditDataPriority(Enum):
    """Priority levels for audit data processing."""
    CRITICAL = "critical"    # Immediate processing required
    HIGH = "high"            # High priority processing
    NORMAL = "normal"        # Standard processing
    LOW = "low"              # Low priority, can be delayed


class CentralizedAuditSink:
    """
    Centralized audit sink service that provides unified audit data management.
    
    This service acts as the single point of entry for all audit operations,
    managing data flow, retention policies, access controls, and storage
    across different audit sinks.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.audit_service = get_audit_service()
        self.retention_service = get_audit_retention_service()
        self.access_control = get_audit_access_control()
        
        # Initialize audit sinks
        self.sinks = {
            AuditSinkType.IMMEDIATE: self._immediate_sink,
            AuditSinkType.BUFFERED: self._buffered_sink,
            AuditSinkType.ASYNC: self._async_sink,
            AuditSinkType.ARCHIVE: self._archive_sink
        }
        
        # Buffer for batched operations
        self.buffer = []
        self.buffer_size = 100
        self.buffer_timeout = 60  # seconds
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for audit processing."""
        try:
            # Start buffer flush task
            asyncio.create_task(self._buffer_flush_task())
            
            # Start retention cleanup task
            asyncio.create_task(self._retention_cleanup_task())
            
            self.logger.info("Background audit tasks started successfully")
            
        except Exception as e:
            self.logger.error("Failed to start background audit tasks", error=str(e), exc_info=True)
    
    async def _buffer_flush_task(self):
        """Background task to flush buffered audit data."""
        while True:
            try:
                await asyncio.sleep(self.buffer_timeout)
                await self._flush_buffer()
            except Exception as e:
                self.logger.error("Error in buffer flush task", error=str(e), exc_info=True)
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _retention_cleanup_task(self):
        """Background task to run retention cleanup."""
        while True:
            try:
                # Run cleanup every 24 hours
                await asyncio.sleep(24 * 60 * 60)
                await self._run_retention_cleanup()
            except Exception as e:
                self.logger.error("Error in retention cleanup task", error=str(e), exc_info=True)
                await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying
    
    async def _flush_buffer(self):
        """Flush buffered audit data to the database."""
        if not self.buffer:
            return
        
        try:
            # Process buffered items
            buffered_items = self.buffer.copy()
            self.buffer.clear()
            
            for item in buffered_items:
                await self._process_audit_item(item)
            
            self.logger.info(f"Flushed {len(buffered_items)} buffered audit items")
            
        except Exception as e:
            self.logger.error("Failed to flush buffer", error=str(e), exc_info=True)
            # Put items back in buffer for retry
            self.buffer.extend(buffered_items)
    
    async def _run_retention_cleanup(self):
        """Run retention cleanup for expired audit data."""
        try:
            cleanup_stats = self.retention_service.cleanup_expired_audit_data()
            self.logger.info("Retention cleanup completed", stats=cleanup_stats)
            
        except Exception as e:
            self.logger.error("Failed to run retention cleanup", error=str(e), exc_info=True)
    
    async def _process_audit_item(self, item: Dict[str, Any]):
        """Process a single audit item."""
        try:
            sink_type = item.get('sink_type', AuditSinkType.IMMEDIATE)
            sink_func = self.sinks.get(sink_type)
            
            if sink_func:
                await sink_func(item)
            else:
                self.logger.error(f"Unknown sink type: {sink_type}")
                
        except Exception as e:
            self.logger.error("Failed to process audit item", item=item, error=str(e), exc_info=True)
    
    async def _immediate_sink(self, item: Dict[str, Any]):
        """Immediate audit sink - writes directly to database."""
        try:
            action = item.get('action')
            organization_id = item.get('organization_id')
            user_id = item.get('user_id')
            resource_type = item.get('resource_type')
            resource_id = item.get('resource_id')
            details = item.get('details')
            ip_address = item.get('ip_address')
            user_agent = item.get('user_agent')
            redact_level = item.get('redact_level')
            
            # Log the action immediately
            audit_id = self.audit_service.log_action(
                action=action,
                organization_id=organization_id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                redact_level=redact_level
            )
            
            if audit_id:
                self.logger.debug(
                    "Audit item processed immediately",
                    audit_id=audit_id,
                    action=action,
                    organization_id=str(organization_id)
                )
            
        except Exception as e:
            self.logger.error("Failed to process immediate audit item", item=item, error=str(e), exc_info=True)
    
    async def _buffered_sink(self, item: Dict[str, Any]):
        """Buffered audit sink - adds to buffer for batch processing."""
        try:
            self.buffer.append(item)
            
            # Flush buffer if it's full
            if len(self.buffer) >= self.buffer_size:
                await self._flush_buffer()
            
        except Exception as e:
            self.logger.error("Failed to add item to buffer", item=item, error=str(e), exc_info=True)
    
    async def _async_sink(self, item: Dict[str, Any]):
        """Asynchronous audit sink - processes in background."""
        try:
            # Create background task for processing
            asyncio.create_task(self._immediate_sink(item))
            
        except Exception as e:
            self.logger.error("Failed to create async audit task", item=item, error=str(e), exc_info=True)
    
    async def _archive_sink(self, item: Dict[str, Any]):
        """Archive audit sink - writes directly to archive."""
        try:
            # For now, just log to immediate sink
            # In the future, this could write directly to archive storage
            await self._immediate_sink(item)
            
        except Exception as e:
            self.logger.error("Failed to process archive audit item", item=item, error=str(e), exc_info=True)
    
    async def log_audit_event(
        self,
        action: str,
        organization_id: int,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        sink_type: AuditSinkType = AuditSinkType.IMMEDIATE,
        priority: AuditDataPriority = AuditDataPriority.NORMAL,
        redact_level: Optional[str] = None
    ) -> str:
        """
        Log an audit event through the centralized sink.
        
        Args:
            action: Description of the action performed
            organization_id: ID of the organization
            user_id: ID of the user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            details: Additional details about the action
            ip_address: IP address of the request
            user_agent: User agent string
            sink_type: Type of audit sink to use
            priority: Priority level for processing
            redact_level: Level of redaction to apply
            
        Returns:
            Audit log ID or task identifier
        """
        try:
            # Create audit item
            audit_item = {
                'action': action,
                'organization_id': organization_id,
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'sink_type': sink_type,
                'priority': priority,
                'redact_level': redact_level,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Process based on sink type
            if sink_type == AuditSinkType.IMMEDIATE:
                await self._immediate_sink(audit_item)
                return "immediate_processed"
            elif sink_type == AuditSinkType.BUFFERED:
                await self._buffered_sink(audit_item)
                return "buffered"
            elif sink_type == AuditSinkType.ASYNC:
                await self._async_sink(audit_item)
                return "async_queued"
            elif sink_type == AuditSinkType.ARCHIVE:
                await self._archive_sink(audit_item)
                return "archived"
            else:
                self.logger.error(f"Unknown sink type: {sink_type}")
                return "error"
            
        except Exception as e:
            self.logger.error(
                "Failed to log audit event",
                action=action,
                organization_id=str(organization_id),
                error=str(e),
                exc_info=True
            )
            return "error"
    
    async def log_ai_request(
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
        sink_type: AuditSinkType = AuditSinkType.IMMEDIATE,
        priority: AuditDataPriority = AuditDataPriority.NORMAL
    ) -> str:
        """
        Log an AI request through the centralized sink.
        
        Args:
            request_type: Type of AI request
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
            sink_type: Type of audit sink to use
            priority: Priority level for processing
            
        Returns:
            AI request log ID or task identifier
        """
        try:
            # Create AI request item
            ai_request_item = {
                'type': 'ai_request',
                'request_type': request_type,
                'organization_id': organization_id,
                'user_id': user_id,
                'model_used': model_used,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'processing_time_ms': processing_time_ms,
                'cost_usd': cost_usd,
                'status': status,
                'error_message': error_message,
                'sink_type': sink_type,
                'priority': priority,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Process based on sink type
            if sink_type == AuditSinkType.IMMEDIATE:
                # Use the audit service directly for AI requests
                ai_request_id = self.audit_service.log_ai_request(
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
                return ai_request_id or "immediate_processed"
            else:
                # For other sink types, process as regular audit item
                return await self.log_audit_event(
                    action=f"ai_request_{request_type}",
                    organization_id=organization_id,
                    user_id=user_id,
                    resource_type="ai_request",
                    details=ai_request_item,
                    sink_type=sink_type,
                    priority=priority
                )
            
        except Exception as e:
            self.logger.error(
                "Failed to log AI request",
                request_type=request_type,
                organization_id=str(organization_id),
                error=str(e),
                exc_info=True
            )
            return "error"
    
    def get_audit_summary(
        self,
        user: User,
        organization_id: Optional[int] = None,
        include_retention_stats: bool = False
    ) -> Dict[str, Any]:
        """
        Get audit summary with access control enforcement.
        
        Args:
            user: User requesting the summary
            organization_id: Organization ID to get summary for
            include_retention_stats: Whether to include retention statistics
            
        Returns:
            Audit summary data
        """
        try:
            # Check permissions
            if not self.access_control.has_permission(user, AuditPermission.VIEW_AUDIT_SUMMARY):
                self.access_control.log_access_attempt(
                    user, "view_summary", "audit_summary", False,
                    {"reason": "Insufficient permissions"}
                )
                return {
                    'error': 'Insufficient permissions to view audit summary',
                    'permissions_required': [AuditPermission.VIEW_AUDIT_SUMMARY.value]
                }
            
            # Use user's organization if not specified
            if not organization_id:
                organization_id = user.organization_id
            
            # Check organization access
            if not self.access_control.can_access_organization_data(user, organization_id):
                self.access_control.log_access_attempt(
                    user, "view_summary", f"org_{organization_id}", False,
                    {"reason": "Cannot access organization data"}
                )
                return {
                    'error': 'Cannot access data for specified organization',
                    'organization_id': organization_id
                }
            
            # Get audit summary
            summary = self.audit_service.get_audit_summary(
                organization_id=organization_id,
                days=30
            )
            
            # Add retention stats if requested and permitted
            if include_retention_stats and self.access_control.has_permission(user, AuditPermission.VIEW_RETENTION_STATS):
                retention_stats = self.retention_service.get_retention_stats(organization_id)
                summary['retention_stats'] = retention_stats
            
            # Add access control summary
            summary['access_control'] = self.access_control.get_audit_access_summary(user)
            
            # Log successful access
            self.access_control.log_access_attempt(
                user, "view_summary", f"org_{organization_id}", True,
                {"summary_period_days": 30, "include_retention_stats": include_retention_stats}
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(
                "Failed to get audit summary",
                user_id=str(user.id) if user else None,
                organization_id=str(organization_id),
                error=str(e),
                exc_info=True
            )
            return {
                'error': 'Failed to retrieve audit summary',
                'details': str(e)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information for the audit sink."""
        try:
            return {
                'status': 'healthy',
                'service': 'centralized_audit_sink',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'audit_service': 'operational',
                    'retention_service': 'operational',
                    'access_control': 'operational'
                },
                'buffer_status': {
                    'current_size': len(self.buffer),
                    'max_size': self.buffer_size,
                    'flush_timeout': self.buffer_timeout
                },
                'features': [
                    'unified_audit_logging',
                    'retention_policies',
                    'access_controls',
                    'data_archiving',
                    'buffered_processing',
                    'asynchronous_processing'
                ]
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'centralized_audit_sink',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }


# Global centralized audit sink instance
centralized_audit_sink = CentralizedAuditSink()


def get_centralized_audit_sink() -> CentralizedAuditSink:
    """Get the global centralized audit sink instance."""
    return centralized_audit_sink
