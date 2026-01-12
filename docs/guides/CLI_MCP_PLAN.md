# EvalVault CLI → MCP 이식 계획 (Living Document)

> Audience: CLI/플랫폼 개발자
> Purpose: CLI 기능을 MCP 도구로 안전하게 이식하고 운영하기 위한 기준 정리
> Last Updated: 2026-01-12

---

## 1. 목적 및 범위
- **목적**: EvalVault CLI의 핵심 기능을 MCP Tool로 노출하여 LLM 기반 자동화가 안정적으로 작동하도록 합니다.
- **범위**: 평가 실행·분석·비교·조회 등 **사용 빈도와 자동화 가치가 높은 CLI 기능**부터 단계적으로 이식합니다.

## 2. 현황 요약
- EvalVault는 Typer 기반 CLI로 평가/분석/보고서/트레이싱 연동을 제공하고 있습니다.
- 동일 워크플로를 Web UI로 이식하는 작업이 병행 중입니다.
- MCP 이식은 **CLI와 동등한 결과·재현성**을 유지하는 것이 핵심입니다.

## 3. MCP 노출 후보 (초안)
> 실제 목록은 CLI 변경과 함께 수시 업데이트합니다.

### 3.1 실행/평가 계열
- `run_evaluation`: 데이터셋 평가 실행 (기존 `evalvault run`에 상응)
- `analyze_compare`: A/B 비교 분석 (기존 `evalvault analyze-compare`에 상응)

### 3.2 조회/요약 계열
- `list_runs` / `get_run_summary`: 실행 결과 조회 및 요약
- `get_artifacts`: 아티팩트/보고서 경로 조회

### 3.3 관리/설정 계열
- `get_profiles`: 사용 가능한 프로필 목록 조회
- `validate_dataset`: 데이터셋 포맷 검사 및 전처리 리포트

## 4. MCP 인터페이스 설계 원칙
- **명확한 입력 스키마**: CLI 옵션을 1:1 매핑하되, 필수·선택을 명확히 분리합니다.
- **구조화된 출력**: `run_id`, `metrics`, `thresholds`, `artifacts`를 JSON으로 반환합니다.
- **멱등성**: 동일 입력에 대해 동일 결과가 나오도록 실행 환경을 고정합니다.

## 5. 보안/프로필/환경변수 정책
- **프로필 기준**: `EVALVAULT_PROFILE`를 기본값으로 사용하며 MCP 호출 시 override 가능.
- **환경변수**: LLM API 키 등 민감 정보는 MCP 서버 환경에서만 읽고 응답에 포함하지 않습니다.
- **파일 접근 범위**: MCP 도구는 `data/`, `tests/fixtures/`, `reports/` 중심으로 제한합니다.

## 6. 오류 처리/로깅/재현성
- **오류 규격화**: exit code, error type, message를 구조화된 필드로 반환합니다.
- **재현성 메타데이터**: 프로필, 모델, ragas_config, prompt_overrides, dataset_preprocess 결과를 기록합니다.
- **실패 시 폴백**: CLI와 동일한 방어 로직(예: NaN 처리, 폴백 메트릭)을 그대로 사용합니다.

## 7. A2A / MAS 설계 (선택적, 조건부 적용)

### 7.1 역할 분리 (A2A 기본 토폴로지)
- **Orchestrator Agent**: 요청 해석·도구 선택·리스크 관리·전체 진행/취소 제어
- **Preprocess Agent**: 데이터 전처리(정규화, 결측 보완, 규격 검사) 전담
- **Analysis Agent**: 결과 요약·비교·리포트 생성 전담

> **원칙**: 역할을 분리하되, *작업 단위가 충분히 크고 반복적일 때만* 분산합니다.

### 7.2 메모리 계층 설계 (Hierarchical Memory)
- **Short-term (작업 메모리)**: 현재 실행 파라미터, run_id, 오류 상태 등 세션 단위 데이터
- **Action Memory (행동 기록)**: MCP 호출 기록, 입력/출력 스냅샷, 재시도 히스토리
- **Long-term (지식/정책)**: 프로필 정책, 안전 규칙, 예외 처리 규칙, 운영 가이드 요약

> **원칙**: 장기 메모리는 룰/정책 중심으로 유지하고, 개인/민감 정보는 저장하지 않습니다.

### 7.3 적용 게이트 (증거 기반)
- **적용 조건**: 현재 기술 수준과 타 서비스 사례를 고려할 때 **업무 시간 30% 이상 감소**가 현실적으로 기대되는 경우에만 도입합니다.
- **근거 부족 시 보류**: MAS/A2A는 운영 복잡도를 증가시키므로, 정량적 근거가 부족하면 단일 에이전트 구조를 유지합니다.

### 7.4 과잉 엔지니어링 판단 기준
- **오버헤드 > 이득**: 오케스트레이션/동기화 비용이 절감 시간보다 큰 경우
- **작업 크기 불충분**: 평균 실행 시간이 짧고 병렬화 이득이 미미한 경우
- **운영 리스크 증가**: 관측성·디버깅 난이도 상승으로 장애 대응 시간이 늘어나는 경우

### 7.5 PoC 설계 (적용 전 필수)
- **대상 워크플로(최소 1~2개)**:
  - Use-case 1: 전체 RAGAS 지표로 데이터셋 평가 → 자동 분석 → 보고서 위치 반환
  - Use-case 2: Use-case 1 결과에 Domain Memory 반영 → 동일 데이터셋/지표 재평가 → A/B 비교 보고서 생성
- **에이전트 구성**: Orchestrator 1 + Preprocess 1 + Analysis 1 (총 3개 고정)
- **성공 기준**:
  - 평균 처리 시간 **30% 이상 감소**
  - 실패/재시도 비율 **유의미한 증가 없음**
  - 디버깅/재현 시간 **증가 없음**
- **측정 지표**:
  - end-to-end 시간, 에이전트 호출 수, 재시도 횟수, 오류 유형 분포
  - 동일 입력 대비 결과 재현성(메트릭 편차)
- **결정 규칙**: 기준 미달 시 **단일 에이전트 구조 유지**

### 7.6 PoC 입력/출력 스키마 (초안)

#### Use-case 1: 전체 RAGAS 평가 + 자동 분석
- **입력**
  - `dataset_path` (string, required)
  - `metrics` (array<string>, required) — 기본값: RAGAS 전체
  - `profile` (string, optional)
  - `db_path` (string, optional)
  - `auto_analyze` (boolean, default true)
- **출력**
  - `run_id` (string)
  - `metrics` (object) — 요약 점수 맵
  - `artifacts` (object)
    - `analysis_report_path` (string)
    - `analysis_artifacts_dir` (string)
  - `errors` (array<object>, optional)

#### 에러 객체 스키마 (공통)
- `code` (string) — 내부 에러 코드
- `message` (string) — 사용자에게 노출할 요약 메시지
- `details` (object, optional) — 원인/스택/외부 서비스 응답 요약
- `retryable` (boolean) — 재시도 가능 여부
- `stage` (string) — `preprocess` | `evaluate` | `analyze` | `compare`

#### Use-case 2: Domain Memory 반영 + 재평가 + A/B 비교
- **입력**
  - `dataset_path` (string, required)
  - `metrics` (array<string>, required)
  - `profile` (string, optional)
  - `db_path` (string, optional)
  - `memory_db_path` (string, optional)
  - `baseline_run_id` (string, optional)
- **출력**
  - `baseline_run_id` (string)
  - `candidate_run_id` (string)
  - `comparison_report_path` (string)
  - `metrics_delta` (object) — 평균/주요 지표 증감 요약
    - `avg` (object) — {metric_name: delta}
    - `by_metric` (object) — {metric_name: delta}
    - `notes` (array<string>, optional) — 주의/해석 문구
  - `errors` (array<object>, optional)

### 7.7 샘플 MCP 응답 (예시)

#### Use-case 1 응답 예시
```json
{
  "run_id": "run_20260112_0001",
  "metrics": {
    "faithfulness": 0.82,
    "answer_relevancy": 0.74,
    "context_precision": 0.67
  },
  "artifacts": {
    "analysis_report_path": "reports/analysis/analysis_run_20260112_0001.md",
    "analysis_artifacts_dir": "reports/analysis/artifacts/analysis_run_20260112_0001"
  },
  "errors": []
}
```

#### Use-case 2 응답 예시
```json
{
  "baseline_run_id": "run_20260112_0001",
  "candidate_run_id": "run_20260112_0002",
  "comparison_report_path": "reports/comparison/comparison_run_20260112_0001_run_20260112_0002.md",
  "metrics_delta": {
    "avg": {
      "faithfulness": 0.03,
      "answer_relevancy": 0.05
    },
    "by_metric": {
      "faithfulness": 0.03,
      "answer_relevancy": 0.05,
      "context_precision": -0.01
    },
    "notes": ["answer_relevancy 개선, context_precision 소폭 하락"]
  },
  "errors": []
}
```

#### 에러 응답 예시
```json
{
  "run_id": "run_20260112_0003",
  "metrics": {},
  "artifacts": {},
  "errors": [
    {
      "code": "EVAL_DATASET_INVALID",
      "message": "dataset_path 포맷이 올바르지 않습니다.",
      "details": {"missing_fields": ["question", "contexts"]},
      "retryable": false,
      "stage": "preprocess"
    }
  ]
}
```

### 7.8 외부 근거 (현재 시점)
- **A2A/오케스트레이션 패턴**
  - https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
  - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
  - https://docs.cloud.google.com/architecture/multiagent-ai-system
- **메모리 계층**
  - https://docs.letta.com/concepts/memgpt/
  - https://arxiv.org/abs/2507.22925
- **벤치마크/검증**
  - https://arxiv.org/abs/2503.01935
  - https://arxiv.org/abs/2502.18836

> **주의**: 공개 자료에서 **30%+ 생산성 향상에 대한 직접적인 정량 근거는 부족**합니다. 따라서 PoC 또는 내부 벤치마크로 효과가 확인될 때만 확장합니다.

## 8. 단계적 롤아웃

### Phase 0 — 설계 확정
- [ ] MCP Tool 후보 목록 확정
- [ ] 입력/출력 스키마 초안 확정
- [ ] 보안/환경변수 처리 기준 확정
- **Owner**: TBD
- **Target Date**: TBD

### Phase 1 — 읽기 전용 도구
- [ ] `list_runs`, `get_run_summary`, `get_artifacts` 제공
- [ ] MCP 응답 스키마 안정화
- [ ] 에러/로깅 포맷 확정
- **Owner**: TBD
- **Target Date**: TBD

### Phase 2 — 실행 도구
- [ ] `run_evaluation` 도입
- [ ] `analyze_compare` 도입
- [ ] 동일 입력 대비 재현성 검증
- **Owner**: TBD
- **Target Date**: TBD

### Phase 3 — 확장/최적화
- [ ] 추가 CLI 기능 확장
- [ ] 장시간 실행/대규모 데이터 처리 최적화
- [ ] 보안 점검 및 운영 가이드 배포
- **Owner**: TBD
- **Target Date**: TBD

## 9. 업데이트 규칙
- CLI 명령/옵션 추가 시 **본 문서를 먼저 갱신**합니다.
- MCP 도구에 영향을 주는 변경은 반드시 변경 사유와 대응을 기록합니다.

## 10. 참고 및 연결 문서
- `docs/INDEX.md` — 문서 허브
- `docs/guides/USER_GUIDE.md` — CLI 사용/운영 가이드
- `docs/guides/DEV_GUIDE.md` — 개발/테스트 루틴

---

> 이 문서는 진행 상황에 따라 지속 업데이트합니다.
