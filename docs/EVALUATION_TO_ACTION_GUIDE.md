# Evaluation-to-Action Guide

EvalVault의 핵심 가치 재정의와 RAG 시스템 개선을 위한 전략 가이드입니다.

## 목차

1. [문제 진단](#문제-진단)
2. [핵심 가치 재정의](#핵심-가치-재정의)
3. [Actionable Insight Generator](#actionable-insight-generator)
4. [메트릭별 개선 플레이북](#메트릭별-개선-플레이북)
5. [증거 기반 분석 리포트](#증거-기반-분석-리포트)
6. [CI/CD 통합](#cicd-통합)
7. [구현 우선순위](#구현-우선순위)

---

## 문제 진단

### 외부 비판 요약

| 비판 포인트 | 상세 내용 |
|------------|----------|
| "RAGAS 래퍼" 인식 | 핵심 차별화 가치가 불명확 |
| 실질적 도움 부족 | 평가 점수만 제공, 개선 방법 부재 |
| CI/CD 통합 부족 | 자동화 예제 미제공 |
| 도메인 특화 한계 | 보험 외 도메인 확장 어려움 |
| 학습 곡선 | 기능이 많아 빠른 시작 어려움 |

### 핵심 문제

**"평가 점수 → RAG 시스템 개선"으로의 연결고리 부재**

```
현재 상태:
  평가 → 점수 → ???

목표 상태:
  평가 → 점수 → 원인 분석 → 개선 액션 → 증거 데이터 → 재평가
```

RAG 구축자가 원하는 것:
- "faithfulness가 0.65인데, 어떻게 0.8로 올리죠?"
- "context_precision이 낮은 이유가 뭔가요?"
- "이 개선이 효과가 있다는 증거가 있나요?"

---

## 핵심 가치 재정의

### 현재 vs 제안

| 현재 | 제안 |
|-----|------|
| "RAGAS 래퍼 + 분석 도구" | "RAG 개선을 위한 증거 기반 의사결정 플랫폼" |

### 메시지 전환

| 기존 메시지 | 새로운 메시지 |
|------------|-------------|
| "RAGAS 메트릭을 평가합니다" | "낮은 점수의 근본 원인을 찾고 개선 방법을 제시합니다" |
| "Langfuse에 점수를 기록합니다" | "개선 전/후 효과를 증거 데이터로 증명합니다" |
| "인과 분석을 수행합니다" | "구체적인 RAG 파이프라인 수정 가이드를 생성합니다" |

### 차별화 포지셔닝

```
RAGAS:      점수
EvalVault:  점수 + 왜 낮은지 + 어떻게 고치는지 + 고친 후 효과 증명
```

---

## Actionable Insight Generator

### 새로운 엔티티 설계

현재 `InterventionSuggestion`이 있지만 추상적입니다. 구체적인 RAG 컴포넌트별 개선 가이드가 필요합니다.

#### RAGImprovementGuide

```python
@dataclass
class RAGImprovementGuide:
    """RAG 파이프라인 개선 가이드."""

    # 영향받는 컴포넌트
    component: Literal["retriever", "reranker", "generator", "chunker", "embedder"]

    # 구체적 개선 액션
    action: str  # "chunk_size 512→256 감소", "top_k 3→5 증가"

    # 증거 데이터
    evidence: ImprovementEvidence

    # 예상 개선폭
    expected_improvement: float  # 0.05 = 5% 개선 예상

    # 관련 테스트 케이스
    affected_test_cases: list[str]

    # 우선순위 (ROI 기반)
    priority: int  # 1=높음 (적은 노력, 큰 효과)
```

#### ImprovementEvidence

```python
@dataclass
class ImprovementEvidence:
    """개선 제안의 증거 데이터."""

    # 문제 패턴
    pattern_name: str  # "long_query_low_precision"

    # 해당 케이스 수
    affected_count: int
    total_count: int

    # 통계적 근거
    correlation: float
    p_value: float

    # 대표 실패 사례
    representative_failures: list[FailureSample]

    # 유사 시스템 벤치마크 (선택)
    benchmark_reference: str | None
```

#### FailureSample

```python
@dataclass
class FailureSample:
    """실패 사례 샘플."""

    test_case_id: str
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None

    # 실패 분석
    failure_reason: str
    metric_scores: dict[str, float]

    # 개선 방향
    suggested_context: str | None  # 이런 컨텍스트가 있었다면...
    suggested_answer: str | None   # 이렇게 답했어야...
```

### 컴포넌트-메트릭 매핑

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Retriever    │────▶│ context_recall  │     │  top_k 증가     │
│                 │────▶│context_precision│     │  reranker 추가  │
└─────────────────┘     └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Generator    │────▶│  faithfulness   │     │ temperature ↓   │
│                 │────▶│answer_relevancy │     │ 프롬프트 개선   │
└─────────────────┘     └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Chunker      │────▶│context_precision│     │ chunk_size ↓    │
│                 │────▶│ context_recall  │     │ overlap 조정    │
└─────────────────┘     └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Embedder     │────▶│context_precision│     │ 모델 교체       │
│                 │────▶│ context_recall  │     │ 파인튜닝        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 메트릭별 개선 플레이북

각 RAGAS 메트릭이 낮을 때 어떤 RAG 컴포넌트를 수정해야 하는지 명확한 가이드입니다.

### Faithfulness (충실도)

답변이 컨텍스트에 얼마나 충실한지 평가합니다.

#### 낮은 점수 원인

| 원인 | 설명 | 증거 확인 방법 |
|-----|------|--------------|
| retriever_missing_evidence | 검색된 컨텍스트에 답변의 근거가 없음 | `answer_claim_in_context_ratio < 0.5` |
| generator_hallucination | LLM이 컨텍스트에 없는 내용 생성 | `context_contains_answer but faithfulness < 0.7` |
| context_noise | 관련 없는 컨텍스트가 LLM을 혼란시킴 | `context_count > 5 and precision < 0.5` |

#### 개선 액션

```yaml
faithfulness:
  cause: retriever_missing_evidence
  actions:
    - action: "top_k 증가"
      detail: "3 → 5 → 10으로 점진적 증가"
      expected_improvement: "+5~10%"
      effort: "low"

    - action: "Reranker 도입"
      detail: "Cross-encoder (ms-marco-MiniLM) 추가"
      expected_improvement: "+10~15%"
      effort: "medium"

  cause: generator_hallucination
  actions:
    - action: "Temperature 감소"
      detail: "0.7 → 0.3 또는 0.0"
      expected_improvement: "+5~10%"
      effort: "low"

    - action: "프롬프트 강화"
      detail: "'컨텍스트에 있는 정보만 사용하세요' 명시"
      expected_improvement: "+10~20%"
      effort: "low"

    - action: "Citation 요구"
      detail: "답변에 출처 표시 요구"
      expected_improvement: "+15~25%"
      effort: "medium"
```

### Context Precision (컨텍스트 정밀도)

검색된 컨텍스트 중 관련 있는 비율입니다.

#### 낮은 점수 원인

| 원인 | 설명 | 증거 확인 방법 |
|-----|------|--------------|
| chunking_too_large | 청크가 커서 불필요한 정보 포함 | `avg_context_length > 1000 and precision < 0.6` |
| embedding_mismatch | 질문과 컨텍스트의 임베딩 유사도 낮음 | `keyword_overlap > 0.5 but semantic_similarity < 0.4` |
| query_complexity | 복합 질문에 대한 검색 실패 | `question_length > 50 and precision < 0.5` |

#### 개선 액션

```yaml
context_precision:
  cause: chunking_too_large
  actions:
    - action: "Chunk size 감소"
      detail: "512 → 256 토큰"
      expected_improvement: "+10~15%"
      effort: "low"

    - action: "Semantic chunking 도입"
      detail: "문장/문단 경계 기반 분할"
      expected_improvement: "+15~20%"
      effort: "medium"

  cause: embedding_mismatch
  actions:
    - action: "임베딩 모델 교체"
      detail: "범용 → 도메인 특화 모델"
      expected_improvement: "+10~20%"
      effort: "high"

    - action: "Hybrid search 도입"
      detail: "Dense + BM25 결합"
      expected_improvement: "+15~25%"
      effort: "medium"

  cause: query_complexity
  actions:
    - action: "Query decomposition"
      detail: "복합 질문을 단순 질문으로 분해"
      expected_improvement: "+15~25%"
      effort: "medium"

    - action: "HyDE (Hypothetical Document Embedding)"
      detail: "가상 답변 생성 후 검색"
      expected_improvement: "+10~15%"
      effort: "medium"
```

### Context Recall (컨텍스트 재현율)

필요한 정보가 검색되었는지 평가합니다.

#### 낮은 점수 원인

| 원인 | 설명 | 증거 확인 방법 |
|-----|------|--------------|
| retriever_k_too_small | top_k가 작아 필요한 정보 누락 | `ground_truth_keywords not in retrieved_contexts` |
| index_coverage_gap | 인덱스에 관련 문서 누락 | `question_entity not in any context` |
| embedding_blind_spot | 특정 유형 질문에 임베딩 취약 | `question_type == 'procedural' and recall < 0.5` |

#### 개선 액션

```yaml
context_recall:
  cause: retriever_k_too_small
  actions:
    - action: "top_k 증가"
      detail: "3 → 5 → 10"
      expected_improvement: "+10~20%"
      effort: "low"

    - action: "Multi-query retrieval"
      detail: "질문 변형 생성 후 다중 검색"
      expected_improvement: "+15~25%"
      effort: "medium"

  cause: index_coverage_gap
  actions:
    - action: "문서 커버리지 분석"
      detail: "누락된 주제 영역 식별"
      expected_improvement: "varies"
      effort: "high"

    - action: "문서 추가 인덱싱"
      detail: "식별된 갭 영역 문서 추가"
      expected_improvement: "+20~40%"
      effort: "high"
```

### Answer Relevancy (답변 관련성)

답변이 질문에 얼마나 관련 있는지 평가합니다.

#### 낮은 점수 원인

| 원인 | 설명 | 증거 확인 방법 |
|-----|------|--------------|
| off_topic_response | 질문과 무관한 답변 생성 | `question_answer_similarity < 0.5` |
| incomplete_answer | 질문의 일부만 답변 | `multi_part_question and answer_coverage < 0.7` |
| verbose_response | 불필요하게 긴 답변 | `answer_length > 500 and relevancy < 0.7` |

#### 개선 액션

```yaml
answer_relevancy:
  cause: off_topic_response
  actions:
    - action: "프롬프트에 질문 재강조"
      detail: "답변 전 질문 반복 요구"
      expected_improvement: "+10~15%"
      effort: "low"

    - action: "Few-shot 예제 추가"
      detail: "좋은 답변 예시 제공"
      expected_improvement: "+15~20%"
      effort: "low"

  cause: incomplete_answer
  actions:
    - action: "질문 분해 요구"
      detail: "각 하위 질문에 순서대로 답변"
      expected_improvement: "+15~25%"
      effort: "low"

    - action: "Chain-of-thought 유도"
      detail: "단계별 추론 요구"
      expected_improvement: "+10~20%"
      effort: "low"
```

---

## 증거 기반 분석 리포트

### 리포트 구조

현재 리포트가 추상적입니다. 다음과 같은 구체적인 증거 데이터를 포함해야 합니다.

````markdown
# RAG 개선 가이드 리포트

## 요약
- 평가 테스트 케이스: 100개
- 전체 통과율: 65%
- 핵심 문제: Context Precision (평균 0.52)

---

## 1. Context Precision 개선 (우선순위: 높음)

### 문제 패턴
- **긴 질문 + 낮은 정밀도**: 50자 이상 질문의 정밀도 평균 0.41
- 상관계수: r=-0.42, p<0.001

### 증거 데이터

| 테스트 케이스 | 질문 길이 | context_precision | 원인 |
|-------------|----------|-------------------|------|
| tc-023 | 78자 | 0.32 | 복합 질문, 청크 경계 문제 |
| tc-045 | 65자 | 0.38 | 키워드 분산, 멀티홉 필요 |
| tc-067 | 92자 | 0.28 | 추론형 질문, 직접 매칭 실패 |

### 대표 실패 사례

```
질문: "자동차 보험에서 자기부담금이 적용되지 않는 경우와
       면책 사유에 해당하는 경우의 차이점은?"

검색된 컨텍스트:
  [1] "자기부담금은 보험금 지급 시..." (관련도: 높음 ✓)
  [2] "자동차 보험 가입 절차는..." (관련도: 낮음 ✗)
  [3] "보험료 산정 기준..." (관련도: 낮음 ✗)

문제: 3개 중 1개만 관련 → precision = 0.33
누락: "면책 사유" 관련 컨텍스트 미검색
```

### 개선 액션

#### 액션 1: Query Decomposition 도입 (예상 개선: +15%)

복합 질문을 단순 질문으로 분해하여 각각 검색합니다.

```
원본: "자기부담금이 적용되지 않는 경우와 면책 사유의 차이점은?"

분해:
  Q1: "자기부담금이 적용되지 않는 경우는?"
  Q2: "면책 사유에 해당하는 경우는?"
  Q3: "자기부담금 미적용과 면책의 차이점은?"
```

#### 액션 2: Reranker 추가 (예상 개선: +10%)

Cross-encoder로 검색 결과를 재정렬합니다.

```python
# 구현 예시
from sentence_transformers import CrossEncoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# 검색 후 재정렬
scores = reranker.predict([(query, doc) for doc in retrieved_docs])
reranked_docs = [doc for _, doc in sorted(zip(scores, retrieved_docs), reverse=True)]
```

#### 액션 3: top_k 증가 (예상 개선: +5%)

검색 개수를 늘린 후 reranker로 필터링합니다.

```
현재: top_k=3
권장: top_k=10 → reranker → top_k=3
```

### 검증 방법

```bash
# 개선 전 baseline 저장
evalvault run test_data.json \
  --metrics context_precision \
  --tag "baseline"

# 개선 후 재평가
evalvault run test_data.json \
  --metrics context_precision \
  --tag "after_reranker"

# 효과 비교
evalvault compare baseline after_reranker \
  --metrics context_precision
```

---

## 2. Faithfulness 개선 (우선순위: 중간)

### 문제 패턴
- **hallucination 패턴**: 컨텍스트에 없는 수치/날짜 생성
- 영향 케이스: 23개 (23%)

### 증거 데이터

| 유형 | 빈도 | 예시 |
|-----|------|------|
| 수치 hallucination | 12건 | "보장금액 5천만원" (실제: 3천만원) |
| 날짜 hallucination | 7건 | "2024년 1월부터" (컨텍스트에 없음) |
| 조건 hallucination | 4건 | "60세 이상 가입 불가" (실제: 제한 없음) |

### 개선 액션

#### 액션 1: Temperature 감소 (예상 개선: +8%)

```python
# 현재
llm = ChatOpenAI(temperature=0.7)

# 권장
llm = ChatOpenAI(temperature=0.0)  # 결정적 출력
```

#### 액션 2: 프롬프트 강화 (예상 개선: +12%)

```
현재 프롬프트:
"다음 컨텍스트를 참고하여 질문에 답하세요."

강화된 프롬프트:
"다음 컨텍스트에 있는 정보만 사용하여 답변하세요.
컨텍스트에 없는 정보는 '해당 정보를 찾을 수 없습니다'라고 답하세요.
수치, 날짜, 조건은 반드시 컨텍스트에서 인용하세요."
```

---

## 부록: 전체 메트릭 요약

| 메트릭 | 평균 | 목표 | 갭 | 우선순위 |
|-------|-----|-----|-----|---------|
| faithfulness | 0.72 | 0.85 | -0.13 | P1 |
| answer_relevancy | 0.78 | 0.80 | -0.02 | P2 |
| context_precision | 0.52 | 0.75 | -0.23 | P0 |
| context_recall | 0.68 | 0.80 | -0.12 | P1 |

---

*Generated by EvalVault v0.x.x*
````

---

## CI/CD 통합

### GitHub Actions 템플릿

#### 기본 평가 워크플로우

```yaml
# .github/workflows/rag-evaluation.yml
name: RAG Quality Gate

on:
  pull_request:
    paths:
      - 'src/retriever/**'
      - 'src/generator/**'
      - 'prompts/**'
      - 'config/rag_config.yaml'

env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
  LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install EvalVault
        run: |
          pip install evalvault

      - name: Run RAG Evaluation
        run: |
          evalvault run tests/eval_dataset.json \
            --metrics faithfulness,context_precision,context_recall,answer_relevancy \
            --output results.json

      - name: Quality Gate Check
        id: gate
        run: |
          evalvault gate results.json \
            --threshold faithfulness:0.8 \
            --threshold context_precision:0.7 \
            --threshold context_recall:0.7 \
            --threshold answer_relevancy:0.75 \
            --fail-on-regression 0.05

      - name: Generate Improvement Report
        if: failure()
        run: |
          evalvault analyze results.json \
            --include-causal \
            --include-playbook \
            --format markdown \
            --output improvement_guide.md

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: |
            results.json
            improvement_guide.md

      - name: Comment PR with Results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            let body = '## RAG Evaluation Results\n\n';

            try {
              const results = JSON.parse(fs.readFileSync('results.json', 'utf8'));
              body += '| Metric | Score | Threshold | Status |\n';
              body += '|--------|-------|-----------|--------|\n';

              for (const [metric, score] of Object.entries(results.metrics)) {
                const threshold = results.thresholds[metric] || 0.7;
                const status = score >= threshold ? ':white_check_mark:' : ':x:';
                body += `| ${metric} | ${score.toFixed(3)} | ${threshold} | ${status} |\n`;
              }
            } catch (e) {
              body += 'Failed to parse results.\n';
            }

            if (fs.existsSync('improvement_guide.md')) {
              const guide = fs.readFileSync('improvement_guide.md', 'utf8');
              body += '\n\n<details><summary>Improvement Guide</summary>\n\n';
              body += guide;
              body += '\n\n</details>';
            }

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body
            });
```

#### Regression 감지 워크플로우

```yaml
# .github/workflows/rag-regression.yml
name: RAG Regression Detection

on:
  push:
    branches: [main]

jobs:
  baseline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Evaluation
        run: |
          evalvault run tests/eval_dataset.json \
            --metrics faithfulness,context_precision \
            --output baseline.json

      - name: Compare with Previous
        run: |
          # 이전 baseline 다운로드
          gh run download -n baseline-results || true

          if [ -f previous_baseline.json ]; then
            evalvault compare previous_baseline.json baseline.json \
              --alert-on-regression 0.03 \
              --output comparison.json
          fi

      - name: Upload New Baseline
        uses: actions/upload-artifact@v4
        with:
          name: baseline-results
          path: baseline.json

      - name: Alert on Regression
        if: failure()
        run: |
          # Slack/Discord 알림
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -H 'Content-Type: application/json' \
            -d '{"text": "RAG Quality Regression Detected!"}'
```

### CLI 명령어 (신규)

```bash
# Quality gate 체크
evalvault gate results.json \
  --threshold faithfulness:0.8 \
  --threshold context_precision:0.7 \
  --fail-on-regression 0.05

# 분석 + 플레이북 포함 리포트
evalvault analyze results.json \
  --include-causal \
  --include-playbook \
  --format markdown

# 두 평가 결과 비교
evalvault compare baseline.json current.json \
  --alert-on-regression 0.03
```

---

## 구현 우선순위

### P0: 핵심 가치 제안의 기반 (최우선)

| 항목 | 설명 | 예상 효과 |
|-----|------|----------|
| RAGImprovementGuide 엔티티 | 개선 가이드의 데이터 구조 | 구조화된 개선 제안 |
| ImprovementEvidence 엔티티 | 증거 데이터 구조 | 신뢰성 있는 제안 |
| 메트릭별 플레이북 YAML | 즉시 사용 가능한 가이드 | 빠른 개선 적용 |
| FailureSample 엔티티 | 실패 사례 구조화 | 문제 이해 용이 |

### P1: 사용자 경험 개선 (단기)

| 항목 | 설명 | 예상 효과 |
|-----|------|----------|
| 증거 기반 리포트 생성기 | 마크다운 리포트 자동 생성 | 즉각적인 가치 제공 |
| CI/CD 템플릿 | GitHub Actions 예제 | 자동화 요구 충족 |
| `evalvault gate` 명령 | 품질 게이트 CLI | 파이프라인 통합 |
| `evalvault analyze --playbook` | 플레이북 포함 분석 | 액션 가능한 인사이트 |

### P2: 확장성 (중기)

| 항목 | 설명 | 예상 효과 |
|-----|------|----------|
| 개선 전/후 비교 대시보드 | 효과 시각화 | 효과 증명 |
| 도메인 확장 (법률, 의료) | 플레이북 확장 | 범용성 확보 |
| Slack/Discord 알림 | 리그레션 알림 | 운영 편의성 |
| 벤치마크 데이터셋 | 산업별 기준 데이터 | 객관적 비교 |

### P3: 고급 기능 (장기)

| 항목 | 설명 | 예상 효과 |
|-----|------|----------|
| 자동 개선 제안 실행 | A/B 테스트 자동화 | 완전 자동화 |
| RAG 컴포넌트 자동 튜닝 | 파라미터 최적화 | 최적 설정 탐색 |
| 멀티 벤더 통합 | LlamaIndex, LangChain 연동 | 생태계 확장 |

---

## 예상 효과

### 비판 해소

| 비판 | 해소 방안 |
|-----|----------|
| "RAGAS 래퍼" | RAGAS + 원인 분석 + 개선 가이드 + 증거 데이터 |
| "핵심 가치 불명확" | "낮은 점수를 받으면 어떻게 고쳐야 하는지 알려줌" |
| "CI/CD 통합 부족" | GitHub Actions 템플릿 + gate 명령 |
| "실제 도움 부족" | 컴포넌트별 구체적 개선 액션 제공 |

### 사용자 시나리오 개선

**현재:**
```
사용자: evalvault run data.json
결과: faithfulness=0.65, context_precision=0.52
사용자: "그래서 뭘 어쩌라고...?"
```

**개선 후:**
```
사용자: evalvault run data.json --analyze
결과:
  - faithfulness: 0.65 (목표 0.80)
  - context_precision: 0.52 (목표 0.75)

  [개선 가이드]
  1. Context Precision 개선 (우선순위: P0)
     - 원인: 긴 질문 + 청크 경계 문제
     - 증거: 50자 이상 질문 23건 중 18건 실패 (r=-0.42)
     - 액션: Query decomposition 도입 (예상 +15%)
     - 검증: evalvault compare baseline after_fix
```

---

## 참고 문서

- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처
- [STRATEGIC_DIRECTION.md](STRATEGIC_DIRECTION.md) - 전략적 방향
- [ROADMAP.md](ROADMAP.md) - 개발 로드맵
- [USER_GUIDE.md](USER_GUIDE.md) - 사용자 가이드
