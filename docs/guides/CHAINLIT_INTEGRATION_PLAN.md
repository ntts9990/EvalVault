# Chainlit 통합 계획 (MCP 포함)

이 문서는 EvalVault 기능 설명/분석 Q&A/즉시 피드백 저장을 **Chainlit 기반 챗봇**으로 빠르게 붙이기 위한 상세 계획입니다.
핵심 목표는 **빠른 PoC → 운영 가능 경로 확보 → MCP 기반 도구 호출**로 확장하는 것입니다.

---

## 목표

- EvalVault 기능 설명/가이드 제공 (사용자 질문 응답)
- 분석 결과 질의응답 제공 (run_id 기반)
- 답변에 대한 즉시 피드백 수집 (thumbs + 코멘트 + 점수)
- 피드백을 EvalVault 저장소 및 도메인 메모리로 반영
- MCP 지원을 계획에 포함 (단, 초기는 Python 직접 호출)

---

## 핵심 결론

- Chainlit의 MCP 기능은 **포함**하되, **현재 EvalVault는 MCP HTTP/SSE 서버가 없음**
- 1차 구현은 **Python 직접 호출** 방식으로 빠르게 구축
- 2차 구현에서 **MCP 서버(SSE/Streamable HTTP)** 를 추가해 Chainlit MCP 클라이언트와 연결

---

## 아키텍처 개요

### 1) 1차 (빠른 PoC: Python 직접 호출)

```
Chainlit UI
  -> EvalVault Python APIs (mcp/tools.py + WebUIAdapter)
  -> SQLite Storage + Domain Memory
  -> Feedback 저장 (satisfaction_feedback)
```

### 2) 2차 (MCP 기반 Tool Calling)

```
Chainlit MCP Client
  -> EvalVault MCP Server (SSE/Streamable HTTP) [추가 구현]
  -> MCP Tools (list_runs, get_run_summary, run_evaluation, analyze_compare, get_artifacts)
```

---

## EvalVault 연동 지점

### MCP 도구 (이미 구현됨, 서버 없음)
- `list_runs`
- `get_run_summary`
- `run_evaluation`
- `analyze_compare`
- `get_artifacts`

파일: `src/evalvault/adapters/inbound/mcp/tools.py`

### 피드백 저장 (이미 구현됨)
- REST: `POST /api/runs/{run_id}/feedback`
- 저장 테이블: `satisfaction_feedback`

파일: `src/evalvault/adapters/inbound/api/routers/runs.py`

### 도메인 메모리
- API: `GET /api/domain/facts`, `/behaviors`
- 학습 훅: 평가 완료 시 DomainLearningHook

파일: `src/evalvault/adapters/inbound/api/routers/domain.py`

---

## 상세 작업 계획 (병렬 가능)

### MCP 서버 트랜스포트 (HTTP JSON-RPC)
- `/api/v1/mcp`에 JSON-RPC 엔드포인트 제공
- 인증 토큰 필수 (`MCP_AUTH_TOKENS`)
- 도구 allowlist(`MCP_ALLOWED_TOOLS`)로 제한
- stdio 비활성화(Chainlit에서는 SSE/Streamable HTTP 사용)

### Stream A: Chainlit 챗봇 핵심 기능
1. Chainlit 앱 구조 생성 (`chainlit_app.py`)
2. 기능 설명 Q&A (문서/설명 응답)
3. run_id 기반 분석 Q&A
4. 기본 도구 실행 흐름 연결 (list_runs, get_run_summary, get_artifacts)

### Stream B: 피드백 수집/저장
1. 메시지별 thumbs up/down + 코멘트 UI 제공
2. 피드백을 EvalVault API에 저장
3. 저장된 피드백을 domain memory 학습 트리거로 확장 가능하게 설계

### Stream C: MCP 기반 도구 호출 (2차)
1. MCP 서버 구현 (SSE/Streamable HTTP)
2. Chainlit MCP 클라이언트 연결
3. 도구 목록 자동 로드 및 tool call 실행

---

## 구현 단계 (우선순위)

### 단계 0: 사전 준비
- Chainlit 설치
- EvalVault API 서버 실행
- DB/메모리 경로 확인

### 단계 1: Chainlit PoC (Python 직접 호출)
- Chainlit 앱에서 `evalvault.adapters.inbound.mcp` 도구 호출
- 결과를 요약 응답으로 전송
- 피드백 저장은 EvalVault API로 POST

### 단계 2: 피드백 → 도메인 지식 반영
- 피드백 수집 후 도메인 메모리로 요약 저장 (선택)
- 예: 불만족 코멘트 → 개선 포인트로 요약 → Domain facts 저장

### 단계 3: MCP 서버 구현
- EvalVault에 MCP HTTP JSON-RPC 엔드포인트 추가
- Chainlit에서 MCP 연결 설정 (Streamable HTTP)
- stdio 연결은 비활성화 (보안상 금지)

---

## Chainlit MCP 반영 판단

### 포함 결정
- Chainlit은 MCP 클라이언트 기능을 제공
- EvalVault는 MCP 도구 로직 구현 완료
- **HTTP JSON-RPC 트랜스포트 추가로 연동 가능**

### 보안 기준
- stdio는 비활성화
- HTTP 기반 연결만 허용
- MCP 토큰 인증 필수 + allowlist 적용

---

## 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| Chainlit 커뮤니티 유지보수 | 버전 pin, 기능 최소화, Streamlit 대안 준비 |
| MCP 서버 미구현 | 초기에는 Python 직접 호출 방식 사용 |
| 피드백 악성 입력 | API rate limit + 필드 길이 제한 + 텍스트 정제 |

---

## 성공 기준

- 사용자가 챗봇에서 EvalVault 기능/결과를 질문하고 답변을 받는다
- 답변에 대한 피드백이 DB에 저장된다
- 특정 run_id 기반 질문이 정상 응답된다
- MCP 기반 호출로 전환 가능한 구조를 확보한다

---

## 다음 액션

- 1차 PoC 구현 (Chainlit 앱 + EvalVault Python 호출 + 피드백 저장)
- 이후 MCP 서버 구현 여부 결정
