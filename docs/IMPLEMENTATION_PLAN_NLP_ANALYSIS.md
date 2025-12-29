# NLP Analysis Implementation Plan (Phase 2)

> **버전**: 1.0.0
> **작성일**: 2025-12-29
> **참조**: `scratch/ragrefine/analysis/` 소스 코드

---

## 1. 개요

### 1.1 목표

EvalVault에 NLP 분석, 데이터 저장, 보고서 생성 기능을 추가합니다. ragrefine 프로젝트의 기능을 참조하되, EvalVault의 Hexagonal Architecture와 개발 정책(TDD, YAGNI)에 맞게 재설계합니다.

### 1.2 핵심 원칙

| 원칙 | 적용 방법 |
|------|-----------|
| **Hexagonal Architecture** | Port 인터페이스 정의 → Adapter 구현 |
| **TDD** | 테스트 먼저 작성 → 최소 구현 → 리팩토링 |
| **YAGNI** | 필요한 기능만 구현, 과도한 추상화 금지 |
| **SOLID** | 단일 책임, 인터페이스 분리 |

### 1.3 의존성 관리

```
새 의존성 (필수):
- 없음 (기존 numpy, scipy 활용)

선택적 의존성 (Extras):
- sentence-transformers: 의미적 유사도 분석
- keybert: 키워드 추출 (sentence-transformers 의존)
```

---

## 2. 아키텍처

### 2.1 전체 구조

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

### 2.2 의존성 방향

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

---

## 3. 구현 단계

### Phase 2.1: NLP 분석 엔티티 정의

**목표**: NLP 분석 결과를 표현하는 도메인 엔티티 추가

**TDD 순서**:
1. `tests/unit/test_nlp_entities.py` 작성
2. `domain/entities/analysis.py`에 엔티티 추가
3. 테스트 통과 확인

**엔티티 설계** (YAGNI - 최소 필요 속성만):

```python
# domain/entities/analysis.py에 추가

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
    avg_metric_scores: dict[str, float] | None = None  # 해당 키워드 포함 케이스의 평균 점수

@dataclass
class TopicCluster:
    """토픽 클러스터."""
    cluster_id: int
    keywords: list[str]
    document_count: int
    avg_scores: dict[str, float]
    representative_questions: list[str]

@dataclass
class NLPAnalysis:
    """NLP 분석 결과."""
    run_id: str

    # 텍스트 통계
    question_stats: TextStats | None = None
    answer_stats: TextStats | None = None
    context_stats: TextStats | None = None

    # 질문 유형 분석
    question_types: list[QuestionTypeStats] = field(default_factory=list)

    # 키워드 분석
    top_keywords: list[KeywordInfo] = field(default_factory=list)

    # 토픽 클러스터링 (선택적)
    topic_clusters: list[TopicCluster] = field(default_factory=list)

    # 인사이트
    insights: list[str] = field(default_factory=list)
```

**테스트 케이스**:
```python
# tests/unit/test_nlp_entities.py

def test_text_stats_creation():
    """TextStats 생성 테스트."""

def test_question_type_stats_creation():
    """QuestionTypeStats 생성 테스트."""

def test_keyword_info_creation():
    """KeywordInfo 생성 테스트."""

def test_nlp_analysis_creation():
    """NLPAnalysis 생성 테스트."""

def test_nlp_analysis_default_values():
    """NLPAnalysis 기본값 테스트."""
```

---

### Phase 2.2: NLP 분석 포트 인터페이스

**목표**: NLP 분석을 위한 포트 인터페이스 정의

**TDD 순서**:
1. 포트 인터페이스 정의
2. 테스트에서 Protocol 준수 확인

**포트 설계**:

```python
# ports/outbound/nlp_analysis_port.py

from typing import Protocol
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import NLPAnalysis, KeywordInfo

class NLPAnalysisPort(Protocol):
    """NLP 분석 포트 인터페이스."""

    def analyze_text_statistics(
        self,
        run: EvaluationRun,
    ) -> NLPAnalysis:
        """텍스트 기본 통계를 분석합니다."""
        ...

    def classify_question_types(
        self,
        run: EvaluationRun,
    ) -> list[QuestionTypeStats]:
        """질문 유형을 분류합니다."""
        ...

    def extract_keywords(
        self,
        run: EvaluationRun,
        *,
        top_k: int = 20,
    ) -> list[KeywordInfo]:
        """키워드를 추출합니다."""
        ...
```

---

### Phase 2.3: NLP 분석 어댑터 구현

**목표**: NLP 분석 포트를 구현하는 어댑터

**TDD 순서**:
1. `tests/unit/test_nlp_adapter.py` 작성
2. `adapters/outbound/analysis/nlp_adapter.py` 구현
3. 테스트 통과 확인

**YAGNI 원칙 적용**:
- 의존성 최소화: TF-IDF 기반 키워드 추출 (scikit-learn 기존 의존성 활용)
- 규칙 기반 질문 유형 분류 (LLM 호출 없음)
- 선택적 의존성: sentence-transformers (설치 시에만 의미적 분석 활성화)

**어댑터 설계**:

```python
# adapters/outbound/analysis/nlp_adapter.py

import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

class NLPAnalysisAdapter:
    """NLP 분석 어댑터.

    NLPAnalysisPort 인터페이스를 구현합니다.
    외부 의존성을 최소화하고, 선택적 의존성은 런타임에 체크합니다.
    """

    def __init__(self):
        self._sentence_transformer = None  # lazy loading
        self._has_sentence_transformers = self._check_sentence_transformers()

    def _check_sentence_transformers(self) -> bool:
        """sentence-transformers 설치 여부 확인."""
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False

    def analyze_text_statistics(self, run: EvaluationRun) -> NLPAnalysis:
        """텍스트 기본 통계 분석."""
        # 구현...

    def classify_question_types(self, run: EvaluationRun) -> list[QuestionTypeStats]:
        """규칙 기반 질문 유형 분류.

        패턴:
        - factual: "무엇", "언제", "어디", "누가", what, when, where, who
        - reasoning: "왜", "어떻게", why, how
        - comparative: "비교", "차이", "vs", compare, difference
        - procedural: "방법", "절차", "단계", how to, steps
        - opinion: "생각", "의견", "평가", opinion, think
        """
        # 구현...

    def extract_keywords(
        self,
        run: EvaluationRun,
        *,
        top_k: int = 20,
    ) -> list[KeywordInfo]:
        """TF-IDF 기반 키워드 추출."""
        # 구현...
```

**테스트 케이스**:
```python
# tests/unit/test_nlp_adapter.py

class TestNLPAnalysisAdapter:
    """NLP 분석 어댑터 테스트."""

    def test_analyze_text_statistics_basic(self, sample_run):
        """기본 텍스트 통계 분석 테스트."""

    def test_analyze_text_statistics_empty_run(self):
        """빈 실행 결과 처리 테스트."""

    def test_classify_question_types_factual(self, sample_run_factual):
        """사실형 질문 분류 테스트."""

    def test_classify_question_types_reasoning(self, sample_run_reasoning):
        """추론형 질문 분류 테스트."""

    def test_classify_question_types_korean(self, sample_run_korean):
        """한국어 질문 분류 테스트."""

    def test_extract_keywords_basic(self, sample_run):
        """기본 키워드 추출 테스트."""

    def test_extract_keywords_with_metric_correlation(self, sample_run):
        """메트릭 상관관계 포함 키워드 추출 테스트."""

    def test_extract_keywords_top_k(self, sample_run):
        """top_k 파라미터 테스트."""
```

---

### Phase 2.4: AnalysisService 통합

**목표**: NLP 분석을 AnalysisService에 통합

**TDD 순서**:
1. `tests/unit/test_analysis_service.py`에 NLP 관련 테스트 추가
2. `AnalysisService.analyze_run()` 수정
3. 테스트 통과 확인

**수정 사항**:

```python
# domain/services/analysis_service.py

class AnalysisService:
    def __init__(
        self,
        statistical_adapter: AnalysisPort | None = None,
        nlp_adapter: NLPAnalysisPort | None = None,  # 추가
        cache: AnalysisCachePort | None = None,
    ):
        self._statistical = statistical_adapter or StatisticalAnalysisAdapter()
        self._nlp = nlp_adapter  # None이면 NLP 분석 비활성화
        self._cache = cache

    def analyze_run(
        self,
        run: EvaluationRun,
        *,
        include_nlp: bool = False,  # 기본값 False (YAGNI)
        include_causal: bool = False,
    ) -> AnalysisBundle:
        """평가 실행을 분석합니다."""

        # 통계 분석 (기존)
        statistical = self._statistical.analyze_statistics(run)

        # NLP 분석 (Phase 2)
        nlp = None
        if include_nlp and self._nlp is not None:
            nlp = self._nlp.analyze_text_statistics(run)
            nlp.question_types = self._nlp.classify_question_types(run)
            nlp.top_keywords = self._nlp.extract_keywords(run)

        return AnalysisBundle(
            statistical=statistical,
            nlp=nlp,
            causal=None,  # Phase 3
        )
```

**테스트 케이스**:
```python
# tests/unit/test_analysis_service.py에 추가

def test_analyze_run_with_nlp(self, sample_run):
    """NLP 분석 포함 테스트."""

def test_analyze_run_without_nlp_adapter(self, sample_run):
    """NLP 어댑터 없이 include_nlp=True 시 graceful 처리."""

def test_analyze_run_nlp_disabled_by_default(self, sample_run):
    """기본적으로 NLP 분석 비활성화 확인."""
```

---

### Phase 2.5: CLI 통합

**목표**: CLI에서 NLP 분석 옵션 사용

**TDD 순서**:
1. CLI 통합 테스트 작성
2. CLI 명령에 `--include-nlp` 옵션 추가
3. 테스트 통과 확인

**CLI 수정**:

```python
# adapters/inbound/cli.py

@app.command("analyze")
def analyze(
    run_id: str,
    include_nlp: bool = typer.Option(False, "--include-nlp", help="Include NLP analysis"),
    output_format: str = typer.Option("table", "--format", "-f"),
):
    """Analyze a stored evaluation run."""
    # 구현...
```

---

## 4. 선택적 확장 (Phase 2.x)

> 아래 기능은 YAGNI 원칙에 따라 초기 구현에서 제외합니다.
> 필요시 별도 Phase로 구현합니다.

### Phase 2.6: 의미적 유사도 분석 (Optional)

**전제 조건**: `sentence-transformers` 설치

```python
# NLPAnalysisAdapter에 추가

def analyze_semantic_similarity(
    self,
    run: EvaluationRun,
) -> SemanticAnalysis:
    """Q-C-A 의미적 유사도 분석.

    sentence-transformers 미설치 시 None 반환.
    """
    if not self._has_sentence_transformers:
        return None
    # 구현...
```

### Phase 2.7: 토픽 클러스터링 (Optional)

**전제 조건**: `sentence-transformers`, `hdbscan` 설치

```python
def cluster_topics(
    self,
    run: EvaluationRun,
    *,
    min_cluster_size: int = 3,
) -> list[TopicCluster]:
    """토픽 클러스터링.

    필요 의존성 미설치 시 빈 리스트 반환.
    """
```

### Phase 2.8: 보고서 생성 (Optional)

```python
# ports/outbound/report_port.py

class ReportPort(Protocol):
    """보고서 생성 포트."""

    def generate_markdown(
        self,
        bundle: AnalysisBundle,
    ) -> str:
        """Markdown 형식 보고서 생성."""
        ...

    def generate_html(
        self,
        bundle: AnalysisBundle,
    ) -> str:
        """HTML 형식 보고서 생성."""
        ...
```

---

## 5. 테스트 전략

### 5.1 테스트 계층

| 계층 | 위치 | 목적 |
|------|------|------|
| Unit | `tests/unit/test_nlp_*.py` | 개별 컴포넌트 테스트 |
| Integration | `tests/integration/test_nlp_analysis.py` | 전체 흐름 테스트 |

### 5.2 테스트 데이터

```python
# tests/conftest.py에 추가

@pytest.fixture
def sample_run_for_nlp() -> EvaluationRun:
    """NLP 분석 테스트용 샘플 데이터."""
    return EvaluationRun(
        run_id="test-nlp-001",
        dataset_name="test-dataset",
        model_name="test-model",
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                question="이 보험의 보장금액은 얼마인가요?",  # factual
                answer="보장금액은 1억원입니다.",
                contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7, passed=True),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                question="왜 보험료가 인상되었나요?",  # reasoning
                answer="물가 상승으로 인해 보험료가 조정되었습니다.",
                contexts=["2024년 물가 상승률 반영으로 보험료가 3% 인상됨."],
                metrics=[
                    MetricScore(name="faithfulness", score=0.7, threshold=0.7, passed=True),
                ],
            ),
        ],
        metrics_evaluated=["faithfulness"],
        thresholds={"faithfulness": 0.7},
    )
```

### 5.3 테스트 마커

```python
# 선택적 의존성 테스트용 마커
@pytest.mark.requires_sentence_transformers
def test_semantic_analysis():
    """sentence-transformers 필요 테스트."""
```

---

## 6. 구현 순서 요약

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

## 7. 검증 기준

### 7.1 기능 검증

- [ ] `NLPAnalysis` 엔티티 생성 가능
- [ ] 텍스트 통계 분석 동작
- [ ] 질문 유형 분류 동작 (한국어/영어)
- [ ] TF-IDF 키워드 추출 동작
- [ ] AnalysisService에서 NLP 분석 통합
- [ ] CLI `--include-nlp` 옵션 동작

### 7.2 품질 검증

- [ ] 모든 유닛 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 코드 커버리지 80% 이상
- [ ] ruff 린트 통과
- [ ] 타입 힌트 완비

### 7.3 YAGNI 검증

- [ ] 불필요한 추상화 없음
- [ ] 선택적 의존성만 extras로 분리
- [ ] 사용하지 않는 기능 구현 안 함

---

## 8. 참고 자료

### 8.1 ragrefine 참조 파일

| 파일 | 참조 내용 |
|------|-----------|
| `analysis/types.py` | 데이터 타입 정의 |
| `analysis/question_analysis.py` | 질문 통계 분석 |
| `analysis/question_type_classifier.py` | 질문 유형 분류 |
| `analysis/keybert_analyzer.py` | 키워드 추출 |
| `analysis/context_semantic_analyzer.py` | 의미적 유사도 |
| `analysis/topic_clustering.py` | 토픽 클러스터링 |

### 8.2 EvalVault 기존 패턴

- Port/Adapter 패턴: `ports/outbound/analysis_port.py`, `adapters/outbound/analysis/statistical_adapter.py`
- 엔티티 정의: `domain/entities/analysis.py`
- 서비스 구현: `domain/services/analysis_service.py`
- 테스트 구조: `tests/unit/test_analysis_*.py`
