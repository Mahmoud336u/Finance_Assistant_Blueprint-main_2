"""Meridian — Transaction Model.

Maps the blueprint's transactions table (Section 6.1).
This is the most heavily-accessed table in the system.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Transaction(TimestampMixin, Base):
    """Financial transaction — maps to the ``transactions`` table.

    This is the core data entity. In production, this table is partitioned
    by transaction_date using pg_partman for monthly partitions.

    Attributes:
        source: plaid | csv | manual — how the transaction was ingested.
        amount: Positive = expense; negative = income.
        category_source: rule | ml | llm | user — who assigned the category.
        category_confidence: 0.0–1.0 confidence score from ML model.
        fingerprint: SHA-256 dedup hash (user_id || external_id || amount || date).
    """

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(255))
    merchant_category_code: Mapped[str | None] = mapped_column(String(10))
    category_id: Mapped[int | None] = mapped_column(Integer, index=True)
    category_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))
    category_source: Mapped[str | None] = mapped_column(String(20))
    is_pending: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    posted_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    recurrence_group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    fingerprint: Mapped[str | None] = mapped_column(String(64), unique=True)
    location: Mapped[dict | None] = mapped_column(JSONB)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    account: Mapped["FinancialAccount"] = relationship(back_populates="transactions")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, amount={self.amount}, "
            f"description={self.description!r:.30})>"
        )
