"""The Fullstack scaffolder — generates a runnable FastAPI skeleton.

This is deterministic on purpose: a FastAPI scaffold is always the same shape, so
we template it in code rather than asking Claude to generate it. The result boots,
serves /health, and ships with one passing test — the solid starting point that
features are then built on top of.
"""

from src.fullstack.models import GeneratedFile, Scaffold

_MAIN_PY = '''"""Application entrypoint — FastAPI app with a health check."""

import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="{project_name}")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    logger.info("Health check called")
    return {{"status": "ok"}}
'''

_TEST_HEALTH = '''"""Test the health endpoint — confirms the app boots and responds."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """GET /health returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
'''

_REQUIREMENTS = """fastapi>=0.110
uvicorn>=0.29
sqlalchemy>=2.0
pydantic>=2.7
python-dotenv>=1.0
httpx>=0.27
pytest>=8.1
pytest-cov>=5.0
"""

_ENV_EXAMPLE = """# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# API auth
API_KEY=change_me
# Logging
LOG_LEVEL=INFO
"""


def build_scaffold(project_name: str) -> Scaffold:
    """Generate the runnable FastAPI skeleton for a project."""
    safe_name = project_name or "project"
    files = [
        GeneratedFile(path="app/__init__.py", content=""),
        GeneratedFile(path="app/main.py", content=_MAIN_PY.format(project_name=safe_name)),
        GeneratedFile(path="tests/__init__.py", content=""),
        GeneratedFile(path="tests/test_health.py", content=_TEST_HEALTH),
        GeneratedFile(path="requirements.txt", content=_REQUIREMENTS),
        GeneratedFile(path=".env.example", content=_ENV_EXAMPLE),
        GeneratedFile(
            path="README.md",
            content=f"# {safe_name}\n\n## Setup\n\n```bash\n"
            f"pip install -r requirements.txt\ncp .env.example .env\n"
            f"uvicorn app.main:app --reload\n```\n\n## Tests\n\n```bash\npytest\n```\n",
        ),
    ]
    return Scaffold(project_name=safe_name, files=files)