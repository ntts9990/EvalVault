"""Unit tests for ImprovementGuideService."""

from datetime import datetime

from evalvault.adapters.outbound.improvement.insight_generator import InsightGenerator
from evalvault.adapters.outbound.improvement.pattern_detector import PatternDetector
from evalvault.adapters.outbound.improvement.playbook_loader import get_default_playbook
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.improvement import (
    EvidenceSource,
    ImprovementPriority,
    RAGComponent,
)
from evalvault.domain.entities.stage import StageMetric
from evalvault.domain.services.improvement_guide_service import ImprovementGuideService


def create_test_run(
    num_cases: int = 20,
    faithfulness_scores: list[float] | None = None,
    context_precision_scores: list[float] | None = None,
) -> EvaluationRun:
    """테스트용 EvaluationRun 생성."""
    results = []

    for i in range(num_cases):
        faithfulness = (
            faithfulness_scores[i]
            if faithfulness_scores and i < len(faithfulness_scores)
            else 0.5 + (i % 5) * 0.1
        )
        precision = (
            context_precision_scores[i]
            if context_precision_scores and i < len(context_precision_scores)
            else 0.4 + (i % 6) * 0.1
        )

        result = TestCaseResult(
            test_case_id=f"tc-{i:03d}",
            metrics=[
                MetricScore(name="faithfulness", score=faithfulness),
                MetricScore(name="context_precision", score=precision),
            ],
            question="이 보험의 보장금액은 얼마인가요?" * (1 + i % 3),
            answer="보장금액은 1억원입니다." * (1 + i % 2),
            contexts=[f"컨텍스트 {j}" for j in range(3)],
            ground_truth="1억원",
        )
        results.append(result)

    return EvaluationRun(
        run_id="test-run-001",
        dataset_name="test-dataset",
        results=results,
        metrics_evaluated=["faithfulness", "context_precision"],
        thresholds={"faithfulness": 0.7, "context_precision": 0.7},
        started_at=datetime.now(),
    )


class TestImprovementGuideService:
    """ImprovementGuideService 테스트."""

    def test_init(self):
        """초기화."""
        detector = PatternDetector()
        generator = InsightGenerator()

        service = ImprovementGuideService(
            pattern_detector=detector,
            insight_generator=generator,
        )

        assert service._detector is detector
        assert service._generator is generator

    def test_init_without_llm(self):
        """LLM 없이 초기화."""
        detector = PatternDetector()

        service = ImprovementGuideService(
            pattern_detector=detector,
            insight_generator=None,
        )

        assert service._generator is None
        assert not service._enable_llm

    def test_generate_report_basic(self):
        """기본 리포트 생성."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        run = create_test_run(num_cases=20)
        report = service.generate_report(run)

        assert report.run_id == "test-run-001"
        assert report.total_test_cases == 20
        assert "faithfulness" in report.metric_scores
        assert "context_precision" in report.metric_scores
        assert EvidenceSource.RULE_BASED in report.analysis_methods_used

    def test_generate_report_with_low_scores(self):
        """낮은 점수로 리포트 생성."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        # 모든 케이스에 낮은 faithfulness 점수
        scores = [0.4] * 20  # 평균 0.4, threshold 0.7
        run = create_test_run(num_cases=20, faithfulness_scores=scores)

        report = service.generate_report(run)

        # 평균이 threshold보다 낮으면 gap > 0
        assert report.metric_gaps.get("faithfulness", 0) > 0

    def test_generate_report_metric_filter(self):
        """특정 메트릭만 분석."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        run = create_test_run(num_cases=20)
        report = service.generate_report(run, metrics=["faithfulness"])

        assert "faithfulness" in report.metric_scores
        # context_precision은 분석에 포함되지 않을 수 있음

    def test_generate_report_with_stage_metrics(self):
        """StageMetric 기반 가이드 생성."""
        detector = PatternDetector(min_sample_size=999)
        stage_metric_playbook = {
            "retrieval.recall_at_k": {
                "title": "Custom recall improvement",
                "expected_improvement": 0.2,
                "expected_improvement_range": [0.1, 0.3],
                "effort": "high",
            }
        }
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
            stage_metric_playbook=stage_metric_playbook,
        )

        run = create_test_run(num_cases=5)
        stage_metrics = [
            StageMetric(
                run_id=run.run_id,
                stage_id="stg-retrieval-01",
                metric_name="retrieval.recall_at_k",
                score=0.4,
                threshold=0.6,
            )
        ]

        report = service.generate_report(run, stage_metrics=stage_metrics)
        retriever_guides = [
            guide for guide in report.guides if guide.component == RAGComponent.RETRIEVER
        ]
        assert retriever_guides
        assert retriever_guides[0].actions[0].title == "Custom recall improvement"
        stage_summary = report.metadata.get("stage_metrics_summary")
        assert stage_summary is not None
        assert stage_summary["total"] == 1
        assert stage_summary["failed"] == 1
        assert stage_summary["pass_rate"] == 0.0
        assert stage_summary["top_failures"][0]["metric_name"] == "retrieval.recall_at_k"

        markdown = report.to_markdown()
        assert "단계 메트릭 요약" in markdown

    def test_generate_report_markdown(self):
        """마크다운 리포트 생성."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        run = create_test_run(num_cases=20)
        report = service.generate_report(run)
        markdown = report.to_markdown()

        assert "# RAG 개선 가이드 리포트" in markdown
        assert "## 요약" in markdown
        assert "faithfulness" in markdown or "context_precision" in markdown

    def test_generate_quick_analysis(self):
        """빠른 분석."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        run = create_test_run(num_cases=20)
        quick = service.generate_quick_analysis(run)

        # 결과는 dict[str, list[str]]
        assert isinstance(quick, dict)

    def test_convert_priority(self):
        """우선순위 변환."""
        detector = PatternDetector()
        service = ImprovementGuideService(pattern_detector=detector)

        assert service._convert_priority("p0_critical") == ImprovementPriority.P0_CRITICAL
        assert service._convert_priority("p1_high") == ImprovementPriority.P1_HIGH
        assert service._convert_priority("p2_medium") == ImprovementPriority.P2_MEDIUM
        assert service._convert_priority("p3_low") == ImprovementPriority.P3_LOW
        assert service._convert_priority("unknown") == ImprovementPriority.P2_MEDIUM

    def test_sort_guides(self):
        """가이드 정렬."""
        from evalvault.domain.entities.improvement import RAGImprovementGuide

        detector = PatternDetector()
        service = ImprovementGuideService(pattern_detector=detector)

        guides = [
            RAGImprovementGuide(priority=ImprovementPriority.P3_LOW),
            RAGImprovementGuide(priority=ImprovementPriority.P0_CRITICAL),
            RAGImprovementGuide(priority=ImprovementPriority.P1_HIGH),
        ]

        sorted_guides = service._sort_guides(guides)

        assert sorted_guides[0].priority == ImprovementPriority.P0_CRITICAL
        assert sorted_guides[1].priority == ImprovementPriority.P1_HIGH
        assert sorted_guides[2].priority == ImprovementPriority.P3_LOW

    def test_generate_verification_command(self):
        """검증 명령어 생성."""
        detector = PatternDetector()
        service = ImprovementGuideService(pattern_detector=detector)

        cmd = service._generate_verification_command("faithfulness", "run-001")

        assert "evalvault run" in cmd
        assert "faithfulness" in cmd
        assert "compare" in cmd

    def test_find_pattern_definition(self):
        """패턴 정의 찾기."""
        playbook = get_default_playbook()
        detector = PatternDetector(playbook=playbook)
        service = ImprovementGuideService(
            pattern_detector=detector,
            playbook=playbook,
        )

        # faithfulness의 hallucination 패턴
        pattern_def = service._find_pattern_definition("faithfulness", "hallucination")
        assert pattern_def is not None
        assert pattern_def.pattern_id == "hallucination"

        # 존재하지 않는 패턴
        pattern_def = service._find_pattern_definition("faithfulness", "nonexistent")
        assert pattern_def is None


class TestImprovementGuideServiceWithMockLLM:
    """Mock LLM을 사용한 테스트."""

    def test_generate_report_with_llm(self):
        """LLM으로 리포트 생성."""

        class MockLLMAdapter:
            def generate_text(self, prompt: str) -> str:
                return """
```json
{
  "failure_reason": "Mock 분석",
  "pattern_type": "hallucination",
  "root_causes": ["원인1"],
  "improvement_suggestions": [
    {"component": "generator", "action": "Temperature 감소"}
  ],
  "suggested_answer": "개선된 답변",
  "confidence": 0.9
}
```
"""

        detector = PatternDetector(min_sample_size=3)
        generator = InsightGenerator(llm_adapter=MockLLMAdapter())
        service = ImprovementGuideService(
            pattern_detector=detector,
            insight_generator=generator,
            enable_llm_enrichment=True,
        )

        # 낮은 점수로 패턴 탐지 유도
        scores = [0.3, 0.4, 0.35, 0.45, 0.5] + [0.8] * 15
        run = create_test_run(num_cases=20, faithfulness_scores=scores)

        report = service.generate_report(run, include_llm_analysis=True)

        assert EvidenceSource.RULE_BASED in report.analysis_methods_used


class TestImprovementReport:
    """ImprovementReport 테스트."""

    def test_to_dict(self):
        """딕셔너리 변환."""
        detector = PatternDetector(min_sample_size=3)
        service = ImprovementGuideService(
            pattern_detector=detector,
            enable_llm_enrichment=False,
        )

        run = create_test_run(num_cases=20)
        report = service.generate_report(run)

        result = report.to_dict()

        assert "run_id" in result
        assert "metric_scores" in result
        assert "guides" in result

    def test_get_guides_by_metric(self):
        """메트릭별 가이드 조회."""
        from evalvault.domain.entities.improvement import (
            ImprovementReport,
            RAGImprovementGuide,
        )

        report = ImprovementReport(
            run_id="test",
            guides=[
                RAGImprovementGuide(target_metrics=["faithfulness"]),
                RAGImprovementGuide(target_metrics=["context_precision"]),
                RAGImprovementGuide(target_metrics=["faithfulness", "answer_relevancy"]),
            ],
        )

        faithfulness_guides = report.get_guides_by_metric("faithfulness")
        assert len(faithfulness_guides) == 2

        precision_guides = report.get_guides_by_metric("context_precision")
        assert len(precision_guides) == 1

    def test_get_critical_guides(self):
        """Critical 가이드 조회."""
        from evalvault.domain.entities.improvement import (
            ImprovementReport,
            RAGImprovementGuide,
        )

        report = ImprovementReport(
            run_id="test",
            guides=[
                RAGImprovementGuide(priority=ImprovementPriority.P0_CRITICAL),
                RAGImprovementGuide(priority=ImprovementPriority.P1_HIGH),
                RAGImprovementGuide(priority=ImprovementPriority.P0_CRITICAL),
            ],
        )

        critical = report.get_critical_guides()
        assert len(critical) == 2
