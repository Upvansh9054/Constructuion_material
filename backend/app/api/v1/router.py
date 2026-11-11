from fastapi import APIRouter
from app.api.v1.endpoints import (
    analysis,
    audit_logs,
    auth,
    buyers,
    marketplace,
    materials,
    reports,
    sites,
    surveys,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Users (Module 1, 2)"])
api_router.include_router(sites.router, prefix="/sites", tags=["Demolition Sites & Structures (Module 3, 4)"])
api_router.include_router(surveys.router, prefix="/surveys", tags=["Site Surveys & Image Evidence (Module 5)"])
api_router.include_router(materials.router, prefix="/materials", tags=["Detected Materials & Valuation (Module 7, 8, 9, 10)"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["AI Analysis & Jobs (Module 6)"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["Secondary Materials Marketplace & Bids (Module 12, 13)"])
api_router.include_router(buyers.router, prefix="/buyers", tags=["Buyers & Recyclers Directory (Module 11)"])
api_router.include_router(reports.router, prefix="/reports", tags=["Pre-Demolition Audit Reports (DMAR) (Module 14)"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Regulatory Audit Ledger (Module 15)"])
