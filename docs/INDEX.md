# EvalVault 문서 인덱스

> Last Updated: 2026-01-11

이 디렉터리(`docs/`)는 **사용자/기여자에게 필요한 문서만** 유지합니다.

- 비슷한 문서는 통합(중복 제거)
- 과거 작업 로그/계획/리포트 성격 문서는 삭제(필요 시 Git 히스토리로 추적)
- "현재 동작"과 맞지 않는 내용은 최신화 후 남김

---

## 빠른 링크

- 설치: `getting-started/INSTALLATION.md`
- 사용자 가이드(운영 포함): `guides/USER_GUIDE.md`
- 개발/기여: `guides/DEV_GUIDE.md`
- CLI→MCP 이식 계획: `guides/CLI_MCP_PLAN.md`
- Web UI 확장 설계서: `guides/WEBUI_CLI_ROLLOUT_PLAN.md` (1단계 구현 파일 목록 포함)
- RAGAS 인간 피드백 보정: `guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- 진단 플레이북: `guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md` (문제→분석→해석→액션 흐름)
- 실행 결과 엑셀 시트 요약: `guides/EVALVAULT_RUN_EXCEL_SHEETS.md`
- 릴리즈 체크리스트: `guides/RELEASE_CHECKLIST.md`
- 상태 요약: `STATUS.md`
- 로드맵: `ROADMAP.md`
- 개발 백서(설계/운영/품질 기준): `new_whitepaper/INDEX.md`

---

## 문서 구조

```
docs/
├── INDEX.md                     # 문서 허브 (이 문서)
├── STATUS.md                    # 1페이지 상태 요약
├── ROADMAP.md                   # 공개 로드맵
├── getting-started/
│   └── INSTALLATION.md          # 설치/환경 설정
├── guides/
│   ├── USER_GUIDE.md            # 사용/운영 종합 가이드
│   ├── DEV_GUIDE.md             # 개발 루틴/테스트/품질
│   ├── EVALVAULT_RUN_EXCEL_SHEETS.md             # 실행 결과 엑셀 컬럼 설명
│   ├── CLI_MCP_PLAN.md          # CLI→MCP 이식 계획 (Living Doc)
│   ├── WEBUI_CLI_ROLLOUT_PLAN.md # Web UI 확장 설계서
│   ├── RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md  # RAGAS 보정 방법론
│   ├── EVALVAULT_DIAGNOSTIC_PLAYBOOK.md          # 진단 플레이북
│   ├── RELEASE_CHECKLIST.md     # 배포 체크리스트
│   ├── OPEN_RAG_TRACE_*.md      # Open RAG Trace 샘플/내부 래퍼
│   └── OPEN_RAG_TRACE_*.md
├── architecture/
│   ├── open-rag-trace-spec.md   # Open RAG Trace 스펙
│   └── open-rag-trace-collector.md
├── api/                         # mkdocstrings 기반 API 레퍼런스
├── new_whitepaper/              # 개발 백서 (챕터 단위)
├── templates/                   # 데이터셋/KG/문서 템플릿
├── tools/                       # 문서 생성/유틸
└── stylesheets/                 # mkdocs 테마 CSS
```

---

## 문서 운영 원칙

- "무엇이 정답인가"는 문서가 아니라 **코드/테스트/CLI 도움말**이 최우선입니다.
- 문서가 코드와 어긋나면 문서를 최신화하거나 삭제합니다.
- 큰 변경(설계/운영/보안/품질 기준)은 `new_whitepaper/`에 먼저 반영하고, 필요한 부분만 `guides/`로 노출합니다.
