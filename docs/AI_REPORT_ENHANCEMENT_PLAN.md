# AI 분석 보고서 개선 계획

> 작성일: 2025-12-30
> 버전: 1.0

## 1. 현황 분석

### 1.1 현재 AI 분석 보고서의 한계

현재 `LLMReportGenerator`는 **메트릭 점수만을 기반**으로 보고서를 생성합니다:

```
입력 데이터:
- 메트릭 점수 (faithfulness, answer_relevancy 등)
- 기본 실행 정보 (dataset_name, model_name, pass_rate)

출력:
- 메트릭별 일반적인 개선 제안
- Executive Summary
```

**문제점:**
1. 실제 테스트 케이스 데이터를 활용하지 않음
2. 패턴 탐지, NLP 분석, 인과 분석 등 기존 분석 기능 미활용
3. 일반적인 제안만 제공 (구체적인 실패 사례 기반 아님)

### 1.2 활용 가능한 분석 기능 (미사용 중)

| 분석 기능 | 위치 | 데이터 |
|-----------|------|--------|
| 패턴 탐지 | `pattern_detector.py` | 실패 패턴, 통계적 유의성, 대표 샘플 |
| LLM 인사이트 | `insight_generator.py` | 근본 원인, 개선 제안, 이상적 답변 |
| 통계 분석 | `analysis_service.py` | 상관관계, 저성과자, 분포 |
| NLP 분석 | `analysis.py` | 질문 유형, 키워드, 토픽 클러스터 |
| 인과 분석 | `analysis.py` | 영향 요인, 방향, 강도 |
| 개선 가이드 | `improvement_guide_service.py` | 우선순위화된 액션, 검증 방법 |

### 1.3 시간 추정 수정 필요

현재 UI/문서에서 "2-3분 소요"라고 표시되어 있지만, 실제 테스트 결과:
- **3개 테스트 케이스 + gpt-5-nano**: ~2분
- 실제 시간은 테스트 케이스 수와 메트릭 수에 비례

## 2. 개선 목표

### 2.1 단기 목표 (P0)
1. **시간 추정 문구 수정**: 동적 추정 또는 정확한 표현으로 변경
2. **테스트 케이스 데이터 통합**: 실패 사례 구체적 분석

### 2.2 중기 목표 (P1)
1. **패턴 탐지 결과 통합**: 규칙 기반 탐지 결과를 보고서에 포함
2. **통계 분석 통합**: 상관관계, 분포 분석 추가
3. **개선 가이드 연동**: 기존 Improve 페이지 분석 재사용

### 2.3 장기 목표 (P2)
1. **NLP/인과 분석 통합**: 심층 분석 옵션 제공
2. **비교 보고서**: 여러 실행 결과 비교 분석
3. **대시보드 연동**: 실시간 모니터링 연계

## 3. 상세 구현 계획

### 3.1 Phase 1: 시간 추정 수정 (1일)

#### 3.1.1 수정 대상 파일
- `src/evalvault/adapters/inbound/web/app.py`
- `src/evalvault/adapters/outbound/report/llm_report_generator.py`
- 관련 UI 컴포넌트

#### 3.1.2 수정 내용
```python
# 동적 시간 추정 공식
def estimate_generation_time(num_metrics: int, num_test_cases: int) -> str:
    """
    기준: gpt-5-nano, 6 메트릭, 3 테스트 케이스 = ~2분
    """
    base_time = 30  # 초 (Executive Summary)
    per_metric_time = 15  # 초

    estimated_seconds = base_time + (num_metrics * per_metric_time)

    if estimated_seconds < 60:
        return f"약 {estimated_seconds}초"
    else:
        minutes = estimated_seconds // 60
        return f"약 {minutes}-{minutes + 1}분"
```

### 3.2 Phase 2: 테스트 케이스 데이터 통합 (3일)

#### 3.2.1 현재 구조
```
LLMReportGenerator.generate_report(run, metrics_to_analyze, thresholds)
                                    ↓
                              메트릭 점수만 사용
```

#### 3.2.2 개선 구조
```
LLMReportGenerator.generate_report(run, metrics_to_analyze, thresholds,
                                   include_test_cases=True,
                                   include_patterns=True)
                                    ↓
                         테스트 케이스 + 패턴 분석 결과 포함
```

#### 3.2.3 프롬프트 개선

**현재 프롬프트 (메트릭 점수만):**
```
## 분석 대상
- 메트릭: Faithfulness (충실도)
- 점수: 0.833 / 1.0
- 임계값: 0.70
- 상태: 통과
```

**개선된 프롬프트 (테스트 케이스 포함):**
```
## 분석 대상
- 메트릭: Faithfulness (충실도)
- 점수: 0.833 / 1.0
- 임계값: 0.70
- 상태: 통과
- 총 테스트 케이스: 10개
- 통과 케이스: 8개
- 실패 케이스: 2개

## 실패 케이스 상세
### 케이스 1 (ID: tc-003)
- 질문: "실손보험 청구 시 필요한 서류는?"
- 답변: "의료비 영수증, 진단서, 통장 사본이 필요합니다."
- 컨텍스트: ["실손보험 청구 시에는..."]
- 점수: 0.45
- 탐지된 패턴: hallucination (컨텍스트에 없는 정보 포함)

### 케이스 2 (ID: tc-007)
...

## 분석 요청
위 실패 케이스들을 기반으로 구체적인 원인과 개선 방안을 제시해주세요.
```

### 3.3 Phase 3: 패턴 탐지 통합 (2일)

#### 3.3.1 PatternDetector 결과 활용

```python
# pattern_detector.py의 결과 구조
@dataclass
class PatternEvidence:
    pattern_type: PatternType
    affected_count: int
    total_count: int
    correlation: float | None
    p_value: float | None
    affected_mean_score: float
    unaffected_mean_score: float
    description: str
    representative_samples: list[FailureSample]
```

#### 3.3.2 보고서 통합 예시

```markdown
## 탐지된 실패 패턴

### 1. Hallucination (환각) - 영향도: 높음
- **영향 케이스**: 3/10 (30%)
- **통계적 유의성**: p-value = 0.023
- **평균 점수 차이**: 0.45 (영향) vs 0.89 (비영향)

**대표 실패 사례:**
> 질문: "보험료 납입 방법은?"
> 답변: "월납, 연납, 일시납 중 선택 가능하며, **카드 자동이체 시 5% 할인**됩니다."
> 문제: 밑줄 친 부분이 컨텍스트에 없는 정보

### 2. Missing Context (컨텍스트 누락) - 영향도: 중간
...
```

### 3.4 Phase 4: 통계 분석 통합 (2일)

#### 3.4.1 StatisticalAnalysis 결과 활용

```python
# analysis_service.py의 결과 구조
@dataclass
class StatisticalAnalysis:
    metric_stats: dict[str, MetricStatistics]
    correlation_matrix: dict[str, dict[str, float]]
    significant_correlations: list[CorrelationInsight]
    low_performers: list[LowPerformerInfo]
    pass_rate_analysis: PassRateAnalysis
    insights: list[str]
```

#### 3.4.2 보고서 통합 예시

```markdown
## 통계 분석

### 메트릭 분포
| 메트릭 | 평균 | 표준편차 | 최소 | 최대 | 중앙값 |
|--------|------|----------|------|------|--------|
| faithfulness | 0.83 | 0.15 | 0.45 | 1.00 | 0.87 |
| answer_relevancy | 0.65 | 0.22 | 0.32 | 0.95 | 0.68 |

### 상관관계 분석
- faithfulness ↔ factual_correctness: **0.78** (강한 양의 상관)
- context_precision ↔ context_recall: **-0.23** (약한 음의 상관)

### 저성과 케이스 (하위 10%)
1. tc-003: 모든 메트릭에서 저성과
2. tc-007: faithfulness, factual_correctness 저성과
```

### 3.5 Phase 5: 개선 가이드 연동 (2일)

#### 3.5.1 ImprovementGuideService 재사용

현재 Improve 페이지에서 사용하는 `ImprovementGuideService`의 결과를
Reports 페이지 AI 분석에서도 활용합니다.

```python
# 개선 가이드 서비스 호출
improvement_service = ImprovementGuideService(
    pattern_detector=PatternDetector(),
    insight_generator=InsightGenerator(llm_adapter),
)
report = improvement_service.generate_report(run, include_llm_insights=True)
```

#### 3.5.2 보고서 통합

```markdown
## 권장 개선 액션

### P0 (즉시 실행) - Generator 개선
**대상 메트릭**: factual_correctness

| 액션 | 예상 개선 | 난이도 | 출처 |
|------|-----------|--------|------|
| Temperature 감소 (0.7→0.0) | +8% | 낮음 | 규칙 기반 |
| 프롬프트 강화 | +15% | 낮음 | 규칙 기반 |
| Fact verification chain | +18% | 높음 | LLM 분석 |

**검증 방법:**
```bash
evalvault run dataset.json --metrics factual_correctness --tag baseline
# ... 개선 적용 ...
evalvault run dataset.json --metrics factual_correctness --tag after_fix
evalvault compare baseline after_fix
```
```

### 3.6 Phase 6: 보고서 옵션 UI 개선 (1일)

#### 3.6.1 현재 ReportConfig
```python
@dataclass
class ReportConfig:
    output_format: Literal["markdown", "html"] = "markdown"
    include_summary: bool = True
    include_metrics_detail: bool = True
    include_charts: bool = True
    include_nlp_analysis: bool = False      # 미구현
    include_causal_analysis: bool = False   # 미구현
    template_name: str = "basic"
```

#### 3.6.2 확장된 ReportConfig
```python
@dataclass
class ReportConfig:
    # 기존 옵션
    output_format: Literal["markdown", "html"] = "markdown"
    include_summary: bool = True
    include_metrics_detail: bool = True
    include_charts: bool = True
    template_name: str = "basic"

    # 새로운 옵션
    include_test_case_details: bool = True   # 실패 케이스 상세
    include_pattern_analysis: bool = True    # 패턴 탐지 결과
    include_statistical_analysis: bool = True # 통계 분석
    include_improvement_guide: bool = True   # 개선 가이드 통합
    include_nlp_analysis: bool = False       # NLP 분석 (선택)
    include_causal_analysis: bool = False    # 인과 분석 (선택)
    max_failure_samples: int = 5             # 포함할 실패 샘플 수
```

## 4. 구현 우선순위

| 우선순위 | Phase | 작업 | 예상 기간 | 효과 |
|----------|-------|------|-----------|------|
| P0 | 1 | 시간 추정 수정 | 1일 | UX 개선 |
| P0 | 2 | 테스트 케이스 통합 | 3일 | 구체적 분석 |
| P1 | 3 | 패턴 탐지 통합 | 2일 | 근본 원인 파악 |
| P1 | 4 | 통계 분석 통합 | 2일 | 정량적 인사이트 |
| P1 | 5 | 개선 가이드 연동 | 2일 | 실행 가능한 제안 |
| P2 | 6 | UI 옵션 개선 | 1일 | 사용자 커스터마이징 |

**총 예상 기간: 11일**

## 5. 아키텍처 변경

### 5.1 현재 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      Web UI (Reports)                    │
│                           ↓                              │
│              LLMReportGenerator.generate_report()        │
│                           ↓                              │
│              메트릭 점수 → LLM 프롬프트 → 보고서         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 개선된 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      Web UI (Reports)                    │
│                           ↓                              │
│              EnhancedReportGenerator.generate()          │
│                    ↓         ↓         ↓                 │
│    ┌───────────────┐ ┌───────────┐ ┌──────────────┐     │
│    │PatternDetector│ │AnalysisSvc│ │ImprovementSvc│     │
│    └───────┬───────┘ └─────┬─────┘ └──────┬───────┘     │
│            ↓               ↓              ↓              │
│         패턴 결과      통계 분석      개선 가이드        │
│            └───────────────┼──────────────┘              │
│                            ↓                             │
│                  통합 컨텍스트 구성                      │
│                            ↓                             │
│              LLM 프롬프트 (풍부한 컨텍스트)              │
│                            ↓                             │
│                   종합 AI 분석 보고서                    │
└─────────────────────────────────────────────────────────┘
```

## 6. 예상 결과물

### 6.1 개선 전 보고서 구조
```
1. Executive Summary (일반적)
2. faithfulness 분석 (점수 기반 일반 제안)
3. answer_relevancy 분석 (점수 기반 일반 제안)
...
```

### 6.2 개선 후 보고서 구조
```
1. Executive Summary (구체적 실패 사례 기반)
2. 탐지된 실패 패턴 요약
   - 패턴별 영향도 및 통계
   - 대표 실패 사례
3. 메트릭별 심층 분석
   - 점수 + 실패 케이스 + 패턴 연관성
   - 통계 분석 (분포, 상관관계)
4. 우선순위화된 개선 액션
   - P0/P1/P2 분류
   - 예상 효과 및 검증 방법
5. 부록: 상세 데이터
   - 전체 실패 케이스 목록
   - 통계 상세
```

## 7. 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 보고서 내 실패 사례 수 | 0 | 5+ |
| 구체적 개선 액션 수 | ~3 (일반적) | 10+ (구체적) |
| 패턴 탐지 결과 포함 | X | O |
| 통계 분석 포함 | X | O |
| 검증 가능한 액션 비율 | 0% | 80%+ |

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| LLM 토큰 한도 초과 | 보고서 잘림 | 점진적 요약, 중요도 기반 필터링 |
| 생성 시간 증가 | UX 저하 | 프로그레스 표시, 병렬 처리 |
| 프롬프트 복잡도 증가 | 품질 저하 | 단계별 생성, 검증 루프 |

## 9. 다음 단계

1. **Phase 1 구현**: 시간 추정 문구 수정
2. **Phase 2 설계 검토**: 테스트 케이스 통합 방식 확정
3. **프로토타입**: 작은 데이터셋으로 검증
4. **전체 구현**: 순차적 Phase 진행
