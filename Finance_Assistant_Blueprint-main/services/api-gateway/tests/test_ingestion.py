"""Tests for the document chunking engine."""

from __future__ import annotations

from finance_assistant.ai.ingestion import chunk_text


class TestChunkText:
    """Tests for the recursive character text splitter."""

    def test_short_text_returns_single_chunk(self) -> None:
        """Text shorter than chunk_size should return as a single chunk."""
        text = "This is a short text."
        chunks = chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text_returns_empty_list(self) -> None:
        """Empty text should return an empty list."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_splits_on_paragraphs(self) -> None:
        """Text with paragraph breaks should split on double newlines first."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_text(text, chunk_size=30)
        assert len(chunks) >= 2
        assert all(len(c) <= 30 for c in chunks)

    def test_splits_on_sentences(self) -> None:
        """If paragraphs are too long, should split on sentences."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, chunk_size=40)
        assert len(chunks) >= 2

    def test_respects_chunk_size(self) -> None:
        """No chunk should exceed chunk_size."""
        text = "word " * 200  # 1000 characters
        chunks = chunk_text(text, chunk_size=100)
        for chunk in chunks:
            assert len(chunk) <= 100, f"Chunk too long: {len(chunk)} chars"

    def test_preserves_content(self) -> None:
        """All content should be preserved across chunks (no data loss)."""
        text = "Hello world. This is a test. Some more text here."
        chunks = chunk_text(text, chunk_size=25)
        # Key words should appear in at least one chunk
        combined = " ".join(chunks)
        assert "Hello" in combined
        assert "test" in combined
        assert "text" in combined

    def test_custom_chunk_size(self) -> None:
        """Chunk size parameter should be respected."""
        text = "A" * 500
        chunks_small = chunk_text(text, chunk_size=50)
        chunks_large = chunk_text(text, chunk_size=250)
        assert len(chunks_small) > len(chunks_large)

    def test_handles_unicode(self) -> None:
        """Should handle unicode text correctly."""
        text = "финансовый помощник. " * 30
        chunks = chunk_text(text, chunk_size=100)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 100


class TestDocumentChunkDataclass:
    """Tests for the DocumentChunk dataclass."""

    def test_content_hash_consistency(self) -> None:
        """Same content should produce the same hash."""
        from finance_assistant.ai.ingestion import DocumentChunk

        chunk1 = DocumentChunk(content="test content", chunk_index=0)
        chunk2 = DocumentChunk(content="test content", chunk_index=1)
        assert chunk1.content_hash == chunk2.content_hash

    def test_content_hash_uniqueness(self) -> None:
        """Different content should produce different hashes."""
        from finance_assistant.ai.ingestion import DocumentChunk

        chunk1 = DocumentChunk(content="content A", chunk_index=0)
        chunk2 = DocumentChunk(content="content B", chunk_index=0)
        assert chunk1.content_hash != chunk2.content_hash
