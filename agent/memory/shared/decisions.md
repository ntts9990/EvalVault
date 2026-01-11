# Architecture Decisions Record (ADR)

> 이 문서는 모든 에이전트가 공유하는 중요 결정 사항을 기록합니다.
> 새 결정 추가 시 최상단에 작성합니다.

---

## Decision Log

### DEC-2026-001: Phoenix를 주 Observability 플랫폼으로 선택

**Date**: 2026-01-01
**Status**: `accepted`
**Stakeholders**: `observability`, `rag-data`, `performance`

**Context**:
RAG 시스템의 검색/생성 단계 데이터를 수집하고 분석할 Observability 플랫폼이 필요함.
기존 LangFuse/MLflow와 새로운 Phoenix를 비교 검토.

**Decision**:
Phoenix를 주 추적 시스템으로, LangFuse는 프롬프트 관리 전용으로 사용.

**Rationale**:
1. Phoenix 점수 9/12 > LangFuse 6.5/12 > MLflow 5.5/12
2. OpenTelemetry 표준 준수 (플랫폼 독립성)
3. RAG 특화 기능 (검색 품질 분석, 임베딩 시각화)
4. Ragas 네이티브 통합
5. 14배 빠른 성능

**Consequences**:
- (+) 검색 품질 자동 분석 가능
- (+) 임베딩 시각화로 쿼리 클러스터 분석
- (+) OpenTelemetry로 언제든 플랫폼 전환 가능
- (-) 팀 협업/프롬프트 관리는 LangFuse 병행 필요

**Related Files**:
- `docs/RAG_PERFORMANCE_DATA_STRATEGY_FINAL.md`
- `docs/OBSERVABILITY_PLATFORM_COMPARISON.md`

---

### DEC-2026-002: 병렬 AI 에이전트 워크플로우 도입

**Date**: 2026-01-01
**Status**: `accepted`
**Stakeholders**: All agents

**Context**:
EvalVault 개선 작업이 다양한 영역(아키텍처, 성능, 테스트 등)에 걸쳐 있어
순차적 작업 시 비효율적. AI 에이전트들의 병렬 작업 필요.

**Decision**:
6개 Worker Agent + 1개 Coordinator Agent 구조 채택.
각 에이전트는 독립적 메모리 공간을 가지며, shared/ 통해 협업.

**Rationale**:
1. 독립적 영역은 병렬 처리로 속도 향상
2. 메모리 시스템으로 컨텍스트 영속화
3. Coordinator가 통합하여 일관성 유지

**Consequences**:
- (+) 작업 속도 3-5배 향상 예상
- (+) 각 에이전트 전문화
- (-) 충돌 관리 오버헤드
- (-) 초기 설정 비용

**Related Files**:
- `agent/memory/README.md`
- `docs/INDEX.md`

---

### DEC-2026-003: 우선순위 기반 데이터 수집 전략

**Date**: 2026-01-01
**Status**: `accepted`
**Stakeholders**: `rag-data`, `observability`

**Context**:
RAG 파이프라인의 모든 데이터를 동시에 수집하면 복잡도가 높아짐.
단계적 접근 필요.

**Decision**:
P0 → P1 → P2 우선순위로 단계적 구현:
- P0 (즉시): 검색 후보/점수, 프롬프트/파라미터, 레이턴시 분해
- P1 (1개월): 쿼리 분류, 문서 메타데이터
- P2 (3개월): 사용자 피드백

**Rationale**:
1. P0만으로도 "왜 점수가 낮은가?" 답변 가능
2. 빠른 ROI 달성 (P0 완료 시 16배 진단 속도 향상)
3. 점진적 복잡도 관리

**Consequences**:
- (+) 빠른 가치 실현
- (+) 리스크 분산
- (-) P2 기능은 3개월 대기

**Related Files**:
- `docs/RAG_PERFORMANCE_DATA_STRATEGY_FINAL.md` (Section 3)

---

## Decision Template

```markdown
### DEC-YYYY-NNN: [결정 제목]

**Date**: YYYY-MM-DD
**Status**: `proposed` / `accepted` / `deprecated` / `superseded`
**Stakeholders**: `agent1`, `agent2`

**Context**:
결정이 필요한 배경 설명

**Decision**:
내린 결정

**Rationale**:
결정 이유 (번호 리스트)

**Consequences**:
- (+) 장점
- (-) 단점

**Related Files**:
- 관련 파일 경로

**Supersedes**: DEC-YYYY-NNN (이전 결정을 대체하는 경우)
```

---

## Status Definitions

| Status | Description |
|--------|-------------|
| `proposed` | 검토 중인 결정 |
| `accepted` | 승인되어 적용 중인 결정 |
| `deprecated` | 더 이상 권장하지 않는 결정 |
| `superseded` | 새 결정으로 대체됨 |

---

**Last Updated**: 2026-01-01
**Maintainer**: Coordinator Agent
