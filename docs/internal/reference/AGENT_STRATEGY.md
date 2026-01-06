# EvalVault 에이전트 시스템 종합 활용 전략

> Last Updated: 2026-01-06
> Version: 2.0
> Status: 검증 완료 / 구현 가능

---

## 1. 개요

### 1.1 문서 목적

이 문서는 EvalVault의 **모든 기능**을 분석하고, 에이전트 시스템을 통해 어떻게 자동화/최적화할 수 있는지 종합적으로 정리합니다.

### 1.2 에이전트 시스템 상태

```
✅ 에이전트 시스템 검증 완료 (2026-01-01)
   - Claude Agent SDK 정상 작동
   - 8개 에이전트 타입 구성됨
   - 메모리 시스템 정상 작동
   - 병렬 실행 그룹 정의됨
```

### 1.3 두 가지 활용 모드

| 모드 | 목적 | 대상 | 현재 상태 |
|------|------|------|-----------|
| **개발 자동화** | EvalVault 코드 개선 | 개발자 | ✅ 구현됨 |
| **운영 자동화** | RAG 평가 워크플로우 자동화 | 평가 담당자 | 📋 제안 단계 |

---

## 2. EvalVault 전체 기능 인벤토리

### 2.1 CLI 명령어 (22개)

| 카테고리 | 명령어 | 설명 | 에이전트 적용 가능성 |
|----------|--------|------|---------------------|
| **평가** | `run` | 데이터셋 평가 실행 | ⭐⭐⭐ 자동화 핵심 |
| | `benchmark` | 반복 벤치마크 실행 | ⭐⭐⭐ 정기 실행 |
| | `gate` | 품질 게이트 검사 | ⭐⭐⭐ CI/CD 통합 |
| **분석** | `analyze` | 평가 결과 분석 (NLP/인과) | ⭐⭐⭐ 인사이트 추출 |
| | `analyze-compare` | 평가 비교 분석 | ⭐⭐⭐ 추세 분석 |
| | `compare` | 두 평가 결과 비교 | ⭐⭐ 회귀 감지 |
| **히스토리** | `history` | 평가 이력 조회 | ⭐ 조회용 |
| | `export` | 결과 내보내기 | ⭐⭐ 보고서 자동화 |
| **생성** | `generate` | 테스트셋 생성 | ⭐⭐⭐ 데이터 증강 |
| | `kg` | Knowledge Graph 분석/생성 | ⭐⭐ 도메인 모델링 |
| **실험** | `experiment-create` | 실험 생성 | ⭐⭐ A/B 테스트 |
| | `experiment-add-group` | 실험 그룹 추가 | ⭐ |
| | `experiment-add-run` | 실험 실행 추가 | ⭐ |
| | `experiment-list` | 실험 목록 | ⭐ |
| | `experiment-compare` | 실험 그룹 비교 | ⭐⭐ 의사결정 지원 |
| | `experiment-conclude` | 실험 종료 및 결론 | ⭐⭐ |
| | `experiment-summary` | 실험 요약 | ⭐ |
| **도메인** | `domain init` | 도메인 초기화 | ⭐⭐ 온보딩 |
| | `domain list` | 도메인 목록 | ⭐ |
| | `domain show` | 도메인 상세 | ⭐ |
| | `domain terms` | 용어사전 관리 | ⭐⭐⭐ 지속 학습 |
| **설정** | `config` | 설정 확인 | ⭐ |
| | `metrics` | 메트릭 목록 | ⭐ |
| | `langfuse-dashboard` | Langfuse 연동 | ⭐ |
| **UI** | `web` | Web UI 실행 | ⭐ |
| **파이프라인** | `pipeline` | DAG 기반 분석 파이프라인 | ⭐⭐⭐ 복합 워크플로우 |

### 2.2 도메인 서비스 (13개)

| 서비스 | 파일 | 기능 | 에이전트 연동 우선순위 |
|--------|------|------|------------------------|
| **RagasEvaluator** | `evaluator.py` | 6개 메트릭 평가 | 🔴 핵심 |
| **AnalysisService** | `analysis_service.py` | 통계/NLP/인과 분석 | 🔴 핵심 |
| **TestsetGenerator** | `testset_generator.py` | 테스트 케이스 생성 | 🔴 핵심 |
| **KGGenerator** | `kg_generator.py` | Knowledge Graph 생성 | 🟡 중요 |
| **EntityExtractor** | `entity_extractor.py` | 엔티티 추출 | 🟡 중요 |
| **ExperimentManager** | `experiment_manager.py` | A/B 실험 관리 | 🟡 중요 |
| **BenchmarkRunner** | `benchmark_runner.py` | 벤치마크 실행 | 🟡 중요 |
| **PipelineOrchestrator** | `pipeline_orchestrator.py` | DAG 파이프라인 | 🟡 중요 |
| **IntentClassifier** | `intent_classifier.py` | 질문 의도 분류 | 🟢 보조 |
| **DomainLearningHook** | `domain_learning_hook.py` | 도메인 학습 | 🔴 핵심 |
| **ImprovementGuideService** | `improvement_guide_service.py` | 개선 가이드 생성 | 🔴 핵심 |
| **DocumentChunker** | `document_chunker.py` | 문서 청킹 | 🟢 보조 |
| **PipelineTemplateRegistry** | `pipeline_template_registry.py` | 파이프라인 템플릿 | 🟢 보조 |

### 2.3 어댑터 (25+개)

| 카테고리 | 어댑터 | 에이전트 활용 방법 |
|----------|--------|-------------------|
| **LLM** | OpenAI, Azure, Anthropic, Ollama | 모델 비교 자동화 |
| **Storage** | SQLite, PostgreSQL | 데이터 마이그레이션 자동화 |
| **Tracker** | Langfuse, MLflow | 실험 추적 자동화 |
| **Analysis** | Statistical, NLP, Causal | 분석 파이프라인 자동화 |
| **Cache** | MemoryCache (LRU+TTL) | 성능 모니터링 |
| **Dataset** | CSV, Excel, JSON Loaders | 데이터 검증 자동화 |
| **Web** | React Components | UI 테스트 자동화 |

### 2.4 도메인 엔티티 (9개)

| 엔티티 | 용도 | 에이전트 활용 |
|--------|------|--------------|
| TestCase, Dataset | 테스트 데이터 | 품질 검증 |
| EvaluationRun, MetricScore | 평가 결과 | 추세 분석 |
| Experiment | A/B 테스트 | 실험 관리 |
| Benchmark | 성능 측정 | 정기 벤치마크 |
| KnowledgeGraph | 도메인 지식 | 지식 확장 |
| AnalysisResult | 분석 결과 | 인사이트 추출 |
| DomainMemory | 도메인 학습 | 지속 개선 |

---

## 3. 기능별 에이전트 적용 전략

### 3.1 개발 자동화 에이전트 (기존 구현)

현재 구현된 8개 에이전트:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Development Mode Agents                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │architecture │  │observability│  │ rag-data    │              │
│  │ P0/P1/P2    │  │    P7       │  │    P7       │              │
│  │             │  │             │  │ (blocked)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ performance │  │  testing    │  │documentation│              │
│  │    P3       │  │    P5       │  │    P6       │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ coordinator │  │web-ui-test  │                               │
│  │   (All)     │  │  (Legacy)   │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                  │
│  병렬 실행 그룹:                                                  │
│  Group A: performance, testing, documentation (독립)             │
│  Group B: observability → rag-data (순차)                        │
│  Group C: architecture (내부 순서 P0→P1→P2)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 운영 자동화 에이전트 (제안)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Operation Mode Agents                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────────────────┐                          │
│                    │eval-coordinator │                          │
│                    │ (운영 총괄)      │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│      ┌──────────────────────┼──────────────────────┐            │
│      │                      │                      │            │
│      ▼                      ▼                      ▼            │
│ ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│ │domain-expert│      │testset-     │      │quality-     │      │
│ │             │      │curator      │      │monitor      │      │
│ │ - 용어사전   │      │ - 갭분석     │      │ - 정기평가   │      │
│ │ - 엔티티학습 │      │ - TC생성     │      │ - 추세분석   │      │
│ │ - 도메인규칙 │      │ - 분포균형   │      │ - 알림       │      │
│ └─────────────┘      └─────────────┘      └─────────────┘      │
│      │                      │                      │            │
│      └──────────────────────┼──────────────────────┘            │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ EvalVault Core  │                          │
│                    └─────────────────┘                          │
│                                                                  │
│  신규 에이전트:                                                   │
│  - experiment-analyst: A/B 테스트 분석 자동화                     │
│  - report-generator: 보고서 자동 생성                             │
│  - data-validator: 데이터셋 품질 검증                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 핵심 기능별 자동화 상세

### 4.1 평가 자동화 (Impact: ⭐⭐⭐⭐⭐)

**대상 CLI**: `run`, `benchmark`, `gate`

**자동화 시나리오**:

```bash
# Quality Monitor 에이전트가 실행하는 일일 워크플로우

# 1. 정기 평가 실행
evalvault run benchmark_data.json \
  --metrics faithfulness,answer_relevancy,context_precision \
  --parallel --batch-size 10 \
  --db data/db/evalvault.db \
  --output daily_$(date +%Y%m%d).json

# 2. 품질 게이트 검사
evalvault gate "$RUN_ID" --db data/db/evalvault.db \
  --threshold faithfulness:0.8 \
  --threshold answer_relevancy:0.7 \
  --fail-on-regression

# 3. 벤치마크 (주간)
evalvault benchmark run --name korean-rag \
  --output weekly_benchmark.json
```

`RUN_ID`는 `evalvault run` 출력 또는 `evalvault history --db data/db/evalvault.db`에서 확인합니다.

**에이전트 역할**:
- **quality-monitor**: 정기 평가 스케줄링, 결과 수집, 알림
- **eval-coordinator**: 복수 도메인 평가 조율

**예상 효과**:
| 지표 | Before | After |
|------|--------|-------|
| 평가 실행 | 수동 | 자동 (일/주/월) |
| 결과 확인 | 매번 수동 | 알림 기반 |
| 회귀 감지 | 1-2주 | 실시간 |

---

### 4.2 분석 자동화 (Impact: ⭐⭐⭐⭐⭐)

**대상 CLI**: `analyze`, `analyze-compare`, `compare`

**자동화 시나리오**:

```bash
# 평가 후 자동 분석 파이프라인

# 1. 통계 + NLP + 인과 분석
evalvault analyze $RUN_ID \
  --nlp --causal \
  --report analysis_report.html

# 2. 이전 결과와 비교
evalvault compare $BASELINE_ID $RUN_ID \
  --detailed

# 3. 다중 실행 비교 분석
evalvault analyze-compare $RUN_ID_1 $RUN_ID_2 $RUN_ID_3 \
  --output comparison.json
```

**연동할 도메인 서비스**:
- `AnalysisService`: 통계/NLP/인과 분석
- `ImprovementGuideService`: 개선 가이드 생성
- `DomainLearningHook`: 분석 결과로부터 학습

**에이전트 역할**:
- **domain-expert**: 도메인 관점 분석, 용어사전 업데이트
- **testset-curator**: 실패 패턴 분석 → 테스트 케이스 보강

**ImprovementGuideService 활용**:
```python
# 에이전트가 개선 가이드를 자동 생성
from evalvault.domain.services import ImprovementGuideService

service = ImprovementGuideService()
guide = await service.generate_guide(
    evaluation_run=run,
    analysis_result=analysis,
    domain="insurance"
)

# 가이드 내용:
# - 낮은 점수 패턴 분석
# - 개선 권장사항
# - 우선순위별 액션 아이템
```

---

### 4.3 테스트셋 관리 자동화 (Impact: ⭐⭐⭐⭐)

**대상 CLI**: `generate`, `kg`

**자동화 시나리오**:

```bash
# Testset Curator 에이전트 워크플로우

# 1. 갭 분석 (낮은 점수 케이스)
evalvault analyze $RUN_ID --causal --output gap_analysis.json

# 2. KG 기반 테스트셋 확장
evalvault generate kg documents.md \
  --num-questions 50 \
  --domain insurance \
  --difficulty mixed \
  --output new_testcases.json

# 3. 기존 테스트셋과 병합
evalvault dataset merge base.json new_testcases.json \
  --output expanded.json \
  --deduplicate
```

**연동할 도메인 서비스**:
- `TestsetGenerator`: 테스트 케이스 생성
- `KGGenerator`: Knowledge Graph 기반 생성
- `EntityExtractor`: 엔티티 추출로 다양성 확보

**에이전트 역할**:
- **testset-curator**:
  1. 평가 실패 케이스 분석
  2. 커버리지 갭 식별
  3. 새 테스트 케이스 생성/제안
  4. 분포 균형 검사
  5. PR 생성 (자동)

**예상 효과**:
| 지표 | Before | After |
|------|--------|-------|
| 테스트셋 커버리지 | 70% | 90% |
| 새 TC 추가 | 수동 | 자동 제안 |
| 갭 발견 | 사후 | 사전 |

---

### 4.4 도메인 지식 관리 자동화 (Impact: ⭐⭐⭐⭐)

**대상 CLI**: `domain init/list/show/terms`

**Domain Memory 구조**:
```
config/domains/{domain}/
├── memory.yaml              # 도메인 설정
├── terms_dictionary_ko.json # 한국어 용어사전
├── terms_dictionary_en.json # 영어 용어사전
└── reliability.json         # 엔티티 타입별 신뢰도
```

**자동화 시나리오**:

```python
# Domain Expert 에이전트의 학습 루프

from evalvault.domain.services import DomainLearningHook

# 1. 평가 완료 후 자동 학습
hook = DomainLearningHook(memory_adapter)
result = await hook.on_evaluation_complete(
    evaluation_run=run,
    domain="insurance",
    language="ko"
)

# 2. 새 용어 발견 시 용어사전 업데이트
if result.new_terms:
    for term in result.new_terms:
        await hook.add_term(
            domain="insurance",
            term=term.text,
            definition=term.definition,
            confidence=term.confidence
        )

# 3. 신뢰도 점수 조정
await hook.update_reliability(
    domain="insurance",
    entity_type="coverage_amount",
    new_score=0.85
)

# 4. 진화 실행 (패턴 통합)
await hook.run_evolution(domain="insurance")
```

**에이전트 역할**:
- **domain-expert**:
  1. 평가 결과 도메인 관점 분석
  2. 새 용어 발견 → 용어사전 추가
  3. 반복 실패 패턴 → 도메인 규칙 보완
  4. 엔티티 추출 정확도 → 신뢰도 조정

---

### 4.5 실험 관리 자동화 (Impact: ⭐⭐⭐)

**대상 CLI**: `experiment-*` (7개 명령어)

**자동화 시나리오**:

```bash
# A/B 테스트 자동화 워크플로우

# 1. 실험 생성
evalvault experiment-create "LLM Model Comparison" \
  --hypothesis "GPT-4 shows better faithfulness than GPT-3.5"

# 2. 그룹 추가
evalvault experiment-add-group $EXP_ID --name "gpt-4" --description "GPT-4 Turbo"
evalvault experiment-add-group $EXP_ID --name "gpt-3.5" --description "GPT-3.5 Turbo"

# 3. 각 그룹으로 평가 실행 (에이전트가 자동 수행)
for group in gpt-4 gpt-3.5; do
  evalvault run testset.json --model $group --output ${group}_result.json
  evalvault experiment-add-run $EXP_ID $group ${group}_result.json
done

# 4. 비교 및 결론
evalvault experiment-compare $EXP_ID
evalvault experiment-conclude $EXP_ID --winner gpt-4 --reasoning "15% higher faithfulness"
```

**에이전트 역할**:
- **experiment-analyst** (신규 제안):
  1. 실험 설계 자동화
  2. 통계적 유의성 검정
  3. 결과 시각화
  4. 의사결정 권장

---

### 4.6 파이프라인 자동화 (Impact: ⭐⭐⭐)

**대상 CLI**: `pipeline`

**DAG 파이프라인 구조**:
```
DataLoader → Evaluator → StatisticalAnalyzer
                      ↘ NLPAnalyzer
                      ↘ CausalAnalyzer → ReportGenerator
```

**자동화 시나리오**:

```bash
# 복합 분석 파이프라인 자동 실행

evalvault pipeline run \
  --template comprehensive_analysis \
  --input data.json \
  --output-dir ./reports/

# 파이프라인 템플릿 예시:
# - quick_eval: 기본 평가만
# - comprehensive: 평가 + 모든 분석
# - regression_check: 이전 결과 비교 중심
# - domain_learning: 평가 + 도메인 학습
```

**연동할 서비스**:
- `PipelineOrchestrator`: DAG 실행 관리
- `PipelineTemplateRegistry`: 템플릿 관리

---

### 4.7 보고서 자동화 (Impact: ⭐⭐⭐)

**대상 CLI**: `export`, `analyze --report`

**자동화 시나리오**:

```bash
# Report Generator 에이전트 워크플로우

# 1. 일일 보고서
evalvault analyze $RUN_ID --report daily_report.html

# 2. 주간 요약 (여러 실행 통합)
evalvault export --format markdown \
  --runs $RUN_1 $RUN_2 $RUN_3 \
  --output weekly_summary.md

# 3. 월간 트렌드 보고서
evalvault analyze-compare \
  --period monthly \
  --output trend_report.html
```

**에이전트 역할**:
- **report-generator** (신규 제안):
  1. 정기 보고서 자동 생성
  2. 이해관계자별 맞춤 보고서
  3. 이메일/Slack 자동 발송

---

## 5. 효율 vs 임팩트 분석

### 5.1 매트릭스 분석

```
                    높은 임팩트
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         │  ⭐ 우선순위 1│ ⭐ 우선순위 2 │
         │              │              │
         │ • 평가 자동화 │ • 실험 관리   │
         │ • 분석 자동화 │ • 보고서 자동화│
         │ • 도메인 학습 │ • 파이프라인   │
낮은 노력 ├──────────────┼──────────────┤ 높은 노력
         │              │              │
         │  우선순위 3   │ 우선순위 4    │
         │              │              │
         │ • 데이터 검증 │ • 전체 통합   │
         │ • 히스토리조회│ • 멀티도메인  │
         │              │              │
         └──────────────┼──────────────┘
                        │
                    낮은 임팩트
```

### 5.2 우선순위 상세

| 우선순위 | 기능 영역 | 구현 노력 | 예상 효과 | ROI |
|----------|-----------|-----------|-----------|-----|
| **P1** | 평가+분석 자동화 | 중 | 매우 높음 | ⭐⭐⭐⭐⭐ |
| **P1** | 도메인 학습 자동화 | 중 | 높음 | ⭐⭐⭐⭐ |
| **P2** | 테스트셋 큐레이션 | 중 | 높음 | ⭐⭐⭐⭐ |
| **P2** | 보고서 자동화 | 낮 | 중간 | ⭐⭐⭐ |
| **P3** | 실험 관리 자동화 | 중 | 중간 | ⭐⭐⭐ |
| **P3** | 파이프라인 자동화 | 중 | 중간 | ⭐⭐⭐ |
| **P4** | 멀티도메인 통합 | 높 | 높음 | ⭐⭐ |

### 5.3 기능별 자동화 가치 분석

| 기능 | 수동 소요 시간 | 자동화 후 | 절감률 | 품질 향상 |
|------|---------------|-----------|--------|-----------|
| 일일 평가 실행 | 30분/일 | 0분 | 100% | 일관성 ↑ |
| 결과 분석 | 2시간/건 | 5분/건 | 96% | 깊이 ↑ |
| 테스트셋 보강 | 4시간/주 | 30분/주 | 88% | 커버리지 ↑ |
| 도메인 용어 관리 | 2시간/주 | 자동 | 100% | 정확도 ↑ |
| 보고서 작성 | 1시간/건 | 5분/건 | 92% | 표준화 ↑ |
| 품질 저하 감지 | 1-2주 | 실시간 | - | 대응속도 ↑ |

---

## 6. 구현 로드맵

### Phase 1: 핵심 운영 에이전트 (구현 준비)

**새 에이전트 타입 추가** (`agent/config.py`):

```python
class AgentType(str, Enum):
    # 기존 개발 자동화
    ARCHITECTURE = "architecture"
    OBSERVABILITY = "observability"
    RAG_DATA = "rag-data"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COORDINATOR = "coordinator"
    WEB_UI_TESTING = "web-ui-testing"

    # 신규 운영 자동화
    DOMAIN_EXPERT = "domain-expert"
    TESTSET_CURATOR = "testset-curator"
    QUALITY_MONITOR = "quality-monitor"
    EVAL_COORDINATOR = "eval-coordinator"
    EXPERIMENT_ANALYST = "experiment-analyst"
    REPORT_GENERATOR = "report-generator"
    DATA_VALIDATOR = "data-validator"
```

**프롬프트 작성** (`agent/prompts/operation/`):

```
agent/prompts/operation/
├── domain_expert_prompt.md
├── testset_curator_prompt.md
├── quality_monitor_prompt.md
├── eval_coordinator_prompt.md
├── experiment_analyst_prompt.md
├── report_generator_prompt.md
└── data_validator_prompt.md
```

### Phase 2: Quality Monitor 구현

**핵심 기능**:
1. 정기 평가 스케줄링 (cron 기반)
2. 결과 수집 및 비교
3. 회귀 감지 및 알림
4. 대시보드 업데이트

**GitHub Actions 통합**:

```yaml
# .github/workflows/quality-monitor.yml
name: Quality Monitor
on:
  schedule:
    - cron: '0 9 * * *'  # 매일 오전 9시
  workflow_dispatch:

jobs:
  daily-evaluation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup uv
        uses: astral-sh/setup-uv@v5

      - name: Run evaluation
        run: |
          uv sync --extra dev
          uv run evalvault run benchmark_data.json \
            --metrics faithfulness,answer_relevancy \
            --db data/db/evalvault.db \
            --output results/daily_$(date +%Y%m%d).json

      - name: Check quality gate
        run: |
          # RUN_ID는 evalvault run 출력 또는 history에서 추출
          uv run evalvault gate "$RUN_ID" --db data/db/evalvault.db \
            --threshold faithfulness:0.8 \
            --fail-on-regression

      - name: Generate report
        if: always()
        run: |
          uv run evalvault analyze ${{ steps.eval.outputs.run_id }} \
            --report reports/daily_report.html

      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {"text": "⚠️ Quality gate failed! Check the report."}
```

### Phase 3: Domain Expert 구현

**DomainLearningHook 연동**:

```python
# agent/domain_integration.py

from evalvault.domain.services import DomainLearningHook
from evalvault.adapters.outbound.storage import SQLiteAdapter

class DomainExpertIntegration:
    """Domain Expert 에이전트와 EvalVault 연동."""

    def __init__(self, domain: str, language: str = "ko"):
        self.domain = domain
        self.language = language
        self.storage = SQLiteAdapter()
        self.hook = DomainLearningHook(self.storage)

    async def learn_from_evaluation(self, run_id: str):
        """평가 결과로부터 학습."""
        run = await self.storage.get_evaluation_run(run_id)

        # 자동 학습 실행
        result = await self.hook.on_evaluation_complete(
            evaluation_run=run,
            domain=self.domain,
            language=self.language
        )

        return {
            "new_terms": result.new_terms,
            "updated_reliability": result.updated_reliability,
            "learned_patterns": result.learned_patterns
        }

    async def update_terms_dictionary(self, terms: list[dict]):
        """용어사전 업데이트."""
        for term in terms:
            await self.hook.add_term(
                domain=self.domain,
                term=term["text"],
                definition=term["definition"],
                confidence=term.get("confidence", 0.8)
            )

    async def run_evolution(self):
        """도메인 지식 진화."""
        return await self.hook.run_evolution(domain=self.domain)
```

### Phase 4: Testset Curator 구현

**갭 분석 및 테스트 생성**:

```python
# agent/testset_integration.py

from evalvault.domain.services import (
    TestsetGenerator,
    KGGenerator,
    AnalysisService
)

class TestsetCuratorIntegration:
    """Testset Curator 에이전트와 EvalVault 연동."""

    def __init__(self, domain: str):
        self.domain = domain
        self.generator = TestsetGenerator()
        self.kg_generator = KGGenerator()
        self.analyzer = AnalysisService()

    async def analyze_gaps(self, run_id: str) -> dict:
        """커버리지 갭 분석."""
        analysis = await self.analyzer.analyze(
            run_id,
            include_nlp=True,
            include_causal=True
        )

        return {
            "low_score_patterns": analysis.low_score_patterns,
            "uncovered_topics": analysis.uncovered_topics,
            "recommended_focus_areas": analysis.recommendations
        }

    async def generate_targeted_cases(
        self,
        gap_analysis: dict,
        num_cases: int = 10
    ) -> list:
        """갭을 보완하는 테스트 케이스 생성."""
        cases = []

        for pattern in gap_analysis["low_score_patterns"]:
            new_cases = await self.generator.generate(
                topic=pattern.topic,
                difficulty=pattern.difficulty,
                count=num_cases // len(gap_analysis["low_score_patterns"])
            )
            cases.extend(new_cases)

        return cases

    async def check_distribution_balance(
        self,
        dataset_path: str
    ) -> dict:
        """테스트셋 분포 균형 검사."""
        # 난이도, 토픽, 길이 등의 분포 분석
        pass
```

### Phase 5: 통합 및 CI/CD

**전체 워크플로우**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Automated RAG Evaluation Pipeline             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │ Trigger     │  • Schedule (cron)                             │
│  │             │  • Manual                                       │
│  │             │  • PR/Push                                      │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ Evaluate    │ ──▶ │ Analyze     │ ──▶ │ Learn       │       │
│  │ (run)       │     │ (analyze)   │     │ (domain)    │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ Gate Check  │     │ Generate    │     │ Update      │       │
│  │ (gate)      │     │ Testcases   │     │ Terms Dict  │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                   │                   │                │
│         └───────────────────┴───────────────────┘                │
│                             │                                    │
│                             ▼                                    │
│                    ┌─────────────┐                              │
│                    │ Report &    │                              │
│                    │ Notify      │                              │
│                    └─────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 예상 효과 종합

### 7.1 정량적 효과

| 지표 | Before | After | 개선 |
|------|--------|-------|------|
| 일일 평가 실행 | 수동 30분 | 자동 0분 | -100% |
| 결과 분석 시간 | 2시간/건 | 5분/건 | -96% |
| 도메인 용어 정확도 | 80% | 95% | +15% |
| 테스트셋 커버리지 | 70% | 90% | +20% |
| 품질 저하 감지 | 1-2주 | 실시간 | 즉시 |
| 보고서 작성 | 1시간/건 | 5분/건 | -92% |
| 전체 수동 작업 | 10시간/주 | 1시간/주 | -90% |

### 7.2 정성적 효과

1. **일관성**: 자동화된 프로세스로 인간 오류 제거
2. **확장성**: 새 도메인/모델 추가 시 빠른 온보딩
3. **지식 축적**: 평가할수록 도메인 이해도 향상
4. **빠른 피드백**: 품질 문제 실시간 감지
5. **의사결정 지원**: 데이터 기반 개선 권장

---

## 8. 결론 및 권장사항

### 8.1 즉시 활용 가능

```bash
# 1. 개발 자동화 에이전트 실행
cd agent/
uv run python main.py --project-dir .. --agent-type architecture

# 2. 코디네이터로 전체 상태 확인
uv run python main.py --project-dir .. --agent-type coordinator
```

### 8.2 단기 구현 권장

1. **Quality Monitor 에이전트**: GitHub Actions 통합
2. **Domain Expert 에이전트**: DomainLearningHook 연동
3. **Testset Curator 에이전트**: 갭 분석 자동화

### 8.3 중장기 목표

1. **운영 자동화 완성**: 7개 신규 에이전트
2. **멀티도메인 지원**: 보험, 법률, 의료 등
3. **CI/CD 통합**: 완전 자동화 파이프라인

---

## 참고

- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md): 개발 가이드 (자동화 계획 포함)
- [agent/README.md](https://github.com/ntts9990/EvalVault/blob/main/agent/README.md): 에이전트 시스템 가이드
- [archive/COMPLETED.md](../archive/COMPLETED.md): Phase 1-14 완료 내역 (아카이브)
- [ROADMAP.md](../../status/ROADMAP.md): 2026-2027 개발 로드맵
