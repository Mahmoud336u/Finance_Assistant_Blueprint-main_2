"""Tests for authentication and authorization modules."""

from __future__ import annotations

import secrets
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from finance_assistant.auth.api_keys import verify_api_key
from finance_assistant.auth.dependencies import get_current_user
from finance_assistant.auth.jwt import verify_cognito_token
from finance_assistant.exceptions import UnauthorizedError


class TestAPIKeyValidation:
    """Tests for the service-to-service API key dependency."""

    def test_missing_api_key(self) -> None:
        """Missing API key should raise UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc:
            verify_api_key(None)
        assert "Missing API Key" in str(exc.value)

    def test_invalid_api_key(self) -> None:
        """Invalid API key should raise UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc:
            verify_api_key("invalid-key")
        assert "Invalid API Key" in str(exc.value)

    def test_valid_api_key(self) -> None:
        """Valid API key should return the service name."""
        # Using the hardcoded dev key
        service = verify_api_key("dev-ingestion-key-2026")
        assert service == "ingestion_worker"


class TestJWTValidation:
    """Tests for Cognito JWT verification."""

    @patch("finance_assistant.auth.jwt.get_settings")
    def test_dev_bypass(self, mock_settings) -> None:
        """Should return dev user if user_pool_id is empty."""
        class MockSettings:
            cognito_user_pool_id = ""
            
        mock_settings.return_value = MockSettings()
        
        payload = verify_cognito_token("any.token.here")
        assert payload["sub"] == "dev-user-123"
        assert payload["username"] == "developer"

    @patch("finance_assistant.auth.jwt.get_settings")
    @patch("finance_assistant.auth.jwt.jwt.get_unverified_headers")
    def test_missing_kid(self, mock_headers, mock_settings) -> None:
        """Token without 'kid' header should raise error."""
        class MockSettings:
            cognito_user_pool_id = "us-east-1_xxxxx"
            
        mock_settings.return_value = MockSettings()
        mock_headers.return_value = {}  # No kid
        
        with pytest.raises(UnauthorizedError) as exc:
            verify_cognito_token("fake.token.here")
            
        assert "missing kid" in str(exc.value).lower()
