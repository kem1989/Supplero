"""
Contracts API endpoints for contract management.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.logging import get_current_trace_context
from app.models.user import User
from app.models.contract import Contract

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractResponse(BaseModel):
    """Response model for contract data"""
    id: int
    title: Optional[str] = None
    type: Optional[str] = None
    status: str
    contract_value: Optional[float] = None
    currency: str
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renewal: bool
    renewal_term_months: Optional[int] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    payment_terms_days: Optional[int] = None
    liability_cap_amount: Optional[float] = None
    liability_cap_type: Optional[str] = None
    sla_uptime_percent: Optional[float] = None
    termination_notice_days: Optional[int] = None
    penalty_rate_percent: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractCreate(BaseModel):
    """Request model for creating a contract"""
    title: Optional[str] = None
    type: Optional[str] = None
    status: str = "ACTIVE"
    contract_value: Optional[float] = None
    currency: str = "USD"
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renewal: bool = False
    renewal_term_months: Optional[int] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    payment_terms_days: Optional[int] = None
    liability_cap_amount: Optional[float] = None
    liability_cap_type: Optional[str] = None
    sla_uptime_percent: Optional[float] = None
    termination_notice_days: Optional[int] = None
    penalty_rate_percent: Optional[float] = None
    organization_id: Optional[int] = None


class ContractUpdate(BaseModel):
    """Request model for updating a contract"""
    title: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    contract_value: Optional[float] = None
    currency: Optional[str] = None
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renewal: Optional[bool] = None
    renewal_term_months: Optional[int] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    payment_terms_days: Optional[int] = None
    liability_cap_amount: Optional[float] = None
    liability_cap_type: Optional[str] = None
    sla_uptime_percent: Optional[float] = None
    termination_notice_days: Optional[int] = None
    penalty_rate_percent: Optional[float] = None


class ContractListResponse(BaseModel):
    """Response model for contract list with pagination"""
    contracts: List[ContractResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


def get_current_user() -> User:
    """Get current user - placeholder for authentication"""
    # TODO: Implement proper authentication
    return User(
        id=1,
        email="test@example.com",
        organization_id=1
    )


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search term for title or type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    contract_type: Optional[str] = Query(None, description="Filter by contract type"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    List contracts with optional filtering and pagination.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Build query
        query = db.query(Contract).filter(Contract.organization_id == current_user.organization_id)
        
        # Apply filters
        if search:
            search_filter = or_(
                Contract.title.ilike(f"%{search}%"),
                Contract.type.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if status:
            query = query.filter(Contract.status == status.upper())
        
        if contract_type:
            query = query.filter(Contract.type.ilike(f"%{contract_type}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        contracts = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(
            "Contracts listed successfully",
            total=total,
            page=page,
            page_size=page_size,
            filters={
                "search": search,
                "status": status,
                "contract_type": contract_type
            },
            **trace_context
        )
        
        return ContractListResponse(
            contracts=[ContractResponse.from_orm(contract) for contract in contracts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list contracts",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contracts: {str(e)}"
        )


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get a specific contract by ID.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find contract
        contract = db.query(Contract).filter(
            and_(
                Contract.id == contract_id,
                Contract.organization_id == current_user.organization_id
            )
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        logger.info(
            "Contract retrieved successfully",
            contract_id=contract_id,
            **trace_context
        )
        
        return ContractResponse.from_orm(contract)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get contract",
            contract_id=contract_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contract: {str(e)}"
        )


@router.post("/", response_model=ContractResponse)
async def create_contract(
    contract_data: ContractCreate,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Create a new contract.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Create contract
        contract = Contract(
            title=contract_data.title,
            type=contract_data.type,
            status=contract_data.status,
            contract_value=contract_data.contract_value,
            currency=contract_data.currency,
            effective_at=contract_data.effective_at,
            expires_at=contract_data.expires_at,
            auto_renewal=contract_data.auto_renewal,
            renewal_term_months=contract_data.renewal_term_months,
            governing_law=contract_data.governing_law,
            jurisdiction=contract_data.jurisdiction,
            payment_terms_days=contract_data.payment_terms_days,
            liability_cap_amount=contract_data.liability_cap_amount,
            liability_cap_type=contract_data.liability_cap_type,
            sla_uptime_percent=contract_data.sla_uptime_percent,
            termination_notice_days=contract_data.termination_notice_days,
            penalty_rate_percent=contract_data.penalty_rate_percent,
            organization_id=contract_data.organization_id or current_user.organization_id
        )
        
        db.add(contract)
        db.commit()
        db.refresh(contract)
        
        logger.info(
            "Contract created successfully",
            contract_id=contract.id,
            contract_title=contract.title,
            **trace_context
        )
        
        return ContractResponse.from_orm(contract)
        
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create contract",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract: {str(e)}"
        )


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing contract.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find contract
        contract = db.query(Contract).filter(
            and_(
                Contract.id == contract_id,
                Contract.organization_id == current_user.organization_id
            )
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Update fields
        update_data = contract_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        
        db.commit()
        db.refresh(contract)
        
        logger.info(
            "Contract updated successfully",
            contract_id=contract_id,
            **trace_context
        )
        
        return ContractResponse.from_orm(contract)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to update contract",
            contract_id=contract_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contract: {str(e)}"
        )


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Delete a contract (soft delete by setting status to INACTIVE).
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find contract
        contract = db.query(Contract).filter(
            and_(
                Contract.id == contract_id,
                Contract.organization_id == current_user.organization_id
            )
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Soft delete
        contract.status = "INACTIVE"
        db.commit()
        
        logger.info(
            "Contract deleted successfully",
            contract_id=contract_id,
            **trace_context
        )
        
        return {"message": "Contract deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete contract",
            contract_id=contract_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contract: {str(e)}"
        )
