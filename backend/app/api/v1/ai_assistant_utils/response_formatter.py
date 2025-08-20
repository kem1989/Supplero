"""
Response formatting utilities for AI Assistant.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

from .intent_classifier import IntentType

logger = structlog.get_logger(__name__)


class ResponseFormatter:
    """Handles formatting of AI Assistant responses for different intents"""
    
    @staticmethod
    def format_response(
        intent: IntentType,
        execution_result: Dict[str, Any],
        query: str,
        processing_time_ms: float
    ) -> Dict[str, Any]:
        """
        Format the final response based on intent and execution result.
        
        Args:
            intent: The classified intent
            execution_result: Result from the execution handler
            query: Original user query
            processing_time_ms: Time taken to process the query
            
        Returns:
            Formatted response dictionary
        """
        
        base_response = {
            "query": query,
            "intent": intent.value,
            "processing_time_ms": round(processing_time_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "success": execution_result.get("performance_met", False)
        }
        
        # Add execution result data
        base_response.update(execution_result)
        
        # Apply intent-specific formatting
        if intent in [IntentType.SEARCH_CONTRACTS, IntentType.SEARCH_SUPPLIERS]:
            return ResponseFormatter._format_search_response(base_response, intent)
        
        elif intent in [IntentType.ANALYZE_RISK, IntentType.ANALYZE_SUPPLIER_RISK]:
            return ResponseFormatter._format_analysis_response(base_response, intent)
        
        elif intent in [IntentType.COMPARE_CLAUSES, IntentType.COMPARE_SUPPLIERS]:
            return ResponseFormatter._format_comparison_response(base_response, intent)
        
        elif intent == IntentType.SUPPLIER_INSIGHTS:
            return ResponseFormatter._format_insights_response(base_response)
        
        elif intent in [
            IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS,
            IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS,
            IntentType.SUPPLIERS_BY_CONTRACT_CLAUSES,
            IntentType.CONTRACTS_BY_SUPPLIER_RISK,
            IntentType.UNIFIED_RISK_SEARCH
        ]:
            return ResponseFormatter._format_cross_system_response(base_response, intent)
        
        else:
            return base_response
    
    @staticmethod
    def _format_search_response(response: Dict[str, Any], intent: IntentType) -> Dict[str, Any]:
        """Format search response with search-specific enhancements"""
        
        if intent == IntentType.SEARCH_CONTRACTS:
            contracts = response.get("contracts", [])
            response["result_summary"] = {
                "total_contracts": len(contracts),
                "has_results": len(contracts) > 0,
                "result_type": "contracts"
            }
            
            # Add quick insights
            if contracts:
                total_value = sum(c.get("contract_value", 0) or 0 for c in contracts)
                suppliers = list(set(c.get("supplier_name") for c in contracts if c.get("supplier_name")))
                
                response["quick_insights"] = {
                    "total_contract_value": total_value,
                    "unique_suppliers": len(suppliers),
                    "average_value": total_value / len(contracts) if contracts else 0
                }
        
        elif intent == IntentType.SEARCH_SUPPLIERS:
            suppliers = response.get("suppliers", [])
            response["result_summary"] = {
                "total_suppliers": len(suppliers),
                "has_results": len(suppliers) > 0,
                "result_type": "suppliers"
            }
        
        return response
    
    @staticmethod
    def _format_analysis_response(response: Dict[str, Any], intent: IntentType) -> Dict[str, Any]:
        """Format analysis response with analysis-specific enhancements"""
        
        if intent == IntentType.ANALYZE_RISK:
            analyses = response.get("risk_analyses", [])
            if analyses:
                response["analysis_summary"] = {
                    "total_analyzed": len(analyses),
                    "highest_risk": max(analyses, key=lambda x: x.get("risk_score", 0)),
                    "average_risk": sum(a.get("risk_score", 0) for a in analyses) / len(analyses)
                }
        
        elif intent == IntentType.ANALYZE_SUPPLIER_RISK:
            analyses = response.get("risk_analyses", [])
            if analyses:
                response["risk_distribution"] = {
                    "high_risk": len([a for a in analyses if a.get("current_risk_score", 0) >= 70]),
                    "medium_risk": len([a for a in analyses if 40 <= a.get("current_risk_score", 0) < 70]),
                    "low_risk": len([a for a in analyses if a.get("current_risk_score", 0) < 40])
                }
        
        return response
    
    @staticmethod
    def _format_comparison_response(response: Dict[str, Any], intent: IntentType) -> Dict[str, Any]:
        """Format comparison response with comparison-specific enhancements"""
        
        comparisons = response.get("comparisons", [])
        if comparisons:
            response["comparison_summary"] = {
                "items_compared": len(comparisons),
                "comparison_type": "clauses" if intent == IntentType.COMPARE_CLAUSES else "suppliers"
            }
            
            # Add comparison insights
            if intent == IntentType.COMPARE_SUPPLIERS:
                insights = response.get("comparison_insights", {})
                if insights:
                    response["key_findings"] = [
                        f"Lowest risk: {insights.get('lowest_risk', {}).get('supplier')} ({insights.get('lowest_risk', {}).get('score')})",
                        f"Highest risk: {insights.get('highest_risk', {}).get('supplier')} ({insights.get('highest_risk', {}).get('score')})",
                        f"Average risk: {insights.get('average_risk', 0):.1f}"
                    ]
        
        return response
    
    @staticmethod
    def _format_insights_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """Format insights response with insights-specific enhancements"""
        
        insights = response.get("insights", {})
        if insights:
            # Extract key metrics for summary
            portfolio_health = insights.get("portfolio_health_score")
            key_metrics = insights.get("key_metrics", {})
            
            response["executive_summary"] = {
                "portfolio_health": portfolio_health,
                "total_suppliers": key_metrics.get("total_suppliers", 0),
                "high_risk_suppliers": key_metrics.get("high_risk_count", 0),
                "key_insight": ResponseFormatter._generate_key_insight(insights)
            }
        
        return response
    
    @staticmethod
    def _format_cross_system_response(response: Dict[str, Any], intent: IntentType) -> Dict[str, Any]:
        """Format cross-system response with cross-system specific enhancements"""
        
        search_results = response.get("search_results", {})
        suppliers = search_results.get("suppliers", [])
        contracts = search_results.get("contracts", [])
        
        response["cross_system_summary"] = {
            "suppliers_found": len(suppliers),
            "contracts_found": len(contracts),
            "query_type": intent.value.lower().replace("_", " ").title()
        }
        
        # Add specific insights based on intent
        if intent == IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS:
            high_risk_suppliers = [s for s in suppliers if s.get("risk_score", 0) >= 70]
            response["risk_insights"] = {
                "high_risk_suppliers": len(high_risk_suppliers),
                "risk_exposure": "high" if len(high_risk_suppliers) > len(suppliers) * 0.3 else "moderate"
            }
        
        elif intent == IntentType.UNIFIED_RISK_SEARCH:
            insights = response.get("unified_insights", {})
            if insights:
                response["unified_summary"] = {
                    "risk_exposure": insights.get("risk_exposure", "unknown"),
                    "average_risk": insights.get("average_supplier_risk", 0),
                    "total_value": insights.get("total_contract_value", 0)
                }
        
        return response
    
    @staticmethod
    def _generate_key_insight(insights: Dict[str, Any]) -> str:
        """Generate a key insight from the insights data"""
        
        portfolio_health = insights.get("portfolio_health_score", 0)
        key_metrics = insights.get("key_metrics", {})
        
        if portfolio_health >= 80:
            return "Portfolio shows strong health with low risk exposure"
        elif portfolio_health >= 60:
            return "Portfolio health is fair with some areas for improvement"
        elif portfolio_health >= 40:
            return "Portfolio shows moderate risk that requires attention"
        else:
            return "Portfolio has significant risk exposure requiring immediate action"
    
    @staticmethod
    def add_helpful_suggestions(
        response: Dict[str, Any],
        intent: IntentType
    ) -> Dict[str, Any]:
        """Add helpful suggestions for follow-up queries"""
        
        suggestions = []
        
        if intent == IntentType.SEARCH_SUPPLIERS:
            suggestions = [
                "Analyze risk for these suppliers",
                "Compare top suppliers",
                "Get insights on supplier portfolio"
            ]
        
        elif intent == IntentType.SEARCH_CONTRACTS:
            suggestions = [
                "Analyze risk in these contracts",
                "Search for specific clauses",
                "Compare contract terms"
            ]
        
        elif intent == IntentType.SUPPLIER_INSIGHTS:
            suggestions = [
                "Get predictive risk analysis",
                "Compare with industry benchmarks",
                "Analyze specific risk trends"
            ]
        
        if suggestions:
            response["suggested_follow_ups"] = suggestions
        
        return response
