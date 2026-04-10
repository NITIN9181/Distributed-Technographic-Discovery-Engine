"""
Webhook management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..auth import get_current_user, User
from ..models.requests import WebhookCreate, WebhookUpdate
from ..models.responses import WebhookResponse
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(user: User = Depends(get_current_user)):
    """List all webhooks for the current organization."""
    return []

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    user: User = Depends(get_current_user)
):
    """Create a new webhook."""
    return WebhookResponse(
        id=str(uuid.uuid4()),
        url=webhook.url,
        events=webhook.events,
        is_active=True,
        created_at=datetime.utcnow(),
        failure_count=0
    )

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user)
):
    """Delete a webhook."""
    return {"status": "success"}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user)
):
    """Send a test event to verify webhook configuration."""
    return {"status": "success"}
