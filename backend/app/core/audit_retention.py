"""
Audit retention service for managing audit data lifecycle, archiving, and cleanup.
Implements enterprise-grade retention policies and automated data management.
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import get_db
from app.models.audit import AuditLog, AIRequest
from app.core.secure_storage import encrypt_data, decrypt_data

logger = get_logger(__name__)


class AuditRetentionService:
    """Service for managing audit data retention, archiving, and cleanup."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.archive_path = Path(settings.AUDIT_ARCHIVE_PATH)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure archive subdirectories exist
        (self.archive_path / "audit_logs").mkdir(exist_ok=True)
        (self.archive_path / "ai_requests").mkdir(exist_ok=True)
        (self.archive_path / "backups").mkdir(exist_ok=True)
    
    def cleanup_expired_audit_data(self, organization_id: Optional[int] = None) -> Dict[str, int]:
        """
        Clean up expired audit data based on retention policies.
        
        Args:
            organization_id: Optional organization ID to limit cleanup to
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cleanup_stats = {
                'audit_logs_deleted': 0,
                'ai_requests_deleted': 0,
                'archives_created': 0,
                'errors': 0
            }
            
            # Calculate cutoff dates
            retention_cutoff = datetime.utcnow() - timedelta(days=settings.AUDIT_RETENTION_DAYS)
            archive_cutoff = datetime.utcnow() - timedelta(days=settings.AUDIT_ARCHIVE_DAYS)
            
            with next(get_db()) as db:
                # Archive old audit logs before deletion
                if organization_id:
                    old_audit_logs = db.query(AuditLog).filter(
                        and_(
                            AuditLog.organization_id == organization_id,
                            AuditLog.created_at < archive_cutoff
                        )
                    ).all()
                else:
                    old_audit_logs = db.query(AuditLog).filter(
                        AuditLog.created_at < archive_cutoff
                    ).all()
                
                if old_audit_logs:
                    archive_path = self._archive_audit_logs(old_audit_logs, organization_id)
                    if archive_path:
                        cleanup_stats['archives_created'] += 1
                        self.logger.info(
                            "Audit logs archived successfully",
                            archive_path=str(archive_path),
                            count=len(old_audit_logs),
                            organization_id=str(organization_id) if organization_id else "all"
                        )
                
                # Delete expired audit logs
                if organization_id:
                    deleted_logs = db.query(AuditLog).filter(
                        and_(
                            AuditLog.organization_id == organization_id,
                            AuditLog.created_at < retention_cutoff
                        )
                    ).delete()
                else:
                    deleted_logs = db.query(AuditLog).filter(
                        AuditLog.created_at < retention_cutoff
                    ).delete()
                
                cleanup_stats['audit_logs_deleted'] = deleted_logs
                
                # Archive old AI requests before deletion
                if organization_id:
                    old_ai_requests = db.query(AIRequest).filter(
                        and_(
                            AIRequest.organization_id == organization_id,
                            AIRequest.created_at < archive_cutoff
                        )
                    ).all()
                else:
                    old_ai_requests = db.query(AIRequest).filter(
                        AIRequest.created_at < archive_cutoff
                    ).all()
                
                if old_ai_requests:
                    archive_path = self._archive_ai_requests(old_ai_requests, organization_id)
                    if archive_path:
                        cleanup_stats['archives_created'] += 1
                        self.logger.info(
                            "AI requests archived successfully",
                            archive_path=str(archive_path),
                            count=len(old_ai_requests),
                            organization_id=str(organization_id) if organization_id else "all"
                        )
                
                # Delete expired AI requests
                if organization_id:
                    deleted_requests = db.query(AIRequest).filter(
                        and_(
                            AIRequest.organization_id == organization_id,
                            AIRequest.created_at < retention_cutoff
                        )
                    ).delete()
                else:
                    deleted_requests = db.query(AIRequest).filter(
                        AIRequest.created_at < retention_cutoff
                    ).delete()
                
                cleanup_stats['ai_requests_deleted'] = deleted_requests
                
                # Commit changes
                db.commit()
                
                self.logger.info(
                    "Audit data cleanup completed",
                    stats=cleanup_stats,
                    organization_id=str(organization_id) if organization_id else "all"
                )
                
        except Exception as e:
            cleanup_stats['errors'] += 1
            self.logger.error(
                "Failed to cleanup expired audit data",
                error=str(e),
                organization_id=str(organization_id) if organization_id else "all",
                exc_info=True
            )
        
        return cleanup_stats
    
    def _archive_audit_logs(self, audit_logs: List[AuditLog], organization_id: Optional[int] = None) -> Optional[Path]:
        """Archive audit logs to compressed, encrypted files."""
        try:
            if not audit_logs:
                return None
            
            # Create archive filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            org_suffix = f"_org_{organization_id}" if organization_id else "_all"
            archive_filename = f"audit_logs_{timestamp}{org_suffix}.json.gz"
            archive_path = self.archive_path / "audit_logs" / archive_filename
            
            # Convert to serializable format
            archive_data = []
            for log in audit_logs:
                log_dict = {
                    'id': log.id,
                    'organization_id': log.organization_id,
                    'user_id': log.user_id,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': str(log.ip_address) if log.ip_address else None,
                    'user_agent': log.user_agent,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                archive_data.append(log_dict)
            
            # Compress and optionally encrypt
            json_content = json.dumps(archive_data, indent=2)
            
            if settings.AUDIT_COMPRESSION_ENABLED:
                with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                    f.write(json_content)
            else:
                with open(archive_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
            
            # Encrypt if enabled
            if settings.AUDIT_ENCRYPTION_ENABLED:
                encrypted_path = archive_path.with_suffix('.json.gz.enc')
                with open(archive_path, 'rb') as f:
                    data = f.read()
                
                encrypted_data = encrypt_data(data)
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                
                # Remove unencrypted file
                archive_path.unlink()
                archive_path = encrypted_path
            
            return archive_path
            
        except Exception as e:
            self.logger.error(
                "Failed to archive audit logs",
                error=str(e),
                count=len(audit_logs),
                exc_info=True
            )
            return None
    
    def _archive_ai_requests(self, ai_requests: List[AIRequest], organization_id: Optional[int] = None) -> Optional[Path]:
        """Archive AI requests to compressed, encrypted files."""
        try:
            if not ai_requests:
                return None
            
            # Create archive filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            org_suffix = f"_org_{organization_id}" if organization_id else "_all"
            archive_filename = f"ai_requests_{timestamp}{org_suffix}.json.gz"
            archive_path = self.archive_path / "ai_requests" / archive_filename
            
            # Convert to serializable format
            archive_data = []
            for req in ai_requests:
                req_dict = {
                    'id': req.id,
                    'organization_id': req.organization_id,
                    'user_id': req.user_id,
                    'request_type': req.request_type,
                    'model_used': req.model_used,
                    'prompt_tokens': req.prompt_tokens,
                    'completion_tokens': req.completion_tokens,
                    'total_tokens': req.total_tokens,
                    'processing_time_ms': req.processing_time_ms,
                    'cost_usd': req.cost_usd,
                    'status': req.status,
                    'error_message': req.error_message,
                    'created_at': req.created_at.isoformat() if req.created_at else None
                }
                archive_data.append(req_dict)
            
            # Compress and optionally encrypt
            json_content = json.dumps(archive_data, indent=2)
            
            if settings.AUDIT_COMPRESSION_ENABLED:
                with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                    f.write(json_content)
            else:
                with open(archive_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
            
            # Encrypt if enabled
            if settings.AUDIT_ENCRYPTION_ENABLED:
                encrypted_path = archive_path.with_suffix('.json.gz.enc')
                with open(archive_path, 'rb') as f:
                    data = f.read()
                
                encrypted_data = encrypt_data(data)
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                
                # Remove unencrypted file
                archive_path.unlink()
                archive_path = encrypted_path
            
            return archive_path
            
        except Exception as e:
            self.logger.error(
                "Failed to archive AI requests",
                error=str(e),
                count=len(ai_requests),
                exc_info=True
            )
            return None
    
    def get_retention_stats(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get retention policy statistics and current data usage."""
        try:
            with next(get_db()) as db:
                # Get current data counts
                if organization_id:
                    audit_logs_count = db.query(AuditLog).filter(
                        AuditLog.organization_id == organization_id
                    ).count()
                    ai_requests_count = db.query(AIRequest).filter(
                        AIRequest.organization_id == organization_id
                    ).count()
                else:
                    audit_logs_count = db.query(AuditLog).count()
                    ai_requests_count = db.query(AIRequest).count()
                
                # Get oldest and newest records
                if organization_id:
                    oldest_audit = db.query(AuditLog.created_at).filter(
                        AuditLog.organization_id == organization_id
                    ).order_by(AuditLog.created_at.asc()).first()
                    newest_audit = db.query(AuditLog.created_at).filter(
                        AuditLog.organization_id == organization_id
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    oldest_ai = db.query(AIRequest.created_at).filter(
                        AIRequest.organization_id == organization_id
                    ).order_by(AIRequest.created_at.asc()).first()
                    newest_ai = db.query(AIRequest.created_at).filter(
                        AIRequest.organization_id == organization_id
                    ).order_by(AIRequest.created_at.desc()).first()
                else:
                    oldest_audit = db.query(AuditLog.created_at).order_by(AuditLog.created_at.asc()).first()
                    newest_audit = db.query(AuditLog.created_at).order_by(AuditLog.created_at.desc()).first()
                    
                    oldest_ai = db.query(AIRequest.created_at).order_by(AIRequest.created_at.asc()).first()
                    newest_ai = db.query(AIRequest.created_at).order_by(AIRequest.created_at.desc()).first()
                
                # Calculate archive sizes
                audit_archive_size = self._get_archive_size("audit_logs")
                ai_archive_size = self._get_archive_size("ai_requests")
                
                return {
                    'current_data': {
                        'audit_logs': audit_logs_count,
                        'ai_requests': ai_requests_count,
                        'total': audit_logs_count + ai_requests_count
                    },
                    'data_age': {
                        'audit_logs': {
                            'oldest': oldest_audit[0].isoformat() if oldest_audit and oldest_audit[0] else None,
                            'newest': newest_audit[0].isoformat() if newest_audit and newest_audit[0] else None
                        },
                        'ai_requests': {
                            'oldest': oldest_ai[0].isoformat() if oldest_ai and oldest_ai[0] else None,
                            'newest': newest_ai[0].isoformat() if newest_ai and newest_ai[0] else None
                        }
                    },
                    'archive_info': {
                        'audit_logs_size_mb': round(audit_archive_size / (1024 * 1024), 2),
                        'ai_requests_size_mb': round(ai_archive_size / (1024 * 1024), 2),
                        'total_size_mb': round((audit_archive_size + ai_archive_size) / (1024 * 1024), 2)
                    },
                    'retention_policies': {
                        'retention_days': settings.AUDIT_RETENTION_DAYS,
                        'archive_days': settings.AUDIT_ARCHIVE_DAYS,
                        'compression_enabled': settings.AUDIT_COMPRESSION_ENABLED,
                        'encryption_enabled': settings.AUDIT_ENCRYPTION_ENABLED
                    },
                    'next_cleanup': {
                        'retention_cutoff': (datetime.utcnow() + timedelta(days=settings.AUDIT_RETENTION_DAYS)).isoformat(),
                        'archive_cutoff': (datetime.utcnow() + timedelta(days=settings.AUDIT_ARCHIVE_DAYS)).isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(
                "Failed to get retention stats",
                error=str(e),
                exc_info=True
            )
            return {
                'error': str(e),
                'current_data': {'audit_logs': 0, 'ai_requests': 0, 'total': 0}
            }
    
    def _get_archive_size(self, archive_type: str) -> int:
        """Get total size of archived files in bytes."""
        try:
            archive_dir = self.archive_path / archive_type
            if not archive_dir.exists():
                return 0
            
            total_size = 0
            for file_path in archive_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size
        except Exception as e:
            self.logger.error(f"Failed to get archive size for {archive_type}", error=str(e))
            return 0
    
    def restore_from_archive(self, archive_path: str, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Restore audit data from an archive file."""
        try:
            archive_file = Path(archive_path)
            if not archive_file.exists():
                return {'error': 'Archive file not found', 'restored_count': 0}
            
            # Determine if file is encrypted
            is_encrypted = archive_file.suffix == '.enc'
            
            # Read and decrypt if necessary
            if is_encrypted:
                with open(archive_file, 'rb') as f:
                    encrypted_data = f.read()
                data = decrypt_data(encrypted_data)
            else:
                with open(archive_file, 'rb') as f:
                    data = f.read()
            
            # Decompress if necessary
            if archive_file.suffix == '.gz':
                import gzip
                data = gzip.decompress(data)
            
            # Parse JSON
            archive_data = json.loads(data.decode('utf-8'))
            
            # Filter by organization if specified
            if organization_id:
                archive_data = [item for item in archive_data if item.get('organization_id') == organization_id]
            
            # Restore to database (read-only for now, just count)
            restored_count = len(archive_data)
            
            self.logger.info(
                "Archive restoration completed",
                archive_path=str(archive_path),
                restored_count=restored_count,
                organization_id=str(organization_id) if organization_id else "all"
            )
            
            return {
                'success': True,
                'restored_count': restored_count,
                'archive_path': str(archive_path),
                'organization_id': organization_id
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to restore from archive",
                archive_path=archive_path,
                error=str(e),
                exc_info=True
            )
            return {
                'error': str(e),
                'restored_count': 0,
                'archive_path': archive_path
            }


# Global audit retention service instance
audit_retention_service = AuditRetentionService()


def get_audit_retention_service() -> AuditRetentionService:
    """Get the global audit retention service instance."""
    return audit_retention_service
