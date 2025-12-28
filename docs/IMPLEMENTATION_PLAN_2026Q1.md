# 2026 Q1 Implementation Plan: Domain Memory Layering

> **Document Version**: 2.0.0
> **Created**: 2025-12-28
> **Last Updated**: 2025-12-28
> **Status**: Final

---

## Executive Summary

### 범위 조정

| Initiative | Q1 Status | 이유 |
|------------|-----------|------|
| **Domain Memory Layering** | ✅ 구현 | 현재 파이프라인 아키텍처에 적용 가능 |
| Coordination Profiler | ⏸️ 연기 | 프로파일링할 에이전트 시스템 부재 |
| Latent Evidence Bus | ⏸️ 연기 | 에이전트 시스템 + 로컬 모델 필요 |

**Q1 집중 목표**: Domain Memory Layering 완성

### 리소스 요약

| Phase | Duration | Effort | Priority |
|-------|----------|--------|----------|
| Factual Memory Store | 2 weeks | 24h | Must Have |
| Config & Multi-language | 1.5 weeks | 16h | Must Have |
| Learning Integration | 1.5 weeks | 20h | Should Have |
| **Total** | **5 weeks** | **60h** | |

---

## 1. 목표 및 가치

### 1.1 해결하는 문제

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
     - 도메인 지식이 정적 파일에 고정
```

### 1.2 Domain Memory로 해결

```
Domain Memory 적용 후
═══════════════════════════════════════════════════════════════

평가 #1:  데이터셋 → 평가 → 결과 저장 → 패턴 학습
평가 #2:  학습된 패턴 적용 → 평가 → 결과 저장 → 패턴 업데이트
    ...
평가 #100: 99번의 학습이 누적된 상태로 평가

결과: 사용할수록 정확도 향상
     - 성공 패턴 강화, 실패 패턴 회피
     - 도메인 지식이 살아있는 데이터베이스
```

### 1.3 정량적 성공 지표

| 지표 | Baseline 측정 방법 | Q1 목표 |
|------|-------------------|---------|
| Entity Extraction Accuracy | Insurance 테스트셋 기준 측정 | +10% 향상 |
| 반복 실수율 | 동일 엔티티 추출 실패 횟수 | -30% 감소 |
| 도메인 온보딩 시간 | 수동 설정 소요 시간 | CLI 자동화 (< 5분) |
| 언어별 신뢰도 편차 | 한국어/영어 정확도 차이 | < 5% |

---

## 2. 아키텍처 설계

### 2.1 메모리 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Memory Layers                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
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
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 다국어 지원 설계

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
  regulatory_rules:
    ko: rules_ko.md
    en: rules_en.md

experiential:
  # 언어별 신뢰도 분리 추적
  reliability_scores:
    ko: reliability_ko.json
    en: reliability_en.json
  # 공통 실패 패턴
  failure_modes: failures.json

working:
  run_cache: ${RUN_DIR}/memory.db
  kg_binding: kg://insurance
```

### 2.3 DomainLearningHook 프로토콜

결합도 최소화를 위한 인터페이스 설계:

```python
# src/evalvault/ports/outbound/domain_learning_port.py

from typing import Protocol
from evalvault.domain.entities.result import EvaluationRun
from evalvault.domain.entities.memory import LearningMemory, BehaviorEntry

class DomainLearningHook(Protocol):
    """
    평가 결과에서 학습하는 훅 인터페이스.

    RagasEvaluator와 EntityExtractor 간 결합도를 낮추기 위해
    Protocol 기반으로 정의합니다.
    """

    def on_evaluation_complete(
        self,
        run: EvaluationRun,
        language: str = "ko"
    ) -> LearningMemory:
        """
        평가 완료 시 패턴 학습.

        Args:
            run: 완료된 평가 실행 결과
            language: 평가 데이터 언어

        Returns:
            학습된 패턴 (신뢰도, 실패 모드 등)
        """
        ...

    def extract_behaviors(
        self,
        run: EvaluationRun
    ) -> list[BehaviorEntry]:
        """
        Metacognitive Reuse를 위한 행동 추출.

        성공적인 평가에서 재사용 가능한 "행동"을 추출하여
        Behavior Handbook에 저장합니다.
        """
        ...

    def apply_learning(
        self,
        extractor: "EntityExtractor",
        language: str = "ko"
    ) -> None:
        """
        학습된 패턴을 추출기에 적용.

        Args:
            extractor: 엔티티 추출기 인스턴스
            language: 적용할 언어
        """
        ...
```

### 2.4 Behavior Handbook 통합

Metacognitive Reuse 논문의 개념을 Domain Memory에 통합:

```python
# src/evalvault/domain/entities/memory.py

@dataclass
class BehaviorEntry:
    """재사용 가능한 행동 정의"""
    behavior_id: str
    description: str
    trigger_pattern: str  # 이 행동을 트리거하는 조건
    action_sequence: list[str]  # 수행할 액션 시퀀스
    success_rate: float  # 역사적 성공률
    token_savings: int  # 이 행동으로 절감되는 토큰 수
    applicable_languages: list[str]
    last_used: datetime
    use_count: int

@dataclass
class BehaviorHandbook:
    """도메인별 행동 핸드북"""
    domain: str
    behaviors: list[BehaviorEntry]

    def find_applicable(
        self,
        context: str,
        language: str
    ) -> list[BehaviorEntry]:
        """현재 컨텍스트에 적용 가능한 행동 찾기"""
        ...
```

---

## 3. 구현 단계

### Phase 1: Factual Memory Store (Week 1-2)

#### 3.1.1 Domain Entities

```python
# src/evalvault/domain/entities/memory.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

@dataclass
class FactualFact:
    """검증된 도메인 사실"""
    fact_id: str
    subject: str           # 엔티티 이름
    predicate: str         # 관계 타입
    object: str            # 대상 엔티티
    language: str          # 언어 코드 (ko, en)
    fact_type: Literal["verified", "inferred", "contradictory"]
    verification_score: float  # 0.0-1.0
    verification_count: int    # 검증 횟수
    source_document_ids: list[str]
    created_at: datetime
    last_verified: datetime | None = None

@dataclass
class LearningMemory:
    """평가에서 학습된 패턴"""
    run_id: str
    language: str
    entity_type_reliability: dict[str, float]    # 타입별 신뢰도
    relation_type_reliability: dict[str, float]  # 관계별 신뢰도
    failed_patterns: list[str]                   # 실패한 추출 패턴
    successful_patterns: list[str]               # 성공한 추출 패턴
    faithfulness_by_entity_type: dict[str, float]
    timestamp: datetime

@dataclass
class DomainMemoryContext:
    """현재 실행의 워킹 메모리"""
    session_id: str
    domain: str
    language: str
    active_entities: set[str]
    entity_type_distribution: dict[str, int]
    current_quality_metrics: dict[str, float]
    started_at: datetime
```

#### 3.1.2 Port Interface

```python
# src/evalvault/ports/outbound/domain_memory_port.py

from abc import ABC, abstractmethod

class DomainMemoryPort(ABC):
    """도메인 메모리 저장 및 조회 포트"""

    @abstractmethod
    def store_fact(self, fact: FactualFact) -> str:
        """검증된 사실 저장"""
        pass

    @abstractmethod
    def query_facts(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        language: str = "ko",
        confidence_min: float = 0.0,
    ) -> list[FactualFact]:
        """사실 조회"""
        pass

    @abstractmethod
    def record_learning(
        self,
        learning: LearningMemory
    ) -> None:
        """학습 결과 기록"""
        pass

    @abstractmethod
    def get_reliability_scores(
        self,
        language: str = "ko"
    ) -> dict[str, dict[str, float]]:
        """언어별 신뢰도 점수 조회"""
        pass

    @abstractmethod
    def store_behavior(
        self,
        behavior: BehaviorEntry
    ) -> str:
        """재사용 가능한 행동 저장"""
        pass

    @abstractmethod
    def get_behavior_handbook(
        self,
        domain: str
    ) -> BehaviorHandbook:
        """도메인 행동 핸드북 조회"""
        pass
```

#### 3.1.3 SQLite Schema

```sql
-- src/evalvault/adapters/outbound/domain_memory/schema.sql

-- 검증된 사실
CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'ko',
    fact_type TEXT CHECK(fact_type IN ('verified', 'inferred', 'contradictory')),
    verification_score REAL DEFAULT 0.0,
    verification_count INTEGER DEFAULT 0,
    source_document_ids TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP
);

CREATE INDEX idx_facts_subject ON facts(subject);
CREATE INDEX idx_facts_language ON facts(language);
CREATE INDEX idx_facts_score ON facts(verification_score);

-- 학습된 패턴
CREATE TABLE IF NOT EXISTS learning_runs (
    run_id TEXT PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'ko',
    entity_type_reliability TEXT NOT NULL,  -- JSON object
    relation_type_reliability TEXT NOT NULL,  -- JSON object
    failed_patterns TEXT,  -- JSON array
    successful_patterns TEXT,  -- JSON array
    faithfulness_by_entity_type TEXT,  -- JSON object
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_language ON learning_runs(language);

-- 행동 핸드북
CREATE TABLE IF NOT EXISTS behaviors (
    behavior_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    description TEXT NOT NULL,
    trigger_pattern TEXT NOT NULL,
    action_sequence TEXT NOT NULL,  -- JSON array
    success_rate REAL DEFAULT 0.0,
    token_savings INTEGER DEFAULT 0,
    applicable_languages TEXT NOT NULL,  -- JSON array
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_behaviors_domain ON behaviors(domain);

-- 스키마 버전 관리
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial domain memory schema');
```

#### 3.1.4 Migration Strategy

```python
# src/evalvault/adapters/outbound/domain_memory/migrations.py

"""
스키마 마이그레이션 전략

Alembic 대신 간단한 버전 기반 마이그레이션 사용:
1. schema_version 테이블로 현재 버전 추적
2. 버전별 마이그레이션 SQL 순차 적용
3. 하위 호환성 보장 (기존 데이터 보존)
"""

MIGRATIONS = {
    1: """
        -- Initial schema (위의 schema.sql)
    """,
    2: """
        -- Future: 추가 필드
        ALTER TABLE facts ADD COLUMN confidence_trend TEXT;
    """,
}

def migrate(conn, target_version: int = None):
    """마이그레이션 실행"""
    current = get_current_version(conn)
    target = target_version or max(MIGRATIONS.keys())

    for version in range(current + 1, target + 1):
        if version in MIGRATIONS:
            conn.executescript(MIGRATIONS[version])
            update_version(conn, version)
```

#### 3.1.5 Tasks & Deliverables

| Task | Effort | Deliverable |
|------|--------|-------------|
| Domain entities 구현 | 4h | `memory.py` with dataclasses |
| DomainMemoryPort 정의 | 2h | Port interface |
| SQLite adapter 구현 | 8h | `sqlite_adapter.py` |
| Migration strategy | 4h | Version-based migrations |
| Unit tests | 6h | 20+ tests |
| **Total Phase 1** | **24h** | |

---

### Phase 2: Config & Multi-language (Week 2-3)

#### 3.2.1 Config Schema

```yaml
# config/domains/insurance/memory.yaml

# 메타데이터
metadata:
  domain: insurance
  version: "1.0.0"
  supported_languages: ["ko", "en"]
  default_language: ko
  description: "보험 도메인 메모리 설정"

# Factual Layer
factual:
  glossary:
    ko: terms_dictionary_ko.json
    en: terms_dictionary_en.json
  regulatory_rules:
    ko: rules_ko.md
    en: rules_en.md
  # 언어 간 공유되는 사실
  shared:
    company_info: companies.json

# Experiential Layer
experiential:
  # 언어별 분리
  reliability_scores:
    ko: reliability_ko.json
    en: reliability_en.json
  # 공통
  failure_modes: failures.json
  behavior_handbook: behaviors.json

# Working Layer
working:
  run_cache: ${RUN_DIR}/memory.db
  kg_binding: kg://insurance
  max_cache_size_mb: 100

# 학습 설정
learning:
  enabled: true
  min_confidence_to_store: 0.6
  behavior_extraction: true
  auto_apply: true
```

#### 3.2.2 Config Loader

```python
# src/evalvault/config/domain_config.py

from pydantic import BaseModel, Field
from pathlib import Path
import yaml

class LanguageConfig(BaseModel):
    """언어별 설정"""
    ko: str | None = None
    en: str | None = None

class FactualConfig(BaseModel):
    glossary: LanguageConfig
    regulatory_rules: LanguageConfig | None = None
    shared: dict[str, str] = Field(default_factory=dict)

class ExperientialConfig(BaseModel):
    reliability_scores: LanguageConfig
    failure_modes: str = "failures.json"
    behavior_handbook: str = "behaviors.json"

class WorkingConfig(BaseModel):
    run_cache: str = "${RUN_DIR}/memory.db"
    kg_binding: str | None = None
    max_cache_size_mb: int = 100

class LearningConfig(BaseModel):
    enabled: bool = True
    min_confidence_to_store: float = 0.6
    behavior_extraction: bool = True
    auto_apply: bool = True

class DomainMemoryConfig(BaseModel):
    """도메인 메모리 설정"""
    metadata: dict[str, str | list[str]]
    factual: FactualConfig
    experiential: ExperientialConfig
    working: WorkingConfig
    learning: LearningConfig = Field(default_factory=LearningConfig)

def load_domain_config(domain: str) -> DomainMemoryConfig:
    """도메인 설정 로드"""
    config_path = Path(f"config/domains/{domain}/memory.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Domain config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return DomainMemoryConfig(**data)
```

#### 3.2.3 CLI Extension

```python
# src/evalvault/adapters/inbound/cli.py (추가)

@app.command()
def domain_init(
    domain: str = typer.Argument(..., help="도메인 이름"),
    languages: str = typer.Option("ko,en", help="지원 언어 (쉼표 구분)"),
):
    """도메인 메모리 설정 초기화"""
    lang_list = [l.strip() for l in languages.split(",")]

    # 디렉토리 생성
    domain_dir = Path(f"config/domains/{domain}")
    domain_dir.mkdir(parents=True, exist_ok=True)

    # 템플릿 생성
    config = generate_domain_template(domain, lang_list)

    with open(domain_dir / "memory.yaml", "w") as f:
        yaml.dump(config, f, allow_unicode=True)

    console.print(f"[green]✓[/green] Domain '{domain}' initialized")
    console.print(f"  Config: {domain_dir / 'memory.yaml'}")

@app.command()
def domain_list():
    """등록된 도메인 목록"""
    domains_dir = Path("config/domains")
    if not domains_dir.exists():
        console.print("[yellow]No domains configured[/yellow]")
        return

    domains = [d.name for d in domains_dir.iterdir() if d.is_dir()]

    table = Table(title="Registered Domains")
    table.add_column("Domain")
    table.add_column("Languages")
    table.add_column("Learning")

    for domain in domains:
        config = load_domain_config(domain)
        langs = ", ".join(config.metadata.get("supported_languages", []))
        learning = "✓" if config.learning.enabled else "✗"
        table.add_row(domain, langs, learning)

    console.print(table)
```

#### 3.2.4 Tasks & Deliverables

| Task | Effort | Deliverable |
|------|--------|-------------|
| Config schema 설계 | 2h | YAML schema |
| DomainMemoryConfig 구현 | 4h | Pydantic models |
| CLI domain init/list | 4h | CLI commands |
| 다국어 terms_dictionary 분리 | 4h | ko/en 분리 파일 |
| Integration tests | 2h | Config loading tests |
| **Total Phase 2** | **16h** | |

---

### Phase 3: Learning Integration (Week 3-4)

#### 3.3.1 Learning Hook Implementation

```python
# src/evalvault/domain/services/domain_learning.py

from evalvault.ports.outbound.domain_learning_port import DomainLearningHook
from evalvault.domain.entities.result import EvaluationRun, TestCaseResult
from evalvault.domain.entities.memory import LearningMemory, BehaviorEntry

class InsuranceDomainLearning(DomainLearningHook):
    """보험 도메인 학습 구현"""

    def __init__(self, memory_port: DomainMemoryPort):
        self._memory = memory_port

    def on_evaluation_complete(
        self,
        run: EvaluationRun,
        language: str = "ko"
    ) -> LearningMemory:
        """평가 완료 시 패턴 학습"""

        # 1. 엔티티 타입별 신뢰도 계산
        entity_reliability = self._calculate_entity_reliability(run)

        # 2. 관계 타입별 신뢰도 계산
        relation_reliability = self._calculate_relation_reliability(run)

        # 3. 실패/성공 패턴 추출
        failed_patterns = self._extract_failed_patterns(run)
        successful_patterns = self._extract_successful_patterns(run)

        # 4. 메트릭별 엔티티 타입 연관성
        faithfulness_by_type = self._analyze_faithfulness_by_entity(run)

        learning = LearningMemory(
            run_id=run.run_id,
            language=language,
            entity_type_reliability=entity_reliability,
            relation_type_reliability=relation_reliability,
            failed_patterns=failed_patterns,
            successful_patterns=successful_patterns,
            faithfulness_by_entity_type=faithfulness_by_type,
            timestamp=datetime.now(),
        )

        self._memory.record_learning(learning)
        return learning

    def extract_behaviors(
        self,
        run: EvaluationRun
    ) -> list[BehaviorEntry]:
        """성공적인 평가에서 재사용 가능한 행동 추출"""

        behaviors = []

        # 높은 점수의 테스트 케이스에서 패턴 추출
        high_score_cases = [
            tc for tc in run.results
            if tc.passed and tc.get_metric("faithfulness").score > 0.9
        ]

        for tc in high_score_cases:
            behavior = self._extract_behavior_from_case(tc)
            if behavior:
                behaviors.append(behavior)
                self._memory.store_behavior(behavior)

        return behaviors

    def apply_learning(
        self,
        extractor: "EntityExtractor",
        language: str = "ko"
    ) -> None:
        """학습된 패턴을 추출기에 적용"""

        # 신뢰도 점수 조회
        reliability = self._memory.get_reliability_scores(language)

        # 추출기에 신뢰도 가중치 적용
        for entity_type, score in reliability.get("entity_types", {}).items():
            extractor.set_type_weight(entity_type, score)

        # 실패 패턴 회피
        recent_learning = self._memory.get_recent_learning(language, limit=10)
        for learning in recent_learning:
            for pattern in learning.failed_patterns:
                extractor.add_negative_pattern(pattern)
```

#### 3.3.2 Evaluator Integration

```python
# src/evalvault/domain/services/evaluator.py (수정)

class RagasEvaluator:
    def __init__(
        self,
        learning_hook: DomainLearningHook | None = None,  # 새로 추가
    ):
        self._learning_hook = learning_hook

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        language: str = "ko",  # 새로 추가
        **kwargs,
    ) -> EvaluationRun:
        """평가 실행"""

        # 기존 평가 로직
        run = await self._run_evaluation(dataset, metrics, llm, **kwargs)

        # 학습 훅 호출 (설정된 경우)
        if self._learning_hook:
            learning = self._learning_hook.on_evaluation_complete(run, language)

            # 행동 추출 (활성화된 경우)
            if self._config.learning.behavior_extraction:
                behaviors = self._learning_hook.extract_behaviors(run)
                run.extracted_behaviors = len(behaviors)

        return run
```

#### 3.3.3 Entity Extractor Integration

```python
# src/evalvault/domain/services/entity_extractor.py (수정)

class EntityExtractor:
    def __init__(
        self,
        domain_memory: DomainMemoryPort | None = None,
        language: str = "ko",
    ):
        self._memory = domain_memory
        self._language = language
        self._type_weights: dict[str, float] = {}
        self._negative_patterns: list[str] = []

    def set_type_weight(self, entity_type: str, weight: float) -> None:
        """엔티티 타입별 가중치 설정 (학습에서 호출)"""
        self._type_weights[entity_type] = weight

    def add_negative_pattern(self, pattern: str) -> None:
        """회피할 패턴 추가 (실패 패턴에서 학습)"""
        self._negative_patterns.append(pattern)

    def extract_entities(self, text: str) -> list[Entity]:
        """엔티티 추출 (학습된 가중치 적용)"""

        entities = []

        for entity_type, patterns in self._patterns.items():
            # 기본 추출
            for pattern in patterns:
                matches = pattern.findall(text)

                for match in matches:
                    # 학습된 가중치 적용
                    base_confidence = 0.85
                    weight = self._type_weights.get(entity_type, 1.0)
                    confidence = base_confidence * weight

                    # 네거티브 패턴 체크
                    if any(neg in match for neg in self._negative_patterns):
                        confidence *= 0.5  # 신뢰도 하락

                    entities.append(Entity(
                        text=match,
                        entity_type=entity_type,
                        confidence=confidence,
                    ))

        return entities
```

#### 3.3.4 Tasks & Deliverables

| Task | Effort | Deliverable |
|------|--------|-------------|
| DomainLearningHook 구현 | 6h | `domain_learning.py` |
| Behavior 추출 로직 | 4h | Behavior extraction |
| RagasEvaluator 통합 | 4h | Learning hook integration |
| EntityExtractor 통합 | 4h | Weight/pattern application |
| Integration tests | 2h | End-to-end learning tests |
| **Total Phase 3** | **20h** | |

---

## 4. 리스크 관리

### 4.1 기술적 리스크

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 다국어 처리 복잡도 (한국어 조사, 띄어쓰기) | Medium | 언어별 전처리 파이프라인 분리 |
| 메모리 증가로 인한 성능 저하 | Low | max_cache_size_mb 제한, LRU 캐시 |
| Behavior 추출 품질 불안정 | Medium | 최소 성공률 임계값 설정 (0.9) |
| 스키마 마이그레이션 오류 | Medium | 버전 기반 점진적 마이그레이션, 롤백 지원 |

### 4.2 사용자 경험 리스크

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 기존 워크플로우 변경 | Low | 학습 기능 opt-in (기본 비활성화) |
| 새 기능 학습 곡선 | Low | CLI 도움말 + 예제 제공 |
| 하위 호환성 | Medium | 기존 config 파일 자동 마이그레이션 |

---

## 5. 테스트 전략

### 5.1 Unit Tests

```python
# tests/unit/test_domain_memory.py

class TestFactualMemory:
    def test_store_and_query_fact(self): ...
    def test_language_filtering(self): ...
    def test_confidence_threshold(self): ...

class TestLearningMemory:
    def test_record_learning(self): ...
    def test_reliability_aggregation(self): ...
    def test_language_separation(self): ...

class TestBehaviorHandbook:
    def test_store_behavior(self): ...
    def test_find_applicable_behaviors(self): ...
    def test_token_savings_calculation(self): ...

class TestDomainLearningHook:
    def test_on_evaluation_complete(self): ...
    def test_extract_behaviors(self): ...
    def test_apply_learning(self): ...
```

### 5.2 Integration Tests

```python
# tests/integration/test_domain_memory_flow.py

class TestLearningFlow:
    def test_evaluation_to_learning_to_extraction(self):
        """평가 → 학습 → 추출 개선 전체 흐름"""

        # 1. 초기 평가 실행
        run1 = await evaluator.evaluate(dataset, metrics, llm)
        initial_accuracy = measure_entity_accuracy(run1)

        # 2. 학습 적용
        learning_hook.on_evaluation_complete(run1, "ko")
        learning_hook.apply_learning(entity_extractor, "ko")

        # 3. 재평가
        run2 = await evaluator.evaluate(dataset, metrics, llm)
        improved_accuracy = measure_entity_accuracy(run2)

        # 4. 개선 확인
        assert improved_accuracy > initial_accuracy
```

---

## 6. Timeline Summary

```
2026 Q1 Implementation Schedule
═══════════════════════════════════════════════════════════════

Week 1-2  ┃ Phase 1: Factual Memory Store
          ┃ ├── Domain entities (memory.py)
          ┃ ├── DomainMemoryPort interface
          ┃ ├── SQLite adapter + schema
          ┃ └── Migration strategy
          ┃
Week 2-3  ┃ Phase 2: Config & Multi-language
          ┃ ├── Config schema (YAML)
          ┃ ├── DomainMemoryConfig (Pydantic)
          ┃ ├── CLI domain init/list
          ┃ └── Multi-language terms dictionary
          ┃
Week 3-4  ┃ Phase 3: Learning Integration
          ┃ ├── DomainLearningHook implementation
          ┃ ├── Behavior extraction
          ┃ ├── RagasEvaluator integration
          ┃ └── EntityExtractor integration
          ┃
Week 5    ┃ Testing & Documentation
          ┃ ├── Unit tests (30+)
          ┃ ├── Integration tests (5+)
          ┃ └── User documentation update

Total: 5 weeks, 60h effort
```

---

## 7. Future Work (Agent System Integration)

> Q2 이후 에이전트 아키텍처 도입 시 추가할 기능

### 7.1 Coordination Profiler

- **전제**: 멀티에이전트 시스템 구축 후
- **목표**: 에이전트 간 조율 오버헤드 정량화
- **baseline_score 정의**: 동일 데이터셋에 대해 단일 에이전트 재실행 결과

### 7.2 Latent Evidence Bus

- **전제**: 에이전트 시스템 + 로컬 모델 (HuggingFace/vLLM)
- **API 제약**: OpenAI/Anthropic API는 hidden state 미노출
- **현실적 범위**: Anthropic Extended Thinking 캡처 (API 기반)

### 7.3 Agent Architecture Roadmap

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

## Appendix A: File Structure

```
src/evalvault/
├── domain/
│   ├── entities/
│   │   └── memory.py                    # NEW: 메모리 엔티티
│   └── services/
│       └── domain_learning.py           # NEW: 학습 훅 구현
├── ports/
│   └── outbound/
│       ├── domain_memory_port.py        # NEW: 메모리 포트
│       └── domain_learning_port.py      # NEW: 학습 훅 포트
├── adapters/
│   └── outbound/
│       └── domain_memory/               # NEW: 메모리 어댑터
│           ├── __init__.py
│           ├── sqlite_adapter.py
│           ├── schema.sql
│           └── migrations.py
└── config/
    └── domain_config.py                 # NEW: 도메인 설정 로더

config/
└── domains/
    └── insurance/                       # NEW: 보험 도메인 설정
        ├── memory.yaml
        ├── terms_dictionary_ko.json
        └── terms_dictionary_en.json
```

---

## Appendix B: References

- **Agent Memory Survey**: Forms×Functions 가이드라인
- **Metacognitive Reuse**: Behavior Handbook 개념
- **Scaling Agent Systems**: 멀티에이전트 오버헤드 분석
- **LatentMAS**: Hidden state 공유 연구
