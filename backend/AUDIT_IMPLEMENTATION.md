# Audit & Redaction Implementation

## Overview

This document describes the comprehensive implementation of **Prompt/output redaction policies and secure storage controls** for the Supplero AI-Powered Procurement Platform. This implementation forms the core of the **Observability & Audit Baseline** as outlined in Phase 1 of the project scope.

## 🎯 **Features Implemented**

### 1. **Data Redaction Service** (`app/core/redaction.py`)
- **Multi-level redaction** with configurable sensitivity levels (LOW, MEDIUM, HIGH, CRITICAL)
- **Pattern-based detection** for PII, financial data, legal terms, and business information
- **Specialized redaction** for AI prompts and responses
- **JSON structure redaction** with sensitive key detection
- **Integrity verification** with redaction summaries

### 2. **Centralized Audit Service** (`app/core/audit.py`)
- **Comprehensive activity tracking** for all user and system actions
- **AI request monitoring** with cost and performance tracking
- **Async processing** with batch operations for high performance
- **Retention policies** with configurable cleanup (default: 7 years)
- **Organization-scoped access** with role-based filtering

### 3. **Secure Storage Service** (`app/core/secure_storage.py`)
- **Encrypted file storage** using Fernet symmetric encryption
- **Content integrity verification** with SHA-256 hashing and HMAC
- **Access control** based on organization membership
- **Secure deletion** with data overwriting before removal
- **Metadata encryption** for additional security

### 4. **Audit API Endpoints** (`app/api/v1/audit.py`)
- **Audit log retrieval** with filtering and pagination
- **AI request monitoring** for compliance and cost tracking
- **Export capabilities** in CSV and JSON formats
- **Summary statistics** for reporting and analytics
- **Health monitoring** for service status

## 🚀 **Quick Start**

### Basic Redaction Usage

```python
from app.core.redaction import get_redactor, RedactionLevel

redactor = get_redactor()

# Redact sensitive text
sensitive_text = "My email is john@company.com and SSN is 123-45-6789"
redacted_text = redactor.redact_text(sensitive_text, RedactionLevel.HIGH)
# Result: "My email is [EMAIL_REDACTED] and SSN is [SSN_REDACTED]"

# Redact JSON data
sensitive_json = {"user_email": "admin@company.com", "api_key": "sk-123..."}
redacted_json = redactor.redact_json(sensitive_json, RedactionLevel.CRITICAL)
```

### Audit Logging

```python
from app.core.audit import log_user_action, log_ai_interaction

# Log user actions
await log_user_action(
    action="contract_uploaded",
    organization_id="org-123",
    user_id="user-456",
    resource_type="contract",
    resource_id="contract-789",
    details={"filename": "contract.pdf", "size": 1024000}
)

# Log AI interactions
await log_ai_interaction(
    request_type="contract_analysis",
    organization_id="org-123",
    user_id="user-456",
    model_used="gpt-4",
    prompt_tokens=150,
    completion_tokens=300,
    total_tokens=450,
    processing_time_ms=2500,
    cost_usd=0.009
)
```

### Secure File Storage

```python
from app.core.secure_storage import get_secure_storage

storage = get_secure_storage()

# Store file securely
result = await storage.store_file(
    content=file_bytes,
    filename="contract.pdf",
    content_type="contract",
    organization_id="org-123",
    metadata={"contract_type": "NDA"},
    encryption_level="high"
)

# Retrieve file securely
file_data = await storage.retrieve_file(
    file_id=result["file_id"],
    organization_id="org-123",
    content_type="contract"
)
```

## 📊 **Redaction Levels & Patterns**

### Redaction Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **NONE** | No redaction | Public information |
| **LOW** | Basic PII | General logging |
| **MEDIUM** | Financial data, contracts | Standard audit logs |
| **HIGH** | Legal documents, sensitive contracts | Compliance reporting |
| **CRITICAL** | Trade secrets, classified information | Security events |

### Detected Patterns

#### Personal Information
- **Email addresses**: `john.doe@company.com` → `[EMAIL_REDACTED]`
- **Phone numbers**: `555-123-4567` → `[PHONE_REDACTED]`
- **SSN**: `123-45-6789` → `[SSN_REDACTED]`

#### Financial Data
- **Monetary amounts**: `$50,000` → `[AMOUNT_REDACTED]`
- **Credit cards**: `1234-5678-9012-3456` → `[CARD_REDACTED]`
- **Bank accounts**: `123456789` → `[ACCOUNT_REDACTED]`

#### Business Information
- **API keys**: `sk-1234567890abcdef` → `[API_KEY_REDACTED]`
- **Confidential terms**: `confidential` → `[SENSITIVE_TERM_REDACTED]`
- **Legal terms**: `NDA` → `[LEGAL_TERM_REDACTED]`

## 🔒 **Security Features**

### Encryption
- **AES-256 encryption** for file content using Fernet
- **Key management** with environment variable support
- **Secure key generation** with cryptographic randomness

### Integrity Protection
- **SHA-256 hashing** for content verification
- **HMAC signatures** for tamper detection
- **Salt generation** for enhanced security

### Access Control
- **Organization isolation** preventing cross-organization access
- **User context tracking** for audit trails
- **Role-based permissions** for audit log access

## 📈 **Performance & Scalability**

### Async Processing
- **Batch operations** for audit log creation (100 logs per batch)
- **Non-blocking queues** for high-throughput scenarios
- **Background processing** with configurable workers

### Storage Optimization
- **Compressed metadata** storage
- **Efficient indexing** for quick retrieval
- **Configurable retention** policies

### Monitoring & Metrics
- **Real-time statistics** for storage usage
- **Performance tracking** for AI requests
- **Cost monitoring** for OpenAI usage

## 🧪 **Testing**

### Run the Test Suite

```bash
cd backend
python test_audit_redaction.py
```

This comprehensive test suite covers:
- Data redaction functionality
- Secure storage operations
- Audit service operations
- Redaction pattern detection
- Integration testing

### Manual Testing

```bash
# Start the application
make dev

# Test audit endpoints
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/audit/logs
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/audit/health
```

## 🔧 **Configuration**

### Environment Variables

```bash
# Encryption key (base64 encoded)
SUPPLERO_ENCRYPTION_KEY=your_base64_encoded_key_here

# Storage path
STORAGE_PATH=./uploads

# Log level
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
```

### Redaction Rules

Custom redaction rules can be added in `app/core/redaction.py`:

```python
RedactionRule(
    pattern=r'\b(custom_pattern)\b',
    replacement='[CUSTOM_REDACTED]',
    description='Custom sensitive pattern',
    sensitivity_level=RedactionLevel.MEDIUM
)
```

## 📊 **API Endpoints**

### Audit Logs
- `GET /api/v1/audit/logs` - Retrieve audit logs with filtering
- `GET /api/v1/audit/logs/summary` - Get audit summary statistics
- `GET /api/v1/audit/logs/export` - Export audit logs in CSV/JSON

### AI Requests
- `GET /api/v1/audit/ai-requests` - Retrieve AI request logs

### Health & Status
- `GET /api/v1/audit/health` - Service health check

## 🔍 **Monitoring & Analysis**

### Key Metrics
1. **Redaction Effectiveness**
   - Patterns detected and redacted
   - False positive/negative rates
   - Redaction coverage by sensitivity level

2. **Storage Security**
   - Encryption coverage
   - Access control effectiveness
   - Integrity verification success rates

3. **Audit Completeness**
   - Action coverage percentage
   - Log retention compliance
   - Export and reporting capabilities

### Compliance Features
- **SOC 2 readiness** with comprehensive audit trails
- **GDPR compliance** with data redaction and retention
- **Industry standards** for financial and legal data protection

## 🚨 **Troubleshooting**

### Common Issues

1. **Encryption Key Problems**
   - Check `SUPPLERO_ENCRYPTION_KEY` environment variable
   - Verify key format (base64 encoded)
   - Regenerate key if corrupted

2. **Storage Permission Issues**
   - Verify `STORAGE_PATH` directory permissions
   - Check organization isolation
   - Validate user access rights

3. **Redaction Performance**
   - Monitor pattern matching efficiency
   - Adjust sensitivity levels as needed
   - Cache frequently used patterns

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

## 🔄 **Next Steps**

This implementation provides the foundation for:

1. **Advanced Compliance** - SOC 2 Type II certification
2. **Real-time Monitoring** - Live audit trail visualization
3. **Machine Learning** - Pattern detection improvement
4. **Integration** - SIEM and compliance tool integration
5. **Automation** - Automated compliance reporting

## 📚 **References**

- [Cryptography Documentation](https://cryptography.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Enterprise Security Best Practices](https://owasp.org/www-project-top-ten/)
- [SOC 2 Compliance Guide](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/soc2.html)

## 🏆 **Success Metrics**

### Phase 1 Goals
- ✅ **Prompt/output redaction policies** implemented
- ✅ **Secure storage controls** with encryption
- ✅ **Centralized audit sink** with retention policies
- ✅ **Comprehensive logging** across all services
- ✅ **API endpoints** for audit access and export

### Compliance Readiness
- **SOC 2**: Ready for Type I assessment
- **GDPR**: Data protection measures implemented
- **Industry Standards**: Financial and legal compliance ready

This implementation establishes Supplero as an enterprise-grade platform with world-class security, audit, and compliance capabilities. 