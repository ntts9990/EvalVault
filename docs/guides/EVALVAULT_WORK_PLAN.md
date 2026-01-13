# EvalVault 작업 계획서 (RAGAS/Tracing/Prompt Override)

## 0) 목적

- RAGAS 평가 → 결과 저장 → Phoenix 트레이싱 → 추가 분석 → 보고서(Markdown)까지 **정상 동작** 확인
- 외부 로그 API 입력(JSON 가정)을 **RAGAS형/비정형**으로 분기해 분석 수행
- RAGAS 프롬프트와 시스템 프롬프트를 **분리 오버라이드**하고 실제 실행으로 검증

## 1) 전제 및 범위

- 언어 비율: 한국어 90%, 영어 10%
- 외부 로그 입력: JSON/JSONL로 가정
- WebUI: 로컬 frontend (`npm run dev`)
- 보고서 출력: Markdown
- Phoenix 에러 로그는 추후 공유 예정

## 2) 실행 순서(내가 진행하는 기준)

1. Web API 서버 기동 오류(순환 import) 해소 확인
2. 신규 데이터셋 생성(JSON) 및 CLI 평가/저장/분석/보고서 검증
3. Phoenix 트레이싱 경로 연결 점검(에러 재현은 로그 수령 후)
4. 외부 로그 JSON 입력 → 분류 → 분석 → 보고서
5. 프롬프트 분리/오버라이드 구현 및 실제 실행 증거 확보
6. WebUI 검증 체크리스트 제공(사용자 수행)

## 3) 1번: RAGAS 평가 전체 흐름 검증 (CLI)

### 3.1 신규 데이터셋 생성
- 포맷: `question`, `answer`, `contexts`, `ground_truth`
- 한국어 90%, 영어 10% 비율 유지
- 저장 경로: `data/datasets/<name>.json` (확정)

### 3.2 CLI 평가 실행
- 예시 명령:
  - `uv run evalvault run data/datasets/<name>.json --metrics faithfulness,answer_relevancy --profile dev --db data/db/evalvault.db --auto-analyze --tracker phoenix`

### 3.3 결과 저장 및 아티팩트 확인
- DB 저장: `data/db/evalvault.db`
- 보고서: `reports/analysis/analysis_<RUN_ID>.md`
- 아티팩트: `reports/analysis/artifacts/analysis_<RUN_ID>/`

### 3.4 추가 분석(형태소/임베딩)
- 분석 명령(예):
  - `uv run evalvault analyze <RUN_ID> --nlp --causal --playbook`

## 4) 2번: 외부 로그 API 입력 → 분류 → 분석

### 4.1 API 규격 원칙 (OpenTelemetry + OpenInference)
- 외부 로그 API는 **OpenTelemetry OTLP** 및 **OpenInference** 속성 규약을 준수한다.
- 필수 키:
  - `trace_id`, `span_id`, `parent_span_id`
  - `name`, `start_time`, `end_time`
  - `attributes` (OpenInference 키 포함)
- OpenInference 필수/권장 키(요약):
  - `rag.module`, `spec.version`, `input.value`, `output.value`
  - `llm.model_name`, `llm.temperature`, `retrieval.documents_json`
- 스펙 참고:
  - `docs/architecture/open-rag-trace-spec.md`
  - `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`

### 4.2 입력 분류 규칙
- RAGAS 형식(JSON)일 때: RAGAS 평가 파이프라인
- 비정형 JSON일 때: Phoenix 트레이싱 + Stage Event 분석

### 4.3 수집 및 저장
- Stage Event ingest:
  - `uv run evalvault stage ingest path/to/external_logs.jsonl --db data/db/evalvault.db`

### 4.4 분석 및 보고서
- RAGAS형: `evalvault run` → `auto-analyze`
- 비정형: Stage summary + 분석 모듈 실행 후 Markdown 보고서

## 5) 3번: 프롬프트 분리/오버라이드

### 5.1 분리 기준
- RAGAS 프롬프트: `ragas_prompt_overrides.py` 기반
- 시스템 프롬프트: `system_prompt`/`system_prompt_file` 기반

### 5.2 CLI 테스트
- RAGAS 오버라이드:
  - `uv run evalvault run data/datasets/<name>.json --ragas-prompts config/ragas_prompts.yaml`
- 시스템 프롬프트 오버라이드:
  - `uv run evalvault run data/datasets/<name>.json --system-prompt-file prompts/system.txt`

### 5.3 증거 확보
- 실행 로그에 오버라이드 적용 여부 기록
- 보고서(Markdown) 생성 결과로 증빙

## 6) WebUI 검증 체크리스트 (사용자 수행)

- `uv run evalvault serve-api --reload`
- `cd frontend && npm install && npm run dev`
- UI에서 신규 데이터셋 업로드 → 평가 실행 → 리포트 생성 확인
- Phoenix 링크/메타데이터 노출 확인
- 프롬프트 오버라이드 적용 결과 확인
- 외부 로그 연동(OTel/OpenInference) 화면/메타데이터 노출 확인

## 7) 증거/산출물 체크리스트

- `reports/analysis/analysis_<RUN_ID>.md` 생성
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json` 생성
- `data/db/evalvault.db` 내 run 기록 존재
- 외부 로그 ingest 결과 조회(`stage summary`)
- 프롬프트 오버라이드 적용 로그

## 8) 현재 알려진 이슈

- `uv run evalvault serve-api --reload` 실행 시 순환 import 에러 발생 기록
- 해결 조치: `create_llm_adapter_for_model`를 `llm/factory.py`로 이동하여 순환 import 제거
- 재확인 필요: 동일 에러 재발 여부
