# EvalVault 문서 인덱스

> **Last Updated**: 2026-01-06

이 디렉터리(`docs/`)는 **배포/공개용 문서**와 **개발·운영 내부용 문서**를 분리하여 관리합니다.
목적, 기능, 시점에 따라 아래 구조를 참고하세요.

---

## 📚 문서 구조

```
docs/
├── 📖 배포용 문서 (Public)
│   ├── INDEX.md                     # 문서 허브 (이 문서)
│   ├── README.ko.md                 # 한국어 README
│   ├── PROJECT_OVERVIEW.md          # 프로젝트 목표/추상화 문서
│   ├── PROJECT_SOURCE_GUIDE.md      # 소스 레벨 가이드
│   ├── getting-started/INSTALLATION.md
│   ├── guides/                      # USER/CLI/DEV/OBS 가이드
│   ├── architecture/ARCHITECTURE.md # 아키텍처 가이드
│   ├── status/                      # STATUS/ROADMAP
│   ├── templates/                   # 데이터셋/KG/문서 템플릿
│   └── tutorials/                   # 7개 튜토리얼
│
└── 🔧 개발용 문서 (Internal)
    └── internal/
        ├── reference/               # 설계/스펙/카탈로그
        ├── plans/                   # 작업 계획/리팩토링
        ├── reports/                 # 완료/진행 리포트
        ├── status/                  # 내부 상태 SSoT
        ├── logs/                    # 운영 로그
        ├── guides/                  # 운영 가이드
        └── archive/                 # 아카이브 (완료/통합)
```

---

## 📖 배포용 문서 (Public)

### 시작하기

| 문서 | 대상 | 설명 |
|------|------|------|
| [README.ko.md](README.ko.md) | 모든 사용자 | 한국어 README, 빠른 시작 가이드 |
| [getting-started/INSTALLATION.md](getting-started/INSTALLATION.md) | 처음 사용자 | 설치/환경 설정 |
| [tutorials/01-quickstart.md](tutorials/01-quickstart.md) | 처음 사용자 | 5분 빠른 시작 |

### 사용 가이드

| 문서 | 대상 | 설명 |
|------|------|------|
| [guides/USER_GUIDE.md](guides/USER_GUIDE.md) | 평가 담당자 | 설치, 환경설정, CLI, Web UI, 트러블슈팅 |
| [guides/CLI_GUIDE.md](guides/CLI_GUIDE.md) | CLI 사용자 | 명령어 참조, 옵션, 예시 |
| [guides/DEV_GUIDE.md](guides/DEV_GUIDE.md) | 기여자/개발자 | 로컬 개발 루틴 (테스트, 린트) |
| [guides/PROJECT_STRUCTURE_METHODS.md](guides/PROJECT_STRUCTURE_METHODS.md) | 개발자/기여자 | 프로젝트 구조 파악 방법론 모음 |
| [guides/structure-methods/01-folder-topology.md](guides/structure-methods/01-folder-topology.md) | 개발자/기여자 | 구조 파악: 폴더 지형도 + 책임 태깅 |
| [guides/structure-methods/02-hexagonal-layer-map.md](guides/structure-methods/02-hexagonal-layer-map.md) | 개발자/기여자 | 구조 파악: 헥사고날 레이어 맵 |
| [guides/structure-methods/03-entrypoint-flow.md](guides/structure-methods/03-entrypoint-flow.md) | 개발자/기여자 | 구조 파악: 엔트리포인트 흐름 추적 |
| [guides/structure-methods/04-c4-component-view.md](guides/structure-methods/04-c4-component-view.md) | 개발자/기여자 | 구조 파악: C4/컴포넌트 관점 |
| [guides/structure-methods/05-dependency-graph.md](guides/structure-methods/05-dependency-graph.md) | 개발자/기여자 | 구조 파악: 모듈 의존성 그래프 |
| [guides/structure-methods/06-data-config-flow.md](guides/structure-methods/06-data-config-flow.md) | 개발자/기여자 | 구조 파악: 데이터/설정 플로우 |
| [guides/structure-methods/07-test-driven-map.md](guides/structure-methods/07-test-driven-map.md) | 개발자/기여자 | 구조 파악: 테스트 기반 기능 지도 |
| [guides/RAGAS_PERFORMANCE_TUNING.md](guides/RAGAS_PERFORMANCE_TUNING.md) | 개발/운영 | Ragas 평가 속도 최적화 가이드 |
| [guides/OBSERVABILITY_PLAYBOOK.md](guides/OBSERVABILITY_PLAYBOOK.md) | 운영팀 | Phoenix 드리프트 감시, 릴리스 노트 |
| [guides/RELEASE_CHECKLIST.md](guides/RELEASE_CHECKLIST.md) | 운영/개발 | 배포 체크리스트, 릴리즈 노트 템플릿 |
| [guides/STREAMLIT_UI.md](guides/STREAMLIT_UI.md) | 참고 | Streamlit UI(레거시) 간단 미리보기 |

### 튜토리얼

| 번호 | 문서 | 주제 |
|------|------|------|
| 01 | [01-quickstart.md](tutorials/01-quickstart.md) | 5분 빠른 시작 |
| 02 | [02-basic-evaluation.md](tutorials/02-basic-evaluation.md) | 기본 평가 실행 |
| 03 | [03-custom-metrics.md](tutorials/03-custom-metrics.md) | 커스텀 메트릭 추가 |
| 04 | [04-phoenix-integration.md](tutorials/04-phoenix-integration.md) | Phoenix 통합 |
| 05 | [05-korean-rag.md](tutorials/05-korean-rag.md) | 한국어 RAG 최적화 |
| 06 | [06-production-tips.md](tutorials/06-production-tips.md) | 프로덕션 배포 가이드 |
| 07 | [07-domain-memory.md](tutorials/07-domain-memory.md) | Domain Memory 활용 |

### 아키텍처 및 로드맵

| 문서 | 대상 | 설명 |
|------|------|------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | 모든 사용자 | 프로젝트 목표, 범위, 상위 구조 요약 |
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 개발자/아키텍트 | Hexagonal Architecture, 컴포넌트, 데이터 플로우 |
| [PROJECT_SOURCE_GUIDE.md](PROJECT_SOURCE_GUIDE.md) | 개발자/기여자 | 소스 구조, 실행 플로우, 확장 지점 |
| [status/ROADMAP.md](status/ROADMAP.md) | 모든 사용자 | 향후 계획, 마일스톤 |
| [status/STATUS.md](status/STATUS.md) | 모든 사용자 | 현재 상태 요약 (버전, 테스트, 완료 항목) |

---

## 🔧 개발용 문서 (Internal)

> `internal/` 폴더는 EvalVault 개발팀을 위한 내부 문서입니다.

### 핵심 개발 문서

| 문서 | 설명 |
|------|------|
| [reference/DEVELOPMENT_GUIDE.md](internal/reference/DEVELOPMENT_GUIDE.md) | 개발 환경 설정, 아키텍처 원칙, 코드 품질, 에이전트 시스템 |
| [reference/FEATURE_SPECS.md](internal/reference/FEATURE_SPECS.md) | 한국어 RAG, DAG Pipeline, 임베딩, Phoenix, Domain Memory 상세 스펙 |
| [reference/CLASS_CATALOG.md](internal/reference/CLASS_CATALOG.md) | 전체 클래스 분류 (200+ 클래스) |

### 진행/운영 문서 (SSoT 포함)

| 문서 | 설명 |
|------|------|
| [status/STATUS.md](internal/status/STATUS.md) | 내부 상태 단일 진실(진행/산출물) |
| [plans/PARALLEL_WORK_PLAN.md](internal/plans/PARALLEL_WORK_PLAN.md) | 병렬 작업 기준/규칙 |
| [status/O1_PARALLEL_STATUS.md](internal/status/O1_PARALLEL_STATUS.md) | 오케스트레이터 요약 |
| [status/O1_D1_DEBUG_REPORT_SUMMARY.md](internal/status/O1_D1_DEBUG_REPORT_SUMMARY.md) | DebugReport 요약 |
| [plans/DOCS_REFACTOR_PLAN.md](internal/plans/DOCS_REFACTOR_PLAN.md) | 문서 통합/최신화 계획 |

### 설계 문서

| 문서 | 설명 |
|------|------|
| [reference/ARCHITECTURE_C4.md](internal/reference/ARCHITECTURE_C4.md) | C4 모델 기반 계층적 다이어그램 |
| [reference/AGENT_STRATEGY.md](internal/reference/AGENT_STRATEGY.md) | AI 에이전트 활용 전략, 운영 자동화 |
| [reference/QUERY_BASED_ANALYSIS_PIPELINE.md](internal/reference/QUERY_BASED_ANALYSIS_PIPELINE.md) | DAG 분석 파이프라인 설계 |

### 아카이브

`internal/archive/` 폴더에는 완료되었거나 다른 문서로 통합된 히스토리 문서가 있습니다.

---

## 📋 문서별 권장 독자

| 역할 | 권장 문서 순서 |
|------|---------------|
| **처음 사용자** | README.ko → tutorials/01 → guides/USER_GUIDE |
| **평가 담당자** | guides/USER_GUIDE → guides/CLI_GUIDE → tutorials/02-07 |
| **운영팀** | guides/OBSERVABILITY_PLAYBOOK → tutorials/06 |
| **개발자** | guides/DEV_GUIDE → architecture/ARCHITECTURE → internal/reference/DEVELOPMENT_GUIDE |
| **아키텍트** | architecture/ARCHITECTURE → internal/reference/CLASS_CATALOG → internal/reference/ARCHITECTURE_C4 |
| **기여자** | https://github.com/ntts9990/EvalVault/blob/main/CONTRIBUTING.md → guides/DEV_GUIDE → internal/reference/DEVELOPMENT_GUIDE |

---

## 🔄 문서 운영 규칙

1. **현재 상태**: `internal/status/STATUS.md`가 단일 진실 소스 (진행/산출물)
2. **배포용 문서**: 기능 변경 시 즉시 업데이트
3. **개발용 문서**: 개발 완료 후 정리
4. **아카이브**: 완료된 작업 추적 문서는 `internal/archive/`로 이동
5. **인덱스**: 새 문서 추가 시 `INDEX.md` 업데이트

---

**문서 담당**: EvalVault 팀
**최종 업데이트**: 2026-01-06
