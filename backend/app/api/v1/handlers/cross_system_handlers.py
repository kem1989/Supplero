"""
Cross-system execution handlers for AI Assistant.
Handles queries that bridge suppliers and contracts.
"""

import structlog
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.cross_system_search import CrossSystemSearchService, CrossSystemSearchRequest, CrossSystemQueryType
from .base_handler import BaseHandler

logger = structlog.get_logger(__name__)


async def execute_suppliers_with_risky_contracts(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute suppliers with risky contracts search"""
    try:
        BaseHandler.log_execution_start(
            "suppliers_with_risky_contracts",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_WITH_RISKY_CONTRACTS,
            contract_risk_level=parameters.get("contract_risk_level"),
            supplier_risk_level=parameters.get("supplier_risk_level"),
            supplier_industries=parameters.get("supplier_industries"),
            supplier_countries=parameters.get("supplier_countries"),
            contract_value_min=parameters.get("contract_value_min"),
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        search_service = CrossSystemSearchService()
        search_result = await search_service.execute_search(search_request, db, current_user.organization_id)
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.suppliers)} suppliers with risky contracts",
            parameters=parameters,
            data={
                "search_results": {
                    "suppliers": [
                        {
                            "id": supplier.id,
                            "name": supplier.name,
                            "risk_score": supplier.risk_score,
                            "risk_level": supplier.risk_level,
                            "industry": supplier.industry,
                            "country": supplier.country
                        }
                        for supplier in search_result.suppliers[:10]  # Limit to top 10
                    ],
                    "contracts": [
                        {
                            "id": contract.id,
                            "supplier_name": contract.supplier_name,
                            "risk_indicators": getattr(contract, 'risk_indicators', []),
                            "contract_value": getattr(contract, 'contract_value', None)
                        }
                        for contract in search_result.contracts[:10]  # Limit to top 10
                    ]
                },
                "statistics": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_contracts": len(search_result.contracts),
                    "high_risk_suppliers": len([s for s in search_result.suppliers if s.risk_score >= 70])
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("suppliers_with_risky_contracts", e, parameters)
        return BaseHandler.create_error_response(
            message="Suppliers with risky contracts search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": [], "contracts": []}}
        )


async def execute_suppliers_with_expiring_contracts(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute suppliers with expiring contracts search"""
    try:
        BaseHandler.log_execution_start(
            "suppliers_with_expiring_contracts",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_WITH_EXPIRING_CONTRACTS,
            contract_expiring_days=parameters.get("contract_expiring_days", 90),
            supplier_risk_level=parameters.get("supplier_risk_level"),
            supplier_industries=parameters.get("supplier_industries"),
            contract_value_min=parameters.get("contract_value_min"),
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute cross-system search
        cross_search_service = CrossSystemSearchService()
        search_result = await cross_search_service.execute_cross_system_search(
            search_request, db, current_user.organization_id
        )
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.suppliers)} suppliers with expiring contracts",
            parameters=parameters,
            data={
                "search_results": {
                    "suppliers": [
                        {
                            "id": s.id,
                            "name": s.name,
                            "risk_score": s.risk_score,
                            "expiring_contracts_count": len([c for c in search_result.contracts if getattr(c, 'supplier_name', '') == s.name])
                        } for s in search_result.suppliers
                    ],
                    "contracts": [
                        {
                            "id": c.id,
                            "supplier_name": getattr(c, 'supplier_name', ''),
                            "expiry_date": getattr(c, 'expiry_date', None),
                            "contract_value": getattr(c, 'contract_value', None)
                        } for c in search_result.contracts
                    ]
                },
                "statistics": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_expiring_contracts": len(search_result.contracts),
                    "expiring_soon_count": len([c for c in search_result.contracts if getattr(c, 'days_to_expiry', 999) <= 30])
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("suppliers_with_expiring_contracts", e, parameters)
        return BaseHandler.create_error_response(
            message="Suppliers with expiring contracts search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": [], "contracts": []}}
        )


async def execute_suppliers_by_contract_clauses(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute suppliers by contract clauses search"""
    try:
        BaseHandler.log_execution_start(
            "suppliers_by_contract_clauses",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Create search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_BY_CONTRACT_CLAUSES,
            clause_types=parameters.get("clause_types", []),
            supplier_industries=parameters.get("supplier_industries"),
            contract_value_min=parameters.get("contract_value_min"),
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        cross_search_service = CrossSystemSearchService()
        search_result = await cross_search_service.execute_cross_system_search(
            search_request, db, current_user.organization_id
        )
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.suppliers)} suppliers with specified contract clauses",
            parameters=parameters,
            data={
                "search_results": {
                    "suppliers": [
                        {
                            "id": s.id, 
                            "name": s.name,
                            "industry": s.industry,
                            "risk_score": s.risk_score,
                            "matching_contracts": len([c for c in search_result.contracts if getattr(c, 'supplier_name', '') == s.name])
                        } for s in search_result.suppliers
                    ],
                    "contracts": [
                        {
                            "id": c.id, 
                            "supplier_name": getattr(c, 'supplier_name', ''),
                            "matching_clauses": getattr(c, 'matching_clauses', []),
                            "filename": getattr(c, 'filename', '')
                        } for c in search_result.contracts
                    ]
                },
                "clause_analysis": {
                    "requested_clauses": parameters.get("clause_types", []),
                    "total_matches": len(search_result.contracts),
                    "suppliers_with_clauses": len(search_result.suppliers)
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("suppliers_by_contract_clauses", e, parameters)
        return BaseHandler.create_error_response(
            message="Suppliers by contract clauses search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": [], "contracts": []}}
        )


async def execute_contracts_by_supplier_risk(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute contracts by supplier risk search"""
    try:
        BaseHandler.log_execution_start(
            "contracts_by_supplier_risk",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Create search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.CONTRACTS_BY_SUPPLIER_RISK,
            supplier_risk_level=parameters.get("supplier_risk_level"),
            contract_value_min=parameters.get("contract_value_min"),
            supplier_industries=parameters.get("supplier_industries"),
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        cross_search_service = CrossSystemSearchService()
        search_result = await cross_search_service.execute_cross_system_search(
            search_request, db, current_user.organization_id
        )
        
        risk_level = parameters.get("supplier_risk_level", "high")
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.contracts)} contracts from {risk_level}-risk suppliers",
            parameters=parameters,
            data={
                "search_results": {
                    "contracts": [
                        {
                            "id": c.id, 
                            "supplier_name": getattr(c, 'supplier_name', ''),
                            "filename": getattr(c, 'filename', ''),
                            "contract_value": getattr(c, 'contract_value', None),
                            "supplier_risk_score": getattr(c, 'supplier_risk_score', None)
                        } for c in search_result.contracts
                    ],
                    "suppliers": [
                        {
                            "id": s.id, 
                            "name": s.name, 
                            "risk_score": s.risk_score,
                            "risk_level": s.risk_level,
                            "contract_count": len([c for c in search_result.contracts if getattr(c, 'supplier_name', '') == s.name])
                        } for s in search_result.suppliers
                    ]
                },
                "risk_analysis": {
                    "target_risk_level": risk_level,
                    "total_contracts": len(search_result.contracts),
                    "unique_suppliers": len(search_result.suppliers),
                    "average_supplier_risk": sum(s.risk_score for s in search_result.suppliers) / len(search_result.suppliers) if search_result.suppliers else 0
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("contracts_by_supplier_risk", e, parameters)
        return BaseHandler.create_error_response(
            message="Contracts by supplier risk search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": [], "contracts": []}}
        )


async def execute_unified_risk_search(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute unified risk search across suppliers and contracts"""
    try:
        BaseHandler.log_execution_start(
            "unified_risk_search",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Create search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.UNIFIED_RISK_SEARCH,
            risk_threshold=parameters.get("risk_threshold", 70),
            supplier_industries=parameters.get("supplier_industries"),
            contract_value_min=parameters.get("contract_value_min"),
            supplier_countries=parameters.get("supplier_countries"),
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        cross_search_service = CrossSystemSearchService()
        search_result = await cross_search_service.execute_cross_system_search(
            search_request, db, current_user.organization_id
        )
        
        # Calculate risk statistics
        supplier_risks = [s.risk_score for s in search_result.suppliers]
        avg_supplier_risk = sum(supplier_risks) / len(supplier_risks) if supplier_risks else 0
        
        return BaseHandler.create_success_response(
            message=f"Unified risk search completed - found {len(search_result.suppliers)} suppliers and {len(search_result.contracts)} contracts",
            parameters=parameters,
            data={
                "search_results": {
                    "suppliers": [
                        {
                            "id": s.id, 
                            "name": s.name, 
                            "risk_score": s.risk_score,
                            "risk_level": s.risk_level,
                            "industry": s.industry,
                            "country": s.country
                        } for s in search_result.suppliers
                    ],
                    "contracts": [
                        {
                            "id": c.id, 
                            "supplier_name": getattr(c, 'supplier_name', ''),
                            "filename": getattr(c, 'filename', ''),
                            "contract_value": getattr(c, 'contract_value', None)
                        } for c in search_result.contracts
                    ]
                },
                "unified_insights": {
                    "risk_threshold": parameters.get("risk_threshold", 70),
                    "suppliers_above_threshold": len([s for s in search_result.suppliers if s.risk_score >= parameters.get("risk_threshold", 70)]),
                    "average_supplier_risk": round(avg_supplier_risk, 2),
                    "total_contract_value": sum(getattr(c, 'contract_value', 0) or 0 for c in search_result.contracts),
                    "risk_exposure": "high" if avg_supplier_risk >= 70 else "medium" if avg_supplier_risk >= 40 else "low"
                },
                "recommendations": [
                    "Monitor high-risk suppliers closely",
                    "Review contracts with risky suppliers",
                    "Consider diversifying supplier base",
                    "Implement enhanced due diligence"
                ] if avg_supplier_risk >= 60 else [
                    "Maintain current monitoring practices",
                    "Continue regular risk assessments"
                ]
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("unified_risk_search", e, parameters)
        return BaseHandler.create_error_response(
            message="Unified risk search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": [], "contracts": []}}
        )
