# RAG 인간 피드백 보정: 상세 구현 계획서

본 문서는 `docs/guides/rag_human_feedback_calibration.md`의 설계를 기반으로 EvalVault에 **사람 만족도 보정(calibration) 기능**을 구현하기 위한 상세 실행 계획을 정리합니다.

---

## 1. 목표/성공 기준

### 목표
- 대표 샘플 기반 인간 평가 수집 → 보정 모델 학습 → 전체 결과에 보정 점수 적용.
- RAGAS 점수와 사용자 만족도 괴리를 줄이고, 이해 가능한 보정 지표를 제공.

### 성공 기준
- DB에 `satisfaction_feedback` 저장/조회 가능.
- Run 상세 응답에 `calibrated_satisfaction`, `imputed`, `imputation_source` 포함.
- CLI `evalvault calibrate` 실행 시 보정 모델 성능 요약 출력.
- Web UI에서 평가 입력/조회/보정 점수 표시.

---

## 2. 전제 및 스코프

### 전제
- 문서에 제시된 정책을 기본값으로 채택:
  - 만족도 라벨: 1~5
  - Thumb 피드백: up/down/none (약한 레이블)
  - 보정 점수: `calibrated_satisfaction`
  - 결측치 보정 규칙: thumb → 매핑, 없으면 모델 예측

### 스코프
- 백엔드: StoragePort, SQL 스키마, API, CLI, 도메인 서비스
- 프론트엔드: RunDetails UI에 만족도 평가 탭 + 보정 점수 표시
- 모델: 선형 회귀 + XGBoost 회귀(선형은 설명용)

### 비스코프(초기)
- 실시간 온라인 학습, A/B 실험 자동 트리거
- 자동 평가자(LLM Judge) 연동

---

## 3. 아키텍처 개요

### 데이터 플로우
1) 대표 샘플 선정(클러스터링) → 2) 인간 평가 수집 → 3) 피처 생성 → 4) 모델 학습 → 5) 보정 점수 추정 → 6) UI 표시

### 재사용 가능한 기존 컴포넌트
- 클러스터링: `src/evalvault/domain/services/cluster_map_builder.py`
- NLP 피처 패턴: `src/evalvault/adapters/outbound/analysis/nlp_adapter.py`
- Storage 어댑터 패턴: `src/evalvault/adapters/outbound/storage/*_adapter.py`

---

## 4. 데이터 모델/스키마 설계

### 신규 테이블
`src/evalvault/adapters/outbound/storage/schema.sql`

`satisfaction_feedback`
- `id` (PK)
- `run_id`
- `test_case_id`
- `satisfaction_score` (1~5, nullable)
- `thumb_feedback` (`up`/`down`/`none`)
- `comment` (nullable)
- `rater_id` (nullable)
- `created_at`

### 결과 확장
- 테스트 케이스 결과: `calibrated_satisfaction`, `imputed`, `imputation_source`
- run summary: `avg_satisfaction_score`, `thumb_up_rate`, `imputed_ratio`

---

## 5. StoragePort/Adapter 설계

### StoragePort 확장
`src/evalvault/ports/outbound/storage_port.py`
- `save_feedback(...)`
- `list_feedback(run_id)`
- `get_feedback_summary(run_id)`

### 어댑터 확장
- `src/evalvault/adapters/outbound/storage/sqlite_adapter.py`
- `src/evalvault/adapters/outbound/storage/postgres_adapter.py`

### 마이그레이션
- 기존 DB에 `satisfaction_feedback` 테이블 추가
- 인덱스: `run_id`, `test_case_id`

---

## 6. API 설계 (FastAPI)

### 라우터 확장
`src/evalvault/adapters/inbound/api/routers/runs.py`

- `POST /api/v1/runs/{run_id}/feedback`
  - 요청: `test_case_id`, `satisfaction_score?`, `thumb_feedback?`, `comment?`, `rater_id?`

- `GET /api/v1/runs/{run_id}/feedback`
  - 응답: 피드백 리스트

- `GET /api/v1/runs/{run_id}`
  - summary에 `avg_satisfaction_score`, `thumb_up_rate`, `imputed_ratio` 포함
  - results[].metrics에 `calibrated_satisfaction`, `imputed`, `imputation_source` 포함

---

## 7. CLI 설계

### 명령
`src/evalvault/adapters/inbound/cli/commands/calibrate.py`

```
evalvault calibrate --run-id <ID> [--model linear|xgb|both] [--write-back]
```

### 출력
- 모델 성능 요약: Pearson/Spearman, MAE
- 피처 중요도(가능 시)

---

## 8. Web UI 설계

`frontend/src/pages/RunDetails.tsx`

### UI 기능
- 탭: `만족도 평가`
  - 별점(1~5), thumb up/down, 코멘트 입력
  - 테스트 케이스별 저장

### 표시
- Summary 카드: 평균 만족도, Thumb Up 비율, 보정 비율
- 메트릭 표에 `calibrated_satisfaction` 컬럼 추가

---

## 9. 보정/결측치 처리 규칙

1. `satisfaction_score` 있음 → 그대로 사용
2. 없고 `thumb_feedback` 있음 → 약한 레이블 매핑
   - `up = 4.0`, `down = 2.0`
3. 둘 다 없으면 모델 예측값 사용
4. 모든 점수는 1~5로 클리핑
5. `imputed` 및 `imputation_source` 필드 표시

---

## 10. 모델/피처 설계

### 피처
- RAGAS: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
- 한국어 피처:
  - 답변 길이
  - 질문 키워드 누락률
  - 형태소 다양성(TTR)

### 모델
- 기본: 선형회귀 (설명용)
- 출력: XGBoost 회귀 (예측 성능용)

### 의존성
- `scikit-learn`은 이미 존재
- `xgboost`는 `pyproject.toml`의 optional dependencies에 추가 필요

---

## 11. 대표 샘플링 전략

### 1차 버전
- `cluster_map_builder.py`의 KMeans + TF-IDF 임베딩 활용
- 클러스터 당 centroid 가까운 케이스 1개씩 선택

### 확장 버전
- 불확실성 기반 샘플 추가 (예측값 2.4~2.6 등)

---

## 12. 테스트/검증 계획

### 단위 테스트
- StoragePort: save/list 피드백 동작
- 보정 모델: 학습/예측 결과 shape 및 범위

### 통합 테스트
- API 엔드포인트: 저장/조회 동작

### 품질 지표
- 상관계수, MAE
- Inter-rater agreement(가능 시): Cohen/Fleiss Kappa

---

## 13. 단계별 일정(제안)

1. **DB/Storage 레이어 확장**
2. **도메인 서비스(모델/보정 로직) 구현**
3. **API 확장**
4. **CLI 구현**
5. **UI 통합**
6. **테스트 및 검증**

---

## 14. 리스크 및 대응

- **라벨 노이즈**: 평가 가이드 문서화 + 다중 평가자 평균
- **샘플 편향**: 대표 샘플링 + 운영 중 추가 샘플링
- **모델 과적합**: 단순 모델 우선, 교차검증

---

## 15. 참고 문서

- `docs/guides/rag_human_feedback_calibration.md`
- `src/evalvault/domain/services/cluster_map_builder.py`
- `src/evalvault/adapters/outbound/analysis/nlp_adapter.py`
