# Eval Report Templates

## 1) Run Comparison Summary

### Metadata
- run_id_a:
- run_id_b:
- dataset_name:
- dataset_version:
- date:
- owner:

### KPI Summary
- answer_relevancy:
- faithfulness:
- context_precision:
- context_recall:
- p95_latency_ms:
- cost_per_run:
- judge_agreement:

### Difficulty Distribution
- easy_pct:
- medium_pct:
- hard_pct:
- difficulty_shift_note:

### Top Error Types
- retrieval_miss:
- retrieval_noise:
- grounding_failure:
- instruction_mismatch:
- multi_turn_drift:

### Recommendation
- primary_cause:
- recommended_lever:
- follow_up_experiment:

---

## 2) Latency and Cost Summary

### Stage Latency (p95)
- retrieval_latency_ms:
- rerank_latency_ms:
- generation_latency_ms:

### Cost Breakdown
- retrieval_cost:
- rerank_cost:
- generation_cost:
- total_cost:

### Notes
- bottleneck_stage:
- optimization_candidate:

---

## 3) Failure Analysis Summary

### Failure Distribution
- retrieval_miss_pct:
- retrieval_noise_pct:
- grounding_failure_pct:
- instruction_mismatch_pct:
- multi_turn_drift_pct:

### Evidence Links
- artifact_index_path:
- top_cases:
  - case_id:
    evidence_path:
  - case_id:
    evidence_path:

---

## 4) Judge Calibration Report

### Calibration Dataset
- label_source: human
- sample_size:
- sampling_method:

### Agreement
- human_correlation:
- judge_agreement:
- bias_summary:

### Uncertainty
- variance:
- confidence_interval_method:
- high_uncertainty_cases:
  - case_id:
  - case_id:

---

## 5) Regression Alert Report

### Trigger
- kpi_drop:
- time_window:
- affected_runs:

### Suspected Causes
- data_shift:
- retrieval_change:
- prompt_change:
- model_change:

### Recommended Actions
- action_1:
- action_2:
- action_3:
