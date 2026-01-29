# 병렬 작업 승인 체계 (공유 스키마/공유 파일)

## 목적
- 병렬 작업 중 충돌을 방지하기 위해 공유 스키마/공유 파일 변경 절차를 정의한다.

---

## 1) 공유 파일 목록
- `src/evalvault/adapters/inbound/cli/commands/__init__.py`
- `src/evalvault/adapters/inbound/cli/app.py`
- `src/evalvault/domain/services/async_batch_executor.py`
- 리포트 템플릿/공통 JSON 스키마
  - `docs/guides/CLI_PARALLEL_FEATURES_SPEC.md`
  - `docs/guides/RAG_NOISE_REDUCTION_GUIDE.md`
- `docs/handbook/CHAPTERS/03_workflows.md`

## 2) 공유 스키마 목록
- artifacts/index.json
- CLI JSON envelope
- stage metrics naming conventions
- comparison/benchmark output JSON

---

## 3) 승인 절차
1. 변경 요청 등록 (작업 ID/오너/목적)
2. 영향 범위 검토 (관련 에픽 오너 확인)
3. 변경 승인 (2명 이상 승인 권장)
4. 변경 적용 + 검증 (테스트/리포트 생성)
5. 변경 로그 기록 (run_id 또는 작업 ID 연결)

---

## 4) 변경 금지 원칙
- 승인 없는 공유 스키마/파일 변경 금지
- 공통 포맷 변경 시 문서/테스트 업데이트 동반
- 승인 없이 commands/__init__.py 수정 금지

---

## 5) 변경 요청 템플릿
```
[CHANGE REQUEST]
- Work ID:
- Owner:
- Target File/Schema:
- Reason:
- Impacted Epics:
- Validation Plan:
- Rollback Plan:
```
