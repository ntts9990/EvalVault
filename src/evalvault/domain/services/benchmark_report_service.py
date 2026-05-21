"""Benchmark Report Service.

LLM을 활용하여 KMMLU 등 벤치마크 결과에 대한 전문가 수준의 분석 보고서를 생성합니다.
RAG 성능 개선에 초점을 맞추어 현황 파악, 문제점 정의, 원인 분석, 해결 방안을 제시합니다.

D-S3b rewiring
--------------
This module exposes the legacy :class:`BenchmarkReportService` *and* the new
:class:`BenchmarkReportBuilder` / :class:`BenchmarkRenderer` pair that conform
to the ``ReportBuilder`` / ``Renderer`` Protocols from
:mod:`evalvault.domain.services.reporting`. The legacy public surface
(``BenchmarkReport``, ``BenchmarkReportService``) remains byte-identical so
CLI output and regression baselines do not change.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)

if TYPE_CHECKING:
    from evalvault.domain.entities.benchmark_run import BenchmarkRun
    from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


BENCHMARK_ANALYSIS_PROMPT = """당신은 LLM 벤치마크 평가 전문가입니다. RAG 시스템 성능 개선 관점에서 분석해주세요.

## 벤치마크 결과
- 벤치마크: {benchmark_name}
- 모델: {model_name}
- 백엔드: {backend}
- 전체 정확도: {overall_accuracy:.1%}
- 평가 샘플 수: {num_samples}

## 도메인별 결과
{subject_results}

## 분석 요청

다음 구조로 **RAG 성능 개선** 관점의 분석을 제공해주세요:

### 1. 현황 요약 (2-3문장)
- 전체 성능 수준과 특이점
- 강점/약점 도메인 명시

### 2. 문제점 정의
각 문제점에 대해:
- **문제**: 구체적 현상 (예: "Accounting 도메인 정확도 45%로 목표 대비 25%p 미달")
- **영향 범위**: 어떤 사용 시나리오에 영향을 미치는지
- **심각도**: Critical / High / Medium / Low

### 3. 원인 분석
각 문제점별로:
- **1차 원인**: 직접적 원인 (예: "도메인 특화 용어 이해 부족")
- **근본 원인**: 구조적 원인 (예: "학습 데이터에 회계 전문 용어 부족")
- **검증 방법**: 원인 확인을 위한 테스트 방법

### 4. 해결 방안
우선순위별로 3-5개 제안:
- **방안명**: 한 줄 설명
- **구현 방법**: 구체적 단계
- **예상 효과**: 정량적 개선 예측 (예: "+15%p 정확도 향상 예상")
- **소요 리소스**: 시간/비용 추정
- **우선순위**: P0(즉시) / P1(1주 내) / P2(1개월 내)

### 5. RAG 파이프라인 개선 제안
벤치마크 결과를 RAG 시스템에 적용할 때:
- **Retriever 개선**: 검색 품질 향상 방안
- **Prompt 최적화**: 도메인별 프롬프트 튜닝
- **Knowledge Base 확장**: 필요한 추가 지식

마크다운 형식으로 작성해주세요. 추상적 조언이 아닌 **구체적이고 실행 가능한** 제안을 해주세요."""


BENCHMARK_COMPARISON_PROMPT = """당신은 LLM 벤치마크 비교 분석 전문가입니다.

## 비교 대상
### 기준 실행 (Baseline)
- 모델: {baseline_model}
- 전체 정확도: {baseline_accuracy:.1%}
- 도메인별: {baseline_subjects}

### 비교 실행 (Target)
- 모델: {target_model}
- 전체 정확도: {target_accuracy:.1%}
- 도메인별: {target_subjects}

## 변화량
- 전체: {accuracy_delta:+.1%}p
- 도메인별 변화: {subject_deltas}

## 분석 요청

### 1. 핵심 변화 요약
- 무엇이 좋아졌는지 / 나빠졌는지 명확히
- 통계적으로 유의미한 변화인지 (샘플 수 고려)

### 2. 개선된 영역 분석
- 어떤 도메인/유형에서 개선되었는지
- 개선의 원인 추정

### 3. 악화된 영역 분석
- 어떤 도메인/유형에서 악화되었는지
- 악화의 원인 추정
- **Regression 방지책** 제안

### 4. RAG 적용 권장사항
- 새 모델을 RAG에 적용해야 하는지
- 적용 시 주의사항
- 롤백 기준

마크다운 형식으로 작성해주세요."""


MULTI_BENCHMARK_TREND_PROMPT = """당신은 LLM 벤치마크 트렌드 분석 전문가입니다.

## 벤치마크 이력 (최신순)
{benchmark_history}

## 분석 요청

### 1. 성능 추세
- 전체 정확도 추세 (상승/하락/정체)
- 도메인별 추세 변화
- 변동성 분석

### 2. 주요 변곡점
- 성능이 크게 변한 시점과 원인
- 모델/설정 변경과의 상관관계

### 3. 지속적 문제점
- 여러 실행에서 반복되는 약점
- 근본 원인과 해결 우선순위

### 4. 개선 로드맵 제안
- 단기 (1주): Quick wins
- 중기 (1개월): 구조적 개선
- 장기 (분기): 전략적 방향

마크다운 형식으로 작성해주세요."""


@dataclass
class BenchmarkReportSection:
    title: str
    content: str
    section_type: str = "analysis"
    metadata: dict = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    run_id: str
    benchmark_name: str
    model_name: str
    backend: str
    overall_accuracy: float
    num_samples: int

    subject_results: dict[str, dict] = field(default_factory=dict)

    executive_summary: str = ""
    problem_analysis: str = ""
    root_cause_analysis: str = ""
    recommendations: str = ""
    rag_improvement_guide: str = ""

    sections: list[BenchmarkReportSection] = field(default_factory=list)

    generated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            f"# 벤치마크 분석 보고서: {self.benchmark_name}",
            "",
            f"> 생성일시: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 모델: {self.model_name} ({self.backend})",
            f"> 전체 정확도: {self.overall_accuracy:.1%}",
            f"> 평가 샘플: {self.num_samples}개",
            "",
            "---",
            "",
            "## 도메인별 결과",
            "",
            "| 도메인 | 정확도 | 샘플 수 | 상태 |",
            "|--------|--------|---------|------|",
        ]

        for subject, result in self.subject_results.items():
            acc = result.get("accuracy", 0)
            samples = result.get("num_samples", 0)
            status = "✅" if acc >= 0.7 else "⚠️" if acc >= 0.5 else "❌"
            lines.append(f"| {subject} | {acc:.1%} | {samples} | {status} |")

        lines.extend(["", "---", ""])

        for section in self.sections:
            lines.extend([f"## {section.title}", "", section.content, "", "---", ""])

        lines.extend(
            [
                "",
                "*본 보고서는 AI가 생성한 분석입니다. 전문가 검토를 권장합니다.*",
                "*EvalVault Benchmark Report | Powered by LLM Analysis*",
            ]
        )

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "benchmark_name": self.benchmark_name,
            "model_name": self.model_name,
            "backend": self.backend,
            "overall_accuracy": self.overall_accuracy,
            "num_samples": self.num_samples,
            "subject_results": self.subject_results,
            "sections": [
                {"title": s.title, "content": s.content, "type": s.section_type}
                for s in self.sections
            ],
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


class BenchmarkReportService:
    def __init__(
        self,
        llm_adapter: LLMPort,
        *,
        language: str = "ko",
    ):
        self._llm_adapter = llm_adapter
        self._language = language

    async def generate_report(
        self,
        benchmark_run: BenchmarkRun,
    ) -> BenchmarkReport:
        logger.info(f"Generating benchmark report for run: {benchmark_run.run_id}")

        subject_results = {}
        for result in benchmark_run.results:
            subject_results[result.task_name] = {
                "accuracy": result.accuracy,
                "num_samples": result.num_samples,
                "metrics": result.metrics,
            }

        subject_lines = []
        for subject, data in subject_results.items():
            acc = data["accuracy"]
            samples = data["num_samples"]
            status = "양호" if acc >= 0.7 else "주의" if acc >= 0.5 else "미달"
            subject_lines.append(f"- {subject}: {acc:.1%} ({samples}샘플) - {status}")

        prompt = BENCHMARK_ANALYSIS_PROMPT.format(
            benchmark_name=benchmark_run.benchmark_name,
            model_name=benchmark_run.model_name,
            backend=benchmark_run.backend,
            overall_accuracy=benchmark_run.overall_accuracy or 0,
            num_samples=sum(r.num_samples for r in benchmark_run.results),
            subject_results="\n".join(subject_lines),
        )

        try:
            analysis_content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate benchmark analysis: {e}")
            analysis_content = f"*분석 생성 실패: {e}*"

        report = BenchmarkReport(
            run_id=benchmark_run.run_id,
            benchmark_name=benchmark_run.benchmark_name,
            model_name=benchmark_run.model_name,
            backend=benchmark_run.backend,
            overall_accuracy=benchmark_run.overall_accuracy or 0,
            num_samples=sum(r.num_samples for r in benchmark_run.results),
            subject_results=subject_results,
            sections=[
                BenchmarkReportSection(
                    title="벤치마크 분석",
                    content=analysis_content,
                    section_type="analysis",
                )
            ],
        )

        return report

    async def generate_comparison_report(
        self,
        baseline: BenchmarkRun,
        target: BenchmarkRun,
    ) -> BenchmarkReport:
        logger.info(f"Generating comparison report: {baseline.run_id} vs {target.run_id}")

        baseline_subjects = {r.task_name: r.accuracy for r in baseline.results}
        target_subjects = {r.task_name: r.accuracy for r in target.results}

        subject_deltas = {}
        for subject in set(baseline_subjects.keys()) | set(target_subjects.keys()):
            b_acc = baseline_subjects.get(subject, 0)
            t_acc = target_subjects.get(subject, 0)
            subject_deltas[subject] = t_acc - b_acc

        baseline_acc = baseline.overall_accuracy or 0
        target_acc = target.overall_accuracy or 0

        prompt = BENCHMARK_COMPARISON_PROMPT.format(
            baseline_model=baseline.model_name,
            baseline_accuracy=baseline_acc,
            baseline_subjects=", ".join(f"{k}: {v:.1%}" for k, v in baseline_subjects.items()),
            target_model=target.model_name,
            target_accuracy=target_acc,
            target_subjects=", ".join(f"{k}: {v:.1%}" for k, v in target_subjects.items()),
            accuracy_delta=target_acc - baseline_acc,
            subject_deltas=", ".join(f"{k}: {v:+.1%}p" for k, v in subject_deltas.items()),
        )

        try:
            comparison_content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate comparison analysis: {e}")
            comparison_content = f"*비교 분석 생성 실패: {e}*"

        subject_results = {}
        for result in target.results:
            baseline_acc_subj = baseline_subjects.get(result.task_name, 0)
            subject_results[result.task_name] = {
                "accuracy": result.accuracy,
                "baseline_accuracy": baseline_acc_subj,
                "delta": result.accuracy - baseline_acc_subj,
                "num_samples": result.num_samples,
            }

        report = BenchmarkReport(
            run_id=target.run_id,
            benchmark_name=target.benchmark_name,
            model_name=f"{baseline.model_name} → {target.model_name}",
            backend=target.backend,
            overall_accuracy=target_acc,
            num_samples=sum(r.num_samples for r in target.results),
            subject_results=subject_results,
            sections=[
                BenchmarkReportSection(
                    title="벤치마크 비교 분석",
                    content=comparison_content,
                    section_type="comparison",
                    metadata={
                        "baseline_run_id": baseline.run_id,
                        "target_run_id": target.run_id,
                    },
                )
            ],
            metadata={
                "comparison": True,
                "baseline_run_id": baseline.run_id,
                "accuracy_delta": target_acc - baseline_acc,
            },
        )

        return report

    async def generate_trend_report(
        self,
        benchmark_runs: list[BenchmarkRun],
    ) -> BenchmarkReport:
        if not benchmark_runs:
            raise ValueError("At least one benchmark run is required")

        logger.info(f"Generating trend report for {len(benchmark_runs)} runs")

        history_lines = []
        for run in benchmark_runs:
            acc = run.overall_accuracy or 0
            subjects = ", ".join(f"{r.task_name}: {r.accuracy:.1%}" for r in run.results)
            history_lines.append(
                f"- {run.completed_at or run.started_at}: {run.model_name} - 전체 {acc:.1%} ({subjects})"
            )

        prompt = MULTI_BENCHMARK_TREND_PROMPT.format(benchmark_history="\n".join(history_lines))

        try:
            trend_content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {e}")
            trend_content = f"*트렌드 분석 생성 실패: {e}*"

        latest = benchmark_runs[-1]
        subject_results = {
            r.task_name: {"accuracy": r.accuracy, "num_samples": r.num_samples}
            for r in latest.results
        }

        report = BenchmarkReport(
            run_id=latest.run_id,
            benchmark_name=latest.benchmark_name,
            model_name=f"{len(benchmark_runs)} runs trend",
            backend=latest.backend,
            overall_accuracy=latest.overall_accuracy or 0,
            num_samples=sum(r.num_samples for r in latest.results),
            subject_results=subject_results,
            sections=[
                BenchmarkReportSection(
                    title="벤치마크 트렌드 분석",
                    content=trend_content,
                    section_type="trend",
                    metadata={"run_count": len(benchmark_runs)},
                )
            ],
            metadata={
                "trend_analysis": True,
                "run_ids": [r.run_id for r in benchmark_runs],
            },
        )

        return report

    def generate_report_sync(
        self,
        benchmark_run: BenchmarkRun,
    ) -> BenchmarkReport:
        return asyncio.run(self.generate_report(benchmark_run))

    def generate_comparison_report_sync(
        self,
        baseline: BenchmarkRun,
        target: BenchmarkRun,
    ) -> BenchmarkReport:
        return asyncio.run(self.generate_comparison_report(baseline, target))

    def generate_trend_report_sync(
        self,
        benchmark_runs: list[BenchmarkRun],
    ) -> BenchmarkReport:
        return asyncio.run(self.generate_trend_report(benchmark_runs))


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer (ReportBuilder + Renderer Protocol conformers)
# ---------------------------------------------------------------------------


def _benchmark_report_to_report_data(report: BenchmarkReport) -> ReportData:
    """Project a legacy :class:`BenchmarkReport` onto :class:`ReportData`.

    The legacy dataclass is preserved as the canonical persistence shape; the
    projection here is used by the new ``ReportBuilder`` / ``Renderer``
    pipeline. The status field is intentionally left ``None`` to honour the
    T2 authority discipline (reports must not emit T3 verdicts).
    """

    sections = tuple(
        ReportSection(
            title=section.title,
            body=section.content,
            section_type=section.section_type,
            metadata=dict(section.metadata),
        )
        for section in report.sections
    )

    rows: list[tuple[object, ...]] = []
    for subject, result in report.subject_results.items():
        accuracy = float(result.get("accuracy", 0.0))
        samples = int(result.get("num_samples", 0))
        rows.append((subject, accuracy, samples))
    subject_table = MetricTable(
        name="subject_results",
        columns=("subject", "accuracy", "num_samples"),
        rows=tuple(rows),
    )

    metadata: dict[str, object] = {
        "benchmark_name": report.benchmark_name,
        "model_name": report.model_name,
        "backend": report.backend,
        "overall_accuracy": report.overall_accuracy,
        "num_samples": report.num_samples,
        **dict(report.metadata),
    }

    return ReportData(
        report_id=report.run_id,
        title=f"벤치마크 분석 보고서: {report.benchmark_name}",
        sections=sections,
        tables=(subject_table,),
        metadata=metadata,
        generated_at=report.generated_at,
    )


class BenchmarkReportBuilder:
    """:class:`ReportBuilder` adapter over :class:`BenchmarkReportService`.

    Modes:

    * ``"report"``   – :meth:`BenchmarkReportService.generate_report`
    * ``"compare"``  – :meth:`BenchmarkReportService.generate_comparison_report`
    * ``"trend"``    – :meth:`BenchmarkReportService.generate_trend_report`

    Builders forward to the existing service, then project the resulting
    :class:`BenchmarkReport` onto :class:`ReportData`. Existing CLI output
    bytes (which still go through ``BenchmarkReport.to_markdown``) are not
    affected.
    """

    def __init__(self, service: BenchmarkReportService) -> None:
        self._service = service

    def build(self, *args: object, **kwargs: object) -> ReportData:
        mode = str(kwargs.pop("mode", "report"))
        if mode == "report":
            (benchmark_run,) = args  # type: ignore[assignment]
            report = self._service.generate_report_sync(benchmark_run)  # type: ignore[arg-type]
        elif mode == "compare":
            baseline, target = args  # type: ignore[assignment]
            report = self._service.generate_comparison_report_sync(
                baseline,  # type: ignore[arg-type]
                target,  # type: ignore[arg-type]
            )
        elif mode == "trend":
            (benchmark_runs,) = args  # type: ignore[assignment]
            report = self._service.generate_trend_report_sync(
                benchmark_runs,  # type: ignore[arg-type]
            )
        else:
            raise ValueError(f"Unknown BenchmarkReportBuilder mode: {mode!r}")
        return _benchmark_report_to_report_data(report)


class BenchmarkRenderer:
    """:class:`Renderer` Protocol adapter for benchmark reports.

    Renders a :class:`ReportData` projected from :class:`BenchmarkReport`
    back into the legacy markdown layout. The output is intentionally aligned
    with ``BenchmarkReport.to_markdown`` for the projected shape; consumers
    who require byte-identical CLI output should keep using
    ``BenchmarkReport.to_markdown`` directly.
    """

    def render(self, data: ReportData) -> str:
        metadata = dict(data.metadata)
        benchmark_name = str(metadata.get("benchmark_name", ""))
        model_name = str(metadata.get("model_name", ""))
        backend = str(metadata.get("backend", ""))
        overall_accuracy = float(metadata.get("overall_accuracy", 0.0))
        num_samples = int(metadata.get("num_samples", 0))

        lines = [
            f"# 벤치마크 분석 보고서: {benchmark_name}",
            "",
            f"> 생성일시: {data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 모델: {model_name} ({backend})",
            f"> 전체 정확도: {overall_accuracy:.1%}",
            f"> 평가 샘플: {num_samples}개",
            "",
            "---",
            "",
            "## 도메인별 결과",
            "",
            "| 도메인 | 정확도 | 샘플 수 | 상태 |",
            "|--------|--------|---------|------|",
        ]
        for table in data.tables:
            if table.name != "subject_results":
                continue
            for subject, accuracy, samples in table.rows:
                acc = float(accuracy)
                status = "✅" if acc >= 0.7 else "⚠️" if acc >= 0.5 else "❌"
                lines.append(f"| {subject} | {acc:.1%} | {samples} | {status} |")

        lines.extend(["", "---", ""])

        for section in data.sections:
            lines.extend([f"## {section.title}", "", section.body, "", "---", ""])

        lines.extend(
            [
                "",
                "*본 보고서는 AI가 생성한 분석입니다. 전문가 검토를 권장합니다.*",
                "*EvalVault Benchmark Report | Powered by LLM Analysis*",
            ]
        )

        return "\n".join(lines)


__all__ = [
    "BENCHMARK_ANALYSIS_PROMPT",
    "BENCHMARK_COMPARISON_PROMPT",
    "MULTI_BENCHMARK_TREND_PROMPT",
    "BenchmarkRenderer",
    "BenchmarkReport",
    "BenchmarkReportBuilder",
    "BenchmarkReportSection",
    "BenchmarkReportService",
]
