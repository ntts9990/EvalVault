# 방법론 4: C4/컴포넌트 관점

> Audience: 개발자/기여자/아키텍트
> Purpose: 시스템 경계와 주요 컴포넌트를 높은 수준에서 정리
> Last Updated: 2026-01-06

---

## 핵심 질문

- “큰 덩어리와 경계(외부 시스템/인터페이스)는 무엇인가?”

---

## 사용 목적

- 시스템 컨텍스트를 빠르게 공유(온보딩/협업/문서화)
- 외부 의존성(LLM, DB, 트레이서)을 명확히 표시
- UI/CLI/API 간 관계를 한눈에 설명

---

## 빠른 절차

1. 컨테이너(CLI, API, Web UI, Domain)를 나눈다.
2. 외부 시스템(LLM, Storage, Tracker)을 식별한다.
3. 컨테이너 간 연결선을 최소한으로 표시한다.
4. 필요 시 컴포넌트 수준으로 한 단계만 내려간다.

---

## 짧은 예시 (개념 파악용)

```mermaid
flowchart LR
  CLI[CLI(Typer)] --> Domain[Domain Services]
  API[FastAPI] --> Domain
  Web[React UI] --> API
  Domain --> Storage[Storage Adapter]
  Domain --> LLM[LLM Adapter]
  Domain --> Tracker[Tracing Adapter]
```

---

## 다른 방법론 대비 장점/단점

| 구분 | 내용 |
|---|---|
| 장점 | 엔트리포인트 흐름보다 “경계와 외부 통합”을 잘 보여준다. |
| 단점 | 도메인 내부 구조나 세부 의존성은 보이지 않는다. |

---

## 시각화/도구

- PlantUML(C4) 또는 Mermaid flowchart
- `docs/internal/reference/ARCHITECTURE_C4.md` 참고

---

## 도구 설치 (선택)

- PlantUML
  - macOS: `brew install plantuml`
  - Ubuntu: `sudo apt-get install plantuml`
  - Windows: `choco install plantuml`
- Java가 필요할 수 있으므로 `java -version`으로 확인한다.
- C4-PlantUML 템플릿 사용 시 Graphviz(dot)가 필요할 수 있다.

---

## EvalVault 적용 포인트

- `frontend/`
- `src/evalvault/adapters/inbound`
- `src/evalvault/adapters/outbound`
- `src/evalvault/domain`
