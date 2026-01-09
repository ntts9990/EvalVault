# Web UI 검증 방법 (Analysis Lab 중심)

> 작성일: 2026-01-09
> 상태: v0.1 (초안)
> 목적: Web UI의 실행/결과 표출이 CLI와 일치하는지 체계적으로 검증한다.

## 1) 범위

- Web UI 전반 + 특히 Analysis Lab 실행/결과 영역.
- API 통신, 결과 구조 매핑, 에러 복원력, 성능/가시성까지 포함.

## 2) 기본 원칙

- **CLI와 동일한 의도/파라미터/결과 구조**를 유지한다.
- **실행 실패/부분 실패/LLM 오류**를 반드시 재현한다.
- UI는 **결과의 위치와 의미가 명확**해야 한다.
- 자동화(E2E/Contract) + 수동 점검을 함께 운영한다.

## 3) 검증 레이어

1. **Contract (API 응답 스키마)**
   - `pipeline/analyze`, `pipeline/results`, `runs/*`의 핵심 필드 타입/키를 고정한다.
   - 파싱 실패 시 즉시 UI에서 경고/대체 출력이 가능해야 한다.
   - 계약 테스트 위치: `tests/integration/test_pipeline_api_contracts.py`
2. **Integration (실제 API + UI)**
   - 로컬 API/프론트를 동시에 켜고 실제 요청 흐름을 확인한다.
3. **E2E (Playwright)**
   - Mock 응답 기반으로 안정적으로 동작을 고정한다.
   - 시나리오 정의는 `docs/internal/reference/WEB_UI_E2E_SCENARIOS.md`를 따른다.
4. **Non-functional**
   - 긴 보고서/다수 노드 결과에서 렌더링/스크롤 성능 확인.
   - 상태 배지/배너가 과도하게 흔들리지 않는지 확인.

## 4) Analysis Lab 핵심 체크리스트

### 4.1 실행 전

- API 연결 상태 배지가 정상 표시되는가.
- Intent 목록/Run 목록/저장된 결과가 로드되는가.
- Run 미선택 시 “샘플 데이터” 안내가 표시되는가.

### 4.2 실행 요청

- Intent 선택 시 `pipeline/analyze`에 예상 파라미터가 전달되는가.
- Run 선택/미선택/벤치마크 옵션별로 요청이 달라지는가.
- LLM 보고서 옵션 on/off가 반영되는가.

### 4.3 실행 결과 표출

- 결과 요약 카드: **분석 유형/처리 시간/상태/보고서 상태**가 표시되는가.
- 결과 출력 영역: `final_output`의 보고서가 명확히 노출되는가.
- 노드 상세 출력: `node_results`가 상태/오류/출력으로 구분되는가.
- 저장 메타데이터/저장 동작이 정상 동작하는가.

### 4.4 에러/대체 처리

- API 연결 실패 시 배지/메시지가 표시되는가.
- LLM 오류 시 대체 보고서 사용 배너가 표시되는가.
- 부분 노드 실패가 결과 요약과 노드 상세에 드러나는가.

## 5) 결과 구조 매핑 (Analysis Lab 기준)

| API 필드 | UI 영역 | 기대 동작 |
| --- | --- | --- |
| `intent` | 결과 카드 “분석 유형” | Intent 라벨로 표시 |
| `duration_ms` | 결과 카드 “처리 시간” | 포맷된 시간 표시 |
| `is_complete` | 결과 카드 “상태” | 완료/미완료 배지 |
| `final_output.*.report` | 결과 출력 | Markdown/텍스트 렌더링 |
| `final_output.*.llm_used` | 결과 카드 “보고서 상태” | LLM 사용 여부 배지 |
| `final_output.*.llm_model` | 결과 카드 하단 | 모델명 표시 |
| `final_output.*.llm_error` | 경고 배너 | 오류 메시지 축약 표시 |
| `node_results` | 노드 상세 출력 | 상태/오류/출력 분리 |

## 6) 검증 시나리오 세트 (추가 권장)

- **LLM 실패 시나리오**: `llm_error` 포함 응답을 주입.
- **부분 노드 실패**: `node_results`에 `failed` 상태 포함.
- **보고서 없음**: `final_output`에 `report` 미포함.
- **대용량 보고서**: 5,000자 이상 보고서 렌더링.
- **빈 결과**: `final_output`/`node_results` 비어 있을 때 UI 대응.

## 7) 검증 로그/증적

- 요청/응답 JSON, 스크린샷, Run ID/Result ID를 함께 기록한다.
- 문제가 재현되면 **API 응답 스냅샷**을 함께 저장한다.

## 8) 완료 기준

- 필수 시나리오(E2E) 전부 통과.
- Analysis Lab 핵심 체크리스트 전 항목 확인.
- 에러/대체 처리 시나리오 2개 이상 재현 완료.
