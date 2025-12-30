# Implementation Roadmap

> **문서 버전**: 1.0.0
> **최종 업데이트**: 2025-12-30
> **Status**: NLP Analysis (계획) | Domain Memory Layering (완료)
>
> *이 문서는 기존 IMPLEMENTATION_PLAN_NLP_ANALYSIS.md, IMPLEMENTATION_PLAN_2026Q1.md를 통합한 문서입니다.*

---

## 개요

EvalVault의 구현 로드맵은 두 가지 주요 트랙으로 구성됩니다:

| 트랙 | 상태 | 설명 |
|------|------|------|
| **NLP Analysis (Phase 2)** | 계획됨 | 텍스트 통계, 질문 유형 분류, 키워드 추출 |
| **Domain Memory Layering** | ✅ 완료 | 도메인 지식 저장, 학습 패턴, 행동 핸드북 |

### 핵심 원칙

| 원칙 | 적용 방법 |
|------|-----------|
| **Hexagonal Architecture** | Port 인터페이스 정의 → Adapter 구현 |
| **TDD** | 테스트 먼저 작성 → 최소 구현 → 리팩토링 |
| **YAGNI** | 필요한 기능만 구현, 과도한 추상화 금지 |
| **SOLID** | 단일 책임, 인터페이스 분리 |

---

# Part 1: NLP Analysis Implementation (Phase 2)

## 1.1 목표

EvalVault에 NLP 분석, 데이터 저장, 보고서 생성 기능을 추가합니다. Hexagonal Architecture와 개발 정책(TDD, YAGNI)에 맞게 설계합니다.

### 의존성 관리

```
새 의존성 (필수): 없음 (기존 numpy, scipy 활용)

선택적 의존성 (Extras):
- sentence-transformers: 의미적 유사도 분석
- keybert: 키워드 추출 (sentence-transformers 의존)
```

## 1.2 아키텍처

```
src/evalvault/
├── domain/
│   └── entities/
│       └── analysis.py              # NLP 분석 엔티티 추가
├── ports/
│   └── outbound/
│       └── nlp_analysis_port.py     # NLP 분석 포트 인터페이스
├── adapters/
│   └── outbound/
│       └── analysis/
│           ├── statistical_adapter.py  # (기존)
│           └── nlp_adapter.py           # NLP 분석 어댑터
```

### 의존성 방향

```
CLI Adapter
    ↓
AnalysisService (domain/services)
    ↓
┌───────────────────────────────────┐
│           PORTS                   │
│  NLPAnalysisPort  AnalysisPort    │
└───────────────────────────────────┘
    ↓                   ↓
NLPAnalysisAdapter  StatisticalAdapter
```

## 1.3 구현 단계

### Phase 2.1: NLP 분석 엔티티 정의

**목표**: NLP 분석 결과를 표현하는 도메인 엔티티 추가

**엔티티 설계** (YAGNI - 최소 필요 속성만):

```python
@dataclass
class TextStats:
    """텍스트 기본 통계."""
    char_count: int
    word_count: int
    sentence_count: int
    avg_word_length: float
    unique_word_ratio: float  # 어휘 다양성

@dataclass
class QuestionTypeStats:
    """질문 유형별 통계."""
    type_name: str  # factual, reasoning, comparative, procedural, opinion
    count: int
    percentage: float
    avg_scores: dict[str, float]  # 메트릭별 평균 점수

@dataclass
class KeywordInfo:
    """키워드 정보."""
    keyword: str
    frequency: int
    tfidf_score: float
    avg_metric_scores: dict[str, float] | None = None

@dataclass
class NLPAnalysis:
    """NLP 분석 결과."""
    run_id: str
    question_stats: TextStats | None = None
    answer_stats: TextStats | None = None
    context_stats: TextStats | None = None
    question_types: list[QuestionTypeStats] = field(default_factory=list)
    top_keywords: list[KeywordInfo] = field(default_factory=list)
    topic_clusters: list[TopicCluster] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
```

### Phase 2.2: NLP 분석 포트 인터페이스

```python
class NLPAnalysisPort(Protocol):
    """NLP 분석 포트 인터페이스."""

    def analyze_text_statistics(self, run: EvaluationRun) -> NLPAnalysis:
        """텍스트 기본 통계를 분석합니다."""
        ...

    def classify_question_types(self, run: EvaluationRun) -> list[QuestionTypeStats]:
        """질문 유형을 분류합니다."""
        ...

    def extract_keywords(self, run: EvaluationRun, *, top_k: int = 20) -> list[KeywordInfo]:
        """키워드를 추출합니다."""
        ...
```

### Phase 2.3: NLP 분석 어댑터 구현

**YAGNI 원칙 적용**:
- 의존성 최소화: TF-IDF 기반 키워드 추출 (scikit-learn 기존 의존성 활용)
- 규칙 기반 질문 유형 분류 (LLM 호출 없음)
- 선택적 의존성: sentence-transformers (설치 시에만 의미적 분석 활성화)

```python
class NLPAnalysisAdapter:
    """NLP 분석 어댑터."""

    def classify_question_types(self, run: EvaluationRun) -> list[QuestionTypeStats]:
        """규칙 기반 질문 유형 분류.

        패턴:
        - factual: "무엇", "언제", "어디", "누가", what, when, where, who
        - reasoning: "왜", "어떻게", why, how
        - comparative: "비교", "차이", "vs", compare, difference
        - procedural: "방법", "절차", "단계", how to, steps
        - opinion: "생각", "의견", "평가", opinion, think
        """
```

### Phase 2.4: AnalysisService 통합

```python
class AnalysisService:
    def __init__(
        self,
        statistical_adapter: AnalysisPort | None = None,
        nlp_adapter: NLPAnalysisPort | None = None,
        cache: AnalysisCachePort | None = None,
    ):
        self._statistical = statistical_adapter or StatisticalAnalysisAdapter()
        self._nlp = nlp_adapter  # None이면 NLP 분석 비활성화

    def analyze_run(
        self,
        run: EvaluationRun,
        *,
        include_nlp: bool = False,  # 기본값 False (YAGNI)
        include_causal: bool = False,
    ) -> AnalysisBundle:
        """평가 실행을 분석합니다."""
```

### Phase 2.5: CLI 통합

```python
@app.command("analyze")
def analyze(
    run_id: str,
    include_nlp: bool = typer.Option(False, "--include-nlp", help="Include NLP analysis"),
    output_format: str = typer.Option("table", "--format", "-f"),
):
    """Analyze a stored evaluation run."""
```

## 1.4 선택적 확장 (Phase 2.x)

> YAGNI 원칙에 따라 초기 구현에서 제외. 필요시 별도 Phase로 구현.

| Phase | 기능 | 전제 조건 |
|-------|------|----------|
| 2.6 | 의미적 유사도 분석 | sentence-transformers 설치 |
| 2.7 | 토픽 클러스터링 | sentence-transformers, hdbscan 설치 |
| 2.8 | 보고서 생성 | - |

## 1.5 구현 순서 요약

```
Phase 2.1: NLP 엔티티 (1일)
├── tests/unit/test_nlp_entities.py
└── domain/entities/analysis.py 확장

Phase 2.2: NLP 포트 (0.5일)
└── ports/outbound/nlp_analysis_port.py

Phase 2.3: NLP 어댑터 (2일)
├── tests/unit/test_nlp_adapter.py
└── adapters/outbound/analysis/nlp_adapter.py

Phase 2.4: AnalysisService 통합 (1일)
├── tests/unit/test_analysis_service.py 확장
└── domain/services/analysis_service.py 수정

Phase 2.5: CLI 통합 (0.5일)
├── tests/integration/test_nlp_cli.py
└── adapters/inbound/cli.py 수정
```

---

# Part 2: Domain Memory Layering (완료)

## 2.1 개요

### 완료 상태

| Phase | Duration | Tests | Status |
|-------|----------|-------|--------|
| Phase 1: Factual Memory Store | 2 weeks | +40 | ✅ Complete |
| Phase 2: Dynamics (Evolution + Retrieval) | 2 weeks | +14 | ✅ Complete |
| Phase 3: Dynamics (Formation) | 1 week | +9 | ✅ Complete |
| Phase 4: Config & Multi-language | 1.5 weeks | +33 | ✅ Complete |
| Phase 5: Forms (Planar/Hierarchical) | 1 week | +17 | ✅ Complete |
| **Total** | **8 weeks** | **+113** | ✅ |

### 해결하는 문제

```
현재 EvalVault의 한계
═══════════════════════════════════════════════════════════════

평가 #1:  데이터셋 → 평가 → 결과 저장 → 끝
평가 #2:  데이터셋 → 평가 → 결과 저장 → 끝
    ...
평가 #100: 데이터셋 → 평가 → 결과 저장 → 끝

문제: 100번 평가해도 시스템이 동일하게 동작
     - 같은 실수를 100번 반복
     - 학습/개선 피드백 루프 없음
```

### Domain Memory로 해결

```
Domain Memory 적용 후
═══════════════════════════════════════════════════════════════

평가 #1:  데이터셋 → 평가 → 결과 저장 → 패턴 학습
평가 #2:  학습된 패턴 적용 → 평가 → 결과 저장 → 패턴 업데이트
    ...
평가 #100: 99번의 학습이 누적된 상태로 평가

결과: 사용할수록 정확도 향상
```

**중요**: 학습 피드백 루프는 Ragas 평가가 아닌 다른 컴포넌트에서 작동합니다:
1. **KG 생성 및 테스트셋 생성**: EntityExtractor가 학습된 패턴을 사용
2. **도메인 지식 축적**: 평가 결과에서 검증된 사실(FactualFact) 추출
3. **패턴 학습**: 엔티티 타입별 신뢰도, 실패 패턴 등을 학습

## 2.2 아키텍처

### 메모리 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Memory Layers                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Factual Layer (정적, 검증된 사실)                   │    │
│  │  ├── terms_dictionary.json (용어 사전)              │    │
│  │  ├── regulatory_rules.md (규정 문서)                │    │
│  │  └── verified_facts.db (평가에서 검증된 사실)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Experiential Layer (학습된 패턴)                    │    │
│  │  ├── entity_reliability.json (엔티티 타입별 신뢰도)  │    │
│  │  ├── relation_reliability.json (관계 타입별 신뢰도)  │    │
│  │  ├── failure_patterns.json (실패 패턴)              │    │
│  │  └── behavior_handbook.json (재사용 가능한 행동)     │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Working Layer (런타임 컨텍스트)                     │    │
│  │  ├── session_cache.db (현재 세션 캐시)              │    │
│  │  ├── active_entities (활성 엔티티 집합)             │    │
│  │  └── quality_metrics (실시간 품질 지표)             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 다국어 지원 설정

```yaml
# config/domains/insurance/memory.yaml
metadata:
  domain: insurance
  supported_languages: ["ko", "en"]
  default_language: ko

factual:
  glossary:
    ko: terms_dictionary_ko.json
    en: terms_dictionary_en.json

experiential:
  reliability_scores:
    ko: reliability_ko.json
    en: reliability_en.json
  failure_modes: failures.json
```

## 2.3 구현된 기능

### Phase 1: Factual Memory Store

| 컴포넌트 | 파일 | 테스트 |
|---------|------|--------|
| Domain Entities | `src/evalvault/domain/entities/memory.py` | 21 tests |
| DomainMemoryPort | `src/evalvault/ports/outbound/domain_memory_port.py` | - |
| SQLiteDomainMemoryAdapter | `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py` | 19 tests |

### Phase 2: Dynamics (Evolution + Retrieval)

**Evolution 메서드**:
- `consolidate_facts`: 유사한 사실들 통합
- `resolve_conflict`: 충돌하는 사실 해결
- `forget_obsolete`: 오래되거나 신뢰도 낮은 메모리 삭제
- `decay_verification_scores`: 시간에 따른 검증 점수 감소

**Retrieval 메서드**:
- `search_facts`: FTS5 기반 사실 검색
- `search_behaviors`: 컨텍스트 기반 행동 검색
- `hybrid_search`: 하이브리드 메모리 검색

### Phase 3: Dynamics (Formation)

**Formation 메서드**:
- `extract_facts_from_evaluation`: 평가 결과에서 사실 추출
- `extract_patterns_from_evaluation`: 평가 결과에서 학습 패턴 추출
- `extract_behaviors_from_evaluation`: 평가 결과에서 행동 추출

### Phase 4: Config & Multi-language

**CLI 명령어**:
```bash
evalvault domain init <domain> [--languages ko,en]
evalvault domain list
evalvault domain show <domain>
evalvault domain terms <domain> [--language ko]
```

### Phase 5: Forms (Planar/Hierarchical)

**Planar Form (KG Integration)**:
- `link_fact_to_kg`: 사실을 KG 엔티티에 연결
- `import_kg_as_facts`: KG를 사실로 변환
- `export_facts_as_kg`: 사실을 KG로 내보내기

**Hierarchical Form (Summary Layers)**:
- `create_summary_fact`: 요약 사실 생성
- `get_facts_by_level`: 추상화 레벨별 사실 조회
- `get_fact_hierarchy`: 사실 계층 구조 조회

## 2.4 성공 지표

| 지표 | Baseline 측정 방법 | Q1 목표 |
|------|-------------------|---------|
| Entity Extraction Accuracy | Insurance 테스트셋 기준 측정 | +10% 향상 |
| 반복 실수율 | 동일 엔티티 추출 실패 횟수 | -30% 감소 |
| 도메인 온보딩 시간 | 수동 설정 소요 시간 | CLI 자동화 (< 5분) |
| 언어별 신뢰도 편차 | 한국어/영어 정확도 차이 | < 5% |

---

# Part 3: Future Work

## 3.1 Agent System Integration (Q2+)

> 에이전트 아키텍처 도입 시 추가할 기능

### Coordination Profiler
- **전제**: 멀티에이전트 시스템 구축 후
- **목표**: 에이전트 간 조율 오버헤드 정량화

### Latent Evidence Bus
- **전제**: 에이전트 시스템 + 로컬 모델 (HuggingFace/vLLM)
- **API 제약**: OpenAI/Anthropic API는 hidden state 미노출
- **현실적 범위**: Anthropic Extended Thinking 캡처 (API 기반)

### Agent Architecture Roadmap

```
2026 Q2: Agent Architecture 설계
         - Planner / Metric / Insight Agent 정의
         - Agent 간 통신 프로토콜

2026 Q3: Coordination Profiler
         - 프로파일링 인프라
         - Policy Guard

2026 Q4: Latent Evidence Bus
         - HuggingFace/vLLM 직접 통합
         - KV cache 공유 연구
```

---

# Appendix A: File Structure

## NLP Analysis (Phase 2)

```
src/evalvault/
├── domain/
│   └── entities/
│       └── analysis.py              # NLP 엔티티 추가
├── ports/
│   └── outbound/
│       └── nlp_analysis_port.py     # NLP 포트
└── adapters/
    └── outbound/
        └── analysis/
            └── nlp_adapter.py       # NLP 어댑터
```

## Domain Memory Layering

```
src/evalvault/
├── domain/
│   ├── entities/
│   │   └── memory.py                    # 메모리 엔티티
│   └── services/
│       └── domain_learning_hook.py      # 학습 훅 서비스
├── ports/
│   ├── inbound/
│   │   └── learning_hook_port.py        # 학습 훅 포트
│   └── outbound/
│       └── domain_memory_port.py        # 메모리 포트
├── adapters/
│   └── outbound/
│       └── domain_memory/               # 메모리 어댑터
│           ├── sqlite_adapter.py
│           └── domain_memory_schema.sql
└── config/
    └── domain_config.py                 # 도메인 설정 로더

config/
└── domains/
    └── insurance/                       # 보험 도메인 설정
        ├── memory.yaml
        ├── terms_dictionary_ko.json
        └── terms_dictionary_en.json
```

---

# Appendix B: References

- **Agent Memory Survey**: Forms×Functions×Dynamics 프레임워크
- **Metacognitive Reuse**: Behavior Handbook 개념
- **Scaling Agent Systems**: 멀티에이전트 오버헤드 분석
- **LatentMAS**: Hidden state 공유 연구
