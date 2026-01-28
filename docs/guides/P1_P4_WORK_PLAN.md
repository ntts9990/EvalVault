# P1-P4 작업 계획서

> **작성일**: 2026-01-27
> **기준 문서**: `reports/feature_verification_report.md`
> **목적**: Gap 분석 결과 도출된 P1-P4 작업의 상세 실행 계획

---

## 개요

기능 종합 검증 보고서에서 식별된 4개 개선 영역의 구체적 작업 계획을 정의한다.

| 우선순위 | 영역 | 예상 기간 | 영향도 |
|---------|------|----------|-------|
| P1 | 자동 회귀 게이트 (CI/CD) | 1-2주 | 높음 |
| P2 | 멀티턴 RAG 평가 | 2-4주 | 중간 |
| P3 | GraphRAG 실험 프레임워크 | 4-6주 | 중간 |
| P4 | Judge 캘리브레이션 Web UI | 1-2주 | 낮음 |

---

## P1: 자동 회귀 게이트 (CI/CD 통합)

### 목표

PR/릴리즈 시점에 자동으로 RAG 평가를 실행하고, threshold 미달 시 배포를 차단하는 품질 게이트 구축

### 배경

현재 `evalvault gate` 명령은 존재하지만, CI/CD 파이프라인과의 자동 연동이 없어 수동 실행에 의존

### 작업 항목

#### 1.1 GitHub Actions 워크플로 작성

**파일**: `.github/workflows/regression-gate.yml`

```yaml
# 설계 스펙
name: RAG Regression Gate
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  regression-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
      - name: Setup Python & uv
      - name: Run baseline evaluation
      - name: Compare with previous run
      - name: Quality gate check
      - name: Post PR comment with results
```

**구현 세부**:
- 베이스라인 데이터셋: `tests/fixtures/e2e/regression_baseline.json`
- 비교 대상: 직전 main 브랜치의 마지막 성공 run_id
- 게이트 조건: 모든 메트릭이 threshold 이상 + 회귀율 < 5%

#### 1.2 CLI 회귀 게이트 커맨드 강화

**파일**: `src/evalvault/adapters/inbound/cli/commands/regress.py`

**추가 기능**:
```python
# 설계 스펙
@app.command()
def ci_gate(
    baseline_run_id: str,
    current_run_id: str,
    regression_threshold: float = 0.05,  # 5% 허용
    output_format: str = "github",  # github, gitlab, json
    fail_on_regression: bool = True,
):
    """CI/CD 파이프라인용 회귀 게이트 체크"""
```

#### 1.3 PR 코멘트 포매터

**파일**: `src/evalvault/adapters/outbound/report/ci_report_formatter.py`

**출력 예시**:
```markdown
## RAG Regression Gate Results

| Metric | Baseline | Current | Change | Status |
|--------|----------|---------|--------|--------|
| faithfulness | 0.85 | 0.87 | +2.4% | ✅ |
| answer_relevancy | 0.82 | 0.80 | -2.4% | ⚠️ |

**Gate Status**: ✅ PASSED (regression: 1.2% < 5% threshold)
```

### 검증 기준

- [ ] PR 생성 시 자동으로 회귀 테스트 실행
- [ ] threshold 미달 시 PR 머지 차단
- [ ] PR 코멘트에 결과 리포트 게시
- [ ] 단위 테스트 추가 (10개 이상)

### 의존성

- 기존 `compare` 기능 활용
- GitHub Actions secrets 설정 (OPENAI_API_KEY)

---

## P2: 멀티턴 RAG 평가 체계

### 목표

대화형 RAG 시스템의 턴별 품질을 평가하고, 대화 드리프트를 감지하는 벤치마크 체계 구축

### 배경

현재 평가 체계는 단일 Q&A에 최적화되어 있어, 멀티턴 대화의 맥락 누적 문제를 평가하지 못함

### 작업 항목

#### 2.1 멀티턴 데이터셋 스키마 정의

**파일**: `src/evalvault/domain/entities/multiturn.py`

```python
# 설계 스펙
@dataclass
class ConversationTurn:
    turn_id: str
    role: Literal["user", "assistant"]
    content: str
    contexts: list[str] | None = None
    ground_truth: str | None = None
    metadata: dict = field(default_factory=dict)

@dataclass
class MultiTurnTestCase:
    conversation_id: str
    turns: list[ConversationTurn]
    expected_final_answer: str | None = None
    drift_tolerance: float = 0.1  # 허용 드리프트
```

#### 2.2 멀티턴 메트릭 추가

**파일**: `src/evalvault/domain/metrics/multiturn_metrics.py`

| 메트릭 | 설명 | 계산 방식 |
|-------|------|----------|
| `turn_faithfulness` | 턴별 근거 충실도 | 각 턴의 faithfulness 평균 |
| `context_coherence` | 맥락 일관성 | 턴 간 컨텍스트 연결성 |
| `drift_rate` | 대화 드리프트 | 초기 의도 대비 최종 응답 거리 |
| `turn_latency` | 턴별 응답 시간 | 각 턴의 p95 지연 |

#### 2.3 멀티턴 평가 서비스

**파일**: `src/evalvault/domain/services/multiturn_evaluator.py`

```python
# 설계 스펙
class MultiTurnEvaluator:
    def evaluate_conversation(
        self,
        conversation: MultiTurnTestCase,
        metrics: list[str],
    ) -> MultiTurnEvaluationResult:
        """대화 전체를 평가하고 턴별 결과를 반환"""

    def detect_drift(
        self,
        conversation: MultiTurnTestCase,
        threshold: float = 0.1,
    ) -> DriftAnalysis:
        """대화 드리프트 감지"""
```

#### 2.4 CLI 통합

**기존 `run` 커맨드 확장**:
```bash
uv run evalvault run --mode multiturn conversation_dataset.json \
  --metrics turn_faithfulness,context_coherence,drift_rate \
  --max-turns 10 \
  --drift-threshold 0.1
```

#### 2.5 벤치마크 데이터셋 생성

**파일**: `tests/fixtures/e2e/multiturn_benchmark.json`

- 최소 50개 대화 시나리오
- 3-10턴 범위
- 드리프트 케이스 포함 (10% 이상)

### 검증 기준

- [ ] 멀티턴 데이터셋 로딩 및 파싱
- [ ] 4개 멀티턴 메트릭 계산
- [ ] 드리프트 감지 및 경고
- [ ] 단위 테스트 추가 (30개 이상)
- [ ] 벤치마크 데이터셋 완성

### 의존성

- DatasetPort 확장 (멀티턴 스키마 지원)
- 기존 RagasEvaluator와의 호환성 유지

---

## P3: GraphRAG 실험 프레임워크

### 목표

엔티티/관계 기반 GraphRAG와 기존 top-k RAG를 동일 조건에서 비교 실험할 수 있는 프레임워크 구축

### 배경

복합 질의(multi-hop reasoning)에서 GraphRAG가 우수하다는 연구 결과가 있으나, EvalVault에서 비교 실험이 불가능

### 작업 항목

#### 3.1 GraphRAG Stage 정의

**파일**: `src/evalvault/domain/entities/graph_rag.py`

```python
# 설계 스펙
@dataclass
class EntityNode:
    entity_id: str
    name: str
    entity_type: str  # person, organization, concept, ...
    attributes: dict = field(default_factory=dict)

@dataclass
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: str  # belongs_to, mentions, related_to, ...
    weight: float = 1.0
    attributes: dict = field(default_factory=dict)

@dataclass
class KnowledgeSubgraph:
    """질의에 대해 추출된 관련 서브그래프"""
    nodes: list[EntityNode]
    edges: list[RelationEdge]
    relevance_score: float
```

#### 3.2 GraphRAG Retriever 포트

**파일**: `src/evalvault/ports/outbound/graph_retriever_port.py`

```python
# 설계 스펙
class GraphRetrieverPort(Protocol):
    def extract_entities(self, text: str) -> list[EntityNode]:
        """텍스트에서 엔티티 추출"""

    def build_subgraph(
        self,
        query: str,
        max_hops: int = 2,
        max_nodes: int = 20,
    ) -> KnowledgeSubgraph:
        """질의 관련 서브그래프 구축"""

    def generate_context(
        self,
        subgraph: KnowledgeSubgraph,
    ) -> str:
        """서브그래프를 LLM 컨텍스트로 변환"""
```

#### 3.3 GraphRAG 어댑터 구현

**파일**: `src/evalvault/adapters/outbound/retriever/graph_rag_adapter.py`

**구현 옵션**:
- Option A: NetworkX + LLM 엔티티 추출
- Option B: LightRAG 라이브러리 래핑
- Option C: Neo4j 연동 (선택적)

#### 3.4 A/B 비교 실험 템플릿

**파일**: `src/evalvault/domain/services/graph_rag_experiment.py`

```python
# 설계 스펙
class GraphRAGExperiment:
    def run_comparison(
        self,
        dataset: Dataset,
        baseline_retriever: RetrieverPort,  # top-k
        graph_retriever: GraphRetrieverPort,
        metrics: list[str],
    ) -> ExperimentComparisonResult:
        """동일 데이터셋에서 두 retriever 비교"""
```

#### 3.5 CLI 통합

```bash
# GraphRAG 평가
uv run evalvault run dataset.json \
  --retriever graph \
  --graph-max-hops 2 \
  --graph-max-nodes 20

# A/B 비교
uv run evalvault experiment create \
  --name "topk-vs-graphrag" \
  --control-retriever topk \
  --variant-retriever graph \
  --dataset dataset.json
```

#### 3.6 아티팩트 저장

GraphRAG 실행 시 추가 아티팩트:
```
reports/analysis/artifacts/analysis_<RUN_ID>/
├── index.json
├── graph_subgraphs/
│   ├── tc_001_subgraph.json
│   ├── tc_002_subgraph.json
│   └── ...
└── entity_extraction/
    └── entities.json
```

### 검증 기준

- [ ] 엔티티 추출 및 관계 구축
- [ ] 서브그래프 기반 컨텍스트 생성
- [ ] top-k vs GraphRAG A/B 비교
- [ ] 단위 테스트 추가 (40개 이상)
- [ ] 비교 실험 벤치마크 완성

### 의존성

- 기존 KGPort 활용 가능
- LLM 기반 엔티티 추출 (OpenAI/Anthropic)

---

## P4: Judge 캘리브레이션 Web UI

### 목표

CLI에서만 가능한 Judge 캘리브레이션 기능을 Web UI에서도 사용할 수 있도록 확장

### 배경

`calibrate-judge` CLI는 구현되어 있으나, Web UI에서는 결과 조회만 가능하고 실행/설정이 불가능

### 작업 항목

#### 4.1 API 엔드포인트 추가

**파일**: `src/evalvault/adapters/inbound/api/routers/calibration.py`

```python
# 설계 스펙
@router.post("/api/calibration/judge")
async def run_judge_calibration(
    request: JudgeCalibrationRequest,
) -> JudgeCalibrationResponse:
    """Judge 캘리브레이션 실행"""

@router.get("/api/calibration/judge/{calibration_id}")
async def get_calibration_result(
    calibration_id: str,
) -> JudgeCalibrationResponse:
    """캘리브레이션 결과 조회"""

@router.get("/api/calibration/judge/history")
async def list_calibrations(
    limit: int = 20,
) -> list[JudgeCalibrationSummary]:
    """캘리브레이션 히스토리"""
```

#### 4.2 React 페이지 추가

**파일**: `frontend/src/pages/JudgeCalibration.tsx`

**UI 구성**:
```
┌─────────────────────────────────────────────────────────────┐
│ Judge Calibration                                           │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────────────────────────┐│
│ │ Settings        │  │ Results                             ││
│ │                 │  │                                     ││
│ │ Dataset: [___]  │  │ ┌─────────────────────────────────┐ ││
│ │ Judge: [___]    │  │ │ Agreement Matrix                │ ││
│ │ Samples: [___]  │  │ │ ┌───┬───┬───┬───┐              │ ││
│ │                 │  │ │ │   │ H │ M │ L │              │ ││
│ │ [Run Calibration│  │ │ ├───┼───┼───┼───┤              │ ││
│ └─────────────────┘  │ │ │ H │85%│10%│5% │              │ ││
│                      │ │ ├───┼───┼───┼───┤              │ ││
│ ┌─────────────────┐  │ │ │ M │8% │80%│12%│              │ ││
│ │ History         │  │ │ ├───┼───┼───┼───┤              │ ││
│ │ • 2026-01-27... │  │ │ │ L │5% │15%│80%│              │ ││
│ │ • 2026-01-26... │  │ │ └───┴───┴───┴───┘              │ ││
│ │ • 2026-01-25... │  │ └─────────────────────────────────┘ ││
│ └─────────────────┘  │                                     ││
│                      │ Metrics:                            ││
│                      │ • Cohen's Kappa: 0.78               ││
│                      │ • Agreement Rate: 85%               ││
│                      │ • Bias Score: 0.02                  ││
│                      └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### 4.3 시각화 컴포넌트

**파일**: `frontend/src/components/calibration/`

- `AgreementMatrix.tsx` - 일치도 히트맵
- `BiasChart.tsx` - 편향 분석 차트
- `CalibrationTrend.tsx` - 시간별 추이

#### 4.4 라우터 등록

**파일**: `frontend/src/App.tsx`

```tsx
<Route path="/calibration" element={<JudgeCalibration />} />
```

**네비게이션**: Settings 하위 또는 독립 메뉴 항목

### 검증 기준

- [ ] API 엔드포인트 3개 동작
- [ ] Web UI 페이지 렌더링
- [ ] 캘리브레이션 실행 및 결과 표시
- [ ] 히스토리 조회
- [ ] 프론트엔드 테스트 추가

### 의존성

- 기존 `JudgeCalibrationService` 활용
- React Query 또는 SWR로 데이터 페칭

---

## 실행 로드맵

```
Week 1-2: P1 (자동 회귀 게이트)
  ├── GitHub Actions 워크플로
  ├── CI 게이트 커맨드
  └── PR 코멘트 포매터

Week 2-4: P4 (Judge 캘리브레이션 UI) [병렬 가능]
  ├── API 엔드포인트
  ├── React 페이지
  └── 시각화 컴포넌트

Week 3-6: P2 (멀티턴 평가)
  ├── 데이터셋 스키마
  ├── 멀티턴 메트릭
  ├── 평가 서비스
  └── 벤치마크 데이터셋

Week 6-12: P3 (GraphRAG)
  ├── Stage 정의
  ├── Retriever 포트/어댑터
  ├── A/B 실험 프레임워크
  └── 비교 벤치마크
```

```
         Week 1    Week 2    Week 3    Week 4    Week 5    Week 6    ...
P1       ████████████████
P4       ░░░░░░░░████████████████
P2                 ░░░░░░░░████████████████████████████████
P3                                   ░░░░░░░░░░░░░░░░████████████████...

█ = Active Development
░ = Planning/Prep
```

---

## 리소스 요구사항

### P1: 자동 회귀 게이트
- 개발자: 1명
- 예상 공수: 40시간
- 외부 의존성: GitHub Actions

### P2: 멀티턴 평가
- 개발자: 1-2명
- 예상 공수: 80시간
- 외부 의존성: 없음 (기존 인프라 활용)

### P3: GraphRAG
- 개발자: 2명
- 예상 공수: 160시간
- 외부 의존성: LightRAG 또는 Neo4j (선택)

### P4: Judge 캘리브레이션 UI
- 개발자: 1명 (프론트엔드)
- 예상 공수: 40시간
- 외부 의존성: 없음

---

## 위험 요소 및 완화 방안

| 위험 | 영향 | 완화 방안 |
|-----|------|----------|
| P1: CI 시간 초과 | 중 | 경량 데이터셋 + 캐싱 |
| P2: 멀티턴 메트릭 정의 불명확 | 높음 | 학술 논문 기반 명확한 정의 |
| P3: GraphRAG 복잡도 | 높음 | 단계적 구현 (v0: 휴리스틱 → v1: LLM) |
| P4: 프론트엔드 복잡도 | 낮음 | 기존 컴포넌트 재사용 |

---

## 성공 기준

### P1
- [ ] PR 생성 시 자동 회귀 테스트 실행 (100%)
- [ ] 회귀 감지 정확도 > 95%
- [ ] CI 실행 시간 < 10분

### P2
- [ ] 멀티턴 데이터셋 50개 이상 평가 가능
- [ ] 드리프트 감지 정확도 > 90%
- [ ] 기존 단일턴 평가와 호환

### P3
- [ ] top-k vs GraphRAG A/B 비교 가능
- [ ] multi-hop 질의에서 GraphRAG 우위 입증
- [ ] 아티팩트에 서브그래프 저장

### P4
- [ ] Web UI에서 캘리브레이션 실행 가능
- [ ] 결과 시각화 (히트맵, 차트)
- [ ] 히스토리 조회 가능

---

## 추가 검증 스크립트

Web UI의 Dashboard 렌더링 이슈(맥OS GUI 백엔드 충돌)를 방지하기 위해
Dashboard 엔드포인트 검증 스크립트를 추가했다.

- 스크립트: `scripts/dev/verify_dashboard_endpoint.sh`
- 용도: `/api/v1/runs/{run_id}/dashboard` 응답이 정상 PNG로 내려오는지 확인

---

## 참고 문서

- `reports/feature_verification_report.md` - 기능 검증 보고서
- `docs/ROADMAP.md` - 프로젝트 로드맵
- `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md` - 성능 개선 제안서
- `docs/new_whitepaper/` - 개발 백서

---

*본 계획서는 feature_verification_report.md의 Gap 분석 결과를 기반으로 작성되었습니다.*
