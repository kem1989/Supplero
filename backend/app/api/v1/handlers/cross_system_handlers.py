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
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.UNIFIED_RISK_SEARCH,
            query_text=parameters.get("query"),
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
            message=f"Unified risk search completed - found {len(search_result.suppliers)} suppliers and {len(search_result.contracts)} contracts",
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
                            "country": supplier.country,
                            "contract_count": supplier.contract_count,
                            "total_contract_value": supplier.total_contract_value,
                            "highest_contract_value": supplier.highest_contract_value if hasattr(supplier, 'highest_contract_value') else None
                        }
                        for supplier in search_result.suppliers[:10]
                    ],
                    "contracts": [
                        {
                            "id": contract.id,
                            "supplier_name": contract.supplier_name,
                            "contract_value": getattr(contract, 'contract_value', None),
                            "risk_indicators": getattr(contract, 'risk_indicators', [])
                        }
                        for contract in search_result.contracts[:10]
                    ]
                },
                "statistics": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_contracts": len(search_result.contracts),
                    "high_risk_suppliers": len([s for s in search_result.suppliers if s.risk_score >= 70]),
                    "total_contract_value": sum(getattr(c, 'contract_value', 0) or 0 for c in search_result.contracts),
                },
                "insights": search_result.key_insights,
                "recommendations": search_result.recommended_actions
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


# NEW: Enhanced supplier-contract relationship handlers

async def execute_suppliers_by_contract_value(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute search for suppliers based on contract value criteria"""
    try:
        BaseHandler.log_execution_start(
            "suppliers_by_contract_value",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract contract value parameters
        contract_value_min = parameters.get("contract_value_min")
        contract_value_max = parameters.get("contract_value_max")
        contract_value_range = parameters.get("contract_value_range")
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_BY_CONTRACT_VALUE,
            contract_value_min=contract_value_min,
            contract_value_max=contract_value_max,
            query_text=contract_value_range or f"contracts between ${contract_value_min:,}" if contract_value_min else f"contracts up to ${contract_value_max:,}" if contract_value_max else "all contracts",
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        search_service = CrossSystemSearchService()
        search_result = await search_service.execute_search(search_request, db, current_user.organization_id)
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.suppliers)} suppliers with contracts matching value criteria",
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
                            "country": supplier.country,
                            "contract_count": supplier.contract_count,
                            "total_contract_value": supplier.total_contract_value,
                            "highest_contract_value": supplier.highest_contract_value if hasattr(supplier, 'highest_contract_value') else None
                        }
                        for supplier in search_result.suppliers[:20]
                    ]
                },
                "statistics": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_contracts": sum(s.contract_count for s in search_result.suppliers),
                    "total_contract_value": sum(s.total_contract_value or 0 for s in search_result.suppliers),
                    "average_contract_value": sum(s.total_contract_value or 0 for s in search_result.suppliers) / len(search_result.suppliers) if search_result.suppliers else 0
                },
                "contract_value_criteria": {
                    "min_value": contract_value_min,
                    "max_value": contract_value_max,
                    "range_description": contract_value_range
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("suppliers_by_contract_value", e, parameters)
        return BaseHandler.create_error_response(
            message="Suppliers by contract value search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": []}}
        )


async def execute_suppliers_with_contract_criteria(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute search for suppliers that meet specific contract criteria"""
    try:
        BaseHandler.log_execution_start(
            "suppliers_with_contract_criteria",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract contract criteria parameters
        contract_status = parameters.get("contract_status")
        contract_type = parameters.get("contract_type")
        payment_terms = parameters.get("payment_terms")
        contract_region = parameters.get("contract_region")
        contract_start_date = parameters.get("contract_start_date")
        contract_end_date = parameters.get("contract_end_date")
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_BY_CONTRACT_CLAUSES,
            clause_types=[contract_type] if contract_type else None,
            query_text=f"suppliers with {contract_type or 'specific'} contracts",
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 20)
        )
        
        # Execute search
        search_service = CrossSystemSearchService()
        search_result = await search_service.execute_search(search_request, db, current_user.organization_id)
        
        return BaseHandler.create_success_response(
            message=f"Found {len(search_result.suppliers)} suppliers meeting contract criteria",
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
                            "country": supplier.country,
                            "contract_count": supplier.contract_count,
                            "total_contract_value": supplier.total_contract_value,
                            "matching_contracts": supplier.matching_contracts if hasattr(supplier, 'matching_contracts') else supplier.contract_count
                        }
                        for supplier in search_result.suppliers[:20]
                    ]
                },
                "statistics": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_contracts": sum(s.contract_count for s in search_result.suppliers),
                    "total_contract_value": sum(s.total_contract_value or 0 for s in search_result.suppliers)
                },
                "contract_criteria": {
                    "status": contract_status,
                    "type": contract_type,
                    "payment_terms": payment_terms,
                    "region": contract_region,
                    "start_date": contract_start_date,
                    "end_date": contract_end_date
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("suppliers_with_contract_criteria", e, parameters)
        return BaseHandler.create_error_response(
            message="Suppliers with contract criteria search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"search_results": {"suppliers": []}}
        )


async def execute_supplier_contract_portfolio(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute search for a comprehensive supplier contract portfolio"""
    try:
        BaseHandler.log_execution_start(
            "supplier_contract_portfolio",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract portfolio parameters
        supplier_name = parameters.get("supplier_name")
        supplier_industry = parameters.get("supplier_industry")
        supplier_country = parameters.get("supplier_country")
        supplier_risk_level = parameters.get("supplier_risk_level")
        
        # Create cross-system search request
        search_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.UNIFIED_RISK_SEARCH,
            query_text=f"portfolio for {supplier_name or supplier_industry or supplier_country or 'all suppliers'}",
            supplier_industries=[supplier_industry] if supplier_industry else None,
            supplier_countries=[supplier_country] if supplier_country else None,
            page=parameters.get("page", 1),
            page_size=parameters.get("page_size", 50)  # Larger page size for portfolio view
        )
        
        # Execute search
        search_service = CrossSystemSearchService()
        search_result = await search_service.execute_search(search_request, db, current_user.organization_id)
        
        return BaseHandler.create_success_response(
            message=f"Generated portfolio view with {len(search_result.suppliers)} suppliers and {len(search_result.contracts)} contracts",
            parameters=parameters,
            data={
                "portfolio_overview": {
                    "total_suppliers": len(search_result.suppliers),
                    "total_contracts": len(search_result.contracts),
                    "total_contract_value": sum(getattr(c, 'contract_value', 0) or 0 for c in search_result.contracts),
                    "average_supplier_risk": sum(s.risk_score for s in search_result.suppliers) / len(search_result.suppliers) if search_result.suppliers else 0,
                    "risk_distribution": {
                        "low": len([s for s in search_result.suppliers if s.risk_level == "LOW"]),
                        "medium": len([s for s in search_result.suppliers if s.risk_level == "MEDIUM"]),
                        "high": len([s for s in search_result.suppliers if s.risk_level == "HIGH"]),
                        "critical": len([s for s in search_result.suppliers if s.risk_level == "CRITICAL"])
                    }
                },
                "search_results": {
                    "suppliers": [
                        {
                            "id": supplier.id,
                            "name": supplier.name,
                            "risk_score": supplier.risk_score,
                            "risk_level": supplier.risk_level,
                            "industry": supplier.industry,
                            "country": supplier.country,
                            "contract_count": supplier.contract_count,
                            "total_contract_value": supplier.total_contract_value,
                            "last_assessment": supplier.last_assessment_date
                        }
                        for supplier in search_result.suppliers[:30]
                    ],
                    "contracts": [
                        {
                            "id": contract.id,
                            "supplier_name": contract.supplier_name,
                            "contract_value": getattr(contract, 'contract_value', None),
                            "contract_status": getattr(contract, 'status', 'unknown')
                        }
                        for contract in search_result.contracts[:30]
                    ]
                },
                "insights": search_result.key_insights,
                "recommendations": search_result.recommended_actions
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("supplier_contract_portfolio", e, parameters)
        return BaseHandler.create_error_response(
            message="Supplier contract portfolio generation failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"portfolio_overview": {}, "search_results": {"suppliers": [], "contracts": []}}
        )
