# Natural Language to SQL Test Prompts - Supplero Database

This document contains test prompts for the Supplero AI Assistant that converts natural language queries into SQL and executes them against the current database structure.

## 🗄️ **Current Database Overview**
- **Total Tables**: 13
- **Tables with Data**: 8 tables
- **Empty Tables**: 5 tables (ready for future data)

### **Tables with Data:**
- `suppliers` (1 record) - Huawei Technologies Co., Ltd.
- `contracts` (1 record) - Network Equipment Supply Agreement
- `contract_clauses` (4 records) - Various clause types with risk flags
- `contract_parties` (2 records) - Acme Corp (buyer) + Huawei (supplier)
- `contract_terms` (1 record) - Payment, SLA, liability terms
- `risk_assessments` (1 record) - Risk assessment for Huawei
- `organizations` (2 records) - Test Organization + Demo Organization
- `users` (4 records) - Various user accounts

### **Empty Tables (Ready for Data):**
- `esg_ratings`, `financial_metrics`, `news_articles`, `sanctions_hits`, `supplier_risk_assessments`

---

## 🎯 **Basic Data Retrieval Queries**

### **Supplier Queries**
```
"Find me all suppliers"
"Show me all suppliers"
"List all suppliers"
"Get suppliers in China"
"Find suppliers with MEDIUM risk level"
"Show me suppliers with risk score above 60"
"Find suppliers in the Telecommunications industry"
"Get suppliers by country: China"
"Show me active suppliers"
"Find suppliers with risk level MEDIUM"
"Get supplier details for Huawei Technologies"
"Show me suppliers with employee count over 100000"
"Find suppliers with revenue over $10B"
```

### **Contract Queries**
```
"Find all contracts"
"Show me all contracts"
"List all contracts"
"Get active contracts"
"Find contracts with status active"
"Show me contracts with Huawei Technologies"
"Find contracts by type: Supply Agreement"
"Get contracts expiring in 2027"
"Show me contract details"
"Find contracts by supplier"
"Get contracts with auto renewal"
"Show me contracts governed by English law"
"Find contracts in London jurisdiction"
```

### **Organization Queries**
```
"Find all organizations"
"Show me all organizations"
"Get organizations in Technology industry"
"Find organizations with size Enterprise"
"Show me organizations with domain test.com"
"Get organizations with size small"
"Find organizations by industry: Technology"
"Show me active organizations"
```

### **User Queries**
```
"Find all users"
"Show me all users"
"Get users with admin role"
"Find users with viewer role"
"Show me users by email domain"
"Get users from test@supplero.com"
"Find users with role admin"
"Show me users created recently"
```

---

## 📊 **Analytics & Reporting Queries**

### **Risk Analysis**
```
"What is the average risk score of suppliers?"
"Show me risk distribution by level"
"Find suppliers with highest risk scores"
"Get risk statistics by country"
"Show me risk trends over time"
"Find suppliers with risk level HIGH"
"Get average risk by industry"
"Show me risk analysis summary"
"Find suppliers with compliance risk below 65"
"Get financial risk scores above 70"
"Show me ESG risk distribution"
"Find suppliers with operational risk above 68"
```

### **Contract Analytics**
```
"How many contracts do we have?"
"What's the total number of contracts?"
"Show me contract statistics"
"Find contracts by expiration date"
"Get contract count by supplier"
"Show me contract trends"
"Find contracts expiring in next 6 months"
"Get contract analysis"
"Show me contracts by status"
"Find contracts by type distribution"
"Get contracts with auto renewal enabled"
"Show me contracts by governing law"
```

### **Supplier Analytics**
```
"How many suppliers do we have?"
"Show me supplier statistics"
"Find suppliers by industry"
"Get supplier count by country"
"Show me supplier distribution"
"Find top suppliers by risk score"
"Get supplier analysis"
"Show me supplier trends"
"Find suppliers by company size"
"Get suppliers by revenue range"
"Show me suppliers by employee count"
"Find suppliers by risk level distribution"
```

---

## 🔍 **Complex Cross-System Queries**

### **Supplier-Contract Analysis**
```
"Find suppliers with active contracts"
"Show me suppliers and their contract details"
"Get suppliers with contracts expiring soon"
"Find contracts for high-risk suppliers"
"Show me supplier risk and contract status"
"Get comprehensive supplier analysis"
"Find suppliers with multiple contracts"
"Show me supplier portfolio analysis"
"Get suppliers with contracts in China"
"Find suppliers with active Supply Agreements"
"Show me contract parties and their roles"
"Get suppliers linked to specific contracts"
```

### **Risk-Contract Integration**
```
"Find risky suppliers with expiring contracts"
"Show me contracts with high-risk clauses"
"Get risk assessment and contract details"
"Find contracts with MEDIUM risk clauses"
"Show me suppliers with compliance issues and their contracts"
"Get risk trends and contract status"
"Find contracts with liability caps over $1M"
"Show me risk factors and contract terms"
```

### **Organization-Based Queries**
```
"Show me suppliers by organization"
"Find contracts for Test Organization"
"Get organization supplier portfolio"
"Find organizations with high-risk suppliers"
"Show me organization contract analysis"
"Get suppliers in Test Organization"
"Find contracts with Demo Organization"
"Show me organization risk summary"
```

---

## ⚖️ **Contract Clause & Terms Analysis**

### **Clause Analysis**
```
"Find high-risk contract clauses"
"Show me contract clauses by type"
"Get clauses with MEDIUM risk flag"
"Find limitation of liability clauses"
"Show me data protection clauses"
"Get anti-bribery clauses"
"Find arbitration clauses"
"Show me clause risk distribution"
"Get clauses by risk level"
"Find clauses for specific contracts"
```

### **Contract Terms Analysis**
```
"Show me contract payment terms"
"Find contracts with NET 60 payment terms"
"Get contracts with 99.9% uptime SLA"
"Find contracts with liability caps"
"Show me contracts with convenience termination"
"Get contracts with penalty clauses"
"Find contracts with specific service levels"
"Show me contract terms analysis"
```

---

## 🔄 **Comparison & Benchmarking Queries**

### **Supplier Comparisons**
```
"Compare suppliers by risk level"
"Show me supplier comparison"
"Find differences between suppliers"
"Compare suppliers by industry"
"Show me risk comparison"
"Get supplier benchmarking"
"Compare suppliers by country"
"Show me performance comparison"
"Find suppliers with similar risk profiles"
"Compare suppliers by company size"
```

### **Contract Comparisons**
```
"Compare contract terms"
"Show me contract comparison"
"Find differences between contracts"
"Compare contracts by type"
"Show me contract terms comparison"
"Get contract benchmarking"
"Compare contracts by status"
"Show me contract analysis comparison"
```

---

## 📈 **Future-Ready Queries (For Empty Tables)**

### **ESG Ratings Queries** *(When data is populated)*
```
"Find suppliers with high ESG ratings"
"Show me ESG scores by supplier"
"Get environmental ratings above 70"
"Find suppliers with governance issues"
"Show me ESG trend analysis"
"Get social responsibility scores"
"Find suppliers with sustainability ratings"
```

### **Financial Metrics Queries** *(When data is populated)*
```
"Show me financial metrics by supplier"
"Find suppliers with strong financial health"
"Get revenue trends by supplier"
"Find suppliers with liquidity issues"
"Show me financial performance analysis"
"Get profitability metrics"
"Find suppliers with debt concerns"
```

### **News Articles Queries** *(When data is populated)*
```
"Find negative news about suppliers"
"Show me news sentiment analysis"
"Get recent news about Huawei"
"Find news articles by supplier"
"Show me news trend analysis"
"Get news sentiment scores"
"Find adverse news events"
```

### **Sanctions Monitoring Queries** *(When data is populated)*
```
"Find suppliers with sanctions hits"
"Show me sanctions monitoring status"
"Get OFAC list matches"
"Find compliance violations"
"Show me sanctions trend analysis"
"Get export control violations"
"Find suppliers under investigation"
```

---

## 🎯 **Advanced Analytical Queries**

### **Multi-Table Joins**
```
"Show me suppliers with their contracts and risk assessments"
"Find contracts with all parties and clauses"
"Get comprehensive supplier portfolio with contracts and risks"
"Show me organization overview with suppliers and contracts"
"Find complete contract analysis with parties, clauses, and terms"
"Get supplier risk assessment with contract details"
"Show me full contract lifecycle analysis"
```

### **Aggregation Queries**
```
"Count suppliers by risk level"
"Sum contract values by supplier"
"Average risk scores by industry"
"Count contracts by status"
"Group suppliers by country and risk level"
"Count contract clauses by risk flag"
"Average employee count by industry"
"Count users by role"
```

### **Date-Based Queries**
```
"Find contracts expiring in the next year"
"Show me contracts created this year"
"Get suppliers with recent risk assessments"
"Find contracts effective in 2025"
"Show me contracts expiring in 2027"
"Get risk assessments from September 2025"
"Find contracts with renewal dates"
```

---

## 🚀 **Testing Scenarios**

### **Scenario 1: Risk Management Dashboard**
```
"Show me all high-risk suppliers with their contracts"
"Find suppliers with compliance risk below 65"
"Get contract clauses with MEDIUM risk flags"
"Show me risk assessment summary for all suppliers"
```

### **Scenario 2: Contract Management**
```
"Find all active contracts with their parties"
"Show me contracts expiring in the next 6 months"
"Get contract terms with liability caps over $1M"
"Find contracts with auto-renewal enabled"
```

### **Scenario 3: Supplier Portfolio Analysis**
```
"Show me complete supplier analysis with contracts and risks"
"Find suppliers in China with Telecommunications industry"
"Get supplier risk scores and contract status"
"Show me organization supplier portfolio"
```

### **Scenario 4: Compliance Monitoring**
```
"Find contracts with data protection clauses"
"Show me anti-bribery compliance across contracts"
"Get risk assessments with compliance scores below 65"
"Find suppliers with sanctions monitoring requirements"
```

---

## 📝 **Notes for Testing**

1. **Current Data**: Most queries will return limited results due to single supplier/contract in the database
2. **Empty Tables**: ESG, financial metrics, news articles, and sanctions queries will return empty results until data is populated
3. **Intent Classification**: These prompts test all 9 intent types in the classifier
4. **SQL Complexity**: Queries range from simple SELECT to complex JOIN operations
5. **Real-world Scenarios**: Prompts simulate actual business use cases

---

**Total Test Prompts**: 150+ natural language queries covering all aspects of the current database structure and future data scenarios.