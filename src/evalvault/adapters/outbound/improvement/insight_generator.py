"""LLM-based insight generator for RAG improvement.

규칙으로 탐지하기 어려운 패턴을 LLM을 사용하여 분석하고
깊은 인사이트와 개선 제안을 생성합니다.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from evalvault.domain.entities.improvement import (
    EvidenceSource,
    FailureSample,
    PatternType,
)
from evalvault.ports.outbound.improvement_port import ClaimImprovementProtocol

if TYPE_CHECKING:
    from evalvault.ports.outbound import LLMPort
    from evalvault.ports.outbound.improvement_port import ClaimImprovementProtocol

logger = logging.getLogger(__name__)


# 프롬프트 템플릿
FAILURE_ANALYSIS_PROMPT = """당신은 RAG(Retrieval-Augmented Generation) 시스템 전문가입니다.
다음 실패 사례를 분석하고 근본 원인과 개선 방안을 제시해주세요.

## 실패 사례

**질문**: {question}

**시스템 답변**: {answer}

**검색된 컨텍스트**:
{contexts}

**정답 (ground_truth)**: {ground_truth}

**메트릭 점수**:
{metric_scores}

## 분석 요청

1. **실패 원인 분석**: 왜 이 답변이 낮은 점수를 받았는지 분석해주세요.
2. **패턴 식별**: 이 실패가 어떤 유형에 해당하는지 식별해주세요.
   - hallucination: 컨텍스트에 없는 정보 생성
   - missing_context: 필요한 정보가 검색되지 않음
   - irrelevant_context: 관련 없는 컨텍스트 검색
   - incomplete_answer: 불완전한 답변
   - off_topic_response: 주제 이탈
   - reasoning_failure: 추론 실패
3. **개선 제안**: 이 문제를 해결하기 위한 구체적인 개선 방안을 제시해주세요.
4. **이상적인 답변**: 이 질문에 대한 이상적인 답변을 작성해주세요.

## 응답 형식 (JSON)

```json
{{
  "failure_reason": "실패 원인 설명",
  "pattern_type": "패턴 유형 (위 목록 중 하나)",
  "root_causes": ["근본 원인 1", "근본 원인 2"],
  "improvement_suggestions": [
    {{
      "component": "retriever|generator|chunker|embedder|prompt",
      "action": "구체적인 개선 액션",
      "expected_impact": "예상 효과"
    }}
  ],
  "suggested_answer": "이상적인 답변",
  "confidence": 0.85
}}
```
"""

BATCH_PATTERN_ANALYSIS_PROMPT = """당신은 RAG 시스템 분석 전문가입니다.
다음은 동일한 메트릭에서 낮은 점수를 받은 여러 실패 사례입니다.
이 사례들의 공통 패턴을 분석해주세요.

## 대상 메트릭: {metric_name}
## 평균 점수: {avg_score:.3f}
## 목표 점수: {threshold:.2f}

## 실패 사례들

{failure_cases}

## 분석 요청

1. **공통 패턴**: 이 실패 사례들에서 발견되는 공통적인 문제 패턴은 무엇인가요?
2. **근본 원인**: 이러한 패턴이 발생하는 근본적인 원인은 무엇인가요?
3. **우선순위 개선안**: 가장 효과적인 개선 방안을 우선순위 순으로 제시해주세요.
4. **예상 개선폭**: 각 개선안을 적용했을 때 예상되는 점수 개선폭은?

## 응답 형식 (JSON)

```json
{{
  "common_patterns": [
    {{
      "pattern_type": "패턴 유형",
      "description": "패턴 설명",
      "affected_ratio": 0.6
    }}
  ],
  "root_causes": [
    {{
      "cause": "근본 원인",
      "evidence": "증거"
    }}
  ],
  "prioritized_improvements": [
    {{
      "priority": 1,
      "component": "컴포넌트",
      "action": "개선 액션",
      "expected_improvement": 0.15,
      "effort": "low|medium|high"
    }}
  ],
  "overall_assessment": "전체 평가",
  "confidence": 0.85
}}
```
"""


@dataclass
class LLMInsight:
    """LLM 분석 결과."""

    failure_reason: str = ""
    pattern_type: str = ""
    root_causes: list[str] = field(default_factory=list)
    improvement_suggestions: list[dict[str, str]] = field(default_factory=list)
    suggested_answer: str | None = None
    confidence: float = 0.0
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "failure_reason": self.failure_reason,
            "pattern_type": self.pattern_type,
            "root_causes": self.root_causes,
            "improvement_suggestions": self.improvement_suggestions,
            "suggested_answer": self.suggested_answer,
            "confidence": self.confidence,
        }


@dataclass
class BatchPatternInsight(ClaimImprovementProtocol):
    """배치 패턴 분석 결과."""

    common_patterns: list[dict[str, Any]] = field(default_factory=list)
    root_causes: list[dict[str, str]] = field(default_factory=list)
    prioritized_improvements: Sequence[Mapping[str, Any]] = field(default_factory=list)
    overall_assessment: str | None = None
    confidence: float | None = None
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "common_patterns": self.common_patterns,
            "root_causes": self.root_causes,
            "prioritized_improvements": self.prioritized_improvements,
            "overall_assessment": self.overall_assessment,
            "confidence": self.confidence,
        }


class InsightGenerator:
    """LLM 기반 인사이트 생성기.

    실패 사례를 분석하여 깊은 인사이트를 생성합니다.
    규칙 기반 탐지와 결합하여 하이브리드 분석을 제공합니다.
    """

    def __init__(
        self,
        llm_adapter: LLMPort | None = None,
        *,
        max_samples_per_analysis: int = 5,
        enable_llm_analysis: bool = True,
    ):
        """초기화.

        Args:
            llm_adapter: LLM 어댑터 (None이면 LLM 분석 비활성화)
            max_samples_per_analysis: 배치 분석 시 최대 샘플 수
            enable_llm_analysis: LLM 분석 활성화 여부
        """
        self._llm_adapter = llm_adapter
        self._max_samples = max_samples_per_analysis
        self._enable_llm = enable_llm_analysis and llm_adapter is not None

    @property
    def is_llm_enabled(self) -> bool:
        """LLM 분석 활성화 여부."""
        return self._enable_llm

    def analyze_single_failure(
        self,
        failure: FailureSample,
    ) -> LLMInsight:
        """단일 실패 사례 분석.

        Args:
            failure: 분석할 실패 사례

        Returns:
            LLMInsight 분석 결과
        """
        if not self._enable_llm:
            return self._fallback_single_analysis(failure)

        # 프롬프트 구성
        contexts_text = "\n".join(
            f"[{i + 1}] {ctx[:500]}..." if len(ctx) > 500 else f"[{i + 1}] {ctx}"
            for i, ctx in enumerate(failure.contexts)
        )

        metric_scores_text = "\n".join(
            f"- {name}: {score:.3f}" for name, score in failure.metric_scores.items()
        )

        prompt = FAILURE_ANALYSIS_PROMPT.format(
            question=failure.question,
            answer=failure.answer,
            contexts=contexts_text or "(없음)",
            ground_truth=failure.ground_truth or "(없음)",
            metric_scores=metric_scores_text or "(없음)",
        )

        llm_adapter = self._llm_adapter
        if llm_adapter is None:
            return self._fallback_single_analysis(failure)
        assert llm_adapter is not None

        try:
            response = llm_adapter.generate_text(prompt, json_mode=True)
            return self._parse_single_response(response)
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return self._fallback_single_analysis(failure)

    def analyze_batch_failures(
        self,
        failures: Sequence[FailureSample],
        metric_name: str,
        avg_score: float,
        threshold: float,
    ) -> ClaimImprovementProtocol:
        """배치 실패 사례 분석.

        Args:
            failures: 분석할 실패 사례 목록
            metric_name: 대상 메트릭
            avg_score: 평균 점수
            threshold: 목표 점수

        Returns:
            BatchPatternInsight 분석 결과
        """
        if not self._enable_llm:
            return self._fallback_batch_analysis(failures, metric_name)

        # 샘플 수 제한
        sample_failures = list(failures)[: self._max_samples]

        # 실패 사례 텍스트 구성
        cases_text = []
        for i, f in enumerate(sample_failures, 1):
            case_text = f"""
### 사례 {i}
- **질문**: {f.question[:200]}{"..." if len(f.question) > 200 else ""}
- **답변**: {f.answer[:200]}{"..." if len(f.answer) > 200 else ""}
- **점수**: {f.metric_scores.get(metric_name, 0):.3f}
- **컨텍스트 수**: {len(f.contexts)}
"""
            cases_text.append(case_text)

        prompt = BATCH_PATTERN_ANALYSIS_PROMPT.format(
            metric_name=metric_name,
            avg_score=avg_score,
            threshold=threshold,
            failure_cases="\n".join(cases_text),
        )

        llm_adapter = self._llm_adapter
        if llm_adapter is None:
            return self._fallback_batch_analysis(failures, metric_name)
        assert llm_adapter is not None

        try:
            response = llm_adapter.generate_text(prompt, json_mode=True)
            return self._parse_batch_response(response)
        except Exception as e:
            logger.warning(f"LLM batch analysis failed: {e}")
            return self._fallback_batch_analysis(failures, metric_name)

    def enrich_failure_sample(
        self,
        failure: FailureSample,
    ) -> FailureSample:
        """실패 샘플에 LLM 분석 결과 추가.

        Args:
            failure: 원본 실패 샘플

        Returns:
            LLM 분석 결과가 추가된 실패 샘플
        """
        if not self._enable_llm:
            return failure

        insight = self.analyze_single_failure(failure)

        # 실패 샘플 업데이트
        failure.failure_reason = insight.failure_reason or failure.failure_reason
        failure.suggested_answer = insight.suggested_answer
        failure.analysis_source = EvidenceSource.LLM_ANALYSIS

        # 패턴 타입 추가
        if insight.pattern_type:
            try:
                pattern = PatternType(insight.pattern_type)
                if pattern not in failure.detected_patterns:
                    failure.detected_patterns.append(pattern)
            except ValueError:
                pass

        return failure

    def _parse_single_response(self, response: str) -> LLMInsight:
        """단일 분석 응답 파싱."""
        insight = LLMInsight(raw_response=response)

        # JSON 블록 추출
        json_str = self._extract_json(response)
        if not json_str:
            logger.warning("No JSON found in LLM response")
            return insight

        try:
            data = json.loads(json_str)
            insight.failure_reason = data.get("failure_reason", "")
            insight.pattern_type = data.get("pattern_type", "")
            insight.root_causes = data.get("root_causes", [])
            insight.improvement_suggestions = data.get("improvement_suggestions", [])
            insight.suggested_answer = data.get("suggested_answer")
            insight.confidence = data.get("confidence", 0.5)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response JSON: {e}")

        return insight

    def _parse_batch_response(self, response: str) -> BatchPatternInsight:
        """배치 분석 응답 파싱."""
        insight = BatchPatternInsight(raw_response=response)

        json_str = self._extract_json(response)
        if not json_str:
            logger.warning("No JSON found in LLM batch response")
            return insight

        try:
            data = json.loads(json_str)
            insight.common_patterns = data.get("common_patterns", [])
            insight.root_causes = data.get("root_causes", [])
            insight.prioritized_improvements = data.get("prioritized_improvements", [])
            insight.overall_assessment = data.get("overall_assessment", "")
            insight.confidence = data.get("confidence", 0.5)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM batch response JSON: {e}")

        return insight

    def _extract_json(self, text: str) -> str | None:
        """텍스트에서 JSON 블록 추출."""
        import re

        # ```json ... ``` 패턴 찾기
        pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

        # ``` ... ``` 패턴 찾기
        pattern = r"```\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            content = match.group(1).strip()
            if content.startswith("{"):
                return content

        # { ... } 직접 찾기
        pattern = r"\{[\s\S]*\}"
        match = re.search(pattern, text)
        if match:
            return match.group(0)

        return None

    def _fallback_single_analysis(self, failure: FailureSample) -> LLMInsight:
        """LLM 없이 기본 분석 수행."""
        # 간단한 휴리스틱 기반 분석
        insight = LLMInsight()

        # 메트릭 점수 기반 패턴 추론
        scores = failure.metric_scores
        faith_score = scores.get("summary_faithfulness", scores.get("faithfulness", 1))
        if faith_score < 0.5:
            insight.pattern_type = "hallucination"
            insight.failure_reason = "답변이 컨텍스트에 충실하지 않음"
        elif scores.get("entity_preservation", 1) < 0.6:
            insight.pattern_type = "incomplete_answer"
            insight.failure_reason = "요약에 핵심 엔티티가 누락됨"
        elif scores.get("summary_score", 1) < 0.5:
            insight.pattern_type = "incomplete_answer"
            insight.failure_reason = "요약 핵심 정보가 충분히 보존되지 않음"
        elif scores.get("context_precision", 1) < 0.5:
            insight.pattern_type = "irrelevant_context"
            insight.failure_reason = "검색된 컨텍스트의 관련성이 낮음"
        elif scores.get("context_recall", 1) < 0.5:
            insight.pattern_type = "missing_context"
            insight.failure_reason = "필요한 정보가 검색되지 않음"
        elif scores.get("answer_relevancy", 1) < 0.5:
            insight.pattern_type = "off_topic_response"
            insight.failure_reason = "답변이 질문과 관련성이 낮음"
        else:
            insight.pattern_type = "unknown"
            insight.failure_reason = "구체적인 원인 분석을 위해 LLM 분석이 필요합니다"

        insight.confidence = 0.3  # 휴리스틱 기반이므로 낮은 신뢰도

        return insight

    def _fallback_batch_analysis(
        self,
        failures: Sequence[FailureSample],
        metric_name: str,
    ) -> BatchPatternInsight:
        """LLM 없이 기본 배치 분석 수행."""
        insight = BatchPatternInsight()

        # 패턴 집계
        pattern_counts: dict[str, int] = {}
        for f in failures:
            for p in f.detected_patterns:
                pattern_counts[p.value] = pattern_counts.get(p.value, 0) + 1

        # 공통 패턴 생성
        total = len(failures)
        for pattern_type, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            insight.common_patterns.append(
                {
                    "pattern_type": pattern_type,
                    "description": f"{metric_name} 관련 {pattern_type} 패턴",
                    "affected_ratio": count / total if total > 0 else 0,
                }
            )

        # 기본 개선 제안
        if metric_name in {"faithfulness", "summary_faithfulness"}:
            insight.prioritized_improvements = [
                {
                    "priority": 1,
                    "component": "generator",
                    "action": "Temperature 감소 및 프롬프트 강화",
                    "expected_improvement": 0.10,
                    "effort": "low",
                }
            ]
        elif metric_name in {"summary_score", "entity_preservation"}:
            insight.prioritized_improvements = [
                {
                    "priority": 1,
                    "component": "prompt",
                    "action": "요약 핵심 엔티티 보존 체크리스트 추가",
                    "expected_improvement": 0.12,
                    "effort": "low",
                }
            ]
        elif metric_name == "context_precision":
            insight.prioritized_improvements = [
                {
                    "priority": 1,
                    "component": "retriever",
                    "action": "Reranker 도입",
                    "expected_improvement": 0.12,
                    "effort": "medium",
                }
            ]
        elif metric_name == "context_recall":
            insight.prioritized_improvements = [
                {
                    "priority": 1,
                    "component": "retriever",
                    "action": "top_k 증가",
                    "expected_improvement": 0.15,
                    "effort": "low",
                }
            ]

        insight.overall_assessment = f"{metric_name} 개선을 위한 기본 분석 결과입니다."
        insight.confidence = 0.3

        return insight
