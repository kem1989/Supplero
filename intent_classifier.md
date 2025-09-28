# Intent Classifier Documentation v2.0 - Supplero AI Assistant

## Overview

The Intent Classifier converts natural language queries into structured intents for SQL generation. This streamlined version uses 5 focused intent types with context parameters to reduce classification complexity while maintaining comprehensive coverage.

---

## Intent Types

### **1. SQL_QUERY**
- **Purpose**: Standard data retrieval queries
- **Description**: Primary intent for most data requests - covers simple to moderately complex SELECT operations
- **Use Cases**: Basic searches, filters, lookups, standard business queries
- **Examples**:
  - "Find all suppliers in China"
  - "Show me active contracts with Huawei"
  - "Get users with admin role"
  - "List contracts expiring in 2025"

### **2. SQL_ANALYTICS**
- **Purpose**: Analytical queries with aggregations, calculations, and reporting
- **Description**: Queries involving mathematical operations, grouping, trends, and statistical analysis
- **Use Cases**: Aggregations, statistics, trend analysis, performance metrics, dashboards
- **Examples**:
  - "What's the average risk score by country?"
  - "Show me contract count trends over time"
  - "Get supplier risk distribution by industry"
  - "Count high-risk contracts by status"

### **3. COMPARISON_QUERY**
- **Purpose**: Comparative analysis between entities
- **Description**: Side-by-side comparisons, benchmarking, and difference analysis
- **Use Cases**: Supplier benchmarking, contract comparisons, risk analysis, performance comparisons
- **Examples**:
  - "Compare risk scores between Chinese and European suppliers"
  - "Show differences in contract terms by supplier"
  - "Benchmark our suppliers against industry standards"
  - "Compare ESG ratings across supplier portfolio"

### **4. GENERATE_EXPLANATION**
- **Purpose**: Explanatory content based on data analysis
- **Description**: Contextual explanations, reasoning, and educational responses about data
- **Use Cases**: Risk assessment explanations, methodology clarifications, business context
- **Examples**:
  - "Explain why this supplier has a high risk score"
  - "Tell me about risk factors in telecommunications industry"
  - "Explain the contract clause risk methodology"
  - "Why are Chinese suppliers flagged for compliance?"

### **5. GENERATE_INSIGHTS**
- **Purpose**: Strategic insights, recommendations, and actionable intelligence
- **Description**: Business intelligence, trend interpretation, and strategic recommendations
- **Use Cases**: Strategic recommendations, business insights, risk mitigation, portfolio optimization
- **Examples**:
  - "Provide insights on supplier portfolio optimization"
  - "What trends should we watch in contract risk?"
  - "Give recommendations for reducing supply chain risk"
  - "Analyze emerging risks in our supplier base"

---

## Context Parameters

Context parameters provide additional specificity without requiring separate intents:

### **Domain Context**
- `suppliers`: Supplier-focused queries
- `contracts`: Contract-focused queries  
- `organizations`: Organization management
- `users`: User management
- `risk`: Risk assessment and analysis
- `compliance`: Compliance and regulatory

### **Query Modifiers**
- `time_scope`: today, this_week, this_month, this_year, custom_range
- `risk_level`: low, medium, high, critical
- `status`: active, inactive, expired, pending
- `filters`: geographic, industry, size, temporal

---

## Classification Rules

### **Primary Decision Flow**
1. **Asking for explanations or reasoning?** → `GENERATE_EXPLANATION`
2. **Asking for insights, recommendations, or strategy?** → `GENERATE_INSIGHTS`
3. **Explicitly comparing multiple entities?** → `COMPARISON_QUERY`
4. **Involves calculations, aggregations, or statistics?** → `SQL_ANALYTICS`
5. **Standard data retrieval request?** → `SQL_QUERY`

### **Intent Selection Examples**

| Query Pattern | Intent | Context |
|---------------|--------|---------|
| "Find all suppliers" | SQL_QUERY | domain=suppliers |
| "Count contracts by status" | SQL_ANALYTICS | metrics=count |
| "Compare supplier risk scores" | COMPARISON_QUERY | entities=suppliers |
| "Why is this contract risky?" | GENERATE_EXPLANATION | type=reasoning |
| "Give portfolio insights" | GENERATE_INSIGHTS | type=strategic |

---

## Multi-Part Query Detection

Complex queries are decomposed into primary and secondary intents:

**Pattern**: "Find high-risk suppliers in China, then explain why Chinese suppliers have higher risk"
- **Primary**: `SQL_QUERY` (domain=suppliers, filters=geographic+risk)
- **Secondary**: `GENERATE_EXPLANATION` (type=reasoning)

---

## Expected Distribution

- **SQL_QUERY**: ~55% (primary data retrieval)
- **SQL_ANALYTICS**: ~25% (reporting and analytics)
- **COMPARISON_QUERY**: ~10% (benchmarking)
- **GENERATE_EXPLANATION**: ~7% (educational)
- **GENERATE_INSIGHTS**: ~3% (strategic)

---

## Test Examples by Intent

### **SQL_QUERY**
- "Find all suppliers"
- "Show me contracts with Huawei"
- "Get active users"
- "List high-risk suppliers in China"

### **SQL_ANALYTICS** 
- "What's the average risk score?"
- "Count contracts by status"
- "Show supplier risk distribution"
- "Get monthly creation trends"

### **COMPARISON_QUERY**
- "Compare suppliers by risk score"
- "Show contract term differences"
- "Benchmark supplier performance"
- "Compare risk levels by country"

### **GENERATE_EXPLANATION**
- "Explain why this supplier is risky"
- "Tell me about risk methodology"
- "Why do we flag certain clauses?"
- "Explain compliance requirements"

### **GENERATE_INSIGHTS**
- "Provide portfolio insights"
- "What trends should we watch?"
- "Give risk mitigation recommendations"
- "Analyze emerging supplier risks"

---

**Version**: 2.0  
**Last Updated**: 2025-09-27  
**Total Intent Types**: 5 (simplified from 9)  
**Focus**: Reduced complexity, improved accuracy