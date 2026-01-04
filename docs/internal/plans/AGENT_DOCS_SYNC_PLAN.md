# 프로젝트 단계/소스 레벨 문서 최신화 에이전트 계획

> **작성일**: 2026-01-04
> **목적**: 프로젝트 목표/추상화 수준 문서와 소스 레벨 문서를 분리 생성하여 최신 상태로 정리
> **산출물**:
> - A 문서: `docs/PROJECT_OVERVIEW.md` (목표/추상화/큰 그림)
> - B 문서: `docs/PROJECT_SOURCE_GUIDE.md` (소스 레벨/구성/확장 지점)
> **SSoT**: `docs/internal/STATUS.md` (내부 상태), `docs/README.md` (Docs Hub 인덱스)

---

## 1) 목표와 범위

- 목적은 **“큰 그림 1개 + 소스 레벨 1개”**로 분리된 종합 문서 2개를 확보하는 것
- 두 문서는 중복을 최소화하되, 서로 링크로 연결
- 문서 근거는 **docs/**와 **중요 소스 코드**로 제한하고, 추측/과장 서술 금지

---

## 2) 에이전트 역할 분담

### Agent A: 프로젝트 목표 & 추상화 레벨

**미션**
- 프로젝트의 “왜/무엇/누구를 위한 것인가”를 상위 레벨로 정리
- 범위, 핵심 기능군, 아키텍처 개요, 운영 방향을 구조화

**필수 입력 (우선순위)**
- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/STATUS.md`
- `docs/USER_GUIDE.md`
- `docs/DEV_GUIDE.md`
- `docs/OBSERVABILITY_PLAYBOOK.md`
- `docs/internal/DEVELOPMENT_GUIDE.md`
- `docs/internal/FEATURE_SPECS.md`
- `docs/internal/ARCHITECTURE_C4.md`
- `docs/internal/STATUS.md`

**산출물 구성 (A 문서)**
1. 프로젝트 미션/문제정의
2. 주요 사용자/사용 시나리오
3. 핵심 기능군/모듈 개요
4. 아키텍처 상위 구조 (Hexagonal 개요, 주요 컴포넌트)
5. 운영/관측/추적 전략
6. 로드맵 및 현재 상태 요약
7. 소스 레벨 문서로의 링크

---

### Agent B: 소스 레벨 (구성/흐름/확장 지점)

**미션**
- 실제 코드 구조와 실행 플로우를 이해하고, 소스 레벨 관점에서 문서화
- 확장/변경 지점, 포트/어댑터 경계, 설정 파일의 역할을 명확히 기술

**필수 입력 (우선순위)**
- `src/evalvault/domain/`
- `src/evalvault/ports/`
- `src/evalvault/adapters/`
- `src/evalvault/config/`
- `config/models.yaml`
- `pyproject.toml`
- `docs/CLI_GUIDE.md`
- `docs/tutorials/`
- `docs/internal/CLASS_CATALOG.md`
- `docs/internal/QUERY_BASED_ANALYSIS_PIPELINE.md`

**산출물 구성 (B 문서)**
1. 레포 구조 요약 (핵심 디렉터리 역할)
2. 도메인/포트/어댑터 구조와 의존 방향
3. 주요 실행 플로우 (CLI, 파이프라인, 평가 루프)
4. 설정/프로파일/환경 변수 (config + `.env` 규칙)
5. 확장 지점 (메트릭 추가, 리트리버 교체, 추적 연동)
6. 테스트 구조 및 주요 픽스처
7. 상위 레벨 문서로의 링크

---

## 3) 공통 조사 규칙

- **근거 우선순위**: 소스 코드 > docs/internal > docs(공개)
- 문서 내 모든 핵심 주장에는 **근거 파일 경로**를 남김
- 불확실한 내용은 “검증 필요” 섹션으로 분리
- 용어는 `docs/README.md` 기준으로 정합성 유지

---

## 4) 검색/확인 체크리스트

- docs 허브 최신화 확인: `docs/README.md`
- 최신 상태 문서 확인: `docs/internal/STATUS.md`
- 주요 진입점:
  - CLI: `src/evalvault/adapters/inbound/cli/`
  - 평가/서비스: `src/evalvault/domain/services/`
  - 포트/계약: `src/evalvault/ports/`
  - 어댑터/연동: `src/evalvault/adapters/outbound/`

---

## 5) 품질 기준

- **정확성**: 코드/문서 간 불일치 발견 시 “검증 필요”에 기록
- **명확성**: 각 섹션은 5~9문장 이내 요약 + 표/리스트 중심
- **구조성**: 상위 → 하위 → 구체 예시 순으로 진행
- **추적성**: 섹션 말미에 근거 경로 2~5개 제공

---

## 6) 통합/검수 단계

1. A/B 문서 초안 작성 후 상호 교차 검토
2. 중복 섹션 제거 및 링크 정합성 보정
3. Docs Hub 인덱스 업데이트 여부 결정 (`docs/README.md`)

---

## 7) 작업 완료 정의 (DoD)

- A/B 문서가 모두 생성되어 `docs/`에 위치
- 각 문서에 “검증 필요” 섹션이 존재 (0개여도 명시)
- 문서 내 주요 주장에 근거 경로가 포함됨
