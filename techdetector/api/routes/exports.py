"""
Bulk data export endpoints.
"""
from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import csv
import io
import json
from datetime import datetime
import uuid
from ..auth import get_current_user, User
from ..models.responses import ExportJob

router = APIRouter()

@router.post("/exports", response_model=ExportJob)
async def create_export(
    background_tasks: BackgroundTasks,
    format: str = Query("csv", pattern="^(csv|json|jsonl)$"),
    technology: Optional[str] = None,
    category: Optional[str] = None,
    since: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Create a bulk export job."""
    job_id = str(uuid.uuid4())
    return ExportJob(
        id=job_id,
        status="pending",
        created_at=datetime.utcnow()
    )

@router.get("/exports/{job_id}")
async def get_export_status(
    job_id: str,
    user: User = Depends(get_current_user)
):
    """Get export job status and download link when complete."""
    return ExportJob(
        id=job_id,
        status="completed",
        created_at=datetime.utcnow(),
        download_url=f"/api/v1/exports/{job_id}/download"
    )

@router.get("/exports/{job_id}/download")
async def download_export(
    job_id: str,
    user: User = Depends(get_current_user)
):
    """Download completed export file."""
    # Mocking stream
    def generate():
        yield b"domain,technology\nexample.com,fastapi\n"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=techdetector_export_{job_id}.csv"
        }
    )
