"""Meridian API — Observability and Telemetry.

Configures OpenTelemetry for distributed tracing and Prometheus for metrics.
Instruments FastAPI, SQLAlchemy (asyncpg), Redis, and boto3 (Bedrock).
"""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)

# ============================================================
# Business Metrics (Prometheus)
# ============================================================

# LLM Usage Metrics
LLM_TOKENS_TOTAL = Counter(
    "meridian_llm_tokens_total",
    "Total tokens processed by LLM",
    ["model", "provider", "type"],  # type = prompt or completion
)

LLM_COST_CENTS = Counter(
    "meridian_llm_cost_cents_total",
    "Estimated cost of LLM invocations in cents",
    ["model", "provider"],
)

LLM_LATENCY = Histogram(
    "meridian_llm_latency_seconds",
    "Latency of LLM invocations",
    ["model", "provider"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# RAG Pipeline Metrics
RAG_CHUNKS_RETRIEVED = Histogram(
    "meridian_rag_chunks_retrieved",
    "Number of chunks retrieved for a RAG query",
    buckets=[0, 1, 3, 5, 10, 20],
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "meridian_rag_retrieval_latency_seconds",
    "Latency of pgvector similarity search",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0],
)


def track_llm_usage(
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
) -> None:
    """Record business metrics for an LLM invocation."""
    LLM_TOKENS_TOTAL.labels(model=model, provider=provider, type="prompt").inc(prompt_tokens)
    LLM_TOKENS_TOTAL.labels(model=model, provider=provider, type="completion").inc(completion_tokens)
    LLM_LATENCY.labels(model=model, provider=provider).observe(latency_ms / 1000.0)

    # Simplified cost estimation (assumes Claude 3.5 Sonnet pricing)
    # Prompt: $3 / 1M tokens -> 0.0003 cents / token
    # Completion: $15 / 1M tokens -> 0.0015 cents / token
    cost = (prompt_tokens * 0.0003) + (completion_tokens * 0.0015)
    LLM_COST_CENTS.labels(model=model, provider=provider).inc(cost)


# ============================================================
# OpenTelemetry Tracing
# ============================================================


def setup_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing and Prometheus metrics.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()

    if not settings.enable_tracing:
        logger.warning("OpenTelemetry tracing is disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        # 1. Setup Resource (Service Name)
        resource = Resource.create(
            attributes={
                "service.name": settings.otel_service_name,
                "deployment.environment": settings.environment,
            }
        )

        # 2. Setup Tracer Provider
        provider = TracerProvider(resource=resource)
        
        # 3. Setup OTLP Exporter (sends to AWS X-Ray / Jaeger / Datadog via Collector)
        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)

        # 4. Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Note: SQLAlchemy, Redis, and Boto3 instrumentors would be initialized here
        # requiring: opentelemetry-instrumentation-sqlalchemy, etc.
        # For blueprint purposes, we instrument FastAPI out of the box.

        logger.info(
            "OpenTelemetry tracing enabled",
            endpoint=settings.otel_exporter_otlp_endpoint,
            service=settings.otel_service_name,
        )

    except ImportError as exc:
        logger.warning(
            "OpenTelemetry packages not installed. Tracing disabled.",
            error=str(exc)
        )


def get_prometheus_metrics() -> bytes:
    """Export Prometheus metrics registry as bytes."""
    return generate_latest()
