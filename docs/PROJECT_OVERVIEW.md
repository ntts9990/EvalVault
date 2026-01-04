# EvalVault 프로젝트 개요

> 작성일: 2026-01-07
> 목적: 프로젝트 목표/추상화 수준의 큰 그림을 정리해 공유한다.

---

## 작성 규칙

- 각 섹션은 5~9문장 내에서 요약
- 섹션 말미에 근거 경로 2~5개 기입
- 불확실한 내용은 "검증 필요"에만 기록

---

## 1) 프로젝트 미션/문제정의

요약
EvalVault는 RAG 시스템의 품질을 일관되게 평가하고 비교할 수 있는 표준 워크플로를 제공하는 것을 목표로 한다. CLI와 Streamlit Web UI를 함께 제공해 평가 실행부터 결과 공유까지의 진입 장벽을 낮춘다. 평가 결과는 SQLite/PostgreSQL에 저장되고 Langfuse·Phoenix·MLflow 같은 추적기와 연결된다. 도메인 메모리와 분석 파이프라인을 통해 과거 평가 결과를 재사용하고 개선 방향을 제시하는 데 초점을 둔다. 한국어 RAG 최적화와 임베딩/검색 통합이 핵심 기능 스펙으로 정의돼 있다. 현재 단계는 병렬 리팩토링과 문서 정합성 확보를 통해 제품 품질을 끌어올리는 데 집중한다.

근거
- docs/guides/USER_GUIDE.md
- docs/status/STATUS.md
- docs/internal/reference/FEATURE_SPECS.md
- docs/internal/status/STATUS.md

---

## 2) 주요 사용자/사용 시나리오

요약
핵심 사용자는 CLI로 평가를 실행하는 개발자와 Web UI로 결과를 확인하는 평가 담당자다. 개발자는 데이터셋을 평가하고 history/compare/export로 실행 결과를 분석하는 시나리오를 가장 많이 사용한다. 평가 담당자는 Web UI에서 평가 실행, 업로드, 히스토리 탐색, 기본 보고서 생성을 진행한다. 운영팀은 Phoenix 기반 드리프트 감시와 Gate 실행을 통해 품질 변화를 상시 모니터링한다. Prompt manifest와 Phoenix 링크를 연결해 프롬프트 변경이 평가 결과에 미치는 영향을 추적할 수 있다. 도메인 메모리와 분석 파이프라인은 반복 오류 탐지와 개선 가이드 생성 흐름에 포함된다.

근거
- docs/internal/reference/ARCHITECTURE_C4.md
- docs/guides/USER_GUIDE.md
- docs/guides/OBSERVABILITY_PLAYBOOK.md
- docs/internal/reference/FEATURE_SPECS.md

---

## 3) 핵심 기능군/모듈 개요

요약
EvalVault의 핵심 기능군은 평가 실행, 결과 저장/비교, 추적 연동, 분석/리포팅으로 구성된다. Ragas 기반 메트릭과 커스텀 메트릭을 조합해 질문/답변/컨텍스트 품질을 정량화한다. DAG 분석 파이프라인은 의도 분류 후 모듈을 조합해 요약·검증·비교·분석 리포트를 만든다. 한국어 RAG 최적화 기능은 Kiwi 형태소 분석, BM25, Dense, Hybrid 검색기와 한국어 faithfulness 검증을 제공한다. Domain Memory 시스템은 사실/행동/학습 레이어를 통해 평가 결과를 축적하고 다음 평가에 반영한다. 멀티 LLM, 멀티 DB, 멀티 트래커 구성을 전제로 통합 포인트가 설계되어 있다.

근거
- docs/internal/reference/FEATURE_SPECS.md
- docs/status/ROADMAP.md
- docs/architecture/ARCHITECTURE.md
- docs/guides/USER_GUIDE.md

---

## 4) 아키텍처 상위 구조 (Hexagonal 개요)

요약
EvalVault는 Hexagonal Architecture를 채택해 도메인 로직을 외부 시스템으로부터 분리한다. Domain 계층은 엔티티, 서비스, 메트릭으로 평가와 분석의 핵심 규칙을 정의한다. Ports 계층은 평가, 파이프라인, 웹, LLM, 저장소, 트래커 등의 계약을 정의해 경계를 고정한다. Adapters 계층은 CLI/Web 같은 입력 어댑터와 LLM/Storage/Tracker/Analysis/Report 같은 출력 어댑터로 구성된다. 의존성 방향은 어댑터에서 포트로 향하며 테스트 가능성과 교체 가능성을 확보한다. C4 모델에서도 CLI·Web 컨테이너가 Core Application을 호출하고 외부 LLM/트래커/스토리지와 연동되는 구조로 설명된다.

근거
- docs/architecture/ARCHITECTURE.md
- docs/internal/reference/ARCHITECTURE_C4.md
- docs/internal/reference/FEATURE_SPECS.md

---

## 5) 운영/관측/추적 전략

요약
운영 관측은 Phoenix 기반 트레이싱을 중심으로 설계되어 평가 실행과 데이터셋/실험을 함께 추적한다. Phoenix Drift Watcher는 실험 변화를 폴링해 임계치 초과 시 Slack 알림과 Gate 실행을 자동화한다. Gate 실행과 회귀 테스트 로그는 동일한 결과 채널로 집계돼 온콜 대응을 단순화한다. Release Notes 스크립트는 평가 결과 JSON과 Phoenix 링크를 결합해 공유 가능한 보고서를 생성한다. History/Reports 화면과 CLI 출력은 Phoenix 지표와 링크를 함께 표시해 분석 흐름을 단축한다. Langfuse·MLflow 연동도 지원해 팀의 기존 관측 스택에 맞춰 선택적으로 사용한다.

근거
- docs/guides/OBSERVABILITY_PLAYBOOK.md
- docs/guides/USER_GUIDE.md
- docs/status/STATUS.md

---

## 6) 로드맵 및 현재 상태 요약

요약
로드맵 기준으로 Phase 1-14 핵심 기능은 완료되었고 현재는 리팩토링/품질 개선 단계에 있다. STATUS 문서는 병렬 리팩토링(R1~R4, D1)과 문서 통합을 현재 핵심 과제로 정리한다. R1 하이브리드 서치 통합, R2 GraphRAG 샘플 확보, R3 대용량 처리 최적화, R4 벤치마크 정비가 병렬로 진행 중이다. D1 디버깅 레이어는 샘플 검증까지 완료되어 이후 CLI 통합이 남아 있다. 테스트 규모는 약 1.3k 수준으로 유지되며 커버리지와 LOC는 재측정 예정으로 표시돼 있다. 문서 허브(Docs Hub)는 내부 상태 문서를 단일 진실로 두고 공개 STATUS/ROADMAP/가이드를 함께 갱신하는 운영 규칙을 명시한다.

근거
- docs/status/ROADMAP.md
- docs/status/STATUS.md
- docs/internal/status/STATUS.md
- docs/INDEX.md

---

## 7) 검증 현황

### 검증 완료 (2026-01-04)

- ✅ Phoenix 플레이북 버전 표기 확인: `Phoenix 12.27.0 · EvalVault 3.2` (OBSERVABILITY_PLAYBOOK.md:3)

### 검증 필요

- ROADMAP에 표시된 커버리지/LOC 재측정 값이 최신 테스트 기준으로 업데이트됐는지 검증해야 한다.
- ROADMAP의 요구사항 커버리지 수치가 최근 실행 결과와 부합하는지 점검이 필요하다.
- 내부 상태 문서에 적힌 run_id와 보고서 경로가 실제로 접근 가능하고 재현 가능한지 확인이 필요하다.
- Web UI 보고서/Domain Memory 인사이트의 제공 범위가 사용자 가이드·STATUS 문서의 제한 사항과 실제 동작이 일치하는지 검증이 필요하다.

근거
- docs/guides/OBSERVABILITY_PLAYBOOK.md
- docs/status/ROADMAP.md
- docs/internal/status/STATUS.md
- docs/guides/USER_GUIDE.md
- docs/status/STATUS.md
