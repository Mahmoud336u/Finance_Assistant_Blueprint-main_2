"""Meridian API — JWT Validation.

Handles verification of AWS Cognito JWT tokens (ID and Access tokens)
using python-jose. Automatically fetches and caches the JWKS (JSON Web
Key Set) from Cognito.
"""

from __future__ import annotations

import httpx
from cachetools import TTLCache, cached
from jose import jwk, jwt
from jose.utils import base64url_decode

from ..config import get_settings
from ..exceptions import UnauthorizedError
from ..logging import get_logger

logger = get_logger(__name__)


@cached(cache=TTLCache(maxsize=1, ttl=3600))
def get_cognito_jwks() -> dict:
    """Fetch and cache the JWKS from AWS Cognito.

    Caches the result for 1 hour to avoid repeated network calls.
    Raises:
        RuntimeError: If the JWKS cannot be fetched.
    """
    settings = get_settings()
    region = settings.cognito_region
    user_pool_id = settings.cognito_user_pool_id

    if not user_pool_id:
        return {}  # For testing/dev without auth

    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

    try:
        response = httpx.get(jwks_url, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch Cognito JWKS", error=str(exc))
        raise RuntimeError("Authentication service unavailable") from exc


def verify_cognito_token(token: str) -> dict:
    """Verify a Cognito JWT token and return its payload.

    Validates:
    - Signature against Cognito JWKS
    - Expiration (exp)
    - Audience/Client ID (aud or client_id)
    - Issuer (iss)

    Args:
        token: The raw JWT string.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        UnauthorizedError: If the token is invalid, expired, or missing.
    """
    settings = get_settings()

    if not settings.cognito_user_pool_id:
        # Development mode bypass
        return {"sub": "dev-user-123", "username": "developer"}

    try:
        # Get unverified headers to find the Key ID (kid)
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")
        if not kid:
            raise UnauthorizedError("Invalid token format: missing kid")

        # Find the public key in JWKS
        jwks = get_cognito_jwks()
        keys = jwks.get("keys", [])
        public_key = None
        for key in keys:
            if key.get("kid") == kid:
                public_key = jwk.construct(key)
                break

        if not public_key:
            raise UnauthorizedError("Public key not found in JWKS")

        # Get the public key in PEM format
        message, encoded_sig = token.rsplit(".", 1)
        decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))

        if not public_key.verify(message.encode("utf8"), decoded_sig):
            raise UnauthorizedError("Signature verification failed")

        # Verify claims
        region = settings.cognito_region
        pool_id = settings.cognito_user_pool_id
        client_id = settings.cognito_app_client_id
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=client_id,  # For ID tokens (aud == client_id)
            options={
                "verify_aud": False,  # We manually check below to support both ID and Access tokens
                "verify_exp": True,
                "verify_iss": True,
            },
        )

        # Cognito Access tokens use 'client_id' instead of 'aud'
        token_use = payload.get("token_use")
        if token_use == "id":
            if payload.get("aud") != client_id:
                raise UnauthorizedError("Invalid audience (aud)")
        elif token_use == "access":
            if payload.get("client_id") != client_id:
                raise UnauthorizedError("Invalid client_id")
        else:
            raise UnauthorizedError("Invalid token_use claim")

        return payload

    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired") from exc
    except jwt.JWTError as exc:
        raise UnauthorizedError(f"Invalid token: {exc!s}") from exc
    except Exception as exc:
        logger.error("Token verification error", error=str(exc))
        raise UnauthorizedError("Authentication failed") from exc
