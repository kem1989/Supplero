# Supplero Database Schema v2.0 - Optimized

## Database Overview

**Database Name**: supplero  
**Schema**: public  
**Total Tables**: 10 (consolidated from 13)  
**Database Type**: PostgreSQL 

This optimized schema eliminates redundancies, improves query performance, and maintains comprehensive supplier risk management capabilities.

---



---

## Table Summary

| Table Name | Purpose | Key Changes | Status |
|------------|---------|-------------|--------|
| `organizations` | Organization/company data | Simplified settings | Active |
| `users` | User accounts and authentication | Unchanged | Active |
| `suppliers` | Main suppliers table | Consolidated risk data | Active |
| `contracts` | Main contracts table | Added value and currency | Active |
| `contract_parties` | Contract participants | Unchanged | Active |
| `contract_clauses` | Contract clauses with risk | Added risk score column | Active |
| `risk_assessments` | Unified risk assessments | Consolidated all risk data | Active |
| `esg_ratings` | ESG ratings and scores | Moved to active tables | Ready |
| `financial_metrics` | Financial performance | Moved to active tables | Ready |
| `compliance_monitoring` | Sanctions, news, compliance | New consolidated table | Ready |

**Removed Tables:**
- `contract_terms` (merged into `contracts`)
- `supplier_risk_assessments` (merged into `risk_assessments`)
- `news_articles` & `sanctions_hits` (consolidated into `compliance_monitoring`)

---

## Detailed Table Schemas

### **1. Organizations Table**
Core organization data - unchanged structure but simplified.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('organizations_id_seq') | Primary key |
| `name` | character varying(255) | NO | | Organization name |
| `domain` | character varying(255) | YES | | Organization domain |
| `industry` | character varying(100) | YES | | Industry classification |
| `size` | character varying(50) | YES | | Organization size |
| `contact_email` | character varying(255) | YES | | Contact email |
| `contact_phone` | character varying(50) | YES | | Contact phone |
| `address` | text | YES | | Physical address |
| `is_active` | boolean | NO | true | Active status |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |
| `updated_at` | timestamp with time zone | NO | now() | Update timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_organizations_domain ON organizations(domain)`
- `INDEX idx_organizations_active ON organizations(is_active)`

---

### **2. Users Table**
User accounts and authentication - structure unchanged.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('users_id_seq') | Primary key |
| `email` | character varying(255) | NO | | User email |
| `username` | character varying(100) | NO | | Username |
| `hashed_password` | character varying(255) | NO | | Hashed password |
| `first_name` | character varying(100) | YES | | First name |
| `last_name` | character varying(100) | YES | | Last name |
| `role` | character varying(50) | NO | | User role |
| `is_active` | boolean | NO | true | Active status |
| `is_verified` | boolean | NO | false | Verification status |
| `organization_id` | integer | NO | | FK to organizations |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |
| `updated_at` | timestamp with time zone | NO | now() | Update timestamp |
| `last_login` | timestamp with time zone | YES | | Last login |

**Indexes:**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_users_email ON users(email)`
- `INDEX idx_users_org ON users(organization_id)`
- `INDEX idx_users_role ON users(role)`

**Foreign Keys:**
- `organization_id` → `organizations.id`

---

### **3. Suppliers Table**
Main suppliers table with consolidated risk information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('suppliers_id_seq') | Primary key |
| `name` | character varying(255) | NO | | Supplier name |
| `industry` | character varying(100) | YES | | Industry classification |
| `country` | character varying(100) | YES | | Country |
| `location` | character varying(255) | YES | | City/location |
| `contact_email` | character varying(255) | YES | | Contact email |
| `contact_phone` | character varying(50) | YES | | Contact phone |
| `website` | character varying(255) | YES | | Website URL |
| `address` | text | YES | | Physical address |
| `company_size` | character varying(50) | YES | | Company size |
| `revenue_range` | character varying(50) | YES | | Revenue range |
| `employee_count` | integer | YES | | Number of employees |
| `current_risk_score` | decimal(5,2) | NO | 0 | Current overall risk score |
| `current_risk_level` | character varying(20) | NO | 'LOW' | Current risk level |
| `geopolitical_risk` | decimal(5,2) | YES | | Geopolitical risk score |
| `financial_risk` | decimal(5,2) | YES | | Financial risk score |
| `operational_risk` | decimal(5,2) | YES | | Operational risk score |
| `compliance_risk` | decimal(5,2) | YES | | Compliance risk score |
| `esg_risk` | decimal(5,2) | YES | | ESG risk score |
| `external_id` | character varying(100) | YES | | External system ID |
| `source_system` | character varying(100) | YES | | Source system |
| `is_active` | boolean | NO | true | Active status |
| `is_watchlisted` | boolean | NO | false | Watchlist status |
| `watchlist_reason` | text | YES | | Watchlist reason |
| `organization_id` | integer | NO | | FK to organizations |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |
| `updated_at` | timestamp with time zone | NO | now() | Update timestamp |
| `last_risk_assessment` | timestamp with time zone | YES | | Last assessment date |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_suppliers_org ON suppliers(organization_id)`
- `INDEX idx_suppliers_risk_level ON suppliers(current_risk_level)`
- `INDEX idx_suppliers_country ON suppliers(country)`
- `INDEX idx_suppliers_industry ON suppliers(industry)`
- `INDEX idx_suppliers_risk_score ON suppliers(current_risk_score)`
- `INDEX idx_suppliers_watchlist ON suppliers(is_watchlisted)`

**Foreign Keys:**
- `organization_id` → `organizations.id`

---

### **4. Contracts Table**
Enhanced contracts table with consolidated terms information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('contracts_id_seq') | Primary key |
| `organization_id` | integer | NO | | FK to organizations |
| `title` | character varying(255) | YES | | Contract title |
| `type` | character varying(100) | YES | | Contract type |
| `status` | character varying(50) | NO | 'ACTIVE' | Contract status |
| `contract_value` | decimal(15,2) | YES | | Contract value |
| `currency` | character varying(3) | YES | 'USD' | Currency code |
| `effective_at` | timestamp with time zone | YES | | Effective date |
| `expires_at` | timestamp with time zone | YES | | Expiration date |
| `auto_renewal` | boolean | NO | false | Auto-renewal flag |
| `renewal_term_months` | integer | YES | | Renewal term months |
| `governing_law` | character varying(100) | YES | | Governing law |
| `jurisdiction` | character varying(100) | YES | | Jurisdiction |
| `payment_terms_days` | integer | YES | | Payment terms in days |
| `liability_cap_amount` | decimal(15,2) | YES | | Liability cap amount |
| `liability_cap_type` | character varying(50) | YES | | Liability cap type |
| `sla_uptime_percent` | decimal(5,2) | YES | | SLA uptime percentage |
| `termination_notice_days` | integer | YES | | Termination notice days |
| `penalty_rate_percent` | decimal(5,2) | YES | | Penalty rate percentage |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |
| `updated_at` | timestamp with time zone | NO | now() | Update timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_contracts_org ON contracts(organization_id)`
- `INDEX idx_contracts_status ON contracts(status)`
- `INDEX idx_contracts_expiry ON contracts(expires_at)`
- `INDEX idx_contracts_type ON contracts(type)`
- `INDEX idx_contracts_value ON contracts(contract_value)`

**Foreign Keys:**
- `organization_id` → `organizations.id`

---

### **5. Contract Parties Table**
Contract participants - structure unchanged.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('contract_parties_id_seq') | Primary key |
| `contract_id` | integer | NO | | FK to contracts |
| `role` | character varying(50) | NO | | Party role |
| `name` | character varying(255) | NO | | Party name |
| `is_internal` | boolean | NO | false | Internal party flag |
| `supplier_id` | integer | YES | | FK to suppliers |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_contract_parties_contract ON contract_parties(contract_id)`
- `INDEX idx_contract_parties_supplier ON contract_parties(supplier_id)`

**Foreign Keys:**
- `contract_id` → `contracts.id`
- `supplier_id` → `suppliers.id`

---

### **6. Contract Clauses Table**
Enhanced contract clauses with risk scoring.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('contract_clauses_id_seq') | Primary key |
| `contract_id` | integer | NO | | FK to contracts |
| `clause_type` | character varying(100) | NO | | Clause type |
| `risk_level` | character varying(20) | YES | | Risk level |
| `risk_score` | decimal(5,2) | YES | | Numerical risk score |
| `text_excerpt` | text | YES | | Clause text excerpt |
| `risk_factors` | text[] | YES | | Array of risk factors |
| `mitigation_notes` | text | YES | | Risk mitigation notes |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_contract_clauses_contract ON contract_clauses(contract_id)`
- `INDEX idx_contract_clauses_risk_level ON contract_clauses(risk_level)`
- `INDEX idx_contract_clauses_type ON contract_clauses(clause_type)`

**Foreign Keys:**
- `contract_id` → `contracts.id`

---

### **7. Risk Assessments Table**
Unified risk assessments for all entities.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('risk_assessments_id_seq') | Primary key |
| `entity_type` | character varying(50) | NO | | Entity type (supplier, contract) |
| `entity_id` | integer | NO | | Entity ID |
| `organization_id` | integer | NO | | FK to organizations |
| `assessment_type` | character varying(50) | NO | | Assessment type |
| `overall_score` | decimal(5,2) | NO | | Overall risk score |
| `overall_level` | character varying(20) | NO | | Overall risk level |
| `geopolitical_score` | decimal(5,2) | YES | | Geopolitical risk |
| `financial_score` | decimal(5,2) | YES | | Financial risk |
| `operational_score` | decimal(5,2) | YES | | Operational risk |
| `compliance_score` | decimal(5,2) | YES | | Compliance risk |
| `esg_score` | decimal(5,2) | YES | | ESG risk |
| `methodology` | character varying(100) | YES | | Assessment methodology |
| `data_sources` | text[] | YES | | Array of data sources |
| `key_factors` | text[] | YES | | Array of key risk factors |
| `reasoning` | text | YES | | Assessment reasoning |
| `assessor` | character varying(100) | YES | | Who performed assessment |
| `assessment_date` | timestamp with time zone | NO | now() | Assessment date |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_risk_assessments_entity ON risk_assessments(entity_type, entity_id)`
- `INDEX idx_risk_assessments_org ON risk_assessments(organization_id)`
- `INDEX idx_risk_assessments_score ON risk_assessments(overall_score)`
- `INDEX idx_risk_assessments_level ON risk_assessments(overall_level)`
- `INDEX idx_risk_assessments_date ON risk_assessments(assessment_date)`

**Foreign Keys:**
- `organization_id` → `organizations.id`

---

### **8. ESG Ratings Table**
Environmental, Social, and Governance ratings.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('esg_ratings_id_seq') | Primary key |
| `supplier_id` | integer | NO | | FK to suppliers |
| `organization_id` | integer | NO | | FK to organizations |
| `provider` | character varying(100) | NO | | Rating provider |
| `rating_period` | date | NO | | Rating period |
| `overall_score` | decimal(5,2) | YES | | Overall ESG score |
| `overall_rating` | character varying(10) | YES | | Overall ESG rating |
| `environmental_score` | decimal(5,2) | YES | | Environmental score |
| `social_score` | decimal(5,2) | YES | | Social score |
| `governance_score` | decimal(5,2) | YES | | Governance score |
| `methodology_version` | character varying(50) | YES | | Methodology version |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |
| `updated_at` | timestamp with time zone | NO | now() | Update timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_esg_ratings_supplier ON esg_ratings(supplier_id)`
- `INDEX idx_esg_ratings_org ON esg_ratings(organization_id)`
- `INDEX idx_esg_ratings_score ON esg_ratings(overall_score)`
- `INDEX idx_esg_ratings_period ON esg_ratings(rating_period)`

**Foreign Keys:**
- `supplier_id` → `suppliers.id`
- `organization_id` → `organizations.id`

---

### **9. Financial Metrics Table**
Financial performance and health metrics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('financial_metrics_id_seq') | Primary key |
| `supplier_id` | integer | NO | | FK to suppliers |
| `organization_id` | integer | NO | | FK to organizations |
| `period_start` | date | NO | | Period start |
| `period_end` | date | NO | | Period end |
| `currency` | character varying(3) | NO | 'USD' | Currency |
| `revenue` | decimal(15,2) | YES | | Revenue |
| `profit_margin` | decimal(5,2) | YES | | Profit margin % |
| `debt_to_equity` | decimal(5,2) | YES | | Debt to equity ratio |
| `current_ratio` | decimal(5,2) | YES | | Current ratio |
| `quick_ratio` | decimal(5,2) | YES | | Quick ratio |
| `credit_rating` | character varying(10) | YES | | Credit rating |
| `financial_health_score` | decimal(5,2) | YES | | Health score |
| `source` | character varying(100) | YES | | Data source |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_financial_metrics_supplier ON financial_metrics(supplier_id)`
- `INDEX idx_financial_metrics_org ON financial_metrics(organization_id)`
- `INDEX idx_financial_metrics_period ON financial_metrics(period_end)`
- `INDEX idx_financial_metrics_health ON financial_metrics(financial_health_score)`

**Foreign Keys:**
- `supplier_id` → `suppliers.id`
- `organization_id` → `organizations.id`

---

### **10. Compliance Monitoring Table**
Consolidated compliance, sanctions, and news monitoring.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NO | nextval('compliance_monitoring_id_seq') | Primary key |
| `supplier_id` | integer | NO | | FK to suppliers |
| `organization_id` | integer | NO | | FK to organizations |
| `monitoring_type` | character varying(50) | NO | | Type: SANCTIONS, NEWS, COMPLIANCE |
| `source` | character varying(100) | NO | | Data source |
| `title` | character varying(500) | NO | | Title/headline |
| `description` | text | YES | | Description |
| `url` | character varying(500) | YES | | URL if applicable |
| `severity_level` | character varying(20) | YES | | Severity level |
| `risk_score` | decimal(5,2) | YES | | Risk impact score |
| `sentiment_score` | decimal(4,2) | YES | | Sentiment (-1 to 1) |
| `match_confidence` | decimal(4,2) | YES | | Match confidence (0 to 1) |
| `status` | character varying(50) | NO | 'ACTIVE' | Status |
| `adjudication` | character varying(50) | YES | | Review status |
| `keywords` | text[] | YES | | Array of keywords |
| `published_at` | timestamp with time zone | YES | | Publication date |
| `created_at` | timestamp with time zone | NO | now() | Creation timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_compliance_monitoring_supplier ON compliance_monitoring(supplier_id)`
- `INDEX idx_compliance_monitoring_org ON compliance_monitoring(organization_id)`
- `INDEX idx_compliance_monitoring_type ON compliance_monitoring(monitoring_type)`
- `INDEX idx_compliance_monitoring_severity ON compliance_monitoring(severity_level)`
- `INDEX idx_compliance_monitoring_published ON compliance_monitoring(published_at)`

**Foreign Keys:**
- `supplier_id` → `suppliers.id`
- `organization_id` → `organizations.id`

---

## Schema Benefits

### **Performance Improvements**
- **Strategic indexes** on all frequently queried columns
- **Extracted JSON fields** into queryable columns for better performance  
- **Consolidated tables** reduce JOIN complexity
- **Proper data types** with appropriate constraints

### **Data Integrity**
- **Single source of truth** for risk data
- **Referential integrity** through proper foreign keys
- **Consistent data types** across related fields
- **Eliminated redundancy** prevents data inconsistencies

### **Query Simplification**
- **Risk data** consolidated in suppliers table for fast access
- **Contract terms** embedded in contracts table
- **Compliance monitoring** unified in single table
- **Fewer JOINs** required for common queries

### **Maintenance Benefits**
- **Reduced complexity** with 10 tables instead of 13
- **Clear data ownership** and relationships
- **Simplified backup/restore** operations
- **Easier schema evolution** and migrations

---

## Migration Notes

**From v1.0 to v2.0:**
1. **Migrate risk data** from multiple tables into consolidated structures
2. **Merge contract terms** into main contracts table
3. **Consolidate compliance data** into unified monitoring table
4. **Add new indexes** for performance optimization
5. **Update application queries** to use new schema structure

**Backward Compatibility:**
- Create database views with old table names for gradual migration
- Maintain data integrity during transition period
- Test performance improvements with production-like data

---

**Schema Version**: 2.0  
**Last Updated**: 2025-09-27  
**Total Tables**: 10 (consolidated from 13)  
**Focus**: Performance, simplicity, data integrity