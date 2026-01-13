# LENA MVP 구현 계획서 (EvalVault)

- 문서 목적: EvalVault에 **LENA(LLM Eval Noise Analyzer)** MVP를 “구현 가능한 작업 단위”로 쪼개고, 구현/리뷰/릴리즈에서 그대로 사용할 **체크리스트 + 설계 스펙(초안)**을 제공한다.
- 현재 상태: **LENA MVP는 아직 미구현**이다. 현재 코드베이스의 `src/evalvault/adapters/outbound/analysis/statistical_adapter.py`는 t-test / Mann-Whitney 등 **전통적(독립 표본 가정 중심) 비교**만 제공하며, PRD의 **노이즈 분해/SE 모드/NK 추천**은 제공하지 않는다.
- 근거 문서(요구사항/인수 기준의 원천):
  - `docs/guides/PRD_LENA.md`
  - `docs/guides/LENA_RAGAS_CALIBRATION_DEV_PLAN.md` (통합 관점 참고. 단, 본 문서는 “LENA MVP”에 한정)

> 주의: 본 문서는 **구현 계획 문서**이며, LENA가 아직 없음을 전제로 “생성/수정 예정 파일 경로”를 명시한다. 또한 CLI/API 스펙 예시는 **계약(Contract) 초안**이며, 현재는 실행 검증이 불가능하다(미구현).

---

## 0) 목표 요약(한 줄)

평가 결과에 대해 **diff + CI + p-value**를 제공하고, 점수 변동성을 **Data vs Prediction 노이즈로 분해**하며, 목표 MDE/power/alpha에 맞춰 다음 실험의 **(N,K) 최소 비용 조합을 추천**한다. (Backend/CLI → API → Web UI 순)

---

## 1) 범위(Scope)

### 1.1 MVP 포함(“Must Have”, PRD M01~M07)

- **M01 다중 예측 수집**: 동일 질문에 대해 K회 예측/평가 결과를 입력으로 수용(“질문×반복” 구조)
- **M02 노이즈 분해**: Total/Data/Prediction 분해 + **small-K 보정** 포함
- **M03 Paired 분석**: A/B 비교는 **동일 질문 ID 매칭을 강제**
- **M04 유의성/신뢰구간**: 평균, diff, CI, p-value, 유의성 판단(기본: 정규 근사 z-test)
- **M05 SE 모드 3종**: `single` / `mean_k` / `expected`
- **M06 (N,K) 추천**: 파일럿(N0,K0) 기반 data_var/pred_var 추정 → 격자 탐색 + 비용 추정
- **M07 결과 시각화용 구조화 산출물(JSON)**: UI/리포트가 소비 가능한 데이터 모델 제공

### 1.2 MVP 제외(Out of scope / Non-goals)

- 강건 통계(확장): bootstrap CI, sign test, all-pairs, 다중비교 보정(FDR/BH)
- 순차 검정/중간중단(optional stopping) 정책 포함 온라인 A/B
- “메트릭 타당도(validity) 보장” 자체 (LENA는 reliability 제공)
- 인간 피드백 기반 보정(calibration) 기능의 구현(통합 관점은 `docs/guides/LENA_RAGAS_CALIBRATION_DEV_PLAN.md` 참고하되, 본 MVP에서는 LENA만)

---

## 2) 전제(Assumptions) & 설계 원칙

### 2.1 전제(데이터/실행)

- A/B 비교는 **동일한 질문 ID(=question_id/test_case_id)가 정렬 가능**해야 한다.
- `N`과 `K` 정의는 `docs/guides/PRD_LENA.md`를 따른다:
  - `N`: 질문(데이터 포인트) 개수
  - `K`: 동일 질문에 대한 반복 예측/평가 수
- **NK를 독립 표본으로 취급하지 않는다.**
  - 기본 단위는 “질문별 K회 평균”이며, 전체 평균/SE도 그 단위로 계산한다.

### 2.2 전제(통계/해석)

- MVP의 기본 검정은 정규 근사(z-test)로 시작한다(PRD의 “빠른 경로”).
- `K <= 1`일 때 Prediction 노이즈 분해는 불안정/정의 불가 구간이 존재한다.
  - 이 경우 결과에 `warnings`를 포함하고, 모드/필드 제한을 명시한다(조용히 NaN만 뿌리지 않음).

### 2.3 구현 원칙(프로덕션 일관성)

- EvalVault는 헥사고날 구조를 따른다(AGENTS.md).
- Domain 로직(분해/SE/추천)은 **도메인 서비스**에 위치시키고,
  - CLI/API는 **유스케이스 호출 + 입력/출력 직렬화**만 담당한다.
- 산출물 저장은 기존 패턴(리포트/아티팩트)을 최대한 재사용한다.
  - 참고: `reports/analysis/*`, `reports/comparison/*`
  - 아티팩트 인덱스/노드 JSON 저장 헬퍼: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

---

## 3) 아키텍처(헥사고날) & 모듈 맵

### 3.1 레이어별 역할(요약)

- Domain: `src/evalvault/domain/**`
  - 엔티티(입출력 스키마), 서비스(노이즈/비교/추천 핵심 로직)
- Ports: `src/evalvault/ports/**`
  - inbound: CLI/API가 호출할 유스케이스 계약(서비스 인터페이스)
  - outbound: (필요 시) 저장/리포트/트래커 연계 계약
- Adapters: `src/evalvault/adapters/**`
  - inbound: Typer CLI / FastAPI
  - outbound: 저장소/분석/트래커 등 외부 의존 구현

### 3.2 LENA MVP 신규/확장 예정 파일(초안)

> 아래 경로는 “생성/수정 예정”이다. 실제 구현 시 기존 네이밍/타입힌트/직렬화 방식에 맞춘다.

| 레이어 | 역할 | 파일(예정) |
|---|---|---|
| Domain Entities | LENA 결과/요청 데이터 모델(직렬화 가능) | `src/evalvault/domain/entities/lena.py` (신규) |
| Domain Service | 노이즈 분해/비교/추천 핵심 로직 | `src/evalvault/domain/services/lena_service.py` (신규) |
| Ports (Inbound) | CLI/API 호출 계약 | `src/evalvault/ports/inbound/lena_port.py` (신규) |
| Adapters (Inbound/CLI) | `evalvault lena ...` 커맨드 | `src/evalvault/adapters/inbound/cli/commands/lena.py` (신규) + `src/evalvault/adapters/inbound/cli/commands/__init__.py` (등록 수정) |
| Adapters (Inbound/API) | UI용 REST 라우터 | `src/evalvault/adapters/inbound/api/routers/lena.py` (신규) + `src/evalvault/adapters/inbound/api/main.py` (라우터 include) |
| Storage/Artifacts | 결과 저장(재사용 중심) | 기존 유틸 재사용: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` |
| Tests | 단위/시뮬/통합 | `tests/unit/...`, `tests/integration/...` (신규) |

### 3.3 데이터 흐름(Backend/CLI → API → UI)

```mermaid
flowchart LR
  A[입력: run_id 또는 EvalMatrix 파일] --> B[EvalMatrix/정렬 구성]
  B --> C[LENA Service<br/>noise/compare/recommend]
  C --> D[Noise 결과]
  C --> E[Compare 결과]
  C --> F[(N,K) 추천]
  D & E & F --> G[JSON 산출물/응답]
  G --> H[CLI 출력/저장]
  G --> I[FastAPI 응답]
  I --> J[Web UI 위젯]
```

---

## 4) 입력 모델(데이터 계약)

### 4.1 핵심 개념: Evaluator vs Run vs Metric

- LENA는 “평가자(Evaluator) 단위” 또는 “Run 단위”로 분석을 수행할 수 있다.
- EvalVault 운영 관점에서 가장 단순한 MVP 경로는 다음 2가지다.

### 4.2 입력 경로 A: EvalVault Run 기반(운영 친화)

- 입력: `run_id`(또는 A/B `run_id_a`, `run_id_b`)
- 내부에서 `EvaluationRun`을 로드한 뒤,
  - 질문 ID 축을 기준으로 정렬하고,
  - `metric_name`별로 (N×K)에 해당하는 값들을 구성한다.

> 구현 상세(질문×반복을 어떤 필드로 복원할지)는 실제 평가 저장 구조에 따라 결정해야 한다. 이 문서는 “정렬/매칭을 강제한다”는 요구사항만 고정한다.

### 4.3 입력 경로 B: 독립형 EvalMatrix 파일 기반(재현성/디버깅 친화)

- 입력: PRD가 제시한 `EvalMatrix(N×K)`를 외부 파일로 로드
- MVP에서는 최소한 아래 정보가 필요하다:
  - `question_ids`(길이 N)
  - `metrics`(shape N×K)
  - `seeds` 또는 `replicate_ids`(길이 K, 이름은 구현에서 확정)

> 파일 포맷(JSONL/CSV/JSON)은 구현에서 확정한다. 다만 “질문×반복” 구조가 손실되지 않아야 한다.

---

## 5) 출력(산출물) 스키마(계약 초안)

### 5.1 공통 메타(`meta`)

모든 결과는 UI/리포트/재현성을 위해 아래 메타를 포함한다(필드는 구현에서 확정하되 의미는 유지).

- `meta` (object)
  - `schema_version` (string)
  - `created_at` (string, ISO 8601)
  - `source` (object)
    - `mode` (`run_id` | `eval_matrix_file`)
    - `run_id` / `run_id_a` / `run_id_b` (optional)
    - `dataset_name` (optional)
    - `metric_name` (string)
  - `params` (object)
    - `se_mode` (`single` | `mean_k` | `expected`)
    - `alpha` (float, optional)
    - `power` (float, optional)
    - `target_mde` (float, optional)
  - `assumptions` (array of string)
  - `warnings` (array of string)
  - `errors` (array of object, optional; 입력 전제 위반 시)

### 5.2 Noise 결과(`noise`)

- `noise` (object)
  - `N` (int)
  - `K` (int)
  - `total_var` (float)
  - `data_var` (float)
  - `pred_var` (float | null) — `K<=1`일 때 null/미정
  - `se` (object)
    - `single` (float)
    - `mean_k` (float | null) — `K<=1`이면 null
    - `expected` (float)

### 5.3 Compare 결과(`comparison`)

- `comparison` (object)
  - `evaluator_a` (object) — 식별 정보(최소: id 또는 run_id)
  - `evaluator_b` (object)
  - `mean_a` (float)
  - `mean_b` (float)
  - `mean_diff` (float)
  - `se_mode` (`single` | `mean_k` | `expected`)
  - `se` (float)
  - `z_score` (float)
  - `p_value` (float)
  - `ci_95` (object)
    - `low` (float)
    - `high` (float)
  - `is_significant` (bool)
  - `paired` (object)
    - `corr_mean` (float | null) — 질문별 평균의 상관(계산 가능 시)
    - `cov_mean` (float | null)
    - `total_var` / `data_var` / `pred_var` (float | null; K 조건에 따라)

### 5.4 Recommend 결과(`recommendation`)

- `recommendation` (object)
  - `pilot` (object)
    - `N0` (int)
    - `K0` (int)
    - `data_var` (float)
    - `pred_var` (float | null)
  - `objective` (object)
    - `target_mde` (float)
    - `alpha` (float)
    - `power` (float)
  - `cost_model` (object)
    - `unit` (string; 예: “calls”)
    - `evaluators` (int; 기본 2 for A/B)
    - `cost_per_call_usd` (float | null)
  - `candidates` (array of object) — 격자 탐색 요약 테이블
    - `N` (int)
    - `K` (int)
    - `se_est` (float)
    - `mde_est` (float)
    - `cost_calls` (int)
    - `cost_usd` (float | null)
    - `meets_target` (bool)
  - `best` (object | null)
    - `N` (int)
    - `K` (int)
    - `reason` (string)

---

## 6) Artifacts(저장) 설계

### 6.1 저장 위치(권장)

- LENA는 “신뢰도(reliability)” 성격이므로, 기존 `reports/analysis/`, `reports/comparison/`와 구분해 아래를 권장한다.
  - `reports/reliability/lena/` (신규 디렉터리; 구현 시 생성)

### 6.2 파일 네이밍(권장)

- 단일 노이즈 분석
  - `reports/reliability/lena/lena_noise_<RUN_ID or INPUT_ID>.json`
- A/B 비교
  - `reports/reliability/lena/lena_compare_<RUN_A>_<RUN_B>.json`
- (N,K) 추천
  - `reports/reliability/lena/lena_recommend_<RUN_ID or PILOT_ID>.json`

### 6.3 아티팩트 인덱스(선택, 기존 패턴 재사용)

- 파이프라인 분석은 `reports/analysis/artifacts/.../index.json` 패턴을 사용한다.
- LENA 결과도 동일한 “인덱스 + 파일” 패턴이 필요하면,
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`의 패턴을 참고해 재사용한다.
- MVP의 최소 목표는 “JSON 산출물 1개가 UI/리포트에서 직접 소비 가능”이다(인덱스는 선택).

---

## 7) 인터페이스 설계(Backend/CLI 우선 → API → UI)

### 7.1 CLI(먼저 구현) — `evalvault lena ...` (스펙 초안)

- CLI 엔트리/등록 패턴:
  - 엔트리: `src/evalvault/adapters/inbound/cli/app.py`
  - 커맨드 등록: `src/evalvault/adapters/inbound/cli/commands/__init__.py`
  - 신규 커맨드 파일(예정): `src/evalvault/adapters/inbound/cli/commands/lena.py`

#### 7.1.1 `evalvault lena noise`

- 목적: 단일 입력(한 evaluator/run)의 노이즈 분해 및 모드별 SE 산출
- 입력(우선순위):
  1) `--run-id <RUN_ID>`
  2) `--eval-matrix <PATH>` (독립형 파일)
- 옵션:
  - `--metric <METRIC_NAME>` (필수 또는 기본값 정책 필요)
  - `--out <PATH>` (선택; 미지정 시 표준 출력 또는 기본 디렉터리 저장)
  - `--output-dir <DIR>` (선택)
- 출력:
  - `meta` + `noise` + `warnings/errors`

#### 7.1.2 `evalvault lena compare`

- 목적: A/B paired 비교 결과(diff/CI/p-value) + paired noise + 상관(corr_mean)
- 입력:
  1) `--run-a <RUN_ID> --run-b <RUN_ID>`
  2) `--eval-a <PATH> --eval-b <PATH>`
- 옵션:
  - `--metric <METRIC_NAME>`
  - `--se-mode {single,mean_k,expected}` (기본값: `mean_k` 권장; PRD)
  - `--alpha <FLOAT>` (기본값: 0.05)
  - `--out <PATH>` / `--output-dir <DIR>`
- 에러 정책(필수):
  - 질문 매칭 실패 시 **즉시 실패**(실패 수/ID 샘플 포함)

#### 7.1.3 `evalvault lena recommend`

- 목적: 파일럿 결과 기반 목표 MDE/power/alpha를 만족하는 최소 비용 (N,K) 추천
- 입력:
  1) `--pilot <PATH_TO_NOISE_JSON>`
  2) 또는 `--run-id <RUN_ID>` + 내부에서 파일럿 추정 수행(구현 범위에서 결정)
- 옵션:
  - `--target-mde <FLOAT>` (예: 0.01)
  - `--power <FLOAT>` (예: 0.8)
  - `--alpha <FLOAT>` (예: 0.05)
  - `--cost-per-call-usd <FLOAT>` (선택)
  - `--evaluators <INT>` (기본 2: A/B)
  - `--grid-n <RANGE>` / `--grid-k <RANGE>` (선택; 격자 범위 제어)
- 출력:
  - `recommendation.candidates` 테이블 + `best`

> 참고: 기존 `evalvault analyze-compare`는 `src/evalvault/adapters/inbound/cli/commands/analyze.py`에서 제공하며, t-test/MWU 중심이다. LENA 기반 비교는 **별도 커맨드(`evalvault lena compare`)로 제공**해 통계 가정 혼선을 줄인다.

### 7.2 REST API(백엔드/CLI 검증 후) — `/api/v1/lena/*` (스펙 초안)

- FastAPI 앱 엔트리: `src/evalvault/adapters/inbound/api/main.py`
- 라우터 디렉터리: `src/evalvault/adapters/inbound/api/routers/`
- 신규 라우터(예정): `src/evalvault/adapters/inbound/api/routers/lena.py`

권장 엔드포인트:

- `POST /api/v1/lena/noise`
- `POST /api/v1/lena/compare`
- `POST /api/v1/lena/recommend`

요청 형태(권장):

- run 기반을 1차로 단순 지원:
  - `{ "run_id": "...", "metric_name": "...", ... }`
- eval-matrix 업로드/파일 기반은 2차 확장:
  - `{ "eval_matrix": { ... }, ... }` 또는 파일 업로드(추후 결정)

응답 형태:

- 상단의 “출력 스키마(§5)”를 그대로 반환(JSON)

### 7.3 Web UI(마지막) — PRD M07 위젯 3종

> UI는 “기존 점수/리포트”를 대체하지 않고, LENA는 “추가 정보”로 노출한다(롤백 용이).

- 위젯 1: **Diff + CI 바 차트**(A/B 비교)
- 위젯 2: **Noise breakdown**(Data vs Prediction)
- 위젯 3: **(N,K) 추천 + SE/MDE 곡선**(목표 MDE 슬라이더)

---

## 8) 구현 순서(체크리스트) — Backend/CLI → API → UI

### 8.1 1단계: Domain(분석 엔진) 구현

- [ ] `src/evalvault/domain/entities/lena.py` 설계(직렬화 가능한 결과 모델)
  - [ ] `NoiseComponents`(unpaired)
  - [ ] `PairedNoiseComponents`(paired)
  - [ ] `LenaComparisonResult`
  - [ ] `LenaRecommendationResult`
  - [ ] 공통 `meta/warnings/errors` 규약
- [ ] `src/evalvault/domain/services/lena_service.py` 구현
  - [ ] unpaired 노이즈 분해(총분산 분해 + small-K 보정)
  - [ ] paired 노이즈 분해(A vs B, 질문 정렬 강제)
  - [ ] SE 모드 계산을 단일 함수로 중앙화
  - [ ] compare: diff/CI/p-value(기본 z-test)
  - [ ] recommend: 파일럿 기반 격자 탐색 + 비용 함수(기본 calls=N×K×evaluators)

### 8.2 2단계: CLI 구현(최소 기능)

- [ ] `src/evalvault/adapters/inbound/cli/commands/lena.py` 추가(예정)
- [ ] `src/evalvault/adapters/inbound/cli/commands/__init__.py`에 등록(예정)
- [ ] `evalvault lena noise/compare/recommend` 입력/출력 동작 정의
- [ ] 산출물 저장 경로/네이밍 확정(§6) 및 기존 유틸 재사용 검토
- [ ] 에러 정책 반영
  - [ ] 질문 매칭 실패: 명시 오류(조용히 진행 금지)
  - [ ] K 부족: warnings + 제한된 필드/모드 처리

### 8.3 3단계: API 구현(내부 소비)

- [ ] `src/evalvault/adapters/inbound/api/routers/lena.py` 추가(예정)
- [ ] `src/evalvault/adapters/inbound/api/main.py`에 라우터 include(예정)
- [ ] 요청/응답 스키마 확정(§5 기반)
- [ ] Web UI 어댑터 경유 여부 결정
  - 참고: `src/evalvault/adapters/inbound/api/adapter.py`

### 8.4 4단계: Web UI 연동(마지막)

- [ ] 위젯 3종 구현(PRD M07)
- [ ] 모드 토글 UX 고정(`single/mean_k/expected`)
- [ ] 기본 표시 정책: 기존 점수 유지 + LENA는 추가 정보(롤백 가능)

---

## 9) 테스트 계획(필수) — PRD의 “검증 가능한 정의”를 코드로 고정

> 테스트 위치 가이드: `tests/unit`, `tests/integration` (AGENTS.md)

### 9.1 단위 테스트(MVP 필수: PRD 12.1)

- [ ] 분해식 일관성(허용오차 `tol` 정의): `|total - (data + pred)| < tol` (K>1)
- [ ] small-K 보정이 분해 오차를 개선하는지 비교(보정 유/무)
- [ ] SE 모드 관계:
  - [ ] `expected SE ≤ mean_k SE ≤ single SE`
  - [ ] K 증가 시 `mean_k SE` 단조 감소

### 9.2 시뮬레이션 테스트(강력 추천: PRD 12.2)

- [ ] Bernoulli(정답/오답) 생성 모델에서 이론적 SE와 근접
- [ ] (확장 시) bootstrap CI vs 분석식 CI 비교(본 MVP 범위 밖)

### 9.3 통합 테스트(PRD 12.3)

- [ ] run/eval-matrix 입력 → LENA 분석 → JSON 산출물 생성 smoke test
- [ ] paired 비교(Inter/Intra 각각 1개) 시나리오 테스트
- [ ] (UI 단계 이후) API 응답 → UI 표시 smoke test

---

## 10) 인수 기준(Acceptance Criteria)

본 섹션은 `docs/guides/PRD_LENA.md`의 Must Have(M01~M07)와 테스트 요구사항을 **완료 정의(DoD)**로 사용한다.

### 10.1 기능 인수(M01~M07)

- [ ] M01: 입력 스키마/로더가 K 축을 보존한다(질문×반복)
- [ ] M02: 노이즈 분해 + small-K 보정, 분해식 오차 허용범위 충족
- [ ] M03: Paired 분석에서 질문 정렬/매칭 강제, 실패 시 명시 오류
- [ ] M04: diff/CI/p-value/유의성 판단이 `se_mode`에 대해 일관되게 산출
- [ ] M05: SE 모드 3종 제공 및 관계(expected ≤ mean_k ≤ single) 성립
- [ ] M06: 파일럿 기반 (N,K) 추천이 재현 가능하며 비용 함수가 명시됨
- [ ] M07: UI는 백엔드 검증 후 구현(본 문서 순서 준수), 3위젯이 동일 결과를 일관 표시

### 10.2 품질/운영 인수(최소)

- [ ] 입력 전제 위반(K 부족/매칭 실패/스키마 오류) 시 명확한 오류/경고 제공
- [ ] JSON 산출물이 UI/리포트에서 재사용 가능한 구조(meta/results/warnings/errors)를 갖춤
- [ ] 기존 통계 비교(t-test/MWU) 흐름과 혼선 없이 병행 가능
  - 참고: `src/evalvault/adapters/outbound/analysis/statistical_adapter.py`

---

## 11) 롤아웃(배포) 단계

### 11.1 파일럿(내부)

- 목표: 파일럿(N0,K0) 1회로 노이즈 추정치 및 추천(N,K)의 합리성 확인
- 산출물: `reports/reliability/lena/` 하위 JSON(필수)

### 11.2 제한 공개(MVP)

- CLI 제공(`evalvault lena ...`) + API 제공(`/api/v1/lena/*`)
- UI는 “추가 위젯”로 노출, 기존 점수/리포트는 그대로 유지(롤백 가능)

### 11.3 운영/확장 의사결정

- 성공 지표(근거: `docs/guides/PRD_LENA.md`):
  - 결론 뒤집힘 비율 감소
  - 목표 MDE 대비 평가 비용 감소
  - 사용자(엔지니어/리서처) 신뢰 확보
- 확장(Should)은 Phase2로 분리:
  - bootstrap/sign test/all-pairs/FDR 등

---

## 12) 리스크 & 대응(최소)

- seed 미지원/비결정성:
  - 대응: 입력 메타/경고로 “재현성 수준”을 명시(조용히 결과만 출력하지 않음)
- 질문 ID 불일치(매칭 실패):
  - 대응: 강제 실패 + 실패 목록/개수 제공
- K 부족:
  - 대응: pred_var/mean_k 관련 필드 제한 + warnings
- 통계 가정 논쟁:
  - 대응: MVP는 PRD의 fixed-horizon + z-test(정규 근사)로 고정하고, 강건 옵션은 Phase2로 분리

---

## 13) 문서 검증 상태(근거 추적)

- 요구사항/인수 기준: `docs/guides/PRD_LENA.md`
- 통합 관점(참고만): `docs/guides/LENA_RAGAS_CALIBRATION_DEV_PLAN.md`
- 본 문서는 **현재 미구현 상태**를 전제로 하며, “생성/수정 예정 파일”과 “계약 초안”을 제공한다.

---

## 14) API 요청/응답 샘플(초안)

> 실제 구현 시 요청/응답 스키마는 `docs/guides/PRD_LENA.md`와 본 문서의 §5를 기준으로 확정한다.

### 14.1 `POST /api/v1/lena/noise`

**요청(JSON)**
```json
{
  "run_id": "RUN_123",
  "metric_name": "faithfulness"
}
```

**응답(JSON)**
```json
{
  "meta": {
    "schema_version": "v1",
    "created_at": "2026-01-13T12:00:00Z",
    "source": {
      "mode": "run_id",
      "run_id": "RUN_123",
      "dataset_name": "insurance-qa",
      "metric_name": "faithfulness"
    },
    "params": {
      "se_mode": "mean_k"
    },
    "assumptions": [
      "question-level mean is the unit"
    ],
    "warnings": []
  },
  "noise": {
    "N": 120,
    "K": 3,
    "total_var": 0.0142,
    "data_var": 0.0101,
    "pred_var": 0.0041,
    "se": {
      "single": 0.028,
      "mean_k": 0.018,
      "expected": 0.015
    }
  }
}
```

### 14.2 `POST /api/v1/lena/compare`

**요청(JSON)**
```json
{
  "run_id_a": "RUN_A",
  "run_id_b": "RUN_B",
  "metric_name": "faithfulness",
  "se_mode": "mean_k",
  "alpha": 0.05
}
```

**응답(JSON)**
```json
{
  "meta": {
    "schema_version": "v1",
    "created_at": "2026-01-13T12:10:00Z",
    "source": {
      "mode": "run_id",
      "run_id_a": "RUN_A",
      "run_id_b": "RUN_B",
      "dataset_name": "insurance-qa",
      "metric_name": "faithfulness"
    },
    "params": {
      "se_mode": "mean_k",
      "alpha": 0.05
    },
    "assumptions": [
      "paired by question_id"
    ],
    "warnings": []
  },
  "comparison": {
    "evaluator_a": {"run_id": "RUN_A"},
    "evaluator_b": {"run_id": "RUN_B"},
    "mean_a": 0.76,
    "mean_b": 0.79,
    "mean_diff": 0.03,
    "se_mode": "mean_k",
    "se": 0.012,
    "z_score": 2.50,
    "p_value": 0.0124,
    "ci_95": {"low": 0.006, "high": 0.054},
    "is_significant": true,
    "paired": {
      "corr_mean": 0.41,
      "cov_mean": 0.0021,
      "total_var": 0.013,
      "data_var": 0.009,
      "pred_var": 0.004
    }
  }
}
```

### 14.3 `POST /api/v1/lena/recommend`

**요청(JSON)**
```json
{
  "pilot": {
    "run_id": "RUN_123",
    "metric_name": "faithfulness",
    "N0": 120,
    "K0": 3,
    "data_var": 0.0101,
    "pred_var": 0.0041
  },
  "objective": {
    "target_mde": 0.01,
    "alpha": 0.05,
    "power": 0.8
  },
  "cost_model": {
    "evaluators": 2,
    "cost_per_call_usd": 0.002
  }
}
```

**응답(JSON)**
```json
{
  "meta": {
    "schema_version": "v1",
    "created_at": "2026-01-13T12:20:00Z",
    "source": {
      "mode": "run_id",
      "run_id": "RUN_123",
      "metric_name": "faithfulness"
    },
    "params": {
      "target_mde": 0.01,
      "alpha": 0.05,
      "power": 0.8
    },
    "assumptions": [
      "cost = N*K*evaluators"
    ],
    "warnings": []
  },
  "recommendation": {
    "pilot": {"N0": 120, "K0": 3, "data_var": 0.0101, "pred_var": 0.0041},
    "objective": {"target_mde": 0.01, "alpha": 0.05, "power": 0.8},
    "cost_model": {"unit": "calls", "evaluators": 2, "cost_per_call_usd": 0.002},
    "candidates": [
      {"N": 160, "K": 3, "se_est": 0.014, "mde_est": 0.009, "cost_calls": 960, "cost_usd": 1.92, "meets_target": true},
      {"N": 120, "K": 4, "se_est": 0.015, "mde_est": 0.010, "cost_calls": 960, "cost_usd": 1.92, "meets_target": true}
    ],
    "best": {"N": 160, "K": 3, "reason": "lowest cost meeting target"}
  }
}
```

---

## 15) JSON 스키마 예시(요약)

> JSON Schema 문법은 간략화했고, 구현 시 정확한 타입/필수 필드는 코드에서 확정한다.

### 15.1 Noise 결과 스키마
```json
{
  "meta": "object",
  "noise": {
    "N": "int",
    "K": "int",
    "total_var": "float",
    "data_var": "float",
    "pred_var": "float|null",
    "se": {
      "single": "float",
      "mean_k": "float|null",
      "expected": "float"
    }
  },
  "warnings": "string[]",
  "errors": "object[]"
}
```

### 15.2 Compare 결과 스키마
```json
{
  "meta": "object",
  "comparison": {
    "mean_a": "float",
    "mean_b": "float",
    "mean_diff": "float",
    "se_mode": "string",
    "se": "float",
    "z_score": "float",
    "p_value": "float",
    "ci_95": {"low": "float", "high": "float"},
    "is_significant": "bool",
    "paired": {
      "corr_mean": "float|null",
      "cov_mean": "float|null",
      "total_var": "float|null",
      "data_var": "float|null",
      "pred_var": "float|null"
    }
  }
}
```

### 15.3 Recommend 결과 스키마
```json
{
  "meta": "object",
  "recommendation": {
    "pilot": {"N0": "int", "K0": "int", "data_var": "float", "pred_var": "float|null"},
    "objective": {"target_mde": "float", "alpha": "float", "power": "float"},
    "cost_model": {"evaluators": "int", "cost_per_call_usd": "float|null"},
    "candidates": "array",
    "best": "object|null"
  }
}
```

---

## 16) CLI 사용 예시(초안)

> 실제 커맨드/옵션명은 `evalvault lena` 구현 시 확정한다.

### 16.1 Noise
```
evalvault lena noise --run-id RUN_123 --metric faithfulness --out reports/reliability/lena/lena_noise_RUN_123.json
```

### 16.2 Compare
```
evalvault lena compare --run-a RUN_A --run-b RUN_B --metric faithfulness --se-mode mean_k --alpha 0.05 --out reports/reliability/lena/lena_compare_RUN_A_RUN_B.json
```

### 16.3 Recommend
```
evalvault lena recommend --pilot reports/reliability/lena/lena_noise_RUN_123.json --target-mde 0.01 --power 0.8 --alpha 0.05 --cost-per-call-usd 0.002
```

---

## 17) EvalMatrix 입력 포맷(초안)

> 독립형 실행/재현성을 위해 최소한 아래 구조를 지원한다. 실제 포맷은 JSONL/CSV/JSON 중 하나로 확정한다.

### 17.1 JSON 예시(권장)
```json
{
  "schema_version": "v1",
  "metric_name": "faithfulness",
  "question_ids": ["q1", "q2", "q3"],
  "replicate_ids": ["k1", "k2", "k3"],
  "scores": [
    [0.7, 0.8, 0.75],
    [0.6, 0.62, 0.58],
    [0.9, 0.88, 0.91]
  ]
}
```

### 17.2 CSV 예시(대안)

```
question_id,k1,k2,k3
q1,0.70,0.80,0.75
q2,0.60,0.62,0.58
q3,0.90,0.88,0.91
```

### 17.3 검증 규칙(필수)

- `scores`는 **N×K 행렬**이어야 한다.
- `question_ids` 길이 = N, `replicate_ids` 길이 = K.
- NaN/비숫자 값은 입력 오류로 처리한다.
- `K <= 1`일 때는 pred_var/mean_k 관련 필드를 제한하거나 warnings를 포함한다.
