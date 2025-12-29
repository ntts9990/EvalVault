#!/usr/bin/env python3
"""EvalVault 종합 워크플로우 테스트.

보험 도메인 RAG 시스템 평가를 위한 전체 기능 통합 테스트입니다.
Domain Memory, NLP 분석, 인과 분석, 보고서 생성 기능을 유기적으로 연결합니다.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# EvalVault 모듈 임포트
from evalvault.adapters.outbound.analysis.causal_adapter import CausalAnalysisAdapter
from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
    SQLiteDomainMemoryAdapter,
)
from evalvault.adapters.outbound.report.markdown_adapter import MarkdownReportAdapter
from evalvault.domain.entities.analysis import AnalysisBundle
from evalvault.domain.entities.memory import FactualFact
from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.services.domain_learning_hook import DomainLearningHook

# 상수
SCRIPT_DIR = Path(__file__).parent
DATASET_PATH = SCRIPT_DIR / "insurance_eval_dataset.json"
OUTPUT_DIR = SCRIPT_DIR / "output"
DB_PATH = OUTPUT_DIR / "evalvault_memory.db"
REPORT_PATH = OUTPUT_DIR / "comprehensive_report.html"


def load_dataset(path: Path) -> dict[str, Any]:
    """데이터셋 로드."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def simulate_evaluation_run(
    dataset: dict,
    run_id: str,
    variation: str = "normal",
    timestamp: datetime | None = None,
) -> EvaluationRun:
    """평가 실행을 시뮬레이션합니다.

    실제 LLM 호출 없이 다양한 시나리오의 평가 결과를 생성합니다.

    Args:
        dataset: 데이터셋 딕셔너리
        run_id: 평가 실행 ID
        variation: 시나리오 유형 (normal, improved, degraded)
        timestamp: 평가 시점 (기본: 현재)
    """
    import random

    # 시드 설정으로 재현 가능한 결과
    random.seed(hash(run_id) % 2**32)

    run = EvaluationRun(
        run_id=run_id,
        dataset_name=dataset["name"],
        model_name="gpt-4o-mini",
        metrics_evaluated=["faithfulness", "answer_relevancy", "context_precision"],
    )

    if timestamp:
        run.started_at = timestamp
        run.completed_at = timestamp + timedelta(minutes=5)

    # 시나리오별 점수 범위
    score_ranges = {
        "normal": (0.65, 0.95),
        "improved": (0.80, 0.98),
        "degraded": (0.45, 0.75),
    }
    min_score, max_score = score_ranges.get(variation, (0.65, 0.95))

    # 카테고리별 특성 반영
    category_modifiers = {
        "생명보험": 0.02,
        "건강보험": -0.03,
        "자동차보험": 0.01,
        "연금보험": -0.02,
        "일반": 0.0,
    }

    for tc in dataset["test_cases"]:
        category = tc.get("category", "일반")
        modifier = category_modifiers.get(category, 0.0)

        # 메트릭별 점수 생성
        base_score = random.uniform(min_score, max_score)

        metrics = [
            MetricScore(
                name="faithfulness",
                score=min(1.0, max(0.0, base_score + modifier + random.uniform(-0.1, 0.1))),
                threshold=dataset["thresholds"].get("faithfulness", 0.7),
            ),
            MetricScore(
                name="answer_relevancy",
                score=min(1.0, max(0.0, base_score + modifier + random.uniform(-0.08, 0.08))),
                threshold=dataset["thresholds"].get("answer_relevancy", 0.7),
            ),
            MetricScore(
                name="context_precision",
                score=min(1.0, max(0.0, base_score + modifier + random.uniform(-0.12, 0.12))),
                threshold=dataset["thresholds"].get("context_precision", 0.7),
            ),
        ]

        result = TestCaseResult(
            test_case_id=tc["id"],
            metrics=metrics,
            question=tc["question"],
            answer=tc["answer"],
            contexts=tc.get("contexts", []),
            ground_truth=tc.get("ground_truth"),
            tokens_used=random.randint(500, 1500),
        )
        run.results.append(result)

    return run


def create_multiple_runs_for_trend_analysis(
    dataset: dict,
) -> list[EvaluationRun]:
    """트렌드 분석을 위한 여러 시점의 평가 실행 생성."""
    runs = []
    base_time = datetime.now() - timedelta(days=30)

    scenarios = [
        ("run-week1-baseline", "normal", 0),
        ("run-week1-v2", "normal", 2),
        ("run-week2-improved", "improved", 7),
        ("run-week2-stable", "improved", 9),
        ("run-week3-degraded", "degraded", 14),
        ("run-week3-recovery", "normal", 16),
        ("run-week4-current", "improved", 21),
    ]

    for run_id, variation, day_offset in scenarios:
        timestamp = base_time + timedelta(days=day_offset)
        run = simulate_evaluation_run(dataset, run_id, variation, timestamp)
        runs.append(run)

    return runs


class WorkflowTester:
    """종합 워크플로우 테스터."""

    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 어댑터 초기화
        self.memory_adapter = SQLiteDomainMemoryAdapter(db_path=DB_PATH)
        self.nlp_adapter = NLPAnalysisAdapter()
        self.causal_adapter = CausalAnalysisAdapter()
        self.report_adapter = MarkdownReportAdapter()

        # 서비스 초기화
        self.learning_hook = DomainLearningHook(memory_port=self.memory_adapter)

        self.results: dict[str, Any] = {}

    def run_evaluation_simulation(self, dataset: dict) -> list[EvaluationRun]:
        """평가 시뮬레이션 실행."""
        print("\n" + "=" * 60)
        print("1. 평가 실행 시뮬레이션")
        print("=" * 60)

        runs = create_multiple_runs_for_trend_analysis(dataset)

        print(f"  - 생성된 평가 실행 수: {len(runs)}")
        for run in runs:
            avg_score = sum(r.metrics[0].score for r in run.results) / len(run.results)
            passed = sum(1 for r in run.results if r.all_passed)
            print(
                f"    - {run.run_id}: 평균 점수 {avg_score:.3f}, 통과 {passed}/{len(run.results)}"
            )

        self.results["runs"] = runs
        return runs

    async def run_domain_memory_formation(
        self, runs: list[EvaluationRun], domain: str = "insurance"
    ) -> dict[str, Any]:
        """도메인 메모리 형성."""
        print("\n" + "=" * 60)
        print("2. 도메인 메모리 형성 (Formation Dynamics)")
        print("=" * 60)

        total_facts = 0
        total_learnings = 0
        total_behaviors = 0

        for run in runs:
            result = await self.learning_hook.on_evaluation_complete(
                evaluation_run=run,
                domain=domain,
                language="ko",
                auto_save=True,
            )
            total_facts += len(result["facts"])
            total_learnings += 1 if result["learning"] else 0
            total_behaviors += len(result["behaviors"])

        print(f"  - 추출된 사실 수: {total_facts}")
        print(f"  - 저장된 학습 패턴 수: {total_learnings}")
        print(f"  - 추출된 행동 패턴 수: {total_behaviors}")

        # 수동 사실 추가 (용어 사전 기반)
        insurance_facts = [
            ("종신보험", "is_a", "생명보험상품"),
            ("정기보험", "is_a", "생명보험상품"),
            ("실손보험", "is_a", "건강보험상품"),
            ("암보험", "is_a", "건강보험상품"),
            ("대인배상", "is_a", "자동차보험담보"),
            ("연금저축", "세액공제한도", "600만원"),
            ("종신보험", "기본보장금액", "1억원"),
            ("실손보험", "급여자기부담금", "20%"),
        ]

        for subject, predicate, obj in insurance_facts:
            existing = self.memory_adapter.find_fact_by_triple(subject, predicate, obj, domain)
            if not existing:
                fact = FactualFact(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    domain=domain,
                    language="ko",
                    fact_type="verified",
                    verification_score=1.0,
                )
                self.memory_adapter.save_fact(fact)
                total_facts += 1

        print(f"  - 용어 사전 사실 추가 후 총 사실 수: {total_facts}")

        memory_result = {
            "total_facts": total_facts,
            "total_learnings": total_learnings,
            "total_behaviors": total_behaviors,
        }
        self.results["memory_formation"] = memory_result
        return memory_result

    def run_memory_evolution(self, domain: str = "insurance") -> dict[str, int]:
        """메모리 진화 (Evolution Dynamics)."""
        print("\n" + "=" * 60)
        print("3. 메모리 진화 (Evolution Dynamics)")
        print("=" * 60)

        evolution_result = self.learning_hook.run_evolution(domain=domain, language="ko")

        print(f"  - 통합된 사실 수: {evolution_result['consolidated']}")
        print(f"  - 삭제된 오래된 메모리: {evolution_result['forgotten']}")
        print(f"  - 점수 감소 적용: {evolution_result['decayed']}")

        # 통계 확인
        stats = self.memory_adapter.get_statistics(domain=domain)
        print(f"  - 현재 메모리 통계: {stats}")

        self.results["memory_evolution"] = evolution_result
        return evolution_result

    def run_memory_search(self, domain: str = "insurance") -> dict[str, Any]:
        """메모리 검색 테스트."""
        print("\n" + "=" * 60)
        print("4. 메모리 검색 테스트 (Retrieval Dynamics)")
        print("=" * 60)

        search_results = {}

        # 리스트 기반 검색 (FTS 대신)
        try:
            # 도메인별 사실 목록 조회
            facts = self.memory_adapter.list_facts(domain=domain, limit=100)
            print(f"  - 도메인 '{domain}' 사실 수: {len(facts)}개")

            # 주제별 필터링
            search_queries = ["보험", "보장", "세액"]
            for query in search_queries:
                filtered = [f for f in facts if query in f.subject or query in f.object]
                print(f"  - '{query}' 포함 사실: {len(filtered)}개")
                search_results[query] = len(filtered)

            # 행동 목록 조회
            behaviors = self.memory_adapter.list_behaviors(domain=domain, limit=100)
            print(f"  - 행동 패턴 수: {len(behaviors)}개")

            # 학습 목록 조회
            learnings = self.memory_adapter.list_learnings(domain=domain, limit=100)
            print(f"  - 학습 패턴 수: {len(learnings)}개")

            self.results["memory_search"] = {
                "keyword_search": search_results,
                "list_search": {
                    "facts": len(facts),
                    "behaviors": len(behaviors),
                    "learnings": len(learnings),
                },
            }
        except Exception as e:
            print(f"  - 검색 오류 (무시됨): {e}")
            self.results["memory_search"] = {
                "keyword_search": {},
                "list_search": {"facts": 0, "behaviors": 0, "learnings": 0},
                "error": str(e),
            }

        return self.results["memory_search"]

    def run_nlp_analysis(self, runs: list[EvaluationRun]) -> dict[str, Any]:
        """NLP 분석 실행."""
        print("\n" + "=" * 60)
        print("5. NLP 분석")
        print("=" * 60)

        # 가장 최근 평가 실행에 대해 분석
        latest_run = runs[-1]

        nlp_results = {
            "text_stats": {},
            "topics": [],
            "keywords": [],
            "question_types": {},
        }

        try:
            # 종합 NLP 분석 실행
            nlp_analysis = self.nlp_adapter.analyze(
                latest_run,
                include_text_stats=True,
                include_question_types=True,
                include_keywords=True,
                include_topic_clusters=True,
            )

            # 텍스트 통계
            if nlp_analysis.has_text_stats:
                nlp_results["text_stats"] = {}
                if nlp_analysis.question_stats:
                    nlp_results["text_stats"]["question_word_count"] = (
                        nlp_analysis.question_stats.word_count
                    )
                    nlp_results["text_stats"]["question_char_count"] = (
                        nlp_analysis.question_stats.char_count
                    )
                    print(f"  - 평균 질문 단어 수: {nlp_analysis.question_stats.word_count}")
                if nlp_analysis.answer_stats:
                    nlp_results["text_stats"]["answer_word_count"] = (
                        nlp_analysis.answer_stats.word_count
                    )
                    nlp_results["text_stats"]["answer_char_count"] = (
                        nlp_analysis.answer_stats.char_count
                    )
                    print(f"  - 평균 답변 단어 수: {nlp_analysis.answer_stats.word_count}")

            # 질문 유형 분포
            if nlp_analysis.question_types:
                nlp_results["question_types"] = {
                    qt.question_type: qt.count for qt in nlp_analysis.question_types
                }
                print(f"  - 질문 유형 수: {len(nlp_analysis.question_types)}")

            # 키워드 추출
            keywords = self.nlp_adapter.extract_keywords(latest_run, top_k=10)
            nlp_results["keywords"] = [
                {"keyword": k.keyword, "tfidf_score": k.tfidf_score, "frequency": k.frequency}
                for k in keywords
            ]
            print(f"  - 추출된 키워드 수: {len(keywords)}")
            if keywords:
                print(f"    - 상위 키워드: {[k.keyword for k in keywords[:5]]}")

            # 토픽 클러스터링
            try:
                clusters = self.nlp_adapter.cluster_topics(
                    latest_run,
                    min_cluster_size=2,
                    max_clusters=5,
                )
                nlp_results["topics"] = [
                    {
                        "cluster_id": c.cluster_id,
                        "keywords": c.keywords[:5] if c.keywords else [],
                        "size": c.size,
                        "label": getattr(c, "label", f"Cluster {c.cluster_id}"),
                    }
                    for c in clusters
                ]
                print(f"  - 토픽 클러스터 수: {len(clusters)}")
                for cluster in clusters:
                    kw = cluster.keywords[:3] if cluster.keywords else []
                    print(f"    - 클러스터 {cluster.cluster_id}: {kw} (크기: {cluster.size})")
            except Exception as e:
                print(f"  - 토픽 클러스터링 스킵: {e}")

        except Exception as e:
            print(f"  - NLP 분석 오류: {e}")
            import traceback

            traceback.print_exc()

        self.results["nlp_analysis"] = nlp_results
        return nlp_results

    def run_causal_analysis(self, runs: list[EvaluationRun]) -> dict[str, Any]:
        """인과 분석 실행."""
        print("\n" + "=" * 60)
        print("6. 인과 분석")
        print("=" * 60)

        # 가장 최근 평가 실행
        latest_run = runs[-1]

        # 인과 분석
        causal_analysis = self.causal_adapter.analyze_causality(latest_run, min_samples=5)

        print(f"  - 추출된 인과 요인 수: {len(causal_analysis.factor_impacts)}")

        # Factor Impact 분석
        significant_impacts = causal_analysis.significant_impacts
        print(f"  - 유의미한 영향 관계: {len(significant_impacts)}개")

        for fi in significant_impacts[:5]:
            print(
                f"    - {fi.factor_type.value} -> {fi.metric_name}: "
                f"상관계수 {fi.correlation:.3f} (p={fi.p_value:.4f})"
            )

        # 근본 원인 분석
        print(f"  - 근본 원인 분석 결과: {len(causal_analysis.root_causes)}개")
        for rc in causal_analysis.root_causes[:3]:
            primary = [f.value for f in rc.primary_causes[:2]] if rc.primary_causes else []
            print(f"    - {rc.metric_name}: {primary}")

        # 개선 제안
        print(f"  - 개선 제안: {len(causal_analysis.interventions)}개")
        for intervention in causal_analysis.interventions[:3]:
            print(f"    - [{intervention.target_metric}] {intervention.intervention}")

        causal_result = {
            "factor_impacts": len(causal_analysis.factor_impacts),
            "significant_impacts": len(significant_impacts),
            "root_causes": len(causal_analysis.root_causes),
            "interventions": len(causal_analysis.interventions),
        }

        self.results["causal_analysis"] = causal_result
        return causal_result

    def run_kg_integration(self, domain: str = "insurance") -> dict[str, Any]:
        """Knowledge Graph 통합 테스트."""
        print("\n" + "=" * 60)
        print("7. Knowledge Graph 통합 (Planar Form)")
        print("=" * 60)

        # KG 엔티티/관계 임포트
        entities = [
            ("삼성생명", "InsuranceCompany", {"founded": "1957", "type": "생명보험사"}),
            ("삼성화재", "InsuranceCompany", {"founded": "1952", "type": "손해보험사"}),
            ("무배당종신보험", "InsuranceProduct", {"company": "삼성생명"}),
            ("운전자보험", "InsuranceProduct", {"company": "삼성화재"}),
        ]
        relations = [
            ("삼성생명", "무배당종신보험", "제공", 1.0),
            ("삼성화재", "운전자보험", "제공", 1.0),
            ("무배당종신보험", "종신보험", "is_a", 0.95),
            ("운전자보험", "상해보험", "is_a", 0.95),
        ]

        import_result = self.memory_adapter.import_kg_as_facts(
            entities=entities,
            relations=relations,
            domain=domain,
            language="ko",
        )
        print(f"  - 임포트된 엔티티: {import_result['entities_imported']}")
        print(f"  - 임포트된 관계: {import_result['relations_imported']}")

        # KG 내보내기
        exported_entities, exported_relations = self.memory_adapter.export_facts_as_kg(
            domain=domain,
            min_confidence=0.5,
        )
        print(f"  - 내보낸 엔티티: {len(exported_entities)}")
        print(f"  - 내보낸 관계: {len(exported_relations)}")

        kg_result = {
            "imported_entities": import_result["entities_imported"],
            "imported_relations": import_result["relations_imported"],
            "exported_entities": len(exported_entities),
            "exported_relations": len(exported_relations),
        }
        self.results["kg_integration"] = kg_result
        return kg_result

    def run_hierarchical_memory(self, domain: str = "insurance") -> dict[str, Any]:
        """계층적 메모리 테스트 (Hierarchical Form)."""
        print("\n" + "=" * 60)
        print("8. 계층적 메모리 (Hierarchical Form)")
        print("=" * 60)

        # Level 0 사실들 생성
        level0_facts = []
        detail_facts = [
            ("종신보험A", "보장금액", "1억원"),
            ("종신보험A", "보험료", "15만원"),
            ("종신보험A", "납입기간", "20년"),
            ("종신보험B", "보장금액", "2억원"),
            ("종신보험B", "보험료", "25만원"),
        ]

        for subject, predicate, obj in detail_facts:
            fact = FactualFact(
                subject=subject,
                predicate=predicate,
                object=obj,
                domain=domain,
                language="ko",
                verification_score=0.9,
                abstraction_level=0,
            )
            self.memory_adapter.save_fact(fact)
            level0_facts.append(fact)

        # Level 1 요약 생성 (종신보험A 요약)
        product_a_facts = [f.fact_id for f in level0_facts if f.subject == "종신보험A"]
        if len(product_a_facts) >= 2:
            summary_a = self.memory_adapter.create_summary_fact(
                child_fact_ids=product_a_facts,
                summary_subject="종신보험A",
                summary_predicate="요약",
                summary_object="보장금액 1억원, 보험료 15만원, 납입기간 20년의 종신보험 상품",
                domain=domain,
                language="ko",
            )
            print(f"  - 생성된 Level 1 요약: {summary_a.fact_id}")
            print(f"    - 추상화 레벨: {summary_a.abstraction_level}")
            print(f"    - 자식 사실 수: {len(summary_a.child_fact_ids)}")

        # 계층별 사실 조회
        level0 = self.memory_adapter.get_facts_by_level(0, domain=domain)
        level1 = self.memory_adapter.get_facts_by_level(1, domain=domain)

        print(f"  - Level 0 사실 수: {len(level0)}")
        print(f"  - Level 1 요약 수: {len(level1)}")

        hierarchy_result = {
            "level0_facts": len(level0),
            "level1_summaries": len(level1),
        }
        self.results["hierarchical_memory"] = hierarchy_result
        return hierarchy_result

    def generate_report(self, runs: list[EvaluationRun]) -> str:
        """종합 보고서 생성."""
        print("\n" + "=" * 60)
        print("9. 보고서 생성")
        print("=" * 60)

        latest_run = runs[-1]

        try:
            # NLP 분석 객체 생성
            nlp_analysis = None
            if self.results.get("nlp_analysis"):
                nlp_analysis = self.nlp_adapter.analyze(latest_run)

            # Causal 분석 객체 생성
            causal_analysis = None
            try:
                causal_analysis = self.causal_adapter.analyze_causality(latest_run, min_samples=5)
            except Exception as e:
                print(f"  - 인과 분석 결과 로드 실패: {e}")

            # AnalysisBundle 생성
            bundle = AnalysisBundle(
                run_id=latest_run.run_id,
                nlp=nlp_analysis,
                causal=causal_analysis,
            )

            # HTML 보고서 생성
            report_content = self.report_adapter.generate_html(
                bundle,
                include_nlp=True,
                include_causal=True,
                include_recommendations=True,
            )

            # 보고서 저장
            with open(REPORT_PATH, "w", encoding="utf-8") as f:
                f.write(report_content)

            print(f"  - 보고서 저장 완료: {REPORT_PATH}")
            print(f"  - 보고서 크기: {len(report_content):,} bytes")

            self.results["report"] = {
                "path": str(REPORT_PATH),
                "size_bytes": len(report_content),
            }
        except Exception as e:
            print(f"  - 보고서 생성 오류: {e}")
            import traceback

            traceback.print_exc()
            self.results["report"] = {"error": str(e)}

        return str(REPORT_PATH)

    def print_summary(self):
        """최종 결과 요약 출력."""
        print("\n" + "=" * 60)
        print("워크플로우 실행 결과 요약")
        print("=" * 60)

        print("\n[Memory Formation]")
        if "memory_formation" in self.results:
            mf = self.results["memory_formation"]
            print(f"  - 사실: {mf['total_facts']}")
            print(f"  - 학습: {mf['total_learnings']}")
            print(f"  - 행동: {mf['total_behaviors']}")

        print("\n[Memory Evolution]")
        if "memory_evolution" in self.results:
            me = self.results["memory_evolution"]
            print(f"  - 통합: {me['consolidated']}")
            print(f"  - 삭제: {me['forgotten']}")
            print(f"  - 감소: {me['decayed']}")

        print("\n[NLP Analysis]")
        if "nlp_analysis" in self.results:
            nlp = self.results["nlp_analysis"]
            print(f"  - 키워드: {nlp.get('keywords', [])[:5]}")
            print(f"  - 토픽 수: {len(nlp.get('topics', []))}")

        print("\n[Causal Analysis]")
        if "causal_analysis" in self.results:
            ca = self.results["causal_analysis"]
            print(f"  - 유의미한 영향: {ca['significant_impacts']}")
            print(f"  - 근본 원인: {ca['root_causes']}")
            print(f"  - 개선 제안: {ca['interventions']}")

        print("\n[KG Integration]")
        if "kg_integration" in self.results:
            kg = self.results["kg_integration"]
            print(f"  - 엔티티: {kg['exported_entities']}")
            print(f"  - 관계: {kg['exported_relations']}")

        print("\n[Report]")
        if "report" in self.results:
            print(f"  - 경로: {self.results['report']['path']}")


async def main():
    """메인 실행 함수."""
    print("=" * 60)
    print("EvalVault 종합 워크플로우 테스트")
    print("보험 도메인 RAG 시스템 평가")
    print("=" * 60)

    # 데이터셋 로드
    if not DATASET_PATH.exists():
        print(f"Error: 데이터셋을 찾을 수 없습니다: {DATASET_PATH}")
        sys.exit(1)

    dataset = load_dataset(DATASET_PATH)
    print(f"\n데이터셋: {dataset['name']}")
    print(f"테스트 케이스 수: {len(dataset['test_cases'])}")

    # 워크플로우 실행
    tester = WorkflowTester()

    try:
        # 1. 평가 시뮬레이션
        runs = tester.run_evaluation_simulation(dataset)

        # 2. 메모리 형성
        await tester.run_domain_memory_formation(runs)

        # 3. 메모리 진화
        tester.run_memory_evolution()

        # 4. 메모리 검색
        tester.run_memory_search()

        # 5. NLP 분석
        tester.run_nlp_analysis(runs)

        # 6. 인과 분석
        tester.run_causal_analysis(runs)

        # 7. KG 통합
        tester.run_kg_integration()

        # 8. 계층적 메모리
        tester.run_hierarchical_memory()

        # 9. 보고서 생성
        tester.generate_report(runs)

        # 결과 요약
        tester.print_summary()

        print("\n" + "=" * 60)
        print("워크플로우 테스트 완료!")
        print("=" * 60)

        return tester.results

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
