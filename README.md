## GitHub Service

Follow the instructions below to set up and run the project.

---

### 1. Clone the Repository

```bash
git clone https://github.com/ESP-2025/github_service
cd github_service
```

---

### 2. Set Up Environment Variables

Rename the `.env.example` file to just `.env` and add your GitHub API Token.

---

### 3. Install Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

> Note: Dependencies will be automatically installed and synced anytime you run `uv` command.

---

### 4. Run the Server

```bash
uv run uvicorn src.main:app --reload
```

---

### 5. Run Tests with Pytest

```bash
uv run pytest
```

---

### 6. Build and Run with Docker

#### Build Docker Image
```bash
docker build -t github_service .
```

#### Run Docker Container
```bash
docker run --env-file .env -p 8000:8000 github_service
```

---

## Project Structure

```
src/        # Source code
tests/      # Test suite
Dockerfile  # Docker configuration
pyproject.toml # Python project config
```

---

## Contributions

| Name    | Contribution                                                                 |
|---------|-------------------------------------------------------------------------------|
| Akshata | Initial project scaffolding, pytest setup, `GET /issues`, `GET /issues/{number}` endpoints. |
| Joshini |                                                                               |
| Parth   |                                                                               |
| Sankalp |                                                                               |
