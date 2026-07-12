"""Meridian — AI Conversation and Message Models.

Maps the blueprint's ai_conversations and ai_messages tables (Section 6.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class AIConversation(UUIDMixin, Base):
    """AI chat conversation — maps to the ``ai_conversations`` table.

    Represents a multi-turn conversation between a user and the AI assistant.
    Tracks token usage and cost for billing and optimization.
    """

    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_cost_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")  # noqa: F821
    messages: Mapped[list[AIMessage]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, title={self.title!r}, messages={self.message_count})>"


class AIMessage(UUIDMixin, Base):
    """Individual AI chat message — maps to the ``ai_messages`` table.

    Stores both user and assistant messages with full observability
    metadata: model used, token counts, latency, cost, and quality scores.

    Attributes:
        role: user | assistant | system | tool.
        provider: bedrock | openai | vllm — which LLM backend served this.
        hallucination_score: 0.0–1.0 from the evaluation pipeline.
    """

    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_sanitized: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(50))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_cents: Mapped[float | None] = mapped_column(Numeric(8, 4))
    rag_retrieved_chunks: Mapped[int | None] = mapped_column(Integer)
    hallucination_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    review_outcome: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    # Relationships
    conversation: Mapped[AIConversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<AIMessage(id={self.id}, role={self.role!r}, model={self.model_used!r})>"
