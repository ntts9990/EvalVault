## 제5부: 전문가 관점 통합 설계

### 5.1 인지심리학자 관점 (Cognitive Psychologist Perspective)

### 5.1.1 인지 부하 최소화 (Minimizing Cognitive Load)

**인지심리학적 근거**:
- 인간의 작업 기억 용량은 제한적 (7±2 청크)
- 과도한 정보는 인지 부하 증가 → 오류율 증가
- 청크 단위로 정보를 나누어 처리하면 기억 부담 감소

**EvalVault 적용**:

#### 5.1.1.1 점진적 정보 공개 (Progressive Disclosure)

**원칙**: 기본 정보에서 시작하여 필요할 때만 상세 정보를 공개

**구현 방법**:

1. **요약(Summary) → 상세(Detail) → 심화(Deep) 3단계 구조**

```python
# 백서 구조 예시
## 제1부: 프로젝트 개요
### 1.1 비전과 미션
# [기본 정보: 3~5개 핵심 포인트]

## 제4부: 주요 컴포넌트 상세
### 4.1 도메인 엔티티
# [상세 정보: 엔티티 정의, 메서드, 코드 예시]
```

2. **UI에서의 계층적 노출 (Layered Disclosure)**

```python
# Web UI 구현 예시
class EvaluationStudio:
    """평가 스튜디오"""

    def __init__(self):
        self._view_state = "summary"  # summary, detail, deep

    def render_summary(self):
        """요약 뷰: 기본 정보만 표시"""
        return {
            "title": "평가 요약",
            "widgets": [
                {"type": "pass_rate_card", "show_all": False},
                {"type": "metric_chart", "show_all": False},
            ]
        }

    def render_detail(self):
        """상세 뷰: 모든 메트릭 정보 표시"""
        return {
            "title": "평가 상세",
            "widgets": [
                {"type": "pass_rate_card", "show_all": True},
                {"type": "metric_chart", "show_all": True},
                {"type": "test_case_table", "show_all": True},
            ]
        }

    def render_deep(self):
        """심화 뷰: Phoenix 연동, Stage 메트릭"""
        return {
            "title": "심화 분석",
            "widgets": [
                {"type": "pass_rate_card", "show_all": True},
                {"type": "metric_chart", "show_all": True},
                {"type": "test_case_table", "show_all": True},
                {"type": "stage_metrics", "show_all": True},
                {"type": "phoenix_link", "show_all": True},
            ]
        }
```

3. **아코디언 접힘 (Accordion) 패턴**

```html
<!-- 아코디언 패턴으로 정보를 그룹화 -->
<details class="accordion-item" data-expanded="false">
  <summary class="accordion-header">
    <span class="icon">📊</span>
    <span class="title">메트릭 상세</span>
  </summary>
  <div class="accordion-content">
    <table class="metrics-table">
      <!-- 메트릭 테이블 -->
    </table>
  </div>
</details>
```

**인지 효과**:
- 사용자는 처음에 3~5개 핵심 정보만 봄 → 인지 부하 최소화
- 필요할 때만 아코디언을 펼�서 상세 정보 확인
- 정보를 논리적으로 그룹화하여 기억 부담 감소

#### 5.1.1.2 시각적 그룹핑 (Visual Grouping)

**원칙**: 유사한 패턴을 시각적으로 그룹화하여 패턴 인식 촉진

**구현 방법**:

1. **성공/실패 케이스를 색상으로 즉시 구분**

```css
/* 색상 인코딩 체계 */
.test-case {
    --success-primary: #22c55e;  /* Green 500 */
    --success-hover: #16a34a;   /* Green 600 */
    --success-text: #ffffff;

    --failure-primary: #ef4444;  /* Red 500 */
    --failure-hover: #dc2626;   /* Red 600 */
    --failure-text: #ffffff;

    --warning-primary: #f59e0b;  /* Yellow 400 */
    --warning-hover: #d97706;   /* Yellow 500 */
    --warning-text: #000000;
}

/* 성공 케이스 */
.test-case.success {
    border-left: 4px solid var(--success-primary);
    background-color: var(--success-primary);
    color: var(--success-text);
}

/* 실패 케이스 */
.test-case.failure {
    border-left: 4px solid var(--failure-primary);
    background-color: var(--failure-primary);
    color: var(--failure-text);
}
```

2. **메트릭 그룹을 공간적으로 배치**

```python
# 메트릭 그룹 예시
METRIC_GROUPS = {
    "faithfulness": {
        "name": "충실도 (Faithfulness)",
        "description": "답변이 컨텍스트에 얼마나 충실한지",
        "icon": "✓",
        "color": "blue",
    },
    "answer_relevancy": {
        "name": "답변 관련성 (Answer Relevancy)",
        "description": "답변이 질문의도와 얼마나 관련있는지",
        "icon": "💬",
        "color": "purple",
    },
    "context_precision": {
        "name": "컨텍스트 정밀도 (Context Precision)",
        "description": "검색된 컨텍스트가 얼마나 관련성 있는지",
        "icon": "🎯",
        "color": "orange",
    },
}
```

**인지 효과**:
- 색상으로 성공/실패를 즉시 인지 → 판정 시간 단축
- 그룹별 아이콘으로 메트릭 유형 식별 → 카테고리 기억 부담 감소
- 시각적 그룹핑으로 패턴 인식 촉진

#### 5.1.1.3 단계별 시각적 구분 (Stage-level Visual Separation)

**원칙**: Retrieval → Rerank → Generation 단계를 시각적으로 구분

**구현 방법**:

```css
/* Stage별 색상 구분 */
.stage-badge {
    /* Input Stage */
    &.input {
        background-color: #9ca3af;  /* Gray */
        color: #ffffff;
        border: 2px solid #6b7280;
    }

    /* Retrieval Stage */
    &.retrieval {
        background-color: #3b82f6;  /* Blue */
        color: #ffffff;
        border: 2px solid #2563eb;
    }

    /* Rerank Stage */
    &.rerank {
        background-color: #f59e0b;  /* Yellow */
        color: #000000;
        border: 2px solid #d97706;
    }

    /* Output Stage */
    &.output {
        background-color: #10b981;  /* Green */
        color: #ffffff;
        border: 2px solid #059669;
    }
}
```

**인지 효과**:
- 각 단계를 색상으로 구분하여 병목 지점을 빠르게 식별
- 단계별 성능을 한눈에 비교 가능 → 패턴 인식 촉진
- 시각적 구분으로 파이프라인 흐름 직관적 이해

---

### 5.2 UI/UX 전문가 관점 (UI/UX Perspective)

### 5.2.1 워크플로우 최적화 (Workflow Optimization)

**UI/UX 원칙**:
- 자주 하는 작업을 빠르게 (수용자 시나리오 최적화)
- 명확한 사용자 경로 (Clear User Path) 제공
- 오류 방지 (Error Prevention)에 집중

**EvalVault 적용**:

#### 5.2.1.1 평가 실행 워크플로우 (Evaluation Workflow)

**사용자 시나리오**:
1. 데이터셋 업로드 → 2. 메트릭 선택 → 3. 모델 프로필 선택 → 4. 고급 설정 → 5. 실행

**최적화 전략**:

1. **데이터셋 미리보기 (Dataset Preview)**

```python
# 데이터셋 업로드 시 자동 검증
class DatasetUploader:
    """데이터셋 업로더"""

    async def upload(self, file: UploadFile) -> DatasetPreview:
        """데이터셋 업로드 및 미리보기"""
        # 1. 파일 형식 자동 감지
        file_type = detect_file_type(file.filename)

        # 2. 파일 파싱
        data = await parse_file(file, file_type)

        # 3. 데이터 검증
        validation_result = validate_dataset(data)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"데이터셋 검증 실패: {validation_result.errors}",
            )

        # 4. 미리보기 생성
        preview = DatasetPreview(
            total_cases=len(data.test_cases),
            sample_cases=data.test_cases[:5],  # 처음 5개 샘플
            columns=list(data.test_cases[0].keys()),
        )

        return preview

# 미리보기 UI 표시
<div class="dataset-preview">
  <h3>📋 데이터셋 미리보기</h3>
  <div class="preview-stats">
    <span class="stat-item">
      <span class="value">150</span>
      <span class="label">전체 케이스</span>
    </span>
    <span class="stat-item">
      <span class="value">3</span>
      <span class="label">컬럼</span>
    </span>
  </div>
  <div class="sample-table">
    <h4>샘플 (처음 5개)</h4>
    <table class="preview-table">
      <!-- 샘플 데이터 -->
    </table>
  </div>
</div>
```

2. **빠른 메트릭 선택 (Quick Metric Selection)**

```html
<!-- 자주 쓰는 메트릭 상단 표시 -->
<div class="quick-metrics">
  <h3>🎯 자주 쓰는 메트릭</h3>
  <div class="metric-chips">
    <button class="metric-chip selected" data-metric="faithfulness">
      ✓ Faithfulness
    </button>
    <button class="metric-chip selected" data-metric="answer_relevancy">
      ✓ Answer Relevancy
    </button>
    <button class="metric-chip" data-metric="context_precision">
      Context Precision
    </button>
  </div>

  <div class="advanced-metrics">
    <details>
      <summary>고급 메트릭 설정</summary>
      <div class="advanced-list">
        <label class="metric-checkbox">
          <input type="checkbox" checked>
          Context Recall
        </label>
        <label class="metric-checkbox">
          <input type="checkbox">
          Factual Correctness
        </label>
      </div>
    </details>
  </div>
</div>
```

3. **한 화면에서 실행 가능 (Single-page Evaluation)**

```python
# 평가 실행 페이지 구조
class EvaluationStudioPage:
    """평가 스튜디오 페이지"""

    def render(self):
        """평가 실행 한 화면 렌더링"""
        return {
            "title": "평가 실행",
            "sections": [
                {
                    "id": "dataset",
                    "title": "📊 1. 데이터셋 선택",
                    "component": DatasetUploader,
                    "collapsible": False,
                },
                {
                    "id": "metrics",
                    "title": "🎯 2. 메트릭 선택",
                    "component": MetricSelector,
                    "collapsible": False,
                },
                {
                    "id": "model",
                    "title": "🤖 3. 모델 선택",
                    "component": ModelProfileSelector,
                    "collapsible": False,
                },
                {
                    "id": "advanced",
                    "title": "⚙️ 4. 고급 설정",
                    "component": AdvancedSettings,
                    "collapsible": True,  # 기본 접힘
                    "default_expanded": False,
                },
            ],
            "actions": [
                {
                    "type": "primary",
                    "label": "🚀 평가 실행",
                    "loading_text": "평가 중...",
                    "success_text": "평가 완료!",
                },
                {
                    "type": "secondary",
                    "label": "💾 저장 후 실행",
                },
            ],
        }
```

**인지 효과**:
- 단일 화면에서 모든 단계 완료 → 페이지 전환 최소화
- 진행 상태 항상 표시 → 사용자 불안감 감소
- 검증된 데이터만 실행 가능 → 에러 방지

#### 5.2.1.2 인터랙션 디자인 (Interaction Design)

**UI/UX 원칙**:
- 모든 액션에 즉각적 피드백 제공
- 호버(Hover)와 클릭(Click)으로 단계적 정보 공개

**EvalVault 적용**:

```html
<!-- 호버: 상세 정보 미리보기 -->
<div class="test-case-card" data-test-id="tc-001">
  <div class="card-header">
    <span class="badge success">✓ PASS</span>
    <span class="question">보장금액은 얼마인가요?</span>
  </div>

  <div class="card-body">
    <div class="answer">
      <strong>답변:</strong>
      <span>보장금액은 1억원입니다.</span>
    </div>

    <!-- 호버 시 상세 메트릭 표시 -->
    <div class="hover-metrics">
      <h4>📊 메트릭 상세</h4>
      <div class="metric-row">
        <span class="metric-name">Faithfulness:</span>
        <span class="metric-score">0.90</span>
        <span class="metric-bar">
          <div class="bar-fill" style="width: 90%"></div>
        </span>
      </div>
      <div class="metric-row">
        <span class="metric-name">Answer Relevancy:</span>
        <span class="metric-score">0.85</span>
        <span class="metric-bar">
          <div class="bar-fill warning" style="width: 85%"></div>
        </span>
      </div>
    </div>
  </div>

  <!-- 클릭 시 상세 페이지로 이동 -->
  <div class="card-footer">
    <a href="/evaluations/run-abc123/test-cases/tc-001" class="detail-link">
      상세 보기 →
    </a>
  </div>
</div>

<style>
.hover-metrics {
  display: none;
  position: absolute;
  z-index: 100;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.test-case-card:hover .hover-metrics {
  display: block;
}

.metric-bar {
  width: 100px;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #22c55e;
  transition: width 0.3s ease;
}

.bar-fill.warning {
  background: #f59e0b;
}
</style>
```

**인지 효과**:
- 호버로 빠르게 상태 확인 → 마우스 이동 최소화
- 클릭으로 상세 페이지 이동 → 의도적 탐색 가능
- 시각적 피드백으로 사용자 행동 확신

---

### 5.3 정보공학 전문가 관점 (Information Engineering Perspective)

### 5.3.1 정보 아키텍처 (Information Architecture)

**정보공학 원칙**:
- 논리적 그룹핑과 계층 구조 (Logical Grouping & Hierarchical Structure)
- 명확한 레이블링과 분류 (Clear Labeling & Categorization)
- 검색 가능한 메타데이터 (Searchable Metadata)

**EvalVault 적용**:

#### 5.3.1.1 메타데이터 스키마 (Metadata Schema)

```python
# 평가 결과 메타데이터 스키마
@dataclass
class EvaluationMetadata:
    """평가 결과 메타데이터"""

    # 식별자 (Identifier)
    run_id: str
    dataset_name: str
    model_name: str

    # 컨텐츠 (Content)
    dataset_version: str
    metrics_evaluated: list[str]
    test_cases_count: int

    # 컨텍스트 (Context)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # 구조 (Structure)
    tags: list[str]
    categories: dict[str, str]

    # 시스템 (System)
    profile: str
    environment: str
    tracker_type: str | None

# 사용 예시
metadata = EvaluationMetadata(
    run_id="run-abc123",
    dataset_name="insurance-qa",
    model_name="gpt-4o-mini",
    dataset_version="1.0.0",
    metrics_evaluated=["faithfulness", "answer_relevancy"],
    test_cases_count=150,
    created_at=datetime.now(),
    tags=["insurance", "qa", "prod"],
    categories={"domain": "insurance", "environment": "prod"},
    profile="prod",
    environment="production",
    tracker_type="phoenix",
)
```

#### 5.3.1.2 정보 계층 구조 (Information Hierarchy)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    정보 계층 구조 (Information Hierarchy)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [레벨 1: 프로젝트 (Project)]                                            │
│      ├─ EvalVault                                                           │
│      ├─ 개발자 가이드 (Developer Guide)                                      │
│      └─ 사용자 가이드 (User Guide)                                        │
│          ↓                                                                    │
│  [레벨 2: 카테고리 (Category)]                                         │
│      ├─ 평가 (Evaluation)                                                  │
│      │   ├─ 데이터셋 (Dataset)                                              │
│      │   ├─ 메트릭 (Metrics)                                                 │
│      │   ├─ 실행 (Execution)                                                  │
│      │   └─ 결과 (Results)                                                  │
│      ├─ 분석 (Analysis)                                                     │
│      │   ├─ 통계 분석 (Statistical Analysis)                                  │
│      │   ├─ NLP 분석 (NLP Analysis)                                          │
│      │   ├─ 인과 분석 (Causal Analysis)                                      │
│      │   └─ 비교 분석 (Comparison Analysis)                                    │
│      ├─ 운영 (Operations)                                                    │
│      │   ├─ 모니터링 (Monitoring)                                            │
│      │   └─ 문제 해결 (Troubleshooting)                                    │
│          ↓                                                                    │
│  [레벨 3: 섹션 (Section)]                                              │
│      ├─ README.md                                                             │
│      ├─ ARCHITECTURE.md                                                       │
│      ├─ USER_GUIDE.md                                                        │
│      ├─ CHANGELOG.md                                                          │
│      └─ API Reference                                                        │
│          ↓                                                                    │
│  [레벨 4: 개념 (Concept)]                                               │
│      ├─ RAG (Retrieval-Augmented Generation)                                     │
│      ├─ 평가 (Evaluation)                                                     │
│      ├─ 메트릭 (Metrics)                                                        │
│      └─ 트레이싱 (Tracing)                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.3.1.3 검색 가능한 메타데이터 (Searchable Metadata)

```python
# 검색 메타데이터 생성
def generate_search_metadata(run: EvaluationRun) -> dict[str, Any]:
    """검색 가능한 메타데이터 생성"""
    return {
        "id": run.run_id,
        "title": f"{run.dataset_name} - {run.model_name}",
        "content": f"평가 결과: {run.pass_rate:.1%} 통과율",
        "metadata": {
            "dataset": run.dataset_name,
            "model": run.model_name,
            "metrics": ",".join(run.metrics_evaluated),
            "pass_rate": run.pass_rate,
            "tags": ["evaluation", "rag"],
            "created_at": run.created_at.isoformat(),
        },
        "categories": [
            run.dataset_name,
            run.model_name,
        ],
    }

# 검색 인덱스 생성 (MeiliSearch 등)
def index_run(run: EvaluationRun):
    """검색 인덱스 생성"""
    metadata = generate_search_metadata(run)

    # MeiliSearch에 인덱싱
    index.add_documents([{
        "id": metadata["id"],
        "title": metadata["title"],
        "content": metadata["content"],
        "metadata": metadata["metadata"],
    }])
```

### 5.4 아키텍트 관점 (Architect Perspective)

### 5.4.1 확장성 설계 (Scalability Architecture)

**아키텍트 원칙**:
- 포트 기반 설계로 새로운 기능 추가 용이
- 모듈화(Modularization)으로 컴포넌트 재사용성 향상
- 느슨한 결합(Loose Coupling)으로 시스템 부하 분산

**EvalVault 적용**:

#### 5.4.1.1 플러그인 아키텍처 (Plugin Architecture)

```python
# 플러그인 시스템 인터페이스
@dataclass
class MetricPlugin:
    """메트릭 플러그인 인터페이스"""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str

    def execute(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> float:
        """메트릭 계산"""
        pass

    def get_metadata(self) -> dict[str, Any]:
        """플러그인 메타데이터"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }

# 커스텀 메트릭 플러그인 구현
@dataclass
class CustomMetricPlugin(MetricPlugin):
    """커스텀 메트릭 플러그인"""

    plugin_id: "insurance-term-accuracy"
    name: "보험 용어 정확도"
    version: "1.0.0"
    description: "보험 도메인 용어 정확도 계산"
    author: "EvalVault Team"

    def execute(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> float:
        """메트릭 계산"""
        # 보험 용어 추출
        terms = extract_insurance_terms(answer)

        # 컨텍스트에서 용어 검증
        grounded_terms = []
        for term in terms:
            if is_term_in_contexts(term, contexts):
                grounded_terms.append(term)

        # 정확도 계산
        if not terms:
            return 1.0  # 용어가 없으면 완벽

        return len(grounded_terms) / len(terms)

    def get_metadata(self) -> dict[str, Any]:
        return super().get_metadata()

# 플러그인 레지스트리
class PluginRegistry:
    """플러그인 레지스트리"""

    def __init__(self):
        self._plugins: dict[str, MetricPlugin] = {}
        self._load_plugins()

    def _load_plugins(self):
        """플러그인 로드"""
        # 내장 플러그인 등록
        self.register_plugin(InsuranceTermAccuracy())

        # 외부 플러그인 로드 (plugins/ 디렉터리)
        import importlib
        for plugin_path in Path("plugins/").glob("*.py"):
            module = importlib.import_module(f"plugins.{plugin_path.stem}")
            plugin_class = getattr(module, "Plugin")
            self.register_plugin(plugin_class())

    def register_plugin(self, plugin: MetricPlugin):
        """플러그인 등록"""
        self._plugins[plugin.plugin_id] = plugin
        print(f"✅ 플러그인 등록: {plugin.name} v{plugin.version}")

    def get_plugin(self, plugin_id: str) -> MetricPlugin:
        """플러그인 조회"""
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[MetricPlugin]:
        """플러그인 목록"""
        return list(self._plugins.values())
```

#### 5.4.1.2 마이크로서비스 아키텍처 (Microservices Architecture)

```python
# 마이크로서비스 분리
# 각 서비스를 독립적인 마이크로서비스로 분리하여 확장성 향상

class EvaluationMicroservice:
    """평가 마이크로서비스"""

    def __init__(
        self,
        dataset_service: DatasetService,
        metrics_service: MetricsService,
        storage_service: StorageService,
    ):
        self.dataset_service = dataset_service
        self.metrics_service = metrics_service
        self.storage_service = storage_service

    async def evaluate(
        self,
        request: EvaluationRequest,
    ) -> EvaluationResult:
        """평가 실행"""
        # 1. 데이터셋 로드
        dataset = await self.dataset_service.load_dataset(request.dataset_id)

        # 2. 메트릭 계산 (병렬 처리 가능)
        metrics = await asyncio.gather([
            self.metrics_service.calculate_faithfulness(dataset),
            self.metrics_service.calculate_answer_relevancy(dataset),
            self.metrics_service.calculate_context_precision(dataset),
        ])

        # 3. 결과 저장
        await self.storage_service.save_result(EvaluationResult(
            run_id=request.run_id,
            metrics=metrics,
        ))

        return EvaluationResult(
            run_id=request.run_id,
            metrics=metrics,
        )

# API Gateway로 마이크로서비스 라우팅
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

@app.post("/api/v1/evaluate")
async def evaluate(request: EvaluationRequest):
    """평가 API 엔드포인트"""
    microservice = EvaluationMicroservice(
        dataset_service=DatasetService(),
        metrics_service=MetricsService(),
        storage_service=StorageService(),
    )

    result = await microservice.evaluate(request)
    return result
```

---

## 업데이트 이력

| 버전 | 날짜 | 변경 사항 | 담당 |
|------|------|----------|------|
| 1.0.0 | 2026-01-10 | 초기 작성 | EvalVault Team |

## 관련 섹션

- 섹션 1: 프로젝트 개요
- 섹션 2: 아키텍처 설계
- 섹션 4: 주요 컴포넌트 상세
- 섹션 6: 구현 상세
