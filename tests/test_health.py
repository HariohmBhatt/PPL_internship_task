"""Health endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-quiz-microservice"


@pytest.mark.asyncio
async def test_readiness_check_with_db():
    """Test readiness check with database connectivity."""
    response = client.get("/readyz")
    # Should be 200 if database is connected
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Quiz Microservice"
    assert data["version"] == "0.1.0"
