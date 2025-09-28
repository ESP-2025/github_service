# GitHub Service API

A FastAPI wrapper for the GitHub REST API focused on issues management with webhook support.

## Features

- **CRUD Operations for Issues**: Create, read, update, and close issues
- **Comments Management**: Add comments to issues
- **Webhook Receiver**: HMAC-validated webhook endpoint for GitHub events
- **Error Handling**: Proper HTTP status code mapping and error responses
- **Rate Limit Handling**: Automatic retry-after header handling
- **OpenAPI 3.1**: Complete API documentation
- **Docker Support**: Containerized deployment
- **Comprehensive Testing**: Unit and integration tests

## API Endpoints

### Issues
- `GET /issues` - List issues with pagination and filtering
- `GET /issues/{number}` - Get a specific issue
- `POST /issues` - Create a new issue
- `PATCH /issues/{number}` - Update an issue (including close)
- `POST /issues/{number}/comments` - Add a comment to an issue

### Webhooks
- `POST /webhook` - GitHub webhook receiver with HMAC validation
- `GET /events` - List processed webhook events

### Health Checks
- `GET /health` - Health check endpoint
- `GET /healthz` - Alternative health check endpoint

## Setup

### Environment Variables

Create a `.env` file with the following variables:

```bash
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_repository_name
WEBHOOK_SECRET=your_webhook_secret_here
PORT=8000
```

### Installation

1. **Using pip:**
```bash
pip install -r requirements.txt
```

2. **Using uv (recommended):**
```bash
uv sync
```

### Running the Application

1. **Development mode:**
```bash
uvicorn src.main:app --reload --port $PORT
```

2. **Production mode:**
```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

3. **Using Docker:**
```bash
docker build -t github-service .
docker run -p 8000:8000 --env-file .env github-service
```

## Testing

Run the test suite:

```bash
pytest -v
```

## Usage Examples

### Create an Issue
```bash
curl -X POST http://localhost:8000/issues \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo Issue","body":"This is a demo issue","labels":["bug"]}'
```

### Close an Issue
```bash
curl -X PATCH http://localhost:8000/issues/123 \
  -H 'Content-Type: application/json' \
  -d '{"state":"closed"}'
```

### Add a Comment
```bash
curl -X POST http://localhost:8000/issues/123/comments \
  -H 'Content-Type: application/json' \
  -d '{"body":"This is a comment"}'
```

### List Issues
```bash
curl http://localhost:8000/issues?state=open&per_page=10
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Error Handling

The API provides proper HTTP status codes:

- `200` - Success
- `201` - Created (for new resources)
- `400` - Bad Request (invalid payload)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden
- `404` - Not Found
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limited)
- `503` - Service Unavailable (upstream failures)

## Webhook Configuration

To set up GitHub webhooks:

1. Go to your repository settings
2. Navigate to "Webhooks"
3. Add a new webhook with:
   - **Payload URL**: `https://your-domain.com/webhook`
   - **Content type**: `application/json`
   - **Secret**: Use the same value as `WEBHOOK_SECRET`
   - **Events**: Select "Issues" and "Issue comments"

## Development

### Project Structure
```
src/
├── main.py          # FastAPI application
├── config.py        # Configuration and environment variables
├── models.py        # Pydantic models
└── routes/
    ├── issues.py    # Issue-related endpoints
    └── webhooks.py  # Webhook endpoints

tests/
├── conftest.py      # Test configuration
├── test_main.py     # Basic app tests
├── test_issues.py   # Issue endpoint tests
└── test_webhooks.py # Webhook tests
```

### Adding New Features

1. Add new endpoints to the appropriate router
2. Create Pydantic models for request/response validation
3. Add comprehensive tests
4. Update the OpenAPI documentation

## Contributions

| Name    | Contribution                                                                 |
|---------|-------------------------------------------------------------------------------|
| Akshata | Initial project scaffolding, pytest setup, `GET /issues`, `GET /issues/{number}` endpoints, tests |
| Joshini | Post & Patch operations, webhooks, handling, tests, Docker setup  |
| Parth   | webhooks, tests , Documentation, Cache an ETag                              |
| Sankalp | error handling, tests, OpenAPI contract                                      |
