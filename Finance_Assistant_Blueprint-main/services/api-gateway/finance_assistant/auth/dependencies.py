"""Meridian API — Authentication Dependencies.

FastAPI dependencies for route protection. Extracts the JWT from
the Authorization header, verifies it, and retrieves the corresponding
User model from the database.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..exceptions import UnauthorizedError
from ..models.user import User
from .jwt import verify_cognito_token

# Bearer token scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency to get the currently authenticated user.

    1. Extracts Bearer token from header.
    2. Verifies Cognito JWT signature and claims.
    3. Looks up the User in the database via cognito_sub.

    Args:
        auth: The Authorization header credentials.
        db: The async database session.

    Returns:
        The authenticated User instance.

    Raises:
        UnauthorizedError: If token is missing, invalid, or user doesn't exist.
    """
    if not auth:
        raise UnauthorizedError("Missing authorization header")

    token = auth.credentials
    payload = verify_cognito_token(token)

    # The 'sub' claim is the unique Cognito user identifier
    cognito_sub = payload.get("sub")
    if not cognito_sub:
        raise UnauthorizedError("Invalid token: missing subject (sub)")

    # Find user in database
    result = await db.execute(select(User).where(User.cognito_sub == cognito_sub))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User not found in database")

    if not user.is_active:
        raise UnauthorizedError("User account is disabled")

    return user
