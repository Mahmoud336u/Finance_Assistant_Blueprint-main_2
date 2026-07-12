"""Tests for prompt assembly module."""

from __future__ import annotations

import pytest

from finance_assistant.ai.prompts import (
    AssembledPrompt,
    _format_rag_context,
    load_template,
)
from finance_assistant.ai.retriever import RetrievedChunk


class TestLoadTemplate:
    """Tests for prompt template loading."""

    def test_load_system_prompt(self) -> None:
        """Should load the system financial advisor prompt."""
        template = load_template("system_financial_advisor")
        assert "Meridian" in template
        assert "{{USER_NAME}}" in template
        assert "Guardrails" in template

    def test_load_anomaly_prompt(self) -> None:
        """Should load the anomaly detection prompt."""
        template = load_template("anomaly_detection")
        assert "anomaly" in template.lower()
        assert "{{AMOUNT}}" in template

    def test_load_categorization_prompt(self) -> None:
        """Should load the categorization prompt."""
        template = load_template("categorize_transaction")
        assert "category" in template.lower()

    def test_load_nonexistent_raises(self) -> None:
        """Loading a nonexistent template should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent_template")


class TestFormatRagContext:
    """Tests for RAG context formatting."""

    def test_empty_chunks(self) -> None:
        """No chunks should return empty string."""
        assert _format_rag_context([]) == ""

    def test_formats_chunks_with_sources(self) -> None:
        """Should format chunks with source labels and relevance scores."""
        chunks = [
            RetrievedChunk(
                id="1",
                content="Tax-free savings accounts allow...",
                content_type="advice",
                metadata=None,
                similarity_score=0.92,
                embedding_model_version="v1",
            ),
            RetrievedChunk(
                id="2",
                content="Budgeting with the 50/30/20 rule...",
                content_type="faq",
                metadata=None,
                similarity_score=0.85,
                embedding_model_version="v1",
            ),
        ]
        result = _format_rag_context(chunks)
        assert "[Source 1 (advice, relevance: 0.92)]" in result
        assert "[Source 2 (faq, relevance: 0.85)]" in result
        assert "Tax-free" in result
        assert "50/30/20" in result


class TestAssembledPrompt:
    """Tests for the AssembledPrompt dataclass."""

    def test_total_context_chunks(self) -> None:
        """Should sum RAG and user context chunk counts."""
        prompt = AssembledPrompt(
            system_prompt="test",
            messages=[],
            rag_chunks_used=5,
            user_context_used=3,
        )
        assert prompt.total_context_chunks == 8


class TestAssembleChatPrompt:
    """Tests for the full prompt assembly pipeline."""

    @pytest.mark.asyncio
    async def test_basic_assembly(self) -> None:
        """Should assemble a basic prompt without context."""
        from finance_assistant.ai.prompts import assemble_chat_prompt

        result = await assemble_chat_prompt(query="What is my spending?")
        assert result.system_prompt  # Non-empty
        assert len(result.messages) >= 1
        assert result.messages[-1]["role"] == "user"
        assert "spending" in result.messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_assembly_with_user_name(self) -> None:
        """Should personalize the system prompt with user name."""
        from finance_assistant.ai.prompts import assemble_chat_prompt

        result = await assemble_chat_prompt(
            query="Hello",
            user_name="Mahmoud",
        )
        assert "Mahmoud" in result.system_prompt

    @pytest.mark.asyncio
    async def test_assembly_with_rag_context(self) -> None:
        """Should include RAG context in the prompt."""
        from finance_assistant.ai.prompts import assemble_chat_prompt

        chunks = [
            RetrievedChunk(
                id="1",
                content="Your food spending was $1,200 last month.",
                content_type="advice",
                metadata=None,
                similarity_score=0.9,
                embedding_model_version="v1",
            ),
        ]
        result = await assemble_chat_prompt(
            query="How much did I spend on food?",
            rag_chunks=chunks,
        )
        assert result.rag_chunks_used == 1
        assert "$1,200" in result.messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_assembly_with_history(self) -> None:
        """Should include conversation history in messages."""
        from finance_assistant.ai.prompts import assemble_chat_prompt

        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"},
        ]
        result = await assemble_chat_prompt(
            query="What is my budget?",
            conversation_history=history,
        )
        # History + current query
        assert len(result.messages) == 3
        assert result.messages[0]["content"] == "Hi"
