"""
Company endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from ..auth import get_current_user, User
from ..models.responses import CompanyResponse, TechProfileResponse
from datetime import datetime

router = APIRouter()

@router.get("/companies", response_model=List[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    technology: Optional[str] = None,
    category: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List companies with optional filtering."""
    # Mock return for Phase 6 build context
    return []

@router.get("/companies/{domain}", response_model=TechProfileResponse)
async def get_company_profile(
    domain: str,
    user: User = Depends(get_current_user)
):
    """
    Get complete technographic profile for a company.
    """
    return TechProfileResponse(
        domain=domain,
        last_scanned=datetime.utcnow(),
        technologies=[]
    )

@router.post("/companies/{domain}/scan")
async def trigger_scan(
    domain: str,
    force: bool = False,
    user: User = Depends(get_current_user)
):
    """Trigger a new scan for a company."""
    from techdetector.orchestrator import Orchestrator
    # We would enqueue here
    return {"status": "queued", "domain": domain}
