# 웹 UI 정보 구조(IA) 정의서

> 작성일: 2026-01-09
> 상태: v0.1 (초안)
> 목적: EvalVault Web UI의 정보 구조와 화면 책임 범위를 고정한다.

## 1) 목적과 범위

- CLI 중심 흐름을 Web UI 단계형 경험으로 재정렬한다.
- 많은 옵션/파라미터를 **Quick → Guided → Expert** 계층으로 구분한다.
- Run 결과를 “이해 → 비교 → 개선”으로 이어지는 체계를 만든다.

## 2) 핵심 제약/브랜드 톤

- 기본 톤: **흰색 배경 + 검은 텍스트**.
- 강조색: **#4E81EE** 기반(흰색 텍스트 조합).
- 제약은 참고 수준이며, 디자인 토큰에서 정리한다.

## 3) 핵심 객체 모델

| 객체 | 설명 | 주요 연결 |
| --- | --- | --- |
| Dataset | 평가 입력 데이터 | Evaluation Studio, Knowledge Base |
| Run | 평가 실행 단위 | Dashboard, Run Details, Compare |
| Analysis | 분석 결과 | Analysis Lab, Run Details |
| Stage Event | 단계별 추적 | Run Details > Performance |
| Knowledge Graph | KG/GraphRAG 입력 | Knowledge Base, Evaluation Studio |
| Domain Memory | 도메인 사실 저장 | Domain Memory, Run Details |
| Prompt Set | 프롬프트 스냅샷 | Run Details, Compare |
| Tracker | Phoenix/Langfuse/MLflow | Run Details, Settings |
| Profile | 모델/환경 설정 | 상단 컨텍스트 바 |

## 4) 앱 전역 구조

### 4.1 앱 셸

- 좌측 내비게이션 + 상단 컨텍스트 바 + 콘텐츠 영역.
- 상단 컨텍스트 바에 **Profile, Project, Dataset, Active Run** 노출.
- 전역 커맨드 팔레트: 새 실행, 비교, 분석, 최근 런 열기.

### 4.2 전역 상태

- **Context**: Profile, Project, Dataset, Run 선택 상태 유지.
- **고정 액션**: “새 Run”, “Compare”, “Export”.

## 5) 내비게이션/라우팅 맵

| 구역 | 라우트(권장) | 화면 | 역할 |
| --- | --- | --- | --- |
| Dashboard | `/` | Dashboard | 실행 요약·추세·알림 |
| Studio | `/studio` | EvaluationStudio | 실행 워크플로 |
| Run Details | `/runs/:id` | RunDetails | 결과/성능/추적 |
| Compare | `/compare` | CompareRuns | 런 비교 |
| Analysis | `/analysis` | AnalysisLab | 파이프라인 분석 |
| Analysis Result | `/analysis/:id` | AnalysisResultView | 분석 결과 |
| Analysis Compare | `/analysis/compare` | AnalysisCompareView | 비교 분석 |
| Knowledge | `/knowledge` | KnowledgeBase | KG/데이터 관리 |
| Memory | `/memory` | DomainMemory | 도메인 메모리 |
| Customer Report | `/report/:id` | CustomerReport | 대외 리포트 |
| Settings | `/settings` | Settings | 프로필/연동 |
| (확장) | `/experiments`, `/benchmarks` | 신규 | 실험/벤치마크 |

## 6) 화면별 IA 상세

### 6.1 Dashboard

- **요약 카드**: pass rate, 평균 메트릭, 최근 회귀, 경고 배지.
- **런 리스트**: 필터(모드/메트릭/임계값/도메인/프로필), 비교 체크박스.
- **빠른 액션**: Compare, Export, Analyze.

### 6.2 Evaluation Studio

#### 단계형 플로우
1. **Dataset**: 업로드/경로 + 스키마 검사 + 타입 자동 감지.
2. **Metrics/Presets**: Quick/Production/Summary/Comprehensive 선택.
3. **Retriever/Memory/Tracker**: 고급 옵션 패널 분리.
4. **Review & Run**: 설정 스냅샷 + CLI 명령 생성.

#### 계층 구조
- **Quick**: 최소 옵션(데이터, 프리셋, 실행).
- **Guided**: 검증/추천/툴팁 포함.
- **Expert**: 모든 CLI 옵션 노출(접힘/검색 가능).

### 6.3 Run Details

- **Summary 탭**: scorecard, 임계값 비교, 경고 요약.
- **Cases 탭**: 테스트 케이스 리스트 + 메트릭 상세.
- **Performance 탭**: stage 이벤트 워터폴/병목 분석.
- **Observability 탭**: Phoenix/Langfuse 링크 및 메타.

### 6.4 Analysis Lab

- **쿼리 입력**: 자연어 분석 쿼리 + intent 프리뷰.
- **선택 컨텍스트**: 런/데이터셋 선택.
- **결과 패널**: 요약 → 상세 → 리포트 다운로드.

### 6.5 Compare

- **Base/Target 선택** + 회귀 케이스 필터.
- **델타 요약**: 메트릭 변화 + 유의성.
- **답변 diff 뷰**: 추가/삭제 강조.

### 6.6 Knowledge Base / Domain Memory

- KG 업로드/검증/정규화 + “Run에 사용” 버튼.
- Domain Memory: 사실 목록 + 추세 + Run 연결.

### 6.7 Customer Report

- 요약 중심, 비기술 사용자에게 공유 가능한 구성.
- 주요 지표, 개선안, 비교 결과를 한 화면에 요약.

### 6.8 Settings

- Profile/Model/Keys/Tracker/Storage 설정 통합.
- 필수 설정 누락 시 경고 및 바로가기 제공.

## 7) 옵션 계층 구조 (UI 단순화 기준)

| 계층 | 노출 기준 | 주요 항목 |
| --- | --- | --- |
| Quick | 기본 실행 | dataset, preset, run |
| Guided | 안전한 확장 | metrics, threshold, retriever, tracker |
| Expert | 전체 옵션 | memory, prompt, streaming, batch, stage |

> 상세 매핑은 `docs/internal/reference/CLI_UI_OPTION_MAPPING.md` 참고.

## 8) 주요 플로우 요약

- **평가 실행**: Studio → RunDetails → 자동 분석/리포트.
- **비교 분석**: Dashboard 선택 → Compare → 회귀 케이스 리뷰.
- **인사이트 도출**: RunDetails → Analysis Lab → 개선안 저장.

## 9) 오류 방지/검증 규칙

- `summary`와 `preset` 동시 사용 방지(UI에서 즉시 경고).
- `system_prompt` vs `system_prompt_file` 배타 선택.
- `stage_store`는 DB 설정이 선행되어야 활성화.
- Retriever/KG 미설정 시 그래프 관련 옵션 비활성.

## 10) 추천/예측 액션 설계

- 임계값 미달 → 분석 파이프라인 추천 버튼.
- KG 불일치 → “검증 실행” 퀵 액션.
- 반복 설정 감지 → 프리셋 저장 제안.

## 11) 접근성/모바일

- 최소 대비 4.5:1.
- 모바일은 **요약 카드 → 상세 접힘** 구조 유지.
- 표/리스트는 가상화 + 축약 모드 제공.

## 12) 다음 산출물

- 디자인 토큰 정리: `docs/internal/reference/DESIGN_TOKENS.md`
- E2E 시나리오 고정: Playwright 시나리오 문서
