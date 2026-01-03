# EvalVault 문서 허브 (Docs Hub)

> **Last Updated**: 2026-01-03

이 디렉터리(`docs/`)는 **배포/공개용 문서**와 **개발·운영 내부용 문서**를 분리하여 관리합니다.
목적, 기능, 시점에 따라 아래 구조를 참고하세요.

---

## 📚 문서 구조

```
docs/
├── 📖 배포용 문서 (Public)
│   ├── README.md              # 전체 문서 인덱스 (이 문서)
│   ├── README.ko.md           # 한국어 README
│   ├── USER_GUIDE.md          # 사용자 가이드
│   ├── CLI_GUIDE.md           # CLI 참조
│   ├── ARCHITECTURE.md        # 아키텍처 가이드
│   ├── ROADMAP.md             # 개발 로드맵
│   ├── STATUS.md              # 현재 상태 요약
│   ├── OBSERVABILITY_PLAYBOOK.md  # Phoenix 운영 가이드
│   └── tutorials/             # 7개 튜토리얼
│
└── 🔧 개발용 문서 (Internal)
    └── internal/
        ├── DEVELOPMENT_GUIDE.md    # 개발 가이드 (통합)
        ├── FEATURE_SPECS.md        # 기능 상세 스펙
        ├── CLASS_CATALOG.md        # 클래스 카탈로그
        ├── ARCHITECTURE_C4.md      # C4 모델 다이어그램
        ├── AGENT_STRATEGY.md       # AI 에이전트 전략
        ├── QUERY_BASED_ANALYSIS_PIPELINE.md  # DAG 파이프라인 설계
        └── archive/                # 아카이브 (완료/통합된 문서)
```

---

## 📖 배포용 문서 (Public)

### 시작하기

| 문서 | 대상 | 설명 |
|------|------|------|
| [README.ko.md](README.ko.md) | 모든 사용자 | 한국어 README, 빠른 시작 가이드 |
| [tutorials/01-quickstart.md](tutorials/01-quickstart.md) | 처음 사용자 | 5분 빠른 시작 |

### 사용 가이드

| 문서 | 대상 | 설명 |
|------|------|------|
| [USER_GUIDE.md](USER_GUIDE.md) | 평가 담당자 | 설치, 환경설정, CLI, Web UI, 트러블슈팅 |
| [CLI_GUIDE.md](CLI_GUIDE.md) | CLI 사용자 | 명령어 참조, 옵션, 예시 |
| [DEV_GUIDE.md](DEV_GUIDE.md) | 기여자/개발자 | 로컬 개발 루틴 (테스트, 린트) |
| [OBSERVABILITY_PLAYBOOK.md](OBSERVABILITY_PLAYBOOK.md) | 운영팀 | Phoenix 드리프트 감시, 릴리스 노트 |

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
| [ARCHITECTURE.md](ARCHITECTURE.md) | 개발자/아키텍트 | Hexagonal Architecture, 컴포넌트, 데이터 플로우 |
| [ROADMAP.md](ROADMAP.md) | 모든 사용자 | 향후 계획, 마일스톤 |
| [STATUS.md](STATUS.md) | 모든 사용자 | 현재 상태 요약 (버전, 테스트, 완료 항목) |

---

## 🔧 개발용 문서 (Internal)

> `internal/` 폴더는 EvalVault 개발팀을 위한 내부 문서입니다.

### 핵심 개발 문서

| 문서 | 설명 |
|------|------|
| [DEVELOPMENT_GUIDE.md](internal/DEVELOPMENT_GUIDE.md) | 개발 환경 설정, 아키텍처 원칙, 코드 품질, 에이전트 시스템 |
| [FEATURE_SPECS.md](internal/FEATURE_SPECS.md) | 한국어 RAG, DAG Pipeline, 임베딩, Phoenix, Domain Memory 상세 스펙 |
| [CLASS_CATALOG.md](internal/CLASS_CATALOG.md) | 전체 클래스 분류 (200+ 클래스) |

### 설계 문서

| 문서 | 설명 |
|------|------|
| [ARCHITECTURE_C4.md](internal/ARCHITECTURE_C4.md) | C4 모델 기반 계층적 다이어그램 |
| [AGENT_STRATEGY.md](internal/AGENT_STRATEGY.md) | AI 에이전트 활용 전략, 운영 자동화 |
| [QUERY_BASED_ANALYSIS_PIPELINE.md](internal/QUERY_BASED_ANALYSIS_PIPELINE.md) | DAG 분석 파이프라인 설계 |

### 아카이브

`internal/archive/` 폴더에는 완료되었거나 다른 문서로 통합된 히스토리 문서가 있습니다.

---

## 📋 문서별 권장 독자

| 역할 | 권장 문서 순서 |
|------|---------------|
| **처음 사용자** | README.ko → tutorials/01 → USER_GUIDE |
| **평가 담당자** | USER_GUIDE → CLI_GUIDE → tutorials/02-07 |
| **운영팀** | OBSERVABILITY_PLAYBOOK → tutorials/06 |
| **개발자** | DEV_GUIDE → ARCHITECTURE → internal/DEVELOPMENT_GUIDE |
| **아키텍트** | ARCHITECTURE → internal/CLASS_CATALOG → internal/ARCHITECTURE_C4 |
| **기여자** | ../CONTRIBUTING.md → DEV_GUIDE → internal/DEVELOPMENT_GUIDE |

---

## 🔄 문서 운영 규칙

1. **현재 상태**: `STATUS.md`가 단일 진실 소스 (버전, 테스트 수, 완료 항목)
2. **배포용 문서**: 기능 변경 시 즉시 업데이트
3. **개발용 문서**: 개발 완료 후 정리
4. **아카이브**: 완료된 작업 추적 문서는 `internal/archive/`로 이동
5. **인덱스**: 새 문서 추가 시 이 문서 업데이트

---

**문서 담당**: EvalVault 팀
**최종 업데이트**: 2026-01-03
