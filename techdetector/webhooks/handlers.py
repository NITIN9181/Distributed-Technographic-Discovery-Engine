"""
Event handlers that trigger webhooks.
Integrated into the worker pipeline.
"""
from .dispatcher import WebhookDispatcher, WebhookEvent
from ..models import Detection
from datetime import datetime

class WebhookEventHandler:
    def __init__(self, dispatcher: WebhookDispatcher):
        self.dispatcher = dispatcher
    
    async def on_scan_completed(self, domain: str, detections: list, org_id: str):
        """Trigger scan.completed event."""
        await self.dispatcher.dispatch(WebhookEvent(
            event_type="scan.completed",
            org_id=org_id,
            payload={
                "domain": domain,
                "technologies_found": len(detections),
                "scan_timestamp": datetime.utcnow().isoformat()
            }
        ))
    
    async def on_technology_detected(self, domain: str, detection: Detection, 
                                      is_new: bool, org_id: str):
        """Trigger technology.detected event for new technologies."""
        if is_new:
            await self.dispatcher.dispatch(WebhookEvent(
                event_type="technology.detected",
                org_id=org_id,
                payload={
                    "domain": domain,
                    "technology": detection.technology.id,
                    "technology_name": detection.technology.name,
                    "category": detection.technology.category,
                    "detection_vector": detection.vector.value,
                    "evidence": detection.evidence
                }
            ))
