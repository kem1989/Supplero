# Complete Sample Data for Supplero Database Schema v2.0



## Suppliers Table
```sql
INSERT INTO suppliers VALUES (
    1,
    'Huawei Technologies Co., Ltd.',
    'Telecommunications',
    'China',
    'Shenzhen',
    'contact@huawei.com',
    '+86-755-28560808',
    'https://www.huawei.com',
    'Huawei Base, Bantian, Longgang District, Shenzhen 518129, China',
    'Large',
    'Over $100B',
    195000,
    72.50,
    'MEDIUM',
    85.00,
    65.00,
    68.00,
    75.00,
    70.00,
    'HW001',
    'CRM_SYSTEM',
    true,
    true,
    'Geopolitical concerns and regulatory restrictions in US/EU markets',
    1,
    '2024-03-01 10:00:00+00',
    '2024-09-15 16:20:00+00',
    '2024-09-15 16:20:00+00'
);
```

## Contracts Table
```sql
INSERT INTO contracts VALUES (
    1,
    1,
    'Network Equipment Supply Agreement',
    'Supply Agreement',
    'ACTIVE',
    15750000.00,
    'USD',
    '2024-01-01 00:00:00+00',
    '2026-12-31 23:59:59+00',
    false,
    24,
    'English Law',
    'London',
    60,
    5000000.00,
    'Annual Contract Value',
    99.90,
    90,
    0.50,
    '2024-01-01 09:00:00+00',
    '2024-09-20 11:15:00+00'
);
```

## Contract Parties Table
```sql
INSERT INTO contract_parties VALUES (
    1,
    1,
    'buyer',
    'Acme Corporation',
    true,
    null
);
```

## Contract Clauses Table
```sql
INSERT INTO contract_clauses VALUES (
    1,
    1,
    'limitation_of_liability',
    'MEDIUM',
    65.00,
    'Liability is limited to the annual contract value of $5M, excluding certain categories of damages...',
    ARRAY['financial_exposure', 'exclusion_scope', 'cap_adequacy'],
    'Consider additional insurance coverage for excluded damages',
    '2024-01-01 09:30:00+00'
);
```

## Risk Assessments Table
```sql
INSERT INTO risk_assessments VALUES (
    1,
    'supplier',
    1,
    1,
    'comprehensive',
    72.50,
    'MEDIUM',
    85.00,
    65.00,
    68.00,
    75.00,
    70.00,
    'Multi-factor Risk Model v2.1',
    ARRAY['regulatory_data', 'financial_reports', 'news_analysis', 'geopolitical_indices'],
    ARRAY['us_export_restrictions', 'eu_5g_bans', 'technology_transfer_concerns', 'market_access_limitations'],
    'Elevated geopolitical risk due to ongoing regulatory restrictions in key Western markets, offset by strong financial performance and operational capabilities',
    'AI_SYSTEM',
    '2024-09-15 16:20:00+00',
    '2024-09-15 16:25:00+00'
);
```

## ESG Ratings Table
```sql
INSERT INTO esg_ratings VALUES (
    1,
    1,
    1,
    'MSCI',
    '2024-06-30',
    6.2,
    'BBB',
    5.8,
    6.8,
    6.0,
    'MSCI ESG Research v3.2',
    '2024-07-15 12:00:00+00',
    '2024-07-15 12:00:00+00'
);
```

## Financial Metrics Table
```sql
INSERT INTO financial_metrics VALUES (
    1,
    1,
    1,
    '2023-01-01',
    '2023-12-31',
    'USD',
    99900000000.00,
    9.85,
    0.32,
    1.85,
    1.22,
    'A-',
    78.50,
    'Annual_Report_2023',
    '2024-03-20 14:30:00+00'
);
```

## Compliance Monitoring Table
```sql
INSERT INTO compliance_monitoring VALUES (
    1,
    1,
    1,
    'SANCTIONS',
    'US_BIS_Entity_List',
    'Huawei Technologies Co Ltd added to Entity List',
    'US Bureau of Industry and Security adds Huawei and affiliates to Entity List restricting access to US technology and components',
    'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list',
    'HIGH',
    85.00,
    null,
    0.95,
    'ACTIVE',
    'CONFIRMED',
    ARRAY['export_controls', 'technology_transfer', 'national_security'],
    '2019-05-16 00:00:00+00',
    '2024-01-15 10:00:00+00'
);
```