"""Meridian — Category and User Category Rule Models.

Maps the blueprint's categories and user_category_rules tables (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Category(Base):
    """Transaction category — maps to the ``categories`` table.

    Supports hierarchical categories via parent_id self-reference.
    System categories are pre-seeded; users can create custom ones.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, index=True)
    icon_url: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(7))
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_income: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Self-referential relationship for subcategories
    children: Mapped[list[Category]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped[Category | None] = relationship(
        back_populates="children",
        remote_side=[id],
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, slug={self.slug!r})>"


class UserCategoryRule(Base):
    """User-defined categorization rule — maps to ``user_category_rules`` table.

    Allows users to create custom merchant-to-category mappings
    that override the ML model's predictions.
    """

    __tablename__ = "user_category_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    match_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<UserCategoryRule(id={self.id}, pattern={self.pattern!r})>"
