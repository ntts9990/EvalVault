# 05. Security (시크릿, 데이터, 접근, 로그)

이 챕터는 EvalVault를 안전하게 운영하기 위한 보안 규칙을 “레포 내부의 사실(코드/설정/워크플로)”만으로 정리한다.

EvalVault는 일반적인 웹 서비스와 달리 아래가 동시에 존재한다.

- 평가 데이터(종종 민감: contexts/ground_truth/원문 발췌)
- 외부 LLM 호출(비용/유출 위험)
- 결과물(리포트/아티팩트/트레이스 링크)

따라서 보안의 초점은 다음 5가지다.

1) 시크릿 관리(절대 커밋 금지)
2) 민감 데이터(PII/고객 데이터) 처리
3) 접근 제어(API 토큰, CORS, 레이트리밋)
4) MCP(JSON-RPC) 노출 범위 제어(도구 allowlist + 파일 경로 allowlist)
5) 로그/트레이스/아티팩트의 레덕션(자동 마스킹)

## TL;DR

- 시크릿은 `.env`/환경변수로만 관리하고, `.env`는 git에 남기지 않는다. (근거: `.env.example`, `.gitignore`)
- API 인증은 “토큰이 설정되면 강제”되는 형태다. 토큰이 비어 있으면 인증이 꺼진다. (근거: `src/evalvault/adapters/inbound/api/main.py#require_api_token`)
- prod 프로필은 안전하지 않은 설정을 빠르게 거부한다(필수 시크릿 누락, CORS 오리진 등). (근거: `src/evalvault/config/settings.py#_validate_production_settings`)
- 트래커(Langfuse/Phoenix/MLflow)는 payload를 그대로 보내지 않고 sanitize(PII 마스킹/길이 제한)를 적용한다. (근거: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`, 각 tracker adapter)
- MCP는 “도구 allowlist + 파일 경로 allowlist”로 임의 파일 접근을 막는다. (근거: `src/evalvault/adapters/inbound/api/routers/mcp.py`, `src/evalvault/adapters/inbound/mcp/tools.py`)

## 목표

- 팀의 보안 기본 규칙(what/where/how)을 합의된 형태로 고정한다.
- 실수로 시크릿/민감 데이터가 커밋/노출되지 않게 한다.
- 공유 가능한 결과물(리포트/아티팩트/트레이스 링크)을 안전하게 만든다.

---

## 1) 위협 모델(간단 버전)

### 1.1 보호해야 하는 자산

- LLM API 키(비용/악용): 예) `OPENAI_API_KEY` (근거: `.env.example`, `src/evalvault/config/settings.py#Settings.openai_api_key`)
- 평가 데이터(PII/고객 문서): dataset 파일 + contexts/ground_truth + 출력물 (근거: `src/evalvault/domain/entities/dataset.py`, `src/evalvault/domain/entities/result.py`)
- 결과물(리포트/아티팩트/트레이스): `reports/` 디렉터리 + 외부 트래커 링크 (근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`, `src/evalvault/config/phoenix_support.py`, `src/evalvault/config/langfuse_support.py`)
- 운영 설정(DB/엔드포인트/토큰): `.env` + Settings (근거: `.env.example`, `src/evalvault/config/settings.py`)

### 1.2 흔한 위협

- 실수로 `.env`를 커밋
- 리포트/아티팩트/트레이스에 원문/PII가 그대로 포함
- 인증 없는 API 노출(또는 약한 CORS)
- MCP를 통해 임의 경로 접근

---

## 2) 시크릿 관리 규칙

### 2.1 원칙

- `.env`는 로컬/운영에서만 사용하고 git에는 포함하지 않는다. (근거: `.gitignore`에 `.env`)
- 모델 프로필(버전 관리)과 시크릿(비공개)을 분리한다.
  - 프로필: `config/models.yaml` (근거: `src/evalvault/config/settings.py#apply_profile`)
  - 시크릿/인프라: `.env`/환경변수 (근거: `.env.example`, `src/evalvault/config/settings.py#Settings.model_config`)
- 최소 권한: 필요한 권한만 가진 키를 사용한다(이건 운영 정책이며, 코드로 강제되지 않으므로 팀 규약으로 고정).

### 2.2 `.env.example`를 “운영 계약서”로 쓴다

`.env.example`는 어떤 값이 시크릿/인프라에 속하는지 구조를 명시한다.

- 근거: `.env.example`

### 2.3 `secret://` 참조(선택)

Settings는 일부 필드에서 `secret://...`를 해석한다.

- 참조 감지/해석: `src/evalvault/config/settings.py#Settings._resolve_secret_references`
- provider 구현: `src/evalvault/config/secret_manager.py`
- 지원 provider: env/aws/gcp/vault (근거: `src/evalvault/config/secret_manager.py#build_secret_provider`)
- 관련 extra: `secrets` (근거: `pyproject.toml`의 `[project.optional-dependencies].secrets`)

운영 포인트:

- provider가 설정되지 않으면 해석 단계에서 실패한다. (근거: `src/evalvault/config/secret_manager.py#build_secret_provider`)

---

## 3) 데이터 분류와 처리

### 3.1 데이터 분류(권장)

- Public: 공개해도 되는 텍스트
- Internal: 내부 문서(민감도 낮음)
- Confidential: PII/고객 데이터(암호화/접근제어 필요)
- Restricted: 시크릿/API 키(최고 수준 보호)

### 3.2 EvalVault에서 특히 주의할 지점

- dataset 파일 자체에 PII가 들어 있을 수 있다.
- `contexts`는 원문 발췌일 수 있어 유출 영향이 크다.
- 리포트/아티팩트는 디버깅을 위해 입력/출력 일부를 담을 수 있다.
- 트래커(Langfuse/Phoenix/MLflow)를 켜면 외부 시스템으로 일부 payload가 전송된다(이 레포는 sanitize를 적용하지만, “무엇을 보내는가”는 팀 정책으로 통제해야 한다).

근거(입력 모델): `src/evalvault/domain/entities/dataset.py#TestCase`

### 3.3 안전한 운영 원칙(권장)

- 테스트/벤치마크는 가능한 한 가짜/익명화 데이터를 사용한다.
- 민감 데이터가 필요한 경우, 최소 샘플 + 보존 기간 + 접근자 제한을 운영 정책으로 고정한다.

---

## 4) API 접근 제어

### 4.1 API 인증(토큰이 설정되면 강제)

FastAPI는 `API_AUTH_TOKENS`가 설정된 경우에만 Bearer 인증을 강제한다.

- settings 필드: `src/evalvault/config/settings.py#Settings.api_auth_tokens`
- 인증 구현: `src/evalvault/adapters/inbound/api/main.py#require_api_token`
- 적용 범위: `app.include_router(... dependencies=[Depends(require_api_token)])` (근거: `src/evalvault/adapters/inbound/api/main.py#create_app`)

운영 체크:

- 인증 없는 운영용 API를 열어두지 않는다(특히 prod).
- prod에서는 API 토큰이 필수로 강제된다. (근거: `src/evalvault/config/settings.py#_validate_production_settings`)

### 4.2 CORS

- settings 필드: `src/evalvault/config/settings.py#Settings.cors_origins`
- prod에서는 `CORS_ORIGINS`가 비어 있으면 실패한다. (근거: `src/evalvault/adapters/inbound/api/main.py#create_app`)
- prod 프로필은 localhost 오리진을 금지한다. (근거: `src/evalvault/config/settings.py#_validate_production_settings`)

### 4.3 레이트 리밋(옵션)

레이트 리밋은 기본 비활성화이며, 켜면 `/api/` 경로에만 적용된다.

- settings 필드: `src/evalvault/config/settings.py` (`rate_limit_enabled`, `rate_limit_requests`, `rate_limit_window_seconds`, `rate_limit_block_threshold`)
- 미들웨어 구현: `src/evalvault/adapters/inbound/api/main.py#rate_limit_middleware`

---

## 5) MCP 보안(JSON-RPC): 노출 범위를 “기능”과 “파일”에서 동시에 제한

MCP는 편리하지만, 보안 경계를 잘못 잡으면 “임의 파일 읽기”가 될 수 있다. EvalVault는 이를 두 단계로 막는다.

### 5.1 MCP 켜기/끄기 + 토큰

- MCP 활성화: `src/evalvault/config/settings.py#Settings.mcp_enabled`
- 토큰: `src/evalvault/config/settings.py#Settings.mcp_auth_tokens` (없으면 `api_auth_tokens`를 fallback으로 사용)
- 인증 구현: `src/evalvault/adapters/inbound/api/routers/mcp.py#_require_mcp_token`

### 5.2 도구 allowlist

- 기본 도구 목록: `src/evalvault/adapters/inbound/api/routers/mcp.py#_tool_registry`
- allowlist 설정: `src/evalvault/config/settings.py#Settings.mcp_allowed_tools`
- allowlist 적용: `src/evalvault/adapters/inbound/api/routers/mcp.py#_allowed_tools`

### 5.3 파일 경로 allowlist(핵심 안전장치)

MCP tool은 결과물 경로를 쓰거나 읽을 수 있는데, 이때 허용 루트 밖 경로 접근을 차단한다.

- 허용 루트: `data/`, `tests/fixtures/`, `reports/` (근거: `src/evalvault/adapters/inbound/mcp/tools.py#_allowed_roots`)
- 차단: `src/evalvault/adapters/inbound/mcp/tools.py#_ensure_allowed_path`

---

## 6) 로그/트레이스/아티팩트 레덕션

### 6.1 원칙

- “디버깅에 필요한 정보”와 “유출되면 위험한 정보”를 분리한다.
- 기본 정책은 보수적으로(마스킹 우선) 설정한다.

### 6.2 sanitize(PII 마스킹 + 길이/리스트/깊이 제한)

EvalVault는 트래커에 기록되는 payload에 sanitize를 적용한다.

- 구현: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`
  - PII 패턴: email/phone/SSN/card (근거: 해당 파일의 정규식)
  - 한도: `MAX_LOG_CHARS`, `MAX_CONTEXT_CHARS`, `MAX_LIST_ITEMS`, `MAX_PAYLOAD_DEPTH`

적용 위치:

- Langfuse: `src/evalvault/adapters/outbound/tracker/langfuse_adapter.py`
- Phoenix: `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
- MLflow: `src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`

### 6.3 Ops snapshot에서 env redact(명시적 레덕션)

Ops snapshot은 실행 조건을 남기되, 지정한 키는 `[redacted]`로 마스킹한다.

- CLI: `src/evalvault/adapters/inbound/cli/commands/ops.py` (`--redact`)
- redact 로직: `src/evalvault/domain/services/ops_snapshot_service.py#_build_env_snapshot`

---

## 7) 사고 대응(Incident) 기본 템플릿

### 7.1 분류(권장)

- P0: 시크릿 유출, 대규모 데이터 유출, 서비스 중단
- P1: 인증 우회 가능성, 제한적 데이터 노출
- P2: 보안 설정 미흡(즉시 악용 가능성 낮음)

### 7.2 즉시 조치(시크릿 유출 가정)

1) 키 회전(rotate) + 기존 키 폐기
2) 영향 범위 확인(로그/트레이스/리포트/아티팩트)
3) 외부 전송 여부 확인(트래커 시스템)
4) 재발 방지(레덕션 규칙/설정 검증/운영 루틴 강화)

---

## 8) 체크리스트

- [ ] `.env`가 커밋/배포 산출물에 포함되지 않는가? (근거: `.gitignore`)
- [ ] prod에서 `API_AUTH_TOKENS`/`CORS_ORIGINS`가 강제되는가? (근거: `src/evalvault/config/settings.py#_validate_production_settings`)
- [ ] 레이트리밋을 켰을 때 `/api/`에만 적용되는가? (근거: `src/evalvault/adapters/inbound/api/main.py#rate_limit_middleware`)
- [ ] MCP가 켜졌을 때 (a) 도구 allowlist (b) 파일 경로 allowlist가 적용되는가? (근거: `src/evalvault/adapters/inbound/api/routers/mcp.py`, `src/evalvault/adapters/inbound/mcp/tools.py`)
- [ ] 트래커가 켜졌을 때 sanitize가 적용되는가? (근거: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`)

## 자기 점검 질문

1) EvalVault에서 데이터 유출 리스크가 높은 경로 3가지는 무엇인가?
2) “시크릿 회전”은 왜 1차 대응에서 최우선인가?
3) MCP를 켤 때, 어떤 두 가지 allowlist를 동시에 확인해야 하는가?

---

## 향후 변경 시 업데이트 가이드

아래가 바뀌면 이 장을 함께 업데이트한다.

- 시크릿/프로필/검증 규칙: `.env.example`, `src/evalvault/config/settings.py`, `src/evalvault/config/secret_manager.py`
- API auth/CORS/rate limit: `src/evalvault/adapters/inbound/api/main.py`
- MCP 토큰/도구/경로 제한: `src/evalvault/adapters/inbound/api/routers/mcp.py`, `src/evalvault/adapters/inbound/mcp/tools.py`
- sanitize 규칙: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`
