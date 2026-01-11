# EvalVault 백서 작성 준비 가이드

> **작성일**: 2026-01-11
> **목적**: 실제 소스 코드를 근거로 백서 작성 준비를 체계화한다.
> **상태**: 🟡 준비 진행 중 (코드 근거 정리 완료)

---

## 1. 코드 근거 기반 섹션 매핑

| 섹션 | 근거 소스 | 핵심 서술 포인트 |
|---|---|---|
| 1부 개요 | `README.md` | 문제 정의, 가치 제안, 사용자 시나리오 |
| 2부 아키텍처 | `docs/architecture/ARCHITECTURE.md` | Hexagonal 설계 원칙, 계층 구분 |
| 3부 데이터 흐름 | `src/evalvault/domain/services/analysis_service.py` | 분석 파이프라인 흐름 |
| 3부 시각화 | `src/evalvault/domain/services/visual_space_service.py` | 좌표 계산 로직과 지표 정의 |
| 4부 CLI | `src/evalvault/adapters/inbound/cli/app.py` | CLI 구조, 메트릭 목록 |
| 4부 API | `src/evalvault/adapters/inbound/api/main.py` | API 진입점, 라우터 등록 |
| 4부 Runs API | `src/evalvault/adapters/inbound/api/routers/runs.py` | 평가 실행/시각화 요청 모델 |
| 4부 평가 엔진 | `src/evalvault/domain/services/evaluator.py` | Ragas + 커스텀 메트릭 |
| 4부 벤치마크 | `src/evalvault/adapters/inbound/cli/commands/benchmark.py` | 벤치마크 실행/리트리벌 비교 |
| 4부 리포트 | `src/evalvault/domain/services/benchmark_report_service.py` | 벤치마크 분석 리포트 |
| 4부 통합 리포트 | `src/evalvault/domain/services/unified_report_service.py` | 평가+벤치마크 통합 분석 |

---

## 2. 전문가 관점 반영 체크리스트

### 2.1 인지심리학자
- [ ] 섹션별 정보량이 과도하지 않은가
- [ ] 개념이 단계적으로 노출되는가

### 2.2 교육학자
- [ ] 초급/중급/고급 구분이 명확한가
- [ ] 학습 경로가 예제 중심으로 구성되는가

### 2.3 컴퓨터공학자
- [ ] 아키텍처 설명이 구현 근거와 일치하는가
- [ ] 메트릭/알고리즘 설명이 소스와 동기화되는가

### 2.4 편집자
- [ ] 용어 표기가 일관적인가
- [ ] 문장 구조가 간결한가

### 2.5 UI/UX 전문가
- [ ] CLI 흐름과 Web UI 흐름이 동일한 용어로 연결되는가
- [ ] 사용자 시나리오가 단계적으로 설명되는가

### 2.6 MD 문서 전문 디자이너
- [ ] 헤딩 계층이 H1/H2/H3로 일관되는가
- [ ] 표/코드 블록이 과밀하지 않은가

---

## 3. 작성 규칙 (내부 기준)

- **근거 명시**: 모든 기술 설명은 소스 파일 경로를 근거로 작성
- **서술 방식**: 기능 설명 → 내부 동작 → 사용자 흐름 순서
- **표준 표현**: 메트릭/엔티티/서비스 명은 코드와 동일하게 표기
- **다이어그램**: Mermaid 사용, 흐름은 좌→우 또는 상→하로 통일

---

## 4. 준비 작업 체크리스트

- [ ] 소스 근거 매핑 표 최신화
- [ ] CLI/REST API 요청·응답 모델 정리
- [ ] 메트릭 목록 및 요구 데이터(ground_truth 등) 정리
- [ ] Visual Space 좌표 계산 논리 요약
- [ ] 벤치마크 실행/리포트 흐름 요약

---

## 5. 아카이브 정책

- 과거 초안 또는 중복되는 백서 파일은 `docs/internal/archive/whitepaper-YYYYMMDD/`로 이동
- 현재 기준 아카이브 위치: `docs/internal/archive/whitepaper-20260111/`

---

## 6. 미작성 섹션 처리 (To be written)

- 7~14부는 **로드맵 수준**으로만 기입하고, 구현 근거가 확보되면 본문으로 승격
- 신규 구현 시 섹션별 매핑 테이블 갱신 후 작성 시작
