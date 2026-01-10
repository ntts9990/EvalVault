---
title: EvalVault 개발 백서 2026
version: 1.0.0
last_updated: 2026-01-10
maintainers:
  - name: EvalVault Team
    email: team@evalvault.dev
    github: https://github.com/ntts9990/EvalVault

metadata:
  project_name: EvalVault
  project_description: RAG(Retrieval-Augmented Generation) 시스템의 품질 측정 · 관측 · 개선을 한 번에 처리하는 평가 플랫폼
  license: Apache 2.0
  python_version: ">=3.12"

sections:
  - id: 1
    name: 프로젝트 개요
    version: 1.0.0
    status: stable
    last_updated: 2026-01-10
    components:
      - src/evalvault/domain/
      - src/evalvault/config/
    dependencies: []

  - id: 2
    name: 아키텍처 설계
    version: 1.0.0
    status: stable
    last_updated: 2026-01-10
    components:
      - src/evalvault/ports/
      - src/evalvault/adapters/
    dependencies: [1]

  - id: 3
    name: 데이터 흐름 분석
    version: 1.0.0
    status: stable
    last_updated: 2026-01-10
    components:
      - src/evalvault/domain/services/
      - src/evalvault/adapters/inbound/
      - src/evalvault/adapters/outbound/
    dependencies: [1, 2]

  - id: 4
    name: 주요 컴포넌트 상세
    version: 1.0.0
    status: stable
    last_updated: 2026-01-10
    components:
      - src/evalvault/domain/entities/
      - src/evalvault/domain/metrics/
    dependencies: [1, 2, 3]

  - id: 5
    name: 전문가 관점 통합 설계
    version: 1.0.0
    status: stable
    last_updated: 2026-01-10
    components:
      - docs/internal/WHITEPAPER_UPDATE_STRATEGY.md
    dependencies: [1, 2, 3, 4]

changelog:
  - version: 1.0.0
    date: 2026-01-10
    changes:
      - type: added
        description: 초기 버전 출시
      - type: added
        description: 전체 구조 및 계획 문서 작성
      - type: added
        description: 백서 업데이트 전략 수립

references:
  - type: architecture
    title: Hexagonal Architecture
    author: Alistair Cockburn
    url: https://alistair.cockburn.us/hexagonal-architecture/

  - type: architecture
    title: Clean Architecture
    author: Robert C. Martin
    url: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

  - type: architecture
    title: Domain-Driven Design
    author: Eric Evans
    url: https://www.domainlanguage.com/ddd/

keywords:
  - RAG
  - Evaluation
  - Retrieval-Augmented Generation
  - Quality Measurement
  - Observability
  - Hexagonal Architecture
  - Clean Architecture
  - Domain-Driven Design
  - Ragas
  - Phoenix
  - Langfuse

---

> **⚠️ 중요**: 이 백서는 EvalVault 프로젝트의 전체 분석 결과를 바탕으로, 다양한 전문가 관점을 통합하여 작성된 문서입니다. 백서의 최신 버전은 [GitHub Repository](https://github.com/ntts9990/EvalVault)에서 확인할 수 있습니다.

> **📝 편집 가이드**: 백서를 수정할 때는 [백서 업데이트 전략](../internal/WHITEPAPER_UPDATE_STRATEGY.md)을 따라주세요.
