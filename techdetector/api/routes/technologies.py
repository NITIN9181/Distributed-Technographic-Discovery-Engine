"""
Technology endpoints.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from ..auth import get_current_user, User
from ..models.responses import TechnologyResponse, TechnologyAdoptionResponse

router = APIRouter()

@router.get("/technologies", response_model=List[TechnologyResponse])
async def list_technologies(
    category: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List all detectable technologies."""
    return []

@router.get("/technologies/{tech_id}", response_model=TechnologyResponse)
async def get_technology(
    tech_id: str,
    user: User = Depends(get_current_user)
):
    """Get details about a specific technology."""
    return TechnologyResponse(id=tech_id, name=tech_id, category="Unknown")

@router.get("/technologies/{tech_id}/companies", response_model=List[str])
async def get_companies_using_technology(
    tech_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """List companies using a specific technology."""
    return []

@router.get("/technologies/trends", response_model=TechnologyAdoptionResponse)
async def get_adoption_trends(
    tech: str = Query(...),
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(get_current_user)
):
    """Get adoption trend data for a technology."""
    tech_list = tech.split(",")
    return TechnologyAdoptionResponse(
        technology_id=tech_list[0],
        technology_name=tech_list[0],
        timeseries=[],
        totals=0,
        newAdoptions=0,
        churned=0
    )
