''' Authored by Akshata Madavi '''

import sys
import os

# Set environment variables before any imports
env_vars = {
    "GITHUB_TOKEN": "test_token",
    "GITHUB_OWNER": "test_owner",
    "GITHUB_REPO": "test_repo",
    "WEBHOOK_SECRET": "test_secret",
    "PORT": "8000"
}

for key, value in env_vars.items():
    os.environ[key] = value

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
