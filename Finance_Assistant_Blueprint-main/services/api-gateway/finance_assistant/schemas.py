"""Meridian API — Pydantic Schemas for Request/Response Validation.

Defines the API contract for all v1 endpoints.
Uses Pydantic v2 with model_config for JSON schema generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Chat Schemas
# ============================================================


class ChatRole(str, Enum):
    """Message role in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=10000, description="The user's message")
    conversation_id: uuid.UUID | None = Field(
        None,
        description="Existing conversation ID. Omit to start a new conversation.",
    )
    stream: bool = Field(False, description="Whether to stream the response via SSE")


class ChatMessageResponse(BaseModel):
    """Response body for a chat message (non-streaming)."""

    conversation_id: uuid.UUID
    message_id: uuid.UUID
    role: ChatRole = ChatRole.ASSISTANT
    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int | None = None
    rag_chunks_used: int = 0
    created_at: datetime


class ChatStreamEvent(BaseModel):
    """A single SSE event during streaming chat."""

    event: str = Field(
        ...,
        description="Event type: 'delta' (text chunk), 'metadata' (final stats), 'error'",
    )
    data: str = Field(..., description="Event payload (text content or JSON metadata)")


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    id: uuid.UUID
    title: str | None
    message_count: int
    started_at: datetime
    last_message_at: datetime


class ConversationHistory(BaseModel):
    """Full conversation with messages."""

    id: uuid.UUID
    title: str | None
    messages: list[ChatMessageResponse]


# ============================================================
# Document Ingestion Schemas
# ============================================================


class ContentType(str, Enum):
    """Type of document content for the knowledge base."""

    ADVICE = "advice"
    REGULATION = "regulation"
    PRODUCT_DOC = "product_doc"
    FAQ = "faq"


class DocumentIngestRequest(BaseModel):
    """Request body for document ingestion."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(..., min_length=10, max_length=500000, description="Document text content")
    content_type: ContentType = Field(..., description="Type of document")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")
    chunk_size: int = Field(512, ge=100, le=2000, description="Max characters per chunk")
    chunk_overlap: int = Field(64, ge=0, le=500, description="Overlap between chunks")


class DocumentIngestResponse(BaseModel):
    """Response body after document ingestion."""

    document_id: str
    filename: str
    content_type: ContentType
    chunks_created: int
    total_characters: int
    embedding_model: str
    ingested_at: datetime


# ============================================================
# Shared / Pagination Schemas
# ============================================================


class PaginatedResponse(BaseModel):
    """Wrapper for paginated responses."""

    items: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: dict | list | None = None
    meta: dict | None = None
