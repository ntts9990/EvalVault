"""Unit tests for InsightGenerator."""

from evalvault.adapters.outbound.improvement.insight_generator import (
    BatchPatternInsight,
    InsightGenerator,
    LLMInsight,
)
from evalvault.domain.entities.improvement import (
    FailureSample,
    PatternType,
)


class TestLLMInsight:
    """LLMInsight 테스트."""

    def test_to_dict(self):
        """딕셔너리 변환."""
        insight = LLMInsight(
            failure_reason="컨텍스트에 없는 정보 생성",
            pattern_type="hallucination",
            root_causes=["Temperature가 높음", "프롬프트 부족"],
            improvement_suggestions=[{"component": "generator", "action": "Temperature 감소"}],
            suggested_answer="수정된 답변",
            confidence=0.85,
        )

        result = insight.to_dict()

        assert result["failure_reason"] == "컨텍스트에 없는 정보 생성"
        assert result["pattern_type"] == "hallucination"
        assert len(result["root_causes"]) == 2
        assert result["confidence"] == 0.85


class TestBatchPatternInsight:
    """BatchPatternInsight 테스트."""

    def test_to_dict(self):
        """딕셔너리 변환."""
        insight = BatchPatternInsight(
            common_patterns=[{"pattern_type": "hallucination", "affected_ratio": 0.6}],
            root_causes=[{"cause": "Temperature", "evidence": "높은 창의성"}],
            prioritized_improvements=[
                {"priority": 1, "component": "generator", "action": "Temperature 감소"}
            ],
            overall_assessment="전체적으로 hallucination 문제가 심각함",
            confidence=0.8,
        )

        result = insight.to_dict()

        assert len(result["common_patterns"]) == 1
        assert result["overall_assessment"] == "전체적으로 hallucination 문제가 심각함"
        assert result["confidence"] == 0.8


class TestInsightGenerator:
    """InsightGenerator 테스트."""

    def test_init_without_llm(self):
        """LLM 없이 초기화."""
        generator = InsightGenerator()

        assert not generator.is_llm_enabled

    def test_init_with_llm_disabled(self):
        """LLM 비활성화."""
        generator = InsightGenerator(enable_llm_analysis=False)

        assert not generator.is_llm_enabled

    def test_fallback_single_analysis_faithfulness(self):
        """LLM 없이 faithfulness 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"faithfulness": 0.3},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "hallucination"
        assert "충실하지 않음" in insight.failure_reason
        assert insight.confidence == 0.3

    def test_fallback_single_analysis_context_precision(self):
        """LLM 없이 context_precision 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"context_precision": 0.3},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "irrelevant_context"
        assert insight.confidence == 0.3

    def test_fallback_single_analysis_context_recall(self):
        """LLM 없이 context_recall 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"context_recall": 0.3},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "missing_context"

    def test_fallback_single_analysis_answer_relevancy(self):
        """LLM 없이 answer_relevancy 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"answer_relevancy": 0.3},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "off_topic_response"

    def test_fallback_single_analysis_summary_faithfulness(self):
        """LLM 없이 summary_faithfulness 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"summary_faithfulness": 0.3},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "hallucination"
        assert "충실하지 않음" in insight.failure_reason

    def test_fallback_single_analysis_summary_score(self):
        """LLM 없이 summary_score 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"summary_score": 0.4},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "incomplete_answer"
        assert "요약 핵심 정보" in insight.failure_reason

    def test_fallback_single_analysis_entity_preservation(self):
        """LLM 없이 entity_preservation 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"entity_preservation": 0.4},
        )

        insight = generator._fallback_single_analysis(failure)

        assert insight.pattern_type == "incomplete_answer"
        assert "핵심 엔티티" in insight.failure_reason

    def test_fallback_batch_analysis_faithfulness(self):
        """LLM 없이 faithfulness 배치 분석."""
        generator = InsightGenerator()

        failures = [
            FailureSample(
                test_case_id=f"tc-{i:03d}",
                question=f"질문 {i}",
                answer=f"답변 {i}",
                contexts=["컨텍스트"],
                metric_scores={"faithfulness": 0.4},
                detected_patterns=[PatternType.HALLUCINATION],
            )
            for i in range(5)
        ]

        insight = generator._fallback_batch_analysis(failures, "faithfulness")

        assert len(insight.common_patterns) > 0
        assert insight.prioritized_improvements[0]["component"] == "generator"
        assert insight.confidence == 0.3

    def test_fallback_batch_analysis_context_precision(self):
        """LLM 없이 context_precision 배치 분석."""
        generator = InsightGenerator()

        failures = [
            FailureSample(
                test_case_id=f"tc-{i:03d}",
                question=f"질문 {i}",
                answer=f"답변 {i}",
                contexts=["컨텍스트"],
                metric_scores={"context_precision": 0.4},
            )
            for i in range(5)
        ]

        insight = generator._fallback_batch_analysis(failures, "context_precision")

        assert insight.prioritized_improvements[0]["component"] == "retriever"
        assert "Reranker" in insight.prioritized_improvements[0]["action"]

    def test_fallback_batch_analysis_summary_score(self):
        """LLM 없이 summary_score 배치 분석."""
        generator = InsightGenerator()

        failures = [
            FailureSample(
                test_case_id=f"tc-{i:03d}",
                question=f"질문 {i}",
                answer=f"답변 {i}",
                contexts=["컨텍스트"],
                metric_scores={"summary_score": 0.4},
            )
            for i in range(5)
        ]

        insight = generator._fallback_batch_analysis(failures, "summary_score")

        assert insight.prioritized_improvements[0]["component"] == "prompt"
        assert "체크리스트" in insight.prioritized_improvements[0]["action"]

    def test_analyze_single_failure_no_llm(self):
        """LLM 없이 단일 실패 분석."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"faithfulness": 0.3},
        )

        insight = generator.analyze_single_failure(failure)

        assert insight.pattern_type == "hallucination"
        assert insight.confidence > 0

    def test_enrich_failure_sample_no_llm(self):
        """LLM 없이 실패 샘플 보강."""
        generator = InsightGenerator()

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"faithfulness": 0.3},
        )

        enriched = generator.enrich_failure_sample(failure)

        # LLM이 없으면 원본 그대로 반환
        assert enriched.test_case_id == "tc-001"

    def test_extract_json_with_code_block(self):
        """JSON 블록 추출 (코드 블록)."""
        generator = InsightGenerator()

        text = """Some text
```json
{"key": "value"}
```
More text"""

        result = generator._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_without_block(self):
        """JSON 블록 추출 (직접)."""
        generator = InsightGenerator()

        text = 'Here is the result: {"key": "value"} and more'

        result = generator._extract_json(text)
        assert '{"key": "value"}' in result

    def test_extract_json_no_json(self):
        """JSON 없는 경우."""
        generator = InsightGenerator()

        text = "No JSON here"

        result = generator._extract_json(text)
        assert result is None


class TestInsightGeneratorWithMockLLM:
    """Mock LLM을 사용한 InsightGenerator 테스트."""

    def test_analyze_with_mock_llm(self):
        """Mock LLM으로 분석."""

        class MockLLMAdapter:
            def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
                return """
```json
{
  "failure_reason": "Mock 분석 결과",
  "pattern_type": "hallucination",
  "root_causes": ["원인1"],
  "improvement_suggestions": [
    {"component": "generator", "action": "Temperature 감소", "expected_impact": "10%"}
  ],
  "suggested_answer": "개선된 답변",
  "confidence": 0.9
}
```
"""

        generator = InsightGenerator(llm_adapter=MockLLMAdapter())

        failure = FailureSample(
            test_case_id="tc-001",
            question="질문",
            answer="답변",
            contexts=["컨텍스트"],
            metric_scores={"faithfulness": 0.3},
        )

        insight = generator.analyze_single_failure(failure)

        assert insight.failure_reason == "Mock 분석 결과"
        assert insight.pattern_type == "hallucination"
        assert insight.confidence == 0.9

    def test_batch_analyze_with_mock_llm(self):
        """Mock LLM으로 배치 분석."""

        class MockLLMAdapter:
            def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
                return """
```json
{
  "common_patterns": [
    {"pattern_type": "hallucination", "description": "할루시네이션", "affected_ratio": 0.6}
  ],
  "root_causes": [{"cause": "Temperature", "evidence": "높음"}],
  "prioritized_improvements": [
    {"priority": 1, "component": "generator", "action": "Temperature 감소", "expected_improvement": 0.15, "effort": "low"}
  ],
  "overall_assessment": "Mock 평가",
  "confidence": 0.85
}
```
"""

        generator = InsightGenerator(llm_adapter=MockLLMAdapter())

        failures = [
            FailureSample(
                test_case_id=f"tc-{i:03d}",
                question=f"질문 {i}",
                answer=f"답변 {i}",
                contexts=["컨텍스트"],
                metric_scores={"faithfulness": 0.4},
            )
            for i in range(3)
        ]

        insight = generator.analyze_batch_failures(
            failures=failures,
            metric_name="faithfulness",
            avg_score=0.4,
            threshold=0.7,
        )

        assert insight.overall_assessment == "Mock 평가"
        assert insight.confidence == 0.85
        assert len(insight.prioritized_improvements) == 1
