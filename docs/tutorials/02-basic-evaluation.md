# 기본 평가 실행 가이드

> 데이터셋 형식, 지원 메트릭, CLI 옵션을 상세히 이해하고 평가를 실행합니다.

---

## 목차

1. [데이터셋 형식](#데이터셋-형식)
2. [지원 메트릭](#지원-메트릭)
3. [CLI 옵션](#cli-옵션)
4. [평가 실행 예제](#평가-실행-예제)
5. [결과 분석](#결과-분석)

---

## 데이터셋 형식

EvalVault는 세 가지 데이터 형식을 지원합니다.

### JSON 형식 (권장)

JSON은 메타데이터와 임계값(thresholds)을 직관적으로 포함할 수 있어 가장 권장됩니다. CSV/Excel도
`threshold_*` 컬럼으로 임계값을 추가할 수 있습니다.

```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7,
    "context_precision": 0.7,
    "context_recall": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "이 보험의 보장금액은 얼마인가요?",
      "answer": "보장금액은 1억원입니다.",
      "contexts": [
        "해당 보험의 사망 보장금액은 1억원입니다.",
        "보험료 납입기간은 20년입니다."
      ],
      "ground_truth": "1억원"
    },
    {
      "id": "tc-002",
      "question": "보험료 납입기간은 얼마인가요?",
      "answer": "납입기간은 20년입니다.",
      "contexts": [
        "보험료 납입기간은 20년입니다."
      ],
      "ground_truth": "20년"
    }
  ]
}
```

> threshold는 데이터셋별 pass 기준입니다. 값이 없으면 기본값 `0.7`을 사용합니다.

**필드 설명**:

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 선택 | 데이터셋 이름 |
| `version` | 선택 | 데이터셋 버전 |
| `thresholds` | 선택 | 메트릭별 통과 기준 (0.0~1.0), 데이터셋별/기본값 0.7 |
| `test_cases` | 필수 | 테스트 케이스 배열 |

**테스트 케이스 필드**:

| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | 필수 | 테스트케이스 고유 ID |
| `question` | 필수 | 사용자 질문 |
| `answer` | 필수 | RAG 시스템의 답변 |
| `contexts` | 필수 | 검색된 컨텍스트 배열 |
| `ground_truth` | 조건부 | 정답 (일부 메트릭에 필요) |

### CSV 형식

스프레드시트에서 간편하게 편집할 수 있습니다.

```csv
id,question,answer,contexts,ground_truth,threshold_faithfulness,threshold_answer_relevancy,threshold_context_precision,threshold_context_recall,threshold_factual_correctness,threshold_semantic_similarity
tc-001,"보장금액은?","1억원입니다.","[""사망 보장금액은 1억원""]","1억원",0.8,0.7,,,,
tc-002,"납입기간은?","20년입니다.","[""납입기간은 20년""]","20년",,,,,,
```

**주의**: `contexts` 필드는 JSON 배열 문자열 또는 `|` 구분 문자열을 사용합니다.
`threshold_*`는 첫 번째로 채워진 행을 데이터셋 임계값으로 사용합니다.

### Excel 형식

`.xlsx` 파일을 직접 사용할 수 있습니다.

| id | question | answer | contexts | ground_truth | threshold_faithfulness | threshold_answer_relevancy |
|----|----------|--------|----------|--------------|------------------------|----------------------------|
| tc-001 | 보장금액은? | 1억원입니다. | ["사망 보장금액은 1억원"] | 1억원 | 0.8 | 0.7 |

`threshold_*` 값은 첫 번째로 채워진 행 기준으로 데이터셋 임계값으로 사용합니다.
`contexts`는 JSON 배열 문자열 또는 `|` 구분 문자열을 사용할 수 있습니다.

---

## 지원 메트릭

EvalVault는 [Ragas](https://docs.ragas.io/) 프레임워크 기반의 6가지 메트릭을 제공합니다.

### 메트릭 요약

| 메트릭 | 측정 대상 | Ground Truth 필요 | 임베딩 필요 |
|--------|-----------|-------------------|-------------|
| `faithfulness` | 답변이 컨텍스트에 충실한지 | No | No |
| `answer_relevancy` | 답변이 질문과 관련있는지 | No | Yes |
| `context_precision` | 검색된 컨텍스트의 정밀도 | Yes | No |
| `context_recall` | 필요한 정보가 검색되었는지 | Yes | No |
| `factual_correctness` | 답변이 정답과 일치하는지 | Yes | No |
| `semantic_similarity` | 답변과 정답의 의미적 유사도 | Yes | Yes |

> 커스텀 메트릭(예: `insurance_term_accuracy`)은 [03-custom-metrics.md](03-custom-metrics.md)에서 다룹니다.

### 메트릭 상세 설명

#### Faithfulness (충실도)

**질문**: "답변이 검색된 컨텍스트에서 벗어나지 않았는가?"

- 점수 1.0: 답변의 모든 주장이 컨텍스트에서 지원됨
- 점수 0.0: 답변이 컨텍스트에 없는 내용을 포함 (환각)

**사용 시기**: 환각(Hallucination) 감지가 필요할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness --db evalvault.db
```

#### Answer Relevancy (답변 관련성)

**질문**: "답변이 질문에 적절히 대응하는가?"

- 점수 1.0: 답변이 질문과 완벽하게 관련됨
- 점수 0.0: 답변이 질문과 무관함

**사용 시기**: 답변 품질과 주제 이탈 감지가 필요할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics answer_relevancy --db evalvault.db
```

#### Context Precision (컨텍스트 정밀도)

**질문**: "검색된 컨텍스트 중 실제로 유용한 것의 비율은?"

- 점수 1.0: 모든 검색 결과가 유용함
- 점수 0.0: 검색 결과가 모두 노이즈

**사용 시기**: Retriever 정밀도 평가가 필요할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics context_precision --db evalvault.db
```

#### Context Recall (컨텍스트 재현율)

**질문**: "정답을 도출하는데 필요한 정보가 모두 검색되었는가?"

- 점수 1.0: 필요한 모든 정보가 검색됨
- 점수 0.0: 필요한 정보가 누락됨

**사용 시기**: Retriever 커버리지 평가가 필요할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics context_recall --db evalvault.db
```

#### Factual Correctness (사실적 정확성)

**질문**: "답변의 사실적 주장이 정답과 일치하는가?"

- 점수 1.0: 모든 사실이 정확함
- 점수 0.0: 사실적 오류 포함

**사용 시기**: 사실 검증이 필요할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics factual_correctness --db evalvault.db
```

#### Semantic Similarity (의미적 유사도)

**질문**: "답변과 정답이 의미적으로 얼마나 유사한가?"

- 점수 1.0: 의미가 동일함
- 점수 0.0: 의미가 완전히 다름

**사용 시기**: 다양한 표현을 허용하면서 답변 품질을 평가할 때

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics semantic_similarity --db evalvault.db
```

### 메트릭 선택 가이드

| 목적 | 권장 메트릭 |
|------|-------------|
| 빠른 평가 | `faithfulness` |
| Retriever 성능 평가 | `context_precision`, `context_recall` |
| 답변 품질 종합 평가 | `answer_relevancy`, `semantic_similarity` |
| 정확도 중심 평가 | `factual_correctness` |
| 전체 파이프라인 평가 | 모든 메트릭 |

---

## CLI 옵션

### 기본 명령어

```bash
uv run evalvault run <dataset_path> --metrics <metrics> --db evalvault.db
```

### 옵션 상세

| 옵션 | 단축 | 설명 | 예시 |
|------|------|------|------|
| `--metrics` | `-m` | 평가할 메트릭 (쉼표 구분) | `--metrics faithfulness,answer_relevancy` |
| `--profile` | `-p` | 모델 프로필 선택 | `--profile dev` |
| `--parallel` | | 병렬 평가 활성화 | `--parallel` |
| `--batch-size` | | 병렬 배치 크기 | `--batch-size 10` |
| `--tracker` | | 추적 백엔드 선택 | `--tracker langfuse` |
| `--verbose` | `-v` | 상세 로그 출력 | `--verbose` |

### 사용 가능한 메트릭 확인

```bash
uv run evalvault metrics
```

출력 예시:
```
Available Metrics:
==================
- faithfulness: 답변이 컨텍스트에 충실한지 평가
- answer_relevancy: 답변이 질문과 관련있는지 평가
- context_precision: 검색된 컨텍스트의 정밀도 평가
- context_recall: 필요한 정보가 검색되었는지 평가
- factual_correctness: 답변이 정답과 일치하는지 평가
- semantic_similarity: 답변과 정답의 의미적 유사도 평가
```

---

## 평가 실행 예제

### 단일 메트릭 평가

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness --db evalvault.db
```

### 여러 메트릭 동시 평가

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness,answer_relevancy,context_precision --db evalvault.db
```

### 모든 메트릭 평가

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness,answer_relevancy,context_precision,context_recall,factual_correctness,semantic_similarity --db evalvault.db
```

### 병렬 평가 (대규모 데이터셋)

```bash
LARGE_DATASET="scripts/perf/r3_evalvault_run_dataset.json"
uv run evalvault run "$LARGE_DATASET" --metrics faithfulness --parallel --batch-size 10 --db evalvault.db
```

### 프로필 지정

```bash
# Ollama (dev 환경)
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --profile dev --metrics faithfulness --db evalvault.db

# OpenAI
uv run evalvault run "$DATASET" --profile openai --metrics faithfulness --db evalvault.db
```

### Langfuse 추적 활성화

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness --tracker langfuse --db evalvault.db
```

---

## 결과 분석

### 히스토리 조회

```bash
uv run evalvault history --limit 10 --db evalvault.db
```

출력 예시:
```
Evaluation History
==================
ID                                    Dataset              Metrics                 Pass Rate   Date
------------------------------------  -------------------  ----------------------  ----------  -------------------
abc123...                             insurance-qa         faithfulness            100%        2025-01-01 10:00:00
def456...                             insurance-qa         faithfulness,answer_... 80%         2025-01-01 09:00:00
```

### 결과 비교

```bash
uv run evalvault compare <id1> <id2> --db evalvault.db
```

출력 예시:
```
Comparison: abc123 vs def456
============================
                    Run 1      Run 2      Diff
faithfulness        0.85       0.92       +0.07
answer_relevancy    0.78       0.81       +0.03
context_precision   0.90       0.88       -0.02
```

### 결과 내보내기

```bash
uv run evalvault export <run_id> -o results.json --db evalvault.db
```

내보낸 JSON 구조:
```json
{
  "run_id": "abc123-def456-...",
  "dataset_name": "insurance-qa",
  "created_at": "2025-01-01T10:00:00Z",
  "pass_rate": 0.8,
  "metrics": {
    "faithfulness": 0.92,
    "answer_relevancy": 0.85
  },
  "results": [
    {
      "test_case_id": "tc-001",
      "scores": {
        "faithfulness": 0.95
      },
      "passed": true
    }
  ]
}
```

---

## 다음 단계

| 주제 | 튜토리얼 |
|------|----------|
| 커스텀 메트릭 만들기 | [03-custom-metrics.md](03-custom-metrics.md) |
| Phoenix 연동하기 | [04-phoenix-integration.md](04-phoenix-integration.md) |
| 한국어 RAG 최적화 | [05-korean-rag.md](05-korean-rag.md) |
| 프로덕션 배포 가이드 | [06-production-tips.md](06-production-tips.md) |

---

<div align="center">

[이전: 빠른 시작](01-quickstart.md) | [다음: 커스텀 메트릭](03-custom-metrics.md)

</div>
