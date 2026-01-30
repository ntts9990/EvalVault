"""Web UI adapter implementing WebUIPort."""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast
from urllib.request import urlopen

from evalvault.adapters.outbound.analysis import (
    CausalAnalysisAdapter,
    NLPAnalysisAdapter,
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.cache import MemoryCacheAdapter
from evalvault.adapters.outbound.judge_calibration_reporter import JudgeCalibrationReporter
from evalvault.adapters.outbound.ops.report_renderer import render_json, render_markdown
from evalvault.adapters.outbound.report import MarkdownReportAdapter
from evalvault.config.phoenix_support import PhoenixExperimentResolver
from evalvault.config.settings import Settings, resolve_tracker_providers
from evalvault.domain.entities import (
    CalibrationResult,
    FeedbackSummary,
    SatisfactionFeedback,
)
from evalvault.domain.entities.analysis import AnalysisBundle
from evalvault.domain.entities.debug import DebugReport
from evalvault.domain.entities.prompt import PromptSetBundle
from evalvault.domain.metrics.registry import (
    get_metric_descriptions as registry_metric_descriptions,
)
from evalvault.domain.metrics.registry import (
    list_metric_names,
    list_metric_specs,
)
from evalvault.domain.services.analysis_service import AnalysisService
from evalvault.domain.services.cluster_map_builder import build_cluster_map
from evalvault.domain.services.debug_report_service import DebugReportService
from evalvault.domain.services.judge_calibration_service import JudgeCalibrationService
from evalvault.domain.services.ops_report_service import OpsReportService
from evalvault.domain.services.prompt_registry import (
    PromptInput,
    build_prompt_bundle,
    build_prompt_inputs_from_snapshots,
    build_prompt_summary,
)
from evalvault.domain.services.prompt_status import extract_prompt_entries
from evalvault.domain.services.satisfaction_calibration_service import (
    SatisfactionCalibrationService,
)
from evalvault.domain.services.stage_event_builder import StageEventBuilder
from evalvault.domain.services.stage_metric_service import StageMetricService
from evalvault.domain.services.threshold_profiles import apply_threshold_profile
from evalvault.domain.services.visual_space_service import VisualSpaceQuery, VisualSpaceService
from evalvault.ports.inbound.web_port import (
    EvalProgress,
    EvalRequest,
    RunFilters,
    RunSummary,
)
from evalvault.ports.outbound.stage_storage_port import StageStoragePort

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun, RunClusterMap, RunClusterMapInfo
    from evalvault.domain.entities.improvement import ImprovementReport
    from evalvault.domain.entities.stage import StageEvent, StageMetric
    from evalvault.domain.services.evaluator import RagasEvaluator
    from evalvault.ports.outbound.dataset_port import DatasetPort
    from evalvault.ports.outbound.llm_port import LLMPort
    from evalvault.ports.outbound.report_port import ReportPort
    from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """품질 게이트 개별 메트릭 결과."""

    metric: str
    score: float
    threshold: float
    passed: bool
    gap: float


@dataclass
class GateReport:
    """품질 게이트 전체 리포트."""

    run_id: str
    results: list[GateResult]
    overall_passed: bool
    regression_detected: bool = False
    regression_amount: float | None = None


class WebUIAdapter:
    """웹 UI 어댑터.

    WebUIPort 프로토콜을 구현하여 웹 UI가 도메인 서비스에
    접근할 수 있도록 합니다.
    """

    def __init__(
        self,
        storage: StoragePort | None = None,
        evaluator: RagasEvaluator | None = None,
        report_generator: ReportPort | None = None,
        llm_adapter: LLMPort | None = None,
        data_loader: DatasetPort | None = None,
        settings: Settings | None = None,
    ):
        """어댑터 초기화.

        Args:
            storage: 저장소 어댑터 (선택적)
            evaluator: 평가 서비스 (선택적)
            report_generator: 보고서 생성기 (선택적)
            llm_adapter: LLM 어댑터 (선택적)
            data_loader: 데이터 로더 (선택적)
        """
        resolved_settings = settings or Settings()
        if storage is None:
            from evalvault.adapters.outbound.storage.factory import build_storage_adapter

            try:
                storage = build_storage_adapter(settings=resolved_settings)
            except Exception as exc:
                logger.warning("Storage initialization failed: %s", exc)
                storage = None

        self._storage = storage
        self._evaluator = evaluator
        self._report_generator = report_generator
        self._llm_adapter = llm_adapter
        self._data_loader = data_loader
        self._settings = resolved_settings
        self._phoenix_resolver: PhoenixExperimentResolver | None = None
        self._phoenix_resolver_checked = False

    def _get_phoenix_resolver(self) -> PhoenixExperimentResolver | None:
        """Lazily initialize Phoenix resolver if available."""

        if self._phoenix_resolver_checked:
            return self._phoenix_resolver

        self._phoenix_resolver_checked = True
        try:
            settings = self._settings or Settings()
        except Exception:
            self._settings = None
            self._phoenix_resolver = None
            return None

        self._settings = settings
        resolver = PhoenixExperimentResolver(settings)
        if not resolver.is_available:
            self._phoenix_resolver = None
            return None

        self._phoenix_resolver = resolver
        return resolver

    def apply_settings_patch(self, overrides: dict[str, Any]) -> Settings:
        """런타임 설정을 업데이트하고 LLM 어댑터를 재초기화."""
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.config.settings import apply_runtime_overrides

        settings = apply_runtime_overrides(overrides)
        self._settings = settings
        self._phoenix_resolver_checked = False
        self._phoenix_resolver = None

        try:
            self._llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            logger.warning("LLM adapter re-initialization failed: %s", exc)
            self._llm_adapter = None
        return settings

    def _get_llm_for_model(self, model_id: str | None) -> LLMPort | None:
        """Get LLM adapter for specified model, or default if None.

        Args:
            model_id: Model ID in format "provider/model_name", or None for default

        Returns:
            LLMPort instance for the specified model, or default adapter
        """
        if model_id is None:
            return self._llm_adapter

        # Parse model_id: "provider/model_name"
        if "/" not in model_id:
            logger.warning(f"Invalid model_id format: {model_id}, using default")
            return self._llm_adapter

        provider, model_name = model_id.split("/", 1)

        # Get base settings
        settings = self._settings or Settings()

        # Create adapter for specific model
        from evalvault.adapters.outbound.llm import create_llm_adapter_for_model

        try:
            return create_llm_adapter_for_model(provider, model_name, settings)
        except Exception as e:
            logger.warning(f"Failed to create LLM adapter for {model_id}: {e}, using default")
            return self._llm_adapter

    def _get_trackers(
        self,
        settings: Settings,
        tracker_config: dict[str, Any] | None,
    ) -> list[tuple[str, Any]]:
        provider = (tracker_config or {}).get("provider") or settings.tracker_provider or "none"
        providers = resolve_tracker_providers(provider)
        if not providers or providers == ["none"]:
            return []
        required = {"mlflow", "phoenix"}
        if not required.issubset(set(providers)):
            raise RuntimeError("Tracker must include both mlflow and phoenix")

        trackers: list[tuple[str, Any]] = []
        for entry in providers:
            if entry == "langfuse":
                if not settings.langfuse_public_key or not settings.langfuse_secret_key:
                    raise RuntimeError("Langfuse credentials missing")
                from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter

                trackers.append(
                    (
                        entry,
                        LangfuseAdapter(
                            public_key=settings.langfuse_public_key,
                            secret_key=settings.langfuse_secret_key,
                            host=settings.langfuse_host,
                        ),
                    )
                )
                continue

            if entry == "phoenix":
                from evalvault.config.phoenix_support import ensure_phoenix_instrumentation

                ensure_phoenix_instrumentation(settings, force=True)
                try:
                    from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter
                except ImportError as exc:
                    raise RuntimeError("Phoenix extras not installed") from exc
                trackers.append(
                    (
                        entry,
                        PhoenixAdapter(
                            endpoint=settings.phoenix_endpoint,
                            project_name=getattr(settings, "phoenix_project_name", None),
                            annotations_enabled=getattr(
                                settings,
                                "phoenix_annotations_enabled",
                                True,
                            ),
                        ),
                    )
                )
                continue

            if entry == "mlflow":
                if not settings.mlflow_tracking_uri:
                    raise RuntimeError("MLflow tracking URI missing")
                try:
                    from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter
                except ImportError as exc:
                    raise RuntimeError("MLflow adapter unavailable") from exc
                trackers.append(
                    (
                        entry,
                        MLflowAdapter(
                            tracking_uri=settings.mlflow_tracking_uri,
                            experiment_name=settings.mlflow_experiment_name,
                        ),
                    )
                )
                continue

            raise RuntimeError(f"Unknown tracker provider: {entry}")

        return trackers

    @staticmethod
    def _build_phoenix_trace_url(endpoint: str, trace_id: str) -> str:
        base = endpoint.rstrip("/")
        suffix = "/v1/traces"
        if base.endswith(suffix):
            base = base[: -len(suffix)]
        return f"{base.rstrip('/')}/#/traces/{trace_id}"

    def _build_retriever(
        self,
        config: dict[str, Any],
        settings: Settings,
    ) -> tuple[Any, list[str], int, str, str]:
        mode = str(config.get("mode") or "").lower()
        if mode not in {"bm25", "hybrid"}:
            raise ValueError(f"Unsupported retriever mode: {mode}")

        docs_path = config.get("docs_path") or config.get("documents_path") or config.get("docs")
        if not docs_path:
            raise ValueError("Retriever docs_path is required.")

        path = Path(str(docs_path))
        if not path.exists():
            raise ValueError(f"Retriever docs_path not found: {path}")

        documents, doc_ids = self._load_retriever_documents(path)

        try:
            from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Korean NLP dependencies not available.") from exc

        toolkit = KoreanNLPToolkit()
        retriever = toolkit.build_retriever(documents, use_hybrid=mode == "hybrid", verbose=False)
        if retriever is None:
            raise RuntimeError("Retriever initialization failed.")

        top_k = int(config.get("top_k") or 5)
        return retriever, doc_ids, top_k, mode, str(path)

    def _load_retriever_documents(self, file_path: Path) -> tuple[list[str], list[str]]:
        suffix = file_path.suffix.lower()
        if suffix == ".jsonl":
            items = self._load_retriever_jsonl(file_path)
        elif suffix == ".json":
            items = self._load_retriever_json(file_path)
        else:
            items = self._load_retriever_text(file_path)

        documents: list[str] = []
        doc_ids: list[str] = []

        for idx, item in enumerate(items, start=1):
            content, doc_id = self._normalize_document_item(item, idx)
            if not content:
                continue
            documents.append(content)
            doc_ids.append(doc_id)

        if not documents:
            raise ValueError("Retriever documents are empty.")

        return documents, doc_ids

    @staticmethod
    def _load_retriever_json(file_path: Path) -> list[Any]:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "documents" in payload:
            items = payload["documents"]
        else:
            items = payload
        if not isinstance(items, list):
            raise ValueError("Retriever JSON must be a list or contain 'documents'.")
        return items

    @staticmethod
    def _load_retriever_jsonl(file_path: Path) -> list[Any]:
        items: list[Any] = []
        with file_path.open(encoding="utf-8") as handle:
            for idx, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    items.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {idx}.") from exc
        return items

    @staticmethod
    def _load_retriever_text(file_path: Path) -> list[str]:
        items: list[str] = []
        with file_path.open(encoding="utf-8") as handle:
            for line in handle:
                content = line.strip()
                if content:
                    items.append(content)
        return items

    @staticmethod
    def _normalize_document_item(item: Any, index: int) -> tuple[str | None, str]:
        if isinstance(item, str):
            return item, f"doc_{index}"
        if isinstance(item, dict):
            content = item.get("content") or item.get("text") or item.get("document")
            doc_id = item.get("doc_id") or item.get("id") or f"doc_{index}"
            return (str(content) if isinstance(content, str) else None, str(doc_id))
        return None, f"doc_{index}"

    async def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """평가 실행.

        Args:
            request: 평가 실행 요청
            on_progress: 진행률 콜백 함수

        Returns:
            평가 실행 결과
        """
        if self._evaluator is None:
            raise RuntimeError("Evaluator not configured")
        evaluator = self._evaluator

        # LLM Adapter Resolution
        resolved_llm = self._get_llm_for_model(request.model_name)
        if resolved_llm is None:
            if self._llm_adapter is None:
                raise RuntimeError("LLM adapter not configured")
            resolved_llm = self._llm_adapter
            logger.warning(f"Using default LLM adapter instead of requested {request.model_name}")

        # 1. 데이터셋 로드 (비동기 처리)
        logger.info(f"Loading dataset from: {request.dataset_path}")

        try:
            if self._data_loader is not None:
                # 주입된 data_loader 사용
                loader = self._data_loader
            else:
                from evalvault.adapters.outbound.dataset import get_loader

                loader = get_loader(request.dataset_path)
            # 파일 I/O는 스레드 풀에서 실행
            dataset = await asyncio.to_thread(loader.load, request.dataset_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load dataset: {e}")

        requested_domain = (request.memory_config or {}).get("domain")
        if requested_domain:
            dataset.metadata["domain"] = requested_domain

        settings = self._settings or Settings()
        try:
            trackers = self._get_trackers(settings, request.tracker_config)
        except RuntimeError as exc:
            raise RuntimeError(f"Tracker configuration error: {exc}") from exc
        tracker_providers = [provider for provider, _ in trackers]
        stage_store = bool(request.stage_store)

        retriever_instance = None
        retriever_doc_ids: list[str] | None = None
        retriever_top_k = 5
        retriever_mode = None
        retriever_docs_path = None
        if request.retriever_config:
            try:
                (
                    retriever_instance,
                    retriever_doc_ids,
                    retriever_top_k,
                    retriever_mode,
                    retriever_docs_path,
                ) = self._build_retriever(request.retriever_config, settings)
            except Exception as exc:
                logger.warning("Failed to initialize retriever: %s", exc)
                raise

        memory_config = request.memory_config or {}
        memory_enabled = bool(memory_config.get("enabled"))
        memory_domain = memory_config.get("domain") or dataset.metadata.get("domain") or "default"
        memory_language = memory_config.get("language") or "ko"
        memory_augment = bool(memory_config.get("augment_context"))
        if memory_config.get("db_path"):
            memory_db_path = memory_config.get("db_path")
        elif settings.db_backend == "sqlite":
            memory_db_path = settings.evalvault_memory_db_path
        else:
            memory_db_path = None
        memory_evaluator = None
        requested_thresholds = request.thresholds or {}
        if request.threshold_profile or requested_thresholds:
            base_thresholds = dict(dataset.thresholds or {})
            if requested_thresholds:
                base_thresholds.update(requested_thresholds)
            resolved_thresholds = {
                metric: base_thresholds.get(metric, 0.7) for metric in request.metrics
            }
            if request.threshold_profile:
                resolved_thresholds = apply_threshold_profile(
                    request.metrics,
                    resolved_thresholds,
                    request.threshold_profile,
                )
        else:
            resolved_thresholds = request.thresholds or {}

        memory_active = False
        if memory_enabled:
            try:
                from evalvault.adapters.outbound.domain_memory import build_domain_memory_adapter
                from evalvault.adapters.outbound.tracer.phoenix_tracer_adapter import (
                    PhoenixTracerAdapter,
                )
                from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator

                tracer = PhoenixTracerAdapter() if "phoenix" in tracker_providers else None
                memory_adapter = build_domain_memory_adapter(
                    settings=self._settings,
                    db_path=Path(memory_db_path) if memory_db_path else None,
                )
                memory_evaluator = MemoryAwareEvaluator(
                    evaluator=self._evaluator,
                    memory_port=memory_adapter,
                    tracer=tracer,
                )
                memory_active = True
                if memory_augment:
                    for test_case in dataset.test_cases:
                        augmented = memory_evaluator.augment_context_with_facts(
                            question=test_case.question,
                            original_context="",
                            domain=memory_domain,
                            language=memory_language,
                        ).strip()
                        if augmented and augmented not in test_case.contexts:
                            test_case.contexts.append(augmented)
            except Exception as exc:
                logger.warning("Domain memory setup failed: %s", exc)
                memory_evaluator = None

        prompt_inputs: list[PromptInput] = []
        if request.system_prompt:
            prompt_inputs.append(
                PromptInput(
                    content=request.system_prompt,
                    name=request.system_prompt_name or "system_prompt",
                    kind="system",
                    role="system",
                    source="api",
                )
            )
        if request.ragas_prompt_overrides:
            for metric_name, prompt_text in request.ragas_prompt_overrides.items():
                if not isinstance(prompt_text, str):
                    continue
                prompt_inputs.append(
                    PromptInput(
                        content=prompt_text,
                        name=f"ragas.{metric_name}",
                        kind="ragas",
                        role=str(metric_name),
                        source="api",
                    )
                )

        # 2. 진행률 초기화
        start_time = time.monotonic()
        if on_progress:
            on_progress(
                EvalProgress(
                    current=0,
                    total=len(dataset.test_cases),
                    current_metric="",
                    percent=0.0,
                    status="running",
                    elapsed_seconds=0.0,
                    eta_seconds=None,
                    rate=None,
                )
            )

        # 3. 평가 실행
        logger.info(f"Starting evaluation with metrics: {request.metrics}")

        def adaptor_progress(current: int, total: int, message: str):
            if on_progress:
                elapsed = time.monotonic() - start_time
                rate = (current / elapsed) if current > 0 and elapsed > 0 else None
                eta = None
                if rate and total > 0:
                    remaining = max(total - current, 0)
                    eta = remaining / rate if rate > 0 else None
                on_progress(
                    EvalProgress(
                        current=current,
                        total=total,
                        current_metric=message,
                        percent=round((current / total) * 100, 1) if total > 0 else 0,
                        status="running",
                        elapsed_seconds=elapsed,
                        eta_seconds=eta,
                        rate=rate,
                    )
                )

        try:
            if memory_evaluator and memory_active:
                result = await memory_evaluator.evaluate_with_memory(
                    dataset=dataset,
                    metrics=request.metrics,
                    llm=resolved_llm,
                    thresholds=resolved_thresholds,
                    parallel=request.parallel,
                    batch_size=request.batch_size,
                    domain=memory_domain,
                    language=memory_language,
                    retriever=retriever_instance,
                    retriever_top_k=retriever_top_k,
                    retriever_doc_ids=retriever_doc_ids,
                    prompt_overrides=request.ragas_prompt_overrides,
                    on_progress=adaptor_progress,
                )
            else:
                result = await evaluator.evaluate(
                    dataset=dataset,
                    metrics=request.metrics,
                    llm=resolved_llm,
                    thresholds=resolved_thresholds,
                    parallel=request.parallel,
                    batch_size=request.batch_size,
                    retriever=retriever_instance,
                    retriever_top_k=retriever_top_k,
                    retriever_doc_ids=retriever_doc_ids,
                    prompt_overrides=request.ragas_prompt_overrides,
                    on_progress=adaptor_progress,
                )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            if on_progress:
                on_progress(EvalProgress(0, 0, "", 0.0, "failed", str(e)))
            raise e

        tracker_meta = result.tracker_metadata or {}
        result.tracker_metadata = tracker_meta
        ragas_snapshots = tracker_meta.get("ragas_prompt_snapshots")
        ragas_snapshot_inputs = build_prompt_inputs_from_snapshots(
            ragas_snapshots if isinstance(ragas_snapshots, dict) else None,
            kind="ragas",
            source="ragas",
        )
        custom_snapshots = tracker_meta.get("custom_prompt_snapshots")
        custom_snapshot_inputs = build_prompt_inputs_from_snapshots(
            custom_snapshots if isinstance(custom_snapshots, dict) else None,
            kind="custom",
            source="custom_rules",
        )
        override_status: dict[str, str] = {}
        raw_override = tracker_meta.get("ragas_prompt_overrides")
        if isinstance(raw_override, dict):
            override_status = cast(dict[str, str], raw_override)
        if override_status:
            prompt_inputs = [
                entry
                for entry in prompt_inputs
                if not (
                    entry.kind == "ragas"
                    and override_status.get(entry.role) is not None
                    and override_status.get(entry.role) != "applied"
                )
            ]

        if ragas_snapshot_inputs:
            existing_roles = {entry.role for entry in prompt_inputs if entry.kind == "ragas"}
            for entry in ragas_snapshot_inputs:
                if entry.role in existing_roles and override_status.get(entry.role) == "applied":
                    continue
                prompt_inputs.append(entry)
        if custom_snapshot_inputs:
            existing_roles = {entry.role for entry in prompt_inputs if entry.kind == "custom"}
            for entry in custom_snapshot_inputs:
                if entry.role in existing_roles:
                    continue
                prompt_inputs.append(entry)

        prompt_bundle = None
        if prompt_inputs:
            prompt_bundle = build_prompt_bundle(
                run_id=result.run_id,
                prompt_set_name=request.prompt_set_name,
                prompt_set_description=request.prompt_set_description,
                prompt_inputs=prompt_inputs,
                metadata={
                    "run_id": result.run_id,
                    "dataset": result.dataset_name,
                    "model": result.model_name,
                    "metrics": request.metrics,
                },
            )
            if prompt_bundle:
                result.tracker_metadata["prompt_set"] = build_prompt_summary(prompt_bundle)

        result.tracker_metadata.setdefault("run_mode", "web")
        if request.evaluation_task:
            result.tracker_metadata.setdefault("evaluation_task", request.evaluation_task)
        if request.project_name:
            result.tracker_metadata["project"] = request.project_name
        if request.prompt_config:
            result.tracker_metadata["prompt_config"] = request.prompt_config
        if retriever_instance:
            result.tracker_metadata["retriever"] = {
                "mode": retriever_mode,
                "docs_path": retriever_docs_path,
                "top_k": retriever_top_k,
            }
        if memory_enabled:
            result.tracker_metadata["domain_memory"] = {
                "enabled": memory_active,
                "domain": memory_domain,
                "language": memory_language,
                "augment_context": memory_augment,
            }
        if request.threshold_profile:
            result.tracker_metadata["threshold_profile"] = (
                str(request.threshold_profile).strip().lower()
            )

        if trackers:
            result.tracker_metadata.setdefault("tracker_providers", tracker_providers)
            for provider, tracker in trackers:
                try:
                    trace_id = tracker.log_evaluation_run(result)
                    provider_meta = result.tracker_metadata.setdefault(provider, {})
                    if isinstance(provider_meta, dict):
                        provider_meta.setdefault("trace_id", trace_id)
                    if provider == "phoenix":
                        endpoint = settings.phoenix_endpoint or "http://localhost:6006/v1/traces"
                        phoenix_meta = result.tracker_metadata.setdefault("phoenix", {})
                        phoenix_meta.update(
                            {
                                "trace_id": trace_id,
                                "endpoint": endpoint,
                                "trace_url": self._build_phoenix_trace_url(endpoint, trace_id),
                                "schema_version": 2,
                            }
                        )
                except Exception as exc:
                    raise RuntimeError(f"Tracker logging failed for {provider}: {exc}") from exc

        if stage_store and self._storage and hasattr(self._storage, "save_stage_events"):
            try:
                prompt_metadata_entries = self._build_prompt_metadata_entries(prompt_bundle)
                stage_event_builder = StageEventBuilder()
                stage_events = stage_event_builder.build_for_run(
                    result,
                    prompt_metadata=prompt_metadata_entries or None,
                    retrieval_metadata=None,
                )
                stored_events = self._storage.save_stage_events(stage_events)
                logger.info("Stored %d stage event(s) for run %s", stored_events, result.run_id)

                if stage_events and hasattr(self._storage, "save_stage_metrics"):
                    stage_metrics = StageMetricService().build_metrics(stage_events)
                    stored_metrics = self._storage.save_stage_metrics(stage_metrics)
                    logger.info(
                        "Stored %d stage metric(s) for run %s",
                        stored_metrics,
                        result.run_id,
                    )
            except Exception as exc:
                logger.warning("Stage event storage failed: %s", exc)

        # 4. 완료 진행률 콜백
        if on_progress:
            elapsed = time.monotonic() - start_time
            rate = (len(dataset.test_cases) / elapsed) if elapsed > 0 else None
            on_progress(
                EvalProgress(
                    current=len(dataset.test_cases),
                    total=len(dataset.test_cases),
                    current_metric="all",
                    percent=100.0,
                    status="completed",
                    elapsed_seconds=elapsed,
                    eta_seconds=0.0,
                    rate=rate,
                )
            )

        # 5. 결과 저장
        if self._storage:
            logger.info(f"Saving evaluation run: {result.run_id}")
            if prompt_bundle:
                self._storage.save_prompt_set(prompt_bundle)
            self._storage.save_run(result)
            if prompt_bundle:
                self._storage.link_prompt_set_to_run(
                    result.run_id,
                    prompt_bundle.prompt_set.prompt_set_id,
                )
            try:
                export_settings = self._settings or Settings()
                export_base = Path(export_settings.evalvault_db_path)
                excel_path = export_base.parent / f"evalvault_run_{result.run_id}.xlsx"
                if hasattr(self._storage, "export_run_to_excel"):
                    self._storage.export_run_to_excel(result.run_id, excel_path)
            except Exception as exc:
                logger.warning("Excel export failed for run %s: %s", result.run_id, exc)
            try:
                self._auto_generate_cluster_map(result, resolved_llm)
            except Exception as exc:
                logger.warning("Cluster map auto-generation failed: %s", exc)

        return result

    def _auto_generate_cluster_map(
        self,
        run: EvaluationRun,
        llm_adapter: LLMPort | None,
    ) -> None:
        if self._storage is None:
            return
        settings = self._settings or Settings()
        if not settings.cluster_map_auto_enabled:
            return

        mode = (settings.cluster_map_embedding_mode or "tfidf").strip().lower()
        if mode not in {"model", "tfidf"}:
            mode = "tfidf"

        result = build_cluster_map(
            run,
            llm_adapter=llm_adapter,
            embedding_mode=mode,  # type: ignore[arg-type]
            min_cluster_size=settings.cluster_map_min_cluster_size,
            max_clusters=settings.cluster_map_max_clusters,
            text_max_chars=settings.cluster_map_text_max_chars,
        )
        if result is None or not result.mapping:
            return

        map_id = self._storage.save_run_cluster_map(
            run.run_id,
            result.mapping,
            source=result.source,
            metadata=result.metadata,
        )
        logger.info(
            "Saved cluster map %s for run %s (%s items)",
            map_id,
            run.run_id,
            len(result.mapping),
        )

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        filters: RunFilters | None = None,
    ) -> list[RunSummary]:
        """평가 목록 조회.

        Args:
            limit: 최대 조회 개수
            filters: 필터 조건

        Returns:
            평가 요약 목록
        """
        if self._storage is None:
            logger.warning("Storage not configured, returning empty list")
            return []

        resolver = self._get_phoenix_resolver()

        try:
            # 저장소에서 평가 목록 조회
            runs = self._storage.list_runs(limit=limit, offset=offset)

            # RunSummary로 변환
            summaries = []
            for run in runs:
                prompt_entries = extract_prompt_entries(getattr(run, "tracker_metadata", None))
                metadata = getattr(run, "tracker_metadata", {}) or {}
                project_name = metadata.get("project") or metadata.get("project_name")
                if isinstance(project_name, str):
                    project_name = project_name.strip() or None
                else:
                    project_name = None
                evaluation_task = metadata.get("evaluation_task")
                threshold_profile = metadata.get("threshold_profile")
                if not isinstance(threshold_profile, str) or not threshold_profile:
                    threshold_profile = None
                avg_metric_scores = {}
                for metric_name in run.metrics_evaluated:
                    avg_score = run.get_avg_score(metric_name)
                    if avg_score is not None:
                        avg_metric_scores[metric_name] = avg_score
                summary = RunSummary(
                    run_id=run.run_id,
                    dataset_name=run.dataset_name,
                    model_name=run.model_name,
                    pass_rate=run.pass_rate,
                    total_test_cases=run.total_test_cases,
                    passed_test_cases=run.passed_test_cases,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    metrics_evaluated=run.metrics_evaluated,
                    run_mode=metadata.get("run_mode"),
                    evaluation_task=evaluation_task if isinstance(evaluation_task, str) else None,
                    threshold_profile=threshold_profile,
                    total_tokens=run.total_tokens,
                    total_cost_usd=run.total_cost_usd,
                    phoenix_prompts=prompt_entries,
                    project_name=project_name,
                    avg_metric_scores=avg_metric_scores,
                )

                if resolver and resolver.can_resolve(getattr(run, "tracker_metadata", None)):
                    stats = resolver.get_stats(getattr(run, "tracker_metadata", None))
                    if stats:
                        summary.phoenix_precision = stats.precision_at_k
                        summary.phoenix_drift = stats.drift_score
                        summary.phoenix_experiment_url = stats.experiment_url
                        summary.phoenix_dataset_url = stats.dataset_url

                # 필터 적용
                if filters:
                    if filters.dataset_name and filters.dataset_name != summary.dataset_name:
                        continue
                    if filters.model_name and filters.model_name != summary.model_name:
                        continue
                    if filters.date_from and summary.started_at < filters.date_from:
                        continue
                    if filters.date_to and summary.started_at > filters.date_to:
                        continue
                    if filters.min_pass_rate and summary.pass_rate < filters.min_pass_rate:
                        continue
                    if filters.max_pass_rate and summary.pass_rate > filters.max_pass_rate:
                        continue
                    if filters.run_mode and (
                        not summary.run_mode or summary.run_mode.lower() != filters.run_mode.lower()
                    ):
                        continue
                    if filters.project_names:
                        allowed = {name.strip() for name in filters.project_names if name.strip()}
                        if summary.project_name not in allowed:
                            continue

                summaries.append(summary)

            return summaries

        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []

    def get_run_details(self, run_id: str) -> EvaluationRun:
        """평가 상세 조회.

        Args:
            run_id: 평가 ID

        Returns:
            평가 상세 정보

        Raises:
            KeyError: 평가를 찾을 수 없는 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        prompt_bundle = self._storage.get_prompt_set_for_run(run_id)
        if prompt_bundle:
            metadata = getattr(run, "tracker_metadata", {}) or {}
            metadata["prompt_set_detail"] = prompt_bundle.to_dict()
            run.tracker_metadata = metadata

        return run

    def get_visual_space(self, query: VisualSpaceQuery) -> dict[str, Any]:
        """시각화 좌표 데이터 생성."""
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        service = VisualSpaceService(
            storage=self._storage,
            phoenix_resolver=self._get_phoenix_resolver(),
        )
        return service.build(query)

    def get_run_cluster_map(self, run_id: str, map_id: str | None = None) -> RunClusterMap | None:
        """런별 클러스터 맵 조회."""
        if self._storage is None or not hasattr(self._storage, "get_run_cluster_map"):
            raise RuntimeError("Storage not configured")
        return self._storage.get_run_cluster_map(run_id, map_id)

    def save_run_cluster_map(
        self,
        run_id: str,
        mapping: dict[str, str],
        source: str | None = None,
        map_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """런별 클러스터 맵 저장."""
        if self._storage is None or not hasattr(self._storage, "save_run_cluster_map"):
            raise RuntimeError("Storage not configured")
        return self._storage.save_run_cluster_map(
            run_id, mapping, source, map_id, metadata=metadata
        )

    def list_run_cluster_maps(self, run_id: str) -> list[RunClusterMapInfo]:
        """런별 클러스터 맵 버전 조회."""
        if self._storage is None or not hasattr(self._storage, "list_run_cluster_maps"):
            raise RuntimeError("Storage not configured")
        return self._storage.list_run_cluster_maps(run_id)

    def delete_run_cluster_map(self, run_id: str, map_id: str) -> int:
        """런별 클러스터 맵 삭제."""
        if self._storage is None or not hasattr(self._storage, "delete_run_cluster_map"):
            raise RuntimeError("Storage not configured")
        return self._storage.delete_run_cluster_map(run_id, map_id)

    def save_feedback(self, feedback: SatisfactionFeedback) -> str:
        if self._storage is None or not hasattr(self._storage, "save_feedback"):
            raise RuntimeError("Storage not configured")
        return self._storage.save_feedback(feedback)

    def list_feedback(self, run_id: str) -> list[SatisfactionFeedback]:
        if self._storage is None or not hasattr(self._storage, "list_feedback"):
            raise RuntimeError("Storage not configured")
        return self._storage.list_feedback(run_id)

    def get_feedback_summary(self, run_id: str) -> FeedbackSummary:
        if self._storage is None or not hasattr(self._storage, "get_feedback_summary"):
            raise RuntimeError("Storage not configured")
        return self._storage.get_feedback_summary(run_id)

    def build_calibration(self, run_id: str, *, model: str = "both") -> CalibrationResult:
        run = self.get_run_details(run_id)
        feedbacks = self.list_feedback(run_id)
        service = SatisfactionCalibrationService()
        return service.build_calibration(run, feedbacks, model=model)

    def run_judge_calibration(
        self,
        *,
        run_id: str,
        labels_source: str,
        method: str,
        metrics: list[str],
        holdout_ratio: float,
        seed: int,
        parallel: bool,
        concurrency: int,
    ) -> dict[str, object]:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        storage = self._storage
        if holdout_ratio <= 0 or holdout_ratio >= 1:
            raise ValueError("holdout_ratio must be between 0 and 1")
        if seed < 0:
            raise ValueError("seed must be >= 0")
        if concurrency <= 0:
            raise ValueError("concurrency must be >= 1")

        run = self.get_run_details(run_id)
        feedbacks = storage.list_feedback(run_id)
        if labels_source in {"feedback", "hybrid"} and not feedbacks:
            raise ValueError(
                f"No feedback labels found for run '{run_id}'. "
                f"Calibration with labels_source='{labels_source}' requires at least one feedback label. "
                "Please add feedback labels via the UI or API, or use labels_source='gold' if gold labels are available."
            )
        resolved_metrics = metrics or list(run.metrics_evaluated)
        if not resolved_metrics:
            raise ValueError("No metrics available for calibration")

        started_at = datetime.now(UTC)
        service = JudgeCalibrationService()
        result = service.calibrate(
            run,
            feedbacks,
            labels_source=labels_source,
            method=method,
            metrics=resolved_metrics,
            holdout_ratio=holdout_ratio,
            seed=seed,
            parallel=parallel,
            concurrency=concurrency,
        )
        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        reporter = JudgeCalibrationReporter()
        timestamp = started_at.strftime("%Y%m%d_%H%M%S")
        calibration_id = f"judge_calibration_{run_id}_{timestamp}"
        base_dir = Path("reports/calibration")
        output_path = base_dir / f"{calibration_id}.json"
        artifacts_dir = base_dir / "artifacts" / calibration_id
        output_path.parent.mkdir(parents=True, exist_ok=True)
        artifacts_index = reporter.write_artifacts(result=result, artifacts_dir=artifacts_dir)

        rendered = reporter.render_json(result)

        status = "ok" if result.summary.gate_passed else "degraded"
        summary_payload = {
            "calibration_id": calibration_id,
            "run_id": result.summary.run_id,
            "labels_source": result.summary.labels_source,
            "method": result.summary.method,
            "metrics": list(result.summary.metrics),
            "holdout_ratio": result.summary.holdout_ratio,
            "seed": result.summary.seed,
            "total_labels": result.summary.total_labels,
            "total_samples": result.summary.total_samples,
            "gate_passed": result.summary.gate_passed,
            "gate_threshold": result.summary.gate_threshold,
            "notes": list(result.summary.notes),
            "created_at": started_at.astimezone(UTC).isoformat(),
        }
        payload = {
            "calibration_id": calibration_id,
            "status": status,
            "started_at": started_at.astimezone(UTC).isoformat(),
            "finished_at": finished_at.astimezone(UTC).isoformat(),
            "duration_ms": duration_ms,
            "artifacts": artifacts_index,
            "summary": summary_payload,
            "metrics": rendered["metrics"],
            "case_results": rendered["case_results"],
            "warnings": list(result.warnings),
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        metadata = run.tracker_metadata or {}
        history = metadata.get("judge_calibration_history")
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "calibration_id": calibration_id,
                "run_id": run_id,
                "labels_source": summary_payload["labels_source"],
                "method": summary_payload["method"],
                "metrics": summary_payload["metrics"],
                "holdout_ratio": summary_payload["holdout_ratio"],
                "seed": summary_payload["seed"],
                "total_labels": summary_payload["total_labels"],
                "total_samples": summary_payload["total_samples"],
                "gate_passed": summary_payload["gate_passed"],
                "gate_threshold": summary_payload["gate_threshold"],
                "created_at": summary_payload["created_at"],
                "output_path": str(output_path),
                "artifacts": artifacts_index,
            }
        )
        metadata["judge_calibration_history"] = history
        storage.update_run_metadata(run_id, metadata)
        return payload

    def get_judge_calibration(self, calibration_id: str) -> dict[str, object]:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        entry = self._find_judge_calibration_entry(calibration_id)
        output_path = Path(str(entry.get("output_path") or ""))
        if not output_path.exists():
            raise KeyError(f"Calibration output not found: {calibration_id}")
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        return payload

    def list_judge_calibrations(self, *, limit: int = 20) -> list[dict[str, object]]:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        storage = self._storage
        scan_limit = max(100, limit * 5)
        runs = storage.list_runs(limit=scan_limit)
        entries: list[dict[str, object]] = []
        for run in runs:
            metadata = getattr(run, "tracker_metadata", {}) or {}
            history = metadata.get("judge_calibration_history")
            if not isinstance(history, list):
                continue
            for item in history:
                if isinstance(item, dict):
                    entries.append(
                        {
                            "calibration_id": item.get("calibration_id"),
                            "run_id": item.get("run_id"),
                            "labels_source": item.get("labels_source"),
                            "method": item.get("method"),
                            "metrics": item.get("metrics") or [],
                            "holdout_ratio": item.get("holdout_ratio"),
                            "seed": item.get("seed"),
                            "total_labels": item.get("total_labels"),
                            "total_samples": item.get("total_samples"),
                            "gate_passed": item.get("gate_passed"),
                            "gate_threshold": item.get("gate_threshold"),
                            "created_at": item.get("created_at"),
                        }
                    )

        def _sort_key(item: dict[str, object]) -> str:
            value = item.get("created_at")
            return value if isinstance(value, str) else ""

        entries.sort(key=_sort_key, reverse=True)
        return entries[:limit]

    def _find_judge_calibration_entry(self, calibration_id: str) -> dict[str, object]:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        storage = self._storage
        scan_limit = 1000
        runs = storage.list_runs(limit=scan_limit)
        for run in runs:
            metadata = getattr(run, "tracker_metadata", {}) or {}
            history = metadata.get("judge_calibration_history")
            if not isinstance(history, list):
                continue
            for item in history:
                if not isinstance(item, dict):
                    continue
                if item.get("calibration_id") == calibration_id:
                    return item
        raise KeyError(f"Calibration not found: {calibration_id}")

    def list_stage_events(self, run_id: str, *, stage_type: str | None = None) -> list[StageEvent]:
        """Stage 이벤트 목록 조회."""
        if self._storage is None or not hasattr(self._storage, "list_stage_events"):
            return []
        return self._storage.list_stage_events(run_id, stage_type=stage_type)

    def list_stage_metrics(
        self,
        run_id: str,
        *,
        stage_id: str | None = None,
        metric_name: str | None = None,
    ) -> list[StageMetric]:
        """Stage 메트릭 목록 조회 (없으면 StageEvent로 재계산)."""
        if self._storage is None or not hasattr(self._storage, "list_stage_metrics"):
            return []

        metrics = self._storage.list_stage_metrics(run_id)
        if not metrics and hasattr(self._storage, "list_stage_events"):
            events = self._storage.list_stage_events(run_id)
            if events:
                service = StageMetricService()
                metrics = service.build_metrics(events)
                if hasattr(self._storage, "save_stage_metrics"):
                    self._storage.save_stage_metrics(metrics)

        if stage_id or metric_name:
            metrics = [
                metric
                for metric in metrics
                if (stage_id is None or metric.stage_id == stage_id)
                and (metric_name is None or metric.metric_name == metric_name)
            ]
        return metrics

    def compare_prompt_sets(
        self,
        base_run_id: str,
        target_run_id: str,
        *,
        max_lines: int = 40,
        include_diff: bool = True,
    ) -> dict[str, Any]:
        if self._storage is None or not hasattr(self._storage, "get_prompt_set_for_run"):
            raise RuntimeError("Storage not configured")

        base_bundle = self._storage.get_prompt_set_for_run(base_run_id)
        target_bundle = self._storage.get_prompt_set_for_run(target_run_id)
        if not base_bundle or not target_bundle:
            raise KeyError("Prompt set not found")

        base_roles = self._prompt_bundle_role_map(base_bundle)
        target_roles = self._prompt_bundle_role_map(target_bundle)
        all_roles = sorted(set(base_roles) | set(target_roles))

        summary: list[dict[str, Any]] = []
        diffs: list[dict[str, Any]] = []

        for role in all_roles:
            base = base_roles.get(role)
            target = target_roles.get(role)
            if not base or not target:
                summary.append(
                    {
                        "role": role,
                        "base_checksum": base["checksum"] if base else None,
                        "target_checksum": target["checksum"] if target else None,
                        "status": "missing",
                        "base_name": base["name"] if base else None,
                        "target_name": target["name"] if target else None,
                        "base_kind": base["kind"] if base else None,
                        "target_kind": target["kind"] if target else None,
                    }
                )
                continue

            status = "same" if base["checksum"] == target["checksum"] else "diff"
            summary.append(
                {
                    "role": role,
                    "base_checksum": base["checksum"],
                    "target_checksum": target["checksum"],
                    "status": status,
                    "base_name": base["name"],
                    "target_name": target["name"],
                    "base_kind": base["kind"],
                    "target_kind": target["kind"],
                }
            )

            if include_diff and status == "diff":
                diff_lines = list(
                    difflib.unified_diff(
                        base["content"].splitlines(),
                        target["content"].splitlines(),
                        fromfile=f"{base_run_id[:8]}:{role}",
                        tofile=f"{target_run_id[:8]}:{role}",
                        lineterm="",
                    )
                )
                truncated = len(diff_lines) > max_lines
                diffs.append(
                    {
                        "role": role,
                        "lines": diff_lines[:max_lines],
                        "truncated": truncated,
                    }
                )

        return {
            "base_run_id": base_run_id,
            "target_run_id": target_run_id,
            "summary": summary,
            "diffs": diffs,
        }

    def _prompt_bundle_role_map(self, bundle: PromptSetBundle) -> dict[str, dict[str, str]]:
        prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
        roles: dict[str, dict[str, str]] = {}
        for item in bundle.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            roles[item.role] = {
                "checksum": prompt.checksum,
                "content": prompt.content,
                "name": prompt.name,
                "kind": prompt.kind,
            }
        return roles

    def build_debug_report(self, run_id: str) -> DebugReport:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        if not hasattr(self._storage, "list_stage_events"):
            raise RuntimeError("Stage storage not configured")

        service = DebugReportService()
        stage_storage = cast(StageStoragePort, self._storage)
        return service.build_report(
            run_id,
            storage=self._storage,
            stage_storage=stage_storage,
        )

    def generate_ops_report(
        self,
        run_id: str,
        *,
        output_format: str,
        save: bool,
    ) -> dict[str, Any] | str:
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        if not hasattr(self._storage, "list_stage_events"):
            raise RuntimeError("Stage storage not configured")

        service = OpsReportService()
        stage_storage = cast(StageStoragePort, self._storage)
        report = service.build_report(
            run_id,
            storage=self._storage,
            stage_storage=stage_storage,
        )

        content = render_markdown(report) if output_format == "markdown" else render_json(report)

        if save:
            self._storage.save_ops_report(
                report_id=None,
                run_id=run_id,
                report_type="ops_report",
                format=output_format,
                content=content,
                metadata={"source": "api"},
            )

        if output_format == "markdown":
            return content
        return report.to_dict()

    def delete_run(self, run_id: str) -> bool:
        """평가 삭제.

        Args:
            run_id: 삭제할 평가 ID

        Returns:
            삭제 성공 여부
        """
        if self._storage is None:
            return False

        try:
            return self._storage.delete_run(run_id)
        except Exception as e:
            logger.error(f"Failed to delete run {run_id}: {e}")
            return False

    def _build_analysis_bundle(
        self,
        run_id: str,
        *,
        include_nlp: bool,
        include_causal: bool,
    ) -> AnalysisBundle:
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        run = self._storage.get_run(run_id)
        if not run.results:
            raise ValueError("Run has no results to analyze")

        analysis_adapter = StatisticalAnalysisAdapter()
        cache_adapter = MemoryCacheAdapter()

        nlp_adapter = None
        if include_nlp:
            settings = self._settings or Settings()
            llm_adapter = self._llm_adapter
            if llm_adapter is None:
                from evalvault.adapters.outbound.llm import get_llm_adapter

                try:
                    llm_adapter = get_llm_adapter(settings)
                except Exception as exc:
                    logger.warning("LLM adapter initialization failed for report: %s", exc)
                    llm_adapter = None
            if llm_adapter is not None:
                nlp_adapter = NLPAnalysisAdapter(
                    llm_adapter=llm_adapter,
                    use_embeddings=True,
                )

        causal_adapter = CausalAnalysisAdapter() if include_causal else None

        service = AnalysisService(
            analysis_adapter=analysis_adapter,
            nlp_adapter=nlp_adapter,
            causal_adapter=causal_adapter,
            cache_adapter=cache_adapter,
        )
        return service.analyze_run(run, include_nlp=include_nlp, include_causal=include_causal)

    @staticmethod
    def _build_dashboard_payload(bundle: AnalysisBundle) -> dict[str, Any]:
        payload: dict[str, Any] = {"run_id": bundle.run_id}
        analysis = bundle.statistical
        if analysis is None:
            return payload

        metrics_summary: dict[str, Any] = {}
        for metric, stats in analysis.metrics_summary.items():
            metrics_summary[metric] = {
                "mean": stats.mean,
                "std": stats.std,
                "min": stats.min,
                "max": stats.max,
                "median": stats.median,
                "percentile_25": stats.percentile_25,
                "percentile_75": stats.percentile_75,
                "count": stats.count,
            }

        payload.update(
            {
                "metrics_summary": metrics_summary,
                "correlation_matrix": analysis.correlation_matrix,
                "correlation_metrics": analysis.correlation_metrics,
                "metric_pass_rates": analysis.metric_pass_rates,
                "low_performers": [asdict(item) for item in analysis.low_performers],
            }
        )
        return payload

    def _find_cached_report(
        self,
        *,
        run_id: str,
        output_format: str,
        include_nlp: bool,
        include_causal: bool,
    ) -> str | None:
        if self._storage is None:
            return None

        reports = self._storage.list_analysis_reports(
            run_id=run_id,
            report_type="analysis",
            format=output_format,
            limit=10,
        )
        for report in reports:
            metadata = report.get("metadata") or {}
            if metadata.get("include_nlp") != include_nlp:
                continue
            if metadata.get("include_causal") != include_causal:
                continue
            content = report.get("content")
            if content:
                return content
        return None

    def generate_report(
        self,
        run_id: str,
        output_format: Literal["markdown", "html"] = "markdown",
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
        use_cache: bool = True,
        save: bool = False,
    ) -> str:
        """보고서 생성.

        Args:
            run_id: 평가 ID
            output_format: 출력 포맷
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부

        Returns:
            생성된 보고서
        """
        if use_cache:
            cached = self._find_cached_report(
                run_id=run_id,
                output_format=output_format,
                include_nlp=include_nlp,
                include_causal=include_causal,
            )
            if cached is not None:
                return cached

        bundle = self._build_analysis_bundle(
            run_id,
            include_nlp=include_nlp,
            include_causal=include_causal,
        )

        report_generator = self._report_generator or MarkdownReportAdapter()
        if output_format == "html":
            if isinstance(report_generator, MarkdownReportAdapter):
                report_content = report_generator.generate_html(
                    bundle,
                    include_nlp=include_nlp,
                    include_causal=include_causal,
                )
            else:
                report_content = report_generator.generate_html(bundle, include_nlp=include_nlp)
        elif isinstance(report_generator, MarkdownReportAdapter):
            report_content = report_generator.generate_markdown(
                bundle,
                include_nlp=include_nlp,
                include_causal=include_causal,
            )
        else:
            report_content = report_generator.generate_markdown(bundle, include_nlp=include_nlp)

        if save and self._storage is not None:
            metadata = {
                "include_nlp": include_nlp,
                "include_causal": include_causal,
                "source": "api",
            }
            self._storage.save_analysis_report(
                report_id=None,
                run_id=run_id,
                experiment_id=None,
                report_type="analysis",
                format=output_format,
                content=report_content,
                metadata=metadata,
            )

        return report_content

    def build_dashboard_payload(
        self,
        run_id: str,
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
    ) -> dict[str, Any]:
        bundle = self._build_analysis_bundle(
            run_id,
            include_nlp=include_nlp,
            include_causal=include_causal,
        )
        return self._build_dashboard_payload(bundle)

    def get_available_metrics(self) -> list[str]:
        """사용 가능한 메트릭 목록 반환."""
        return list_metric_names()

    def get_metric_specs(self) -> list[dict[str, object]]:
        """메트릭 스펙 목록 반환."""
        return [spec.to_dict() for spec in list_metric_specs()]

    def get_metric_descriptions(self) -> dict[str, str]:
        """메트릭별 설명 반환."""
        return registry_metric_descriptions()

    def create_dataset_from_upload(
        self,
        filename: str,
        content: bytes,
    ):
        """업로드된 파일에서 Dataset 생성.

        Args:
            filename: 원본 파일명 (확장자로 형식 판단)
            content: 파일 내용 (bytes)

        Returns:
            Dataset 인스턴스

        Raises:
            ValueError: 지원하지 않는 파일 형식인 경우
        """
        import csv
        import io
        import json
        import tempfile

        from evalvault.domain.entities import Dataset, TestCase

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "json":
            # JSON 파일 파싱
            text = content.decode("utf-8")
            data = json.loads(text)

            test_cases = []
            for idx, tc_data in enumerate(data.get("test_cases", [])):
                test_cases.append(
                    TestCase(
                        id=str(tc_data.get("id", f"tc-{idx + 1:03d}")),
                        question=tc_data["question"],
                        answer=tc_data["answer"],
                        contexts=tc_data.get("contexts", []),
                        ground_truth=tc_data.get("ground_truth"),
                    )
                )

            return Dataset(
                name=data.get("name", Path(filename).stem),
                version=data.get("version", "1.0.0"),
                test_cases=test_cases,
                thresholds=data.get("thresholds", {}),
            )

        elif ext == "csv":
            # CSV 파일 파싱
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))

            test_cases = []
            for idx, row in enumerate(reader):
                # contexts 파싱 (JSON 배열 또는 | 구분)
                contexts_raw = row.get("contexts", "[]")
                if contexts_raw.startswith("["):
                    contexts = json.loads(contexts_raw)
                else:
                    contexts = [c.strip() for c in contexts_raw.split("|") if c.strip()]

                test_cases.append(
                    TestCase(
                        id=row.get("id", f"tc-{idx + 1:03d}"),
                        question=row["question"],
                        answer=row["answer"],
                        contexts=contexts,
                        ground_truth=row.get("ground_truth"),
                    )
                )

            return Dataset(
                name=Path(filename).stem,
                version="1.0.0",
                test_cases=test_cases,
            )

        elif ext in ("xlsx", "xls"):
            # Excel 파일은 임시 파일로 저장 후 기존 loader 사용
            from evalvault.adapters.outbound.dataset import get_loader

            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            try:
                loader = get_loader(tmp_path)
                return loader.load(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    def run_evaluation_with_dataset(
        self,
        dataset,
        metrics: list[str],
        thresholds: dict[str, float] | None = None,
        *,
        parallel: bool = True,
        batch_size: int = 5,
        on_progress: Callable[[EvalProgress], None] | None = None,
        run_mode: str | None = None,
        project_name: str | None = None,
    ) -> EvaluationRun:
        """데이터셋 객체로 직접 평가 실행.

        Args:
            dataset: 평가할 Dataset 객체
            metrics: 평가 메트릭 목록
            thresholds: 메트릭별 임계값 (선택)
            parallel: 병렬 처리 여부 (기본값: True)
            batch_size: 병렬 처리 배치 크기 (기본값: 5)
            on_progress: 진행 상황 콜백 (선택)

        Returns:
            EvaluationRun 결과

        Raises:
            RuntimeError: evaluator 또는 llm_adapter가 설정되지 않은 경우
        """
        if self._evaluator is None:
            raise RuntimeError("Evaluator not configured")
        if self._llm_adapter is None:
            raise RuntimeError("LLM adapter not configured. .env에 OPENAI_API_KEY를 설정하세요.")
        evaluator = self._evaluator
        llm_adapter = self._llm_adapter

        # 진행률 초기화
        if on_progress:
            on_progress(
                EvalProgress(
                    current=0,
                    total=len(dataset.test_cases),
                    current_metric="",
                    percent=0.0,
                    status="running",
                )
            )

        # 평가 실행 (비동기 -> 동기 변환)
        mode = "병렬" if parallel else "순차"
        logger.info(f"Starting evaluation ({mode}) with metrics: {metrics}")

        async def run_async_evaluation():
            return await evaluator.evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=llm_adapter,
                thresholds=thresholds or {},
                parallel=parallel,
                batch_size=batch_size,
            )

        result = asyncio.run(run_async_evaluation())

        # 완료 진행률 콜백
        if on_progress:
            on_progress(
                EvalProgress(
                    current=result.total_test_cases,
                    total=result.total_test_cases,
                    current_metric="",
                    percent=100.0,
                    status="completed",
                )
            )

        metadata = getattr(result, "tracker_metadata", None) or {}
        metadata.setdefault("run_mode", (run_mode or "full"))
        if project_name:
            metadata["project"] = project_name
        result.tracker_metadata = metadata

        # 결과 저장
        if self._storage:
            logger.info(f"Saving evaluation run: {result.run_id}")
            self._storage.save_run(result)

        return result

    def get_improvement_guide(
        self,
        run_id: str,
        *,
        include_llm: bool = False,
        metrics: list[str] | None = None,
        model_id: str | None = None,
    ) -> ImprovementReport:
        """개선 가이드 생성.

        평가 결과를 분석하여 RAG 시스템 개선 가이드를 생성합니다.

        Args:
            run_id: 분석할 평가 실행 ID
            include_llm: LLM 기반 분석 포함 여부
            metrics: 분석할 메트릭 (None이면 모두)
            model_id: 사용할 모델 ID (None이면 기본 모델)

        Returns:
            ImprovementReport 개선 가이드 리포트

        Raises:
            KeyError: 평가 결과를 찾을 수 없는 경우
            RuntimeError: 저장소가 설정되지 않은 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        # 평가 결과 조회
        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        stage_metrics = None
        if hasattr(self._storage, "list_stage_metrics"):
            stage_metrics = self._storage.list_stage_metrics(run_id)

        # 개선 가이드 서비스 초기화
        from evalvault.adapters.outbound.improvement.insight_generator import (
            InsightGenerator,
        )
        from evalvault.adapters.outbound.improvement.pattern_detector import (
            PatternDetector,
        )
        from evalvault.adapters.outbound.improvement.playbook_loader import (
            PlaybookLoader,
        )
        from evalvault.adapters.outbound.improvement.stage_metric_playbook_loader import (
            StageMetricPlaybookLoader,
        )
        from evalvault.domain.services.improvement_guide_service import (
            ImprovementGuideService,
        )

        # 기본 플레이북 로드
        playbook_path = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "playbooks"
            / "improvement_playbook.yaml"
        )
        playbook = None
        if playbook_path.exists():
            loader = PlaybookLoader(playbook_path)
            playbook = loader.load()

        # 패턴 탐지기 초기화
        detector = PatternDetector(playbook=playbook)

        # 인사이트 생성기 초기화 (LLM 사용 시)
        generator = None
        if include_llm:
            llm_adapter = self._get_llm_for_model(model_id)
            if llm_adapter:
                generator = InsightGenerator(llm_adapter=llm_adapter)

        # 서비스 초기화 및 리포트 생성
        # max_llm_samples=2로 설정하여 LLM 호출 수 감소 (속도 개선)
        stage_metric_playbook = StageMetricPlaybookLoader().load()

        service = ImprovementGuideService(
            pattern_detector=detector,
            insight_generator=generator,
            playbook=playbook,
            stage_metric_playbook=stage_metric_playbook,
            enable_llm_enrichment=include_llm,
            max_llm_samples=2,
        )

        return service.generate_report(
            run,
            metrics=metrics,
            include_llm_analysis=include_llm,
            stage_metrics=stage_metrics,
        )

    def check_quality_gate(
        self,
        run_id: str,
        thresholds: dict[str, float] | None = None,
    ) -> GateReport:
        """품질 게이트 체크.

        평가 결과가 설정된 임계값을 통과하는지 확인합니다.

        Args:
            run_id: 체크할 평가 실행 ID
            thresholds: 커스텀 임계값 (None이면 평가 시 설정된 임계값 사용)

        Returns:
            GateReport 품질 게이트 결과

        Raises:
            KeyError: 평가 결과를 찾을 수 없는 경우
            RuntimeError: 저장소가 설정되지 않은 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        # 평가 결과 조회
        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        # 임계값 결정 (커스텀 > 평가 시 설정값)
        effective_thresholds = thresholds or run.thresholds or {}

        # 각 메트릭에 대해 게이트 체크
        results: list[GateResult] = []
        for metric in run.metrics_evaluated:
            score = run.get_avg_score(metric)
            if score is None:
                score = 0.0

            threshold = effective_thresholds.get(metric, 0.7)
            passed = score >= threshold
            gap = threshold - score

            results.append(
                GateResult(
                    metric=metric,
                    score=score,
                    threshold=threshold,
                    passed=passed,
                    gap=gap,
                )
            )

        # 전체 통과 여부 계산
        overall_passed = all(r.passed for r in results)

        return GateReport(
            run_id=run_id,
            results=results,
            overall_passed=overall_passed,
        )

    def generate_llm_report(
        self,
        run_id: str,
        *,
        metrics_to_analyze: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
        model_id: str | None = None,
        language: str | None = None,
    ):
        """LLM 기반 지능형 보고서 생성.

        전문가 수준의 분석, 최신 연구 기반 권장사항,
        구체적인 액션 아이템을 포함한 보고서를 생성합니다.

        Args:
            run_id: 분석할 평가 실행 ID
            metrics_to_analyze: 분석할 메트릭 (None이면 모두)
            thresholds: 메트릭별 임계값
            model_id: 사용할 모델 ID (None이면 기본 모델)

        Returns:
            LLMReport 인스턴스

        Raises:
            KeyError: 평가 결과를 찾을 수 없는 경우
            RuntimeError: LLM 또는 저장소가 설정되지 않은 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        # Get LLM adapter (default or model-specific)
        llm_adapter = self._get_llm_for_model(model_id)
        if llm_adapter is None:
            raise RuntimeError("LLM adapter not configured. .env에 OPENAI_API_KEY를 설정하세요.")

        # 평가 결과 조회
        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        # LLM 보고서 생성기 초기화
        from evalvault.adapters.outbound.report import LLMReportGenerator

        generator = LLMReportGenerator(
            llm_adapter=llm_adapter,
            include_research_insights=True,
            include_action_items=True,
            language=language or "ko",
        )

        # 동기 방식으로 보고서 생성
        return generator.generate_report_sync(
            run,
            metrics_to_analyze=metrics_to_analyze,
            thresholds=thresholds or run.thresholds,
        )

    def list_datasets(self) -> list[dict[str, str | int]]:
        """사용 가능한 데이터셋 목록 조회."""
        datasets = []
        data_dirs = ["data/datasets", "data/inputs", "."]

        for dir_path in data_dirs:
            path = Path(dir_path)
            if not path.exists():
                continue

            for file in path.iterdir():
                if file.suffix.lower() in [".json", ".csv", ".xlsx", ".xls"]:
                    datasets.append(
                        {
                            "name": file.name,
                            "path": str(file.absolute()),
                            "type": file.suffix[1:],
                            "size": file.stat().st_size,
                        }
                    )
        return datasets

    def save_dataset_file(self, filename: str, content: bytes) -> str:
        """데이터셋 파일 저장.

        Args:
            filename: 파일명
            content: 파일 내용

        Returns:
            저장된 파일 경로
        """
        save_dir = Path("data/datasets")
        save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / filename
        file_path.write_bytes(content)

        return str(file_path.absolute())

    def save_retriever_docs_file(self, filename: str, content: bytes) -> str:
        """리트리버 문서 파일 저장.

        Args:
            filename: 파일명
            content: 파일 내용

        Returns:
            저장된 파일 경로
        """
        save_dir = Path("data/retriever_docs")
        save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / filename
        file_path.write_bytes(content)

        return str(file_path.absolute())

    def list_models(self, provider: str | None = None) -> list[dict[str, str | bool]]:
        """사용 가능한 모델 목록 조회."""
        settings = self._settings or Settings()
        provider_key = provider.lower() if provider else None

        if provider_key == "openai":
            return self._list_openai_models()
        if provider_key == "ollama":
            return self._list_ollama_models(settings)
        if provider_key == "vllm":
            return self._list_vllm_models(settings)
        if provider_key:
            return self._list_other_models(provider_key)

        models: list[dict[str, str | bool]] = []
        models.extend(self._list_ollama_models(settings))
        models.extend(self._list_openai_models())
        models.extend(self._list_vllm_models(settings))
        models.extend(self._list_other_models())
        return models

    @staticmethod
    def _is_embedding_model(model_name: str) -> bool:
        markers = ("embedding", "embed", "bge", "e5", "gte", "instructor")
        lowered = model_name.lower()
        return any(marker in lowered for marker in markers)

    def _list_openai_models(self) -> list[dict[str, str | bool]]:
        return [
            {"id": "openai/gpt-5-mini", "name": "OpenAI gpt-5-mini", "supports_tools": True},
            {"id": "openai/gpt-5.1", "name": "OpenAI gpt-5.1", "supports_tools": True},
            {"id": "openai/gpt-5.2", "name": "OpenAI gpt-5.2", "supports_tools": True},
            {"id": "openai/gpt-5-nano", "name": "OpenAI gpt-5-nano", "supports_tools": True},
        ]

    def _list_vllm_models(self, settings: Settings) -> list[dict[str, str | bool]]:
        model_name = settings.vllm_model
        if not model_name:
            return []
        return [
            {
                "id": f"vllm/{model_name}",
                "name": f"vLLM {model_name}",
                "supports_tools": False,
            }
        ]

    def _list_ollama_models(self, settings: Settings) -> list[dict[str, str | bool]]:
        allowlist = self._get_ollama_tool_allowlist(settings)
        models = self._fetch_ollama_models(settings, allowlist)
        if models:
            return models

        fallback = settings.ollama_model
        if fallback and not self._is_embedding_model(fallback):
            return [
                {
                    "id": f"ollama/{fallback}",
                    "name": fallback,
                    "supports_tools": self._matches_tool_allowlist(fallback, allowlist),
                }
            ]
        return []

    def _fetch_ollama_models(
        self,
        settings: Settings,
        allowlist: set[str],
    ) -> list[dict[str, str | bool]]:
        base_url = settings.ollama_base_url.rstrip("/")
        url = f"{base_url}/api/tags"

        try:
            with urlopen(url, timeout=settings.ollama_timeout) as response:
                payload = json.load(response)
        except Exception as exc:
            logger.warning("Failed to fetch Ollama models: %s", exc)
            return []

        items = payload.get("models", [])
        names = []
        for item in items:
            name = item.get("name")
            if not name or self._is_embedding_model(name):
                continue
            names.append(name)

        unique_names = sorted(set(names))
        return [
            {
                "id": f"ollama/{name}",
                "name": name,
                "supports_tools": self._matches_tool_allowlist(name, allowlist),
            }
            for name in unique_names
        ]

    @staticmethod
    def _get_ollama_tool_allowlist(settings: Settings) -> set[str]:
        raw = settings.ollama_tool_models or ""
        return {item.strip().lower() for item in raw.split(",") if item.strip()}

    @staticmethod
    def _matches_tool_allowlist(model_name: str, allowlist: set[str]) -> bool:
        if not allowlist:
            return False
        lowered = model_name.lower()
        return any(lowered == entry or lowered.startswith(f"{entry}:") for entry in allowlist)

    def _list_other_models(self, provider: str | None = None) -> list[dict[str, str | bool]]:
        if provider and provider not in {"anthropic", "azure"}:
            return []
        return [
            {"id": "anthropic/claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        ]

    @staticmethod
    def _build_prompt_metadata_entries(
        bundle: PromptSetBundle | None,
        *,
        preview_length: int = 400,
    ) -> list[dict[str, Any]]:
        if bundle is None:
            return []
        prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
        entries: list[dict[str, Any]] = []
        for item in bundle.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            entry: dict[str, Any] = {
                "prompt_id": prompt.prompt_id,
                "name": prompt.name,
                "kind": prompt.kind,
                "role": item.role,
                "checksum": prompt.checksum,
            }
            if prompt.source:
                entry["source"] = prompt.source
            if prompt.content:
                entry["content_preview"] = prompt.content[:preview_length]
            entries.append(entry)
        return entries


def create_adapter() -> WebUIAdapter:
    """WebUIAdapter 인스턴스 생성 팩토리.

    설정에 따라 적절한 저장소와 서비스를 주입합니다.
    """
    from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
    from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
    from evalvault.adapters.outbound.storage.factory import build_storage_adapter
    from evalvault.config.settings import get_settings
    from evalvault.domain.services.evaluator import RagasEvaluator

    # 설정 로드
    settings = get_settings()

    # Storage 생성
    storage = build_storage_adapter(settings=settings)

    # LLM adapter 생성 (API 키 없으면 None)
    llm_adapter = None
    try:
        llm_adapter = get_llm_adapter(settings)
        logger.info(f"LLM adapter initialized: {settings.llm_provider}")
    except Exception as e:
        logger.warning(f"LLM adapter initialization failed: {e}")

    # Evaluator 생성
    llm_factory = SettingsLLMFactory(settings)
    korean_toolkit = try_create_korean_toolkit()
    evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)

    return WebUIAdapter(
        storage=storage,
        evaluator=evaluator,
        llm_adapter=llm_adapter,
        settings=settings,
    )
