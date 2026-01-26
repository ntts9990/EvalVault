# 다음 개발 실행 계획 (P0→P3)

> 기준 문서: `docs/ROADMAP.md`, `docs/security_audit_worklog.md`
> 목적: 문서에 정의된 P0→P3를 **실행 순서/검증 게이트**로 정리

## 실행 원칙
- P0→P3 순차 진행
- 각 단계 완료 시 단위 테스트 + 작업 로그 기록
- 전체 테스트 통과 후 e2e 검증 수행
- e2e 통과 시 커밋/푸시/릴리즈
- CI 실패 시 원인 수정 후 재검증

## 실행 순서

### P0 (안정성/운영)
1) CI/테스트 안정성 강화
   - 목표: 플래키 제거, OS 차이 최소화
   - 검증: `uv run pytest tests -q` 2회 연속 통과

2) 설정/프로필 검증 및 오류 메시지 개선
   - 목표: 온보딩 실패율 감소
   - 검증: `tests/unit/test_settings.py`, `tests/integration/test_cli_integration.py`

### P1 (사용성)
1) Web UI 핵심 워크플로 완성도 향상
   - Run 상세 탭(Staging/Prompts/Gate/Debug)
   - AnalysisLab 연동 강화
   - 검증: `npm run build` (프론트는 코드로만 확인)

2) CLI/웹 공통 경로 규약 UX 노출
   - 문서/UI 일관성 확인

### P2 (관측성/표준)
1) Open RAG Trace 스펙/샘플 확장
2) Collector/보존/PII 마스킹 가이드 강화
3) Stage Events 최소 스키마 표준화 및 문서 동기화

### P3 (성능 개선)
1) KPI/평가 프로토콜/로드맵 정립
2) Retrieval/리랭킹/GraphRAG 지표 통합
3) 노이즈 저감/ordering_warning 운영 기준 정착

## 테스트 게이트
1) 단위 테스트: 변경 범위별 최소 단위 테스트 통과
2) 전체 테스트: `uv run pytest tests -q`
3) e2e 테스트: 백엔드 e2e 실행, 프론트는 코드로만 확인

## 릴리즈 게이트
1) 테스트 통과
2) e2e 통과
3) 커밋/푸시
4) CI 상태 확인 및 실패 시 수정 반복

## 작업 로그
- 작업 완료 시 `.sisyphus/notepads/*/worklog.md`에 기록
