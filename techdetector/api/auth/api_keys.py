"""
API Keys authentication.
"""
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
import hashlib
from typing import Optional
from ..models.responses import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> User:
    """
    Verify API key and return associated user/org.
    API keys are stored as SHA256 hashes.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Temporarily returning mock org until database is ready
    return User(
        id="00000000-0000-0000-0000-000000000000",
        org_id="00000000-0000-0000-0000-000000000000",
        role="member"
    )

async def get_current_user(user: User = Security(verify_api_key)) -> User:
    return user

async def get_org_from_request(request: Request) -> Optional[str]:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return "00000000-0000-0000-0000-000000000000"
    return None
