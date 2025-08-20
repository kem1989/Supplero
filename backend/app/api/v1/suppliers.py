"""
Supplier API endpoints for supplier risk management and profiling.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from datetime import datetime
import structlog

from app.core.database import get_db
from app.core.logging import get_current_trace_context
from app.models.supplier import Supplier, SupplierRiskAssessment
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierRiskResponse,
    SupplierListResponse, RiskAssessmentCreate, RiskAssessmentResponse
)
from app.schemas.supplier_insights import (
    SupplierInsightsRequest,
    SupplierInsightsResponse,
    TrendAnalysisResponse,
    PredictiveAnalysisResponse,
    BenchmarkAnalysisResponse,
    PortfolioHealthResponse,
    InsightType
)
# from app.core.audit import audit_action  # TODO: Implement proper audit integration
from app.core.supplier_risk import SupplierRiskService
from app.core.supplier_insights import SupplierInsightsService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("/profile", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier_profile(
    supplier_data: SupplierCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new supplier profile with basic information.
    
    This endpoint ingests basic supplier data and creates an initial risk profile.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Check if supplier with same name already exists in the organization
        if supplier_data.organization_id:
            existing_supplier = db.query(Supplier).filter(
                and_(
                    Supplier.name == supplier_data.name,
                    Supplier.organization_id == supplier_data.organization_id
                )
            ).first()
            
            if existing_supplier:
                logger.warning(
                    "Supplier creation failed - name already exists in organization",
                    supplier_name=supplier_data.name,
                    organization_id=supplier_data.organization_id,
                    **trace_context
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Supplier with this name already exists in the organization"
                )
        
        # Create new supplier
        db_supplier = Supplier(**supplier_data.dict())
        
        # Calculate initial risk assessment
        risk_assessment = SupplierRiskService.calculate_basic_risk_score(
            industry=supplier_data.industry,
            company_size=supplier_data.company_size,
            country=supplier_data.country,
            employee_count=supplier_data.employee_count,
            revenue_range=supplier_data.revenue_range
        )
        
        # Set risk values from assessment
        db_supplier.risk_score = risk_assessment["risk_score"]
        db_supplier.risk_level = risk_assessment["risk_level"]
        db_supplier.risk_factors = risk_assessment["risk_factors"]
        
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        
        # TODO: Implement proper audit integration
        # await audit_action(
        #     action="supplier_created",
        #     resource_type="supplier",
        #     resource_id=db_supplier.id,
        #     details={
        #         "supplier_name": db_supplier.name,
        #         "organization_id": db_supplier.organization_id,
        #         "risk_score": db_supplier.risk_score,
        #         "risk_level": db_supplier.risk_level
        #     },
        #     request=request
        # )
        
        logger.info(
            "Supplier profile created successfully",
            supplier_id=db_supplier.id,
            name=db_supplier.name,
            organization_id=db_supplier.organization_id,
            **trace_context
        )
        
        return db_supplier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create supplier profile",
            error=str(e),
            supplier_name=supplier_data.name,
            **trace_context,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{supplier_id}/risk", response_model=SupplierRiskResponse)
async def get_supplier_risk(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Retrieve basic risk score and assessment for a supplier.
    
    This endpoint provides the current risk assessment and basic risk information.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Get supplier with latest risk assessment
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            logger.warning(
                "Supplier not found for risk assessment",
                supplier_id=supplier_id,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        # Get latest risk assessment
        latest_assessment = db.query(SupplierRiskAssessment).filter(
            SupplierRiskAssessment.supplier_id == supplier_id
        ).order_by(desc(SupplierRiskAssessment.created_at)).first()
        
        # Determine alert level based on risk score
        if supplier.risk_score >= 80:
            alert_level = "CRITICAL"
        elif supplier.risk_score >= 60:
            alert_level = "ALERT"
        elif supplier.risk_score >= 40:
            alert_level = "WARNING"
        else:
            alert_level = "INFO"
        
        # Generate recommendations using the risk service
        recommendations = SupplierRiskService.generate_recommendations(
            risk_score=supplier.risk_score,
            risk_factors=supplier.risk_factors,
            industry=supplier.industry
        )
        
        # Build risk response
        risk_response = SupplierRiskResponse(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            risk_score=supplier.risk_score,
            risk_level=supplier.risk_level,
            risk_factors=supplier.risk_factors,
            last_assessment=supplier.last_risk_assessment,
            assessment_method=latest_assessment.assessment_method if latest_assessment else "initial",
            news_sentiment=latest_assessment.news_sentiment if latest_assessment else None,
            financial_health=latest_assessment.financial_health if latest_assessment else None,
            compliance_status=latest_assessment.compliance_status if latest_assessment else None,
            recommendations=recommendations,
            watchlist_status=supplier.is_watchlisted,
            alert_level=alert_level
        )
        
        logger.info(
            "Supplier risk assessment retrieved successfully",
            supplier_id=supplier_id,
            risk_score=supplier.risk_score,
            risk_level=supplier.risk_level,
            **trace_context
        )
        
        return risk_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve supplier risk assessment",
            error=str(e),
            supplier_id=supplier_id,
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{supplier_id}/risk/enhanced", response_model=SupplierRiskResponse)
async def get_enhanced_supplier_risk(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Retrieve enhanced risk assessment using external data sources.
    
    This endpoint aggregates data from public sources (news APIs, financial data APIs)
    to provide a more comprehensive risk assessment.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Get supplier
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            logger.warning(
                "Supplier not found for enhanced risk assessment",
                supplier_id=supplier_id,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        # Calculate enhanced risk score using external data
        enhanced_risk = await SupplierRiskService.calculate_enhanced_risk_score(
            supplier_name=supplier.name,
            industry=supplier.industry,
            company_size=supplier.company_size,
            country=supplier.country,
            employee_count=supplier.employee_count,
            revenue_range=supplier.revenue_range
        )
        
        # Update supplier with enhanced risk assessment
        supplier.risk_score = enhanced_risk["risk_score"]
        supplier.risk_level = enhanced_risk["risk_level"]
        supplier.risk_factors = enhanced_risk["risk_factors"]
        supplier.last_risk_assessment = datetime.utcnow()
        
        # Create new risk assessment record
        new_assessment = SupplierRiskAssessment(
            supplier_id=supplier.id,
            risk_score=enhanced_risk["risk_score"],
            risk_level=enhanced_risk["risk_level"],
            risk_factors=enhanced_risk["risk_factors"],
            assessment_method=enhanced_risk["assessment_method"],
            data_sources=enhanced_risk.get("external_data", {}).get("data_sources", []),
            notes=f"Enhanced assessment with external data aggregation"
        )
        
        db.add(new_assessment)
        db.commit()
        db.refresh(supplier)
        
        # Determine alert level based on enhanced risk score
        if supplier.risk_score >= 80:
            alert_level = "CRITICAL"
        elif supplier.risk_score >= 60:
            alert_level = "ALERT"
        elif supplier.risk_score >= 40:
            alert_level = "WARNING"
        else:
            alert_level = "INFO"
        
        # Generate recommendations using the enhanced risk data
        recommendations = SupplierRiskService.generate_recommendations(
            risk_score=supplier.risk_score,
            risk_factors=supplier.risk_factors,
            industry=supplier.industry
        )
        
        # Add external data recommendations
        external_data = enhanced_risk.get("external_data", {})
        if external_data.get("risk_signals"):
            high_risk_signals = [
                signal for signal in external_data["risk_signals"] 
                if signal.severity in ["high", "critical"]
            ]
            if high_risk_signals:
                recommendations.append(
                    f"External data shows {len(high_risk_signals)} high/critical risk signals - recommend immediate review"
                )
        
        # Build enhanced risk response
        risk_response = SupplierRiskResponse(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            risk_score=supplier.risk_score,
            risk_level=supplier.risk_level,
            risk_factors=supplier.risk_factors,
            last_assessment=supplier.last_risk_assessment,
            assessment_method=enhanced_risk["assessment_method"],
            news_sentiment=None,  # Deprecated granular fields; see latest_news/external_data
            financial_health=None,  # Will be populated from external data if available
            compliance_status=None,  # Will be populated from external data if available
            recommendations=recommendations,
            watchlist_status=supplier.is_watchlisted,
            alert_level=alert_level,
            latest_news=[
                {
                    "title": a.title,
                    "description": a.description,
                    "url": a.url,
                    "published_at": a.published_at.isoformat() if hasattr(a, 'published_at') else None,
                    "source": a.source,
                    "sentiment_score": a.sentiment_score,
                    "relevance_score": a.relevance_score,
                    "risk_keywords": a.risk_keywords,
                }
                for a in enhanced_risk.get("external_data", {}).get("news_data", [])[:10]
            ] or None
        )
        
        logger.info(
            "Enhanced supplier risk assessment completed successfully",
            supplier_id=supplier_id,
            enhanced_risk_score=supplier.risk_score,
            risk_level=supplier.risk_level,
            external_signals=len(external_data.get("risk_signals", [])),
            **trace_context
        )
        
        return risk_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to complete enhanced supplier risk assessment",
            error=str(e),
            supplier_id=supplier_id,
            **trace_context,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or industry"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    watchlisted: Optional[bool] = Query(None, description="Filter by watchlist status")
):
    """
    List suppliers with pagination and filtering options.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Build query with filters
        query = db.query(Supplier)
        
        # Apply filters
        if search:
            search_filter = or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.industry.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if risk_level:
            query = query.filter(Supplier.risk_level == risk_level)
        
        if industry:
            query = query.filter(Supplier.industry == industry)
        
        if watchlisted is not None:
            query = query.filter(Supplier.is_watchlisted == watchlisted)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        suppliers = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        logger.info(
            "Suppliers list retrieved successfully",
            total_count=total_count,
            page=page,
            page_size=page_size,
            **trace_context
        )
        
        return SupplierListResponse(
            suppliers=suppliers,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to retrieve suppliers list",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get supplier by ID.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            logger.warning(
                "Supplier not found",
                supplier_id=supplier_id,
                **trace_context
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        logger.debug(
            "Supplier retrieved successfully",
            supplier_id=supplier_id,
            name=supplier.name,
            **trace_context
        )
        
        return supplier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve supplier",
            error=str(e),
            supplier_id=supplier_id,
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Update supplier information.
    """
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            logger.warning(
                "Supplier not found for update",
                supplier_id=supplier_id,
                **trace_context
            )
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
        
        # TODO: Implement proper audit integration
        # await audit_action(
        #     action="supplier_updated",
        #     resource_type="supplier",
        #     resource_id=supplier.id,
        #     details={
        #         "supplier_name": supplier.name,
        #         "updated_fields": list(update_data.keys())
        #         },
        #     request=request
        # )
        
        logger.info(
            "Supplier updated successfully",
            supplier_id=supplier_id,
            updated_fields=list(update_data.keys()),
            **trace_context
        )
        
        return supplier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update supplier",
            error=str(e),
            supplier_id=supplier_id,
            **trace_context,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
