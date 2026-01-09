# CLI 출력 스키마 스냅샷

> 작성일: 2026-01-09
> 목적: 웹 UI와 테스트 데이터에 참조할 수 있는 CLI 출력 구조를 고정한다.
> 범위: `run`, `export`, `analyze`, `analyze-compare`, `pipeline analyze`, `stage`.

## 1) `evalvault run --output`

**요약 JSON (기본 결과 저장)**
`EvaluationRun.to_summary_dict()` + `results` + `retrieval_metadata` 조합.

```json
{
  "run_id": "e0a1b2c3-...-f901",
  "dataset_name": "insurance_qa",
  "dataset_version": "v1",
  "model_name": "gpt-4.1",
  "started_at": "2026-01-09T10:12:34",
  "finished_at": "2026-01-09T10:13:10",
  "total_test_cases": 120,
  "passed_test_cases": 88,
  "pass_rate": 0.7333,
  "total_tokens": 182030,
  "total_cost_usd": 2.41,
  "duration_seconds": 36.2,
  "tracker_metadata": {
    "run_mode": "full",
    "evaluation_task": "qa",
    "threshold_profile": "qa",
    "project": "insurance"
  },
  "metrics_evaluated": ["faithfulness", "answer_relevancy"],
  "thresholds": {
    "faithfulness": 0.7,
    "answer_relevancy": 0.7
  },
  "avg_faithfulness": 0.82,
  "avg_answer_relevancy": 0.76,
  "results": [
    {
      "test_case_id": "tc-001",
      "all_passed": true,
      "metrics": [
        {
          "name": "faithfulness",
          "score": 0.91,
          "threshold": 0.7,
          "passed": true
        }
      ]
    }
  ],
  "retrieval_metadata": {
    "tc-001": {
      "doc_ids": ["doc_1", "doc_2"],
      "top_k": 5,
      "retrieval_time_ms": 12.4,
      "scores": [0.21, 0.18],
      "graph_nodes": 10,
      "graph_edges": 22,
      "subgraph_size": 32,
      "community_id": "3"
    }
  }
}
```

## 2) `evalvault export --output`

**상세 JSON (테스트 케이스별 토큰/지연/사유 포함)**

```json
{
  "run_id": "e0a1b2c3-...-f901",
  "dataset_name": "insurance_qa",
  "model_name": "gpt-4.1",
  "metrics_evaluated": ["faithfulness", "answer_relevancy"],
  "results": [
    {
      "test_case_id": "tc-001",
      "all_passed": true,
      "tokens_used": 430,
      "latency_ms": 980,
      "metrics": [
        {
          "name": "faithfulness",
          "score": 0.91,
          "threshold": 0.7,
          "passed": true,
          "reason": "근거 문장과 답변이 일치합니다."
        }
      ]
    }
  ]
}
```

## 3) `evalvault analyze --output`

```json
{
  "analysis_id": "a-001",
  "run_id": "e0a1b2c3-...-f901",
  "analysis_type": "statistical",
  "created_at": "2026-01-09T10:20:00",
  "overall_pass_rate": 0.7333,
  "metric_pass_rates": {
    "faithfulness": 0.78
  },
  "metrics_summary": {
    "faithfulness": {
      "mean": 0.82,
      "std": 0.09,
      "min": 0.41,
      "max": 0.97
    }
  },
  "correlation_matrix": {
    "faithfulness": {"answer_relevancy": 0.38}
  },
  "correlation_metrics": ["faithfulness", "answer_relevancy"],
  "significant_correlations": [],
  "low_performers": [],
  "insights": ["faithfulness 점수가 특정 도메인에서 낮습니다."],
  "nlp_analysis": {
    "run_id": "e0a1b2c3-...-f901",
    "question_stats": {
      "count": 120,
      "avg_tokens": 18.2
    },
    "answer_stats": {
      "count": 120,
      "avg_tokens": 62.4
    },
    "context_stats": null,
    "question_types": [],
    "top_keywords": [],
    "insights": []
  },
  "improvement_report": {
    "summary": "임계값 미달 원인 후보가 2건 탐지됨"
  }
}
```

## 4) `evalvault analyze-compare --output`

**비교 분석 파이프라인 결과 (자동 리포트/아티팩트 포함)**

```json
{
  "intent": "generate_comparison",
  "pipeline_id": "p-compare-001",
  "is_complete": true,
  "duration_ms": 2310,
  "started_at": "2026-01-09T10:30:00",
  "finished_at": "2026-01-09T10:30:02",
  "final_output": {
    "run_metric_comparison": {
      "summary": {"winner": "run_a"}
    }
  },
  "node_results": {
    "run_metric_comparison": {
      "status": "success",
      "error": null,
      "duration_ms": 420,
      "output": {}
    }
  },
  "run_ids": ["run_a", "run_b"],
  "artifacts": {
    "dir": "reports/comparison/artifacts/comparison_run_a_run_b",
    "index": "reports/comparison/artifacts/comparison_run_a_run_b/index.json"
  }
}
```

## 5) `evalvault run --auto-analyze` 출력 (`--analysis-json`)

**자동 분석 파이프라인 결과 (구조는 4)와 동일 + `run_id` 추가**

```json
{
  "intent": "generate_detailed",
  "pipeline_id": "p-analysis-001",
  "is_complete": true,
  "duration_ms": 4100,
  "final_output": {},
  "node_results": {},
  "run_id": "e0a1b2c3-...-f901",
  "artifacts": {
    "dir": "reports/analysis/artifacts/analysis_e0a1b2c3",
    "index": "reports/analysis/artifacts/analysis_e0a1b2c3/index.json"
  }
}
```

## 6) `evalvault pipeline analyze --output`

```json
{
  "query": "요약해줘",
  "intent": "generate_summary",
  "is_complete": true,
  "duration_ms": 1200,
  "final_output": {
    "report": "# Summary\n..."
  }
}
```

## 7) Stage 이벤트 JSON/JSONL

**단일 이벤트 예시 (JSONL 한 줄)**

```json
{
  "run_id": "e0a1b2c3-...-f901",
  "stage_id": "stage-001",
  "parent_stage_id": null,
  "stage_type": "retrieval",
  "stage_name": "bm25",
  "status": "success",
  "attempt": 1,
  "started_at": "2026-01-09T10:12:40",
  "finished_at": "2026-01-09T10:12:40.120",
  "duration_ms": 120.0,
  "input_ref": {"store": "sqlite", "id": "payload_1", "type": "json"},
  "output_ref": {"store": "sqlite", "id": "payload_2", "type": "json"},
  "attributes": {"top_k": 5},
  "metadata": {"retriever": "bm25"},
  "trace": {"trace_id": "trace-001", "span_id": "span-001"}
}
```

**필수 stage_type**: `system_prompt`, `input`, `retrieval`, `output`

## 8) Stage 메트릭 (DB 저장/가이드 생성용)

```json
{
  "run_id": "e0a1b2c3-...-f901",
  "stage_id": "stage-001",
  "metric_name": "latency_ms",
  "score": 120.0,
  "threshold": 200.0,
  "evidence": {"comparison": "max"}
}
```

## 9) 파이프라인 아티팩트 인덱스 예시 (`index.json`)

```json
{
  "pipeline_id": "p-analysis-001",
  "intent": "generate_detailed",
  "duration_ms": 4100,
  "started_at": "2026-01-09T10:15:00",
  "finished_at": "2026-01-09T10:15:04",
  "nodes": [
    {
      "node_id": "statistical_analyzer",
      "status": "success",
      "duration_ms": 800,
      "error": null,
      "path": "reports/analysis/artifacts/analysis_e0a1b2c3/statistical_analyzer.json"
    }
  ],
  "final_output_path": "reports/analysis/artifacts/analysis_e0a1b2c3/final_output.json"
}
```
