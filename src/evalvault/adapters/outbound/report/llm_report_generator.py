"""LLM-powered intelligent report generator.

LLM을 활용하여 전문가 수준의 RAG 평가 보고서를 생성합니다.
각 메트릭에 대한 심층 분석, 최신 연구 기반 개선 권장사항,
구체적인 액션 아이템을 제공합니다.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


# 메트릭별 전문가 분석 프롬프트
METRIC_ANALYSIS_PROMPTS = {
    "faithfulness": """당신은 RAG(Retrieval-Augmented Generation) 시스템의 Faithfulness 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Faithfulness (충실도)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Faithfulness 메트릭 설명
Faithfulness는 생성된 답변이 제공된 컨텍스트에 얼마나 충실한지를 측정합니다.
낮은 점수는 LLM이 컨텍스트에 없는 정보를 "환각(hallucination)"하고 있음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 이 점수가 의미하는 바를 구체적으로 설명
2. **주요 원인 분석**: 낮은/높은 점수의 가능한 원인들
3. **최신 연구 인사이트**: RAG 환각 감소에 대한 최신 연구 동향 (2023-2024)
   - Chain-of-Verification, Self-RAG, CRAG 등의 기법 언급
4. **구체적 개선 방안**: 실무에서 적용 가능한 3-5개의 개선 방안
5. **예상 효과**: 각 개선 방안의 예상 효과

마크다운 형식으로 작성해주세요.""",
    "answer_relevancy": """당신은 RAG 시스템의 Answer Relevancy 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Answer Relevancy (답변 관련성)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Answer Relevancy 메트릭 설명
Answer Relevancy는 생성된 답변이 사용자의 질문에 얼마나 관련있는지를 측정합니다.
낮은 점수는 답변이 질문의 의도를 제대로 파악하지 못했음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 이 점수가 의미하는 바를 구체적으로 설명
2. **주요 원인 분석**:
   - Query Understanding 문제
   - 프롬프트 설계 문제
   - 컨텍스트 선택 문제
3. **최신 연구 인사이트**: Query Rewriting, HyDE, Multi-Query 등 최신 기법
4. **구체적 개선 방안**: 실무에서 적용 가능한 개선 방안
5. **프롬프트 엔지니어링 팁**: 관련성 향상을 위한 프롬프트 최적화 방법

마크다운 형식으로 작성해주세요.""",
    "context_precision": """당신은 RAG 시스템의 Context Precision 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Context Precision (컨텍스트 정밀도)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Context Precision 메트릭 설명
Context Precision은 검색된 컨텍스트 중 실제로 관련있는 컨텍스트의 비율을 측정합니다.
낮은 점수는 불필요한 컨텍스트가 많이 검색되고 있음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: Retriever의 정밀도 상태 분석
2. **주요 원인 분석**:
   - 임베딩 모델 품질 문제
   - 청킹 전략 문제
   - 유사도 임계값 설정 문제
3. **최신 연구 인사이트**:
   - Reranking (Cohere Rerank, BGE Reranker)
   - Hybrid Search (BM25 + Dense)
   - Late Interaction 모델 (ColBERT)
4. **구체적 개선 방안**: Retriever 최적화 전략
5. **벤치마크 참고**: BEIR, MTEB 벤치마크 기준 권장 모델

마크다운 형식으로 작성해주세요.""",
    "context_recall": """당신은 RAG 시스템의 Context Recall 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Context Recall (컨텍스트 재현율)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Context Recall 메트릭 설명
Context Recall은 정답을 도출하는데 필요한 정보가 검색된 컨텍스트에 얼마나 포함되어 있는지를 측정합니다.
낮은 점수는 중요한 정보가 검색에서 누락되고 있음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: Retriever의 재현율 상태 분석
2. **주요 원인 분석**:
   - 인덱싱 커버리지 문제
   - 청킹 크기/오버랩 문제
   - 검색 top-k 설정 문제
3. **최신 연구 인사이트**:
   - Multi-Vector Retrieval
   - Parent Document Retriever
   - Contextual Compression
4. **구체적 개선 방안**: 재현율 향상 전략
5. **트레이드오프 분석**: Precision vs Recall 균형 전략

마크다운 형식으로 작성해주세요.""",
    "factual_correctness": """당신은 RAG 시스템의 Factual Correctness 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Factual Correctness (사실적 정확성)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Factual Correctness 메트릭 설명
Factual Correctness는 생성된 답변이 ground truth와 비교하여 사실적으로 얼마나 정확한지를 측정합니다.
낮은 점수는 답변에 사실적 오류가 포함되어 있음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 사실적 정확성 상태 분석
2. **주요 원인 분석**:
   - LLM의 사전 학습 지식과의 충돌
   - 컨텍스트 정보 활용 부족
   - 추론 오류
3. **최신 연구 인사이트**:
   - Fact Verification 기법
   - Knowledge Grounding
   - Citation Generation
4. **구체적 개선 방안**: 사실적 정확성 향상 전략
5. **검증 메커니즘**: 답변 검증을 위한 파이프라인 제안

마크다운 형식으로 작성해주세요.""",
    "semantic_similarity": """당신은 RAG 시스템의 Semantic Similarity 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Semantic Similarity (의미적 유사도)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Semantic Similarity 메트릭 설명
Semantic Similarity는 생성된 답변과 ground truth 간의 의미적 유사도를 측정합니다.
낮은 점수는 답변의 의미가 기대하는 답변과 다름을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 의미적 유사도 상태 분석
2. **주요 원인 분석**:
   - 답변 스타일/형식 차이
   - 핵심 정보 누락
   - 불필요한 정보 추가
3. **최신 연구 인사이트**:
   - Sentence Embedding 모델 발전
   - Cross-Encoder vs Bi-Encoder
4. **구체적 개선 방안**: 의미적 유사도 향상 전략
5. **평가 방법론**: 다양한 유사도 측정 방법 비교

마크다운 형식으로 작성해주세요.""",
}

# 기본 메트릭 분석 프롬프트 (등록되지 않은 메트릭용)
DEFAULT_METRIC_PROMPT = """당신은 RAG 시스템 평가 전문가입니다.

## 분석 대상
- 메트릭: {metric_name}
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 이 점수가 의미하는 바
2. **주요 원인 분석**: 가능한 원인들
3. **개선 권장사항**: 실무에서 적용 가능한 개선 방안
4. **예상 효과**: 각 개선 방안의 예상 효과

마크다운 형식으로 작성해주세요."""


# 종합 보고서 프롬프트
EXECUTIVE_SUMMARY_PROMPT = """당신은 RAG 시스템 평가 전문 컨설턴트입니다.

## 평가 결과 요약
- 데이터셋: {dataset_name}
- 모델: {model_name}
- 전체 통과율: {pass_rate:.1%}
- 테스트 케이스: {total_test_cases}개

## 메트릭별 점수
{metrics_summary}

## 요청사항
위 평가 결과를 바탕으로 경영진/의사결정자를 위한 **Executive Summary**를 작성해주세요:

1. **핵심 요약** (3-4문장): 전체 평가 결과의 핵심 인사이트
2. **강점 분석**: 잘 수행되고 있는 영역
3. **개선 필요 영역**: 우선적으로 개선이 필요한 영역 (우선순위 포함)
4. **비즈니스 영향**: 현재 상태가 비즈니스에 미치는 영향
5. **권장 액션 플랜**:
   - 즉시 실행 (Quick Wins)
   - 단기 (1-2주)
   - 중기 (1개월)
6. **예상 ROI**: 개선 시 예상되는 효과

마크다운 형식으로 작성해주세요. 전문적이면서도 이해하기 쉽게 작성해주세요."""


@dataclass
class LLMReportSection:
    """LLM 생성 보고서 섹션."""

    title: str
    content: str
    metric_name: str | None = None
    score: float | None = None
    threshold: float | None = None


@dataclass
class LLMReport:
    """LLM 기반 전체 보고서."""

    run_id: str
    dataset_name: str
    model_name: str
    pass_rate: float
    total_test_cases: int

    executive_summary: str = ""
    metric_analyses: list[LLMReportSection] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """마크다운 형식으로 변환."""
        lines = [
            f"# RAG 평가 보고서: {self.dataset_name}",
            "",
            f"> 생성일시: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 모델: {self.model_name}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
            "---",
            "",
        ]

        for section in self.metric_analyses:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                ]
            )
            if section.score is not None and section.threshold is not None:
                status = "✅ Pass" if section.score >= section.threshold else "❌ Fail"
                lines.extend(
                    [
                        f"**점수**: {section.score:.3f} / {section.threshold:.2f} ({status})",
                        "",
                    ]
                )
            lines.extend(
                [
                    section.content,
                    "",
                    "---",
                    "",
                ]
            )

        lines.extend(
            [
                "",
                "*본 보고서는 AI가 생성한 분석입니다. 전문가 검토를 권장합니다.*",
                "*EvalVault v1.3.0 | Powered by Ragas + LLM Analysis*",
            ]
        )

        return "\n".join(lines)


class LLMReportGenerator:
    """LLM 기반 지능형 보고서 생성기.

    LLM을 활용하여 전문가 수준의 RAG 평가 보고서를 생성합니다.
    """

    def __init__(
        self,
        llm_adapter: LLMPort,
        *,
        include_research_insights: bool = True,
        include_action_items: bool = True,
        language: str = "ko",
    ):
        """초기화.

        Args:
            llm_adapter: LLM 어댑터
            include_research_insights: 최신 연구 인사이트 포함 여부
            include_action_items: 구체적 액션 아이템 포함 여부
            language: 보고서 언어 (ko/en)
        """
        self._llm_adapter = llm_adapter
        self._include_research = include_research_insights
        self._include_actions = include_action_items
        self._language = language

    async def generate_report(
        self,
        run: EvaluationRun,
        *,
        metrics_to_analyze: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> LLMReport:
        """LLM 기반 보고서 생성.

        Args:
            run: 평가 실행 결과
            metrics_to_analyze: 분석할 메트릭 (None이면 모두)
            thresholds: 메트릭별 임계값

        Returns:
            LLMReport 인스턴스
        """
        thresholds = thresholds or run.thresholds or {}
        metrics_to_analyze = metrics_to_analyze or run.metrics_evaluated

        # 메트릭 점수 수집
        metrics_scores = {}
        for metric in metrics_to_analyze:
            score = run.get_avg_score(metric)
            if score is not None:
                metrics_scores[metric] = score

        # 1. 각 메트릭 분석 (병렬 처리)
        logger.info(f"Generating LLM analysis for {len(metrics_scores)} metrics...")
        analysis_tasks = []
        for metric_name, score in metrics_scores.items():
            threshold = thresholds.get(metric_name, 0.7)
            task = self._analyze_metric(metric_name, score, threshold)
            analysis_tasks.append(task)

        metric_analyses = await asyncio.gather(*analysis_tasks)

        # 2. Executive Summary 생성
        logger.info("Generating executive summary...")
        executive_summary = await self._generate_executive_summary(run, metrics_scores, thresholds)

        return LLMReport(
            run_id=run.run_id,
            dataset_name=run.dataset_name,
            model_name=run.model_name,
            pass_rate=run.pass_rate,
            total_test_cases=run.total_test_cases,
            executive_summary=executive_summary,
            metric_analyses=metric_analyses,
        )

    async def _analyze_metric(
        self,
        metric_name: str,
        score: float,
        threshold: float,
    ) -> LLMReportSection:
        """개별 메트릭 분석."""
        # 프롬프트 선택
        prompt_template = METRIC_ANALYSIS_PROMPTS.get(metric_name, DEFAULT_METRIC_PROMPT)

        # 상태 계산
        status = "통과" if score >= threshold else "미달"

        prompt = prompt_template.format(
            metric_name=metric_name,
            score=score,
            threshold=threshold,
            status=status,
        )

        try:
            # LLM adapter의 agenerate_text 사용
            content = await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to analyze metric {metric_name}: {e}")
            content = f"*분석 생성 실패: {e}*"

        return LLMReportSection(
            title=f"{metric_name} 분석",
            content=content,
            metric_name=metric_name,
            score=score,
            threshold=threshold,
        )

    async def _generate_executive_summary(
        self,
        run: EvaluationRun,
        metrics_scores: dict[str, float],
        thresholds: dict[str, float],
    ) -> str:
        """Executive Summary 생성."""
        # 메트릭 요약 문자열 생성
        metrics_lines = []
        for metric, score in metrics_scores.items():
            threshold = thresholds.get(metric, 0.7)
            status = "✅" if score >= threshold else "❌"
            metrics_lines.append(f"- {metric}: {score:.3f} (임계값: {threshold:.2f}) {status}")

        metrics_summary = "\n".join(metrics_lines)

        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            dataset_name=run.dataset_name,
            model_name=run.model_name,
            pass_rate=run.pass_rate,
            total_test_cases=run.total_test_cases,
            metrics_summary=metrics_summary,
        )

        try:
            # LLM adapter의 agenerate_text 사용
            return await self._llm_adapter.agenerate_text(prompt)
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return f"*Executive Summary 생성 실패: {e}*"

    def generate_report_sync(
        self,
        run: EvaluationRun,
        *,
        metrics_to_analyze: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> LLMReport:
        """동기 방식 보고서 생성 (Streamlit 호환)."""
        return asyncio.run(
            self.generate_report(
                run,
                metrics_to_analyze=metrics_to_analyze,
                thresholds=thresholds,
            )
        )
