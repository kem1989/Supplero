"""
Suppliers API endpoints for supplier management and risk assessment.
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
from app.models.supplier import Supplier

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


class SupplierResponse(BaseModel):
    """Response model for supplier data"""
    id: int
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    employee_count: Optional[int] = None
    current_risk_score: float
    current_risk_level: str
    geopolitical_risk: Optional[float] = None
    financial_risk: Optional[float] = None
    operational_risk: Optional[float] = None
    compliance_risk: Optional[float] = None
    esg_risk: Optional[float] = None
    is_active: bool
    is_watchlisted: bool
    watchlist_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_risk_assessment: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    """Request model for creating a supplier"""
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    employee_count: Optional[int] = None
    organization_id: Optional[int] = None


class SupplierUpdate(BaseModel):
    """Request model for updating a supplier"""
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    employee_count: Optional[int] = None
    is_active: Optional[bool] = None
    is_watchlisted: Optional[bool] = None
    watchlist_reason: Optional[str] = None


class SupplierListResponse(BaseModel):
    """Response model for supplier list with pagination"""
    suppliers: List[SupplierResponse]
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


@router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search term for name, industry, or country"),
    country: Optional[str] = Query(None, description="Filter by country"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    is_watchlisted: Optional[bool] = Query(None, description="Filter by watchlist status"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    List suppliers with optional filtering and pagination.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Build query
        query = db.query(Supplier).filter(Supplier.organization_id == current_user.organization_id)
        
        # Apply filters
        if search:
            search_filter = or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.industry.ilike(f"%{search}%"),
                Supplier.country.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if country:
            query = query.filter(Supplier.country.ilike(f"%{country}%"))
        
        if industry:
            query = query.filter(Supplier.industry.ilike(f"%{industry}%"))
        
        if risk_level:
            query = query.filter(Supplier.current_risk_level == risk_level.upper())
        
        if is_watchlisted is not None:
            query = query.filter(Supplier.is_watchlisted == is_watchlisted)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        suppliers = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(
            "Suppliers listed successfully",
            total=total,
            page=page,
            page_size=page_size,
            filters={
                "search": search,
                "country": country,
                "industry": industry,
                "risk_level": risk_level,
                "is_watchlisted": is_watchlisted
            },
            **trace_context
        )
        
        return SupplierListResponse(
            suppliers=[SupplierResponse.from_orm(supplier) for supplier in suppliers],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list suppliers",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list suppliers: {str(e)}"
        )


@router.get("/search", response_model=SupplierListResponse)
async def search_suppliers(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Search suppliers by name, industry, or country.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Build search query
        search_filter = or_(
            Supplier.name.ilike(f"%{q}%"),
            Supplier.industry.ilike(f"%{q}%"),
            Supplier.country.ilike(f"%{q}%")
        )
        
        query = db.query(Supplier).filter(
            and_(
                Supplier.organization_id == current_user.organization_id,
                search_filter
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        suppliers = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(
            "Suppliers searched successfully",
            query=q,
            total=total,
            page=page,
            page_size=page_size,
            **trace_context
        )
        
        return SupplierListResponse(
            suppliers=[SupplierResponse.from_orm(supplier) for supplier in suppliers],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to search suppliers",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search suppliers: {str(e)}"
        )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get a specific supplier by ID.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find supplier
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.organization_id == current_user.organization_id
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        logger.info(
            "Supplier retrieved successfully",
            supplier_id=supplier_id,
            **trace_context
        )
        
        return SupplierResponse.from_orm(supplier)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get supplier",
            supplier_id=supplier_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supplier: {str(e)}"
        )


@router.post("/profile", response_model=SupplierResponse)
async def create_supplier(
    supplier_data: SupplierCreate,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Create a new supplier profile.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Create supplier
        supplier = Supplier(
            name=supplier_data.name,
            industry=supplier_data.industry,
            country=supplier_data.country,
            location=supplier_data.location,
            contact_email=supplier_data.contact_email,
            contact_phone=supplier_data.contact_phone,
            website=supplier_data.website,
            address=supplier_data.address,
            company_size=supplier_data.company_size,
            revenue_range=supplier_data.revenue_range,
            employee_count=supplier_data.employee_count,
            organization_id=supplier_data.organization_id or current_user.organization_id,
            current_risk_score=0.0,
            current_risk_level="LOW"
        )
        
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        logger.info(
            "Supplier created successfully",
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            **trace_context
        )
        
        return SupplierResponse.from_orm(supplier)
        
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create supplier",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create supplier: {str(e)}"
        )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing supplier.
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find supplier
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.organization_id == current_user.organization_id
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        # Update fields
        update_data = supplier_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        
        db.commit()
        db.refresh(supplier)
        
        logger.info(
            "Supplier updated successfully",
            supplier_id=supplier_id,
            **trace_context
        )
        
        return SupplierResponse.from_orm(supplier)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to update supplier",
            supplier_id=supplier_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update supplier: {str(e)}"
        )


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Delete a supplier (soft delete by setting is_active to False).
    """
    trace_context = get_current_trace_context()
    
    try:
        # Get current user (placeholder)
        current_user = get_current_user()
        
        # Find supplier
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.organization_id == current_user.organization_id
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        # Soft delete
        supplier.is_active = False
        db.commit()
        
        logger.info(
            "Supplier deleted successfully",
            supplier_id=supplier_id,
            **trace_context
        )
        
        return {"message": "Supplier deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete supplier",
            supplier_id=supplier_id,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete supplier: {str(e)}"
        )
