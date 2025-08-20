# Supplier Risk Management Implementation

This document describes the implementation of Month 3, Step 1: Supplier Data Ingestion & Basic Profiling for the Supplero application.

## Overview

The supplier risk management system provides:
- Supplier profile creation and management
- Automated risk assessment using rule-based scoring
- Risk monitoring and alerting
- Integration-ready architecture for future ERP/P2P connectors

## API Endpoints

### 1. Create Supplier Profile
- **Endpoint**: `POST /api/v1/suppliers/profile`
- **Purpose**: Ingest basic supplier information and create initial risk profile
- **Input**: Basic supplier info (name, industry, location, etc.)
- **Output**: Complete supplier profile with calculated risk score

### 2. Get Supplier Risk Assessment
- **Endpoint**: `GET /api/v1/suppliers/{id}/risk`
- **Purpose**: Retrieve current risk score and assessment details
- **Output**: Risk score, level, factors, and recommendations

### 3. List Suppliers
- **Endpoint**: `GET /api/v1/suppliers/`
- **Purpose**: List all suppliers with pagination and filtering
- **Query Parameters**: 
  - `page`: Page number
  - `page_size`: Items per page
  - `search`: Search by name or industry
  - `risk_level`: Filter by risk level
  - `industry`: Filter by industry
  - `watchlisted`: Filter by watchlist status

### 4. Get Supplier Details
- **Endpoint**: `GET /api/v1/suppliers/{id}`
- **Purpose**: Retrieve complete supplier information

### 5. Update Supplier
- **Endpoint**: `PUT /api/v1/suppliers/{id}`
- **Purpose**: Update supplier information

## Data Models

### Supplier Model
- Basic information (name, industry, location, country)
- Contact details (email, phone, website, address)
- Business information (size, revenue, employee count)
- Risk assessment (score, level, factors)
- Integration data (external ID, source system)
- Status flags (active, watchlisted)

### SupplierRiskAssessment Model
- Historical risk assessments
- Assessment method and data sources
- Risk factor breakdown
- Metadata and notes

## Risk Assessment Engine

### Rule-Based Scoring
The system uses a rule-based approach for initial risk assessment:

1. **Industry Risk** (0-30 points): Higher risk industries get higher scores
2. **Company Size** (0-25 points): Smaller companies get higher risk scores
3. **Country Risk** (0-20 points): Geographic risk factors
4. **Employee Count** (0-15 points): Smaller workforce = higher risk
5. **Revenue Risk** (0-10 points): Lower revenue = higher risk
6. **Data Completeness** (0-10 points): Penalty for missing information

### Risk Levels
- **LOW**: 0-39 points
- **MEDIUM**: 40-59 points
- **HIGH**: 60-79 points
- **CRITICAL**: 80-100 points

### Industry-Specific Risk Factors
- **High Risk**: Pharmaceuticals, Healthcare, Financial Services, Defense
- **Medium Risk**: Manufacturing, Energy, Construction, Aviation
- **Low Risk**: Technology, Retail, Consulting, Education

## Usage Examples

### Creating a Supplier Profile
```bash
curl -X POST "http://localhost:8000/api/v1/suppliers/profile" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Manufacturing",
    "industry": "manufacturing",
    "location": "Detroit, MI",
    "country": "US",
    "company_size": "medium",
    "employee_count": 250,
    "revenue_range": "10-50 million",
    "organization_id": 1
  }'
```

### Getting Risk Assessment
```bash
curl "http://localhost:8000/api/v1/suppliers/1/risk"
```

### Listing Suppliers with Filters
```bash
curl "http://localhost:8000/api/v1/suppliers/?industry=manufacturing&risk_level=HIGH&page=1&page_size=10"
```

## Testing

Run the test script to verify functionality:
```bash
cd backend
python test_supplier_api.py
```

## Future Enhancements

### Month 3 (Current)
- [x] Basic supplier profiling and risk assessment
- [ ] Integration connectors for ERP/P2P systems
- [ ] Enhanced risk models with external data sources

### Month 4
- [ ] Advanced risk analytics and benchmarking
- [ ] Machine learning risk models
- [ ] Real-time risk monitoring and alerts
- [ ] Compliance framework integration

## Architecture Notes

- **Audit Trail**: All supplier operations are logged with full audit trail
- **Multi-tenancy**: Suppliers are scoped to organizations
- **Extensible**: Risk assessment engine designed for easy enhancement
- **Integration Ready**: External ID fields prepared for ERP system integration

## Dependencies

- FastAPI for API endpoints
- SQLAlchemy for database models
- Pydantic for data validation
- Structured logging for observability
- Audit system for compliance tracking








