''' Authored by Parth Maradia '''
import json
import time
import pytest
from fastapi.testclient import TestClient
from httpx import Response
from src.main import app
from src import config

client = TestClient(app)

def test_create_issue_happy_path(httpx_mock):
    """Test successful issue creation with proper response and Location header."""
    gh_resp = {
        "number": 123, "html_url": "https://github.com/x/y/issues/123",
        "state": "open", "title": "t", "body": "b", "labels": [{"name": "bug"}],
        "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="POST",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues",
        status_code=201,
        json=gh_resp,
    )
    r = client.post("/issues", json={"title": "t", "body": "b", "labels": ["bug"]})
    assert r.status_code == 201
    assert r.headers["Location"] == "/issues/123"
    data = r.json()
    assert data["labels"] == ["bug"]

def test_create_issue_missing_title():
    """Test issue creation fails when title is missing (validation error)."""
    r = client.post("/issues", json={"body": "no title"})
    assert r.status_code == 422 or r.status_code == 400  # Pydantic validation -> 422 in FastAPI

def test_rate_limited_on_create(httpx_mock, monkeypatch):
    """Test that rate limiting is properly handled with Retry-After header."""
    reset = str(int(time.time()) + 42)
    httpx_mock.add_response(
        method="POST",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues",
        status_code=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset},
        json={"message": "API rate limit exceeded"},
    )
    r = client.post("/issues", json={"title": "t"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers

def test_patch_close_issue(httpx_mock):
    """Test that an issue can be closed via PATCH request."""
    gh_resp = {
        "number": 123, "html_url": "https://github.com/x/y/issues/123",
        "state": "closed", "title": "t", "body": "b", "labels": [],
        "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-02T00:00:00Z",
    }
    httpx_mock.add_response(
        method="PATCH",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/123",
        status_code=200,
        json=gh_resp,
    )
    r = client.patch("/issues/123", json={"state": "closed"})
    assert r.status_code == 200
    assert r.json()["state"] == "closed"

def test_patch_issue_not_found(httpx_mock):
    """Test that PATCH request returns 404 for non-existent issues."""
    httpx_mock.add_response(
        method="PATCH",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/999",
        status_code=404,
        json={"message": "Not Found"},
    )
    r = client.patch("/issues/999", json={"title": "x"})
    assert r.status_code == 404

def test_patch_empty_body():
    """Test that PATCH request with empty body returns 400 error."""
    r = client.patch("/issues/123", json={})
    assert r.status_code == 400

def test_get_issues(httpx_mock):
    """Test that GET /issues returns a list of issues with normalized labels."""
    gh_resp = [
        {
            "number": 1, "html_url": "https://github.com/x/y/issues/1",
            "state": "open", "title": "Issue 1", "body": "Body 1", "labels": [{"name": "bug"}],
            "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
        }
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues?per_page=30&page=1",
        status_code=200,
        json=gh_resp,
        headers={"ETag": '"abc123"'},
        match_headers={"Authorization": "Bearer test_token"},
    )
    r = client.get("/issues")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["labels"] == ["bug"]
    assert r.headers.get("ETag") == '"abc123"'

def test_get_issue_by_number(httpx_mock):
    """Test that GET /issues/{number} returns a specific issue with normalized labels."""
    gh_resp = {
        "number": 123, "html_url": "https://github.com/x/y/issues/123",
        "state": "open", "title": "Test Issue", "body": "Test Body", "labels": [{"name": "enhancement"}],
        "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/123",
        status_code=200,
        json=gh_resp,
        headers={"ETag": '"def456"'},
    )
    r = client.get("/issues/123")
    assert r.status_code == 200
    data = r.json()
    assert data["number"] == 123
    assert data["labels"] == ["enhancement"]
    assert r.headers.get("ETag") == '"def456"'

def test_create_comment(httpx_mock):
    """Test that a comment can be added to an issue successfully."""
    gh_resp = {
        "id": 456, "body": "Test comment", "user": {"login": "testuser"},
        "created_at": "2025-01-01T00:00:00Z", "html_url": "https://github.com/x/y/issues/123#issuecomment-456"
    }
    httpx_mock.add_response(
        method="POST",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/123/comments",
        status_code=201,
        json=gh_resp,
    )
    r = client.post("/issues/123/comments", json={"body": "Test comment"})
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == 456
    assert data["body"] == "Test comment"

def test_conditional_get_issues_304(httpx_mock):
    """Test that GET /issues returns 304 Not Modified when If-None-Match matches cached ETag."""
    # First request - cache the ETag
    gh_resp = [
        {
            "number": 1, "html_url": "https://github.com/x/y/issues/1",
            "state": "open", "title": "Issue 1", "body": "Body 1", "labels": [{"name": "bug"}],
            "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
        }
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues?per_page=30&page=1",
        status_code=200,
        json=gh_resp,
        headers={"ETag": '"abc123"'},
    )
    
    # First request to cache the ETag
    r1 = client.get("/issues")
    assert r1.status_code == 200
    assert r1.headers.get("ETag") == '"abc123"'
    
    # Second request with If-None-Match header - should return 304
    r2 = client.get("/issues", headers={"If-None-Match": '"abc123"'})
    assert r2.status_code == 304

def test_conditional_get_issue_304(httpx_mock):
    """Test that GET /issues/{number} returns 304 Not Modified when If-None-Match matches cached ETag."""
    # First request - cache the ETag
    gh_resp = {
        "number": 123, "html_url": "https://github.com/x/y/issues/123",
        "state": "open", "title": "Test Issue", "body": "Test Body", "labels": [{"name": "enhancement"}],
        "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/123",
        status_code=200,
        json=gh_resp,
        headers={"ETag": '"def456"'},
    )
    
    # First request to cache the ETag
    r1 = client.get("/issues/123")
    assert r1.status_code == 200
    assert r1.headers.get("ETag") == '"def456"'
    
    # Second request with If-None-Match header - should return 304
    r2 = client.get("/issues/123", headers={"If-None-Match": '"def456"'})
    assert r2.status_code == 304

def test_conditional_get_issues_different_etag(httpx_mock):
    """Test that GET /issues makes GitHub API call when If-None-Match doesn't match cached ETag."""
    # First request - cache the ETag
    gh_resp1 = [
        {
            "number": 1, "html_url": "https://github.com/x/y/issues/1",
            "state": "open", "title": "Issue 1", "body": "Body 1", "labels": [{"name": "bug"}],
            "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
        }
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues?per_page=30&page=1",
        status_code=200,
        json=gh_resp1,
        headers={"ETag": '"abc123"'},
    )
    
    # First request to cache the ETag
    r1 = client.get("/issues")
    assert r1.status_code == 200
    assert r1.headers.get("ETag") == '"abc123"'
    
    # Second request with different If-None-Match header - should make GitHub API call
    gh_resp2 = [
        {
            "number": 1, "html_url": "https://github.com/x/y/issues/1",
            "state": "open", "title": "Updated Issue 1", "body": "Updated Body 1", "labels": [{"name": "enhancement"}],
            "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-02T00:00:00Z",
        }
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues?per_page=30&page=1",
        status_code=200,
        json=gh_resp2,
        headers={"ETag": '"xyz789"'},
    )
    
    r2 = client.get("/issues", headers={"If-None-Match": '"different_etag"'})
    assert r2.status_code == 200
    assert r2.headers.get("ETag") == '"xyz789"'
    data = r2.json()
    assert data[0]["title"] == "Updated Issue 1"
