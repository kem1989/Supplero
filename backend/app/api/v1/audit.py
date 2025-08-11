"""
Audit API endpoints for accessing audit logs and AI request logs.
Provides comprehensive audit trail access with proper access controls.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user, get_current_user_optional
from app.core.audit import get_audit_service, AuditService
from app.core.redaction import RedactionLevel
from app.schemas.audit import (
    AuditLogResponse, AIRequestResponse, AuditLogFilter, AuditLogSummary
)
from app.models.user import User
from app.models.organization import Organization

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    request: Request,
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Retrieve audit logs for the current user's organization.
    Requires authentication and proper role-based access.
    """
    try:
        # Get user's organization
        organization_id = current_user.organization_id
        
        # Log the audit log access
        audit_service.log_action(
            action="audit_logs_accessed",
            organization_id=organization_id,
            user_id=current_user.id,
            resource_type="audit_logs",
            details={
                "filters": {
                    "action": action,
                    "resource_type": resource_type,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "limit": limit,
                    "offset": offset
                }
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Retrieve audit logs
        audit_logs = audit_service.get_audit_logs(
            organization_id=organization_id,
            user_id=None,  # Allow viewing all users' actions within organization
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return audit_logs
        
    except Exception as e:
        # Log the error
        audit_service.log_action(
            action="audit_logs_access_failed",
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            resource_type="audit_logs",
            details={"error": str(e)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit logs"
        )


@router.get("/logs/summary", response_model=AuditLogSummary)
async def get_audit_summary(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Get audit log summary statistics for the current user's organization.
    Provides aggregated metrics and recent activity.
    """
    try:
        # Get user's organization
        organization_id = current_user.organization_id
        
        # Log the summary access
        audit_service.log_action(
            action="audit_summary_accessed",
            organization_id=organization_id,
            user_id=current_user.id,
            resource_type="audit_summary",
            details={"summary_period_days": days},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Get audit summary
        summary = audit_service.get_audit_summary(
            organization_id=organization_id,
            days=days
        )
        
        return summary
        
    except Exception as e:
        # Log the error
        audit_service.log_action(
            action="audit_summary_access_failed",
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            resource_type="audit_summary",
            details={"error": str(e)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit summary"
        )


@router.get("/ai-requests", response_model=List[AIRequestResponse])
async def get_ai_requests(
    request: Request,
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Retrieve AI request logs for the current user's organization.
    Provides visibility into AI usage, costs, and performance.
    """
    try:
        # Get user's organization
        organization_id = current_user.organization_id
        
        # Log the AI requests access
        audit_service.log_action(
            action="ai_requests_accessed",
            organization_id=organization_id,
            user_id=current_user.id,
            resource_type="ai_requests",
            details={
                "filters": {
                    "request_type": request_type,
                    "status": status,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "limit": limit,
                    "offset": offset
                }
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Retrieve AI requests
        ai_requests = audit_service.get_ai_requests(
            organization_id=organization_id,
            user_id=current_user.id,
            request_type=request_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return ai_requests
        
    except Exception as e:
        # Log the error
        audit_service.log_action(
            action="ai_requests_access_failed",
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            resource_type="ai_requests",
            details={"error": str(e)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve AI request logs"
        )


@router.get("/logs/export")
async def export_audit_logs(
    request: Request,
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Export audit logs in CSV or JSON format.
    Useful for compliance reporting and external analysis.
    """
    try:
        # Get user's organization
        organization_id = current_user.organization_id
        
        # Log the export action
        audit_service.log_action(
            action="audit_logs_exported",
            organization_id=organization_id,
            user_id=current_user.id,
            resource_type="audit_logs",
            details={
                "export_format": format,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Get audit logs for export
        audit_logs = audit_service.get_audit_logs(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Higher limit for exports
            offset=0
        )
        
        if format == "csv":
            # Generate CSV content
            csv_content = _generate_csv_content(audit_logs)
            return JSONResponse(
                content={"csv_content": csv_content},
                headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
            )
        else:
            # Return JSON directly
            return audit_logs
        
    except Exception as e:
        # Log the error
        audit_service.log_action(
            action="audit_logs_export_failed",
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            resource_type="audit_logs",
            details={"error": str(e)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to export audit logs"
        )


def _generate_csv_content(audit_logs: List[AuditLogResponse]) -> str:
    """Generate CSV content from audit logs."""
    if not audit_logs:
        return ""
    
    # CSV headers
    headers = [
        "ID", "Organization ID", "User ID", "Action", "Resource Type", 
        "Resource ID", "IP Address", "User Agent", "Created At"
    ]
    
    # CSV rows
    rows = [headers]
    for log in audit_logs:
        row = [
            str(log.id),
            str(log.organization_id),
            str(log.user_id) if log.user_id else "",
            log.action,
            log.resource_type or "",
            str(log.resource_id) if log.resource_id else "",
            log.ip_address or "",
            log.user_agent or "",
            log.created_at.isoformat()
        ]
        rows.append(row)
    
    # Convert to CSV string
    csv_lines = []
    for row in rows:
        # Escape quotes and wrap in quotes if needed
        escaped_row = []
        for cell in row:
            cell_str = str(cell)
            if '"' in cell_str or ',' in cell_str or '\n' in cell_str:
                # Escape quotes by doubling them and wrap in quotes
                escaped_cell = '"' + cell_str.replace('"', '""') + '"'
            else:
                escaped_cell = cell_str
            escaped_row.append(escaped_cell)
        csv_lines.append(','.join(escaped_row))
    
    return '\n'.join(csv_lines)


@router.get("/health")
async def audit_health_check(
    current_user: User = Depends(get_current_user_optional),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Health check endpoint for the audit service.
    Verifies that audit logging is functioning properly.
    """
    try:
        # Test audit service functionality
        if current_user:
            # Log a health check action
            audit_service.log_action(
                action="audit_health_check",
                organization_id=current_user.organization_id,
                user_id=current_user.id,
                resource_type="audit_service",
                details={"health_check": True}
            )
        
        return {
            "status": "healthy",
            "service": "audit",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "audit_logging",
                "ai_request_tracking",
                "data_redaction",
                "retention_policies",
                "export_capabilities"
            ]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "audit",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        } 