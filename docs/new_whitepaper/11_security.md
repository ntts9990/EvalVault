# 11. 보안/프라이버시(Security)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: 내부 개발자가 EvalVault를 안전하게 개발/운영하기 위한 최소 기준(비밀 관리, 데이터 취급, 공개 정책)을 정리한다.
- **독자**: 내부 개발자/운영자
- **선행 지식**: 없음

---

## TL;DR

- `.env`는 커밋하지 않는다(로컬 전용).
- 외부 서비스 키(LLM/트래커)는 환경 변수로 주입하고, 문서/로그/픽스처에 절대 복사하지 않는다.
- 리포트/아티팩트(`reports/`)는 “평가 산출물”이므로 민감 데이터가 섞일 수 있다 → 공유 전에 스크럽.
- 로컬 Docker(특히 Langfuse)는 `# CHANGEME` 기본값을 반드시 교체한다.
- 취약점 제보는 `SECURITY.md` 정책을 따른다.

---

## 1) 비밀(Secrets) 관리

### 1.1 `.env`/환경 변수 원칙

- 설정 로딩: `src/evalvault/config/settings.py`
  - `Settings`는 `.env`를 읽는다(`env_file=".env"`, case-insensitive).
- `.env` 생성은 `.env.example`을 복사해서 시작하고, **실제 키는 로컬에서만** 관리한다.

주요 비밀/설정(예시, 값은 절대 문서에 적지 않기):
- LLM:
  - `OPENAI_API_KEY` (Settings: `openai_api_key`)
  - `ANTHROPIC_API_KEY` (Settings: `anthropic_api_key`)
  - Azure 계열 키/엔드포인트(필요 시)
- 트레이싱:
  - Phoenix cloud 토큰(필요 시): `PHOENIX_API_TOKEN` (Settings: `phoenix_api_token`)
  - Langfuse 키(필요 시): `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`

> **NOTE**: Settings 필드명은 코드에서 단일 진실이며, 환경 변수는 일반적으로
> `PHOENIX_ENABLED`처럼 대문자/언더스코어 형태로 매핑된다.

### 1.2 저장소 경로(데이터 유출 관점)

- DB 경로는 로컬 파일 시스템에 저장된다.
  - `Settings.evalvault_db_path` (기본: `data/db/evalvault.db`)
  - `Settings.evalvault_memory_db_path` (기본: `data/db/evalvault_memory.db`)

운영 원칙:
- 공유 PC/공용 디렉터리에서는 DB/리포트 경로를 명시적으로 분리한다.

---

## 2) 데이터 프라이버시

### 2.1 픽스처/테스트 데이터

- `tests/fixtures/`에는 고객 데이터/PII를 넣지 않는다.
- 실제 운영 데이터에서 샘플을 만들 때는 “스크럽(익명화/마스킹)”을 기본으로 한다.

### 2.2 리포트/아티팩트

- 자동 분석 산출물은 로컬에 저장되며, 다음이 포함될 수 있다.
  - 질문/답변/컨텍스트(원문)
  - 메트릭별 reason(LLM이 생성한 텍스트)
  - 검색 doc_ids/scores
- 산출물 저장은 재현성을 위해 중요하지만, 공유 전에는 민감 정보 제거가 필요하다.

근거(아티팩트 인덱스 생성):
- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (`write_pipeline_artifacts`)

---

## 3) 로컬 서비스(Docker) 보안 주의

### 3.1 Langfuse Compose

- `docker-compose.langfuse.yml`에는 `# CHANGEME`로 표시된 기본 비밀값이 포함되어 있다.
- 최소한 아래 항목은 로컬이라도 교체를 권장한다.
  - `DATABASE_URL`
  - `SALT`
  - `ENCRYPTION_KEY`
  - `CLICKHOUSE_PASSWORD`
  - `LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY`
  - `LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY`
  - `LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY`
  - `REDIS_AUTH`
  - `NEXTAUTH_SECRET`
  - `MINIO_ROOT_PASSWORD`
  - `POSTGRES_PASSWORD`

### 3.2 포트 바인딩/외부 노출

- `docker-compose.langfuse.yml` 상단 주석은 “외부 노출 포트를 최소화”하도록 권장한다.
- 운영/공유 환경에서는 반드시 방화벽/포트 바인딩 정책을 재검토한다.

---

## 4) 취약점 보고 정책

- `SECURITY.md`의 프로세스를 따른다.
  - 제보 채널: `security@evalvault.dev`
  - 공개 전 조사 기간: 최소 14일

---

## Evidence

- 설정 로딩/환경 변수: `src/evalvault/config/settings.py`
- 아티팩트 산출/저장: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- Langfuse 기본 비밀값/포트 권장: `docker-compose.langfuse.yml`
- 취약점 보고 정책: `SECURITY.md`
- 개발 가이드(커밋 금지 등): `AGENTS.md`

---

## 전문가 관점 체크리스트

- [ ] 비밀값이 문서/로그/테스트에 노출되지 않도록 가이드가 충분한가
- [ ] “로컬에서만 쓰니까 괜찮다”는 함정을 피하도록 경고가 있는가
- [ ] 리포트/아티팩트 공유 시 스크럽 루틴이 명시되는가
- [ ] 공개 제보 정책(SECURITY)이 내부 개발 흐름에 연결되는가

---

## 향후 변경 시 업데이트 가이드

- Settings에 새 비밀/환경 변수가 추가되면:
  - `src/evalvault/config/settings.py` 근거로 이 장의 **1장**에 “어떤 값이 민감한지”를 추가한다.

- 산출물(리포트/아티팩트)에 새 필드가 추가되면:
  - 민감 데이터 포함 가능성을 검토하고, 이 장의 **2.2**에 공유 주의사항을 갱신한다.

- Compose 파일에 `# CHANGEME` 항목이 추가되면:
  - 이 장의 **3.1** 목록을 업데이트한다.
