# EvalVault 전략적 발전 방향

> RAGAS 래퍼를 넘어서는 고유 가치 창출을 위한 로드맵

## 현재 상태 분석

### 강점 (차별화 포인트)
1. **Knowledge Graph 기반 테스트셋 생성** - RAGAS에는 없는 고유 기능
2. **Insurance 도메인 특화 메트릭** - `InsuranceTermAccuracy` 등
3. **Experiment Management** - A/B 테스트 및 그룹 비교
4. **다양한 어댑터 지원** - LLM, Storage, Tracker 확장성
5. **Hexagonal Architecture** - 확장 가능한 설계

### 약점 (비판의 핵심)
1. **RAGAS 의존성** - 단순히 RAGAS를 실행하는 래퍼로 보임
2. **도메인 특화 부족** - Insurance 외 다른 도메인 지원 미흡
3. **인사이트 부족** - 평가 결과를 넘어선 액션 가능한 인사이트 부재
4. **자동화 부족** - CI/CD 통합, 자동 평가 파이프라인 미흡

---

## 전략적 발전 방향

### 방향 1: 도메인 특화 플랫폼으로 진화

**목표**: RAGAS는 범용 도구, EvalVault는 도메인 특화 평가 플랫폼

#### 1.1 도메인별 메트릭 확장
- **Insurance**: `InsuranceTermAccuracy` (현재 구현됨)
- **Legal**: 법률 용어 정확도, 조항 참조 정확도
- **Medical**: 의학 용어 정확도, 약물 상호작용 검증
- **Finance**: 금융 용어 정확도, 규제 준수 검증
- **Technical**: 코드/API 문서 정확도, 기술 명세 준수

**구현 전략**:
```python
# 도메인별 메트릭 플러그인 시스템
class DomainMetric(Protocol):
    """도메인 특화 메트릭 인터페이스"""
    domain: str
    name: str
    def score(self, answer: str, contexts: list[str], **kwargs) -> float

# 도메인별 용어 사전 관리
config/
├── domains/
│   ├── insurance/
│   │   ├── terms_dictionary.json
│   │   └── metrics.py
│   ├── legal/
│   │   ├── terms_dictionary.json
│   │   └── metrics.py
│   └── medical/
│       ├── terms_dictionary.json
│       └── metrics.py
```

#### 1.2 도메인별 엔티티 추출기 확장
- 현재: Insurance 엔티티 추출기만 존재
- 확장: Legal, Medical, Finance 등 도메인별 추출기
- 공통 인터페이스로 통합하여 도메인 전환 용이

#### 1.3 도메인별 테스트셋 생성 전략
- Insurance: 보험 상품, 보장 내용, 청구 절차 중심
- Legal: 법률 조항, 판례, 계약서 중심
- Medical: 질병, 치료, 약물 중심

**예시**:
```bash
# 도메인별 테스트셋 생성
evalvault generate insurance-doc.txt --domain insurance -n 100
evalvault generate legal-doc.txt --domain legal -n 100
```

---

### 방향 2: 평가 자동화 및 CI/CD 통합

**목표**: 평가를 개발 워크플로우에 자연스럽게 통합

#### 2.1 CI/CD 통합
- GitHub Actions, GitLab CI, Jenkins 플러그인
- PR마다 자동 평가 실행
- 메트릭 임계값 미달 시 PR 차단

**예시**:
```yaml
# .github/workflows/evalvault.yml
- name: Run EvalVault
  run: |
    evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
      --metrics faithfulness,answer_relevancy \
      --threshold faithfulness:0.8 \
      --fail-on-threshold
```

#### 2.2 자동 평가 스케줄링
- 정기적으로 평가 실행 (cron, GitHub Actions scheduled)
- 모델 변경 시 자동 평가
- 데이터셋 업데이트 시 자동 평가

#### 2.3 평가 결과 알림
- Slack, Discord, Email 통합
- 메트릭 임계값 하회 시 알림
- 개선/악화 추이 알림

---

### 방향 3: 액션 가능한 인사이트 제공

**목표**: 평가 결과를 넘어서 문제 해결 방안 제시

#### 3.1 실패 케이스 분석
- 낮은 점수를 받은 테스트 케이스 자동 분석
- 실패 원인 분류 (hallucination, retrieval failure, context mismatch 등)
- 개선 제안 생성

**예시**:
```bash
evalvault analyze <run_id> --focus failures
# 출력:
# - 15개 케이스에서 hallucination 감지
# - 8개 케이스에서 retrieval failure
# - 제안: context_precision 메트릭 개선 필요
```

#### 3.2 메트릭 간 상관관계 분석
- 메트릭 간 상관관계 시각화
- 어떤 메트릭이 전체 품질과 가장 연관 있는지 분석
- 메트릭별 개선 우선순위 제시

#### 3.3 데이터셋 품질 분석
- 테스트셋의 다양성, 난이도 분석
- 커버리지 분석 (어떤 주제가 부족한지)
- 데이터셋 개선 제안

#### 3.4 모델 비교 및 추천
- 여러 모델 평가 결과 비교
- 도메인별 최적 모델 추천
- 비용 대비 성능 분석

---

### 방향 4: Knowledge Graph 고도화

**목표**: KG를 단순 테스트셋 생성 도구가 아닌 평가 인프라로 진화

#### 4.1 KG 기반 평가
- KG를 ground truth로 활용한 평가
- 엔티티-관계 기반 정확도 평가
- Multi-hop reasoning 평가

#### 4.2 KG 기반 자동 테스트셋 생성
- 현재: 문서 → KG → 테스트셋
- 확장: KG 업데이트 → 자동 테스트셋 재생성
- KG 커버리지 기반 테스트셋 보완

#### 4.3 KG 기반 인사이트
- KG 구조 분석 (어떤 관계가 자주 등장하는지)
- KG 불일치 감지 (답변과 KG 간 불일치)
- KG 업데이트 제안

**구현 계획**: `docs/KG_IMPROVEMENT_PLAN.md` 참조

---

### 방향 5: 평가 파이프라인 오케스트레이션

**목표**: 복잡한 평가 워크플로우를 쉽게 구성

#### 5.1 평가 파이프라인 정의
- YAML/JSON으로 평가 파이프라인 정의
- 여러 데이터셋, 여러 모델, 여러 메트릭 조합
- 파이프라인 재사용 및 공유

**예시**:
```yaml
# pipeline.yaml
name: "Insurance QA Evaluation"
datasets:
  - path: "data/insurance_qa_korean.json"
    metrics: ["faithfulness", "answer_relevancy"]
  - path: "data/insurance_qa_english.json"
    metrics: ["faithfulness", "answer_relevancy", "context_precision"]
models:
  - profile: "openai"
  - profile: "anthropic"
output:
  storage: "sqlite"
  tracker: "langfuse"
```

#### 5.2 평가 워크플로우 시각화
- 파이프라인 실행 흐름 시각화
- 각 단계별 진행 상황 추적
- 병목 지점 식별

#### 5.3 평가 결과 통합 리포트
- 여러 평가 실행 결과 통합 분석
- 트렌드 분석 (시간에 따른 변화)
- 비교 리포트 생성

---

### 방향 6: 커뮤니티 및 생태계 구축

**목표**: EvalVault를 단순 도구가 아닌 생태계로 확장

#### 6.1 도메인별 프리셋 제공
- Insurance, Legal, Medical 등 도메인별 프리셋
- 커뮤니티가 프리셋 공유 가능
- 프리셋 마켓플레이스

#### 6.2 데이터셋 공유 플랫폼
- 커뮤니티 데이터셋 공유
- 데이터셋 품질 평가 및 검증
- 데이터셋 버전 관리

#### 6.3 플러그인 시스템
- 커스텀 메트릭 플러그인
- 커스텀 어댑터 플러그인
- 커스텀 데이터 로더 플러그인

---

## 오픈소스 도구 적극 활용 전략

> 2025년 12월 기준, GitHub에서 인기 있고 평가가 좋은 오픈소스 도구들을 적극적으로 통합하여 개발 효율성과 기능성을 향상시킵니다.

### 평가 및 테스트 프레임워크

#### 1. **Phoenix (Arize AI)**
- **GitHub**: https://github.com/Arize-ai/phoenix
- **용도**: LLM 애플리케이션 평가 및 관찰성
- **활용 방안**:
  - RAGAS와 병행하여 평가 메트릭 확장
  - 실시간 평가 대시보드 통합
  - 트레이싱 및 디버깅 기능 활용
- **통합 예시**:
```python
# Phoenix 어댑터 추가
from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

tracker = PhoenixAdapter()
evaluator.evaluate(dataset, metrics, llm, tracker=tracker)
```

#### 2. **DeepEval (Confident AI)**
- **GitHub**: https://github.com/confident-ai/deepeval
- **용도**: LLM 평가 프레임워크
- **활용 방안**:
  - 평가 메트릭 라이브러리 확장
  - 자동 평가 파이프라인 구축
  - CI/CD 통합 지원
- **통합 예시**:
```python
# DeepEval 메트릭을 EvalVault 메트릭으로 통합
from deepeval.metrics import AnswerRelevancyMetric
from evalvault.domain.metrics.deepeval_adapter import DeepEvalMetricAdapter

metric = DeepEvalMetricAdapter(AnswerRelevancyMetric())
evaluator.add_custom_metric("deepeval_relevancy", metric)
```

#### 3. **Promptfoo**
- **GitHub**: https://github.com/promptfoo/promptfoo
- **용도**: LLM 프롬프트 테스트 및 평가
- **활용 방안**:
  - 프롬프트 버전 비교
  - A/B 테스트 자동화
  - 프롬프트 최적화
- **통합 예시**:
```bash
# Promptfoo와 EvalVault 통합
evalvault run dataset.json --promptfoo-config promptfoo.yaml
```

---

### CI/CD 및 자동화

#### 4. **GitHub Actions**
- **GitHub**: https://github.com/features/actions
- **용도**: CI/CD 자동화
- **활용 방안**:
  - PR마다 자동 평가 실행
  - 평가 결과를 PR 코멘트로 자동 업로드
  - 메트릭 임계값 미달 시 PR 차단
- **통합 예시**:
```yaml
# .github/workflows/evalvault.yml
name: EvalVault CI
on: [pull_request]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install evalvault
      - run: |
          evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
            --metrics faithfulness,answer_relevancy \
            --threshold faithfulness:0.8 \
            --fail-on-threshold \
            --github-pr-comment
```

#### 5. **Pre-commit Hooks**
- **GitHub**: https://github.com/pre-commit/pre-commit
- **용도**: 커밋 전 자동 검증
- **활용 방안**:
  - 데이터셋 스키마 검증
  - 평가 결과 형식 검증
  - 메트릭 임계값 검증
- **통합 예시**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: evalvault-validate
        name: EvalVault Dataset Validation
        entry: evalvault validate
        language: system
        files: \.(json|csv|xlsx)$
```

---

### 인사이트 및 분석

#### 6. **Apache Superset**
- **GitHub**: https://github.com/apache/superset
- **용도**: 데이터 시각화 및 BI
- **활용 방안**:
  - 평가 결과 대시보드 구축
  - 메트릭 트렌드 시각화
  - 모델 비교 리포트 생성
- **통합 예시**:
```python
# Superset 어댑터
from evalvault.adapters.outbound.analytics.superset_adapter import SupersetAdapter

analytics = SupersetAdapter()
analytics.export_evaluation_results(run_id, dashboard_id="evalvault-dashboard")
```

#### 7. **Grafana**
- **GitHub**: https://github.com/grafana/grafana
- **용도**: 메트릭 시각화 및 모니터링
- **활용 방안**:
  - 실시간 평가 메트릭 모니터링
  - 알림 설정 (임계값 하회 시)
  - 대시보드 공유
- **통합 예시**:
```python
# Grafana 메트릭 전송
from evalvault.adapters.outbound.metrics.grafana_adapter import GrafanaAdapter

metrics = GrafanaAdapter(grafana_url="http://localhost:3000")
metrics.send_metrics(evaluation_run)
```

#### 8. **Great Expectations**
- **GitHub**: https://github.com/great-expectations/great-expectations
- **용도**: 데이터 품질 검증
- **활용 방안**:
  - 데이터셋 품질 검증
  - 평가 결과 데이터 검증
  - 데이터 드리프트 감지
- **통합 예시**:
```python
# Great Expectations 통합
from evalvault.adapters.outbound.validation.gx_adapter import GXAdapter

validator = GXAdapter()
validator.validate_dataset(dataset, expectations_suite="insurance_qa")
```

---

### Knowledge Graph 및 NLP

#### 9. **spaCy**
- **GitHub**: https://github.com/explosion/spaCy
- **용도**: 자연어 처리 라이브러리
- **활용 방안**:
  - 도메인별 엔티티 추출기 구축
  - 커스텀 NER 모델 학습
  - 의존성 파싱을 통한 관계 추출
- **통합 예시**:
```python
# spaCy 기반 엔티티 추출기
from evalvault.domain.services.entity_extractor import SpacyEntityExtractor

extractor = SpacyEntityExtractor(
    model="ko_core_news_sm",  # 또는 커스텀 모델
    domain="insurance"
)
entities = extractor.extract(document)
```

#### 10. **Neo4j**
- **GitHub**: https://github.com/neo4j/neo4j
- **용도**: 그래프 데이터베이스
- **활용 방안**:
  - Knowledge Graph 영구 저장
  - 그래프 쿼리를 통한 복잡한 질문 생성
  - 그래프 분석 및 시각화
- **통합 예시**:
```python
# Neo4j 어댑터
from evalvault.adapters.outbound.storage.neo4j_adapter import Neo4jAdapter

kg_storage = Neo4jAdapter(uri="bolt://localhost:7687")
kg_storage.save_knowledge_graph(kg)
```

#### 11. **NetworkX** (이미 사용 중)
- **GitHub**: https://github.com/networkx/networkx
- **용도**: 그래프 분석 라이브러리
- **활용 방안**:
  - 그래프 알고리즘 활용 (최단 경로, 커뮤니티 탐지)
  - 그래프 통계 계산
  - 시각화
- **현재 상태**: 이미 `kg_generator.py`에서 사용 중
- **확장 계획**: `docs/KG_IMPROVEMENT_PLAN.md` 참조

---

### 파이프라인 오케스트레이션

#### 12. **Apache Airflow**
- **GitHub**: https://github.com/apache/airflow
- **용도**: 워크플로우 관리 플랫폼
- **활용 방안**:
  - 복잡한 평가 파이프라인 오케스트레이션
  - 스케줄링된 평가 실행
  - 의존성 관리
- **통합 예시**:
```python
# Airflow DAG 예시
from airflow import DAG
from airflow.operators.bash import BashOperator

dag = DAG('evalvault_pipeline', schedule_interval='@daily')

evaluate_task = BashOperator(
    task_id='run_evaluation',
    bash_command='evalvault run dataset.json --metrics faithfulness',
    dag=dag
)
```

#### 13. **Prefect**
- **GitHub**: https://github.com/PrefectHQ/prefect
- **용도**: 현대적인 워크플로우 오케스트레이션
- **활용 방안**:
  - Airflow 대안으로 사용
  - 더 나은 Python 네이티브 지원
  - 실시간 모니터링
- **통합 예시**:
```python
# Prefect 플로우
from prefect import flow, task
from evalvault.domain.services.evaluator import RagasEvaluator

@task
def evaluate_dataset(dataset_path: str):
    evaluator = RagasEvaluator()
    return evaluator.evaluate(dataset_path)

@flow
def evaluation_pipeline():
    results = evaluate_dataset("data/insurance_qa.json")
    return results
```

---

### 데이터 버전 관리

#### 14. **DVC (Data Version Control)**
- **GitHub**: https://github.com/iterative/dvc
- **용도**: 데이터 및 모델 버전 관리
- **활용 방안**:
  - 데이터셋 버전 관리
  - 평가 결과 버전 관리
  - 재현 가능한 평가 보장
- **통합 예시**:
```bash
# DVC와 통합
dvc add data/insurance_qa_korean.json
evalvault run data/insurance_qa_korean.json --metrics faithfulness
dvc add results/evaluation_run_001.json
```

#### 15. **Pachyderm**
- **GitHub**: https://github.com/pachyderm/pachyderm
- **용도**: 데이터 파이프라인 버전 관리
- **활용 방안**:
  - 대규모 데이터셋 버전 관리
  - 데이터 파이프라인 자동화
  - 데이터 계보 추적
- **통합 예시**:
```yaml
# Pachyderm pipeline
pipeline:
  name: evalvault-evaluation
  input:
    pfs:
      repo: datasets
      glob: "/*.json"
  transform:
    image: evalvault:latest
    cmd: ["evalvault", "run", "/pfs/datasets/", "--metrics", "faithfulness"]
```

---

### 모니터링 및 관찰성

#### 16. **OpenTelemetry**
- **GitHub**: https://github.com/open-telemetry/opentelemetry-python
- **용도**: 분산 추적 및 메트릭
- **활용 방안**:
  - 평가 실행 추적
  - 성능 메트릭 수집
  - 분산 시스템 관찰성
- **통합 예시**:
```python
# OpenTelemetry 통합
from opentelemetry import trace
from evalvault.adapters.outbound.tracker.otel_adapter import OpenTelemetryAdapter

tracer = trace.get_tracer(__name__)
tracker = OpenTelemetryAdapter(tracer)
evaluator.evaluate(dataset, metrics, llm, tracker=tracker)
```

#### 17. **Prometheus**
- **GitHub**: https://github.com/prometheus/prometheus
- **용도**: 메트릭 수집 및 모니터링
- **활용 방안**:
  - 평가 메트릭 수집
  - 알림 설정
  - 장기 트렌드 분석
- **통합 예시**:
```python
# Prometheus 메트릭 전송
from evalvault.adapters.outbound.metrics.prometheus_adapter import PrometheusAdapter

metrics = PrometheusAdapter()
metrics.record_evaluation_metrics(evaluation_run)
```

---

### 커뮤니티 및 협업

#### 18. **Discourse**
- **GitHub**: https://github.com/discourse/discourse
- **용도**: 커뮤니티 포럼
- **활용 방안**:
  - 사용자 커뮤니티 구축
  - 프리셋 공유 플랫폼
  - 질문 및 답변
- **통합 예시**:
```python
# Discourse API 통합
from evalvault.adapters.outbound.community.discourse_adapter import DiscourseAdapter

community = DiscourseAdapter(api_url="https://community.evalvault.io")
community.share_preset(preset_name="insurance-korean", preset_data=preset)
```

#### 19. **Weights & Biases (W&B)**
- **GitHub**: https://github.com/wandb/wandb
- **용도**: ML 실험 추적 및 협업
- **활용 방안**:
  - 평가 실험 추적
  - 모델 비교
  - 팀 협업
- **통합 예시**:
```python
# W&B 통합
from evalvault.adapters.outbound.tracker.wandb_adapter import WandBAdapter

tracker = WandBAdapter(project="evalvault-evaluations")
tracker.log_evaluation_run(evaluation_run)
```

---

### 통합 전략

#### 단계별 통합 계획

1. **Phase 1 (즉시 통합 가능)**:
   - Phoenix: 평가 메트릭 확장
   - spaCy: 엔티티 추출기 강화
   - DVC: 데이터 버전 관리

2. **Phase 2 (단기, 1-2개월)**:
   - GitHub Actions: CI/CD 통합
   - Apache Superset: 대시보드 구축
   - Great Expectations: 데이터 품질 검증

3. **Phase 3 (중기, 3-6개월)**:
   - Apache Airflow/Prefect: 파이프라인 오케스트레이션
   - Neo4j: KG 영구 저장
   - OpenTelemetry: 분산 추적

4. **Phase 4 (장기, 6개월+)**:
   - Discourse: 커뮤니티 플랫폼
   - Pachyderm: 대규모 데이터 관리
   - Prometheus: 장기 모니터링

#### 통합 원칙

1. **어댑터 패턴 유지**: 모든 외부 도구는 어댑터를 통해 통합
2. **선택적 의존성**: 사용자가 필요한 도구만 설치
3. **표준 인터페이스**: 포트 인터페이스를 통한 일관된 통합
4. **문서화**: 각 통합에 대한 상세한 문서 제공

---

## 우선순위 로드맵

### Phase 8: 도메인 확장 (1-2개월)
**목표**: Insurance 외 1-2개 도메인 지원

- [ ] Legal 도메인 메트릭 및 엔티티 추출기
- [ ] Medical 도메인 메트릭 및 엔티티 추출기
- [ ] 도메인별 프리셋 시스템
- [ ] 도메인 전환 CLI 옵션

**오픈소스 통합**:
- **spaCy**: 도메인별 커스텀 NER 모델 학습 및 엔티티 추출
- **Phoenix**: 도메인별 평가 메트릭 확장
- **DeepEval**: 도메인 특화 평가 메트릭 라이브러리 활용

**성공 지표**:
- 2개 이상 도메인 지원
- 도메인별 10개 이상 테스트 케이스 생성 가능

---

### Phase 9: CI/CD 통합 (1개월)
**목표**: 개발 워크플로우에 자연스럽게 통합

- [ ] GitHub Actions 통합
- [ ] GitLab CI 통합
- [ ] PR 자동 평가
- [ ] 임계값 미달 시 PR 차단

**오픈소스 통합**:
- **GitHub Actions**: PR 자동 평가 워크플로우
- **Pre-commit**: 커밋 전 데이터셋 검증
- **DVC**: 평가 결과 버전 관리

**성공 지표**:
- GitHub Actions에서 실행 가능
- PR마다 자동 평가 실행

---

### Phase 10: 인사이트 엔진 (2개월)
**목표**: 평가 결과를 넘어선 액션 가능한 인사이트

- [ ] 실패 케이스 자동 분석
- [ ] 메트릭 간 상관관계 분석
- [ ] 데이터셋 품질 분석
- [ ] 모델 비교 및 추천

**오픈소스 통합**:
- **Apache Superset**: 평가 결과 대시보드 및 시각화
- **Grafana**: 실시간 메트릭 모니터링 및 알림
- **Great Expectations**: 데이터셋 품질 검증 및 드리프트 감지
- **Weights & Biases**: 실험 추적 및 모델 비교

**성공 지표**:
- 실패 케이스 분석 정확도 80% 이상
- 사용자 만족도 향상 (설문 기반)

---

### Phase 11: KG 고도화 (2-3개월)
**목표**: KG를 평가 인프라로 진화

- [ ] KG 기반 평가 메트릭
- [ ] KG 기반 자동 테스트셋 보완
- [ ] KG 불일치 감지
- [ ] KG 통계 및 분석 CLI

**오픈소스 통합**:
- **Neo4j**: KG 영구 저장 및 고급 쿼리
- **NetworkX**: 그래프 알고리즘 활용 (이미 사용 중, 고도화)
- **spaCy**: 관계 추출 정확도 향상

**성공 지표**:
- KG 기반 평가 메트릭 3개 이상
- KG 커버리지 기반 테스트셋 보완 정확도 70% 이상

---

### Phase 12: 파이프라인 오케스트레이션 (1-2개월)
**목표**: 복잡한 평가 워크플로우 쉽게 구성

- [ ] YAML 기반 파이프라인 정의
- [ ] 파이프라인 실행 엔진
- [ ] 통합 리포트 생성
- [ ] 파이프라인 시각화

**오픈소스 통합**:
- **Apache Airflow** 또는 **Prefect**: 파이프라인 오케스트레이션
- **DVC**: 데이터 및 파이프라인 버전 관리
- **OpenTelemetry**: 분산 추적 및 관찰성

**성공 지표**:
- 5개 이상 파이프라인 예제 제공
- 파이프라인 실행 시간 30% 단축

---

## 핵심 메시지 재정의

### 현재
> "RAGAS를 쉽게 실행하는 도구"

### 목표
> "도메인 특화 RAG 평가 플랫폼 - 평가부터 인사이트까지"

### 차별화 포인트
1. **도메인 특화**: Insurance, Legal, Medical 등 도메인별 메트릭 및 도구
2. **자동화**: CI/CD 통합, 자동 평가 파이프라인
3. **인사이트**: 평가 결과를 넘어선 액션 가능한 인사이트
4. **KG 기반**: Knowledge Graph를 활용한 고급 평가 및 테스트셋 생성
5. **생태계**: 커뮤니티 프리셋, 데이터셋 공유, 플러그인 시스템

---

## 참고 자료

### 내부 문서
- [KG Improvement Plan](./KG_IMPROVEMENT_PLAN.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Roadmap](./ROADMAP.md)

### 오픈소스 도구 공식 문서
- [Phoenix (Arize AI)](https://github.com/Arize-ai/phoenix)
- [DeepEval (Confident AI)](https://github.com/confident-ai/deepeval)
- [Promptfoo](https://github.com/promptfoo/promptfoo)
- [Apache Superset](https://github.com/apache/superset)
- [Grafana](https://github.com/grafana/grafana)
- [Great Expectations](https://github.com/great-expectations/great-expectations)
- [spaCy](https://github.com/explosion/spaCy)
- [Neo4j](https://github.com/neo4j/neo4j)
- [NetworkX](https://github.com/networkx/networkx)
- [Apache Airflow](https://github.com/apache/airflow)
- [Prefect](https://github.com/PrefectHQ/prefect)
- [DVC](https://github.com/iterative/dvc)
- [OpenTelemetry](https://github.com/open-telemetry/opentelemetry-python)
- [Prometheus](https://github.com/prometheus/prometheus)
- [Weights & Biases](https://github.com/wandb/wandb)
