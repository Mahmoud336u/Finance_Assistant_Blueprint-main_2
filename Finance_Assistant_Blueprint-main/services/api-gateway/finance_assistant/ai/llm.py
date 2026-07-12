"""Meridian AI — LLM Client.

Interfaces with AWS Bedrock (Claude) for chat completions.
Supports both streaming (SSE) and non-streaming responses.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import boto3

from ..config import get_settings
from ..exceptions import ExternalServiceError
from ..logging import get_logger

logger = get_logger(__name__)

_bedrock_client = None


def _get_bedrock_client():
    """Get or create the Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        settings = get_settings()
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.bedrock_region,
        )
    return _bedrock_client


@dataclass
class LLMResponse:
    """Complete LLM response with metadata."""

    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int | None = None


@dataclass
class StreamChunk:
    """A single chunk from a streaming LLM response."""

    text: str
    is_final: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


async def invoke_llm(
    messages: list[dict[str, str]],
    *,
    system_prompt: str | None = None,
    model_id: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> LLMResponse:
    """Invoke the LLM (Claude via Bedrock) for a non-streaming response.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        system_prompt: Optional system prompt.
        model_id: Override the default model.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0.0–1.0).

    Returns:
        LLMResponse with content and usage metadata.
    """
    import time

    settings = get_settings()
    model = model_id or settings.bedrock_model_id

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system_prompt:
        body["system"] = system_prompt

    try:
        client = _get_bedrock_client()
        start = time.perf_counter()

        response = client.invoke_model(
            modelId=model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        result = json.loads(response["body"].read())

        content = result["content"][0]["text"]
        usage = result.get("usage", {})

        await logger.ainfo(
            "LLM invocation complete",
            model=model,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            latency_ms=latency_ms,
        )

        return LLMResponse(
            content=content,
            model=model,
            provider="bedrock",
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            latency_ms=latency_ms,
        )

    except Exception as exc:
        await logger.aerror("LLM invocation failed", model=model, error=str(exc))
        raise ExternalServiceError("bedrock-llm", str(exc)) from exc


async def stream_llm(
    messages: list[dict[str, str]],
    *,
    system_prompt: str | None = None,
    model_id: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> AsyncGenerator[StreamChunk, None]:
    """Stream a response from the LLM (Claude via Bedrock).

    Yields StreamChunk objects as they arrive from the API.
    The final chunk has is_final=True with token usage stats.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        system_prompt: Optional system prompt.
        model_id: Override the default model.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature.

    Yields:
        StreamChunk objects with progressive text content.
    """
    settings = get_settings()
    model = model_id or settings.bedrock_model_id

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system_prompt:
        body["system"] = system_prompt

    try:
        client = _get_bedrock_client()

        response = client.invoke_model_with_response_stream(
            modelId=model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        prompt_tokens = 0
        completion_tokens = 0

        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            event_type = chunk.get("type")

            if event_type == "content_block_delta":
                delta = chunk.get("delta", {})
                text = delta.get("text", "")
                if text:
                    yield StreamChunk(text=text)

            elif event_type == "message_delta":
                usage = chunk.get("usage", {})
                completion_tokens = usage.get("output_tokens", 0)

            elif event_type == "message_start":
                msg = chunk.get("message", {})
                usage = msg.get("usage", {})
                prompt_tokens = usage.get("input_tokens", 0)

            elif event_type == "message_stop":
                yield StreamChunk(
                    text="",
                    is_final=True,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

        await logger.ainfo(
            "LLM streaming complete",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    except Exception as exc:
        await logger.aerror("LLM streaming failed", model=model, error=str(exc))
        raise ExternalServiceError("bedrock-llm-stream", str(exc)) from exc
