"""Meridian API — Service-to-Service Authentication.

Provides API key validation for internal services (e.g., ingestion workers,
cron jobs) that need to access the API without a user context.
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from ..exceptions import UnauthorizedError

# API keys are passed in the X-API-Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In production, these should be loaded from Secrets Manager or environment variables
# Hardcoded for development blueprint purposes
_VALID_API_KEYS = {
    "dev-ingestion-key-2026": "ingestion_worker",
    "dev-cron-key-2026": "cron_scheduler",
}


def verify_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    """FastAPI dependency to verify service API keys.

    Args:
        api_key: The API key from the X-API-Key header.

    Returns:
        The service name associated with the valid key.

    Raises:
        UnauthorizedError: If the key is missing or invalid.
    """
    if not api_key:
        raise UnauthorizedError("Missing API Key (X-API-Key header)")

    # Use constant-time comparison to prevent timing attacks
    for valid_key, service_name in _VALID_API_KEYS.items():
        if secrets.compare_digest(api_key, valid_key):
            return service_name

    raise UnauthorizedError("Invalid API Key")
