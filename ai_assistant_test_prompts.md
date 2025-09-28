# AI Assistant Test Prompts for Natural Language to SQL

These prompts are designed to test the AI Assistant's ability to convert natural language queries into SQL and retrieve data from the populated testing database.

## Test Prompt 1: Basic Supplier Information Query
**Prompt:** "Show me all suppliers with their current risk scores and risk levels"

**Expected SQL:** 
```sql
SELECT name, current_risk_score, current_risk_level FROM suppliers;
```

**Expected Result:** 
- Huawei Technologies Co., Ltd. with risk score 72.50 and level MEDIUM

**Test Purpose:** 
- Tests basic table selection and column mapping
- Verifies understanding of risk assessment fields
- Simple query without complex joins or filters

---

## Test Prompt 2: Complex Risk Analysis Query
**Prompt:** "Find suppliers that are watchlisted and show their geopolitical risk scores along with the reasons for being on the watchlist"

**Expected SQL:**
```sql
SELECT name, geopolitical_risk, watchlist_reason, is_watchlisted 
FROM suppliers 
WHERE is_watchlisted = true;
```

**Expected Result:**
- Huawei Technologies Co., Ltd. with geopolitical risk 85.00 and watchlist reason about regulatory restrictions

**Test Purpose:**
- Tests boolean field filtering (is_watchlisted = true)
- Verifies understanding of multiple column selection
- Tests specific risk category queries

---

## Test Prompt 3: Contract and Financial Analysis Query
**Prompt:** "Show me all active contracts with their values and the suppliers' financial health scores"

**Expected SQL:**
```sql
SELECT 
    c.title as contract_title,
    c.contract_value,
    c.currency,
    c.status,
    s.name as supplier_name,
    fm.financial_health_score
FROM contracts c
JOIN contract_parties cp ON c.id = cp.contract_id
JOIN suppliers s ON cp.supplier_id = s.id
JOIN financial_metrics fm ON s.id = fm.supplier_id
WHERE c.status = 'ACTIVE';
```

**Expected Result:**
- Network Equipment Supply Agreement with $15.75M USD value and financial health score 78.50

**Test Purpose:**
- Tests complex JOIN operations across multiple tables
- Verifies understanding of table relationships
- Tests filtering on contract status
- Tests aggregation of financial and contract data

---

## Test Prompt 4: Advanced Risk and Compliance Query
**Prompt:** "Find suppliers with high-risk compliance issues and show their overall risk assessment details along with any sanctions or regulatory concerns"

**Expected SQL:**
```sql
SELECT 
    s.name as supplier_name,
    ra.overall_score,
    ra.overall_level,
    ra.geopolitical_score,
    ra.financial_score,
    ra.operational_score,
    ra.compliance_score,
    cm.monitoring_type,
    cm.title as compliance_title,
    cm.severity_level,
    cm.risk_score as compliance_risk_score
FROM suppliers s
JOIN risk_assessments ra ON s.id = ra.entity_id AND ra.entity_type = 'supplier'
JOIN compliance_monitoring cm ON s.id = cm.supplier_id
WHERE cm.severity_level = 'HIGH' OR ra.overall_level IN ('HIGH', 'CRITICAL');
```

**Expected Result:**
- Huawei Technologies Co., Ltd. with comprehensive risk breakdown and HIGH severity sanctions from US BIS Entity List

**Test Purpose:**
- Tests complex multi-table JOINs with conditional logic
- Verifies understanding of entity relationships (supplier to risk_assessments)
- Tests OR conditions in WHERE clauses
- Tests aggregation of risk and compliance data
- Most complex query to test advanced SQL generation capabilities

---

## Additional Test Scenarios (Optional)

### Test Prompt 5: ESG and Sustainability Query
**Prompt:** "Show me suppliers' ESG ratings broken down by environmental, social, and governance scores"

### Test Prompt 6: Contract Clause Risk Analysis
**Prompt:** "Find contracts with high-risk clauses and show the specific risk factors identified"

### Test Prompt 7: Time-based Analysis
**Prompt:** "Show me suppliers whose risk assessments were updated in the last 6 months"

### Test Prompt 8: Aggregate Analysis
**Prompt:** "What is the average risk score by industry and country for all suppliers?"

---

## Testing Instructions

1. **Test each prompt individually** through the AI Assistant interface
2. **Verify the SQL generated** matches the expected structure
3. **Check the results returned** match the expected data
4. **Test error handling** by trying variations or invalid queries
5. **Document any issues** with SQL generation or data retrieval

## Success Criteria

- ✅ AI generates syntactically correct SQL
- ✅ SQL queries return expected results
- ✅ Complex JOINs are handled correctly
- ✅ Boolean and conditional logic works
- ✅ Table relationships are understood
- ✅ Column names are mapped correctly
- ✅ Filtering and aggregation functions properly
