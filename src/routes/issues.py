import httpx
import time
import hashlib
from typing import Optional, Dict
from fastapi import APIRouter, Query, HTTPException, Response, status, Request
from fastapi.responses import JSONResponse

from src import config
from src.models import CreateIssueRequest, UpdateIssueRequest, CreateCommentRequest

router = APIRouter()

# In-memory cache for ETags
etag_cache: Dict[str, str] = {}

## Authored by Akshata Madavi
@router.get("")
async def get_repo_issues(
    request: Request,
    state: Optional[str] = Query(None, description="Issue state: open, closed, or all"),
    sort: Optional[str] = Query(None, description="Sort field"),
    direction: Optional[str] = Query(None, description="Sort direction"),
    per_page: Optional[int] = Query(30, description="Results per page (max 100)"),
    page: Optional[int] = Query(1, description="Page number")
):
    """Fetch issues from a GitHub repository with pagination and filtering, with ETag caching support."""
    # Build cache key from parameters
    cache_key = _build_cache_key("issues", state, sort, direction, per_page, page)

    # Check for If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and cache_key in etag_cache and etag_cache[cache_key] == if_none_match:
        return Response(status_code=304)

    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues"
    params = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": per_page,
        "page": page
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=config.gh_headers())
            await _handle_github_response(response)
            issues_data = response.json()
            # Normalize each issue in the list
            normalized_issues = [_normalize_issue_response(issue) for issue in issues_data]
            # Collect headers to forward
            headers_out = {}
            etag = response.headers.get("ETag")
            if etag:
                etag_cache[cache_key] = etag
                headers_out["ETag"] = etag

            link = response.headers.get("Link")
            if link:
                headers_out["Link"] = link  # propagate GitHub pagination

            # Optionally forward rate-limit headers too:
            for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
                if h in response.headers:
                    headers_out[h] = response.headers[h]

            if headers_out:
                return JSONResponse(content=normalized_issues, headers=headers_out)
            else:
                return normalized_issues

        except httpx.HTTPStatusError as e:
            await _handle_github_error(e)
## Authored by Akshata Madavi
@router.get("/{number}")
async def get_issue(number: int, request: Request):
    """Fetch a specific issue by its number from the GitHub repository, with ETag caching support."""
    # Build cache key for specific issue
    cache_key = f"issue_{number}"
    
    # Check for If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and cache_key in etag_cache and etag_cache[cache_key] == if_none_match:
        return Response(status_code=304)
    
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/{number}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=config.gh_headers())
            await _handle_github_response(response)
            normalized_issue = _normalize_issue_response(response.json())
            
            # Store ETag in cache and return with ETag header
            etag = response.headers.get("ETag")
            if etag:
                etag_cache[cache_key] = etag
                return JSONResponse(
                    content=normalized_issue,
                    headers={"ETag": etag}
                )
            
            return normalized_issue
        except httpx.HTTPStatusError as e:
            await _handle_github_error(e)

## Authored by Joshini M Naagraj
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_issue(issue_data: CreateIssueRequest, response: Response):
    """Create a new issue in the GitHub repository and return the created issue."""
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues"
    
    async with httpx.AsyncClient() as client:
        try:
            response_gh = await client.post(url, json=issue_data.dict(), headers=config.gh_headers())
            await _handle_github_response(response_gh)
            
            issue_data_response = response_gh.json()
            response.headers["Location"] = f"/issues/{issue_data_response['number']}"
            
            return _normalize_issue_response(issue_data_response)
        except httpx.HTTPStatusError as e:
            await _handle_github_error(e)

## Authored by Joshini M Naagraj
@router.patch("/{number}")
async def update_issue(number: int, issue_data: UpdateIssueRequest):
    """Update an existing issue (title, body, or state) in the GitHub repository."""
    # Reject empty body
    if not issue_data.dict(exclude_unset=True):
        raise HTTPException(status_code=400, detail="Request body cannot be empty")
    
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/{number}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(url, json=issue_data.dict(exclude_unset=True), headers=config.gh_headers())
            await _handle_github_response(response)
            return _normalize_issue_response(response.json())
        except httpx.HTTPStatusError as e:
            await _handle_github_error(e)

## Authored by Sankalp Wahane
@router.post("/{number}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(number: int, comment_data: CreateCommentRequest):
    """Add a comment to an existing issue."""
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/{number}/comments"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=comment_data.dict(), headers=config.gh_headers())
            await _handle_github_response(response)
            return response.json()
        except httpx.HTTPStatusError as e:
            await _handle_github_error(e)

# Helper functions
async def _handle_github_response(response: httpx.Response):
    """Handle GitHub API response and raise appropriate HTTP exceptions for errors."""
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid GitHub token")
    elif response.status_code == 403:
        # Check for rate limiting
        if "X-RateLimit-Remaining" in response.headers and response.headers["X-RateLimit-Remaining"] == "0":
            retry_after = response.headers.get("X-RateLimit-Reset", str(int(time.time()) + 60))
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded",
                headers={"Retry-After": retry_after}
            )
        raise HTTPException(status_code=403, detail="Forbidden")
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="Not found")
    elif response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Upstream failure")
    elif not response.is_success:
        raise HTTPException(status_code=400, detail="Bad request")

async def _handle_github_error(e: httpx.HTTPStatusError):
    """Handle GitHub API HTTP errors and map them to appropriate HTTP status codes."""
    if e.response.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid GitHub token")
    elif e.response.status_code == 403:
        # Check for rate limiting
        if "X-RateLimit-Remaining" in e.response.headers and e.response.headers["X-RateLimit-Remaining"] == "0":
            retry_after = e.response.headers.get("X-RateLimit-Reset", str(int(time.time()) + 60))
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded",
                headers={"Retry-After": retry_after}
            )
        raise HTTPException(status_code=403, detail="Forbidden")
    elif e.response.status_code == 404:
        raise HTTPException(status_code=404, detail="Not found")
    elif e.response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Upstream failure")
    else:
        raise HTTPException(status_code=400, detail="Bad request")

def _build_cache_key(endpoint: str, *args) -> str:
    """Build a cache key from endpoint and parameters."""
    # Create a hash of all parameters to ensure uniqueness
    param_str = "_".join(str(arg) if arg is not None else "None" for arg in args)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
    return f"{endpoint}_{param_hash}"

def _normalize_issue_response(issue_data: dict) -> dict:
    """Normalize GitHub issue response by converting labels from objects to list of names."""
    # Convert labels from objects to list of names
    if "labels" in issue_data and issue_data["labels"]:
        issue_data["labels"] = [label.get("name", "") for label in issue_data["labels"] if isinstance(label, dict)]
    else:
        issue_data["labels"] = []
    
    return issue_data