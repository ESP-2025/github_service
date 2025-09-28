''' Authored by Akshata Madavi '''

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CreateIssueRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Issue title")
    body: Optional[str] = Field(None, description="Issue body")
    labels: Optional[List[str]] = Field(None, description="Issue labels")

class UpdateIssueRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Issue title")
    body: Optional[str] = Field(None, description="Issue body")
    state: Optional[str] = Field(None, pattern="^(open|closed)$", description="Issue state")

class CreateCommentRequest(BaseModel):
    body: str = Field(..., min_length=1, description="Comment body")

class IssueResponse(BaseModel):
    number: int
    html_url: str
    state: str
    title: str
    body: Optional[str]
    labels: List[str]  # Normalized to list of names
    created_at: datetime
    updated_at: datetime

class CommentResponse(BaseModel):
    id: int
    body: str
    user: dict
    created_at: datetime
    html_url: str

class WebhookEvent(BaseModel):
    id: str
    event: str
    action: Optional[str]
    issue_number: Optional[int]
    timestamp: datetime
