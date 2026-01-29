# EvalVault 보안 전수조사 작업 기록 (중간)

> 목적: 엔터프라이즈 전환을 위해 보안 리스크와 준비 항목을 사전 정리
> 범위: `src/`, `config/`, `scripts/`, `docs/`, `frontend/`, `docker-compose*`, `.env*`
> 기준: OWASP LLM Top 10 2025, NIST AI RMF, 일반 SaaS 보안 체크리스트

## 1) 조사 방법
- 키워드 스캔: `api_key`, `secret`, `token`, `password`, `oauth`, `jwt`, `cors`, `shell=True`, `subprocess` 등
- 네트워크/추적/스토리지 경로 확인
- 설정/런타임 패치 경로 점검

## 2) 현재까지 확인된 핵심 영역
### 2.1 시크릿/설정
- `Settings`에 API 키/DB 비밀번호가 환경변수로 정의됨
- `.env`에 실제 키가 존재(레포 내 보관 위험)
- docker-compose 기본값에 `CHANGEME`/기본 패스워드 존재

### 2.2 API/인증
- FastAPI는 CORS만 적용, 인증/인가 미구현
- `/api/v1/config`는 비밀 값 제외하고 반환/패치 가능

### 2.3 네트워크/외부 연동
- OpenAI/Anthropic/Azure/vLLM/Ollama 연동
- Langfuse/Phoenix/MLflow 추적 연동
- 기본 엔드포인트가 `http://`로 설정된 항목 다수(로컬 전제)

### 2.4 스토리지
- 기본 저장소는 Postgres이며, SQLite 사용 시 `data/db/*.db`
- Postgres 연결 문자열에 비밀번호가 포함될 수 있음
- 저장 데이터 암호화/보관 정책 미명시

### 2.5 위험 명령 실행
- 외부 커맨드 실행 어댑터 존재 (`subprocess.run`)
- 운영 스크립트에서 `shell=True` 옵션 제공

### 2.6 해시/암호화
- 해시는 주로 캐시/식별용(MD5/SHA1/SHA256 혼재)
- 보안 목적으로의 암호화는 미확인

## 3) 우선 리스크 (요약)
- 레포 내 `.env` 실제 키 보관
- API 인증/인가 부재
- 로그/트레이스에 PII/민감 프롬프트 저장 가능성
- 데이터 암호화/보관 정책 부재
- 운영 환경에서 기본 비밀번호 사용 가능성

## 4) 엔터프라이즈 준비 체크리스트 (확장)
> 표기: P0(즉시) / P1(단기) / P2(중기) / P3(장기)

### 4.1 시크릿/키 관리
- [P0] 레포에서 `.env` 제거 및 키 전면 회전
- [P0] 운영 환경 기본 비밀번호 전면 교체 (`docker-compose*` 기본값 포함)
- [P1] Secret Manager 연동(Vault/ASM/GSM 중 택1)
- [P1] 키/토큰 로테이션 주기 및 감사 로그 정의
- [P2] SecretStr/마스킹 로깅 적용 범위 정의

### 4.2 인증/인가 (API/CLI)
- [P0] API 인증 도입 (토큰 기반 최소 인증)
- [P1] RBAC/프로젝트/테넌트 경계 정의
- [P1] 관리자/운영용 엔드포인트 분리 및 접근제어
- [P2] SSO(OIDC/SAML) 통합 로드맵

### 4.3 네트워크/전송 보안
- [P0] 외부 연동(LLM/Tracker) HTTPS 강제, 로컬 기본값 재정의
- [P1] vLLM/Ollama/추적 서버 인증/방화벽 규칙 정립
- [P1] 서비스 간 mTLS 적용 가능성 검토
- [P2] 네트워크 분리(내부/외부) 및 제로트러스트 정책

### 4.4 데이터 보호/보관
- [P0] 데이터 보관 기간/삭제 정책 수립 (PII 포함 데이터)
- [P1] 저장 데이터 암호화(디스크/DB 레벨) 정책
- [P1] 백업 암호화 및 복구 테스트 절차
- [P2] 고객 데이터 분리(테넌트 분리/암호화 키 분리)

### 4.5 로깅/트레이싱 보안
- [P0] 프롬프트/응답/트레이스에 PII 마스킹 기준 정의
- [P1] 로그 스키마 표준화(누가/무엇을/언제/어디서)
- [P1] 감사 로그 보관/삭제/위변조 방지 정책
- [P2] 이상 징후 탐지(비정상 토큰 사용량/실패율 급증)

### 4.6 LLM 전용 보안
- [P0] 프롬프트 인젝션 방어 정책 정의
- [P1] 입력/출력 가드레일(PII/정책 위반) 적용
- [P1] RAG 데이터 접근 통제(문서 등급/권한)
- [P2] Red Teaming/Adversarial 테스트 체계화

### 4.7 실행/스크립트 안전성
- [P0] `shell=True` 사용 구간 명시 및 운영 제한
- [P1] 외부 커맨드 실행 어댑터 접근 제어
- [P2] 샌드박스 실행(격리된 런타임) 검토

### 4.8 공급망/의존성
- [P0] 의존성 고정 및 SBOM 생성
- [P1] 취약점 스캐너(Snyk/Dependabot/CodeQL) CI 연동
- [P2] 모델/데이터셋 무결성 검증(체크섬)

### 4.9 운영/거버넌스
- [P1] 보안 사고 대응 프로세스/런북
- [P1] 변경관리(프로덕션 설정 변경 승인 흐름)
- [P2] 규정 준수 맵핑(GDPR/CCPA 등)
- [P3] 정기 보안 감사/펜테스트 계획

### 4.10 프론트엔드 보안
- [P0] CORS 운영 도메인 최소화
- [P1] 토큰 저장 정책(localStorage 금지 권장)
- [P2] CSP/보안 헤더 정책 정리

## 5) 우선 리스크 (요약)
- 레포 내 `.env` 실제 키 보관
- API 인증/인가 부재
- 로그/트레이스에 PII/민감 프롬프트 저장 가능성
- 데이터 암호화/보관 정책 부재
- 운영 환경에서 기본 비밀번호 사용 가능성

## 6) 다음 단계
- 체크리스트 항목별 담당/일정/상태 컬럼 정의
- 단계별(Dev/Stage/Prod) 보안 기준 분리
- 실제 구현 이슈 목록화 및 마일스톤화

## 7) 병렬 에이전트 작업 분장
> 목표: 소스 파일 충돌 최소화, 영역별 병렬 조사/설계

### Agent A: API 인증/인가
- **범위**: `src/evalvault/adapters/inbound/api/**`
- **주요 산출물**: 엔드포인트 목록, 인증 적용 포인트, 최소 인증 스키마 초안
- **겹침 금지**: 설정/로깅/스크립트 파일 접근 금지

### Agent B: 시크릿/설정 하드닝
- **범위**: `src/evalvault/config/**`, `.env.example`, `docker-compose*.yml`, `config/*.yaml`
- **주요 산출물**: 기본값 위험 항목, Secret Manager 연동 지점, 설정 검증 강화안
- **겹침 금지**: API/트레이싱 코드 접근 금지

### Agent C: 로깅/트레이싱 PII 마스킹
- **범위**: `src/evalvault/adapters/outbound/tracker/**`, `src/evalvault/config/instrumentation.py`, `src/evalvault/config/phoenix_support.py`
- **주요 산출물**: PII 마스킹 후보 필드, 로깅 스키마 개선안, 감사 로그 설계 초안
- **겹침 금지**: API/설정/스크립트 파일 접근 금지

### Agent D: 실행/스크립트 안전성
- **범위**: `src/evalvault/adapters/outbound/methods/external_command.py`, `scripts/ops/**`, `scripts/run_with_timeout.py`, `scripts/verify_workflows.py`
- **주요 산출물**: `shell=True` 사용 구간 목록, 실행 제어 방안, 위험도 평가
- **겹침 금지**: 설정/트레이싱 파일 접근 금지

## 8) 우선순위 기준(재정의)
- **P0**: 외부 노출 + 데이터 유출/권한 상승 가능성 높음 + 대응 난이도 낮음
- **P1**: 외부 노출 또는 민감 데이터 취급 + 대응 난이도 중간
- **P2**: 내부 통제/가시성 개선 또는 장기적 리스크 감소
- **P3**: 운영 성숙도(거버넌스/컴플라이언스) 강화

## 9) 실행 이슈 목록(작업 카드)
> 카드 상태: TODO / IN-PROGRESS / BLOCKED / DONE
> 주의: `.env` 변경은 **모든 작업 이후** 진행

### 카드 메타 템플릿
- 상태:
- 담당:
- 기한:
- 의존:
- 난이도: Low / Medium / High
- 범위:
- 산출물:
- 검증:

### P0
**[P0-01] API 인증/인가 도입 (최소 토큰 기반)**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: High
- 범위: `src/evalvault/adapters/inbound/api/**`
- 산출물: 인증 미들웨어/의존성, 라우터 적용, 문서 업데이트
- 검증: 인증 없는 접근 차단 확인

**[P0-02] 트레이싱/로깅 PII 마스킹 적용**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Medium
- 범위: `src/evalvault/adapters/outbound/tracker/**`
- 산출물: 마스킹 규칙, 길이 제한, 테스트 케이스
- 검증: PII 포함 입력이 마스킹되어 전송되는지 확인

**[P0-03] Langfuse compose 기본 시크릿 제거/강제**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Medium
- 범위: `docker-compose.langfuse.yml`
- 산출물: 기본값 제거, 필수값 검증 스크립트
- 검증: 기본값이면 컨테이너가 시작 실패

**[P0-04] 외부 명령 실행 안전화**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Medium
- 범위: `src/evalvault/adapters/outbound/methods/external_command.py`, `scripts/ops/phoenix_watch.py`
- 산출물: `shell=True` 경고/제한, 입력 검증
- 검증: 위험 입력 차단/경고 로그 확인

### P1
**[P1-01] 프로덕션 프로필 시크릿 검증**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: P0-03
- 난이도: Medium
- 범위: `src/evalvault/config/settings.py`
- 산출물: prod 프로필 필수값 검증
- 검증: 누락 시 실행 실패

**[P1-02] CORS 운영 도메인 제한**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Low
- 범위: `src/evalvault/config/settings.py`, `src/evalvault/adapters/inbound/api/main.py`
- 산출물: prod 기본값 제거, 경고 로깅
- 검증: localhost origin 차단 확인

**[P1-03] 저장 데이터 암호화 정책 적용**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: High
- 범위: `src/evalvault/adapters/outbound/storage/**`
- 산출물: DB/TDE 암호화 정책, 백업 암호화, 키 관리/회전 가이드
- 검증: 암호화 구성 점검 체크리스트

**[P1-04] 감사 로그 스키마 정의**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Medium
- 범위: `docs/`, `src/evalvault/config/` (설계 위주)
- 산출물: 필수 필드(actor_id, action, resource_type, resource_id, status, ip, user_agent, request_id, trace_id), 보관 기간/접근 정책
- 검증: 문서 리뷰

### P2
**[P2-01] Secret Manager 연동**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: P1-01
- 난이도: High
- 범위: `src/evalvault/config/**`
- 산출물: 연동 모듈/운영 가이드
- 검증: 로컬/스테이징에서 시크릿 로드 확인

**[P2-02] RAG 문서 접근 제어**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: P0-01
- 난이도: High
- 범위: `src/evalvault/adapters/inbound/api/routers/knowledge.py`
- 산출물: 등급/권한 모델 설계
- 검증: 권한 없는 접근 차단

**[P2-03] 레이트리밋/이상 징후 탐지**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: P0-01
- 난이도: Medium
- 범위: `src/evalvault/adapters/inbound/api/**`
- 산출물: rate limit 설정/로그 지표
- 검증: 초과 요청 차단

### P3
**[P3-01] SSO(OIDC/SAML) 로드맵**
- 상태: IN-PROGRESS
- 담당: TBD
- 기한: TBD
- 의존: P0-01
- 난이도: Medium
- 범위: `docs/`
- 산출물: 통합 시나리오/마이그레이션 플랜
- 검증: 설계 리뷰

**[P3-02] 정기 보안 감사/펜테스트 계획**
- 상태: DONE
- 담당: TBD
- 기한: TBD
- 의존: 없음
- 난이도: Low
- 범위: `docs/`
- 산출물: 주기/책임/범위 정의
- 검증: 운영 승인

### 후속(모든 작업 이후)
**[POST-01] .env 정리 및 키 회전**
- 상태: TODO
- 담당: TBD
- 기한: TBD
- 의존: P0~P3 완료
- 난이도: Medium
- 범위: `.env` (현 단계에서는 **변경 금지**)
- 산출물: 키 회전 체크리스트/실행 로그
- 검증: 기존 키 폐기 및 신규 키 적용 확인

## 10) 작업 진행 기록 (상세)
### P0 완료 내역
- API 인증/인가 적용: `src/evalvault/adapters/inbound/api/main.py`에 토큰 인증 의존성 추가 및 라우터 전반 적용.
- 설정 민감값 보호: `src/evalvault/adapters/inbound/api/routers/config.py`에서 `api_auth_tokens` 제외.
- PII 마스킹/길이 제한 도입: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py` 신설 및 Langfuse/Phoenix/MLflow 로깅 경로 적용.
- Langfuse compose 기본 시크릿 강제: `docker-compose.langfuse.yml`의 기본값 제거 및 필수값 요구.
- 외부 명령 안전화: `src/evalvault/adapters/outbound/methods/external_command.py`에 shell 사용 검증/경고, `scripts/ops/phoenix_watch.py`에 gate-shell 단일 라인 제한.

### P1 완료 내역
- 프로덕션 필수 설정 검증 추가: `src/evalvault/config/settings.py`에서 prod 프로필 필수값 검증 및 localhost CORS 금지.
- 프로덕션 CORS 강제: `src/evalvault/adapters/inbound/api/main.py`에서 prod CORS 비어있을 경우 실행 실패.
- 문서 보강: 저장 데이터 암호화 정책 및 감사 로그 필드 상세화.

### 테스트 기록
- `uv run pytest tests/unit -q` (1983 passed, 2 skipped, 14 warnings)
- `uv run pytest tests/integration/test_pipeline_api_contracts.py -q` (7 passed, 13 warnings)
- `uv run pytest tests/unit/config -q` (3 passed)
- `uv run pytest tests/unit/test_settings.py -q` (7 passed)

### 제약/보류
- `.env`는 요청에 따라 변경하지 않음 (POST-01로 이관)

## 11) P1 에이전트 리뷰 결과(요약)
### 11.1 P1-01 프로덕션 시크릿 검증 갭
- `vLLM`, `Azure`, `Anthropic` 프로바이더 필수값 검증 누락 (예: `VLLM_BASE_URL`, `AZURE_*`, `ANTHROPIC_API_KEY`).
- `faithfulness_fallback_provider` 설정 시 대응 키 검증 누락.
- `tracker_provider=phoenix`일 때 `PHOENIX_ENDPOINT` 검증 없음.
- `postgres_connection_string` 형식 검증 없음.
- 관련 위치: `src/evalvault/config/settings.py`.

### 11.2 P1-02 CORS 프로덕션 제한 갭
- `settings.py`와 `main.py`의 검증 범위 불일치(현재 `main.py`는 localhost 포함 여부를 재검증하지 않음).
- 런타임 CORS 변경(`config` API)은 미들웨어에 즉시 반영되지 않음.
- CORS origin 형식 검증 부재 및 `.env.example` 문서화 부족.
- 관련 위치: `src/evalvault/config/settings.py`, `src/evalvault/adapters/inbound/api/main.py`, `.env.example`.

### 11.3 P1-03 스토리지 암호화 격차
- SQLite/Postgres 저장 데이터 전부 평문 저장, TLS/암호화 미적용.
- JSON 직렬화/역직렬화 훅(`_serialize_json`, `_deserialize_json`)에 암호화 레이어 없음.
- Excel export가 민감 데이터 평문 노출.
- 관련 위치: `src/evalvault/adapters/outbound/storage/base_sql.py`, `src/evalvault/adapters/outbound/storage/sqlite_adapter.py`, `src/evalvault/adapters/outbound/storage/postgres_adapter.py`.

### 11.4 P1-04 감사 로그 통합 포인트
- API/CLI/Storage 전반에 감사 로그 훅 부재.
- 후보 지점: API 라우터(평가/설정/지식그래프), CLI 명령(run/analyze/config), 저장소 write/delete.
- 구조화된 로거 도입 및 `audit_log_port` 확장 필요.
- 관련 위치: `src/evalvault/adapters/inbound/api/**`, `src/evalvault/adapters/inbound/cli/**`, `src/evalvault/adapters/outbound/storage/**`.

## 12) P2 진행 기록 (Secret Manager 연동)
- `secret://` 참조를 해석하기 위한 공통 모듈 추가: `src/evalvault/config/secret_manager.py`.
- `Settings`에 `secret_provider`, `secret_cache_enabled` 필드 추가 및 시크릿 참조 자동 해석.
- 지원 Provider: `env`, `aws`(Secrets Manager), `gcp`(Secret Manager), `vault`.
- 선택 의존성: `secrets` extra(boto3, google-cloud-secret-manager, hvac).
- 테스트 추가: `tests/unit/test_settings.py`에 `secret://` 해석 및 provider 누락 에러 검증.
- 테스트 실행: `uv run pytest tests/unit/test_settings.py -q`, `uv run pytest tests/unit -q`.
- `.env`는 변경하지 않음(POST-01 유지).

## 13) P2 진행 기록 (RAG 문서 접근 제어)
- Knowledge API에 read/write 토큰 기반 접근 제어 추가.
- 설정 필드/시크릿 참조 대상에 knowledge 토큰 필드 추가.
- `.env.example`에 `KNOWLEDGE_READ_TOKENS`, `KNOWLEDGE_WRITE_TOKENS` 항목 추가.
- 테스트 추가: `tests/integration/test_pipeline_api_contracts.py`에 read/write 토큰 검사.

## 14) P2 진행 기록 (레이트리밋/이상 징후 탐지)
- API 레이트리밋 미들웨어 추가: `/api/` 경로에 한해 적용.
- 설정 필드 추가: `rate_limit_enabled`, `rate_limit_requests`, `rate_limit_window_seconds`, `rate_limit_block_threshold`.
- 레이트리밋 초과 시 429 + `Retry-After` 헤더 반환.
- 차단 횟수 임계치 도달 시 경고 로그 출력.
- `.env.example`에 레이트리밋 환경 변수 예시 추가.
- 테스트 추가: `tests/integration/test_pipeline_api_contracts.py`에 레이트리밋 차단 검증.

## 15) P3 진행 기록 (SSO 로드맵 초안)
### 15.1 범위/전제
- 기본 인증은 `API_AUTH_TOKENS` 유지(긴급 우회/백업 경로).
- Enterprise는 OIDC 우선, SAML은 브로커(IdP) 연계로 흡수.
- 테넌트/프로젝트 경계 정의 후 권한 매핑 적용.

### 15.2 결정 포인트
- OIDC만으로 충분한지 vs SAML 필요(기관/금융 IdP 요구).
- 직접 연동 vs 브로커(Keycloak/Auth0/Okta) 사용.
- 토큰 주체(sub/email) 기준과 역할 클레임 규격 확정.

### 15.3 단계별 로드맵
- Phase 0: 요구사항 수집(IdP, 클레임, 사용자 식별자, 테넌트 모델)
- Phase 1: OIDC 인증 코드 플로우 + JWKS 검증 + 캐시/클럭스큐 처리
- Phase 2: 역할/스코프 매핑 및 API 권한 정책 정의(라우터별 scope)
- Phase 3: SAML 연동(브로커 기반) + 사용자 프로비저닝(SCIM 옵션)
- Phase 4: 로그아웃/세션 정책(리프레시 토큰, 회수, 만료 정책)

### 15.4 설정 키 초안
- `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`
- `OIDC_ALLOWED_ALGS`, `OIDC_REQUIRED_CLAIMS`, `OIDC_ROLE_CLAIM`, `OIDC_EMAIL_CLAIM`
- `SSO_ENABLED`, `SSO_PROVIDER`(oidc/saml), `SSO_FALLBACK_TOKENS`

### 15.5 테스트/롤아웃
- 스테이징 IdP로 통합 테스트 후 프로덕션 순차 롤아웃
- 롤백 경로: `API_AUTH_TOKENS` 유지
- 감사 로그 연계: 로그인/권한 거부/토큰 검증 실패 이벤트 기록

## 16) P3 진행 기록 (정기 보안 감사/펜테스트 계획)
> 목적: 릴리스 직전 1회성 점검이 아니라, 주기적 검증과 개선 루프 고정
> 기준: OWASP ASVS, OWASP LLM Top 10 2025, 공급망/SBOM, SaaS 보안 체크리스트

### 16.1 목표/원칙
- 실제 배포 형태(API/CLI/DB/Tracker) 기준으로 점검
- 테스트 과정에서 프로덕션 PII/고객 프롬프트 사용 금지
- 모든 이슈는 재현 절차/근거 로그 포함
- 결과는 P0~P3 백로그와 SLA로 연결

### 16.2 주기/트리거
- 월간: 내부 경량 점검(시크릿/의존성/설정 회귀)
- 분기: DAST + LLM/RAG 공격 시나리오 점검
- 반기 또는 릴리스 전: 외부 펜테스트 1회 권장
- 변경 트리거: 인증/인가, RAG 지식 API, Tracker 연동, Storage/Export 변경 시 스팟 점검

### 16.3 점검 범위
- API: 인증/인가/CORS/설정 API 민감정보, Rate limit/DoS
- CLI: 경로/템플릿 인젝션, 명령 실행 경로, 환경변수 노출
- Storage: 평문 저장/암호화, Export 민감정보, 테넌트 분리
- Tracker/Tracing: PII 마스킹 회귀, 전송 보안, 인증 누락
- LLM/RAG: Prompt Injection, Retrieval Poisoning, 컨텍스트/시크릿 유출

### 16.4 사전 조건
- 스테이징 환경(Prod 유사, TLS 포함)
- 테스트 전용 데이터/계정/토큰 사용
- 감사 로그/트레이스 접근 권한 확보
- 점검 중 롤백/차단 절차 준비

### 16.5 방법론
- SAST/Config/SBOM 기반 취약점 스캔
- DAST: OpenAPI 기반 + 수동 시나리오
- Gray-box 리뷰: 토큰 검증 경계/설정 반영 타이밍
- LLM Red Teaming: 간접 인젝션, 지식베이스 오염, Canary 추적

### 16.6 데이터 처리/보관
- 산출물은 민감정보 제거 후 보관
- 보관 위치/기간/폐기 기준 사전 합의
- 프로덕션 데이터 사용 시 사전 승인 및 최소 범위 적용

### 16.7 보고/산출물
- Executive Summary + 기술 리포트
- 심각도/재현 절차/영향/권장 조치/재검증 포함
- OWASP ASVS/LLM Top 10 매핑

### 16.8 리메디에이션 SLA(권장)
- Critical 7일, High 14일, Medium 30일, Low 90일
- 예외는 임시 완화 후 일정 재합의

### 16.9 Responsible Disclosure
- 외부 제보 채널 및 공개 일정 수립
- 0-day 성격 이슈는 비공개 채널 공유

### 16.10 Ready-to-Test 체크리스트
- [ ] 스테이징 환경 준비
- [ ] 테스트 전용 데이터/토큰
- [ ] 마스킹/로그 회귀 확인
- [ ] 롤백/차단 플래그
- [ ] 리포트 템플릿/SLA 합의

## 17) 지금까지 작업 요약
- API 인증/인가 및 Knowledge 접근 제어 도입, 레이트리밋 추가
- Secret Manager 연동(`secret://`) 및 `secrets` extra 추가
- PII 마스킹/로깅 안전성 강화, 외부 명령 실행 제한
- 프로덕션 설정 검증(CORS/필수 시크릿) 강화
- 테스트 통과 기록 유지(유닛/통합)

## 18) 앞으로 작업할 항목(정리)
- P1 갭 보완: Azure/Anthropic/vLLM/phoenix 필수값 검증 추가
- CORS 런타임 반영/형식 검증, `.env.example` 문서 보강
- 저장소 암호화/Export 민감정보 보호(정책→구현)
- 감사 로그/권한 정책 포트 설계 및 연동
- SSO(OIDC/SAML) 상세 설계 및 구현 계획 수립
- POST-01: `.env` 정리 및 키 회전

(추가 조사 및 보강 예정)
