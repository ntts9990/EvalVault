# 보험 도메인 요약 평가(옵션) 병렬 작업 계획서

> **작성일**: 2026-01-07
> **목적**: 보험 RAG 시스템의 요약 평가를 옵션으로 분리하고, 사용자 노출 기준의 최소 필수 지표(3종)를 병렬로 통합한다.

---

## 1) 결정사항 요약 (사용자 확인 반영)

- 요약 평가는 **옵션**으로 분리 (기본 off, 명시 실행 시만 동작).
- 언어 비중: **ko 92.5% / en 7.5%**, **한 문서 안에 혼용 가능**.
- 평가 LLM: **현재 선택한 LLM 그대로 사용** (별도 모델 없음).
- Summary Faithfulness: **LLM Judge 우선**.
- Summarization Score는 Summary Faithfulness와 **별도 측정**(서로 다른 목적).
- 요약 평가용 테스트셋: **개발 확인용 최소 케이스**로 먼저 구성.
- 사용자 노출 가정: **보수적 경고/플래그 기준**을 적용.
- DB 스키마: **신규 메트릭명 추가만으로 저장 가능**(마이그레이션 불필요).
- 성능/재현성: `docs/guides/RAGAS_PERFORMANCE_TUNING.md` 및
  `docs/internal/reports/TEMPERATURE_SEED_ANALYSIS.md`의 권고를 **문서/운영 가이드로 반영**.

---

## 2) 범위 / 비범위 (YAGNI)

### 포함 (필수)
- SummaryScore, Summary Faithfulness, 엔티티 보존(보험 핵심) 3종 지표.
- 요약 평가 옵션화(플래그/프리셋) + 결과 리포팅.
- 혼용 언어 대응(언어 감지/메타 기록, 프롬프트 가이드 포함).
- 최소 테스트 fixture + 핵심 단위/통합 테스트.

### 제외 (현재 보류)
- 운영 실시간 게이팅(상담원 전환 포함).
- 대규모 요약 전용 테스트셋 구축.
- 번역 기반 평가(혼용 문서에서는 왜곡 가능).
- CLIR 전용 평가 파이프라인(요약과 직접 연관 낮음).

---

## 3) 핵심 설계 포인트

### 3.1 메트릭 정의 (요약)
- **summary_score**: RAGAS SummaryScore, keyphrase-QA 기반 정보 보존 + 간결성(옵션).
- **summary_faithfulness**: LLM Judge 기반, 요약 내 주장 vs 원문 근거 일치.
- **entity_preservation**: 보험 핵심 엔티티(금액/기간/비율/면책/조건) 보존율.

### 3.2 SummaryScore vs Summary Faithfulness (명확화)
- **SummaryScore**는 “중요 정보 보존/간결성” 중심.
- **Summary Faithfulness**는 “원문에 없는 주장/왜곡” 차단 중심.
- 따라서 **별도 지표로 유지**하며, 둘 다 충족되어야 안전.

### 3.3 혼용 언어 대응 원칙
- 문서/컨텍스트는 **언어 혼용 허용**.
- 평가 시 **번역 없이 원문 그대로** Judge 수행.
- 간단 언어 비율 추정(ko/en) 후 **메타로 기록**, 보고서에서 참고.

### 3.3.1 Summary Faithfulness Judge 가이드 (요약)
- 판단 기준: **원문에 없는 주장/조건/숫자 추가는 Fail**.
- 혼용 언어 처리: **의미 동치 허용**, 번역 필요 시 설명에만 사용.
- 보험 리스크 우선: **면책/제외/조건/금액/기간/비율** 불일치 시 즉시 Fail.
- 출력 형식: `supported | unsupported` + 한 줄 사유(원문 근거 유무).

### 3.4 사용자 노출 가정 (보수 기준, 확정)
- 초기 경고 기준(확정):
  | Metric | 기준 | 의미 |
  | --- | --- | --- |
  | `summary_faithfulness` | ≥ 0.90 | 원문 근거 없는 주장 차단 |
  | `summary_score` | ≥ 0.85 | 핵심 정보 보존/간결성 |
  | `entity_preservation` | ≥ 0.90 | 보험 핵심 엔티티 보존 |
- **3개 중 하나라도 미달 시 경고 플래그**(게이팅은 하지 않음).
- 사용자 노출 전제이므로 **경고 플래그가 있으면 요약 제공 제한**을 우선 고려.

**적용 방식 (권장)**
- 데이터셋 `thresholds`에 아래를 명시해 pass/fail을 경고 기준으로 사용:
```json
{
  "thresholds": {
    "summary_faithfulness": 0.9,
    "summary_score": 0.85,
    "entity_preservation": 0.9
  }
}
```
- 필요 시 CLI에서 `--threshold`로 임시 오버라이드(예: `summary_score:0.85`).

### 3.5 DB 스키마 영향
- `metric_scores.metric_name`이 TEXT이므로 **새 메트릭명 추가만으로 저장 가능**.
- 별도 마이그레이션 없이 적용하되, 혼용 언어 비율은 **리포트 계산**으로 처리(필요 시 run metadata에 추가).

### 3.6 성능/재현성 고려 (문서 기반 적용)
- **성능 튜닝**: 요약 평가는 3종 메트릭만 사용하고 `--parallel/--batch-size`로 처리량 확보.
- **컨텍스트 크기**: 요약 전용 데이터셋은 context 길이/개수를 억제(토큰 폭증 방지).
- **재현성**: Temperature=0.0은 RAGAS 공식 권장이 아니므로 **강제하지 않음**.
- **운영 가이드**: 변동성은 다회 실행 평균으로 흡수(문서에 명시).

---

## 4) 병렬 작업 구조 (에이전트별)

### 전체 트랙 요약

| Agent | 트랙 | 난이도 | 핵심 역할 | 의존성 |
|------|------|--------|----------|--------|
| A | Core Metrics | 높음 | RAGAS 통합/메트릭 맵핑 | 없음 |
| B | Entity & Faithfulness | 중~높음 | 엔티티 보존 + 요약 충실도 방식 확정 | A |
| C | CLI/UX/Reporting | 중간 | 옵션 플래그, 리포트/웹 표시 | A, B |
| D | Fixtures & Tests & Docs | 낮음 | 최소 데이터셋/테스트/문서 보강 | A, B |

> **경량 작업 집중**: Agent D에 fixture/테스트/문서 관련 업무를 몰아서 병렬 충돌을 최소화.

**선행 의존성 요약**
- A: 시작점
- B: A의 메트릭 명세 고정 후
- C: A+B 결과 반영 필요
- D: 스켈레톤은 병렬 가능, **메트릭 명세 확정 후 고정**

---

## 5) 에이전트별 상세 계획

### Agent A — Core Metrics (난이도 높음)

**목표**: 요약 지표를 RAGAS 평가 파이프라인에 통합하고, 옵션 실행을 위한 최소 스펙 확정.

**작업 범위**
- `src/evalvault/domain/services/evaluator.py`
- `src/evalvault/domain/entities/result.py`
- `src/evalvault/adapters/inbound/cli/commands/method.py`
- `src/evalvault/adapters/inbound/cli/commands/run.py`

**주요 작업**
1. RAGAS SummaryScore 통합
   - `METRIC_MAP`에 `summary_score` 등록.
   - `METRIC_ARGS`에 `reference_contexts` 매핑 추가.
   - `all_args` 구성 시 `reference_contexts = retrieved_contexts` 제공.
2. Summary Faithfulness 처리 방식 결정
   - 최소 변경안: `summary_faithfulness`를 **RAGAS Faithfulness 래핑**으로 등록.
   - 래퍼 클래스에서 `name`만 변경해 **결과 키 분리**.
3. 메트릭 노출 범위 확장
   - CLI 옵션/메트릭 목록에 `summary_score`, `summary_faithfulness`, `entity_preservation` 추가.
4. 기본 임계값/옵션 경고 기준 정의
   - user-exposed 기준에 맞는 기본 임계값을 문서화(코드 기본값은 0.7 유지 가능).

**산출물**
- 요약 메트릭이 `RagasEvaluator`에서 정상 평가되는 코드.
- CLI에서 `--metrics summary_score,summary_faithfulness` 실행 가능.

**테스트**
- `tests/unit/test_evaluator.py`에 메트릭 맵 등록 테스트 추가.
- `tests/unit/test_cli.py`에 메트릭 옵션 파싱 테스트 추가.

---

### Agent B — Entity & Faithfulness (난이도 중~높음)

**목표**: 보험 요약의 핵심 엔티티 보존 지표와 요약 충실도 정책 확정.

**작업 범위**
- `src/evalvault/domain/metrics/` (신규 메트릭)
- `src/evalvault/domain/services/dataset_preprocessor.py` (필요 시)
- `src/evalvault/config/settings.py` (메타 옵션 추가 시)

**주요 작업**
1. 엔티티 보존 메트릭 설계
   - 보험 핵심 엔티티: 금액, 비율, 기간, 면책/제외 조건, 지급 조건.
   - 정규식 + 키워드 기반 최소 버전 구현(LLM 없이).
2. 혼용 언어 대응
   - 숫자/기호 기반 엔티티 우선 추출 → 언어 혼용 영향 최소화.
   - `metadata`에 `language_mix`(ko/en 비율) 기록 필요 시 추가.
3. Summary Faithfulness 정책 문서화
   - LLM Judge가 **원문 근거 위주**로 판단하도록 프롬프트 지침 작성(영/한 혼용 대응).

**산출물**
- `entity_preservation` 메트릭 1차 버전.
- 혼용 문서 기준의 최소 정책 가이드(프롬프트/판정 기준).

**테스트**
- 단위 테스트: 엔티티 추출 및 보존율 계산.

---

### Agent C — CLI/UX/Reporting (난이도 중간)

**목표**: 요약 평가 옵션 실행 경로와 사용자 노출 경고 메시지를 제공.

**작업 범위**
- `src/evalvault/adapters/inbound/cli/commands/run.py`
- `src/evalvault/adapters/inbound/cli/utils/presets.py`
- `src/evalvault/adapters/inbound/web/components/metrics.py`
- `src/evalvault/adapters/inbound/web/adapter.py`
- `src/evalvault/adapters/outbound/report/llm_report_generator.py`

**주요 작업**
1. 요약 평가 옵션 추가
   - 예: `--summary` 또는 `--task summarization` (기본 off).
   - preset에 요약 전용 메트릭 묶음 추가.
2. 리포트 표시 보강
   - 요약 메트릭 설명/경고 문구 추가.
   - 사용자 노출 가정 시 Fail 경고 강조.
   - 성능/재현성 주의사항 링크 또는 요약 문구 추가.
3. 웹 UI 메트릭 표기/라벨 추가.

**산출물**
- 요약 평가 옵션 플래그 및 프리셋 적용.
- 리포트/웹에서 요약 메트릭 표시.

**테스트**
- CLI 통합 테스트(옵션 파싱 + metrics 전달 확인).

---

### Agent D — Fixtures & Tests & Docs (난이도 낮음)

**목표**: 최소 요약 테스트셋과 관련 문서를 준비하여 빠른 개발 검증 가능하게 한다.

**작업 범위**
- `tests/fixtures/` 또는 `tests/fixtures/e2e/`
- `tests/unit/`, `tests/integration/`
- `docs/internal/plans/` (관련 문서 업데이트)

**주요 작업**
1. 최소 요약 fixture 생성
   - 6~8 케이스, 아래 요소 모두 포함:
     - ko-only, en-only, ko+en 혼용
     - 금액/비율/기간/면책 문장 포함
     - 요약 내 누락/왜곡 사례 1~2개 포함
2. 테스트 케이스 스펙 확정
   - 필수 필드: `id`, `question`, `answer(요약)`, `contexts`, `ground_truth(optional)`
3. 문서 업데이트
   - 요약 평가 실행 예시 및 주의사항 간단 기록.
   - 성능 튜닝/재현성 문서 링크 추가.

**산출물**
- 최소 fixture 파일 1개.
- 테스트 최소 셋(단위 1~2개, 통합 1개).

---

## 6) 최소 Fixture 스펙 (확정)

- 파일 위치: `tests/fixtures/e2e/summary_eval_minimal.json`
- 케이스 구성(**8개 고정**, 정상 5 / 실패 3):
  1. ko-only + 면책 조건 포함 (정상)
  2. ko-only + 금액/비율 포함 (정상)
  3. en-only + 기간/조건 포함 (정상)
  4. ko+en **동일 문맥 내 혼용** + 핵심 조항 포함 (정상)
  5. ko+en **문맥 간 혼용** + 지급 조건 포함 (정상)
  6. ko-only + 요약 **면책 누락** (의도적 실패)
  7. ko-only + 요약 **조건 반전/왜곡** (의도적 실패)
  8. en-only + 요약 **환각 추가** (의도적 실패)
- 필드 기준:
  - `question`: 요약 요청 문장(ko/en)
  - `answer`: 요약 결과(정상/실패 포함)
  - `contexts`: 2~3개 chunk, 혼용 케이스는 **하나의 chunk에 ko+en 동시 포함**
  - `ground_truth`: 비워도 됨(요약 전용), 필요 시 1개만 샘플로 채움

---

## 6.1) 실행 예시 및 주의사항 (옵션 도입 후)

- 실행 예시:
  - `uv run evalvault run tests/fixtures/e2e/summary_eval_minimal.json --metrics summary_score,summary_faithfulness,entity_preservation --summary`
- 주의사항:
  - 혼용 문서는 번역 없이 원문 그대로 판정하도록 가이드한다.
  - 성능/재현성 가이드는 `docs/guides/RAGAS_PERFORMANCE_TUNING.md`와
    `docs/internal/reports/TEMPERATURE_SEED_ANALYSIS.md`를 참고한다.

---

## 7) 통합 순서 (의존성)

1. **Agent A**: 메트릭 맵/평가 파이프라인 통합
2. **Agent B**: 엔티티 보존/요약 정책 확정
3. **Agent C**: CLI/리포트 반영
4. **Agent D**: fixture/테스트/문서 보강 (A/B 명세 확정 후 고정)
5. 통합 테스트 및 기준값 조정

---

## 8) 리스크 & 대응

- **RAGAS SummaryScore 입력 스키마 불일치**
  → `reference_contexts` 매핑 확인, RAGAS 버전별 분기 처리 필요.
- **혼용 언어로 인한 Judge 불안정**
  → 프롬프트에 “혼용 허용” 명시, 엔티티 기반 보정 사용.
- **요약 평가가 사용자 노출에 비해 느슨함**
  → 초기에는 경고 플래그 강화 + 샘플 리뷰 비중 높임.

---

## 9) 완료 기준 (Exit Criteria)

- 요약 평가가 옵션으로 실행 가능.
- 3종 지표가 산출되고 리포트/웹에 노출됨.
- 최소 fixture로 단위/통합 테스트 통과.
- 혼용 언어 케이스에서 기본 동작 확인 완료.
