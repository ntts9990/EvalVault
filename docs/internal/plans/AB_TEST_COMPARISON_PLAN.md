# A/B Test Comparison Enhancement Plan

> 단순 지표 비교를 넘어서 분석 결과 매칭, 통계적 해석, LLM 의견 생성, 최종 비교 보고서를 생성하는 고급 A/B 테스트 비교 시스템

## 1. 현황 분석 (As-Is)

### 1.1 현재 A/B 비교 구현

| 컴포넌트 | 위치 | 기능 | 한계 |
|----------|------|------|------|
| `ExperimentComparator` | `domain/services/experiment_comparator.py` | 그룹 간 기본 메트릭 비교 | 분석 결과 매칭 없음 |
| `RunComparatorModule` | `adapters/outbound/analysis/run_comparator_module.py` | 평균 점수로 승자 결정 | 단순 숫자 비교만 |
| `StatisticalComparatorModule` | `adapters/outbound/analysis/statistical_comparator_module.py` | 집계된 점수 비교 | 분석 번들 미활용 |
| `ComparisonReportModule` | `adapters/outbound/analysis/comparison_report_module.py` | 기본 마크다운 보고서 | LLM 해석 없음 |
| `LLMReportModule` | `adapters/outbound/analysis/llm_report_module.py` | 증거 기반 LLM 보고서 | 비교 분석 미지원 |

### 1.2 파이프라인/모듈 규약 (아키텍처 정합성 체크)

- `BaseAnalysisModule`/`AnalysisModulePort`는 `execute(inputs, params)` 시그니처를 사용
- `inputs`에는 `__context__`(query/run_id/params)와 의존 노드 출력이 `node_id` 키로 저장됨
- 모듈 간 데이터 연결은 `get_upstream_output` 헬퍼 사용 권장
- API/저장 시 `jsonable_encoder`로 직렬화되므로 출력은 JSON-serializable 형태 유지 필요
  - `analysis/common.py:AnalysisDataProcessor.to_serializable`
  - `analysis/pipeline_helpers.to_serializable`

### 1.3 분석 결과 엔터티

현재 사용 가능한 분석 번들 (`analysis.py`):

```python
@dataclass
class AnalysisBundle:
    run_id: str
    statistical: StatisticalAnalysis | None  # 메트릭 통계, 상관관계, 낮은 성능 케이스
    nlp: NLPAnalysis | None                   # 텍스트 통계, 질문 유형, 키워드
    causal: CausalAnalysis | None             # 요인 영향, 인과 관계, 근본 원인
```

> `AnalysisType`에는 `DATA_QUALITY`도 존재하므로, 매칭 로직은 확장 가능하게 설계.

### 1.4 파이프라인 템플릿 현황

`pipeline_template_registry.py`의 비교 관련 템플릿:
- `COMPARE_RUNS`: load_runs → run_analysis → statistical_comparison → report
- `GENERATE_COMPARISON`: load_runs → run_comparison → llm_report

**문제점**: 분석 결과(StatisticalAnalysis, NLPAnalysis, CausalAnalysis)를 로드하여 매칭하는 로직이 없음.

---

## 2. 요구사항 정의 (To-Be)

### 2.1 핵심 기능

1. **분석 결과 매칭 (Analysis Result Matching)**
   - Run A와 Run B의 분석 번들에서 동일한 분석 유형 식별
   - 매칭되는 분석: 통계적/설명적 심층 해석
   - 매칭되지 않는 분석: 개별 LLM 의견 생성 후 비교

2. **통계적 심층 해석 (Statistical Deep Interpretation)**
   - 매칭된 통계 분석 간 차이의 유의성 검정
   - 효과 크기 해석 (Cohen's d)
   - 상관관계 패턴 비교

3. **LLM 의견 생성 (LLM Opinion Generation)**
   - 각 분석 결과에 대한 독립적 LLM 의견
   - 두 의견을 비교하는 메타 분석

4. **통합 비교 보고서 (Consolidated Comparison Report)**
   - A 분석 보고서 (전문)
   - B 분석 보고서 (전문)
   - 비교 분석 섹션
   - 권장사항 및 결론

### 2.2 아키텍처/개발 정책 정합성

- 핵심 비교 로직은 `domain/services`로 이동하고, 모듈은 얇은 오케스트레이션만 담당
- LLM/보고서/저장소는 포트를 통해 주입 (`LLMPort`, `ReportPort`, `StoragePort` 등)
- `AnalysisType` enum 기반 매칭 + `MISSING` 상태 추가로 케이스 분기 명확화
- `AnalysisService`/`AnalysisCachePort` 재사용으로 분석 번들 캐싱 및 중복 비용 최소화
- 파이프라인 입력은 `__context__` + `params` 규약 준수, 출력은 JSON 직렬화 가능 형태 유지
- 인텐트/템플릿/CLI/API 카탈로그 동시 업데이트로 탐색성과 회귀 방지
- `analysis_types` 파라미터는 문자열→`AnalysisType` 변환 후 유효 타입만 사용
- LLM 프롬프트/버전은 메타데이터(트래커) 또는 manifest로 기록해 재현성 확보

### 2.3 사용자 시나리오

```
사용자: Run A (GPT-5-nano)와 Run B (Gemma 3) 비교해줘

시스템:
1. 두 Run의 분석 결과 로드
2. 분석 유형 매칭:
   - Statistical (A) ↔ Statistical (B) → 통계 비교 수행
   - NLP (A) ↔ NLP (B) → 패턴 비교 수행
   - Causal (A만 존재) → LLM 의견 생성
3. 최종 보고서 생성:
   - Run A 상세 분석
   - Run B 상세 분석
   - 비교 분석 결과
   - 종합 권장사항
```

---

## 3. 아키텍처 설계

### 3.1 새로운 컴포넌트

```
src/evalvault/
├── domain/
│   ├── entities/
│   │   └── comparison.py                 # [NEW] 비교 도메인 엔터티
│   └── services/
│       └── ab_comparison_service.py      # [NEW] 비교 오케스트레이션 (핵심 로직)
├── ports/
│   └── outbound/
│       ├── comparison_repository_port.py # [NEW/OPTIONAL] 저장/조회 포트
│       └── comparison_report_port.py     # [NEW/OPTIONAL] 통합 보고서 포트
├── adapters/outbound/analysis/
│   ├── analysis_bundle_builder_module.py # [NEW] AnalysisService 래퍼
│   ├── analysis_matcher_module.py        # [NEW] 분석 결과 매칭
│   ├── matched_analysis_interpreter_module.py  # [NEW] 매칭 해석
│   ├── unmatched_opinion_module.py       # [NEW] LLM 의견 생성
│   ├── opinion_comparator_module.py      # [NEW] 의견 비교
│   ├── bundle_report_module.py           # [NEW] 번들 기반 보고서
│   └── ab_comparison_report_module.py    # [NEW] 통합 보고서
└── adapters/inbound/api/routers/
    └── pipeline.py                   # COMPARE_RUNS_DEEP 추가 (필수)
```

> 이번 작업은 `/pipeline/analyze` 기반으로만 구현하고 전용 엔드포인트는 범위에서 제외.

### 3.2 새로운 엔터티 (`comparison.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from evalvault.domain.entities.analysis import AnalysisType, ComparisonResult


class AnalysisMatchStatus(str, Enum):
    """분석 매칭 상태."""
    MATCHED = "matched"              # 양쪽 모두 존재
    ONLY_A = "only_a"                # A에만 존재
    ONLY_B = "only_b"                # B에만 존재
    MISSING = "missing"              # 둘 다 없음


@dataclass
class MatchedAnalysisPair:
    """매칭된 분석 쌍."""
    analysis_type: AnalysisType
    status: AnalysisMatchStatus
    analysis_a: Any | None           # StatisticalAnalysis, NLPAnalysis, 등
    analysis_b: Any | None
    interpretation: str = ""         # 통계적 해석 (매칭된 경우)
    significance: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMOpinion:
    """LLM이 생성한 분석 의견."""
    run_id: str
    analysis_type: AnalysisType
    summary: str                     # 주요 발견사항 요약
    strengths: list[str]             # 강점
    weaknesses: list[str]            # 약점
    recommendations: list[str]       # 권장사항
    confidence: float                # 0.0 ~ 1.0


@dataclass
class OpinionComparison:
    """두 LLM 의견의 비교 결과."""
    analysis_type: AnalysisType
    opinion_a: LLMOpinion
    opinion_b: LLMOpinion
    comparative_summary: str         # 비교 요약
    key_differences: list[str]       # 핵심 차이점
    winner: str | None               # "a", "b", or None (동등)
    winner_rationale: str = ""


@dataclass
class ABComparisonConfig:
    """A/B 비교 실행 옵션."""
    analysis_types: list[AnalysisType] | None = None
    include_nlp: bool = True
    include_causal: bool = True
    use_llm: bool = True
    p_value_threshold: float = 0.05
    effect_size_thresholds: dict[str, float] = field(
        default_factory=lambda: {"small": 0.2, "medium": 0.5, "large": 0.8}
    )


@dataclass
class ABComparisonResult:
    """A/B 테스트 비교 최종 결과."""
    comparison_id: str
    run_id_a: str
    run_id_b: str
    config: ABComparisonConfig

    # 메트릭 수준 비교 (기존 기능)
    metric_comparisons: list[ComparisonResult]

    # 분석 매칭 결과
    matched_pairs: list[MatchedAnalysisPair]

    # 매칭되지 않은 분석의 LLM 의견 비교
    opinion_comparisons: list[OpinionComparison]

    # 개별 보고서
    report_a: str | None             # Run A 전체 분석 보고서
    report_b: str | None             # Run B 전체 분석 보고서

    # 통합 비교 보고서
    comparison_report: str           # 최종 비교 분석 보고서

    # 메타데이터
    created_at: str
    total_duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 3.3 새로운 파이프라인 템플릿

```python
def _create_ab_comparison_template(self) -> AnalysisPipeline:
    """A/B 테스트 비교 템플릿."""
    nodes = [
        # 1단계: 데이터 로드
        AnalysisNode(
            id="load_runs",
            name="Run A/B 로드",
            module="run_loader",
        ),

        # 2단계: 분석 번들 생성
        AnalysisNode(
            id="analysis_bundles",
            name="분석 번들 생성",
            module="analysis_bundle_builder",
            depends_on=["load_runs"],
        ),

        # 3단계: 분석 매칭
        AnalysisNode(
            id="analysis_matching",
            name="분석 매칭",
            module="analysis_matcher",
            depends_on=["analysis_bundles"],
        ),

        # 4단계: 매칭 분석 해석 (병렬)
        AnalysisNode(
            id="matched_interpretation",
            name="매칭 분석 해석",
            module="matched_analysis_interpreter",
            depends_on=["analysis_matching", "analysis_bundles"],
        ),
        AnalysisNode(
            id="unmatched_opinions",
            name="LLM 의견 생성",
            module="unmatched_opinion_generator",
            depends_on=["analysis_matching", "analysis_bundles"],
        ),

        # 5단계: 의견 비교
        AnalysisNode(
            id="opinion_comparison",
            name="의견 비교 분석",
            module="opinion_comparator",
            depends_on=["unmatched_opinions"],
        ),

        # 6단계: 개별 보고서 생성 (병렬)
        AnalysisNode(
            id="report_a",
            name="Run A 보고서",
            module="bundle_report",
            params={"run_key": "a"},
            depends_on=["analysis_bundles"],
        ),
        AnalysisNode(
            id="report_b",
            name="Run B 보고서",
            module="bundle_report",
            params={"run_key": "b"},
            depends_on=["analysis_bundles"],
        ),

        # 7단계: 통합 비교 보고서
        AnalysisNode(
            id="comparison_report",
            name="통합 비교 보고서",
            module="ab_comparison_report",
            depends_on=[
                "matched_interpretation",
                "opinion_comparison",
                "report_a",
                "report_b",
            ],
        ),
    ]
    return AnalysisPipeline(
        intent=AnalysisIntent.COMPARE_RUNS_DEEP,
        nodes=nodes,
    )
```

> `run_loader`는 `AnalysisContext.additional_params` 또는 `params`의 `run_ids`로 A/B를 지정.
> 예: `params={"run_ids": [run_id_a, run_id_b]}` 또는 API에서 `params.run_ids` 전달.

### 3.4 DAG 시각화

```
                    ┌─────────────┐
                    │   Start     │
                    └──────┬──────┘
                           │
              ▼
        ┌──────────┐
        │load_runs │
        └────┬─────┘
             │
             ▼
      ┌───────────────┐
      │analysis_bundles│
      └────┬──────────┘
           │
           ▼
    ┌───────────────┐
    │analysis_matching│
    └──────┬────────┘
           │
  ┌────────┼─────────┐
  ▼                  ▼
┌─────────────────┐  ┌────────────────┐
│matched_interpret│  │unmatched_opin. │
└────────┬────────┘  └───────┬────────┘
         │                   ▼
         │            ┌─────────────────┐
         │            │opinion_compare  │
         │            └───────┬─────────┘
         │                    │
         └─────────┬──────────┘
                   │
        ┌──────────┼──────────┐
        │                     │
        ▼                     ▼
   ┌─────────┐          ┌─────────┐
   │report_a │          │report_b │
   └────┬────┘          └────┬────┘
        │                    │
        └─────────┬──────────┘
                  ▼
         ┌────────────────┐
         │comparison_report│
         └────────────────┘
```

---

## 4. 구현 세부 사항

### 4.1 Phase 1: 분석 번들 생성 + 매칭 모듈

**파일**: `analysis_bundle_builder_module.py`

```python
class AnalysisBundleBuilderModule(BaseAnalysisModule):
    """RunLoader 결과를 AnalysisBundle로 변환."""

    module_id = "analysis_bundle_builder"
    name = "Analysis Bundle Builder"
    description = "EvaluationRun을 분석 번들로 변환합니다."
    input_types = ["runs"]
    output_types = ["bundles", "metric_comparisons"]
    requires = ["run_loader"]
    tags = ["analysis", "bundle"]

    def __init__(self, analysis_service: AnalysisService):
        self._service = analysis_service
        self._processor = AnalysisDataProcessor()

    def execute(self, inputs: dict[str, Any], params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])
        run_map = self._resolve_runs(runs, params)

        include_nlp = params.get("include_nlp", True)
        include_causal = params.get("include_causal", False)
        use_cache = params.get("use_cache", True)

        bundles = {
            key: self._service.analyze_run(
                run,
                include_nlp=include_nlp,
                include_causal=include_causal,
                use_cache=use_cache,
            )
            for key, run in run_map.items()
            if isinstance(run, EvaluationRun)
        }
        bundle_payloads = {
            key: self._processor.to_serializable(bundle)
            for key, bundle in bundles.items()
        }

        comparisons = []
        if "a" in run_map and "b" in run_map:
            comparisons = self._service.compare_runs(
                run_map["a"],
                run_map["b"],
                metrics=params.get("metrics"),
                test_type=params.get("test_type", "t-test"),
            )

        return {
            "runs": run_map,
            "run_ids": {k: v.run_id for k, v in run_map.items()},
            "bundles": bundles,
            "bundle_payloads": bundle_payloads,
            "analysis_types": params.get("analysis_types"),
            "metric_comparisons": self._processor.to_serializable(comparisons),
        }
```

> `run_map`은 `run_ids` 순서 또는 `params.run_id_a/run_id_b`를 기준으로
> `{"a": run_a, "b": run_b}` 형태로 매핑.

**파일**: `analysis_matcher_module.py`

```python
class AnalysisMatcherModule(BaseAnalysisModule):
    """분석 결과 매칭 모듈."""

    def __init__(self):
        super().__init__(module_id="analysis_matcher")

    def execute(self, inputs: dict[str, Any], params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        bundles_output = get_upstream_output(
            inputs, "analysis_bundles", "analysis_bundle_builder"
        ) or {}
        bundles = bundles_output.get("bundles", {})
        bundle_a: AnalysisBundle | None = bundles.get("a")
        bundle_b: AnalysisBundle | None = bundles.get("b")

        analysis_types = params.get("analysis_types") or bundles_output.get(
            "analysis_types"
        ) or [
            AnalysisType.STATISTICAL,
            AnalysisType.NLP,
            AnalysisType.CAUSAL,
        ]
        analysis_types = [
            AnalysisType(item) if isinstance(item, str) else item
            for item in analysis_types
        ]

        matched_pairs: list[MatchedAnalysisPair] = []

        for analysis_type in analysis_types:
            analysis_a = self._extract_analysis(bundle_a, analysis_type)
            analysis_b = self._extract_analysis(bundle_b, analysis_type)
            matched_pairs.append(
                self._match_analysis(analysis_type, analysis_a, analysis_b)
            )

        return {
            "matched_pairs": matched_pairs,
            "has_matched": any(p.status == AnalysisMatchStatus.MATCHED for p in matched_pairs),
            "has_unmatched": any(p.status != AnalysisMatchStatus.MATCHED for p in matched_pairs),
        }

    def _match_analysis(
        self,
        analysis_type: AnalysisType,
        analysis_a: Any | None,
        analysis_b: Any | None,
    ) -> MatchedAnalysisPair:
        if analysis_a and analysis_b:
            status = AnalysisMatchStatus.MATCHED
        elif analysis_a:
            status = AnalysisMatchStatus.ONLY_A
        elif analysis_b:
            status = AnalysisMatchStatus.ONLY_B
        else:
            status = AnalysisMatchStatus.MISSING

        return MatchedAnalysisPair(
            analysis_type=analysis_type,
            status=status,
            analysis_a=analysis_a,
            analysis_b=analysis_b,
        )

    def _extract_analysis(
        self, bundle: AnalysisBundle | None, analysis_type: AnalysisType
    ) -> Any | None:
        if not bundle:
            return None
        if analysis_type == AnalysisType.STATISTICAL:
            return bundle.statistical
        if analysis_type == AnalysisType.NLP:
            return bundle.nlp
        if analysis_type == AnalysisType.CAUSAL:
            return bundle.causal
        return None
```

### 4.2 Phase 2: 통계적 해석 모듈

**파일**: `matched_analysis_interpreter_module.py`

```python
class MatchedAnalysisInterpreterModule(BaseAnalysisModule):
    """매칭된 분석의 통계적 해석."""

    def __init__(self, analysis_adapter: AnalysisPort):
        super().__init__(module_id="matched_analysis_interpreter")
        self._analysis = analysis_adapter
        self._processor = AnalysisDataProcessor()

    def execute(self, inputs: dict[str, Any], params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        matched_output = get_upstream_output(
            inputs, "analysis_matching", "analysis_matcher"
        ) or {}
        matched_pairs = matched_output.get("matched_pairs", [])
        bundles_output = get_upstream_output(
            inputs, "analysis_bundles", "analysis_bundle_builder"
        ) or {}
        runs = bundles_output.get("runs", {})
        run_a = runs.get("a")
        run_b = runs.get("b")
        interpretations = []

        for pair in matched_pairs:
            if pair.status != AnalysisMatchStatus.MATCHED:
                continue

            if pair.analysis_type == AnalysisType.STATISTICAL:
                interp = self._interpret_statistical(pair, run_a, run_b, params)
            elif pair.analysis_type == AnalysisType.NLP:
                interp = self._interpret_nlp(pair)
            elif pair.analysis_type == AnalysisType.CAUSAL:
                interp = self._interpret_causal(pair)
            else:
                continue

            pair.interpretation = interp["summary"]
            pair.significance = interp["details"]
            interpretations.append(interp)

        return {"interpretations": interpretations}

    def _interpret_statistical(
        self,
        pair: MatchedAnalysisPair,
        run_a: EvaluationRun | None,
        run_b: EvaluationRun | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """통계 분석 비교 해석."""
        stat_a: StatisticalAnalysis = pair.analysis_a
        stat_b: StatisticalAnalysis = pair.analysis_b

        # 실제 run 데이터를 활용한 유의성 검정/효과 크기 계산 권장
        comparisons: list[ComparisonResult] = []
        if isinstance(run_a, EvaluationRun) and isinstance(run_b, EvaluationRun):
            comparisons = self._analysis.compare_runs(
                run_a,
                run_b,
                metrics=params.get("metrics"),
                test_type=params.get("test_type", "t-test"),
            )

        # 요약/세부 정보 구성
        metric_diffs = self._summarize_comparisons(comparisons)
        correlation_diff = self._compare_correlations(stat_a, stat_b)
        low_perf_diff = self._compare_low_performers(stat_a, stat_b)

        return {
            "summary": self._generate_stat_summary(metric_diffs, correlation_diff, low_perf_diff),
            "details": {
                "metric_differences": metric_diffs,
                "correlation_differences": correlation_diff,
                "low_performer_differences": low_perf_diff,
                "comparisons": self._processor.to_serializable(comparisons),
            },
        }
```

### 4.3 Phase 3: LLM 의견 생성 모듈

**파일**: `unmatched_opinion_module.py`

```python
class UnmatchedOpinionModule(BaseAnalysisModule):
    """매칭되지 않은 분석에 대한 LLM 의견 생성."""

    def __init__(self, llm_adapter: LLMPort | None = None):
        super().__init__(module_id="unmatched_opinion_generator")
        self.llm_adapter = llm_adapter

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        matched_output = get_upstream_output(
            inputs, "analysis_matching", "analysis_matcher"
        ) or {}
        matched_pairs = matched_output.get("matched_pairs", [])
        bundles_output = get_upstream_output(
            inputs, "analysis_bundles", "analysis_bundle_builder"
        ) or {}
        run_ids = bundles_output.get("run_ids", {})
        opinions = []

        if self.llm_adapter is None:
            return {"unmatched_opinions": opinions, "error": "LLM adapter not configured"}

        for pair in matched_pairs:
            if pair.status == AnalysisMatchStatus.MATCHED:
                continue  # 매칭된 것은 해석 모듈에서 처리

            if pair.status == AnalysisMatchStatus.ONLY_A and pair.analysis_a:
                opinion = await self._generate_opinion(
                    run_ids.get("a"),
                    pair.analysis_type,
                    pair.analysis_a,
                )
                opinions.append(("a", pair.analysis_type, opinion))

            if pair.status == AnalysisMatchStatus.ONLY_B and pair.analysis_b:
                opinion = await self._generate_opinion(
                    run_ids.get("b"),
                    pair.analysis_type,
                    pair.analysis_b,
                )
                opinions.append(("b", pair.analysis_type, opinion))

        return {"unmatched_opinions": opinions}

    async def _generate_opinion(
        self,
        run_id: str,
        analysis_type: AnalysisType,
        analysis: Any,
    ) -> LLMOpinion:
        """분석 결과에 대한 LLM 의견 생성."""
        prompt = self._build_opinion_prompt(analysis_type, analysis)

        response_text = await asyncio.to_thread(
            self.llm_adapter.generate_text,
            prompt,
            json_mode=True,
        )
        response = LLMOpinionSchema.model_validate_json(response_text)

        return LLMOpinion(
            run_id=run_id,
            analysis_type=analysis_type,
            summary=response.summary,
            strengths=response.strengths,
            weaknesses=response.weaknesses,
            recommendations=response.recommendations,
            confidence=response.confidence,
        )
```

> `use_llm=false`일 때는 의견 생성 단계를 스킵하고 빈 결과를 반환하도록 가드.

### 4.4 Phase 4: 의견 비교 모듈

**파일**: `opinion_comparator_module.py`

```python
class OpinionComparatorModule(BaseAnalysisModule):
    """두 LLM 의견을 비교 분석."""

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        unmatched_output = get_upstream_output(
            inputs, "unmatched_opinions", "unmatched_opinion_generator"
        ) or {}
        unmatched_opinions = unmatched_output.get("unmatched_opinions", [])

        # 분석 유형별로 그룹화
        opinions_by_type: dict[str, dict[str, LLMOpinion]] = {}
        for run_key, analysis_type, opinion in unmatched_opinions:
            if analysis_type not in opinions_by_type:
                opinions_by_type[analysis_type] = {}
            opinions_by_type[analysis_type][run_key] = opinion

        comparisons = []
        for analysis_type, opinions in opinions_by_type.items():
            if "a" in opinions and "b" in opinions:
                comparison = await self._compare_opinions(
                    analysis_type,
                    opinions["a"],
                    opinions["b"],
                )
                comparisons.append(comparison)

        return {"opinion_comparisons": comparisons}

    async def _compare_opinions(
        self,
        analysis_type: AnalysisType,
        opinion_a: LLMOpinion,
        opinion_b: LLMOpinion,
    ) -> OpinionComparison:
        """두 의견을 LLM으로 비교."""
        prompt = self._build_comparison_prompt(opinion_a, opinion_b)

        response_text = await asyncio.to_thread(
            self.llm_adapter.generate_text,
            prompt,
            json_mode=True,
        )
        response = OpinionComparisonSchema.model_validate_json(response_text)

        return OpinionComparison(
            analysis_type=analysis_type,
            opinion_a=opinion_a,
            opinion_b=opinion_b,
            comparative_summary=response.summary,
            key_differences=response.differences,
            winner=response.winner,
            winner_rationale=response.rationale,
        )
```

> `llm_adapter`가 없으면 비교 단계는 스킵하고 빈 리스트를 반환.

> `bundle_report_module.py`는 `ReportPort`(예: `MarkdownReportAdapter`)로 번들을
> Markdown 보고서로 변환하며, 필요 시 LLM 요약을 추가하는 얇은 래퍼로 구성.

### 4.5 Phase 5: 통합 보고서 모듈

**파일**: `ab_comparison_report_module.py`

```python
class ABComparisonReportModule(BaseAnalysisModule):
    """통합 A/B 비교 보고서 생성."""

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = inputs.get("__context__", {})
        # 모든 이전 노드 결과 수집
        report_a = (inputs.get("report_a") or {}).get("report", "")
        report_b = (inputs.get("report_b") or {}).get("report", "")
        interpretations = (inputs.get("matched_interpretation") or {}).get(
            "interpretations", []
        )
        opinion_comparisons = (inputs.get("opinion_comparison") or {}).get(
            "opinion_comparisons", []
        )
        bundles_output = get_upstream_output(
            inputs, "analysis_bundles", "analysis_bundle_builder"
        ) or {}
        metric_comparisons = bundles_output.get("metric_comparisons", [])

        # 보고서 섹션 구성
        sections = [
            self._build_header(context),
            self._build_executive_summary(interpretations, opinion_comparisons),
            self._build_metric_comparison_section(metric_comparisons),
            self._build_matched_analysis_section(interpretations),
            self._build_opinion_comparison_section(opinion_comparisons),
            "---",
            "## Run A 상세 분석",
            report_a,
            "---",
            "## Run B 상세 분석",
            report_b,
            "---",
            self._build_conclusion(context),
        ]

        final_report = "\n\n".join(sections)

        return {
            "comparison_report": final_report,
            "report_a": report_a,
            "report_b": report_b,
        }
```

---

## 5. API 설계

### 5.1 Pipeline 인텐트 확장

- `AnalysisIntent.COMPARE_RUNS_DEEP` 추가 후 `/pipeline/analyze`로 호출
- `params`로 run_ids / 분석 옵션 전달 (기존 파이프라인 결과 저장 흐름 재사용)

```json
POST /pipeline/analyze
{
  "query": "A/B 비교",
  "intent": "compare_runs_deep",
  "params": {
    "run_ids": ["run_id_a", "run_id_b"],
    "analysis_types": ["statistical", "nlp", "causal"],
    "include_nlp": true,
    "include_causal": false,
    "use_llm": true,
    "include_reports": true
  }
}
```

### 5.2 프론트엔드 통합

```typescript
// frontend/src/services/api.ts
export const compareAB = async (
  runIdA: string,
  runIdB: string,
  options?: { includeReports?: boolean }
): Promise<AnalysisResponse> => {
  const response = await api.post('/pipeline/analyze', {
    query: 'A/B 비교',
    intent: 'compare_runs_deep',
    params: {
      run_ids: [runIdA, runIdB],
      include_reports: options?.includeReports ?? true,
    },
  });
  return response.data;
};
```

---

## 6. 테스트 전략

### 6.1 단위 테스트

```python
# tests/unit/test_analysis_matcher.py
class TestAnalysisMatcher:
    def test_match_both_present(self):
        """양쪽 모두 있을 때 MATCHED 반환."""
        ...

    def test_match_only_a(self):
        """A에만 있을 때 ONLY_A 반환."""
        ...

    def test_match_only_b(self):
        """B에만 있을 때 ONLY_B 반환."""
        ...

    def test_match_missing(self):
        """양쪽 모두 없을 때 MISSING 반환."""
        ...

# tests/unit/test_bundle_builder.py
class TestAnalysisBundleBuilder:
    def test_builds_bundles_and_comparisons(self, sample_runs):
        """AnalysisBundle과 metric 비교 결과가 직렬화 가능해야 함."""
        ...

# tests/unit/test_matched_interpreter.py
class TestMatchedInterpreter:
    def test_interpret_statistical_significant_diff(self):
        """유의미한 통계 차이 해석."""
        ...

    def test_interpret_nlp_pattern_diff(self):
        """NLP 패턴 차이 해석."""
        ...

# tests/unit/test_opinion_comparator.py
class TestOpinionComparator:
    @pytest.mark.requires_openai
    async def test_compare_opinions(self):
        """두 의견 비교 LLM 호출."""
        ...
```

### 6.2 통합 테스트

```python
# tests/integration/test_ab_comparison_pipeline.py
class TestABComparisonPipeline:
    @pytest.mark.requires_openai
    async def test_full_ab_comparison(self, sample_runs):
        """전체 A/B 비교 파이프라인 테스트."""
        ...

    async def test_ab_comparison_partial_analysis(self, partial_runs):
        """부분 분석만 있는 경우 테스트."""
        ...
```

---

## 7. 구현 순서 및 체크리스트

### Phase 1: 기반 엔터티/인텐트 정리 (1-2일)
- [ ] `comparison.py` 엔터티 + `ABComparisonConfig` 정의
- [ ] `AnalysisIntent.COMPARE_RUNS_DEEP` 추가 및 분류기/CLI/카탈로그 반영
- [ ] 단위 테스트 작성

### Phase 2: 분석 번들 빌더/매칭 (1-2일)
- [ ] `AnalysisBundleBuilderModule` 구현 (AnalysisService 래퍼)
- [ ] `AnalysisMatcherModule` 구현
- [ ] `AnalysisCachePort` 연동 및 단위 테스트

### Phase 3: 통계 해석 (2-3일)
- [ ] `MatchedAnalysisInterpreterModule` 구현
- [ ] `AnalysisPort.compare_runs` 기반 유의성/효과크기 비교
- [ ] 단위 테스트

### Phase 4: LLM 의견 생성 (2-3일)
- [ ] `UnmatchedOpinionModule` 구현
- [ ] JSON 스키마 파싱(Pydantic) + 실패 시 fallback
- [ ] 단위 테스트 (모킹)

### Phase 5: 의견 비교 (1-2일)
- [ ] `OpinionComparatorModule` 구현
- [ ] JSON 파싱/실패 처리
- [ ] 단위 테스트

### Phase 6: 보고서 모듈 (2-3일)
- [ ] `BundleReportModule` 구현 (ReportPort 기반)
- [ ] `ABComparisonReportModule` 구현 및 템플릿 정리
- [ ] 단위 테스트

### Phase 7: 파이프라인 통합 (1-2일)
- [ ] `PipelineTemplateRegistry` 업데이트
- [ ] `COMPARE_RUNS_DEEP` 템플릿 등록
- [ ] 모듈 등록 및 DAG 의존성 검증

### Phase 8: API 및 저장소 (1-2일)
- [ ] `/pipeline/analyze` 경로에서 비교 결과 직렬화 확인
- [ ] `pipeline_results` 저장/조회 흐름 확인
- [ ] API 테스트

### Phase 9: 프론트엔드 (2-3일)
- [ ] A/B 비교 UI 컴포넌트
- [ ] 보고서 뷰어
- [ ] 분석 선택 UI

### Phase 10: 통합 테스트 및 문서화 (1-2일)
- [ ] E2E 테스트
- [ ] 사용자 문서 업데이트
- [ ] API 문서 업데이트

---

## 8. 리스크 및 완화 전략

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|------|------|-----------|
| LLM 비용 증가 | 높음 | 중간 | 캐싱, 요약 압축, 배치 처리 |
| 응답 지연 | 중간 | 높음 | 비동기 처리, 진행률 표시, 스트리밍 |
| 분석 결과 불일치 | 중간 | 낮음 | 버전 검증, 스키마 마이그레이션 |
| LLM 환각 | 높음 | 중간 | 증거 기반 프롬프트, 신뢰도 점수 |
| JSON 파싱 실패 | 중간 | 중간 | json_mode 강제, 파싱 실패 시 fallback |
| 직렬화 실패/저장 오류 | 중간 | 중간 | to_serializable 사용, API 직렬화 테스트 |

---

## 9. 성공 지표

1. **기능 완성도**: 모든 분석 유형에 대해 매칭/비교 동작
2. **테스트 커버리지**: 새 코드 90% 이상
3. **응답 시간**: 전체 비교 < 60초 (LLM 포함)
4. **사용자 만족도**: 보고서 가독성 및 유용성 피드백
5. **안정성**: API 직렬화/저장 오류 0건

---

## 10. 참고 자료

- 기존 구현: `experiment_comparator.py`, `llm_report_module.py`
- 엔터티: `analysis.py`, `analysis_pipeline.py`
- 서비스/포트: `analysis_service.py`, `analysis_port.py`, `report_port.py`
- 파이프라인: `pipeline_template_registry.py`, `pipeline_orchestrator.py`
- API: `pipeline.py` 라우터
