"""
Simplified SQL-based execution handlers for AI Assistant.
All queries go through SQL generation - no more Elasticsearch dependencies.
"""

import structlog
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.models.user import User
from .base_handler import BaseHandler

logger = structlog.get_logger(__name__)


async def execute_sql_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute generic SQL query - the main handler for most queries"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "sql_query",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting SQL query with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.SQL_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        results = []
        for row in rows:
            result_dict = dict(row._mapping)
            results.append(result_dict)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"SQL query completed in {total_time:.2f}ms")
        logger.info(f"Found {len(results)} results")
        
        return BaseHandler.create_success_response(
            message=f"Found {len(results)} results using SQL",
            parameters=parameters,
            data={
                "results": results,
                "total_found": len(results),
                "search_strategy": "sql_query",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "sql_query"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"SQL query failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="SQL query failed",
            parameters=parameters,
            error=str(e)
        )


async def execute_sql_analytics(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute SQL analytics query - for aggregations, trends, statistics"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "sql_analytics",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting SQL analytics query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query for analytics
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.SQL_ANALYTICS.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        results_data = [dict(row._mapping) for row in rows]
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"SQL analytics completed in {total_time:.2f}ms, found {len(results_data)} results")
        
        return BaseHandler.create_success_response(
            message=f"Analytics query completed successfully",
            parameters=parameters,
            data={
                "results": results_data,
                "total_found": len(results_data),
                "search_strategy": "sql_analytics",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "sql_analytics"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"SQL analytics failed in {total_time:.2f}ms: {str(e)}")
        return BaseHandler.create_error_response(
            message=f"Analytics query failed: {str(e)}",
            parameters=parameters,
            error=str(e)
        )


async def execute_sql_complex_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute complex SQL query - for multi-table joins, subqueries"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "sql_complex_query",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting complex SQL query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate complex SQL query
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.SQL_COMPLEX_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        results_data = [dict(row._mapping) for row in rows]
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Complex SQL query completed in {total_time:.2f}ms, found {len(results_data)} results")
        
        return BaseHandler.create_success_response(
            message=f"Complex query completed successfully",
            parameters=parameters,
            data={
                "results": results_data,
                "total_found": len(results_data),
                "search_strategy": "sql_complex_query",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "sql_complex_query"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Complex SQL query failed in {total_time:.2f}ms: {str(e)}")
        return BaseHandler.create_error_response(
            message=f"Complex query failed: {str(e)}",
            parameters=parameters,
            error=str(e)
        )


async def execute_contract_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute contract-specific SQL query"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "contract_query",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting contract query with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query with contract context
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.CONTRACT_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        contracts = []
        for row in rows:
            contract_dict = dict(row._mapping)
            contracts.append(contract_dict)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Contract query completed in {total_time:.2f}ms")
        logger.info(f"Found {len(contracts)} contracts")
        
        return BaseHandler.create_success_response(
            message=f"Found {len(contracts)} contracts using SQL",
            parameters=parameters,
            data={
                "contracts": contracts,
                "total_found": len(contracts),
                "search_strategy": "contract_query",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "contract_query"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Contract query failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Contract query failed",
            parameters=parameters,
            error=str(e)
        )


async def execute_supplier_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute supplier-specific SQL query"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "supplier_query",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting supplier query with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query with supplier context
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.SUPPLIER_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        suppliers = []
        for row in rows:
            supplier_dict = dict(row._mapping)
            suppliers.append(supplier_dict)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Supplier query completed in {total_time:.2f}ms")
        logger.info(f"Found {len(suppliers)} suppliers")
        
        return BaseHandler.create_success_response(
            message=f"Found {len(suppliers)} suppliers using SQL",
            parameters=parameters,
            data={
                "suppliers": suppliers,
                "total_found": len(suppliers),
                "search_strategy": "supplier_query",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "supplier_query"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Supplier query failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Supplier query failed",
            parameters=parameters,
            error=str(e)
        )


async def execute_risk_analysis(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute risk analysis SQL query"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "risk_analysis",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting risk analysis with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query with risk analysis context
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.RISK_ANALYSIS.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        risk_data = []
        for row in rows:
            risk_dict = dict(row._mapping)
            risk_data.append(risk_dict)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Risk analysis completed in {total_time:.2f}ms")
        logger.info(f"Generated {len(risk_data)} risk analysis results")
        
        return BaseHandler.create_success_response(
            message=f"Generated {len(risk_data)} risk analysis results using SQL",
            parameters=parameters,
            data={
                "risk_analysis": risk_data,
                "total_found": len(risk_data),
                "search_strategy": "risk_analysis",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "risk_analysis"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Risk analysis failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Risk analysis failed",
            parameters=parameters,
            error=str(e)
        )


async def execute_comparison_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute comparison SQL query"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "comparison_query",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting comparison query with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        from app.core.sql_query_generator import sql_query_generator
        from app.api.v1.ai_assistant_utils.intent_classifier import IntentType
        
        # Generate SQL query with comparison context
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.COMPARISON_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        comparison_data = []
        for row in rows:
            comparison_dict = dict(row._mapping)
            comparison_data.append(comparison_dict)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Comparison query completed in {total_time:.2f}ms")
        logger.info(f"Generated {len(comparison_data)} comparison results")
        
        return BaseHandler.create_success_response(
            message=f"Generated {len(comparison_data)} comparison results using SQL",
            parameters=parameters,
            data={
                "comparison": comparison_data,
                "total_found": len(comparison_data),
                "search_strategy": "comparison_query",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "comparison_query"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Comparison query failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Comparison query failed",
            parameters=parameters,
            error=str(e)
        )


# Multi-part query handler removed for simplification


async def execute_generate_explanation(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Generate explanation for query results"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "generate_explanation",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting explanation generation with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        # For now, return a simple explanation
        # In the future, this could use AI to generate explanations
        explanation = f"Explanation for query: {original_query}. This query was processed using SQL generation to retrieve relevant data from the database."
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Explanation generation completed in {total_time:.2f}ms")
        
        return BaseHandler.create_success_response(
            message="Explanation generated successfully",
            parameters=parameters,
            data={
                "explanation": explanation,
                "search_strategy": "generate_explanation",
                "search_method": "explanation_generation",
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "generate_explanation"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Explanation generation failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Explanation generation failed",
            parameters=parameters,
            error=str(e)
        )


async def execute_generate_insights(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Generate insights from query results"""
    start_time = time.time()
    try:
        BaseHandler.log_execution_start(
            "generate_insights",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        logger.info(f"Starting insights generation with parameters: {parameters}")
        logger.info(f"Original query: {original_query}")
        
        # For now, return simple insights
        # In the future, this could use AI to generate insights
        insights = [
            f"Query: {original_query}",
            "This query was processed using SQL generation",
            "Results are based on current database state",
            "Consider reviewing data freshness for time-sensitive insights"
        ]
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Insights generation completed in {total_time:.2f}ms")
        
        return BaseHandler.create_success_response(
            message="Insights generated successfully",
            parameters=parameters,
            data={
                "insights": insights,
                "search_strategy": "generate_insights",
                "search_method": "insights_generation",
                "search_performance": {
                    "total_time_ms": total_time,
                    "phase": "generate_insights"
                }
            }
        )
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Insights generation failed after {total_time:.2f}ms: {str(e)}")
        
        return BaseHandler.create_error_response(
            message="Insights generation failed",
            parameters=parameters,
            error=str(e)
        )
