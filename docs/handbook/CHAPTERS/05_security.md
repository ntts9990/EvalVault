# 05. Security

## 목표

시크릿/키/민감 데이터의 취급 원칙과 외부 공개 요약본의 경계 규칙을 고정한다.

## 기본 원칙

- 시크릿은 `.env`/환경변수로 관리하고, git 커밋 대상이 아니다.
- 외부 공개 요약본(`../EXTERNAL.md`)에는 내부 경로/운영 절차/실데이터/수치를 포함하지 않는다.

## 시크릿 관리

- `secret://` 참조 지원: `../../src/evalvault/config/secret_manager.py`
- 런타임 해석/검증: `../../src/evalvault/config/settings.py`
- 환경 템플릿: `../../.env.example`

## API 인증/토큰

- API 토큰 인증: `../../src/evalvault/adapters/inbound/api/main.py`
- 지식 API read/write 토큰: `../../src/evalvault/adapters/inbound/api/routers/knowledge.py`
- MCP 토큰: `../../src/evalvault/adapters/inbound/api/routers/mcp.py`

## 로깅/PII 마스킹

- 로그 정제/PII 마스킹: `../../src/evalvault/adapters/outbound/tracker/log_sanitizer.py`
- Phoenix/Langfuse/MLflow 트래커에서 공통 적용

## 운영 스냅샷/레덕션

- 환경 스냅샷 레덕션: `../../src/evalvault/domain/services/ops_snapshot_service.py`
- CLI: `evalvault ops snapshot --redact ...`

예시 명령:
- `uv run evalvault ops snapshot --redact OPENAI_API_KEY --redact LANGFUSE_SECRET_KEY --redact DATABASE_URL`

## 구성 보안

- CORS/프로덕션 검증: `../../src/evalvault/config/settings.py`
- Langfuse compose 시크릿 교체: `../../docker-compose.langfuse.yml`

## 참고

- 보안 문서: `../../SECURITY.md`
- 내부 백서: `../new_whitepaper/11_security.md`
- 보안 감사 로그: `../security_audit_worklog.md`
