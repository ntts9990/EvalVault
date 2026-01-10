# EvalVault 문서 인덱스

> **Last Updated**: 2026-01-10

이 디렉터리(`docs/`)는 **배포/공개용 문서**와 **개발·운영 내부용 문서**를 분리하여 관리합니다.
목적, 기능, 시점에 따라 아래 구조를 참고하세요.

---

## 📚 문서 구조

```
docs/
├── 📖 배포용 문서 (Public)
│   ├── INDEX.md                     # 문서 허브 (이 문서)
│   ├── getting-started/INSTALLATION.md
│   ├── guides/USER_GUIDE.md        # 통합 사용자 가이드
│   ├── architecture/ARCHITECTURE.md # 통합 아키텍처 가이드
│   ├── status/                      # STATUS/ROADMAP
│   ├── templates/                   # 데이터셋/KG/문서 템플릿
│   └── tutorials/                   # 핵심 튜토리얼 (01, 02, 04, 07)
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
| [README.md](../../README.md) | 모든 사용자 | 한국어 README, 빠른 시작 가이드 |
| [README.en.md](../../README.en.md) | 모든 사용자 | 영어 README, Quickstart guide |
| [getting-started/INSTALLATION.md](getting-started/INSTALLATION.md) | 처음 사용자 | 설치/환경 설정 |
| [tutorials/01-quickstart.md](tutorials/01-quickstart.md) | 처음 사용자 | 5분 빠른 시작 |

### 사용 가이드

| 문서 | 대상 | 설명 |
|------|------|------|
| [guides/USER_GUIDE.md](guides/USER_GUIDE.md) | 모든 사용자 | 통합 사용자 가이드 (CLI, Web UI, 분석 워크플로, Domain Memory, 관측성, 프롬프트 관리, 성능 튜닝, 메서드 플러그인, 문제 해결) |
| [guides/open-rag-trace-samples.md](guides/open-rag-trace-samples.md) | 개발자 | Open RAG Trace 최소 계측 샘플 |
| [guides/open-rag-trace-internal-adapter.md](guides/open-rag-trace-internal-adapter.md) | 개발자 | 내부 시스템 최소 계측 래퍼 가이드 |

**USER_GUIDE.md에 통합된 내용**:
- CLI 명령어 참조 (기존 CLI_GUIDE.md)
- 분석 워크플로 (기존 ANALYSIS_WORKFLOW.md)
- 프롬프트 관리 (기존 PROMPT_MANAGEMENT.md)
- 성능 튜닝 (기존 RAGAS_PERFORMANCE_TUNING.md)
- 관측성 & Phoenix (기존 OBSERVABILITY_PLAYBOOK.md)
- 메서드 플러그인 (기존 method_plugins.md)

### 튜토리얼

| 번호 | 문서 | 주제 |
|------|------|------|
| 01 | [01-quickstart.md](tutorials/01-quickstart.md) | 5분 빠른 시작 |
| 02 | [02-basic-evaluation.md](tutorials/02-basic-evaluation.md) | 기본 평가 실행 |
| 04 | [04-phoenix-integration.md](tutorials/04-phoenix-integration.md) | Phoenix 통합 |
| 07 | [07-domain-memory.md](tutorials/07-domain-memory.md) | Domain Memory 활용 |

**통합/삭제된 튜토리얼**:
- 03-custom-metrics.md → USER_GUIDE.md에 통합
- 05-korean-rag.md → USER_GUIDE.md에 통합
- 06-production-tips.md → USER_GUIDE.md에 통합

### 아키텍처 및 로드맵

| 문서 | 대상 | 설명 |
|------|------|------|
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 개발자/아키텍트 | 통합 아키텍처 가이드 (Hexagonal Architecture, 프로젝트 개요, 소스 구조, 확장 지점, 구조 파악 방법론) |
| [architecture/open-rag-trace-spec.md](architecture/open-rag-trace-spec.md) | 개발자/아키텍트 | OpenTelemetry + OpenInference 기반 RAG 트레이싱 표준 초안 |
| [architecture/open-rag-trace-collector.md](architecture/open-rag-trace-collector.md) | 개발자/아키텍트 | Open RAG Trace Collector 구성 예시 |
| [status/ROADMAP.md](status/ROADMAP.md) | 모든 사용자 | 향후 계획, 마일스톤 |
| [status/STATUS.md](status/STATUS.md) | 모든 사용자 | 현재 상태 요약 (버전, 테스트, 완료 항목) |

**ARCHITECTURE.md에 통합된 내용**:
- 프로젝트 미션 및 핵심 기능 (기존 PROJECT_OVERVIEW.md)
- 소스 구조 요약 (기존 PROJECT_SOURCE_GUIDE.md)
- 구조 파악 방법론 요약 (기존 PROJECT_STRUCTURE_METHODS.md)

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
| **처음 사용자** | README.md → tutorials/01 → guides/USER_GUIDE |
| **평가 담당자** | guides/USER_GUIDE → tutorials/02, 04, 07 |
| **운영팀** | guides/USER_GUIDE (관측성 & Phoenix 섹션) → tutorials/04 |
| **개발자** | architecture/ARCHITECTURE → internal/reference/DEVELOPMENT_GUIDE |
| **아키텍트** | architecture/ARCHITECTURE → internal/reference/CLASS_CATALOG → internal/reference/ARCHITECTURE_C4 |
| **기여자** | [CONTRIBUTING.md](../../CONTRIBUTING.md) → architecture/ARCHITECTURE → internal/reference/DEVELOPMENT_GUIDE |

---

## 🔄 문서 운영 규칙

1. **현재 상태**: `internal/status/STATUS.md`가 단일 진실 소스 (진행/산출물)
2. **배포용 문서**: 기능 변경 시 즉시 업데이트
3. **개발용 문서**: 개발 완료 후 정리
4. **아카이브**: 완료된 작업 추적 문서는 `internal/archive/`로 이동
5. **인덱스**: 새 문서 추가 시 `INDEX.md` 업데이트

---

## 📝 주요 변경 사항 (2026-01-09)

### 통합된 문서
- `guides/CLI_GUIDE.md` → `guides/USER_GUIDE.md`에 통합
- `guides/ANALYSIS_WORKFLOW.md` → `guides/USER_GUIDE.md`에 통합
- `guides/PROMPT_MANAGEMENT.md` → `guides/USER_GUIDE.md`에 통합
- `guides/RAGAS_PERFORMANCE_TUNING.md` → `guides/USER_GUIDE.md`에 통합
- `guides/OBSERVABILITY_PLAYBOOK.md` → `guides/USER_GUIDE.md`에 통합
- `method_plugins.md` → `guides/USER_GUIDE.md`에 통합
- `PROJECT_OVERVIEW.md` → `architecture/ARCHITECTURE.md`에 통합
- `PROJECT_SOURCE_GUIDE.md` → `architecture/ARCHITECTURE.md`에 통합
- `guides/PROJECT_STRUCTURE_METHODS.md` → `architecture/ARCHITECTURE.md`에 통합

### 삭제된 문서
- `tutorials/03-custom-metrics.md` (USER_GUIDE에 통합)
- `tutorials/05-korean-rag.md` (USER_GUIDE에 통합)
- `tutorials/06-production-tips.md` (USER_GUIDE에 통합)

### 언어 변경
- `README.md` → 한국어 버전 (기존 `README.ko.md` 내용)
- `README.en.md` → 영어 버전 (기존 `README.md` 내용)

---

**문서 담당**: EvalVault 팀
**최종 업데이트**: 2026-01-09
