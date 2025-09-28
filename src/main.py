''' Authored by Akshata Madavi '''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import issues, webhooks

app = FastAPI(
    title="GitHub Service API",
    description="FastAPI wrapper for GitHub REST API for issues",
    version="0.1.0",
    openapi_version="3.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Return application health status."""
    return {"status": "ok"}

@app.get("/healthz")
def healthz_check():
    """Return application health status (alternative endpoint)."""
    return {"status": "ok"}

@app.get("/")
def read_root():
    """Return a simple welcome message."""
    return {"Hello": "World"}

# Include routers
app.include_router(issues.router, prefix="/issues", tags=["issues"])
app.include_router(webhooks.router, tags=["webhooks"])