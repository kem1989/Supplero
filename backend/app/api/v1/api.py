"""
Main API router for Supplero v1 API endpoints.
"""

from fastapi import APIRouter

# Import simplified route modules
from .auth import router as auth_router
from .organizations import router as organizations_router
from .audit import router as audit_router
from .audit_sink import router as audit_sink_router
from .ai_assistant import router as ai_assistant_router
from .suppliers import router as suppliers_router
from .contracts import router as contracts_router

# Create the main API router
api_router = APIRouter()

# Include simplified route modules
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(audit_router)
api_router.include_router(audit_sink_router)
api_router.include_router(ai_assistant_router)
api_router.include_router(suppliers_router)
api_router.include_router(contracts_router)

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