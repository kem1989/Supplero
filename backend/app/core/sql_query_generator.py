"""
SQL Query Generator for converting natural language queries to SQL.
This service replaces Elasticsearch with direct SQL generation for better performance and control.
"""

import structlog
import httpx
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date
import json
import re

from app.core.config import settings
from app.models.contract import Contract, ContractParty, ContractClause
from app.models.supplier import Supplier
from app.models.organization import Organization
from app.models.risk_assessment import RiskAssessment
from app.models.esg_rating import ESGRating
from app.models.financial_metric import FinancialMetric
from app.models.compliance_monitoring import ComplianceMonitoring

logger = structlog.get_logger(__name__)


class QueryType(str, Enum):
    """Types of SQL queries that can be generated"""
    SELECT = "SELECT"
    COUNT = "COUNT"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    COMPLEX = "COMPLEX"


@dataclass
class SQLQueryResult:
    """Result of SQL query generation"""
    query: str
    query_type: QueryType
    parameters: Dict[str, Any]
    tables: List[str]
    confidence: float
    reasoning: str
    estimated_complexity: str  # "simple", "medium", "complex"


class SQLQueryGenerator:
    """Service for converting natural language queries to SQL"""
    
    def __init__(self):
        self.openai_client = httpx.AsyncClient()
        
        # Database schema information for context
        self.schema_context = self._build_schema_context()
        
        # Common query patterns and their SQL equivalents
        self.query_patterns = self._build_query_patterns()
    
    def _build_schema_context(self) -> str:
        """Build context about the database schema for AI"""
        return """
        Database Schema v2.0 (Optimized):
        
        Tables:
        1. organizations (id, name, domain, industry, size, contact_email, contact_phone, address, is_active, created_at, updated_at)
        2. users (id, email, username, hashed_password, first_name, last_name, role, is_active, is_verified, organization_id, created_at, updated_at, last_login)
        3. suppliers (id, name, industry, country, location, contact_email, contact_phone, website, address, company_size, revenue_range, employee_count, current_risk_score, current_risk_level, geopolitical_risk, financial_risk, operational_risk, compliance_risk, esg_risk, external_id, source_system, is_active, is_watchlisted, watchlist_reason, organization_id, created_at, updated_at, last_risk_assessment)
        4. contracts (id, organization_id, title, type, status, contract_value, currency, effective_at, expires_at, auto_renewal, renewal_term_months, governing_law, jurisdiction, payment_terms_days, liability_cap_amount, liability_cap_type, sla_uptime_percent, termination_notice_days, penalty_rate_percent, created_at, updated_at)
        5. contract_parties (id, contract_id, role, name, is_internal, supplier_id)
        6. contract_clauses (id, contract_id, clause_type, risk_level, risk_score, text_excerpt, risk_factors, mitigation_notes, created_at)
        7. risk_assessments (id, entity_type, entity_id, organization_id, assessment_type, overall_score, overall_level, geopolitical_score, financial_score, operational_score, compliance_score, esg_score, methodology, data_sources, key_factors, reasoning, assessor, assessment_date, created_at)
        8. esg_ratings (id, supplier_id, organization_id, provider, rating_period, overall_score, overall_rating, environmental_score, social_score, governance_score, methodology_version, created_at, updated_at)
        9. financial_metrics (id, supplier_id, organization_id, period_start, period_end, currency, revenue, profit_margin, debt_to_equity, current_ratio, quick_ratio, credit_rating, financial_health_score, source, created_at)
        10. compliance_monitoring (id, supplier_id, organization_id, monitoring_type, source, title, description, url, severity_level, risk_score, sentiment_score, match_confidence, status, adjudication, keywords, published_at, created_at)
        
        Key Relationships:
        - users.organization_id -> organizations.id
        - suppliers.organization_id -> organizations.id
        - contracts.organization_id -> organizations.id
        - contract_parties.contract_id -> contracts.id
        - contract_parties.supplier_id -> suppliers.id
        - contract_clauses.contract_id -> contracts.id
        - risk_assessments.organization_id -> organizations.id
        - esg_ratings.supplier_id -> suppliers.id
        - esg_ratings.organization_id -> organizations.id
        - financial_metrics.supplier_id -> suppliers.id
        - financial_metrics.organization_id -> organizations.id
        - compliance_monitoring.supplier_id -> suppliers.id
        - compliance_monitoring.organization_id -> organizations.id
        
        Common Query Patterns:
        - Find suppliers by risk: Filter suppliers by current_risk_level or current_risk_score
        - Find contracts by supplier: JOIN contracts with contract_parties where supplier_id matches
        - Find expiring contracts: Filter contracts by expires_at < NOW()
        - Find contracts by value: Filter contracts by contract_value
        - Find risky clauses: Filter contract_clauses by risk_level IN ('HIGH', 'CRITICAL')
        - Find compliance issues: Filter compliance_monitoring by severity_level = 'HIGH'
        - Find ESG ratings: Query esg_ratings by supplier_id
        - Find financial metrics: Query financial_metrics by supplier_id and period
        - Find risk assessments: Query risk_assessments by entity_type and entity_id
        
        Risk Levels: LOW, MEDIUM, HIGH, CRITICAL
        Monitoring Types: SANCTIONS, NEWS, COMPLIANCE
        Contract Status: ACTIVE, EXPIRED, TERMINATED, PENDING
        """
    
    def _build_query_patterns(self) -> Dict[str, str]:
        """Build common query patterns for quick matching"""
        return {
            "suppliers_by_risk": """
                SELECT s.name, s.current_risk_score, s.current_risk_level, s.industry, s.country
                FROM suppliers s
                WHERE s.organization_id = :organization_id 
                AND s.current_risk_level = :risk_level
                ORDER BY s.current_risk_score DESC
            """,
            "suppliers_with_risk_scores": """
                SELECT s.name, s.current_risk_score, s.current_risk_level, s.geopolitical_risk, s.financial_risk, s.operational_risk, s.compliance_risk, s.esg_risk
                FROM suppliers s
                WHERE s.organization_id = :organization_id
                ORDER BY s.current_risk_score DESC
            """,
            "watchlisted_suppliers": """
                SELECT s.name, s.geopolitical_risk, s.watchlist_reason, s.current_risk_level
                FROM suppliers s
                WHERE s.organization_id = :organization_id 
                AND s.is_watchlisted = true
                ORDER BY s.current_risk_score DESC
            """,
            "contracts_by_supplier": """
                SELECT c.title, c.contract_value, c.currency, c.status, s.name as supplier_name
                FROM contracts c
                JOIN contract_parties cp ON c.id = cp.contract_id
                JOIN suppliers s ON cp.supplier_id = s.id
                WHERE c.organization_id = :organization_id 
                AND cp.supplier_id = :supplier_id
                ORDER BY c.created_at DESC
            """,
            "active_contracts_with_financials": """
                SELECT c.title, c.contract_value, c.currency, c.status, s.name as supplier_name, fm.financial_health_score
                FROM contracts c
                JOIN contract_parties cp ON c.id = cp.contract_id
                JOIN suppliers s ON cp.supplier_id = s.id
                LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id
                WHERE c.organization_id = :organization_id 
                AND c.status = 'ACTIVE'
                ORDER BY c.contract_value DESC
            """,
            "expiring_contracts": """
                SELECT c.title, c.expires_at, c.contract_value, c.currency, cp.name as supplier_name
                FROM contracts c
                LEFT JOIN contract_parties cp ON c.id = cp.contract_id AND cp.role = 'supplier'
                WHERE c.organization_id = :organization_id 
                AND c.expires_at BETWEEN NOW() AND NOW() + INTERVAL '30 days'
                ORDER BY c.expires_at ASC
            """,
            "risky_clauses": """
                SELECT cc.clause_type, cc.risk_level, cc.risk_score, c.title as contract_title, cp.name as supplier_name
                FROM contract_clauses cc
                JOIN contracts c ON cc.contract_id = c.id
                LEFT JOIN contract_parties cp ON c.id = cp.contract_id AND cp.role = 'supplier'
                WHERE c.organization_id = :organization_id 
                AND cc.risk_level IN ('HIGH', 'CRITICAL')
                ORDER BY cc.risk_score DESC, cc.created_at DESC
            """,
            "high_risk_compliance": """
                SELECT s.name as supplier_name, ra.overall_score, ra.overall_level, ra.geopolitical_score, ra.financial_score, ra.operational_score, ra.compliance_score, cm.monitoring_type, cm.title as compliance_title, cm.severity_level, cm.risk_score as compliance_risk_score
                FROM suppliers s
                JOIN risk_assessments ra ON s.id = ra.entity_id AND ra.entity_type = 'supplier'
                JOIN compliance_monitoring cm ON s.id = cm.supplier_id
                WHERE s.organization_id = :organization_id 
                AND (cm.severity_level = 'HIGH' OR ra.overall_level IN ('HIGH', 'CRITICAL'))
                ORDER BY cm.risk_score DESC
            """,
            "suppliers_with_contracts": """
                SELECT DISTINCT s.name, s.industry, s.country, COUNT(c.id) as contract_count
                FROM suppliers s
                JOIN contract_parties cp ON s.id = cp.supplier_id
                JOIN contracts c ON cp.contract_id = c.id
                WHERE s.organization_id = :organization_id
                GROUP BY s.id, s.name, s.industry, s.country
                ORDER BY contract_count DESC
            """
        }
    
    async def generate_sql_query(
        self,
        natural_language_query: str,
        intent_type: str,
        parameters: Dict[str, Any],
        organization_id: int
    ) -> SQLQueryResult:
        """
        Generate SQL query from natural language input.
        
        Args:
            natural_language_query: The original natural language query
            intent_type: The classified intent type
            parameters: Extracted parameters from the query
            organization_id: Organization ID for filtering
            
        Returns:
            SQLQueryResult with generated SQL and metadata
        """
        try:
            logger.info(
                "Generating SQL query from natural language",
                query=natural_language_query,
                intent_type=intent_type,
                parameters=parameters
            )
            
            # First, try to match against common patterns
            pattern_result = self._try_pattern_matching(natural_language_query, intent_type, parameters, organization_id)
            if pattern_result:
                return pattern_result
            
            # If no pattern matches, use AI to generate SQL
            return await self._generate_sql_with_ai(natural_language_query, intent_type, parameters, organization_id)
            
        except Exception as e:
            logger.error("Failed to generate SQL query", error=str(e))
            return self._create_fallback_query(intent_type, parameters, organization_id)
    
    def _analyze_query_requirements(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine what data sources and relationships are needed"""
        query_lower = query.lower()
        
        requirements = {
            "needs_suppliers": False,
            "needs_contracts": False,
            "needs_financial_metrics": False,
            "needs_compliance_monitoring": False,
            "needs_risk_assessments": False,
            "needs_esg_ratings": False,
            "needs_contract_parties": False,
            "needs_contract_clauses": False,
            "filters": [],
            "aggregations": [],
            "complexity": "simple"
        }
        
        # Detect required tables
        if any(word in query_lower for word in ["supplier", "suppliers"]):
            requirements["needs_suppliers"] = True
        
        if any(word in query_lower for word in ["contract", "contracts", "agreement"]):
            requirements["needs_contracts"] = True
        
        if any(word in query_lower for word in ["financial", "revenue", "profit", "debt", "equity", "financial health"]):
            requirements["needs_financial_metrics"] = True
        
        if any(word in query_lower for word in ["compliance", "monitoring", "sanctions", "severity"]):
            requirements["needs_compliance_monitoring"] = True
        
        if any(word in query_lower for word in ["risk assessment", "risk analysis", "overall score"]):
            requirements["needs_risk_assessments"] = True
        
        if any(word in query_lower for word in ["esg", "environmental", "social", "governance"]):
            requirements["needs_esg_ratings"] = True
        
        # Detect if contract relationships are needed
        if requirements["needs_contracts"] and requirements["needs_suppliers"]:
            requirements["needs_contract_parties"] = True
        
        # Detect filters
        if "financial health score" in query_lower and "above" in query_lower:
            requirements["filters"].append("fm.financial_health_score > 70")
        
        if "watchlisted" in query_lower:
            requirements["filters"].append("s.is_watchlisted = true")
        
        if "high" in query_lower and ("risk" in query_lower or "severity" in query_lower):
            requirements["filters"].append("(s.current_risk_level IN ('HIGH', 'CRITICAL') OR cm.severity_level = 'HIGH')")
        
        if "medium" in query_lower and "risk" in query_lower:
            requirements["filters"].append("s.current_risk_level IN ('MEDIUM', 'HIGH')")
        
        # Detect aggregations
        if any(word in query_lower for word in ["count", "how many", "total", "sum", "average", "avg"]):
            requirements["aggregations"].append("count")
        
        # Determine complexity
        table_count = sum([
            requirements["needs_suppliers"],
            requirements["needs_contracts"], 
            requirements["needs_financial_metrics"],
            requirements["needs_compliance_monitoring"],
            requirements["needs_risk_assessments"],
            requirements["needs_esg_ratings"]
        ])
        
        if table_count > 2 or len(requirements["filters"]) > 1:
            requirements["complexity"] = "complex"
        elif table_count > 1 or len(requirements["filters"]) > 0:
            requirements["complexity"] = "medium"
        
        return requirements
    
    def _build_dynamic_query(self, query: str, requirements: Dict[str, Any], organization_id: int) -> Optional[SQLQueryResult]:
        """Build a dynamic query based on analyzed requirements"""
        
        # Build SELECT clause
        select_fields = []
        from_clause = ""
        joins = []
        where_conditions = [f"s.organization_id = :organization_id"]
        
        # Add supplier fields if needed
        if requirements["needs_suppliers"]:
            select_fields.extend([
                "s.name as supplier_name",
                "s.current_risk_score",
                "s.current_risk_level",
                "s.geopolitical_risk",
                "s.financial_risk",
                "s.operational_risk",
                "s.compliance_risk",
                "s.esg_risk"
            ])
            from_clause = "FROM suppliers s"
        
        # Add contract fields if needed
        if requirements["needs_contracts"]:
            select_fields.extend([
                "c.title as contract_title",
                "c.contract_value",
                "c.currency",
                "c.status as contract_status",
                "c.expires_at"
            ])
            
            if not from_clause:
                from_clause = "FROM contracts c"
            else:
                joins.append("JOIN contract_parties cp ON s.id = cp.supplier_id")
                joins.append("JOIN contracts c ON cp.contract_id = c.id")
                where_conditions.append("cp.role = 'supplier'")
        
        # Add financial metrics if needed
        if requirements["needs_financial_metrics"]:
            select_fields.extend([
                "fm.financial_health_score",
                "fm.revenue",
                "fm.profit_margin",
                "fm.credit_rating"
            ])
            joins.append("LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id")
        
        # Add compliance monitoring if needed
        if requirements["needs_compliance_monitoring"]:
            select_fields.extend([
                "cm.title as compliance_title",
                "cm.severity_level",
                "cm.monitoring_type",
                "cm.risk_score as compliance_risk_score"
            ])
            joins.append("LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id")
        
        # Add risk assessments if needed
        if requirements["needs_risk_assessments"]:
            select_fields.extend([
                "ra.overall_score",
                "ra.overall_level",
                "ra.assessment_date"
            ])
            joins.append("LEFT JOIN risk_assessments ra ON s.id = ra.entity_id AND ra.entity_type = 'supplier'")
        
        # Add filters
        where_conditions.extend(requirements["filters"])
        
        # Build the complete query
        if not select_fields:
            return None
        
        query_sql = f"""
            SELECT {', '.join(select_fields)}
            {from_clause}
            {' '.join(joins)}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY s.current_risk_score DESC
            LIMIT 20
        """
        
        return SQLQueryResult(
            query=query_sql,
            query_type=QueryType.JOIN if len(joins) > 0 else QueryType.SELECT,
            parameters={"organization_id": organization_id},
            tables=["suppliers"] + (["contracts", "contract_parties"] if requirements["needs_contracts"] else []) + 
                   (["financial_metrics"] if requirements["needs_financial_metrics"] else []) +
                   (["compliance_monitoring"] if requirements["needs_compliance_monitoring"] else []) +
                   (["risk_assessments"] if requirements["needs_risk_assessments"] else []),
            confidence=0.9,
            reasoning=f"Dynamic query built for {requirements['complexity']} complexity query",
            estimated_complexity=requirements["complexity"]
        )
    
    def _try_pattern_matching(
        self,
        query: str,
        intent_type: str,
        parameters: Dict[str, Any],
        organization_id: int
    ) -> Optional[SQLQueryResult]:
        """Try to match against common query patterns or build dynamic queries"""
        
        query_lower = query.lower()
        
        # First, try dynamic query building for complex queries
        complex_indicators = [
            "financial health", "financial score", "revenue", "profit margin",
            "compliance monitoring", "severity", "sanctions", "monitoring",
            "contracts where supplier", "supplier's financial", "latest revenue",
            "risk assessment", "compliance records", "high-severity"
        ]
        
        if any(indicator in query_lower for indicator in complex_indicators):
            logger.info(f"Detected complex query, attempting dynamic query building: {query}")
            requirements = self._analyze_query_requirements(query)
            dynamic_result = self._build_dynamic_query(query, requirements, organization_id)
            if dynamic_result:
                return dynamic_result
        
        # Skip pattern matching for analytics queries - let AI handle them
        if intent_type == "SQL_ANALYTICS":
            return None
        
        # Pattern matching logic
        if "how many" in query_lower and "contract" in query_lower:
            sql = "SELECT COUNT(*) as contract_count FROM contracts c WHERE c.organization_id = :organization_id"
            return SQLQueryResult(
                query=sql,
                query_type=QueryType.COUNT,
                parameters={"organization_id": organization_id},
                tables=["contracts"],
                confidence=0.95,
                reasoning="Matched contract count pattern",
                estimated_complexity="simple"
            )
        
        elif "how many" in query_lower and "supplier" in query_lower:
            sql = "SELECT COUNT(*) as supplier_count FROM suppliers s WHERE s.organization_id = :organization_id AND s.is_active = true"
            return SQLQueryResult(
                query=sql,
                query_type=QueryType.COUNT,
                parameters={"organization_id": organization_id},
                tables=["suppliers"],
                confidence=0.95,
                reasoning="Matched supplier count pattern",
                estimated_complexity="simple"
            )
        
        elif "supplier" in query_lower and "risk" in query_lower:
            if "watchlisted" in query_lower or "watchlist" in query_lower:
                sql = self.query_patterns["watchlisted_suppliers"]
                return SQLQueryResult(
                    query=sql,
                    query_type=QueryType.SELECT,
                    parameters={"organization_id": organization_id},
                    tables=["suppliers"],
                    confidence=0.95,
                    reasoning="Matched watchlisted supplier pattern",
                    estimated_complexity="simple"
                )
            else:
                sql = self.query_patterns["suppliers_with_risk_scores"]
                return SQLQueryResult(
                    query=sql,
                    query_type=QueryType.SELECT,
                    parameters={"organization_id": organization_id},
                    tables=["suppliers"],
                    confidence=0.95,
                    reasoning="Matched supplier risk pattern",
                    estimated_complexity="simple"
                )
        
        elif "contract" in query_lower and "supplier" in query_lower:
            supplier_name = parameters.get("supplier_name", "%")
            sql = self.query_patterns["contracts_by_supplier"]
            return SQLQueryResult(
                query=sql,
                query_type=QueryType.JOIN,
                parameters={"organization_id": organization_id, "supplier_name": f"%{supplier_name}%"},
                tables=["contracts", "contract_parties"],
                confidence=0.9,
                reasoning="Matched contracts by supplier pattern",
                estimated_complexity="medium"
            )
        
        elif "expiring" in query_lower or "expire" in query_lower:
            date_from = parameters.get("date_from", datetime.now().date())
            date_to = parameters.get("date_to", datetime.now().date())
            sql = self.query_patterns["expiring_contracts"]
            return SQLQueryResult(
                query=sql,
                query_type=QueryType.JOIN,
                parameters={"organization_id": organization_id, "date_from": date_from, "date_to": date_to},
                tables=["contracts", "contract_parties"],
                confidence=0.9,
                reasoning="Matched expiring contracts pattern",
                estimated_complexity="medium"
            )
        
        elif "risky" in query_lower and "clause" in query_lower:
            sql = self.query_patterns["risky_clauses"]
            return SQLQueryResult(
                query=sql,
                query_type=QueryType.JOIN,
                parameters={"organization_id": organization_id},
                tables=["contract_clauses", "contracts", "contract_parties"],
                confidence=0.9,
                reasoning="Matched risky clauses pattern",
                estimated_complexity="medium"
            )
        
        return None
    
    async def _generate_sql_with_ai(
        self,
        natural_language_query: str,
        intent_type: str,
        parameters: Dict[str, Any],
        organization_id: int
    ) -> SQLQueryResult:
        """Generate SQL using AI when pattern matching fails"""
        
        prompt = f"""
        You are a SQL expert specializing in complex multi-table queries for a supplier and contract management system. 
        Convert the following natural language query to SQL.
        
        Database Schema:
        {self.schema_context}
        
        Natural Language Query: {natural_language_query}
        Intent Type: {intent_type}
        Parameters: {json.dumps(parameters, default=str)}
        Organization ID: {organization_id}
        
        CRITICAL REQUIREMENTS:
        1. ALWAYS filter by organization_id = {organization_id} for ALL tables
        2. Use proper SQL syntax for PostgreSQL
        3. Use parameterized queries with :parameter_name syntax
        4. Order results logically (by date DESC, score DESC, etc.)
        5. Limit results to reasonable numbers (20-50 rows) when appropriate
        
        COMPLEX QUERY PATTERNS - When to Use Each Join:
        
        **Supplier + Financial Data Queries:**
        - When query mentions "financial health", "revenue", "profit margin", "financial score"
        - JOIN: suppliers s LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id
        - Filter financial data: WHERE fm.financial_health_score > 70 OR fm.revenue > 1000000
        
        **Supplier + Compliance Monitoring Queries:**
        - When query mentions "compliance", "monitoring", "sanctions", "severity"
        - JOIN: suppliers s LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id
        - Filter compliance: WHERE cm.severity_level = 'HIGH' OR cm.status = 'ACTIVE'
        
        **Contract + Supplier Queries:**
        - When query mentions contracts with supplier information
        - JOIN: contracts c JOIN contract_parties cp ON c.id = cp.contract_id JOIN suppliers s ON cp.supplier_id = s.id
        - Filter by supplier: WHERE cp.role = 'supplier' AND s.name ILIKE '%supplier_name%'
        
        **Contract + Financial Analysis Queries:**
        - When query combines contract data with financial metrics
        - JOIN: contracts c JOIN contract_parties cp ON c.id = cp.contract_id 
               JOIN suppliers s ON cp.supplier_id = s.id 
               LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id
        - Filter: WHERE fm.financial_health_score > 70 AND c.status = 'ACTIVE'
        
        **Risk Assessment + Compliance Queries:**
        - When query combines risk data with compliance monitoring
        - JOIN: suppliers s LEFT JOIN risk_assessments ra ON s.id = ra.entity_id AND ra.entity_type = 'supplier'
               LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id
        - Filter: WHERE (ra.overall_level IN ('HIGH', 'MEDIUM') OR cm.severity_level = 'HIGH')
        
        **Multi-Table Complex Queries:**
        - When query requires supplier + contract + financial + compliance data
        - JOIN: suppliers s 
               LEFT JOIN contract_parties cp ON s.id = cp.supplier_id
               LEFT JOIN contracts c ON cp.contract_id = c.id
               LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id
               LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id
        
        ADVANCED FILTERING PATTERNS:
        
        **Temporal Filters:**
        - "latest revenue" → ORDER BY fm.period_end DESC LIMIT 1 or use window functions
        - "recent assessments" → WHERE ra.assessment_date >= NOW() - INTERVAL '90 days'
        - "expiring contracts" → WHERE c.expires_at BETWEEN NOW() AND NOW() + INTERVAL '30 days'
        
        **Conditional Logic:**
        - "where supplier's financial health score is above 70" → WHERE fm.financial_health_score > 70
        - "suppliers with high risk or compliance issues" → WHERE (s.current_risk_level IN ('HIGH', 'CRITICAL') OR cm.severity_level = 'HIGH')
        - "watchlisted suppliers from China" → WHERE s.is_watchlisted = true AND s.country = 'China'
        
        **Aggregation Patterns (SQL_ANALYTICS intent):**
        - Use AVG(), COUNT(), SUM(), MIN(), MAX() with GROUP BY
        - "average risk score by country" → SELECT s.country, AVG(s.current_risk_score) as avg_risk FROM suppliers s GROUP BY s.country
        - "contract count by supplier" → SELECT s.name, COUNT(c.id) as contract_count FROM suppliers s LEFT JOIN contract_parties cp ON s.id = cp.supplier_id LEFT JOIN contracts c ON cp.contract_id = c.id GROUP BY s.id, s.name
        
        **Complex Selection Patterns:**
        - When query asks for "title, contract value, currency AND supplier name, revenue" → SELECT multiple fields from joined tables
        - Use table aliases: c.title, c.contract_value, c.currency, s.name as supplier_name, fm.revenue
        - Always include the requested fields even if they come from different tables
        
        COMMON QUERY EXAMPLES:
        
        1. "Find contracts where supplier's financial health score is above 70":
           SELECT c.title, c.contract_value, c.currency, s.name as supplier_name, fm.revenue
           FROM contracts c
           JOIN contract_parties cp ON c.id = cp.contract_id
           JOIN suppliers s ON cp.supplier_id = s.id
           LEFT JOIN financial_metrics fm ON s.id = fm.supplier_id
           WHERE c.organization_id = :organization_id 
           AND fm.financial_health_score > 70
           AND cp.role = 'supplier'
           ORDER BY c.contract_value DESC
        
        2. "Suppliers with high-severity compliance issues":
           SELECT s.name, s.current_risk_score, cm.title as compliance_title, cm.severity_level
           FROM suppliers s
           LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id
           WHERE s.organization_id = :organization_id
           AND cm.severity_level = 'HIGH'
           ORDER BY s.current_risk_score DESC
        
        3. "Risk assessment with compliance monitoring":
           SELECT s.name, ra.overall_score, ra.overall_level, cm.title, cm.severity_level
           FROM suppliers s
           LEFT JOIN risk_assessments ra ON s.id = ra.entity_id AND ra.entity_type = 'supplier'
           LEFT JOIN compliance_monitoring cm ON s.id = cm.supplier_id
           WHERE s.organization_id = :organization_id
           AND (ra.overall_level IN ('MEDIUM', 'HIGH') OR cm.severity_level = 'HIGH')
           ORDER BY ra.overall_score DESC
        
        Return ONLY the SQL query, no explanations or markdown formatting.
        """
        
        try:
            logger.info("Sending prompt to OpenAI for SQL generation", prompt=prompt[:500] + "..." if len(prompt) > 500 else prompt)
            
            response = await self.openai_client.post(
                f"{settings.OPENAI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "You are a SQL expert. Return only SQL queries."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                sql_query = result["choices"][0]["message"]["content"].strip()
                
                logger.info("OpenAI response", sql_query=sql_query)
                
                # Clean up the SQL query
                sql_query = self._clean_sql_query(sql_query)
                
                # Analyze the query
                tables = self._extract_tables_from_sql(sql_query)
                query_type = self._determine_query_type(sql_query)
                complexity = self._estimate_complexity(sql_query, tables)
                
                return SQLQueryResult(
                    query=sql_query,
                    query_type=query_type,
                    parameters=parameters,
                    tables=tables,
                    confidence=0.8,
                    reasoning="Generated using AI",
                    estimated_complexity=complexity
                )
            else:
                logger.error("OpenAI API error", status_code=response.status_code, response=response.text)
                return self._create_fallback_query(intent_type, parameters, organization_id)
                
        except Exception as e:
            logger.error("AI SQL generation failed", error=str(e))
            return self._create_fallback_query(intent_type, parameters, organization_id)
    
    def _clean_sql_query(self, sql: str) -> str:
        """Clean and validate SQL query"""
        # Remove any markdown formatting
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove extra whitespace
        sql = ' '.join(sql.split())
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        tables = []
        
        # Simple regex to find table names (basic implementation)
        table_patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        
        return list(set(tables))  # Remove duplicates
    
    def _determine_query_type(self, sql: str) -> QueryType:
        """Determine the type of SQL query"""
        sql_upper = sql.upper()
        
        if 'COUNT(' in sql_upper:
            return QueryType.COUNT
        elif any(func in sql_upper for func in ['SUM(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY']):
            return QueryType.AGGREGATE
        elif 'JOIN' in sql_upper:
            return QueryType.JOIN
        elif len(re.findall(r'JOIN|UNION|SUBQUERY|WITH', sql_upper)) > 1:
            return QueryType.COMPLEX
        else:
            return QueryType.SELECT
    
    def _estimate_complexity(self, sql: str, tables: List[str]) -> str:
        """Estimate query complexity"""
        sql_upper = sql.upper()
        
        complexity_indicators = [
            'JOIN' in sql_upper,
            'UNION' in sql_upper,
            'SUBQUERY' in sql_upper,
            'WITH' in sql_upper,
            'GROUP BY' in sql_upper,
            'HAVING' in sql_upper,
            'WINDOW' in sql_upper,
            len(tables) > 2,
            'JSON' in sql_upper
        ]
        
        complexity_score = sum(complexity_indicators)
        
        if complexity_score >= 4:
            return "complex"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "simple"
    
    def _create_fallback_query(
        self,
        intent_type: str,
        parameters: Dict[str, Any],
        organization_id: int
    ) -> SQLQueryResult:
        """Create a fallback query when generation fails"""
        
        if "ANALYTICS" in intent_type:
            # Check if this is a count query by looking at parameters or using a simple heuristic
            # For now, default to counting contracts since that's more common
            sql = """
                SELECT COUNT(*) as contract_count
                FROM contracts c
                WHERE c.organization_id = :organization_id
            """
            tables = ["contracts"]
        elif "CONTRACT" in intent_type:
            sql = """
                SELECT c.*, cp.name as supplier_name
                FROM contracts c
                LEFT JOIN contract_parties cp ON c.id = cp.contract_id AND cp.role = 'supplier'
                WHERE c.organization_id = :organization_id
                ORDER BY c.created_at DESC
                LIMIT 20
            """
            tables = ["contracts", "contract_parties"]
        elif "SUPPLIER" in intent_type:
            sql = """
                SELECT s.*
                FROM suppliers s
                WHERE s.organization_id = :organization_id
                AND s.is_active = true
                ORDER BY s.risk_score DESC
                LIMIT 20
            """
            tables = ["suppliers"]
        else:
            sql = """
                SELECT c.*, cp.name as supplier_name
                FROM contracts c
                LEFT JOIN contract_parties cp ON c.id = cp.contract_id AND cp.role = 'supplier'
                WHERE c.organization_id = :organization_id
                ORDER BY c.created_at DESC
                LIMIT 20
            """
            tables = ["contracts", "contract_parties"]
        
        return SQLQueryResult(
            query=sql,
            query_type=QueryType.SELECT,
            parameters={"organization_id": organization_id},
            tables=tables,
            confidence=0.5,
            reasoning="Fallback query due to generation failure",
            estimated_complexity="simple"
        )


# Global instance
sql_query_generator = SQLQueryGenerator()
