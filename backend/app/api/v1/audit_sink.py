"""
Centralized audit sink API endpoints.
Provides access to retention policies, access controls, and system health.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user, get_current_user_optional
from app.core.audit_sink import get_centralized_audit_sink, CentralizedAuditSink, AuditSinkType, AuditDataPriority
from app.core.audit_access_control import get_audit_access_control, AuditPermission
from app.core.audit_retention import get_audit_retention_service
from app.models.user import User

router = APIRouter(prefix="/audit-sink", tags=["audit-sink"])


@router.get("/health")
async def get_audit_sink_health(
    current_user: User = Depends(get_current_user_optional),
    audit_sink: CentralizedAuditSink = Depends(get_centralized_audit_sink)
):
    """
    Get health status of the centralized audit sink.
    Provides information about all audit components and their status.
    """
    try:
        health_info = audit_sink.get_system_health()
        return health_info
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "centralized_audit_sink",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/access-control/summary")
async def get_audit_access_summary(
    current_user: User = Depends(get_current_user),
    audit_access_control = Depends(get_audit_access_control)
):
    """
    Get audit access control summary for the current user.
    Shows permissions, access levels, and restrictions.
    """
    try:
        summary = audit_access_control.get_audit_access_summary(current_user)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get access control summary: {str(e)}"
        )


@router.get("/retention/stats")
async def get_retention_statistics(
    organization_id: Optional[int] = Query(None, description="Organization ID to get stats for"),
    current_user: User = Depends(get_current_user),
    audit_access_control = Depends(get_audit_access_control),
    audit_retention_service = Depends(get_audit_retention_service)
):
    """
    Get retention policy statistics and current data usage.
    Requires VIEW_RETENTION_STATS permission.
    """
    try:
        # Check permissions
        if not audit_access_control.has_permission(current_user, AuditPermission.VIEW_RETENTION_STATS):
            audit_access_control.log_access_attempt(
                current_user, "view_retention_stats", "retention_stats", False,
                {"reason": "Insufficient permissions"}
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view retention statistics"
            )
        
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Check organization access
        if not audit_access_control.can_access_organization_data(current_user, organization_id):
            audit_access_control.log_access_attempt(
                current_user, "view_retention_stats", f"org_{organization_id}", False,
                {"reason": "Cannot access organization data"}
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot access data for specified organization"
            )
        
        # Get retention statistics
        stats = audit_retention_service.get_retention_stats(organization_id)
        
        # Log successful access
        audit_access_control.log_access_attempt(
            current_user, "view_retention_stats", f"org_{organization_id}", True,
            {"organization_id": organization_id}
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get retention statistics: {str(e)}"
        )


@router.post("/retention/cleanup")
async def trigger_retention_cleanup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    audit_access_control = Depends(get_audit_access_control),
    audit_retention_service = Depends(get_audit_retention_service),
    organization_id: Optional[int] = Query(None, description="Organization ID to cleanup")
):
    """
    Trigger manual retention cleanup for expired audit data.
    Requires MANAGE_RETENTION_POLICIES permission.
    """
    try:
        # Check permissions
        if not audit_access_control.has_permission(current_user, AuditPermission.MANAGE_RETENTION_POLICIES):
            audit_access_control.log_access_attempt(
                current_user, "trigger_cleanup", "retention_cleanup", False,
                {"reason": "Insufficient permissions"}
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to manage retention policies"
            )
        
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Check organization access
        if not audit_access_control.can_access_organization_data(current_user, organization_id):
            audit_access_control.log_access_attempt(
                current_user, "trigger_cleanup", f"org_{organization_id}", False,
                {"reason": "Cannot access organization data"}
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot access data for specified organization"
            )
        
        # Add cleanup task to background tasks
        def run_cleanup():
            try:
                cleanup_stats = audit_retention_service.cleanup_expired_audit_data(organization_id)
                return cleanup_stats
            except Exception as e:
                return {"error": str(e)}
        
        background_tasks.add_task(run_cleanup)
        
        # Log successful access
        audit_access_control.log_access_attempt(
            current_user, "trigger_cleanup", f"org_{organization_id}", True,
            {"organization_id": organization_id, "background_task": True}
        )
        
        return {
            "message": "Retention cleanup triggered successfully",
            "organization_id": organization_id,
            "background_task": True,
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger retention cleanup: {str(e)}"
        )


@router.post("/log/event")
async def log_audit_event_via_sink(
    request: Request,
    action: str,
    organization_id: int,
    current_user: User = Depends(get_current_user),
    audit_sink: CentralizedAuditSink = Depends(get_centralized_audit_sink),
    user_id: Optional[int] = Query(None, description="User ID who performed the action"),
    resource_type: Optional[str] = Query(None, description="Type of resource affected"),
    resource_id: Optional[str] = Query(None, description="ID of resource affected"),
    details: Optional[Dict[str, Any]] = None,
    sink_type: AuditSinkType = Query(AuditSinkType.IMMEDIATE, description="Type of audit sink to use"),
    priority: AuditDataPriority = Query(AuditDataPriority.NORMAL, description="Priority level for processing"),
    redact_level: Optional[str] = Query(None, description="Level of redaction to apply")
):
    """
    Log an audit event through the centralized audit sink.
    Provides flexible sink types and priority levels.
    """
    try:
        # Use current user's ID if not specified
        if not user_id:
            user_id = current_user.id
        
        # Use current user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Log the audit event
        result = await audit_sink.log_audit_event(
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            sink_type=sink_type,
            priority=priority,
            redact_level=redact_level
        )
        
        return {
            "success": True,
            "result": result,
            "action": action,
            "organization_id": organization_id,
            "sink_type": sink_type.value,
            "priority": priority.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log audit event: {str(e)}"
        )


@router.post("/log/ai-request")
async def log_ai_request_via_sink(
    request: Request,
    request_type: str,
    organization_id: int,
    current_user: User = Depends(get_current_user),
    audit_sink: CentralizedAuditSink = Depends(get_centralized_audit_sink),
    user_id: Optional[int] = Query(None, description="User ID who made the request"),
    model_used: Optional[str] = Query(None, description="AI model used"),
    prompt_tokens: Optional[int] = Query(None, description="Number of prompt tokens"),
    completion_tokens: Optional[int] = Query(None, description="Number of completion tokens"),
    total_tokens: Optional[int] = Query(None, description="Total tokens used"),
    processing_time_ms: Optional[int] = Query(None, description="Processing time in milliseconds"),
    cost_usd: Optional[float] = Query(None, description="Cost in USD"),
    status: str = Query("completed", description="Request status"),
    error_message: Optional[str] = Query(None, description="Error message if failed"),
    sink_type: AuditSinkType = Query(AuditSinkType.IMMEDIATE, description="Type of audit sink to use"),
    priority: AuditDataPriority = Query(AuditDataPriority.NORMAL, description="Priority level for processing")
):
    """
    Log an AI request through the centralized audit sink.
    Provides flexible sink types and priority levels for AI request tracking.
    """
    try:
        # Use current user's ID if not specified
        if not user_id:
            user_id = current_user.id
        
        # Use current user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Log the AI request
        result = await audit_sink.log_ai_request(
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
            error_message=error_message,
            sink_type=sink_type,
            priority=priority
        )
        
        return {
            "success": True,
            "result": result,
            "request_type": request_type,
            "organization_id": organization_id,
            "sink_type": sink_type.value,
            "priority": priority.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log AI request: {str(e)}"
        )


@router.get("/summary")
async def get_audit_summary_via_sink(
    organization_id: Optional[int] = Query(None, description="Organization ID to get summary for"),
    include_retention_stats: bool = Query(False, description="Include retention statistics"),
    current_user: User = Depends(get_current_user),
    audit_sink: CentralizedAuditSink = Depends(get_centralized_audit_sink)
):
    """
    Get audit summary through the centralized audit sink.
    Provides access control enforcement and optional retention statistics.
    """
    try:
        summary = audit_sink.get_audit_summary(
            user=current_user,
            organization_id=organization_id,
            include_retention_stats=include_retention_stats
        )
        
        if 'error' in summary:
            raise HTTPException(status_code=400, detail=summary['error'])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audit summary: {str(e)}"
        )


@router.get("/archive/list")
async def list_archived_audit_data(
    archive_type: Optional[str] = Query(None, description="Type of archive to list (audit_logs, ai_requests)"),
    organization_id: Optional[int] = Query(None, description="Organization ID to filter by"),
    current_user: User = Depends(get_current_user),
    audit_access_control = Depends(get_audit_access_control),
    audit_retention_service = Depends(get_audit_retention_service)
):
    """
    List archived audit data files.
    Requires VIEW_ARCHIVED_DATA permission.
    """
    try:
        # Check permissions
        if not audit_access_control.has_permission(current_user, AuditPermission.VIEW_ARCHIVED_DATA):
            audit_access_control.log_access_attempt(
                current_user, "list_archives", "archived_data", False,
                {"reason": "Insufficient permissions"}
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view archived data"
            )
        
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Check organization access
        if not audit_access_control.can_access_organization_data(current_user, organization_id):
            audit_access_control.log_access_attempt(
                current_user, "list_archives", f"org_{organization_id}", False,
                {"reason": "Cannot access organization data"}
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot access data for specified organization"
            )
        
        # Get archive information
        retention_stats = audit_retention_service.get_retention_stats(organization_id)
        
        # Log successful access
        audit_access_control.log_access_attempt(
            current_user, "list_archives", f"org_{organization_id}", True,
            {"organization_id": organization_id, "archive_type": archive_type}
        )
        
        return {
            "organization_id": organization_id,
            "archive_type": archive_type,
            "archive_info": retention_stats.get('archive_info', {}),
            "message": "Archive listing retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list archived data: {str(e)}"
        )


@router.post("/archive/restore")
async def restore_from_archive(
    archive_path: str,
    organization_id: Optional[int] = Query(None, description="Organization ID to filter restoration by"),
    current_user: User = Depends(get_current_user),
    audit_access_control = Depends(get_audit_access_control),
    audit_retention_service = Depends(get_audit_retention_service)
):
    """
    Restore audit data from an archive file.
    Requires RESTORE_ARCHIVED_DATA permission.
    """
    try:
        # Check permissions
        if not audit_access_control.has_permission(current_user, AuditPermission.RESTORE_ARCHIVED_DATA):
            audit_access_control.log_access_attempt(
                current_user, "restore_archive", "archived_data", False,
                {"reason": "Insufficient permissions"}
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to restore archived data"
            )
        
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id
        
        # Check organization access
        if not audit_access_control.can_access_organization_data(current_user, organization_id):
            audit_access_control.log_access_attempt(
                current_user, "restore_archive", f"org_{organization_id}", False,
                {"reason": "Cannot access organization data"}
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot access data for specified organization"
            )
        
        # Restore from archive
        result = audit_retention_service.restore_from_archive(archive_path, organization_id)
        
        # Log successful access
        audit_access_control.log_access_attempt(
            current_user, "restore_archive", f"org_{organization_id}", True,
            {"archive_path": archive_path, "organization_id": organization_id}
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore from archive: {str(e)}"
        )
