# Centralized Audit Sink with Retention and Access Policies

## Overview

The Centralized Audit Sink is the final component of the **Observability & Audit Baseline** section in Phase 1 of the Supplero project. It provides a unified interface for all audit operations, implements enterprise-grade retention policies, and enforces granular access controls.

## Architecture

### Components

1. **CentralizedAuditSink** - Main service that orchestrates all audit operations
2. **AuditRetentionService** - Manages data lifecycle, archiving, and cleanup
3. **AuditAccessControl** - Implements role-based access policies
4. **AuditSinkType** - Different processing modes for audit data
5. **AuditDataPriority** - Priority levels for audit data processing

### Data Flow

```
User Action → CentralizedAuditSink → [Immediate/Buffered/Async/Archive] → Storage
                                    ↓
                            Access Control Check
                                    ↓
                            Retention Policy Enforcement
                                    ↓
                            Data Archiving & Cleanup
```

## Features

### 1. Unified Audit Interface

- **Single Point of Entry**: All audit operations go through one service
- **Multiple Sink Types**: Support for immediate, buffered, async, and archive processing
- **Priority Handling**: Different priority levels for critical vs. normal operations
- **Flexible Logging**: Support for both regular audit events and AI requests

### 2. Retention Policies

- **Configurable Retention**: 7-year retention for compliance (configurable)
- **Automated Archiving**: Data archived after 1 year with compression and encryption
- **Background Cleanup**: Automated cleanup runs every 24 hours
- **Archive Management**: Compressed, encrypted archives with metadata tracking

### 3. Access Controls

- **Role-Based Permissions**: Granular permissions for different user roles
- **Access Levels**: From own-actions-only to cross-organization access
- **Permission Enforcement**: Automatic filtering based on user permissions
- **Audit Trail**: All access attempts are logged for security monitoring

### 4. Data Management

- **Compression**: Gzip compression for archived data
- **Encryption**: Optional encryption for sensitive archived data
- **Metadata Tracking**: Comprehensive tracking of data age and usage
- **Backup Support**: Configurable backup retention policies

## Configuration

### Environment Variables

```bash
# Audit & Retention Policies
AUDIT_RETENTION_DAYS=2555          # 7 years for compliance
AUDIT_ARCHIVE_DAYS=365             # Archive after 1 year
AUDIT_MAX_LOG_SIZE_MB=100          # Max size for individual logs
AUDIT_COMPRESSION_ENABLED=true     # Enable compression
AUDIT_ENCRYPTION_ENABLED=true      # Enable encryption

# Access Controls
AUDIT_ADMIN_ROLES=admin,auditor,compliance_officer
AUDIT_VIEWER_ROLES=manager,viewer
AUDIT_EXPORT_ROLES=admin,auditor,compliance_officer
AUDIT_DELETE_ROLES=admin

# Storage
AUDIT_STORAGE_TYPE=database        # database, file, s3, elasticsearch
AUDIT_ARCHIVE_STORAGE=file         # file, s3, elasticsearch
AUDIT_ARCHIVE_PATH=./uploads/audit/archive
AUDIT_BACKUP_ENABLED=true
AUDIT_BACKUP_RETENTION_DAYS=3650   # 10 years for backups
```

## API Endpoints

### Audit Sink Health

```http
GET /api/v1/audit-sink/health
```

Returns system health information for all audit components.

### Access Control Summary

```http
GET /api/v1/audit-sink/access-control/summary
```

Shows current user's audit permissions and access levels.

### Retention Statistics

```http
GET /api/v1/audit-sink/retention/stats?organization_id=1
```

Returns retention policy statistics and current data usage.

### Manual Cleanup

```http
POST /api/v1/audit-sink/retention/cleanup?organization_id=1
```

Triggers manual retention cleanup (requires MANAGE_RETENTION_POLICIES permission).

### Audit Event Logging

```http
POST /api/v1/audit-sink/log/event
```

Log audit events through the centralized sink with flexible sink types.

### AI Request Logging

```http
POST /api/v1/audit-sink/log/ai-request
```

Log AI requests with comprehensive tracking and cost monitoring.

### Audit Summary

```http
GET /api/v1/audit-sink/summary?include_retention_stats=true
```

Get audit summary with access control enforcement and optional retention stats.

### Archive Management

```http
GET /api/v1/audit-sink/archive/list
POST /api/v1/audit-sink/archive/restore
```

List and restore archived audit data.

## Usage Examples

### Basic Audit Logging

```python
from app.core.audit_sink import get_centralized_audit_sink, AuditSinkType, AuditDataPriority

audit_sink = get_centralized_audit_sink()

# Immediate logging
await audit_sink.log_audit_event(
    action="user_login",
    organization_id=1,
    user_id=123,
    resource_type="user_session",
    sink_type=AuditSinkType.IMMEDIATE,
    priority=AuditDataPriority.HIGH
)

# Buffered logging for high-volume operations
await audit_sink.log_audit_event(
    action="data_export",
    organization_id=1,
    user_id=123,
    sink_type=AuditSinkType.BUFFERED,
    priority=AuditDataPriority.NORMAL
)
```

### AI Request Logging

```python
# Log AI request with cost tracking
await audit_sink.log_ai_request(
    request_type="contract_analysis",
    organization_id=1,
    user_id=123,
    model_used="gpt-4",
    prompt_tokens=500,
    completion_tokens=200,
    total_tokens=700,
    processing_time_ms=3000,
    cost_usd=0.05,
    status="completed"
)
```

### Access Control

```python
from app.core.audit_access_control import get_audit_access_control, AuditPermission

access_control = get_audit_access_control()

# Check permissions
if access_control.has_permission(user, AuditPermission.VIEW_RETENTION_STATS):
    # Show retention statistics
    pass

# Get access summary
summary = access_control.get_audit_access_summary(user)
print(f"User can access: {summary['access_level']}")
```

## Management Tools

### Command Line Interface

```bash
# Show retention statistics
python -m app.core.audit_management stats --organization-id 1

# Run retention cleanup
python -m app.core.audit_management cleanup --organization-id 1

# Show system health
python -m app.core.audit_management health

# Show access control information
python -m app.core.audit_management access

# Dry run cleanup (no changes)
python -m app.core.audit_management cleanup --dry-run
```

### Testing

```bash
# Run comprehensive tests
python test_audit_sink.py
```

## Security Features

### Data Protection

- **Encryption at Rest**: Archived data can be encrypted
- **Compression**: Reduces storage requirements and transfer times
- **Access Logging**: All access attempts are logged for security monitoring
- **Role-Based Access**: Granular permissions prevent unauthorized access

### Compliance

- **Retention Policies**: Configurable retention periods for different data types
- **Audit Trails**: Complete audit trail of all data access and modifications
- **Data Archiving**: Long-term storage with metadata preservation
- **Export Controls**: Controlled export of audit data for compliance reporting

## Performance Considerations

### Optimization Strategies

- **Buffered Processing**: Batch operations for high-volume scenarios
- **Asynchronous Processing**: Non-blocking operations for better performance
- **Background Cleanup**: Retention cleanup runs in background tasks
- **Compression**: Reduces storage and transfer overhead

### Monitoring

- **Health Checks**: Regular health monitoring of all components
- **Buffer Monitoring**: Track buffer usage and flush performance
- **Archive Statistics**: Monitor archive sizes and cleanup effectiveness
- **Performance Metrics**: Track processing times and throughput

## Deployment

### Prerequisites

- PostgreSQL database with audit tables
- File system access for archive storage
- Redis for caching (optional)
- Proper file permissions for archive directories

### Setup

1. **Configure Environment**: Set all required environment variables
2. **Create Archive Directories**: Ensure archive paths exist and are writable
3. **Database Migration**: Run database migrations for audit tables
4. **Service Registration**: Register audit sink services in your application
5. **Background Tasks**: Ensure background tasks can run (for cleanup)

### Health Checks

```python
# Check system health
health = audit_sink.get_system_health()
if health['status'] == 'healthy':
    print("Audit system is operational")
else:
    print(f"Audit system issues: {health['error']}")
```

## Troubleshooting

### Common Issues

1. **Archive Directory Permissions**
   - Ensure archive directories exist and are writable
   - Check file system permissions

2. **Database Connection Issues**
   - Verify database connectivity
   - Check connection pool settings

3. **Background Task Failures**
   - Monitor background task logs
   - Check system resources

4. **Access Control Issues**
   - Verify user roles and permissions
   - Check organization access settings

### Logging

All operations are logged with structured logging:

```python
logger.info(
    "Audit log created successfully",
    audit_id=audit_log.id,
    action=action,
    user_id=str(user_id),
    organization_id=str(organization_id)
)
```

## Future Enhancements

### Phase 2 Plans

- **Elasticsearch Integration**: Advanced search and analytics
- **S3 Storage**: Cloud-based archive storage
- **Real-time Streaming**: Kafka integration for real-time audit data
- **Advanced Analytics**: Machine learning for anomaly detection

### Phase 3 Plans

- **Multi-Region Support**: Global audit data distribution
- **Advanced Encryption**: Field-level encryption and key rotation
- **Compliance Frameworks**: Built-in compliance reporting
- **Integration APIs**: Third-party system integration

## Conclusion

The Centralized Audit Sink provides a robust, scalable, and secure foundation for enterprise audit requirements. It implements industry best practices for data retention, access control, and compliance while maintaining high performance and reliability.

This implementation completes the **Observability & Audit Baseline** section of Phase 1, providing the foundation for advanced audit capabilities in future phases.
