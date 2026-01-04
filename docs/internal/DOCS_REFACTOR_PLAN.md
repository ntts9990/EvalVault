# 문서 통합/최신화 계획 (클러스터링 기반)

> **작성일**: 2026-01-04
> **목적**: 문서가 많아진 현 상태를 클러스터링 → 통합 → 최신화 순서로 정리
> **SSoT**: `docs/internal/PARALLEL_WORK_PLAN.md` (병렬 작업 기준), `docs/internal/STATUS.md` (진행 상태)

---

## 1) 문서 클러스터 맵 (1차 분류)

### A. 내부 상태/리포트 (운영/진행 상황)
- `docs/internal/STATUS.md`
- `docs/internal/O1_PARALLEL_STATUS.md`
- `docs/internal/O1_D1_DEBUG_REPORT_SUMMARY.md`
- `docs/internal/R1_COMPLETION_REPORT.md`
- `docs/internal/R2_COMPLETION_REPORT.md`
- `docs/internal/R3_PROGRESS_REPORT.md`
- `docs/internal/R4_PROGRESS_REPORT.md`
- `docs/internal/DEBUG_TOOL_PLAN.md`
- `docs/internal/D1_DEBUG_LAYER_AGENT_GUIDE.md`

### B. 내부 설계/규칙/참조
- `docs/internal/DEVELOPMENT_GUIDE.md`
- `docs/internal/FEATURE_SPECS.md`
- `docs/internal/CLASS_CATALOG.md`
- `docs/internal/ARCHITECTURE_C4.md`
- `docs/internal/QUERY_BASED_ANALYSIS_PIPELINE.md`
- `docs/internal/LIGHTRAG_OPERATIONS_GUIDE.md`
- `docs/internal/AGENT_STRATEGY.md`

### C. 공개 문서 (사용자/기여자)
- `docs/README.md`, `docs/INDEX.md`, `docs/STATUS.md`
- `docs/README.ko.md`
- `docs/USER_GUIDE.md`, `docs/CLI_GUIDE.md`, `docs/DEV_GUIDE.md`
- `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`
- `docs/OBSERVABILITY_PLAYBOOK.md`, `docs/tutorials/*`

### D. Enterprise 문서
- `docs/enterprise/ENTERPRISE_READINESS.md`
- `docs/enterprise/IMPLEMENTATION_PLAN.md`

### E. API 문서
- `docs/api/**`

---

## 2) 통합 원칙 (위계적 클러스터링)

1. **A → B → C → D/E** 순서로 정리
2. 먼저 **비슷한 성격의 문서끼리 합치고**, 그 다음 최신화
3. SSoT는 고정:
   - 병렬 작업 기준: `docs/internal/PARALLEL_WORK_PLAN.md`
   - 진행 상태: `docs/internal/STATUS.md`
   - 공개 로드맵: `docs/ROADMAP.md`
4. 2027+ 계획은 “장기”가 아닌 **근시일 착수**로 재분류

---

## 3) 통합 대상 (1차)

### A 클러스터 통합
- `docs/internal/STATUS.md` 중심으로 **O1_*.md, R1~R4 보고서, D1 요약**을 묶어
  - 상태 요약 → 샘플/산출물 → 리스크/다음 단계 순으로 재정렬
- `docs/internal/O1_PARALLEL_STATUS.md`는 **스냅샷/요약**으로 축소 또는 아카이브 이동

### C 클러스터 통합
- `docs/README.md` + `docs/INDEX.md` → **단일 Docs Hub**로 통합
- `docs/STATUS.md`는 내부 STATUS와 충돌하지 않도록 **공개용 요약판**으로 축소
- `docs/ROADMAP.md`에서 **2027+ 항목을 “근시일 착수”로 재분류**

---

## 4) 작업 체크리스트

- [ ] A 클러스터 통합 계획 상세화 (섹션 구조 확정)
- [ ] A 클러스터 통합 실행 및 링크 정합성 보정
- [ ] C 클러스터 통합 계획 상세화 (Docs Hub 중심)
- [ ] C 클러스터 통합 실행 및 ROADMAP 재분류
- [ ] 폴더 재구성 필요 여부 결정 (필요 시 이동/리다이렉트)

---

## 5) 진행 기록

- 2026-01-04: 계획 문서 생성 및 1차 클러스터 맵 확정
