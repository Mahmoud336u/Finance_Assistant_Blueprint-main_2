"""Tests for Pydantic API schemas."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from finance_assistant.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatRole,
    ContentType,
    DocumentIngestRequest,
)


class TestChatMessageRequest:
    """Tests for chat message request validation."""

    def test_valid_request(self) -> None:
        """A valid chat request should pass validation."""
        req = ChatMessageRequest(message="What is my spending?")
        assert req.message == "What is my spending?"
        assert req.conversation_id is None
        assert req.stream is False

    def test_strips_whitespace(self) -> None:
        """Message should be stripped of whitespace."""
        req = ChatMessageRequest(message="  Hello  ")
        assert req.message == "Hello"

    def test_empty_message_rejected(self) -> None:
        """Empty message should be rejected."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="")

    def test_too_long_message_rejected(self) -> None:
        """Message exceeding max length should be rejected."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="x" * 10001)

    def test_with_conversation_id(self) -> None:
        """Should accept a valid conversation UUID."""
        cid = uuid.uuid4()
        req = ChatMessageRequest(message="Follow up", conversation_id=cid)
        assert req.conversation_id == cid

    def test_streaming_flag(self) -> None:
        """Should accept stream=true."""
        req = ChatMessageRequest(message="Hello", stream=True)
        assert req.stream is True


class TestDocumentIngestRequest:
    """Tests for document ingestion request validation."""

    def test_valid_request(self) -> None:
        """A valid ingest request should pass validation."""
        req = DocumentIngestRequest(
            content="This is a financial document with enough content to pass validation.",
            content_type=ContentType.ADVICE,
            filename="guide.txt",
        )
        assert req.content_type == ContentType.ADVICE
        assert req.chunk_size == 512  # default
        assert req.chunk_overlap == 64  # default

    def test_short_content_rejected(self) -> None:
        """Content shorter than 10 chars should be rejected."""
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="short",
                content_type=ContentType.FAQ,
                filename="test.txt",
            )

    def test_custom_chunk_settings(self) -> None:
        """Should accept custom chunk size and overlap."""
        req = DocumentIngestRequest(
            content="A" * 100,
            content_type=ContentType.REGULATION,
            filename="reg.txt",
            chunk_size=256,
            chunk_overlap=32,
        )
        assert req.chunk_size == 256
        assert req.chunk_overlap == 32

    def test_invalid_content_type_rejected(self) -> None:
        """Invalid content type should be rejected."""
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="A" * 100,
                content_type="invalid_type",  # type: ignore
                filename="test.txt",
            )


class TestChatMessageResponse:
    """Tests for chat message response schema."""

    def test_serialization(self) -> None:
        """Response should serialize correctly."""
        from datetime import datetime, timezone

        resp = ChatMessageResponse(
            conversation_id=uuid.uuid4(),
            message_id=uuid.uuid4(),
            role=ChatRole.ASSISTANT,
            content="Your spending increased.",
            model="claude-3-5-sonnet",
            provider="bedrock",
            prompt_tokens=1000,
            completion_tokens=200,
            latency_ms=1500,
            rag_chunks_used=3,
            created_at=datetime.now(timezone.utc),
        )
        data = resp.model_dump()
        assert data["role"] == "assistant"
        assert data["prompt_tokens"] == 1000
        assert data["rag_chunks_used"] == 3
