# CLI 개발 따라잡기와 웹 UI 전문화 계획

> 작성일: 2026-01-09
> 목적: CLI 진행 상황을 재동기화하고, 다중 전문가 관점을 반영한 웹 UI 재설계/검증 로드맵을 고정한다.
> 범위: CLI 스냅샷/옵션 매핑, IA·디자인 토큰 정의, E2E 시나리오 고정.

## 1) 배경과 목표

- CLI 중심으로 진행된 개발·테스트 흐름을 Web UI 기준으로 재정렬한다.
- 많은 CLI 옵션/파라미터를 **계층화·프리셋화**하여 직관적 선택 흐름을 만든다.
- 결과 이해를 강화하고, 사용자의 다음 행동을 예측해 인터랙티브하게 안내한다.

## 2) 참조 문서

- `docs/internal/plans/CLI_DEVELOPMENT_PLAN.md`
- `docs/internal/plans/WEB_UI_FOLLOWUP_PLAN.md`
- `docs/internal/FRONTEND_GAP_ANALYSIS_AND_PLAN.md`
- `docs/internal/reference/FEATURE_SPECS.md`
- `docs/internal/reference/USER_SCENARIO_REQUIREMENTS.md`
- `docs/internal/reference/CLI_UI_OPTION_MAPPING.md`
- `docs/internal/reference/CLI_OUTPUT_SCHEMA_SNAPSHOT.md`
- `docs/internal/reference/IA_STRUCTURE.md`
- `docs/internal/reference/DESIGN_TOKENS.md`
- `docs/internal/reference/WEB_UI_E2E_SCENARIOS.md`
- `docs/internal/plans/REACT_DEV.md`

## 3) 진행 순서 (요청 확정 순서)

- 1단계: CLI 스냅샷·옵션 매핑 재정리
- 2단계: 정보 구조(IA) + 디자인 토큰(시각·인터랙션) 확정
- 3단계: Playwright 기반 UI E2E 시나리오 고정

## 4) 전문가 관점 정의와 적용 기준

| 전문가 관점 | 핵심 관점 | UI 적용 기준 | 검증 지표 |
| --- | --- | --- | --- |
| 인지심리학 | 인지 부하 최소화, 작업기억 관리 | 프리셋 중심 단계형 입력, 용어 일관화, 요약+툴팁 | TTFV, 중단율 |
| 뇌과학 | 주의 자원·보상 지연 최소화 | 즉시 피드백, ETA/진행률, 리듬감 있는 시각 구조 | 이탈률, 작업 완료율 |
| 사회심리학 | 신뢰·사회적 증거 | 비교/벤치마크, 공유 리포트, 팀·도메인 배지 | 공유율, 합의 시간 |
| UI/UX | 오류 방지·접근성·일관성 | 실시간 유효성 검사, 되돌리기, 키보드 내비, 반응형 | 에러율, 접근성 점수 |
| 색채심리 | 의미 기반 색채·가독성 | 역할 색상 체계, 대비 기준, 색맹 안전 | 경고 인지 시간 |
| 컴퓨터공학 | 신뢰성·성능·확장성 | 타입 안전, 비동기 상태관리, 오류 경로 표준화 | 응답시간, 실패율 |
| 데이터분석 | 분포·변동·재현성 | 분포/추세 시각화, 기준선·신뢰구간 | 분석 소요시간 |
| 교육공학 | 스캐폴딩·학습 전이 | 가이드 모드, 단계별 힌트, 근거 설명 | 학습 완료율 |
| 마케팅 | 가치 전달·활성화 | 온보딩 스토리, 템플릿, ROI 메시지 | 활성화율 |
| 2025 React UI/UX | 현대적 패턴·성능 | 디자인 토큰, 라우트 분할, 가상화, 스켈레톤 | LCP/INP |

## 5) 통합 설계 원칙

- 프리셋 우선 + 점진 공개(Quick → Guided → Expert)
- 문제 해결 플로우 중심(Setup → Run → Analyze → Improve → Share)
- 재현성 기본값(설정 스냅샷과 CLI 명령 자동 생성)
- 인지 부하 최소화(요약 카드 + 드릴다운)
- 신뢰 강화(임계값·근거·데이터 출처 명시)
- 학습/온보딩 통합(가이드 모드, 예시 데이터)

## 6) 2025 모던 웹 UI 가이드 (React 기준)

- 타이포그래피: 본문 `IBM Plex Sans KR`, 헤더 `Space Grotesk` 기반의 명확한 대비
- 배경/분위기: 단색 배경 금지, 미세 그라디언트와 형태 패턴 사용
- 모션: 페이지 로드/스텝 전환/결과 요약에 의미 있는 애니메이션만 사용
- 색상 체계: 의미 기반 팔레트(안정·경고·개선·위험), 데이터 시각화 색상 분리
- 정보 밀도: 핵심 요약→세부로 내려가는 계층 구조, 기본은 간결

## 7) 정보 구조(IA) 및 기능 선택 흐름

| 영역 | 목적 | 주요 입력 | 주요 출력 |
| --- | --- | --- | --- |
| Dashboard | 전체 현황/추세 | 기간, 프로필, 필터 | 요약 카드, 경고 배지 |
| Evaluation Studio | 평가 실행 | 데이터셋, 메트릭, 리트리버, 트래커 | 실행 결과/스냅샷 |
| Analysis Lab | 분석 파이프라인 | 분석 의도, 대상 런 | 분석 리포트 |
| Compare | 결과 비교 | Base/Target 런 | 델타/회귀 케이스 |
| Knowledge/Memory | 지식/메모리 관리 | KG, 메모리 DB | 정합성·활용 |
| Settings | 프로필/연동 | 모델/키/트래커 | 설정 상태 |

| 단계 | Evaluation Studio 흐름 | 핵심 목표 |
| --- | --- | --- |
| 1 | 데이터 선택/검증 | 스키마/타입 확인 |
| 2 | 메트릭/프리셋 | 최소 인지부하 |
| 3 | 리트리버/메모리/트래커 | 고급 옵션 분리 |
| 4 | 실행/분석 | 결과 이해와 다음 행동 |

## 8) CLI 옵션·파라미터 매핑(핵심)

| UI 구역 | CLI 대응 옵션 | 적용 메모 |
| --- | --- | --- |
| 데이터셋 | `evalvault run <dataset>` | 업로드·경로 선택, 스키마 검증 |
| 프리셋 | `--preset`, `--summary` | Quick/Production 등 프리셋 버튼 |
| 메트릭 | `--metrics` | 커스텀/기본 구분 표시 |
| 임계값 | `--threshold-profile` | 프로필 비교 패널 |
| 리트리버 | `--retriever`, `--retriever-docs` | GraphRAG 포함, 컨텍스트 채움 조건 안내 |
| 지식그래프 | `--kg` | 업로드·검증·정규화 |
| 모델/프로필 | `--profile`, `--model` | 유효성 체크, 프로필 스냅샷 |
| 분석 자동화 | `--auto-analyze` | 결과 탭에서 분석 바로가기 |
| 출력/리포트 | `--output`, `--analysis-json`, `--analysis-report` | 저장 위치 안내 |

## 9) 결과 이해 설계

| 목표 | 시각화/정보 | 데이터 소스 |
| --- | --- | --- |
| 요약 이해 | 스코어카드, 임계값 비교 | Run summary |
| 분포/변동 | 히스토그램, 추세선 | Metrics + History |
| 비교/회귀 | 델타 차트, 회귀 필터 | Compare API |
| 성능/병목 | Stage 워터폴 | Stage events |
| 근거/맥락 | Context vs Memory 분리 | Run details |

## 10) 예측 니즈와 인터랙션

| 상황 | 자동 제안 | 후속 액션 |
| --- | --- | --- |
| 스키마 불일치 | 템플릿 다운로드 | 재업로드 |
| 임계값 미달 | 분석 파이프라인 추천 | 자동 분석 실행 |
| KG 불일치 | KG 검증 안내 | 수정 가이드 |
| 키/연동 누락 | 필요한 ENV 표시 | 설정 페이지 이동 |
| 반복 설정 | 프리셋 저장 제안 | 템플릿 생성 |

## 11) 실행 로드맵 (1 → 2 → 3)

| 단계 | 범위 | 산출물 |
| --- | --- | --- |
| 1단계 | CLI 스냅샷/옵션 매핑 | 옵션 매핑표, 결과 스키마 샘플 |
| 2단계 | IA + 디자인 토큰 | 내비 구조, 컴포넌트 토큰 |
| 3단계 | UI E2E 시나리오 | Playwright 시나리오 정의 |

## 12) 산출물 정의

- CLI 옵션 매핑표 (UI 요소 ↔ CLI 옵션) → `docs/internal/reference/CLI_UI_OPTION_MAPPING.md`
- 결과 스키마 스냅샷 (run 결과/분석 리포트/스테이지 이벤트) → `docs/internal/reference/CLI_OUTPUT_SCHEMA_SNAPSHOT.md`
- IA 문서 (라우팅·화면 역할·정보 계층) → `docs/internal/reference/IA_STRUCTURE.md`
- 디자인 토큰 문서 (색/타이포/모션/간격) → `docs/internal/reference/DESIGN_TOKENS.md`
- E2E 시나리오 문서 (플로우 + 기대 결과) → `docs/internal/reference/WEB_UI_E2E_SCENARIOS.md`

## 13) 테스트/검증 기준

- CLI 스모크: `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`
- 분석 파이프라인: `uv run evalvault pipeline analyze "요약해줘" --profile dev`
- UI E2E: Evaluation → RunDetails → Compare → Analysis 흐름
- 접근성/성능: Lighthouse 기준선 확보

## 14) 체크리스트

- [x] CLI 옵션·파라미터 매핑표 초안 작성
- [x] 주요 출력 스키마 샘플 확보
- [x] IA 내비 구조 초안 작성
- [x] 디자인 토큰(색/타이포/모션) 초안 작성
- [x] 핵심 사용자 시나리오 기반 E2E 시나리오 고정

## 15) 확인 필요사항

- 최우선 사용자 역할(엔지니어/분석가/PM) 우선순위
- 유지해야 할 브랜드 톤/색상 제약
- 필수 연동 대상(Phoenix/Langfuse/MLflow) 우선순위
- 대표 데이터 규모(평균 케이스 수/파일 크기)
