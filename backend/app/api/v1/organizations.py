"""
Organization API endpoints for organization management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.logging import get_current_trace_context
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Check if organization with same domain already exists
        if organization_data.domain:
            existing_org = db.query(Organization).filter(
                Organization.domain == organization_data.domain
            ).first()
            if existing_org:
                logger.warning(
                    "Organization creation failed - domain already exists",
                    domain=organization_data.domain,
                    **trace_context
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this domain already exists"
                )
        
        # Create new organization
        db_organization = Organization(**organization_data.dict())
        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
        
        logger.info(
            "Organization created successfully", 
            org_id=db_organization.id, 
            name=db_organization.name,
            domain=db_organization.domain,
            **trace_context
        )
        return db_organization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create organization", 
            error=str(e),
            organization_name=organization_data.name,
            domain=organization_data.domain,
            **trace_context,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: int, request: Request, db: Session = Depends(get_db)):
    """Get organization by ID."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning(
            "Organization not found",
            organization_id=organization_id,
            **trace_context
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    logger.debug(
        "Organization retrieved successfully",
        organization_id=organization_id,
        name=organization.name,
        **trace_context
    )
    
    return organization


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    skip: int = 0, 
    limit: int = 100, 
    request: Request = None,
    db: Session = Depends(get_db)
):
    """List all organizations with pagination."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    organizations = db.query(Organization).offset(skip).limit(limit).all()
    
    logger.debug(
        "Organizations listed successfully",
        count=len(organizations),
        skip=skip,
        limit=limit,
        **trace_context
    )
    
    return organizations 