"""Meridian AI — Semantic Cache.

Redis-backed cache for RAG query results. If a query is semantically
similar (cosine ≥ 0.95) to a previous query, the cached response is
returned without hitting the LLM, saving latency and cost.

Per blueprint Section 7.5 — Semantic Caching.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from ..cache import cache_get, cache_set
from ..config import get_settings
from ..logging import get_logger
from ..telemetry import LLM_COST_CENTS
from .embeddings import generate_embedding

logger = get_logger(__name__)

# ============================================================
# Configuration
# ============================================================

SIMILARITY_THRESHOLD = 0.95  # Must be very high to avoid returning wrong answers
CACHE_TTL_SECONDS = 3600  # 1 hour default
CACHE_KEY_PREFIX = "semantic_cache:"
MAX_CACHED_EMBEDDINGS = 10000  # Prevent memory bloat


@dataclass
class CacheEntry:
    """A cached semantic query-response pair."""

    query: str
    response: str
    embedding: list[float]
    model: str
    prompt_tokens: int
    completion_tokens: int
    rag_chunks_used: int
    cached_at: float  # Unix timestamp


@dataclass
class CacheResult:
    """Result of a semantic cache lookup."""

    hit: bool
    response: str | None = None
    similarity: float | None = None
    cache_entry: CacheEntry | None = None
    lookup_time_ms: float = 0.0


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Uses pure Python for simplicity. In production at scale,
    you'd use numpy or a compiled extension.
    """
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = sum(x * x for x in a) ** 0.5
    magnitude_b = sum(x * x for x in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


async def semantic_cache_lookup(
    query: str,
    user_id: str,
) -> CacheResult:
    """Check if a semantically similar query exists in cache.

    Pipeline:
    1. Embed the query
    2. Retrieve cached embeddings for this user
    3. Compute cosine similarity against each
    4. If any ≥ threshold, return the cached response

    Args:
        query: The user's question.
        user_id: User ID for cache isolation.

    Returns:
        CacheResult with hit status and optional cached response.
    """
    settings = get_settings()
    if not settings.semantic_cache_enabled:
        return CacheResult(hit=False)

    start = time.perf_counter()

    try:
        # Step 1: Embed the query
        query_embedding = await generate_embedding(query)

        # Step 2: Get the user's cache index
        index_key = f"{CACHE_KEY_PREFIX}index:{user_id}"
        raw_index = await cache_get(index_key)

        if not raw_index:
            return CacheResult(
                hit=False,
                lookup_time_ms=_elapsed(start),
            )

        cache_keys: list[str] = json.loads(raw_index)

        # Step 3: Check each cached entry for similarity
        best_similarity = 0.0
        best_entry: CacheEntry | None = None

        for cache_key in cache_keys:
            raw_entry = await cache_get(cache_key)
            if not raw_entry:
                continue

            entry_data = json.loads(raw_entry)
            entry = CacheEntry(**entry_data)

            similarity = _cosine_similarity(query_embedding, entry.embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        # Step 4: Return hit if above threshold
        if best_similarity >= SIMILARITY_THRESHOLD and best_entry is not None:
            await logger.ainfo(
                "Semantic cache hit",
                similarity=round(best_similarity, 4),
                original_query=best_entry.query[:100],
                user_id=user_id,
            )
            return CacheResult(
                hit=True,
                response=best_entry.response,
                similarity=round(best_similarity, 4),
                cache_entry=best_entry,
                lookup_time_ms=_elapsed(start),
            )

        return CacheResult(
            hit=False,
            similarity=round(best_similarity, 4) if best_similarity > 0 else None,
            lookup_time_ms=_elapsed(start),
        )

    except Exception as exc:
        await logger.awarning("Semantic cache lookup failed", error=str(exc))
        return CacheResult(hit=False, lookup_time_ms=_elapsed(start))


async def semantic_cache_store(
    query: str,
    response: str,
    query_embedding: list[float],
    user_id: str,
    *,
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    rag_chunks_used: int = 0,
    ttl: int | None = None,
) -> bool:
    """Store a query-response pair in the semantic cache.

    Args:
        query: The original query.
        response: The LLM response.
        query_embedding: The query's embedding vector.
        user_id: User ID for cache isolation.
        model: LLM model used.
        prompt_tokens: Tokens in the prompt.
        completion_tokens: Tokens in the completion.
        rag_chunks_used: Number of RAG chunks used.
        ttl: Time-to-live in seconds.

    Returns:
        True if stored successfully.
    """
    settings = get_settings()
    if not settings.semantic_cache_enabled:
        return False

    try:
        entry = CacheEntry(
            query=query,
            response=response,
            embedding=query_embedding,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            rag_chunks_used=rag_chunks_used,
            cached_at=time.time(),
        )

        cache_key = f"{CACHE_KEY_PREFIX}entry:{user_id}:{hash(query)}"
        entry_ttl = ttl or CACHE_TTL_SECONDS

        # Store the entry
        from dataclasses import asdict
        await cache_set(cache_key, json.dumps(asdict(entry)), ttl=entry_ttl)

        # Update the user's cache index
        index_key = f"{CACHE_KEY_PREFIX}index:{user_id}"
        raw_index = await cache_get(index_key)
        cache_keys = json.loads(raw_index) if raw_index else []

        if cache_key not in cache_keys:
            cache_keys.append(cache_key)
            # Limit the index size
            if len(cache_keys) > MAX_CACHED_EMBEDDINGS:
                cache_keys = cache_keys[-MAX_CACHED_EMBEDDINGS:]

        await cache_set(index_key, json.dumps(cache_keys), ttl=entry_ttl)

        await logger.adebug(
            "Semantic cache stored",
            cache_key=cache_key,
            user_id=user_id,
        )
        return True

    except Exception as exc:
        await logger.awarning("Semantic cache store failed", error=str(exc))
        return False


def _elapsed(start: float) -> float:
    """Calculate elapsed time in ms."""
    return round((time.perf_counter() - start) * 1000, 2)
