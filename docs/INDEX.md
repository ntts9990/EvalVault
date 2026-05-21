# EvalVault 문서 인덱스

> Last Updated: 2026-05-21

이 디렉터리(`docs/`)는 **사용자/기여자에게 필요한 문서만** 유지합니다.

- 비슷한 문서는 통합(중복 제거)
- 과거 작업 로그/계획/리포트 성격 문서는 삭제(필요 시 Git 히스토리로 추적)
- "현재 동작"과 맞지 않는 내용은 최신화 후 남김

---

## 진입점 (Entry points)

> 인수팀/신규 기여자는 아래 순서대로 읽습니다.

1. [`PROJECT_STATE.md`](PROJECT_STATE.md) — **SSoT**. 현재 구현 현황·CLI 표면·운영·로드맵 요약. 이 프로젝트를 처음 보는 사람의 진입 문서.
2. [`REFACTOR_DIAGNOSIS.md`](REFACTOR_DIAGNOSIS.md) — 누적 부담의 슬라이스 단위 해체 계획. 진행 중인 리팩터 슬라이스 마스터 테이블.
3. [`handbook/INDEX.md`](handbook/INDEX.md) — 교과서형 총정리(handbook, 내부 SSoT 상세본).

---

## 빠른 링크

- 워크플로/명령 템플릿: [`handbook/CHAPTERS/03_workflows.md`](handbook/CHAPTERS/03_workflows.md)
- 운영/런북(로컬/DB/오프라인 포함, 구 USER_GUIDE 대체): [`handbook/CHAPTERS/04_operations.md`](handbook/CHAPTERS/04_operations.md)
- 데이터/메트릭/임계값/산출물(구 KG plan 통합): [`handbook/CHAPTERS/02_data_and_metrics.md`](handbook/CHAPTERS/02_data_and_metrics.md)
- 아키텍처 상세(구 ARCHITECTURE 대체): [`handbook/CHAPTERS/01_architecture.md`](handbook/CHAPTERS/01_architecture.md)
- 로드맵 SSoT(구 ROADMAP 대체): [`handbook/CHAPTERS/08_roadmap.md`](handbook/CHAPTERS/08_roadmap.md)

참고(특수 주제):

- 폐쇄망 Docker: [`guides/OFFLINE_DOCKER.md`](guides/OFFLINE_DOCKER.md)
- 폐쇄망 모델 캐시: [`guides/OFFLINE_MODELS.md`](guides/OFFLINE_MODELS.md)
- 진단 플레이북: [`guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md`](guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md)
- RAGAS 인간 피드백 보정: [`guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`](guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md)
- 실행 결과 엑셀 시트: [`guides/EVALVAULT_RUN_EXCEL_SHEETS.md`](guides/EVALVAULT_RUN_EXCEL_SHEETS.md)
- 평가 리포트 템플릿: [`templates/eval_report_templates.md`](templates/eval_report_templates.md)
- Open RAG Trace 스펙: [`architecture/open-rag-trace-spec.md`](architecture/open-rag-trace-spec.md)

---

## 문서 구조

```
docs/
├── INDEX.md                     # 문서 허브 (이 문서)
├── PROJECT_STATE.md             # SSoT (인수팀 진입 문서)
├── REFACTOR_DIAGNOSIS.md        # 슬라이스 단위 리팩터 진행 계획
├── STATUS.md                    # deprecated (handbook로 통합, DOC-S3에서 정리 예정)
├── ROADMAP.md                   # deprecated (handbook/CHAPTERS/08_roadmap.md로 통합)
├── getting-started/
│   └── INSTALLATION.md          # deprecated (handbook/CHAPTERS/04_operations.md로 통합)
├── guides/
│   ├── EVALVAULT_RUN_EXCEL_SHEETS.md             # 실행 결과 엑셀 컬럼 설명
│   ├── RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md # RAGAS 보정 방법론
│   ├── EVALVAULT_DIAGNOSTIC_PLAYBOOK.md          # 진단 플레이북
│   ├── RELEASE_CHECKLIST.md     # 배포 체크리스트
│   ├── OFFLINE_DOCKER.md        # 폐쇄망 Docker 배포
│   ├── OFFLINE_MODELS.md        # 폐쇄망 모델 캐시
│   └── OPEN_RAG_TRACE_*.md      # Open RAG Trace 샘플/내부 래퍼
├── architecture/
│   ├── open-rag-trace-spec.md   # Open RAG Trace 스펙
│   └── open-rag-trace-collector.md
├── api/                         # mkdocstrings 기반 API 레퍼런스
├── handbook/                    # 교과서형 총정리(SSoT 상세본)
├── templates/                   # 데이터셋/KG/문서 템플릿
├── tools/                       # 문서 생성/유틸
└── stylesheets/                 # mkdocs 테마 CSS
```

> `docs/` 최상위에서 다음 문서들은 모두 deprecated(파일이 존재하지 않거나 스텁): `USER_GUIDE`, `ARCHITECTURE`, `COMPLETED`, `IMPROVEMENT_PLAN`, `KG_IMPROVEMENT_PLAN`. handbook과 `PROJECT_STATE.md`가 진입점입니다. 마찬가지로 `docs/new_whitepaper/`는 handbook으로 통합되어 더 이상 nav에 노출하지 않습니다.

---

## 문서 운영 원칙

- "무엇이 정답인가"는 문서가 아니라 **코드/테스트/CLI 도움말**이 최우선입니다.
- 문서가 코드와 어긋나면 문서를 최신화하거나 삭제합니다.
- 큰 변경(설계/운영/보안/품질 기준)은 `handbook/`에 먼저 반영하고, 필요한 부분만 `guides/`로 노출합니다.
