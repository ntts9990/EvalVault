"""Phoenix instrumentation setup for automatic LLM tracing.

This module provides automatic instrumentation for LangChain and LlamaIndex,
sending all LLM calls to Phoenix for observability.

Example:
    >>> from evalvault.config.instrumentation import setup_phoenix_instrumentation
    >>> setup_phoenix_instrumentation("http://localhost:6006/v1/traces")
    >>> # All subsequent LangChain/LlamaIndex calls are automatically traced
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger(__name__)

_instrumentation_initialized = False
_tracer_provider: TracerProvider | None = None


def setup_phoenix_instrumentation(
    endpoint: str = "http://localhost:6006/v1/traces",
    service_name: str = "evalvault",
    project_name: str | None = None,
    enable_langchain: bool = True,
    enable_openai: bool = True,
    sample_rate: float = 1.0,
    headers: dict[str, str] | None = None,
) -> TracerProvider | None:
    """Setup Phoenix instrumentation for automatic LLM tracing.

    This function configures OpenTelemetry to send traces to Phoenix,
    and instruments LangChain for automatic tracing.

    Args:
        endpoint: Phoenix OTLP endpoint URL
        service_name: Service name for traces
        enable_langchain: Enable LangChain auto-instrumentation
        enable_openai: Enable OpenAI auto-instrumentation

    Returns:
        TracerProvider if successful, None if dependencies not available

    Example:
        >>> setup_phoenix_instrumentation("http://localhost:6006/v1/traces")
        >>> # Now all LangChain calls are traced
        >>> chain = load_qa_chain(llm, chain_type="stuff")
        >>> answer = chain.run(input_documents=docs, question=question)
        >>> # Check Phoenix UI at http://localhost:6006
    """
    global _instrumentation_initialized, _tracer_provider

    if _instrumentation_initialized:
        logger.debug("Phoenix instrumentation already initialized")
        return _tracer_provider

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except ImportError as e:
        logger.warning("OpenTelemetry SDK not installed. Install with: uv sync --extra phoenix")
        logger.debug(f"Import error: {e}")
        return None

    # Create resource with service name
    resource_attributes = {
        "service.name": service_name,
        "service.version": "0.1.0",
    }
    if project_name:
        resource_attributes["project.name"] = project_name
    resource = Resource.create(resource_attributes)

    # Clamp sample rate between 0 and 1
    ratio = max(0.0, min(sample_rate, 1.0))

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(ratio))

    # Add OTLP exporter for Phoenix
    exporter_kwargs: dict[str, Any] = {"endpoint": endpoint}
    if headers:
        exporter_kwargs["headers"] = headers
    otlp_exporter = OTLPSpanExporter(**exporter_kwargs)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument LangChain
    if enable_langchain:
        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor

            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("LangChain instrumentation enabled")
        except ImportError:
            logger.debug(
                "LangChain instrumentation not available. "
                "Install: pip install openinference-instrumentation-langchain"
            )

    # Instrument OpenAI
    if enable_openai:
        try:
            from openinference.instrumentation.openai import OpenAIInstrumentor

            OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("OpenAI instrumentation enabled")
        except ImportError:
            logger.debug(
                "OpenAI instrumentation not available. "
                "Install: pip install openinference-instrumentation-openai"
            )

    _tracer_provider = tracer_provider
    _instrumentation_initialized = True

    logger.info(f"Phoenix instrumentation initialized: {endpoint}")
    return tracer_provider


def shutdown_instrumentation() -> None:
    """Shutdown instrumentation and flush remaining traces."""
    global _instrumentation_initialized, _tracer_provider

    if _tracer_provider:
        _tracer_provider.force_flush()
        _tracer_provider.shutdown()
        _tracer_provider = None

    _instrumentation_initialized = False
    logger.info("Phoenix instrumentation shutdown complete")


def is_instrumentation_enabled() -> bool:
    """Check if instrumentation is enabled."""
    return _instrumentation_initialized


def get_tracer_provider() -> TracerProvider | None:
    """Get the current tracer provider."""
    return _tracer_provider
