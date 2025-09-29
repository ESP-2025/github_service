''' Authored by Sankalp Wahane'''
# tests/test_webhooks.py
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from src.main import app
from src import config

client = TestClient(app)

def _create_signature(body: bytes, secret: str) -> str:
    """Create HMAC SHA-256 signature for webhook payload testing."""
    signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_webhook_ping():
    """Test that webhook ping events are handled correctly."""
    payload = {"zen": "Keep it logically awesome."}
    body = json.dumps(payload).encode('utf-8')
    signature = _create_signature(body, config.WEBHOOK_SECRET)
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "ping",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 204

def test_webhook_issues_opened():
    """Test that issue opened webhook events are processed correctly."""
    payload = {
        "action": "opened",
        "issue": {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body"
        }
    }
    body = json.dumps(payload).encode('utf-8')
    signature = _create_signature(body, config.WEBHOOK_SECRET)
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 204

def test_webhook_issue_comment():
    """Test that issue comment webhook events are processed correctly."""
    payload = {
        "action": "created",
        "issue": {
            "number": 123
        },
        "comment": {
            "id": 456,
            "body": "Test comment"
        }
    }
    body = json.dumps(payload).encode('utf-8')
    signature = _create_signature(body, config.WEBHOOK_SECRET)
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "issue_comment",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 204

def test_webhook_invalid_signature():
    """Test that webhooks with invalid signatures are rejected."""
    payload = {"test": "data"}
    body = json.dumps(payload).encode('utf-8')
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 401

def test_webhook_missing_signature():
    """Test that webhooks without signatures are rejected."""
    payload = {"test": "data"}
    body = json.dumps(payload).encode('utf-8')
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 401

def test_webhook_unsupported_event():
    """Test that webhooks with unsupported event types are rejected."""
    payload = {"test": "data"}
    body = json.dumps(payload).encode('utf-8')
    signature = _create_signature(body, config.WEBHOOK_SECRET)
    
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 400

def test_get_webhook_events():
    """Test that webhook events can be retrieved via GET /events endpoint."""
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_webhook_events_with_limit():
    """Test that webhook events can be retrieved with a limit parameter."""
    response = client.get("/events?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
