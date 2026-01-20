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
    "faithfulness": """당신은 RAG 시스템의 Faithfulness(충실도) 개선 전문가입니다.

## 현재 상태
- 점수: {score:.3f} / 1.0
- 목표: {threshold:.2f}
- 상태: {status}

## Faithfulness란?
답변이 컨텍스트에 있는 정보만 사용하는지 측정. 낮으면 환각(hallucination) 발생.

---

## 분석 요청

### 1. 현황 진단
- 이 점수에서 예상되는 환각 빈도
- 사용자 경험에 미치는 영향

### 2. 문제점 정의
| 가능한 문제 | 현상 | 검증 방법 |
|-------------|------|-----------|
| (예: 컨텍스트 무시) | (예: 사전지식 사용) | (예: 컨텍스트 없이 테스트) |

### 3. 원인 분석

**1차 원인 (직접적)**
- 프롬프트에서 컨텍스트 사용 강조 부족
- 컨텍스트 길이 초과로 잘림
- 관련 없는 컨텍스트로 혼란

**근본 원인 (구조적)**
- Retriever가 관련 정보를 못 찾음
- 청킹 전략으로 문맥 단절
- LLM의 지시 따르기 능력 부족

### 4. 해결 방안

#### 즉시 적용 가능 (1-2일)
```
방안 1: 프롬프트에 "오직 제공된 문서에서만 답변하세요" 명시 추가
예상 효과: +0.05~0.10
구현: system_prompt 수정

방안 2: 컨텍스트 길이 제한 및 최적화
예상 효과: +0.03~0.08
구현: max_context_length 파라미터 조정
```

#### 단기 개선 (1주)
```
방안 3: Citation 생성 강제 ("출처: [문서명]" 형식)
예상 효과: +0.10~0.15
구현: 프롬프트 + 후처리 검증

방안 4: Reranker 도입으로 컨텍스트 품질 향상
예상 효과: +0.08~0.12
구현: Cohere Rerank / BGE Reranker 추가
```

#### 중기 개선 (1개월)
```
방안 5: Self-RAG 또는 CRAG 패턴 적용
예상 효과: +0.15~0.25
구현: 답변 생성 후 자체 검증 단계 추가
```

### 5. 검증 방법
- 환각 케이스 샘플링 후 수동 검토
- 컨텍스트 없이 동일 질문 테스트하여 사전지식 의존도 확인

마크다운 형식으로 작성해주세요. **구체적 수치와 실행 방법**을 포함해야 합니다.""",
    "answer_relevancy": """당신은 RAG 시스템의 Answer Relevancy(답변 관련성) 개선 전문가입니다.

## 현재 상태
- 점수: {score:.3f} / 1.0
- 목표: {threshold:.2f}
- 상태: {status}

## Answer Relevancy란?
답변이 질문의 의도에 맞는지 측정. 낮으면 질문과 무관한 답변 생성.

---

## 분석 요청

### 1. 현황 진단
- 질문 의도 파악 실패 빈도 추정
- 사용자 만족도에 미치는 영향

### 2. 문제점 정의
| 가능한 문제 | 현상 | 검증 방법 |
|-------------|------|-----------|
| (예: 질문 이해 실패) | (예: 다른 주제로 답변) | (예: 질문 유형별 분석) |

### 3. 원인 분석

**1차 원인 (직접적)**
- 질문이 모호하거나 복합적
- 관련 없는 컨텍스트가 검색됨
- 프롬프트에서 질문 의도 강조 부족

**근본 원인 (구조적)**
- Query와 Document의 의미적 불일치
- 도메인 특화 용어 이해 부족
- 복잡한 질문 분해 능력 부족

### 4. 해결 방안

#### 즉시 적용 가능 (1-2일)
```
방안 1: 프롬프트에 "질문에 직접 답변하세요" 강조
예상 효과: +0.05~0.08
구현: "사용자의 질문: {question}에 직접적으로 답변하세요"

방안 2: 답변 시작을 질문 재확인으로 유도
예상 효과: +0.03~0.05
구현: "먼저 질문을 이해했는지 확인 후 답변"
```

#### 단기 개선 (1주)
```
방안 3: Query Rewriting 적용
예상 효과: +0.08~0.12
구현: 원본 쿼리를 명확하게 재작성 후 검색

방안 4: HyDE (Hypothetical Document Embedding) 적용
예상 효과: +0.10~0.15
구현: 가상 답변 생성 후 유사 문서 검색
```

#### 중기 개선 (1개월)
```
방안 5: Multi-Query Retrieval
예상 효과: +0.12~0.18
구현: 질문을 여러 관점으로 확장하여 검색

방안 6: 질문 유형 분류 후 맞춤 프롬프트
예상 효과: +0.10~0.15
구현: 정의형/비교형/절차형 등 분류 후 템플릿 적용
```

### 5. 검증 방법
- 질문 유형별 relevancy 점수 비교
- 저점수 케이스에서 질문-답변 매핑 수동 검토

마크다운 형식으로 작성해주세요. **구체적 수치와 실행 방법**을 포함해야 합니다.""",
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
    "summary_score": """당신은 요약 평가 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Summary Score (요약 점수)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Summary Score 메트릭 설명
Summary Score는 요약이 원문 핵심 정보를 얼마나 보존하면서 간결하게 정리되었는지 측정합니다.
낮은 점수는 정보 누락 또는 과도한 장황함을 의미할 수 있습니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 점수 해석과 요약 품질 진단
2. **주요 원인 분석**: 정보 누락/장황함/핵심 포인트 왜곡 원인
3. **개선 방안**: 요약 구조/프롬프트/컨텍스트 개선 제안
4. **검증 포인트**: 핵심 정보 보존 체크리스트 제안
5. **운영 팁**: 요약 품질 모니터링 방법

마크다운 형식으로 작성해주세요.""",
    "summary_faithfulness": """당신은 요약 평가 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Summary Faithfulness (요약 충실도)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Summary Faithfulness 메트릭 설명
Summary Faithfulness는 요약 내 주장/숫자/조건이 원문 근거와 일치하는지 측정합니다.
낮은 점수는 원문에 없는 정보가 포함되었거나 조건이 왜곡되었음을 의미합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 요약 충실도 상태 진단
2. **주요 원인 분석**: 근거 누락, 환각, 조건 반전 등 원인
3. **보험 리스크 관점**: 면책/제외/금액/기간/비율 왜곡 위험 설명
4. **개선 방안**: 근거 인용/체크리스트/검증 파이프라인 제안
5. **품질 게이트 제안**: 사용자 노출 전 확인 포인트

마크다운 형식으로 작성해주세요.""",
    "entity_preservation": """당신은 보험 요약 평가 메트릭 전문가입니다.

## 분석 대상
- 메트릭: Entity Preservation (엔티티 보존)
- 점수: {score:.3f} / 1.0
- 임계값: {threshold:.2f}
- 상태: {status}

## Entity Preservation 메트릭 설명
Entity Preservation은 요약에서 보험 핵심 엔티티(금액/기간/비율/면책/조건)가
원문과 비교해 얼마나 보존되었는지 측정합니다.

## 요청사항
다음 내용을 포함하여 전문가 관점에서 분석해주세요:

1. **현재 상태 진단**: 핵심 엔티티 보존 상태 평가
2. **주요 원인 분석**: 엔티티 누락/왜곡/치환 원인
3. **개선 방안**: 엔티티 하이라이트/보존 프롬프트/후처리 제안
4. **검증 기준**: 보험 문서에서 필수 엔티티 체크리스트
5. **운영 팁**: 엔티티 보존율 모니터링/샘플 리뷰 방법

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

DEFAULT_METRIC_PROMPT_EN = """You are a RAG evaluation expert.

## Target
- Metric: {metric_name}
- Score: {score:.3f} / 1.0
- Threshold: {threshold:.2f}
- Status: {status}

## Request
Provide a Markdown analysis covering:

1. **Current assessment**: what this score implies
2. **Likely causes**: plausible root causes
3. **Actionable improvements**: practical steps the team can take
4. **Expected impact**: anticipated gains per action

Respond in Markdown."""


EXECUTIVE_SUMMARY_PROMPT = """당신은 RAG 시스템 성능 개선 전문가입니다. 평가 결과를 분석하고 구체적인 개선 방안을 제시해주세요.

## 평가 결과
- 데이터셋: {dataset_name}
- 모델: {model_name}
- 통과율: {pass_rate:.1%}
- 테스트 케이스: {total_test_cases}개

## 메트릭별 점수
{metrics_summary}

---

## 분석 요청

다음 구조로 **RAG 성능 개선 중심** 분석을 제공해주세요:

### 1. 현황 요약 (3문장)
- 전체 품질 수준과 가장 시급한 문제
- 잘 되는 영역 vs 안 되는 영역 명확히 구분

### 2. 문제점 정의

| 문제 | 메트릭 | 현재값 | 목표값 | 심각도 |
|------|--------|--------|--------|--------|
| (구체적 현상) | (관련 메트릭) | (점수) | (목표) | Critical/High/Medium |

### 3. 근본 원인 분석

각 문제점별로:
- **1차 원인**: 직접적 원인 (예: "컨텍스트에 관련 정보가 검색되지 않음")
- **근본 원인**: 구조적 원인 (예: "청킹 크기가 너무 커서 관련 정보가 희석됨")
- **검증 방법**: 원인 확인을 위한 테스트 (예: "top_k=10으로 늘려서 재평가")

### 4. 해결 방안

#### P0 - 즉시 실행 (1-3일)
각 방안별:
- **방안**: 한 줄 설명
- **구현**: 구체적 단계 (코드/설정 변경 포함)
- **예상 효과**: 정량적 개선 예측 (예: "faithfulness +0.15 예상")

#### P1 - 단기 (1-2주)
동일 형식으로 2-3개 방안

#### P2 - 중기 (1개월)
동일 형식으로 1-2개 방안

### 5. 검증 계획
- 각 개선의 효과 측정 방법
- 회귀 방지를 위한 모니터링 지표

**주의**: 추상적 조언(예: "품질을 높이세요")은 금지. 모든 제안은 **구체적이고 실행 가능**해야 합니다.

마크다운 형식으로 작성해주세요."""

EXECUTIVE_SUMMARY_PROMPT_EN = """You are a RAG performance improvement expert. Analyze the evaluation results and propose concrete actions.

Evaluation Results:
- Dataset: {dataset_name}
- Model: {model_name}
- Pass rate: {pass_rate:.1%}
- Test cases: {total_test_cases}

Metric Scores:
{metrics_summary}

Analysis Request:

Provide a RAG performance improvement-focused analysis using the structure below:

1) Current Summary (3 sentences)
- Overall quality level and the most urgent issue
- Clearly distinguish strong areas vs weak areas

2) Problem Definition

| Problem | Metric | Current | Target | Severity |
|------|--------|--------|--------|--------|
| (Specific issue) | (Related metric) | (Score) | (Target) | Critical/High/Medium |

3) Root Cause Analysis

For each problem:
- Direct cause: immediate cause (e.g., "relevant context is not retrieved")
- Root cause: structural cause (e.g., "chunk size is too large and dilutes relevance")
- Verification: how to validate (e.g., "re-run with top_k=10")

4) Solutions

P0 - Immediate (1-3 days)
For each action:
- Action: one-line description
- Implementation: concrete steps (including code/config changes)
- Expected impact: quantified estimate (e.g., "faithfulness +0.15")

P1 - Short term (1-2 weeks)
Provide 2-3 actions in the same format

P2 - Mid term (1 month)
Provide 1-2 actions in the same format

5) Verification Plan
- How to measure improvement for each action
- Monitoring indicators to prevent regressions

Note: Do not give abstract advice. All suggestions must be concrete and actionable.

Respond in Markdown."""

SUMMARY_RECOMMENDED_THRESHOLDS = {
    "summary_faithfulness": 0.90,
    "summary_score": 0.85,
    "entity_preservation": 0.90,
    "summary_accuracy": 0.90,
    "summary_risk_coverage": 0.90,
    "summary_non_definitive": 0.80,
    "summary_needs_followup": 0.80,
}
SUMMARY_METRIC_ORDER = (
    "summary_faithfulness",
    "summary_score",
    "entity_preservation",
    "summary_accuracy",
    "summary_risk_coverage",
    "summary_non_definitive",
    "summary_needs_followup",
)


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
        summary_notice = _build_summary_notice(self.metric_analyses)
        lines = [
            f"# RAG 평가 보고서: {self.dataset_name}",
            "",
            f"> 생성일시: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 모델: {self.model_name}",
            "",
            "---",
            "",
            "## 요약",
            "",
            self.executive_summary,
            "",
            "---",
            "",
        ]

        if summary_notice:
            lines.extend(
                [
                    "## 요약 평가 주의사항",
                    "",
                    summary_notice,
                    "",
                    "---",
                    "",
                ]
            )

        for section in self.metric_analyses:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                ]
            )
            if section.score is not None and section.threshold is not None:
                status = "✅ 통과" if section.score >= section.threshold else "❌ 실패"
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
                "*EvalVault v1.3.0 | Ragas + LLM 분석 기반*",
            ]
        )

        return "\n".join(lines)


def _build_summary_notice(sections: list[LLMReportSection]) -> str | None:
    summary_scores = {
        section.metric_name: section.score
        for section in sections
        if section.metric_name in SUMMARY_RECOMMENDED_THRESHOLDS and section.score is not None
    }
    if not summary_scores:
        return None

    threshold_line = ", ".join(
        f"{metric}>={SUMMARY_RECOMMENDED_THRESHOLDS[metric]:.2f}"
        for metric in SUMMARY_METRIC_ORDER
        if metric in SUMMARY_RECOMMENDED_THRESHOLDS
    )
    warnings = [
        f"- {metric}: {score:.3f} < {SUMMARY_RECOMMENDED_THRESHOLDS[metric]:.2f}"
        for metric, score in summary_scores.items()
        if score < SUMMARY_RECOMMENDED_THRESHOLDS[metric]
    ]

    lines = []
    if warnings:
        lines.append("**기준 미달 메트릭**")
        lines.extend(warnings)
        lines.append("")
    lines.extend(
        [
            f"- 사용자 노출 권장 기준: {threshold_line}",
            "- 혼용 언어/temperature 변동으로 점수가 흔들릴 수 있어 다회 실행 평균 확인 권장.",
            "- 참고 문서: docs/guides/RAGAS_PERFORMANCE_TUNING.md, "
            "docs/internal/reports/TEMPERATURE_SEED_ANALYSIS.md",
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
        prompt_template = (
            DEFAULT_METRIC_PROMPT_EN
            if self._language == "en"
            else METRIC_ANALYSIS_PROMPTS.get(metric_name, DEFAULT_METRIC_PROMPT)
        )

        status = "pass" if score >= threshold else "fail"
        if self._language != "en":
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
            if self._language == "en":
                metrics_lines.append(
                    f"- {metric}: {score:.3f} (threshold: {threshold:.2f}) {status}"
                )
            else:
                metrics_lines.append(f"- {metric}: {score:.3f} (임계값: {threshold:.2f}) {status}")

        metrics_summary = "\n".join(metrics_lines)

        prompt_template = (
            EXECUTIVE_SUMMARY_PROMPT_EN if self._language == "en" else EXECUTIVE_SUMMARY_PROMPT
        )
        prompt = prompt_template.format(
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
            return f"*요약 생성 실패: {e}*"

    def generate_report_sync(
        self,
        run: EvaluationRun,
        *,
        metrics_to_analyze: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> LLMReport:
        """동기 방식 보고서 생성."""
        return asyncio.run(
            self.generate_report(
                run,
                metrics_to_analyze=metrics_to_analyze,
                thresholds=thresholds,
            )
        )
