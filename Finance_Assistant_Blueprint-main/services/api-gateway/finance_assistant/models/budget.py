"""Meridian — Budget and BudgetPeriod Models.

Maps the blueprint's budgets and budget_periods tables (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Budget(UUIDMixin, TimestampMixin, Base):
    """Budget rule — maps to the ``budgets`` table.

    Attributes:
        period: weekly | biweekly | monthly | quarterly | annual | custom.
        alert_at_percent: Threshold percentage to trigger budget alerts.
        rollover: Whether unused amount carries forward to next period.
    """

    __tablename__ = "budgets"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    rollover: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    alert_at_percent: Mapped[int] = mapped_column(Integer, default=80, server_default="80")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    periods: Mapped[list[BudgetPeriod]] = relationship(back_populates="budget", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, name={self.name!r}, amount={self.amount})>"


class BudgetPeriod(UUIDMixin, Base):
    """Budget tracking period — maps to the ``budget_periods`` table.

    Tracks actual spending against the budgeted amount for a specific
    time window. Updated in real-time as transactions are ingested.
    """

    __tablename__ = "budget_periods"
    __table_args__ = (UniqueConstraint("budget_id", "period_start", name="uq_budget_period"),)

    budget_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    allocated_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    spent_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, server_default="0")
    alert_50_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alert_80_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alert_100_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    budget: Mapped[Budget] = relationship(back_populates="periods")

    def __repr__(self) -> str:
        return (
            f"<BudgetPeriod(id={self.id}, budget_id={self.budget_id}, "
            f"spent={self.spent_amount}/{self.allocated_amount})>"
        )
