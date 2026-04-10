"""
Search endpoints.
"""
from fastapi import APIRouter, Depends, Query
from typing import List
from ..auth import get_current_user, User
from ..models.responses import SearchResult

router = APIRouter()

@router.get("/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=2),
    type: str = Query("all", pattern="^(all|companies|technologies)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user)
):
    """Universal search across companies and technologies."""
    return []
