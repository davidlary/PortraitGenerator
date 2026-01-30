"""Unit tests for API server."""

import pytest
from fastapi.testclient import TestClient


def test_create_app():
    """Test app creation."""
    from portrait_generator.api.server import create_app

    app = create_app()

    assert app is not None
    assert app.title == "Portrait Generator API"
    assert app.version == "1.0.0"


def test_health_check():
    """Test health check endpoint."""
    from portrait_generator.api.server import create_app

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "gemini_configured" in data
    assert "output_dir_writable" in data
    assert "timestamp" in data


def test_status_endpoint_not_found():
    """Test status endpoint for non-existent subject."""
    from portrait_generator.api.server import create_app

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/status/NonExistentPerson")

    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "NonExistentPerson"
    assert "exists" in data
    # No portraits should exist
    assert data["exists"] is False
    assert len(data["files"]) == 0
