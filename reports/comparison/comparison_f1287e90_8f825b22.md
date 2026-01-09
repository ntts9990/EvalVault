# RAG 평가 비교 분석 보고서

## 요약
두 실행 결과를 비교해 본 결과, **Run A**는 질문에 대한 답변이 대부분 문맥과 일치했으나 신뢰성(faithfulness) 측면에서 부진했으며, **Run B**는 `faithfulness`가 높게 나타났으나 `answer_relevancy`가 크게 감소하였다.
- 지표 : `answer_relevancy`가 35 % 감소
- 변경 사항 : 데이터셋이 4개 → 18개로 확대, 실제 테스트 케이스 수 적음
- 사용자 영향 : 한국어 보험 관련 질문에 대해 정확한 답변 제공이 어려움

---

## 1. 변경 사항 요약
| 항목 | 전 상태 | 후 상태 | 비고 |
|------|----------|---------|------|
| dataset_name | test_dataset | e2e‑auto‑insurance‑qa‑korean | 데이터셋 변경 |
| total_test_cases | 4 | 18 | 샘플 수 확장, 실제 케이스 4개만 제공 |
| prompt_change_count | 0 | 0 | 프롬프트 변경 없음 (snapshot 미발견) |

---

## 2. 지표 비교 스코어카드
| metric | Run A | Run B | diff | p‑value | effect size | 효과 수준 | 승자 | 상태 |
|--------|-------|-------|------|---------|-------------|------------|------|------|
| faithfulness | 0.50 | 0.83 | +0.33 | 0.165 | 0.756 | 중간 | — | 비고 : 차이통계 유의미 아님 |
| answer_relevancy | 0.884 | 0.566 | –0.318 | 7.1e‑07 | –4.99 | 대 | Run A | 유의미 감소 |

> **주의**: 두 실행은 다른 데이터셋을 사용하므로 지표 차이를 해석할 때 반드시 데이터셋 차이를 반영해야 합니다.

---

## 3. 통계적 신뢰도
- **표본 수**: Run A는 4건, Run B는 18건 중 4건만 공개 → **표본 수 부족** (quality_checks flagged).
- **p‑value**
  - `faithfulness`: 0.165 → **비유의미**
  - `answer_relevancy`: 7.1 × 10⁻⁷ → **확실히 유의미**

> *확인 필요*: 추가 사례를 포함해 테스트 집합의 통계적 파워를 증가시키는 것이 권장됩니다.

---

## 4. 원인 분석
| 원인 | 증거 | 영향 | 비고 |
|------|------|------|------|
| 데이터셋 변화 | `e2e‑auto‑insurance‑qa‑korean` 도입 | `answer_relevancy` 감소 (비한국어 → 한국어 내용이 비일관적) | [B1] |
| 테스트 케이스 수 부족 | `quality_summary.flags` | 표본 수가 4건 ≤ 10개 → 신뢰도가 낮음 |  |
| 모델 신뢰성 변동 | `faithfulness` 0.0 → 0.833 (전반) | 특정 문맥에 대한 정확도 개선 | – |

> *핵심*: 한국어 도메인에서는 문맥이 복잡해 `faithfulness`가 개선되었으나, relevancy가 크게 떨어지면서 실제 사용자에게 불리함.

---

## 5. 개선 제안
1. **데이터셋 보강**
   - `e2e‑auto‑insurance‑qa‑korean`에 포함된 모든 18개 테스트 케이스에 대한 **metrics**를 재측정.
   - **증거**: [B2] `answer_relevancy`가 0.632 → 여전히 낮음.

2. **프롬프트 최적화**
   - `--db`, `--system-prompt`, `--ragas-prompts` 옵션을 활용해 문맥 명시성 강화.
   - 프롬프트 버전 관리가 필요합니다 (snapshot이 없으므로 재생성).

3. **모델 튜닝**
   - `faithfulness`는 현재 충분히 높으므로 `answer_relevancy` 향상에 초점을 맞춤.
   - retrieval 구성(베이스, 유사도 임계값)을 재설정해 문맥 일관성 보장.

4. **평가 프레임워크 검증**
   - `quality_checks.flags`를 토대로, **sample_count**를 10 이상으로 설정하고 재실험.

> **추가 데이터 필요**: 현재 4개 사례만으로는 통계적 유의성 판단이 불충분합니다.

---

## 6. 다음 단계
| 단계 | 목표 | 담당 | 비고 |
|------|------|------|------|
| 6.1 | 전 데이터셋(18건) 평가 | QA팀 | `run_b` 메트릭 완전 기록 |
| 6.2 | 프롬프트 재설정 및 재실험 | 엔지니어 | `--system-prompt` 업데이트 |
| 6.3 | 재실험 결과 비교 | 분석가 | `scorecard` 자동화 |
| 6.4 | 결과 보고서 업데이트 | 문서팀 | 최신 시각화 & 설명 |

---

## 부록(산출물 링크)

- [load_runs.json](artifacts/comparison_f1287e90_8f825b22/load_runs.json)
- [run_metric_comparison.json](artifacts/comparison_f1287e90_8f825b22/run_metric_comparison.json)
- [run_change_detection.json](artifacts/comparison_f1287e90_8f825b22/run_change_detection.json)
- [report.json](artifacts/comparison_f1287e90_8f825b22/report.json)
- [final_output.json](artifacts/comparison_f1287e90_8f825b22/final_output.json)
- [index.json](artifacts/comparison_f1287e90_8f825b22/index.json)
