# EvalVault 문서 인덱스

> **Last Updated**: 2026-01-03

이 문서는 EvalVault 문서의 구조와 각 문서의 목적을 설명합니다.

---

## 📚 문서 구조

```
docs/
├── 📖 배포용 문서 (Public)
│   ├── README.ko.md           # 한국어 README
│   ├── USER_GUIDE.md          # 사용자 가이드
│   ├── CLI_GUIDE.md           # CLI 참조
│   ├── ARCHITECTURE.md        # 아키텍처 가이드
│   ├── ROADMAP.md             # 개발 로드맵
│   ├── OBSERVABILITY_PLAYBOOK.md  # Phoenix 운영 가이드
│   └── tutorials/             # 튜토리얼 (7개)
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

## 📖 배포용 문서

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
| [ROADMAP.md](ROADMAP.md) | 모든 사용자 | 현재 상태, 향후 계획, 마일스톤 |

---

## 🔧 개발용 문서

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

`internal/archive/` 폴더에는 완료되었거나 다른 문서로 통합된 히스토리 문서가 있습니다:

- COMPLETED.md - 달성 기록 (→ DEVELOPMENT_GUIDE.md로 통합)
- IMPROVEMENT_PLAN.md - 개선 계획 (→ DEVELOPMENT_GUIDE.md로 통합)
- PARALLEL_*.md - 병렬 작업 계획 (→ DEVELOPMENT_GUIDE.md로 통합)
- KOREAN_RAG_OPTIMIZATION.md - (→ FEATURE_SPECS.md + tutorials로 통합)
- DOMAIN_MEMORY_USAGE.md - (→ USER_GUIDE.md + tutorials로 통합)
- ARCHITECTURE_AUDIT.md - 아키텍처 감사 (→ DEVELOPMENT_GUIDE.md 부록)
- RAG_PERFORMANCE_DATA_STRATEGY_FINAL.md - Phoenix 전략 (→ FEATURE_SPECS.md로 통합)
- QWEN3_EMBEDDING_INTEGRATION.md - (→ FEATURE_SPECS.md로 통합)

---

## 📋 문서별 권장 독자

| 역할 | 권장 문서 |
|------|----------|
| **처음 사용자** | README.ko → tutorials/01 → USER_GUIDE |
| **평가 담당자** | USER_GUIDE → CLI_GUIDE → tutorials/02-07 |
| **운영팀** | OBSERVABILITY_PLAYBOOK → tutorials/06 |
| **개발자** | ARCHITECTURE → internal/DEVELOPMENT_GUIDE → ROADMAP |
| **아키텍트** | ARCHITECTURE → internal/CLASS_CATALOG → internal/ARCHITECTURE_C4 |
| **기여자** | ../CONTRIBUTING.md → internal/DEVELOPMENT_GUIDE |

---

## 🔄 문서 업데이트 규칙

1. **배포용 문서**: 기능 변경 시 즉시 업데이트
2. **개발용 문서**: 개발 완료 후 정리
3. **아카이브**: 완료된 문서는 `internal/archive/`로 이동
4. **인덱스**: 새 문서 추가 시 이 문서 업데이트

---

**문서 담당**: EvalVault 팀
**최종 업데이트**: 2026-01-03
