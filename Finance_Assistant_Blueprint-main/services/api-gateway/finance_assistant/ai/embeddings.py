"""Meridian AI — Embedding Client.

Interfaces with AWS Bedrock Titan Text Embeddings v2 for generating
vector embeddings used in the RAG pipeline's retrieval stage.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import boto3

from ..config import get_settings
from ..logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

logger = get_logger(__name__)

# Module-level client (initialized lazily)
_bedrock_client: BedrockRuntimeClient | None = None


def _get_bedrock_client() -> BedrockRuntimeClient:
    """Get or create the Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        settings = get_settings()
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.bedrock_region,
        )
    return _bedrock_client


async def generate_embedding(text: str, model_id: str | None = None) -> list[float]:
    """Generate a vector embedding for the given text.

    Uses AWS Bedrock Titan Text Embeddings v2 (1024 dimensions).

    Args:
        text: The text to embed.
        model_id: Override the default embedding model ID.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        ExternalServiceError: If the Bedrock API call fails.
    """
    from ..exceptions import ExternalServiceError

    settings = get_settings()
    model = model_id or settings.bedrock_embedding_model_id

    try:
        client = _get_bedrock_client()
        response = client.invoke_model(
            modelId=model,
            body=json.dumps({
                "inputText": text,
            }),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        embedding: list[float] = result["embedding"]

        await logger.adebug(
            "Embedding generated",
            model=model,
            input_length=len(text),
            dimensions=len(embedding),
        )

        return embedding

    except Exception as exc:
        await logger.aerror("Embedding generation failed", model=model, error=str(exc))
        raise ExternalServiceError("bedrock-embeddings", str(exc)) from exc


async def generate_embeddings_batch(texts: list[str], model_id: str | None = None) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    Processes texts sequentially (Bedrock doesn't support batch embedding natively).
    For high-throughput scenarios, consider parallelizing with asyncio.gather().

    Args:
        texts: List of texts to embed.
        model_id: Override the default embedding model ID.

    Returns:
        List of embedding vectors, one per input text.
    """
    embeddings: list[list[float]] = []
    for text in texts:
        embedding = await generate_embedding(text, model_id=model_id)
        embeddings.append(embedding)
    return embeddings


def get_embedding_model_version() -> str:
    """Return the current embedding model version string.

    Used for versioning embeddings stored in pgvector
    (per blueprint Section 17.3 — Embedding Versioning).
    """
    settings = get_settings()
    return settings.bedrock_embedding_model_id
