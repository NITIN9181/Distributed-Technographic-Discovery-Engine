"""
API Responses Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class User(BaseModel):
    id: str
    email: Optional[str] = None
    org_id: str
    role: str

class TechnologyResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None

class DetectionResponse(BaseModel):
    technology_id: str
    technology_name: str
    category: str
    vector: str
    evidence: str
    first_detected_at: datetime
    last_verified_at: datetime

class CompanyResponse(BaseModel):
    domain: str
    org_id: str
    last_scanned: datetime
    tech_count: int

class TechProfileResponse(BaseModel):
    domain: str
    last_scanned: datetime
    technologies: List[DetectionResponse]

class TechnologyAdoptionResponse(BaseModel):
    technology_id: str
    technology_name: str
    timeseries: List[Dict[str, Any]]
    totals: int
    newAdoptions: int
    churned: int

class SearchResult(BaseModel):
    type: str # 'company' or 'technology'
    id: str
    name: str
    snippet: Optional[str] = None

class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    failure_count: int

class ExportJob(BaseModel):
    id: str
    status: str
    created_at: datetime
    download_url: Optional[str] = None
