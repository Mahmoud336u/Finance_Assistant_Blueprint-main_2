"""Meridian — User and Session Models.

Maps the blueprint's users and user_sessions tables (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """User account — maps to the ``users`` table.

    Attributes:
        email: Unique email address (login identifier).
        cognito_sub: AWS Cognito identity reference.
        subscription_tier: free | premium | family | business | enterprise.
        deleted_at: Soft delete timestamp for GDPR Right to Erasure.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    cognito_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        server_default="free",
        nullable=False,
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gdpr_consent_version: Mapped[str | None] = mapped_column(String(10))
    data_region: Mapped[str] = mapped_column(String(20), default="us-east-1", server_default="us-east-1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    sessions: Mapped[list[UserSession]] = relationship(back_populates="user", cascade="all, delete-orphan")
    accounts: Mapped[list["FinancialAccount"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["AIConversation"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"


class UserSession(UUIDMixin, Base):
    """User session — maps to the ``user_sessions`` table.

    Stores refresh token hashes and device fingerprints for session management.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
