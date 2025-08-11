"""
Main API router for Supplero v1 API endpoints.
"""

from fastapi import APIRouter

# Import all route modules here
from .auth import router as auth_router
from .organizations import router as organizations_router
from .audit import router as audit_router
# from .contracts import router as contracts_router
# from .suppliers import router as suppliers_router
# from .ai_analysis import router as ai_analysis_router

# Create the main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(audit_router)
# api_router.include_router(contracts_router, prefix="/contracts", tags=["contracts"])
# api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
# api_router.include_router(ai_analysis_router, prefix="/ai", tags=["ai-analysis"])

# Root API endpoint
@api_router.get("/")
async def api_root():
    """Root endpoint for the v1 API."""
    return {
        "message": "Supplero API v1",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    } 