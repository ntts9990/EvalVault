#!/usr/bin/env python3
"""Emit sample Open RAG Trace spans to an OTLP endpoint."""

from __future__ import annotations

import argparse
import logging
import time
from collections.abc import Mapping, Sequence
from typing import Any

from evalvault.adapters.outbound.tracer import (
    OpenRagTraceAdapter,
    build_eval_attributes,
    build_input_output_attributes,
    build_llm_attributes,
    build_retrieval_attributes,
    install_open_rag_log_handler,
    serialize_json,
    trace_module,
)

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "OpenTelemetry SDK is required. Install with:\n"
        "pip install opentelemetry-api opentelemetry-sdk "
        "opentelemetry-exporter-otlp-proto-http"
    ) from exc

logger = logging.getLogger("rag-demo")


def setup_tracer(endpoint: str, service_name: str, environment: str) -> None:
    resource = Resource.create(
        {"service.name": service_name, "deployment.environment": environment}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)


def _mock_documents(query: str, top_k: int) -> list[dict[str, Any]]:
    return [
        {"doc_id": f"policy_{index + 1}", "score": 0.82 - index * 0.05, "source": "kb"}
        for index in range(top_k)
    ]


def _doc_ids(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    doc_ids: list[str] = []
    for document in documents:
        doc_id = document.get("doc_id")
        if doc_id is not None:
            doc_ids.append(str(doc_id))
    return doc_ids


def _reference_preview(documents: Sequence[Mapping[str, Any]], limit: int = 3) -> str:
    entries: list[str] = []
    for document in documents[:limit]:
        doc_id = document.get("doc_id")
        if doc_id is None:
            continue
        score = document.get("score")
        if score is None:
            entries.append(str(doc_id))
        else:
            entries.append(f"{doc_id}({score})")
    if len(documents) > limit:
        entries.append(f"+{len(documents) - limit} more")
    return ", ".join(entries)


def _retrieval_attrs(query: str, top_k: int = 5) -> dict[str, Any]:
    attrs = build_retrieval_attributes(query, top_k=top_k)
    attrs.update(build_input_output_attributes(input_value=query))
    return attrs


def _llm_attrs(prompt: str, model_name: str = "gpt-4o-mini") -> dict[str, Any]:
    attrs = build_llm_attributes(
        model_name=model_name,
        temperature=0.2,
        token_counts={"total": 1050},
    )
    attrs.update(build_input_output_attributes(input_value=prompt))
    return attrs


def _eval_attrs(answer: str, reference_docs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    attrs = build_eval_attributes("faithfulness")
    attrs.update(build_input_output_attributes(input_value=answer))
    doc_ids = _doc_ids(reference_docs)
    attrs["custom.reference_count"] = len(reference_docs)
    if doc_ids:
        attrs["custom.reference_doc_ids"] = doc_ids
    preview = _reference_preview(reference_docs)
    if preview:
        attrs["custom.reference_preview"] = preview
    attrs["custom.reference_json"] = serialize_json(reference_docs)
    return attrs


@trace_module("retrieve", attributes_builder=_retrieval_attrs)
def retrieve_documents(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    logger.info("retrieval start", extra={"query": query, "top_k": top_k})
    docs = _mock_documents(query, top_k)
    span = trace.get_current_span()
    span.set_attribute("retrieval.documents_json", serialize_json(docs))
    span.set_attribute("output.value", _doc_ids(docs))
    span.set_attribute("custom.retrieval.doc_count", len(docs))
    logger.info("retrieval complete", extra={"count": len(docs)})
    time.sleep(0.05)
    return docs


@trace_module("llm", attributes_builder=_llm_attrs)
def generate_answer(prompt: str, model_name: str = "gpt-4o-mini") -> str:
    logger.info("llm start", extra={"model_name": model_name})
    answer = "The payout conditions are defined in the policy."
    span = trace.get_current_span()
    span.set_attribute("output.value", answer)
    logger.info("llm complete")
    time.sleep(0.05)
    return answer


@trace_module("eval", attributes_builder=_eval_attrs)
def evaluate_answer(answer: str, reference_docs: Sequence[Mapping[str, Any]]) -> float:
    logger.info("eval start", extra={"metric": "faithfulness"})
    score = 0.91
    span = trace.get_current_span()
    span.set_attribute("eval.score", score)
    span.set_attribute("eval.passed", score >= 0.8)
    span.set_attribute("output.value", score)
    logger.info("eval complete", extra={"score": score})
    time.sleep(0.05)
    return score


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit demo spans for Open RAG Trace.")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:6006/v1/traces",
        help="OTLP HTTP endpoint (default: Phoenix localhost)",
    )
    parser.add_argument("--service", default="rag-service", help="service.name")
    parser.add_argument("--env", default="dev", help="deployment.environment")
    args = parser.parse_args()

    setup_tracer(args.endpoint, args.service, args.env)
    tracer = trace.get_tracer("open-rag-trace-demo")
    adapter = OpenRagTraceAdapter(tracer=tracer)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    install_open_rag_log_handler(logger)
    logger.setLevel(logging.INFO)

    query = "insurance payout conditions"
    root_attrs = build_input_output_attributes(input_value=query)

    with adapter.span("rag_pipeline", "custom.pipeline", root_attrs):
        documents = retrieve_documents(query, top_k=3)
        answer = generate_answer(query)
        evaluate_answer(answer, reference_docs=documents)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
