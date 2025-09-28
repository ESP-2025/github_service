import httpx
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from src import config

router = APIRouter()

@router.get("")
async def get_repo_issues(
	state: Optional[str] = Query(None, description="Issue state: open, closed, or all"),
	sort: Optional[str] = Query(None, description="Sort field"),
	direction: Optional[str] = Query(None, description="Sort direction"),
	per_page: Optional[int] = Query(30, description="Results per page (max 100)"),
	page: Optional[int] = Query(1, description="Page number")
):
	"""
	Fetch issues from a GitHub repository using the GitHub REST API.
	"""
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
		response = await client.get(url, params=params)
		response.raise_for_status()
		return response.json()
	
@router.get("/{issue_number}")
async def get_issue(issue_number: int):
    """
    Fetch a specific issue from a GitHub repository using the GitHub REST API.
    """
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/issues/{issue_number}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 404:
              raise HTTPException(status_code=404, detail="Issue not found")
        return response.json()