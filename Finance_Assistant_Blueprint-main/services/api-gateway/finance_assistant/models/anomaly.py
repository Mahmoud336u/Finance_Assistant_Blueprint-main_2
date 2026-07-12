"""Meridian — Anomaly Event Model.

Maps the blueprint's anomaly_events table (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class AnomalyEvent(UUIDMixin, Base):
    """Detected spending anomaly — maps to the ``anomaly_events`` table.

    Created by the Isolation Forest anomaly detection pipeline when
    a transaction's score exceeds the configured threshold (0.75).

    Attributes:
        anomaly_type: high_spend | new_merchant | duplicate | velocity.
        severity: low | medium | high | critical.
        score: Anomaly score from the ML model (0.0–1.0).
    """

    __tablename__ = "anomaly_events"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_false_positive: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<AnomalyEvent(id={self.id}, type={self.anomaly_type!r}, "
            f"severity={self.severity!r}, score={self.score})>"
        )
