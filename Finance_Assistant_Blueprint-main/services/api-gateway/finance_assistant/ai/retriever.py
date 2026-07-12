"""Meridian AI — Vector Retriever.

Implements pgvector similarity search for the RAG pipeline.
Retrieves relevant document chunks based on query embeddings.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..logging import get_logger
from .embeddings import generate_embedding

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with its relevance score."""

    id: str
    content: str
    content_type: str
    metadata: dict | None
    similarity_score: float
    embedding_model_version: str | None


async def retrieve_similar_chunks(
    query: str,
    db: AsyncSession,
    *,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    content_type: str | None = None,
    table: str = "knowledge_embeddings",
) -> list[RetrievedChunk]:
    """Retrieve the most similar document chunks for a query.

    Pipeline: query → embed → pgvector cosine similarity → rank → filter.

    Args:
        query: The user's natural language query.
        db: Async database session.
        top_k: Maximum number of chunks to return.
        similarity_threshold: Minimum cosine similarity (0.0–1.0).
        content_type: Optional filter by content type.
        table: Which embedding table to search.

    Returns:
        List of RetrievedChunks ranked by descending similarity.
    """
    # Step 1: Embed the query
    query_embedding = await generate_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    await logger.adebug("Retriever: query embedded", query_length=len(query))

    # Step 2: Build the SQL query with pgvector cosine distance
    # cosine distance = 1 - cosine similarity, so we use <=> operator
    # and convert: similarity = 1 - distance
    filters = ""
    params: dict = {
        "embedding": embedding_str,
        "top_k": top_k,
        "threshold": 1.0 - similarity_threshold,  # Convert similarity to distance threshold
    }

    if content_type:
        filters = "AND content_type = :content_type"
        params["content_type"] = content_type

    sql = text(f"""
        SELECT
            id::text,
            content,
            content_type,
            metadata,
            embedding_model_version,
            (embedding <=> :embedding::vector) AS distance
        FROM {table}
        WHERE embedding IS NOT NULL
            AND (embedding <=> :embedding::vector) < :threshold
            {filters}
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    chunks: list[RetrievedChunk] = []
    for row in rows:
        chunks.append(
            RetrievedChunk(
                id=row[0],
                content=row[1],
                content_type=row[2],
                metadata=row[3],
                similarity_score=round(1.0 - row[5], 4),  # Convert distance → similarity
                embedding_model_version=row[4],
            )
        )

    await logger.ainfo(
        "Retriever: search complete",
        query_length=len(query),
        chunks_found=len(chunks),
        top_similarity=chunks[0].similarity_score if chunks else 0,
    )

    return chunks


async def retrieve_user_context(
    query: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    *,
    top_k: int = 3,
    similarity_threshold: float = 0.65,
) -> list[RetrievedChunk]:
    """Retrieve user-specific financial context for personalized RAG.

    Searches the user_financial_embeddings table for summaries
    relevant to the user's query (monthly summaries, category patterns, etc.).

    Args:
        query: The user's query.
        user_id: The user's UUID.
        db: Async database session.
        top_k: Maximum chunks to return.
        similarity_threshold: Minimum similarity.

    Returns:
        List of user-specific context chunks.
    """
    query_embedding = await generate_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = text("""
        SELECT
            id::text,
            content,
            summary_type AS content_type,
            NULL AS metadata,
            embedding_model_version,
            (embedding <=> :embedding::vector) AS distance
        FROM user_financial_embeddings
        WHERE user_id = :user_id
            AND embedding IS NOT NULL
            AND (embedding <=> :embedding::vector) < :threshold
            AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "embedding": embedding_str,
        "user_id": str(user_id),
        "top_k": top_k,
        "threshold": 1.0 - similarity_threshold,
    })
    rows = result.fetchall()

    return [
        RetrievedChunk(
            id=row[0],
            content=row[1],
            content_type=row[2],
            metadata=row[3],
            similarity_score=round(1.0 - row[5], 4),
            embedding_model_version=row[4],
        )
        for row in rows
    ]
