# Test Fixtures

이 디렉터리는 EvalVault 테스트에 사용되는 모든 픽스처 데이터를 포함합니다.

## 디렉터리 구조

```
tests/fixtures/
├── sample_dataset.csv      # 단위 테스트용 샘플 (영어)
├── sample_dataset.json     # 단위 테스트용 샘플 (영어)
├── sample_dataset.xlsx     # 단위 테스트용 샘플 (영어)
├── benchmark/              # 벤치마크용 doc_id ground_truth
│   ├── retrieval_ground_truth_min.json
│   └── retrieval_ground_truth_multi.json
└── e2e/                    # E2E 및 통합 테스트용 데이터셋
    ├── insurance_qa_korean.*    # 한국어 보험 QA
    ├── insurance_qa_english.*   # 영어 보험 QA
    ├── edge_cases.*             # 엣지 케이스 테스트
    ├── evaluation_test_sample.json
    ├── comprehensive_dataset.json  # 종합 E2E 테스트
    ├── summary_eval_minimal.json   # 요약 평가 최소 케이스
    └── insurance_document.txt      # 테스트용 보험 문서
```

## 파일 형식

모든 JSON 데이터셋은 다음 스키마를 따릅니다:

```json
{
  "name": "dataset-name",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.7,
    "answer_relevancy": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "질문",
      "answer": "답변",
      "contexts": ["컨텍스트1", "컨텍스트2"],
      "ground_truth": "정답"
    }
  ]
}
```

## 사용 방법

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
E2E_DIR = FIXTURES_DIR / "e2e"

# 단위 테스트
sample_data = FIXTURES_DIR / "sample_dataset.json"

# E2E 테스트
korean_qa = E2E_DIR / "insurance_qa_korean.json"
```

## 주의사항

- 새 픽스처 추가 시 이 디렉터리에 통합하세요
- 런타임 생성 데이터는 `data/e2e_results/`에 저장됩니다 (gitignore)
- CSV/Excel 파일은 JSON과 동일한 데이터를 다른 형식으로 제공합니다
