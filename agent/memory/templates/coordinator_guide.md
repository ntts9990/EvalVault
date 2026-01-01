# Coordinator Agent Guide

> **Version**: 1.0.0
> **Purpose**: 병렬 AI 에이전트 워크플로우의 통합 관리 가이드

---

## Overview

Coordinator Agent는 6개 Worker Agent의 작업을 조율하고, 전체 개선 계획의 진행 상황을 관리합니다.

---

## 핵심 역할

### 1. 상태 모니터링

```bash
# 전체 에이전트 상태 확인
for agent in architecture performance observability testing documentation rag-data; do
    echo "=== $agent ==="
    cat agent/memory/agents/$agent/session_*.md 2>/dev/null | tail -20
done
```

### 2. 의존성 관리

`shared/dependencies.md`에서:
- 블로킹 이슈 확인 및 해결
- 작업 순서 조정
- 병렬 실행 그룹 관리

### 3. 병합 충돌 해결

**우선순위**: `architecture` > `observability` > `rag-data` > `performance` > `testing` > `documentation`

### 4. 품질 검증

- 테스트 통과 확인
- 코드 리뷰 조율
- 릴리스 준비

---

## Daily Routine

### 1. 아침 체크

```markdown
1. [ ] 각 에이전트 session summary 확인
2. [ ] Blocking Issues 현황 파악
3. [ ] 오늘 병렬 실행 가능한 작업 식별
4. [ ] 우선순위 조정 필요 여부 확인
```

### 2. 중간 체크

```markdown
1. [ ] 진행 중인 작업 상태 확인
2. [ ] 새로운 블로킹 이슈 대응
3. [ ] 크로스 에이전트 커뮤니케이션 필요 사항 처리
```

### 3. 저녁 정리

```markdown
1. [ ] 오늘 완료된 작업 기록
2. [ ] dependencies.md 업데이트
3. [ ] 내일 작업 계획 수립
4. [ ] 진행률 계산 및 리포트
```

---

## Decision Making

### 언제 개입해야 하는가?

| 상황 | 조치 |
|------|------|
| 블로킹 > 2시간 | 우선순위 조정 또는 우회 방안 제시 |
| 병합 충돌 | 우선순위에 따라 해결 방향 결정 |
| 설계 결정 필요 | 관련 에이전트 의견 수렴 후 결정 |
| 스코프 변경 | 영향 분석 후 로드맵 조정 |

### 결정 기록

모든 중요 결정은 `shared/decisions.md`에 기록:

```markdown
### DEC-YYYY-NNN: [결정 제목]

**Date**: YYYY-MM-DD
**Status**: `accepted`
**Stakeholders**: `agent1`, `agent2`

**Context**: 배경
**Decision**: 결정 내용
**Rationale**: 이유
**Consequences**: 영향
```

---

## Communication Patterns

### 1. Async (기본)

- Work logs와 session summaries 통해 상태 공유
- `shared/` 문서로 크로스 에이전트 정보 공유

### 2. Sync (필요 시)

- 긴급 블로킹
- 설계 토론
- 병합 충돌

---

## Metrics & Reporting

### Weekly Report Template

```markdown
# Weekly Report - Week N

## Summary
- 완료: X tasks
- 진행 중: Y tasks
- 블로킹: Z tasks

## Agent Status
| Agent | Completed | In Progress | Blocked |
|-------|-----------|-------------|---------|
| ... | ... | ... | ... |

## Key Achievements
- ...

## Blockers
- ...

## Next Week Focus
- ...
```

### Progress Calculation

```python
def calculate_progress():
    total_tasks = count_all_tasks()
    completed = count_completed_tasks()
    return completed / total_tasks * 100
```

---

## Escalation Path

1. **Level 1**: 에이전트 자체 해결 시도
2. **Level 2**: Coordinator 개입
3. **Level 3**: 사용자 개입 요청

---

**Last Updated**: 2026-01-01
