# Korean RAG Benchmark Guide

> **Version**: 1.0.0
> **Last Updated**: 2025-12-30
> **Phase**: 9.5 Complete

## Overview

EvalVault Korean RAG Benchmark는 한국어 RAG 시스템 최적화 효과를 측정하는 벤치마크 도구입니다.

### 측정 대상

| Task | 측정 항목 | 예상 개선 |
|------|----------|----------|
| **Faithfulness** | 조사/어미 변형 무시 효과 | +25%p |
| **Keyword Extraction** | 형태소 분석 vs 공백 기반 | +20-50%p |
| **Retrieval** | 하이브리드 검색 효과 | +15-20% |

---

## Quick Start

```bash
# 전체 벤치마크 실행
uv run python examples/benchmarks/run_korean_benchmark.py

# 개별 벤치마크 실행
uv run python examples/benchmarks/run_korean_benchmark.py --task faithfulness
uv run python examples/benchmarks/run_korean_benchmark.py --task keyword
uv run python examples/benchmarks/run_korean_benchmark.py --task retrieval

# 기준선 비교 (형태소 분석 vs 공백 기반)
uv run python examples/benchmarks/run_korean_benchmark.py --compare

# 상세 출력
uv run python examples/benchmarks/run_korean_benchmark.py --verbose
```

---

## Output Formats

벤치마크 결과는 여러 프레임워크 호환 형식으로 출력됩니다:

### 1. MTEB Format

[MTEB (Massive Text Embedding Benchmark)](https://github.com/embeddings-benchmark/mteb) 호환 형식:

```json
{
  "task_name": "KoreanRAGFaithfulness",
  "task_type": "faithfulness",
  "languages": ["ko"],
  "scores": {
    "main_score": 0.89,
    "subscores": {
      "token_overlap": 0.92,
      "semantic_match": 0.86
    }
  },
  "hf_subset": "ko-insurance",
  "mteb_version": "1.0.0"
}
```

### 2. lm-evaluation-harness Format

[EleutherAI lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) 호환 형식:

```json
{
  "results": {
    "korean_rag_faithfulness": {
      "main_score": 0.89,
      "main_score_stderr": 0.02
    }
  },
  "config": {
    "model": "korean-rag-evaluator",
    "num_fewshot": 0
  },
  "versions": {
    "korean_rag_faithfulness": "1.0.0"
  }
}
```

### 3. DeepEval Format

[DeepEval](https://github.com/confident-ai/deepeval) 호환 형식:

```json
{
  "test_cases": [
    {
      "input": "보험료가 얼마인가요?",
      "actual_output": "보험료는 월 3만원입니다.",
      "retrieval_context": ["보험료는 월 3만원입니다."],
      "expected_output": "월 3만원"
    }
  ],
  "metrics": [
    {
      "name": "FaithfulnessMetric",
      "score": 0.89,
      "success": true
    }
  ]
}
```

### 4. Leaderboard Format

자체 리더보드 형식:

```json
{
  "generated_at": "2025-12-30T12:00:00",
  "model_name": "korean-rag-evaluator",
  "leaderboard": [
    {
      "task": "korean_rag_faithfulness",
      "score": 0.89,
      "pass_rate": 0.87
    },
    {
      "task": "korean_rag_keyword",
      "score": 0.92,
      "pass_rate": 0.90
    },
    {
      "task": "korean_rag_retrieval",
      "score": 0.85,
      "pass_rate": 0.80
    }
  ],
  "average_score": 0.887
}
```

---

## Benchmark Tasks

### 1. Faithfulness Benchmark

한국어 문장에서 조사/어미 변형을 무시하고 의미적 일치를 검증합니다.

**테스트 케이스 예시:**

```json
{
  "id": "faith-001",
  "question": "이 보험의 보장금액은 얼마인가요?",
  "answer": "보장금액은 1억원입니다.",
  "contexts": ["해당 보험의 사망 보장금액은 1억원입니다."],
  "expected_faithful": true
}
```

**측정 메트릭:**
- `token_overlap`: 형태소 분석 후 토큰 겹침 비율
- `semantic_match`: 의미적 일치도

### 2. Keyword Extraction Benchmark

형태소 분석 기반 키워드 추출 정확도를 측정합니다.

**테스트 케이스 예시:**

```json
{
  "id": "kw-001",
  "text": "암보험은 암 진단 시 보험금을 지급하는 보험입니다.",
  "expected_keywords": ["암보험", "암", "진단", "보험금", "지급", "보험"]
}
```

**측정 메트릭:**
- `precision`: 추출 정밀도
- `recall`: 추출 재현율
- `f1_score`: F1 점수

### 3. Retrieval Benchmark

하이브리드 검색(BM25 + Dense)의 효과를 측정합니다.

**테스트 케이스 예시:**

```json
{
  "id": "ret-001",
  "query": "보험료가 얼마인가요?",
  "documents": [
    {"id": "doc-1", "content": "보험료는 월 3만원입니다.", "relevant": true},
    {"id": "doc-2", "content": "보장 기간은 20년입니다.", "relevant": false}
  ],
  "relevant_doc_ids": ["doc-1"]
}
```

**측정 메트릭:**
- `recall_at_5`: 상위 5개 문서 재현율
- `mrr`: Mean Reciprocal Rank

---

## Comparison Mode

`--compare` 옵션을 사용하면 형태소 분석 기반 vs 공백 기반 토큰화의 성능을 비교합니다:

```
======================================================================
  Baseline Comparison (Morpheme Analysis vs Whitespace)
======================================================================

  [FAITHFULNESS]
    ✓ token_overlap: 0.620 → 0.890 (+0.270, +43.5%)
    ✓ semantic_match: 0.580 → 0.850 (+0.270, +46.6%)

  [KEYWORD]
    ✓ precision: 0.450 → 0.920 (+0.470, +104.4%)
    ✓ recall: 0.680 → 0.850 (+0.170, +25.0%)
    ✓ f1_score: 0.542 → 0.884 (+0.342, +63.1%)

  [RETRIEVAL]
    ✓ recall_at_5: 0.650 → 0.850 (+0.200, +30.8%)
    ✓ mrr: 0.550 → 0.780 (+0.230, +41.8%)
```

---

## Adding Custom Test Cases

### 파일 구조

```
examples/benchmarks/korean_rag/
├── insurance_qa_100.json      # 100개 보험 QA 테스트
├── faithfulness_test.json     # 15개 Faithfulness 테스트
├── keyword_extraction_test.json  # 10개 키워드 추출 테스트
└── retrieval_test.json        # 15개 검색 테스트
```

### 테스트 케이스 추가 방법

1. **Faithfulness 테스트 추가:**

```json
{
  "id": "faith-custom-001",
  "question": "질문 내용",
  "answer": "RAG 생성 답변",
  "contexts": ["관련 컨텍스트 1", "관련 컨텍스트 2"],
  "expected_faithful": true
}
```

2. **키워드 추출 테스트 추가:**

```json
{
  "id": "kw-custom-001",
  "text": "분석할 텍스트",
  "expected_keywords": ["예상", "키워드", "목록"]
}
```

3. **검색 테스트 추가:**

```json
{
  "id": "ret-custom-001",
  "query": "검색 쿼리",
  "documents": [
    {"id": "doc-1", "content": "문서 내용", "relevant": true}
  ],
  "relevant_doc_ids": ["doc-1"]
}
```

---

## Integration with pytest

벤치마크는 pytest와 통합하여 CI/CD 파이프라인에서 실행할 수 있습니다:

```python
# tests/unit/test_benchmark_runner.py

import pytest
from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner

@pytest.fixture
def benchmark_runner():
    return KoreanRAGBenchmarkRunner(
        use_korean_tokenizer=True,
        threshold=0.7,
    )

def test_faithfulness_benchmark(benchmark_runner, tmp_path):
    # 테스트 데이터 생성
    test_file = tmp_path / "faithfulness_test.json"
    test_file.write_text(json.dumps({
        "test_cases": [
            {
                "id": "test-001",
                "question": "보험료는?",
                "answer": "보험료는 3만원입니다.",
                "contexts": ["보험료는 월 3만원입니다."],
                "expected_faithful": True
            }
        ]
    }))

    result = benchmark_runner.run_faithfulness_benchmark(test_file)
    assert result.main_score >= 0.7
```

---

## Programmatic Usage

```python
from pathlib import Path
from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner

# 러너 초기화
runner = KoreanRAGBenchmarkRunner(
    use_korean_tokenizer=True,
    threshold=0.7,
    verbose=True,
)

# 전체 스위트 실행
benchmark_dir = Path("examples/benchmarks/korean_rag")
output_dir = Path("examples/benchmarks/output")

suite = runner.run_full_suite(
    benchmark_dir=benchmark_dir,
    output_dir=output_dir,
)

# 결과 출력
print(f"Total Score: {suite.main_score:.4f}")
for result in suite.results:
    print(f"  {result.task_name}: {result.main_score:.4f}")

# 다양한 형식으로 변환
mteb_dict = suite.results[0].to_mteb_dict()
lm_harness_dict = suite.results[0].to_lm_harness_dict()
deepeval_dict = suite.results[0].to_deepeval_dict()
leaderboard = suite.to_leaderboard_format()
```

---

## Output Files

벤치마크 실행 후 생성되는 파일:

| 파일 | 설명 |
|------|------|
| `full_results.json` | 전체 벤치마크 결과 |
| `results_mteb.json` | MTEB 호환 결과 |
| `results_lm_harness.json` | lm-evaluation-harness 호환 결과 |
| `results_deepeval.json` | DeepEval 호환 결과 |
| `leaderboard.json` | 리더보드 형식 결과 |
| `comparison.json` | 기준선 비교 결과 (--compare 사용 시) |
| `{task}_result.json` | 개별 태스크 결과 |

---

## References

- [MTEB (Massive Text Embedding Benchmark)](https://github.com/embeddings-benchmark/mteb)
- [DeepEval](https://github.com/confident-ai/deepeval)
- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)
- [Ragas](https://github.com/explodinggradients/ragas)
- [Kiwi 형태소 분석기](https://github.com/bab2min/kiwipiepy)

---

**문서 끝**
