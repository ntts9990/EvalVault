"""Pipeline API contract tests for Web UI compatibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette import status

from evalvault.adapters.inbound.api.main import create_app
from evalvault.config.model_config import reset_model_config
from evalvault.config.settings import reset_settings
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent


@dataclass
class FakeNodeResult:
    """Minimal node result payload for API serialization."""

    status: str = "completed"
    error: str | None = None
    duration_ms: float = 120.0
    output: dict[str, Any] = field(
        default_factory=lambda: {"report": "# Summary Report\n\n- Stable."}
    )


@dataclass
class FakePipelineNode:
    """Pipeline node definition for intent catalog."""

    id: str
    name: str
    module: str
    depends_on: list[str]


@dataclass
class FakePipelineTemplate:
    """Pipeline template container."""

    nodes: list[FakePipelineNode]


class FakePipelineResult:
    """Minimal pipeline result for contract validation."""

    def __init__(self) -> None:
        self.intent = AnalysisIntent.GENERATE_SUMMARY
        self.is_complete = True
        self.total_duration_ms = 1200.0
        self.pipeline_id = "pipeline-123"
        self.started_at = datetime(2026, 1, 9, 10, 0, 0)
        self.finished_at = datetime(2026, 1, 9, 10, 0, 1)
        self.final_output = {
            "report": {
                "report": "# Summary Report\n\n- Stable.",
                "llm_used": True,
                "llm_model": "gpt-4o-mini",
            }
        }
        self.node_results = {"summary_report": FakeNodeResult()}


class FakePipelineService:
    """Pipeline service stub for API contract tests."""

    def __init__(self, result: FakePipelineResult) -> None:
        self._result = result
        self._template = FakePipelineTemplate(
            nodes=[
                FakePipelineNode(
                    id="summary_report",
                    name="Summary Report",
                    module="summary_report",
                    depends_on=[],
                )
            ]
        )

    async def analyze_intent_async(
        self,
        _intent: AnalysisIntent,
        query: str,
        run_id: str | None = None,
        **_params: Any,
    ) -> FakePipelineResult:
        return self._result

    async def analyze_async(
        self,
        query: str,
        run_id: str | None = None,
        **_params: Any,
    ) -> FakePipelineResult:
        return self._result

    def get_available_intents(self) -> list[AnalysisIntent]:
        return [AnalysisIntent.GENERATE_SUMMARY]

    def get_registered_modules(self) -> list[str]:
        return ["summary_report"]

    def get_pipeline_template(self, _intent: AnalysisIntent) -> FakePipelineTemplate:
        return self._template


class FakeStorage:
    """In-memory storage stub for pipeline results."""

    def __init__(self) -> None:
        created_at = datetime(2026, 1, 9, 10, 2, 0).isoformat()
        self._records: dict[str, dict[str, Any]] = {
            "result-123": {
                "result_id": "result-123",
                "intent": AnalysisIntent.GENERATE_SUMMARY.value,
                "query": "요약해줘",
                "run_id": "run-123",
                "pipeline_id": "pipeline-123",
                "profile": "dev",
                "tags": ["baseline"],
                "duration_ms": 1200.0,
                "is_complete": True,
                "created_at": created_at,
                "started_at": "2026-01-09T10:00:00",
                "finished_at": "2026-01-09T10:00:01",
                "final_output": {"report": {"report": "# Summary Report"}},
                "node_results": {"summary_report": {"status": "completed"}},
                "metadata": {"dataset": "insurance"},
            }
        }

    def save_pipeline_result(self, record: dict[str, Any]) -> None:
        self._records[record["result_id"]] = record

    def list_pipeline_results(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._records.values())[:limit]

    def get_pipeline_result(self, result_id: str) -> dict[str, Any]:
        if result_id not in self._records:
            raise KeyError(f"Pipeline result not found: {result_id}")
        return self._records[result_id]


@pytest.fixture()
def api_client() -> TestClient:
    """FastAPI TestClient with adapter stubbed out."""
    with patch(
        "evalvault.adapters.inbound.api.main.create_adapter",
        return_value=MagicMock(),
    ):
        app = create_app()
        with TestClient(app) as client:
            yield client


@pytest.fixture()
def knowledge_client(monkeypatch) -> TestClient:
    reset_settings()
    reset_model_config()
    monkeypatch.setenv("KNOWLEDGE_READ_TOKENS", "read-token")
    monkeypatch.setenv("KNOWLEDGE_WRITE_TOKENS", "write-token")
    with patch(
        "evalvault.adapters.inbound.api.main.create_adapter",
        return_value=MagicMock(),
    ):
        app = create_app()
        with TestClient(app) as client:
            yield client


@pytest.fixture()
def rate_limited_client(monkeypatch) -> TestClient:
    reset_settings()
    reset_model_config()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_BLOCK_THRESHOLD", "1")
    monkeypatch.delenv("API_AUTH_TOKENS", raising=False)
    with patch(
        "evalvault.adapters.inbound.api.main.create_adapter",
        return_value=MagicMock(),
    ):
        app = create_app()
        with TestClient(app) as client:
            yield client


@pytest.fixture()
def pipeline_mocks() -> tuple[FakePipelineService, FakeStorage]:
    """Service/storage stubs for pipeline endpoints."""
    result = FakePipelineResult()
    service = FakePipelineService(result)
    storage = FakeStorage()
    return service, storage


def test_pipeline_analyze_contract(
    api_client: TestClient, pipeline_mocks: tuple[FakePipelineService, FakeStorage]
) -> None:
    """Analyze endpoint should keep the expected response structure."""
    service, storage = pipeline_mocks
    with patch(
        "evalvault.adapters.inbound.api.routers.pipeline._build_pipeline_service",
        return_value=(service, storage),
    ):
        response = api_client.post(
            "/api/v1/pipeline/analyze",
            json={"query": "요약해줘", "intent": "generate_summary"},
        )

    assert response.status_code == 200
    payload = response.json()
    required_keys = {
        "intent",
        "is_complete",
        "duration_ms",
        "pipeline_id",
        "started_at",
        "finished_at",
        "final_output",
        "node_results",
    }
    assert required_keys.issubset(payload.keys())
    assert isinstance(payload["node_results"], dict)
    node = payload["node_results"]["summary_report"]
    assert {"status", "error", "duration_ms", "output"}.issubset(node.keys())


def test_pipeline_intents_contract(
    api_client: TestClient, pipeline_mocks: tuple[FakePipelineService, FakeStorage]
) -> None:
    """Intents endpoint should provide UI catalog fields."""
    service, storage = pipeline_mocks
    with patch(
        "evalvault.adapters.inbound.api.routers.pipeline._build_pipeline_service",
        return_value=(service, storage),
    ):
        response = api_client.get("/api/v1/pipeline/intents")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload, "intent catalog should not be empty"
    first = payload[0]
    required_keys = {
        "intent",
        "label",
        "category",
        "description",
        "sample_query",
        "available",
        "missing_modules",
        "nodes",
    }
    assert required_keys.issubset(first.keys())


def test_pipeline_results_contract(
    api_client: TestClient, pipeline_mocks: tuple[FakePipelineService, FakeStorage]
) -> None:
    """Saved results endpoints should keep summary/detail contracts."""
    service, storage = pipeline_mocks
    with patch(
        "evalvault.adapters.inbound.api.routers.pipeline._build_pipeline_service",
        return_value=(service, storage),
    ):
        list_response = api_client.get("/api/v1/pipeline/results?limit=5")
        detail_response = api_client.get("/api/v1/pipeline/results/result-123")

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert isinstance(list_payload, list)
    assert list_payload
    summary = list_payload[0]
    summary_keys = {
        "result_id",
        "intent",
        "label",
        "query",
        "run_id",
        "duration_ms",
        "is_complete",
        "created_at",
    }
    assert summary_keys.issubset(summary.keys())

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    detail_keys = summary_keys | {"pipeline_id", "final_output", "node_results", "metadata"}
    assert detail_keys.issubset(detail_payload.keys())


def test_pipeline_results_save_contract(
    api_client: TestClient, pipeline_mocks: tuple[FakePipelineService, FakeStorage]
) -> None:
    """Save endpoint should return summary fields after storing."""
    service, storage = pipeline_mocks
    with patch(
        "evalvault.adapters.inbound.api.routers.pipeline._build_pipeline_service",
        return_value=(service, storage),
    ):
        response = api_client.post(
            "/api/v1/pipeline/results",
            json={
                "intent": "generate_summary",
                "query": "요약해줘",
                "run_id": "run-456",
                "is_complete": True,
                "duration_ms": 800.0,
                "final_output": {"report": {"report": "# Summary"}},
                "node_results": {"summary_report": {"status": "completed"}},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "generate_summary"
    assert "result_id" in payload


def test_knowledge_requires_read_token(knowledge_client: TestClient) -> None:
    response = knowledge_client.get("/api/v1/knowledge/files")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = knowledge_client.get(
        "/api/v1/knowledge/files",
        headers={"Authorization": "Bearer read-token"},
    )
    assert response.status_code == status.HTTP_200_OK

    response = knowledge_client.get(
        "/api/v1/knowledge/files",
        headers={"Authorization": "Bearer write-token"},
    )
    assert response.status_code == status.HTTP_200_OK


def test_knowledge_requires_write_token(knowledge_client: TestClient) -> None:
    files = {"files": ("doc.txt", b"hello", "text/plain")}

    response = knowledge_client.post("/api/v1/knowledge/upload", files=files)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = knowledge_client.post(
        "/api/v1/knowledge/upload",
        headers={"Authorization": "Bearer write-token"},
        files=files,
    )
    assert response.status_code == status.HTTP_200_OK


def test_rate_limit_blocks_excess_requests(rate_limited_client: TestClient) -> None:
    response = rate_limited_client.get("/api/v1/config/profiles")
    assert response.status_code == status.HTTP_200_OK

    response = rate_limited_client.get("/api/v1/config/profiles")
    assert response.status_code == status.HTTP_200_OK

    response = rate_limited_client.get("/api/v1/config/profiles")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.headers.get("Retry-After")
