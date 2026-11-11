from fastapi import APIRouter
from app.api.v1.endpoints import (
    analysis,
    auth,
    marketplace,
    materials,
    sites,
    surveys,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Users"])
api_router.include_router(sites.router, prefix="/sites", tags=["Demolition Sites"])
api_router.include_router(surveys.router, prefix="/surveys", tags=["Site Surveys & Image Evidence"])
api_router.include_router(materials.router, prefix="/materials", tags=["Detected Materials & Valuation"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["AI Analysis & Audit Reports"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["Secondary Materials Marketplace"])
