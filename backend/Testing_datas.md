## Testing Data: Supplier and Contract (aligned with Future_Update.md)

### Supplier: Huawei Technologies

```json
{
  "suppliers": {
    "id": 1001,
    "organization_id": 1,
    "name": "Huawei Technologies Co., Ltd.",
    "industry": "Telecommunications",
    "country": "China",
    "location": "Shenzhen, Guangdong, China",
    "contact_email": "corp@huawei.com",
    "contact_phone": "+86-755-28780808",
    "website": "https://www.huawei.com",
    "company_size": "enterprise",
    "revenue_range": "> $10B",
    "employee_count": 200000,
    "external_id": "HUAWEI-ERP-0001",
    "source_system": "ERP-Seed",
    "risk_score": 68.0,
    "risk_level": "MEDIUM",
    "risk_factors": {
      "financial": { "score": 72, "notes": "Stable revenue, sanctions exposure risk" },
      "operational": { "score": 70, "notes": "Global supply chain, logistics complexity" },
      "compliance": { "score": 60, "notes": "Export control/sanctions monitoring required" },
      "esg": { "score": 65, "notes": "ESG disclosures mixed across sources" }
    },
    "is_active": true,
    "is_watchlisted": false
  },
  "supplier_profiles": [
    {
      "supplier_id": 1001,
      "as_of_date": "2025-06-30",
      "industry": "Telecommunications",
      "region": "APAC",
      "headquarters": "Shenzhen, China",
      "aliases": ["Huawei", "Huawei Technologies"]
    }
  ],
  "supplier_embeddings": [
    {
      "supplier_id": 1001,
      "vector": "EMBEDDING_PLACEHOLDER",
      "model": "text-embedding-3-large",
      "created_at": "2025-09-26T00:00:00Z"
    }
  ],
  "risk_assessments": [
    {
      "id": 50001,
      "entity_type": "supplier",
      "entity_id": 1001,
      "as_of": "2025-09-20",
      "overall_score": 68,
      "category_scores": {
        "financial": 72,
        "esg": 65,
        "operational": 70,
        "compliance": 60
      },
      "method": "enhanced_v1",
      "source": "aggregation_service",
      "inputs_snapshot": {
        "news_sentiment": -0.05,
        "sanctions_hits": 0,
        "financial_trend": "stable"
      },
      "reasoning": "Moderate compliance risk; overall stable operations and financials"
    }
  ]
}
```

### Contract: Network Equipment Supply Agreement (with Huawei)

```json
{
  "contracts": {
    "id": 20001,
    "organization_id": 1,
    "status": "active",
    "type": "Supply Agreement",
    "title": "Network Equipment Supply Agreement",
    "effective_at": "2025-01-15",
    "expires_at": "2027-01-14",
    "auto_renewal": true,
    "renewal_term_months": 12,
    "governing_law": "England & Wales",
    "jurisdiction": "London, UK"
  },
  "contract_parties": [
    { "contract_id": 20001, "role": "buyer", "name": "Acme Corp", "is_internal": true },
    { "contract_id": 20001, "role": "supplier", "name": "Huawei Technologies Co., Ltd.", "is_internal": false, "supplier_id": 1001 }
  ],
  "contract_terms": {
    "contract_id": 20001,
    "payment_terms": { "type": "NET", "days": 60 },
    "penalties": { "late_delivery": "1% per week capped at 5%" },
    "service_levels": { "uptime": "99.9%", "response_time_hours": 4 },
    "liability_cap": { "type": "cap", "amount": 2000000, "currency": "USD" },
    "termination": { "for_convenience": true, "notice_days": 60 }
  },
  "contract_clauses": [
    {
      "id": 30001,
      "contract_id": 20001,
      "type": "limitation_of_liability",
      "risk_flag": "LOW",
      "text_excerpt": "Total liability shall not exceed USD 2,000,000..."
    },
    {
      "id": 30002,
      "contract_id": 20001,
      "type": "data_protection",
      "risk_flag": "MEDIUM",
      "text_excerpt": "Supplier shall comply with applicable data protection laws..."
    },
    {
      "id": 30003,
      "contract_id": 20001,
      "type": "anti_bribery",
      "risk_flag": "LOW",
      "text_excerpt": "Parties shall comply with anti-bribery and corruption laws..."
    },
    {
      "id": 30004,
      "contract_id": 20001,
      "type": "arbitration",
      "risk_flag": "LOW",
      "text_excerpt": "Any dispute shall be settled by arbitration in London..."
    }
  ],
  "clause_embeddings": [
    { "clause_id": 30001, "vector": "EMBEDDING_PLACEHOLDER", "model": "text-embedding-3-large" },
    { "clause_id": 30002, "vector": "EMBEDDING_PLACEHOLDER", "model": "text-embedding-3-large" },
    { "clause_id": 30003, "vector": "EMBEDDING_PLACEHOLDER", "model": "text-embedding-3-large" },
    { "clause_id": 30004, "vector": "EMBEDDING_PLACEHOLDER", "model": "text-embedding-3-large" }
  ],
  "contract_documents": [
    {
      "contract_id": 20001,
      "document_id": 90001,
      "version": 1,
      "filename": "network_equipment_supply_agreement.pdf",
      "extracted": true
    }
  ]
}
```

### Notes
- IDs are illustrative and can be changed to match your environment.
- Dates use ISO-8601; currency is USD for clarity.
- EMBEDDING_PLACEHOLDER indicates where vectors would be stored by your embedding pipeline.
- These examples align with the “Target data model” in `Future_Update.md` and can be converted into SQL/CSV seed data as needed.



