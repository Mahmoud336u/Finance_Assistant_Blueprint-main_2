"""Meridian API — Chat Routes (v1).

Provides the /v1/chat endpoint for AI-powered financial conversations.
Supports both non-streaming and SSE streaming responses.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.llm import invoke_llm, stream_llm
from ..ai.prompts import assemble_chat_prompt
from ..ai.retriever import retrieve_similar_chunks, retrieve_user_context
from ..database import get_db_session
from ..exceptions import NotFoundError, ValidationError
from ..logging import get_logger
from ..schemas import ChatMessageRequest, ChatMessageResponse, ChatRole

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ChatMessageResponse | StreamingResponse:
    """Send a message and receive an AI-powered financial response.

    The pipeline:
    1. Retrieve relevant knowledge base chunks (RAG)
    2. Retrieve user-specific financial context
    3. Assemble the prompt with context + history
    4. Invoke the LLM (Claude via Bedrock)
    5. Store the conversation and return the response

    If `stream=true`, returns an SSE stream instead of a JSON response.
    """
    if not request.message.strip():
        raise ValidationError("Message cannot be empty")

    # TODO: Get actual user_id from auth middleware (Phase 4)
    # For now, use a placeholder for development
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    # Step 1: Retrieve RAG context
    rag_chunks = await retrieve_similar_chunks(
        query=request.message,
        db=db,
        top_k=5,
        similarity_threshold=0.7,
    )

    # Step 2: Retrieve user-specific context
    user_context = await retrieve_user_context(
        query=request.message,
        user_id=user_id,
        db=db,
        top_k=3,
    )

    # Step 3: Load conversation history if continuing
    conversation_history: list[dict[str, str]] = []
    conversation_id = request.conversation_id or uuid.uuid4()

    if request.conversation_id:
        # TODO: Load conversation history from database (Phase 3.7)
        conversation_history = []

    # Step 4: Assemble the prompt
    assembled = await assemble_chat_prompt(
        query=request.message,
        rag_chunks=rag_chunks,
        user_context=user_context,
        conversation_history=conversation_history,
    )

    # Step 5: Stream or invoke
    if request.stream:
        return StreamingResponse(
            _stream_response(
                assembled=assembled,
                conversation_id=conversation_id,
                user_id=user_id,
                db=db,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming response
    llm_response = await invoke_llm(
        messages=assembled.messages,
        system_prompt=assembled.system_prompt,
    )

    message_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # TODO: Store conversation and message in database (Phase 3.7)

    await logger.ainfo(
        "Chat response generated",
        conversation_id=str(conversation_id),
        rag_chunks=assembled.rag_chunks_used,
        prompt_tokens=llm_response.prompt_tokens,
        completion_tokens=llm_response.completion_tokens,
        latency_ms=llm_response.latency_ms,
    )

    return ChatMessageResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        role=ChatRole.ASSISTANT,
        content=llm_response.content,
        model=llm_response.model,
        provider=llm_response.provider,
        prompt_tokens=llm_response.prompt_tokens,
        completion_tokens=llm_response.completion_tokens,
        latency_ms=llm_response.latency_ms,
        rag_chunks_used=assembled.total_context_chunks,
        created_at=now,
    )


async def _stream_response(
    assembled,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
):
    """Generate SSE events from the LLM streaming response.

    SSE format:
        event: delta
        data: {"text": "chunk of text"}

        event: metadata
        data: {"prompt_tokens": 123, "completion_tokens": 456, ...}
    """
    full_content = ""

    async for chunk in stream_llm(
        messages=assembled.messages,
        system_prompt=assembled.system_prompt,
    ):
        if chunk.is_final:
            # Send final metadata event
            metadata = json.dumps({
                "conversation_id": str(conversation_id),
                "prompt_tokens": chunk.prompt_tokens,
                "completion_tokens": chunk.completion_tokens,
                "rag_chunks_used": assembled.total_context_chunks,
            })
            yield f"event: metadata\ndata: {metadata}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
        else:
            full_content += chunk.text
            data = json.dumps({"text": chunk.text})
            yield f"event: delta\ndata: {data}\n\n"

    # TODO: Store full response in database after streaming completes
