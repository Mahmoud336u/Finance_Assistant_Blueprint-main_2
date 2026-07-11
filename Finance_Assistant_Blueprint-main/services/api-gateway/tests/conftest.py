"""Tests for the Meridian API — Configuration and Fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from finance_assistant.config import Settings
from finance_assistant.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Provide test-specific settings."""
    return Settings(
        environment="dev",
        log_level="WARNING",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/1",
        ai_chat_enabled=False,
    )


@pytest.fixture
def app(test_settings: Settings) -> create_app:  # type: ignore[valid-type]
    """Create a test FastAPI application."""
    return create_app(settings=test_settings)


@pytest.fixture
def client(app) -> TestClient:  # type: ignore[type-arg]
    """Provide a test HTTP client."""
    return TestClient(app)
