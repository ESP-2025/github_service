''' Authored by Akshata Madavi '''

import os
from typing import Dict

# Load required environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "ESP-2025")
GITHUB_REPO = os.getenv("GITHUB_REPO", "github_service")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
PORT = int(os.getenv("PORT", "8000"))

# Validate required vars when accessed (not at import time for testing)
def _validate_config():
    """Validate that required environment variables are set."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    if not WEBHOOK_SECRET:
        raise ValueError("WEBHOOK_SECRET environment variable is required")

def gh_headers() -> Dict[str, str]:
    """Return standard GitHub API headers with Bearer token and Accept header."""
    _validate_config()
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }