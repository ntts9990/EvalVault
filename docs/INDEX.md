# EvalVault 문서 인덱스

> Last Updated: 2026-01-27

이 디렉터리(`docs/`)는 **사용자/기여자에게 필요한 문서만** 유지합니다.

- 비슷한 문서는 통합(중복 제거)
- 과거 작업 로그/계획/리포트 성격 문서는 삭제(필요 시 Git 히스토리로 추적)
- "현재 동작"과 맞지 않는 내용은 최신화 후 남김

---

## 빠른 링크

- 교과서형 총정리(handbook, SSoT): `handbook/INDEX.md`
- 워크플로/명령 템플릿: `handbook/CHAPTERS/03_workflows.md`
- 운영/런북(로컬/DB/오프라인 포함): `handbook/CHAPTERS/04_operations.md`
- 데이터/메트릭/임계값/산출물: `handbook/CHAPTERS/02_data_and_metrics.md`

참고(특수 주제):

- 폐쇄망 Docker: `guides/OFFLINE_DOCKER.md`
- 폐쇄망 모델 캐시: `guides/OFFLINE_MODELS.md`
- 진단 플레이북: `guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md`
- RAGAS 인간 피드백 보정: `guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- 실행 결과 엑셀 시트: `guides/EVALVAULT_RUN_EXCEL_SHEETS.md`
- 평가 리포트 템플릿: `templates/eval_report_templates.md`
- Open RAG Trace 스펙: `architecture/open-rag-trace-spec.md`

---

## 문서 구조

```
docs/
├── INDEX.md                     # 문서 허브 (이 문서)
├── STATUS.md                    # deprecated (handbook로 통합)
├── ROADMAP.md                   # deprecated (handbook로 통합)
├── getting-started/
│   └── INSTALLATION.md          # deprecated (handbook로 통합)
├── guides/
│   ├── USER_GUIDE.md            # deprecated (handbook로 통합)
│   ├── DEV_GUIDE.md             # deprecated (handbook로 통합)
│   ├── EVALVAULT_RUN_EXCEL_SHEETS.md             # 실행 결과 엑셀 컬럼 설명
│   ├── CLI_MCP_PLAN.md          # deprecated (handbook로 통합)
│   ├── WEBUI_CLI_ROLLOUT_PLAN.md # deprecated (handbook로 통합)
│   ├── RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md  # RAGAS 보정 방법론
│   ├── EVALVAULT_DIAGNOSTIC_PLAYBOOK.md          # 진단 플레이북
│   ├── RELEASE_CHECKLIST.md     # 배포 체크리스트
│   ├── P1_P4_WORK_PLAN.md       # deprecated (handbook로 통합)
│   ├── OPEN_RAG_TRACE_*.md      # Open RAG Trace 샘플/내부 래퍼
│   └── OPEN_RAG_TRACE_*.md
├── architecture/
│   ├── open-rag-trace-spec.md   # Open RAG Trace 스펙
│   └── open-rag-trace-collector.md
├── api/                         # mkdocstrings 기반 API 레퍼런스
├── new_whitepaper/              # deprecated (handbook로 통합)
├── handbook/                    # 교과서형 총정리(SSoT)
├── templates/                   # 데이터셋/KG/문서 템플릿
├── tools/                       # 문서 생성/유틸
└── stylesheets/                 # mkdocs 테마 CSS
```

---

## 문서 운영 원칙

- "무엇이 정답인가"는 문서가 아니라 **코드/테스트/CLI 도움말**이 최우선입니다.
- 문서가 코드와 어긋나면 문서를 최신화하거나 삭제합니다.
- 큰 변경(설계/운영/보안/품질 기준)은 `handbook/`에 먼저 반영하고, 필요한 부분만 `guides/`로 노출합니다.
