''' Authored by Akshata Madavi '''

import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import Response

from src import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for webhook events (in production, use a database)
webhook_events: List[Dict] = []
## Authored by  Parth Maradia
@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def receive_webhook(request: Request):
    """Receive and validate GitHub webhooks with HMAC signature verification."""
    # Get the raw body
    body = await request.body()
    
    # Get the signature from headers
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Verify HMAC signature
    if not _verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Get event type
    event_type = request.headers.get("X-GitHub-Event")
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event type")
    
    # Parse the payload
    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Handle different event types
    if event_type == "ping":
        logger.info("Received ping event")
        return Response(status_code=204)
    
    if event_type not in ["issues", "issue_comment"]:
        raise HTTPException(status_code=400, detail=f"Unsupported event type: {event_type}")
    
    # Extract event details
    action = payload.get("action")
    issue_number = None
    
    if event_type == "issues" and "issue" in payload:
        issue_number = payload["issue"].get("number")
    elif event_type == "issue_comment" and "issue" in payload:
        issue_number = payload["issue"].get("number")
    
    # Store the event
    event_id = f"{event_type}_{action}_{datetime.now().timestamp()}"
    webhook_event = {
        "id": event_id,
        "event": event_type,
        "action": action,
        "issue_number": issue_number,
        "timestamp": datetime.now().isoformat(),
        "payload": payload  # Store full payload for debugging
    }
    
    webhook_events.append(webhook_event)
    
    # Log the event
    logger.info(f"Processed webhook: {event_type}.{action} for issue #{issue_number}")
    
    return Response(status_code=204)
## Authored by  Parth Maradia
@router.get("/events")
async def get_webhook_events(limit: int = 50):
    """Get the last N processed webhook events for debugging purposes."""
    # Return the most recent events
    recent_events = webhook_events[-limit:] if len(webhook_events) > limit else webhook_events
    
    # Format response
    formatted_events = []
    for event in recent_events:
        formatted_events.append({
            "id": event["id"],
            "event": event["event"],
            "action": event["action"],
            "issue_number": event["issue_number"],
            "timestamp": event["timestamp"]
        })
    
    return formatted_events

def _verify_signature(body: bytes, signature: str) -> bool:
    """Verify the HMAC SHA-256 signature of the webhook payload using the webhook secret."""
    if not signature.startswith("sha256="):
        return False
    
    # Remove the "sha256=" prefix
    signature = signature[7:]
    
    # Validate config and get webhook secret
    from src.config import _validate_config
    _validate_config()
    
    # Create the expected signature
    expected_signature = hmac.new(
        config.WEBHOOK_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)
