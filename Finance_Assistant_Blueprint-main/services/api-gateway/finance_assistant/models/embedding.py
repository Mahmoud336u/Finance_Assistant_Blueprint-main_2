"""Meridian — Vector Embedding Models (pgvector).

Maps the blueprint's knowledge_embeddings and user_financial_embeddings
tables (Section 6.3). Uses the pgvector extension for similarity search.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin

# Embedding dimension — Titan Text Embeddings v2 produces 1024-dim vectors.
# Cohere embed-english-v3 produces 1024-dim vectors.
# Adjust if using a different embedding model.
EMBEDDING_DIMENSION = 1024


class KnowledgeEmbedding(UUIDMixin, Base):
    """Financial knowledge base entry for RAG retrieval.

    Maps to the ``knowledge_embeddings`` table.
    Stores chunked documents with their vector embeddings for
    similarity search during the RAG pipeline.

    Attributes:
        content_type: advice | regulation | product_doc | faq.
        embedding: Vector column (pgvector) for similarity search.
        metadata: Flexible JSONB for source, date, category, tags.
    """

    __tablename__ = "knowledge_embeddings"

    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION))
    embedding_model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEmbedding(id={self.id}, type={self.content_type!r})>"


class UserFinancialEmbedding(UUIDMixin, Base):
    """User-specific financial summary embedding for personalized RAG.

    Maps to the ``user_financial_embeddings`` table.
    Contains embeddings of user transaction summaries, category patterns,
    and anomaly descriptions for personalized retrieval.

    Attributes:
        summary_type: monthly_summary | category_pattern | anomaly.
        period_start/end: Time range this summary covers.
        expires_at: Auto-cleanup for stale summaries.
    """

    __tablename__ = "user_financial_embeddings"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION))
    embedding_model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<UserFinancialEmbedding(id={self.id}, user_id={self.user_id}, "
            f"type={self.summary_type!r})>"
        )
