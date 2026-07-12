"""Meridian — Financial Account Model.

Maps the blueprint's financial_accounts table (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class FinancialAccount(UUIDMixin, TimestampMixin, Base):
    """Financial account linked via Plaid — maps to ``financial_accounts`` table.

    Attributes:
        plaid_account_id: Plaid account reference.
        plaid_item_id: Plaid institution connection reference.
        account_type: checking | savings | credit | investment | loan | other.
        sync_status: active | paused | error | disconnected.
    """

    __tablename__ = "financial_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    plaid_account_id: Mapped[str | None] = mapped_column(String(255))
    plaid_item_id: Mapped[str | None] = mapped_column(String(255))
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    account_subtype: Mapped[str | None] = mapped_column(String(50))
    mask: Mapped[str | None] = mapped_column(String(10))
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")
    current_balance: Mapped[float | None] = mapped_column(Numeric(15, 2))
    available_balance: Mapped[float | None] = mapped_column(Numeric(15, 2))
    balance_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sync_status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    sync_error_code: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="accounts")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FinancialAccount(id={self.id}, name={self.account_name!r}, type={self.account_type!r})>"
