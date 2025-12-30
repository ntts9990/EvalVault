"""Web UI adapter implementing WebUIPort."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from evalvault.ports.inbound.web_port import (
    EvalProgress,
    EvalRequest,
    RunFilters,
    RunSummary,
)

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.domain.entities.improvement import ImprovementReport
    from evalvault.ports.outbound.llm_port import LLMPort
    from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)

# 지원하는 메트릭 목록
AVAILABLE_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
    "insurance_term_accuracy",
]


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
        evaluator: object | None = None,
        report_generator: object | None = None,
        llm_adapter: LLMPort | None = None,
        data_loader: object | None = None,
    ):
        """어댑터 초기화.

        Args:
            storage: 저장소 어댑터 (선택적)
            evaluator: 평가 서비스 (선택적)
            report_generator: 보고서 생성기 (선택적)
            llm_adapter: LLM 어댑터 (선택적)
            data_loader: 데이터 로더 (선택적)
        """
        self._storage = storage
        self._evaluator = evaluator
        self._report_generator = report_generator
        self._llm_adapter = llm_adapter
        self._data_loader = data_loader

    def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """평가 실행.

        Args:
            request: 평가 요청
            on_progress: 진행률 콜백

        Returns:
            평가 결과

        Raises:
            RuntimeError: 필수 컴포넌트가 설정되지 않은 경우
        """
        if self._evaluator is None:
            raise RuntimeError("Evaluator not configured")
        if self._llm_adapter is None:
            raise RuntimeError("LLM adapter not configured")
        if self._data_loader is None:
            raise RuntimeError("Data loader not configured")

        # 1. 데이터셋 로드
        logger.info(f"Loading dataset from: {request.dataset_path}")
        dataset = self._data_loader.load(request.dataset_path)

        # 2. 진행률 초기화
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

        # 3. 평가 실행 (비동기 -> 동기 변환)
        logger.info(f"Starting evaluation with metrics: {request.metrics}")

        async def run_async_evaluation():
            return await self._evaluator.evaluate(
                dataset=dataset,
                metrics=request.metrics,
                llm=self._llm_adapter,
                thresholds=request.thresholds or {},
                parallel=True,
                batch_size=5,
            )

        result = asyncio.run(run_async_evaluation())

        # 4. 완료 진행률 콜백
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

        # 5. 결과 저장
        if self._storage:
            logger.info(f"Saving evaluation run: {result.run_id}")
            self._storage.save_run(result)

        return result

    def list_runs(
        self,
        limit: int = 50,
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

        try:
            # 저장소에서 평가 목록 조회
            runs = self._storage.list_runs(limit=limit)

            # RunSummary로 변환
            summaries = []
            for run in runs:
                summary = RunSummary(
                    run_id=run.run_id,
                    dataset_name=run.dataset_name,
                    model_name=run.model_name,
                    pass_rate=run.pass_rate,
                    total_test_cases=run.total_test_cases,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    metrics_evaluated=run.metrics_evaluated,
                    total_tokens=run.total_tokens,
                    total_cost_usd=run.total_cost_usd,
                )

                # 필터 적용
                if filters:
                    if filters.dataset_name and filters.dataset_name != summary.dataset_name:
                        continue
                    if filters.model_name and filters.model_name != summary.model_name:
                        continue
                    if filters.min_pass_rate and summary.pass_rate < filters.min_pass_rate:
                        continue
                    if filters.max_pass_rate and summary.pass_rate > filters.max_pass_rate:
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

        return run

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

    def generate_report(
        self,
        run_id: str,
        output_format: Literal["markdown", "html"] = "markdown",
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
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
        # TODO: 실제 보고서 생성 로직 구현
        raise NotImplementedError("Report generation not yet implemented")

    def get_available_metrics(self) -> list[str]:
        """사용 가능한 메트릭 목록 반환."""
        return AVAILABLE_METRICS.copy()

    def get_metric_descriptions(self) -> dict[str, str]:
        """메트릭별 설명 반환."""
        return {
            "faithfulness": "답변이 컨텍스트에 충실한지 평가",
            "answer_relevancy": "답변이 질문과 관련있는지 평가",
            "context_precision": "검색된 컨텍스트의 정밀도 평가",
            "context_recall": "필요한 정보가 검색되었는지 평가",
            "factual_correctness": "ground_truth 대비 사실적 정확성 평가",
            "semantic_similarity": "답변과 ground_truth 간 의미적 유사도 평가",
            "insurance_term_accuracy": "보험 용어 정확성 평가",
        }

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
            return await self._evaluator.evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self._llm_adapter,
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
    ) -> ImprovementReport:
        """개선 가이드 생성.

        평가 결과를 분석하여 RAG 시스템 개선 가이드를 생성합니다.

        Args:
            run_id: 분석할 평가 실행 ID
            include_llm: LLM 기반 분석 포함 여부
            metrics: 분석할 메트릭 (None이면 모두)

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
        if include_llm and self._llm_adapter:
            generator = InsightGenerator(llm_adapter=self._llm_adapter)

        # 서비스 초기화 및 리포트 생성
        # max_llm_samples=2로 설정하여 LLM 호출 수 감소 (속도 개선)
        service = ImprovementGuideService(
            pattern_detector=detector,
            insight_generator=generator,
            playbook=playbook,
            enable_llm_enrichment=include_llm,
            max_llm_samples=2,
        )

        return service.generate_report(run, metrics=metrics, include_llm_analysis=include_llm)

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
    ):
        """LLM 기반 지능형 보고서 생성.

        전문가 수준의 분석, 최신 연구 기반 권장사항,
        구체적인 액션 아이템을 포함한 보고서를 생성합니다.

        Args:
            run_id: 분석할 평가 실행 ID
            metrics_to_analyze: 분석할 메트릭 (None이면 모두)
            thresholds: 메트릭별 임계값

        Returns:
            LLMReport 인스턴스

        Raises:
            KeyError: 평가 결과를 찾을 수 없는 경우
            RuntimeError: LLM 또는 저장소가 설정되지 않은 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")
        if self._llm_adapter is None:
            raise RuntimeError("LLM adapter not configured. .env에 OPENAI_API_KEY를 설정하세요.")

        # 평가 결과 조회
        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        # LLM 보고서 생성기 초기화
        from evalvault.adapters.outbound.report import LLMReportGenerator

        generator = LLMReportGenerator(
            llm_adapter=self._llm_adapter,
            include_research_insights=True,
            include_action_items=True,
        )

        # 동기 방식으로 보고서 생성
        return generator.generate_report_sync(
            run,
            metrics_to_analyze=metrics_to_analyze,
            thresholds=thresholds or run.thresholds,
        )


def create_adapter() -> WebUIAdapter:
    """WebUIAdapter 인스턴스 생성 팩토리.

    설정에 따라 적절한 저장소와 서비스를 주입합니다.
    """
    from evalvault.adapters.outbound.llm import get_llm_adapter
    from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
    from evalvault.config.settings import Settings
    from evalvault.domain.services.evaluator import RagasEvaluator

    # 설정 로드
    settings = Settings()

    # Storage 생성 (기본 SQLite)
    db_path = Path("evalvault.db")
    storage = SQLiteStorageAdapter(db_path=db_path)

    # LLM adapter 생성 (API 키 없으면 None)
    llm_adapter = None
    try:
        llm_adapter = get_llm_adapter(settings)
        logger.info(f"LLM adapter initialized: {settings.llm_provider}")
    except Exception as e:
        logger.warning(f"LLM adapter initialization failed: {e}")

    # Evaluator 생성
    evaluator = RagasEvaluator()

    return WebUIAdapter(
        storage=storage,
        evaluator=evaluator,
        llm_adapter=llm_adapter,
    )
