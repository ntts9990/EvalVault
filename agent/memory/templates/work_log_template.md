# [Task Name] Work Log

## Session Info

| Field | Value |
|-------|-------|
| **Agent** | `{agent-name}` |
| **Task ID** | `TASK-YYYY-NNN` |
| **Date** | YYYY-MM-DD |
| **Started** | HH:MM |
| **Duration** | Xh Ym |
| **Status** | `pending` / `in_progress` / `completed` / `blocked` |

---

## 1. Objective (목적)

### Primary Goal
이 작업의 핵심 목표를 한 문장으로 기술

### Success Criteria
- [ ] 성공 조건 1
- [ ] 성공 조건 2
- [ ] 성공 조건 3

### Scope
- **In Scope**: 포함 범위
- **Out of Scope**: 제외 범위

---

## 2. Context (배경)

### Why This Task?
이 작업이 필요한 이유

### Related Tasks
- `TASK-YYYY-NNN`: 관련 작업 1
- `TASK-YYYY-NNN`: 관련 작업 2

### Prerequisites
- [x] 선행 조건 1 (완료)
- [ ] 선행 조건 2 (대기)

---

## 3. Approach (방법)

### Selected Approach
선택한 접근 방식 설명

### Alternatives Considered
1. **대안 1**: 설명 - 선택하지 않은 이유
2. **대안 2**: 설명 - 선택하지 않은 이유

### Technical Details
```python
# 핵심 코드 스니펫 또는 의사 코드
def approach():
    pass
```

---

## 4. Progress (진행 과정)

### Step 1: [단계명]
**Time**: HH:MM - HH:MM

**Actions**:
- 수행 내용 1
- 수행 내용 2

**Result**:
결과 설명

**Issues**:
- 발생 이슈 (있는 경우)

---

### Step 2: [단계명]
**Time**: HH:MM - HH:MM

**Actions**:
- 수행 내용

**Result**:
결과 설명

---

## 5. Artifacts (생성물)

### Created Files
| File Path | Description |
|-----------|-------------|
| `src/evalvault/...` | 설명 |

### Modified Files
| File Path | Changes |
|-----------|---------|
| `src/evalvault/...` | 변경 내용 요약 |

### Deleted Files
| File Path | Reason |
|-----------|--------|
| - | - |

---

## 6. Decisions (결정 사항)

### DEC-YYYY-NNN: [결정 제목]
- **Context**: 결정이 필요했던 상황
- **Decision**: 내린 결정
- **Rationale**: 결정 이유
- **Consequences**: 예상되는 영향
- **Reversibility**: 높음 / 중간 / 낮음

> **Note**: 중요 결정은 `shared/decisions.md`에도 기록할 것

---

## 7. Testing (검증)

### Tests Run
```bash
uv run pytest tests/unit/test_xxx.py -v
```

### Results
```
X passed, Y failed, Z skipped
```

### Coverage Impact
- Before: XX%
- After: YY%

---

## 8. Dependencies (의존성)

### Blocking This Task
| Agent | Task | Status | ETA |
|-------|------|--------|-----|
| - | - | - | - |

### Blocked By This Task
| Agent | Task | Notes |
|-------|------|-------|
| - | - | - |

### Shared Resources
- 공유 리소스 1
- 공유 리소스 2

---

## 9. Issues & Blockers

### Current Issues
| Issue | Severity | Status | Owner |
|-------|----------|--------|-------|
| - | - | - | - |

### Resolved Issues
| Issue | Resolution |
|-------|------------|
| - | - |

---

## 10. Next Steps (다음 단계)

### Immediate (이번 세션)
- [ ] 즉시 할 일 1
- [ ] 즉시 할 일 2

### Short-term (다음 세션)
- [ ] 단기 할 일 1
- [ ] 단기 할 일 2

### Handoff Notes
다음 에이전트/세션을 위한 인수인계 사항:
- 주의 사항
- 알아야 할 컨텍스트

---

## 11. Metrics

### Performance
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| - | - | - | - |

### Quality
| Metric | Value |
|--------|-------|
| Code Coverage | XX% |
| Test Pass Rate | XX% |
| Lint Errors | N |

---

## 12. Learnings (교훈)

### What Worked Well
- 잘 된 점 1
- 잘 된 점 2

### What Could Be Improved
- 개선 가능 점 1
- 개선 가능 점 2

### Knowledge Gained
- 새로 알게 된 점

---

## Changelog

| Time | Change |
|------|--------|
| HH:MM | Initial log created |
| HH:MM | Step 1 completed |
| HH:MM | Status updated to completed |

---

**Template Version**: 1.0.0
