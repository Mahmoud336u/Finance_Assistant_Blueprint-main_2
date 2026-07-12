"""Meridian AI — Document Chunking and Ingestion.

Handles the document ingestion pipeline:
  Upload → Chunk → Embed → Store in pgvector

Supports recursive character-based chunking with configurable
chunk size and overlap per the RAG best practices.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..logging import get_logger
from .embeddings import generate_embedding, get_embedding_model_version

logger = get_logger(__name__)

# ============================================================
# Chunking Configuration
# ============================================================

DEFAULT_CHUNK_SIZE = 512  # tokens (approximately characters / 4)
DEFAULT_CHUNK_OVERLAP = 64
SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]


@dataclass
class DocumentChunk:
    """A single chunk of a document with its metadata."""

    content: str
    chunk_index: int
    metadata: dict[str, str | int] = field(default_factory=dict)
    embedding: list[float] | None = None

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of the chunk content for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()


@dataclass
class IngestedDocument:
    """Result of a document ingestion operation."""

    document_id: str
    filename: str
    content_type: str
    chunks_created: int
    total_characters: int
    embedding_model: str
    ingested_at: str


# ============================================================
# Chunking Engine
# ============================================================


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: list[str] | None = None,
) -> list[str]:
    """Split text into overlapping chunks using recursive character splitting.

    Uses a hierarchy of separators (paragraph → sentence → word) to find
    natural break points, preserving semantic coherence within chunks.

    Args:
        text: The full text to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of characters to overlap between chunks.
        separators: Custom separator hierarchy. Defaults to paragraph → sentence → word.

    Returns:
        List of text chunks.
    """
    if separators is None:
        separators = SEPARATORS

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    _recursive_split(text, chunks, chunk_size, chunk_overlap, separators, 0)
    return [c for c in chunks if c.strip()]


def _recursive_split(
    text: str,
    chunks: list[str],
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
    sep_index: int,
) -> None:
    """Recursively split text using the separator hierarchy."""
    if not text.strip():
        return

    if len(text) <= chunk_size:
        chunks.append(text.strip())
        return

    if sep_index >= len(separators):
        # No more separators — force split at chunk_size
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i : i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return

    separator = separators[sep_index]
    parts = text.split(separator)

    current_chunk = ""
    for part in parts:
        candidate = f"{current_chunk}{separator}{part}" if current_chunk else part

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(part) > chunk_size:
                # Part is too large — recurse with next separator
                _recursive_split(part, chunks, chunk_size, chunk_overlap, separators, sep_index + 1)
                current_chunk = ""
            else:
                current_chunk = part

    if current_chunk.strip():
        chunks.append(current_chunk.strip())


# ============================================================
# Ingestion Pipeline
# ============================================================


async def ingest_document(
    content: str,
    content_type: str,
    filename: str,
    metadata: dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[list[DocumentChunk], IngestedDocument]:
    """Ingest a document into the RAG knowledge base.

    Pipeline: text → chunk → embed → return chunks for storage.

    Args:
        content: The full text content of the document.
        content_type: Type of content (advice, regulation, product_doc, faq).
        filename: Original filename for tracking.
        metadata: Additional metadata to store with each chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        Tuple of (list of DocumentChunks with embeddings, IngestedDocument summary).
    """
    document_id = str(uuid.uuid4())
    base_metadata = {
        "document_id": document_id,
        "filename": filename,
        "content_type": content_type,
        **(metadata or {}),
    }

    await logger.ainfo(
        "Ingesting document",
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        content_length=len(content),
    )

    # Step 1: Chunk
    text_chunks = chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    await logger.ainfo(
        "Document chunked",
        document_id=document_id,
        num_chunks=len(text_chunks),
    )

    # Step 2: Embed each chunk
    doc_chunks: list[DocumentChunk] = []
    for i, chunk_text_content in enumerate(text_chunks):
        embedding = await generate_embedding(chunk_text_content)
        doc_chunk = DocumentChunk(
            content=chunk_text_content,
            chunk_index=i,
            metadata={**base_metadata, "chunk_index": i, "total_chunks": len(text_chunks)},
            embedding=embedding,
        )
        doc_chunks.append(doc_chunk)

    # Step 3: Return for storage
    summary = IngestedDocument(
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        chunks_created=len(doc_chunks),
        total_characters=len(content),
        embedding_model=get_embedding_model_version(),
        ingested_at=datetime.now(timezone.utc).isoformat(),
    )

    await logger.ainfo(
        "Document ingestion complete",
        document_id=document_id,
        chunks_created=len(doc_chunks),
    )

    return doc_chunks, summary
