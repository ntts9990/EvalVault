"""Unified Report Service.

RAG 평가 결과와 벤치마크 결과를 통합하여 종합적인 성능 분석 보고서를 생성합니다.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.domain.entities.benchmark_run import BenchmarkRun
    from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


UNIFIED_REPORT_PROMPT = """당신은 RAG 시스템 성능 분석 전문가입니다. 평가 결과와 벤치마크 결과를 종합하여 분석해주세요.

## RAG 평가 결과
- 데이터셋: {dataset_name}
- 모델: {eval_model}
- 통과율: {pass_rate:.1%}
- 테스트 케이스: {total_test_cases}개

### 메트릭별 점수
{metrics_summary}

## 벤치마크 결과 (KMMLU)
- 모델: {benchmark_model}
- 전체 정확도: {benchmark_accuracy:.1%}
- 평가 샘플: {benchmark_samples}개

### 도메인별 점수
{benchmark_summary}

---

## 분석 요청

다음 구조로 **통합 성능 분석**을 제공해주세요:

### 1. 종합 현황 (Executive Summary)
- RAG 품질과 LLM 기반 지식 수준의 전체적인 상태
- 두 평가 결과 간의 상관관계 분석
- 핵심 강점과 약점 3줄 요약

### 2. 문제점 정의 및 우선순위
각 문제점에 대해:

| 문제 | 출처 | 심각도 | 영향 범위 |
|------|------|--------|----------|
| (구체적 현상) | RAG/벤치마크/공통 | Critical/High/Medium/Low | (영향받는 시나리오) |

### 3. 근본 원인 분석

#### 3.1 RAG 파이프라인 관점
- **Retriever 문제**: 검색 품질 이슈
- **Generator 문제**: 생성 품질 이슈
- **Knowledge Base 문제**: 지식 커버리지 이슈

#### 3.2 LLM 역량 관점
- **도메인 지식 부족**: 벤치마크에서 드러난 약점
- **추론 능력 한계**: 복잡한 질문 처리 능력
- **언어 이해 한계**: 한국어 특화 이슈

#### 3.3 상호작용 관점
- RAG 품질 저하가 LLM 약점과 연관되는 패턴
- 벤치마크 고득점 도메인에서 RAG도 높은지 확인

### 4. 해결 방안 (우선순위별)

#### P0 - 즉시 실행 (1-3일)
- 빠르게 효과를 볼 수 있는 Quick Wins
- 구체적 실행 방법과 예상 효과

#### P1 - 단기 (1-2주)
- 구조적 개선이 필요한 항목
- 필요 리소스와 예상 효과

#### P2 - 중기 (1개월)
- 전략적 방향 제시
- ROI 분석

### 5. 검증 및 모니터링 계획
- 각 개선 방안의 효과 측정 방법
- 지속적 모니터링을 위한 메트릭
- 롤백 기준

### 6. 다음 단계 권장사항
- 즉시 실행할 3가지 액션 아이템
- 다음 평가 시 추가로 확인할 사항
- 장기적 품질 개선 로드맵

마크다운 형식으로 작성해주세요. **추상적 조언 대신 구체적이고 실행 가능한 제안**을 해주세요."""


CORRELATION_ANALYSIS_PROMPT = """당신은 RAG 시스템과 LLM 벤치마크 간의 상관관계 분석 전문가입니다.

## 데이터

### RAG 메트릭별 점수
{rag_metrics}

### 벤치마크 도메인별 점수
{benchmark_domains}

## 분석 요청

### 1. 상관관계 패턴
- 벤치마크 고득점 도메인에서 RAG 품질도 높은가?
- 특정 RAG 메트릭과 벤치마크 점수 간 연관성
- 예상과 다른 패턴 (벤치마크 높은데 RAG 낮은 경우 등)

### 2. 원인 가설
각 패턴에 대한 가능한 원인:
- 데이터 분포 차이
- 태스크 특성 차이
- 프롬프트/컨텍스트 영향

### 3. 검증 방법
각 가설을 검증할 수 있는 추가 테스트 제안

### 4. 최적화 방향
상관관계 분석을 바탕으로 한 개선 우선순위

마크다운 형식으로 작성해주세요."""


@dataclass
class UnifiedReportSection:
    title: str
    content: str
    section_type: str = "analysis"
    metadata: dict = field(default_factory=dict)


@dataclass
class UnifiedReport:
    report_id: str

    eval_run_id: str | None = None
    benchmark_run_id: str | None = None

    dataset_name: str = ""
    eval_model: str = ""
    benchmark_model: str = ""

    pass_rate: float = 0.0
    benchmark_accuracy: float = 0.0

    metric_scores: dict[str, float] = field(default_factory=dict)
    benchmark_results: dict[str, dict] = field(default_factory=dict)

    sections: list[UnifiedReportSection] = field(default_factory=list)

    generated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# RAG 성능 통합 분석 보고서",
            "",
            f"> 생성일시: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 평가 개요",
            "",
            "| 구분 | 항목 | 값 |",
            "|------|------|-----|",
            f"| RAG 평가 | 데이터셋 | {self.dataset_name} |",
            f"| RAG 평가 | 모델 | {self.eval_model} |",
            f"| RAG 평가 | 통과율 | {self.pass_rate:.1%} |",
            f"| 벤치마크 | 모델 | {self.benchmark_model} |",
            f"| 벤치마크 | 정확도 | {self.benchmark_accuracy:.1%} |",
            "",
            "---",
            "",
        ]

        if self.metric_scores:
            lines.extend(
                ["### RAG 메트릭 점수", "", "| 메트릭 | 점수 | 상태 |", "|--------|------|------|"]
            )
            for metric, score in self.metric_scores.items():
                status = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                lines.append(f"| {metric} | {score:.3f} | {status} |")
            lines.extend(["", "---", ""])

        if self.benchmark_results:
            lines.extend(
                [
                    "### 벤치마크 도메인 점수",
                    "",
                    "| 도메인 | 정확도 | 상태 |",
                    "|--------|--------|------|",
                ]
            )
            for domain, result in self.benchmark_results.items():
                acc = result.get("accuracy", 0)
                status = "✅" if acc >= 0.7 else "⚠️" if acc >= 0.5 else "❌"
                lines.append(f"| {domain} | {acc:.1%} | {status} |")
            lines.extend(["", "---", ""])

        for section in self.sections:
            lines.extend([f"## {section.title}", "", section.content, "", "---", ""])

        lines.extend(
            [
                "",
                "*본 보고서는 AI가 생성한 분석입니다. 전문가 검토를 권장합니다.*",
                "*EvalVault Unified Report | RAG Evaluation + Benchmark Analysis*",
            ]
        )

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "eval_run_id": self.eval_run_id,
            "benchmark_run_id": self.benchmark_run_id,
            "dataset_name": self.dataset_name,
            "eval_model": self.eval_model,
            "benchmark_model": self.benchmark_model,
            "pass_rate": self.pass_rate,
            "benchmark_accuracy": self.benchmark_accuracy,
            "metric_scores": self.metric_scores,
            "benchmark_results": self.benchmark_results,
            "sections": [
                {"title": s.title, "content": s.content, "type": s.section_type}
                for s in self.sections
            ],
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


class UnifiedReportService:
    def __init__(
        self,
        llm_adapter: LLMPort,
        *,
        language: str = "ko",
    ):
        self._llm_adapter = llm_adapter
        self._language = language

    async def generate_unified_report(
        self,
        eval_run: EvaluationRun,
        benchmark_run: BenchmarkRun,
    ) -> UnifiedReport:
        logger.info(
            f"Generating unified report: eval={eval_run.run_id}, benchmark={benchmark_run.run_id}"
        )

        metric_scores = {}
        for metric in eval_run.metrics_evaluated:
            score = eval_run.get_avg_score(metric)
            if score is not None:
                metric_scores[metric] = score

        benchmark_results = {}
        for result in benchmark_run.results:
            benchmark_results[result.task_name] = {
                "accuracy": result.accuracy,
                "num_samples": result.num_samples,
            }

        metrics_lines = [f"- {m}: {s:.3f}" for m, s in metric_scores.items()]
        benchmark_lines = [f"- {d}: {r['accuracy']:.1%}" for d, r in benchmark_results.items()]

        prompt = UNIFIED_REPORT_PROMPT.format(
            dataset_name=eval_run.dataset_name,
            eval_model=eval_run.model_name,
            pass_rate=eval_run.pass_rate,
            total_test_cases=eval_run.total_test_cases,
            metrics_summary="\n".join(metrics_lines),
            benchmark_model=benchmark_run.model_name,
            benchmark_accuracy=benchmark_run.overall_accuracy or 0,
            benchmark_samples=sum(r.num_samples for r in benchmark_run.results),
            benchmark_summary="\n".join(benchmark_lines),
        )

        try:
            analysis_content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate unified analysis: {e}")
            analysis_content = f"*통합 분석 생성 실패: {e}*"

        report = UnifiedReport(
            report_id=f"unified-{eval_run.run_id[:8]}-{benchmark_run.run_id[:8]}",
            eval_run_id=eval_run.run_id,
            benchmark_run_id=benchmark_run.run_id,
            dataset_name=eval_run.dataset_name,
            eval_model=eval_run.model_name,
            benchmark_model=benchmark_run.model_name,
            pass_rate=eval_run.pass_rate,
            benchmark_accuracy=benchmark_run.overall_accuracy or 0,
            metric_scores=metric_scores,
            benchmark_results=benchmark_results,
            sections=[
                UnifiedReportSection(
                    title="통합 성능 분석",
                    content=analysis_content,
                    section_type="unified",
                )
            ],
        )

        return report

    async def generate_correlation_analysis(
        self,
        eval_run: EvaluationRun,
        benchmark_run: BenchmarkRun,
    ) -> UnifiedReportSection:
        metric_scores = {}
        for metric in eval_run.metrics_evaluated:
            score = eval_run.get_avg_score(metric)
            if score is not None:
                metric_scores[metric] = score

        benchmark_results = {r.task_name: r.accuracy for r in benchmark_run.results}

        rag_lines = [f"- {m}: {s:.3f}" for m, s in metric_scores.items()]
        benchmark_lines = [f"- {d}: {a:.1%}" for d, a in benchmark_results.items()]

        prompt = CORRELATION_ANALYSIS_PROMPT.format(
            rag_metrics="\n".join(rag_lines),
            benchmark_domains="\n".join(benchmark_lines),
        )

        try:
            content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate correlation analysis: {e}")
            content = f"*상관관계 분석 생성 실패: {e}*"

        return UnifiedReportSection(
            title="RAG-벤치마크 상관관계 분석",
            content=content,
            section_type="correlation",
        )

    def generate_unified_report_sync(
        self,
        eval_run: EvaluationRun,
        benchmark_run: BenchmarkRun,
    ) -> UnifiedReport:
        return asyncio.run(self.generate_unified_report(eval_run, benchmark_run))
