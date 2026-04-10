"""
API Requests Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class WebhookCreate(BaseModel):
    url: str
    events: List[str]

class WebhookUpdate(BaseModel):
    is_active: Optional[bool] = None
    events: Optional[List[str]] = None
