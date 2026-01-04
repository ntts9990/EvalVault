# 에이전트 퀘스트 로그: 정책 준수 리뷰 (R1~R4/D1/O1)

> 업데이트: 2026-01-07
> 범위: R1, R2, R3, R4, D1, O1(오케스트레이션) 현황 기준의 구조/정책 준수 점검
> 주의: 최신 상태는 일부 문서와 상충할 수 있으므로 코드/스모크 산출물과 함께 판단

---

## 월드 맵 (헥사고날/클린 아키텍처 시야)

```
   [사용자/운영자]
         |
   Inbound Adapters
   (CLI, Web UI)
         |
   Inbound Ports
         |
   Domain
  (entities/services/metrics)
         |
   Outbound Ports
         |
   Outbound Adapters
 (LLM/NLP/KG/Storage/Tracker/Debug)
         |
   External Systems
 (SQLite, LLM APIs, Langfuse/Phoenix, FS)
```

관찰 포인트
- 의존성 방향은 **Inbound → Domain → Outbound**가 이상적
- StageEvent/StageMetric은 Domain 중심, 저장/렌더링은 Adapter에서 처리
- CLI 변경은 P4.1 이후 조율 필요

---

## 퀘스트 보드 (에이전트별 상태)

| 퀘스트 | 상태 | 핵심 산출물 | 정책 준수 요약 |
| --- | --- | --- | --- |
| R1: Retriever 파이프라인 | 완료 | run_id/DB/stage_report/stage_events | Hex/Clean 준수, CLI 변경(P4.1 충돌 위험) |
| R2: GraphRAG | 완료 | GraphRAG retriever + 샘플 산출물 | Hex/Clean 준수, CLI 변경(P4.1 충돌 위험) |
| R3: 대용량 최적화 | 중간 완료 | 병렬 KG/FAISS/스트리밍 + 성능 로그 | Hex 준수, 성능 스크립트 중심 |
| R4: 벤치마크 | 진행/완료 혼재 | ground_truth 스키마/벤치마크 CLI | Hex 준수, CLI 조율 필요 |
| D1: DebugReport | 구현 완료(검증 일부) | DebugReportService + 렌더러 | Domain→config 의존성 이슈 |
| O1: 오케스트레이션 | 진행 | 상태 문서/샘플 수집 | 문서 정합성 이슈 있음 |

---

## 연쇄 이벤트(퀘스트 체인)

### 체인 A: Retrieval 메타데이터 계약
- R1 (retriever 메타데이터 기록) → R2 (GraphRAG 확장) → R3 (성능 attributes) → R4 (doc_id 매핑) → D1 (DebugReport 렌더링)

### 체인 B: 관측성/로깅 정합성
- R3 (Langfuse/Phoenix 메타데이터) → D1 (trace URL 렌더링)
- **P4.1 이후** CLI/로깅 표면 정리 필요

### 체인 C: 벤치마크/ground_truth
- R4 ground_truth → R1/R2/R3 doc_id 규칙 정합성 → D1 리포트 품질 진단

---

## 정책 준수 검토 (Hex/Clean/TDD/YAGNI/SOLID)

### R1 (Retriever 파이프라인)
- **Hex/Clean**: retriever 포트(ports) + 구현(adapters) 분리 흐름 유지
- **TDD**: unit/integration 테스트 존재, 스모크 스크립트도 제공
- **YAGNI**: 필요한 최소 CLI 옵션 중심이나, CLI 수정은 P4.1 조율 필요
- **SOLID**: StageEventBuilder는 역할 집중, 의존성 방향 양호

### R2 (GraphRAG)
- **Hex/Clean**: GraphRAG 구현은 outbound adapter에 집중
- **TDD**: GraphRAGRetriever/NetworkX 테스트 존재
- **YAGNI**: 캐시/키워드 추출은 범위 내 합리적
- **SOLID**: Retriever 자체 책임은 명확하나, 설정 파라미터가 많아 확장 시 분리 고려

### R3 (대용량 최적화)
- **Hex/Clean**: 병렬 KG/FAISS/스트리밍이 outbound adapter에 위치
- **TDD**: 관련 단위 테스트 및 스모크 스크립트 존재
- **YAGNI**: GPU/FAISS 옵션은 optional/flags로 분리되어 과도하지 않음
- **SOLID**: Dense retriever 기능 확장으로 단일 책임이 커짐(추후 분리 고려)

### R4 (벤치마크)
- **Hex/Clean**: benchmark runner는 domain, CLI는 inbound 분리
- **TDD**: retrieval_metrics 중심의 유닛 테스트 확인
- **YAGNI**: 출력 포맷/메트릭은 요구 범위 내
- **SOLID**: 책임 분리 양호, 다만 CLI 조율 필요

### D1 (DebugReport)
- **Hex/Clean**: Domain 서비스가 StageStoragePort/StoragePort로 접근 (양호)
- **TDD**: DebugReportService/Renderer 테스트 부재
- **YAGNI**: Markdown/JSON 렌더링은 MVP 범위 내
- **SOLID**: `DebugReportService`가 config 모듈에 의존(클린 경계 위반 가능)

### O1 (오케스트레이션)
- **Hex/Clean/TDD**: 문서 중심 작업이라 코드 영향 최소
- **YAGNI**: 문서 과잉 분산 위험(상충 정보 발생)

---

## 위협/리스크(보스전)

1. **P4.1 이후 CLI/로깅 조율 위반 가능성**
   - R1/R2/R4에서 CLI 변경이 발생해 조율 충돌 위험
2. **D1 Clean Architecture 경계 위반**
   - `DebugReportService`가 `config/*_support.py`에 직접 의존
3. **TDD 공백**
   - DebugReportService/Renderer 테스트 부재 → 회귀 위험
4. **문서 정합성 불일치**
   - run_id/샘플 경로가 `STATUS.md` vs `O1_PARALLEL_STATUS.md`에서 상이
5. **워크트리 분산**
   - web/cli 관련 변경이 별도 worktree에 누적되어 통합 충돌 가능

---

## 퀘스트 TODO (다음 액션)

1. **O1**: 상태 문서 단일화(`docs/internal/STATUS.md`) 기준으로 정리
2. **D1**: DebugReportService/Renderer 단위 테스트 추가
3. **R1/R2/R4**: P4.1 이후 CLI/로깅 옵션 통합/정리 작업 예약
4. **R3**: 성능 JSONL ↔ StageEvent 매핑 가이드 확정 문서화 보강
5. **R4**: retrieval benchmark 결과/지표 요약을 상태 문서에 반영
6. **워크트리 통합 전**: 각 worktree의 변경 이력/문서 충돌 확인

---

## 병렬 작업 방법 (레이드 운영 규칙)

목표: 충돌 최소화 + Hex/Clean/TDD/YAGNI/SOLID 정책 유지

1) **사전 체크**
   - `docs/internal/PARALLEL_WORK_PLAN.md`에서 수정 금지 영역 확인
   - 상태/샘플 경로는 `docs/internal/STATUS.md`만 최신화

2) **워크트리/브랜치 운영**
   - 에이전트 1명당 **브랜치 1개 + worktree 1개** 원칙
   - 공용 파일(`pyproject.toml`, `src/evalvault/__init__.py`, `src/evalvault/config/settings.py`, `README.md`) 수정은 사전 공유

3) **수정 범위 고정**
   - R1/R2/R3/R4는 각 트랙의 수정 가능 영역만 변경
   - **CLI 변경은 P4.1 이후**로 이관(조율 필요)

4) **TDD/검증**
   - 신규 로직은 단위 테스트 먼저 추가
   - 스모크/통합 테스트는 최소 fixture로 확인

5) **산출물/증거 관리**
   - run_id, DB, stage_events, stage_report를 확보해 `scratch/` 또는 `reports/`에 보관
   - 리포트/DB 파일은 gitignore 대상이므로 **경로만 문서화**

6) **핸드오프 규칙**
   - D1 요청 포맷(템플릿)을 그대로 사용해 전달
   - O1은 `STATUS.md`만 갱신, 다른 문서는 참고용으로 유지

7) **충돌 대응**
   - 병합 전 `git status`로 작업 범위 점검
   - 충돌 예상 시 오케스트레이터 조율 후 통합

---

## 워크트리 체크(요약)

- 확인된 worktree:
  - `/Users/isle/PycharmProjects/EvalVault` (현재)
  - `/Users/isle/.claude-worktrees/EvalVault/cool-knuth`
  - `/Users/isle/.cursor/worktrees/EvalVault/{eol,kib,pot,xsp}`
- eol/kib/pot/xsp는 주로 **CLI/Web** 변경이 누적된 상태
- 본 리뷰는 현재 워크트리 기준이며, 통합 전 추가 리뷰 필요
