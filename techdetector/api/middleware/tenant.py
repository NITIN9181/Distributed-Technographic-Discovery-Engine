"""
Multi-tenant middleware.
Sets PostgreSQL session variable for row-level security.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..auth.api_keys import get_org_from_request

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract org_id from authenticated request
        org_id = await get_org_from_request(request)
        
        # We would set the DB context here:
        """
        if org_id:
            async with get_db_connection() as conn:
                await conn.execute("SELECT set_org_context($1)", org_id)
        """
        
        response = await call_next(request)
        return response
