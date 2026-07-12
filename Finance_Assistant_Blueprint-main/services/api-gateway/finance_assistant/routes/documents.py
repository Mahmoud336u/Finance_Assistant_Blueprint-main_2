"""Meridian API — Document Ingestion Routes (v1).

Provides endpoints for ingesting documents into the RAG knowledge base.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.embeddings import get_embedding_model_version
from ..ai.ingestion import ingest_document
from ..auth.api_keys import verify_api_key
from ..database import get_db_session
from ..logging import get_logger
from ..models.embedding import KnowledgeEmbedding
from ..schemas import DocumentIngestRequest, DocumentIngestResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentIngestResponse, status_code=201)
async def ingest_document_endpoint(
    request: DocumentIngestRequest,
    service_name: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentIngestResponse:
    """Ingest a document into the RAG knowledge base.

    Pipeline:
    1. Chunk the document into smaller pieces
    2. Generate embeddings for each chunk
    3. Store chunks + embeddings in pgvector

    The document is immediately available for retrieval in subsequent
    chat queries.
    """
    # Step 1 & 2: Chunk and embed
    chunks, summary = await ingest_document(
        content=request.content,
        content_type=request.content_type.value,
        filename=request.filename,
        metadata=request.metadata,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
    )

    # Step 3: Store in database
    model_version = get_embedding_model_version()

    for chunk in chunks:
        db_record = KnowledgeEmbedding(
            content_type=request.content_type.value,
            content=chunk.content,
            metadata_json=chunk.metadata,
            embedding=chunk.embedding,
            embedding_model_version=model_version,
        )
        db.add(db_record)

    await db.flush()

    await logger.ainfo(
        "Document ingested and stored",
        document_id=summary.document_id,
        chunks_stored=len(chunks),
        content_type=request.content_type.value,
    )

    return DocumentIngestResponse(
        document_id=summary.document_id,
        filename=summary.filename,
        content_type=request.content_type,
        chunks_created=summary.chunks_created,
        total_characters=summary.total_characters,
        embedding_model=summary.embedding_model,
        ingested_at=datetime.fromisoformat(summary.ingested_at),
    )


@router.get("/stats")
async def document_stats(
    service_name: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get statistics about the knowledge base.

    Returns counts of documents, chunks, and embeddings by content type.
    """
    from sqlalchemy import func, select

    result = await db.execute(
        select(
            KnowledgeEmbedding.content_type,
            func.count().label("count"),
        ).group_by(KnowledgeEmbedding.content_type)
    )
    rows = result.all()

    stats = {row[0]: row[1] for row in rows}
    total = sum(stats.values())

    return {
        "total_chunks": total,
        "by_content_type": stats,
        "embedding_model": get_embedding_model_version(),
    }
