"""Meridian AI — Hybrid Search.

Combines pgvector cosine similarity search with BM25 keyword search
using Reciprocal Rank Fusion (RRF) for improved retrieval quality.

Per blueprint Section 7.3 — Hybrid Search Strategy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..logging import get_logger
from .embeddings import generate_embedding
from .retriever import RetrievedChunk

logger = get_logger(__name__)

# RRF constant (standard value from the original RRF paper)
RRF_K = 60


@dataclass
class HybridSearchResult:
    """Result of a hybrid search with fused ranking."""

    chunks: list[RetrievedChunk]
    vector_count: int
    keyword_count: int
    fused_count: int


async def hybrid_search(
    query: str,
    db: AsyncSession,
    *,
    top_k: int = 5,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
    similarity_threshold: float = 0.6,
    content_type: str | None = None,
) -> HybridSearchResult:
    """Perform hybrid search combining vector similarity and keyword matching.

    Pipeline:
    1. Run pgvector cosine similarity search
    2. Run PostgreSQL full-text search (BM25-like via ts_rank)
    3. Fuse results using Reciprocal Rank Fusion (RRF)
    4. Return top-K fused results

    Args:
        query: The user's search query.
        db: Async database session.
        top_k: Maximum number of results.
        vector_weight: Weight for vector search in RRF (0.0–1.0).
        keyword_weight: Weight for keyword search in RRF (0.0–1.0).
        similarity_threshold: Minimum cosine similarity for vector results.
        content_type: Optional content type filter.

    Returns:
        HybridSearchResult with fused, ranked chunks.
    """
    # Step 1: Vector search
    vector_results = await _vector_search(
        query, db, top_k=top_k * 2, threshold=similarity_threshold, content_type=content_type
    )

    # Step 2: Keyword search
    keyword_results = await _keyword_search(
        query, db, top_k=top_k * 2, content_type=content_type
    )

    # Step 3: Reciprocal Rank Fusion
    fused = _reciprocal_rank_fusion(
        vector_results,
        keyword_results,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
    )

    # Step 4: Take top-K
    top_results = fused[:top_k]

    await logger.ainfo(
        "Hybrid search complete",
        vector_hits=len(vector_results),
        keyword_hits=len(keyword_results),
        fused_results=len(top_results),
    )

    return HybridSearchResult(
        chunks=top_results,
        vector_count=len(vector_results),
        keyword_count=len(keyword_results),
        fused_count=len(top_results),
    )


async def _vector_search(
    query: str,
    db: AsyncSession,
    *,
    top_k: int,
    threshold: float,
    content_type: str | None,
) -> list[tuple[str, RetrievedChunk, int]]:
    """Run pgvector cosine similarity search.

    Returns: List of (id, chunk, rank) tuples.
    """
    query_embedding = await generate_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    filters = ""
    params: dict = {
        "embedding": embedding_str,
        "top_k": top_k,
        "threshold": 1.0 - threshold,
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
        FROM knowledge_embeddings
        WHERE embedding IS NOT NULL
            AND (embedding <=> :embedding::vector) < :threshold
            {filters}
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    ranked: list[tuple[str, RetrievedChunk, int]] = []
    for rank, row in enumerate(rows):
        chunk = RetrievedChunk(
            id=row[0],
            content=row[1],
            content_type=row[2],
            metadata=row[3],
            similarity_score=round(1.0 - row[5], 4),
            embedding_model_version=row[4],
        )
        ranked.append((row[0], chunk, rank))

    return ranked


async def _keyword_search(
    query: str,
    db: AsyncSession,
    *,
    top_k: int,
    content_type: str | None,
) -> list[tuple[str, RetrievedChunk, int]]:
    """Run PostgreSQL full-text search using ts_rank.

    Uses plainto_tsquery for natural language query parsing.
    """
    # Clean query for full-text search
    clean_query = re.sub(r"[^\w\s]", " ", query)

    filters = ""
    params: dict = {
        "query": clean_query,
        "top_k": top_k,
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
            ts_rank(
                to_tsvector('english', content),
                plainto_tsquery('english', :query)
            ) AS rank_score
        FROM knowledge_embeddings
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            {filters}
        ORDER BY rank_score DESC
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    ranked: list[tuple[str, RetrievedChunk, int]] = []
    for rank, row in enumerate(rows):
        chunk = RetrievedChunk(
            id=row[0],
            content=row[1],
            content_type=row[2],
            metadata=row[3],
            similarity_score=float(row[5]),  # ts_rank score
            embedding_model_version=row[4],
        )
        ranked.append((row[0], chunk, rank))

    return ranked


def _reciprocal_rank_fusion(
    vector_results: list[tuple[str, RetrievedChunk, int]],
    keyword_results: list[tuple[str, RetrievedChunk, int]],
    *,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[RetrievedChunk]:
    """Fuse two ranked lists using Reciprocal Rank Fusion (RRF).

    RRF score = Σ weight / (k + rank)

    This method is robust and doesn't require score normalization,
    making it ideal for combining different scoring functions.
    """
    scores: dict[str, float] = {}
    chunks: dict[str, RetrievedChunk] = {}

    for doc_id, chunk, rank in vector_results:
        rrf_score = vector_weight / (RRF_K + rank)
        scores[doc_id] = scores.get(doc_id, 0) + rrf_score
        chunks[doc_id] = chunk

    for doc_id, chunk, rank in keyword_results:
        rrf_score = keyword_weight / (RRF_K + rank)
        scores[doc_id] = scores.get(doc_id, 0) + rrf_score
        if doc_id not in chunks:
            chunks[doc_id] = chunk

    # Sort by fused RRF score descending
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    return [chunks[doc_id] for doc_id in sorted_ids if doc_id in chunks]
