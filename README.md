# Chief of Staff API

A production-grade FastAPI backend service built with modern tooling and strict guardrails.

## Overview

This project is configured to provide a seamless developer experience while enforcing strict code quality standards. The setup ensures that all code written adheres to the same style, is properly typed, and includes necessary tests before merging.

### Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)
- **Formatting**: [Black](https://github.com/psf/black)
- **Linting**: [Ruff](https://docs.astral.sh/ruff/)
- **Type Checking**: [Mypy](https://mypy.readthedocs.io/)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Settings Management**: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## 🚀 Getting Started (Local Development)

### Prerequisites

Ensure you have the following installed on your machine:

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Fast Python package and project manager)
- [Docker](https://docs.docker.com/get-docker/) (optional, for containerized environments)

### 1. Setup Environment

First, duplicate the example environment file:

```bash
cp .env.example .env
```

_(Update the `.env` file with your specific local credentials if necessary)._

### 2. Install Dependencies

Use `uv` to create a virtual environment and install dependencies (including development tools):

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks

Pre-commit hooks are **mandatory**. They run formatting, linting, and type checking automatically before every commit to ensure no bad code enters the repository.

```bash
pre-commit install
```

### 4. Run the Development Server

Start the application with live-reloading enabled:

```bash
uvicorn app.main:app --reload
```

- API is available at: `http://localhost:8080`
- Interactive Swagger UI Docs: `http://localhost:8080/docs`
- Alternative Redoc Docs: `http://localhost:8080/redoc`

---

## 🛠 Code Quality & Checks

This project enforces strict code quality. You can run any of the following tools manually to check your code:

**Format the codebase:**

```bash
uv run black .
```

**Run the linter:**

```bash
uv run ruff check .
# To automatically fix linting issues:
uv run ruff check --fix .
```

**Run type checking:**

```bash
uv run mypy .
```

**Run the test suite:**

```bash
uv run pytest
```

---

## 📂 Project Structure

```
.
├── .github/                # GitHub Actions CI/CD workflows
├── app/
│   ├── api/                # API routers and endpoints
│   ├── core/               # Core application configuration (settings, security, etc.)
│   ├── models/             # Database models (e.g., SQLAlchemy/SQLModel)
│   ├── schemas/            # Pydantic validation schemas (requests/responses)
│   ├── services/           # Business logic and complex operations
│   └── main.py             # FastAPI application instance and entry point
├── tests/                  # Pytest testing suite
├── .env.example            # Environment variables template
├── .pre-commit-config.yaml # Pre-commit hook definitions
├── Dockerfile              # Container definition
├── pyproject.toml          # Project configuration & dependencies
└── README.md
```

---

## 🐳 Docker Deployment

To build and run the application using Docker:

```bash
# Build the image
docker build -t chief-of-staff-api .

# Run the container
docker run -p 8080:8080 --env-file .env chief-of-staff-api
```
