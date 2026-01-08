Explored
  └ List ls
    Read
INSURANCE_SUMMARY_EVAL_PARALLEL_PLAN.m
         d
    List frontend
    Search rg --files frontend/src -g '*.
           {ts,tsx,css,md,mdx,json}'
    Read
INSURANCE_SUMMARY_EVAL_PARALLEL_PLAN.m
         d
    Search metric|metrics|score|summary|
           faithfulness|entity in frontend
    Read RunDetails.tsx,
EvaluationStudio.tsx,
         api.ts



• Explored
  └ Search fastapi|APIRouter|@app|/runs in
           evalvault
    Search serve-api|api in evalvault
    Read Layout.tsx, Dashboard.tsx,
runs.py,
         adapter.py, EvaluationStudio.tsx,
         RunDetails.tsx, AnalysisLab.tsx,
         AnalysisResultView.tsx,
         CompareRuns.tsx,
CustomerReport.tsx,
         App.tsx, App.css, index.css,
         Settings.tsx, runAnalytics.ts,
         PrioritySummaryPanel.tsx,
         AnalysisNodeOutputs.tsx,
  intuitive with clear warnings and charts.
  I’ll also prepare the document in Korean
  as requested, noting key files and
  endpoints to modify.

• Explored
  └ Search class EvaluationRun|run_mode|

• I'll map out a detailed plan doc covering
  goals, current UI analysis, per-page
  changes, data/API needs, UX and chart
  principles, plus rollout phases—all
  tailored to the user’s Korean-language
  doc request and focused on React, Vite,
  and FastAPI integration.

• Explored
  └ Search Run list|Run in Dashboard.tsx
    Read Dashboard.tsx
    Search startEvaluation in api.ts
    Read api.ts

• I'll create a comprehensive planning
  document outlining how to integrate
  optional summary evaluation into the
  React/Vite/FastAPI web UI. The plan
  covers goals, current UI structure,
  detailed per-screen integration points
  with file paths, API data needs, UX
  principles focusing on cognitive load and
  error prevention, and a staged rollout
  approach, all emphasizing maintaining
  existing layouts and language consistency
  while clearly indicating where new
  components and toggles should live. This
  document matches the user’s request to
  deliver a well-structured, Korean-
  oriented plan referencing relevant files
  and features like summary metrics
  toggles, warnings, and dashboard badges.

  Preparing final plan with next-step
  suggestions

  I'll finalize the planning document with
  structured sections and concise bullet
  points in Korean, exactly as requested,
  and add a clear numeric list of natural
  next steps at the end to guide
  prioritization, API definition, and
  initial implementation phases. This will
  give the user an easy-to-follow roadmap
  for advancing the summary evaluation UI
  integration.

─ Worked for 5m 57s ───────────────────────

• 목표/전제

  - docs/internal/plans/
    INSURANCE_SUMMARY_EVAL_PARALLEL_PLAN.md
    기준으로 요약 평가는 기본 off, 명시 선
    택 시만 실행
  - 핵심 지표는 summary_score,
    summary_faithfulness,
    entity_preservation 3종으로 사용자 노출
    안전성에 집중
  - LLM은 기존 선택 모델 사용, 번역 없이 혼
    용 언어 평가, 결과에 언어 혼용 비율 노
    출
  - UI는 “요약 안전성” 빠른 판단 + 필요한
    경우만 상세 드릴다운
  - 기존 레이아웃/스타일 유지, 차트 중심,
    오류 예방 메시지 강화

  현행 UI 구조 파악

  - frontend/src/pages/EvaluationStudio.tsx
    에서 메트릭 칩 선택 후 frontend/src/
    services/api.ts의 startEvaluation으로
    실행
  - frontend/src/pages/RunDetails.tsx는 메
    트릭 평균 바차트와 케이스 상세 카드 제
    공, 경고 기준/요약 전용 섹션 없음
  - frontend/src/pages/Dashboard.tsx와
    frontend/src/pages/CustomerReport.tsx는
    avg_metric_scores 기반 트렌드 차트, 메
    트릭 그룹링 미지원
  - frontend/src/pages/CompareRuns.tsx는
    metrics_evaluated로 델타 계산, 요약 메
    트릭 구분 없음
  - frontend/src/components/
    PrioritySummaryPanel.tsx와 frontend/
    src/components/AnalysisNodeOutputs.tsx
    는 메트릭 액션/요약 표기 가능하나 요약
    메트릭 매핑 없음
  - src/evalvault/adapters/inbound/api/
    routers/runs.py와 src/evalvault/
    adapters/inbound/api/adapter.py는 옵션/
    요약 제공, run_mode·언어 혼용 메타가 UI
    로 전달되지 않음

  화면별 반영 상세

  - Evaluation Studio: 요약 평가 토글/프리
    셋 추가, ON 시 3지표 자동 선택 + 임계값
    안내 + “혼용 언어/LLM Judge/옵션 평가”
    설명 배너
  - Run Details: 상단 “Summary Safety” 카드
    (3지표 점수/임계값/경고 플래그), 케이스
    상세에서 요약 메트릭 reason 강조
  - Dashboard: 런 카드에 요약 평가 배지, 요
    약 메트릭 평균 미니칩, 트렌드 영역에
    “요약 지표” 탭 분리
  - Compare Runs: 요약 메트릭 델타 전용 섹
    션, 임계값 기준으로 개선/악화 강조 배지
  - Customer Report: 요약 평가 요약 블록을
    별도 배치, 기본은 간략 보기(접힘) + 보
    고용 요약 설명 제공
  - Analysis Lab/Result: 요약 메트릭 액션
    문구 추가, summary 출력/메타(언어 혼용)
    노출 강화

  API/데이터 요구사항

  - src/evalvault/adapters/inbound/api/
    adapter.py의 AVAILABLE_METRICS에 3개 요
    약 메트릭 추가
  - StartEvaluationRequest에 run_mode 또는
    summary_enabled 추가 후 트래커 메타에
    기록
  - RunSummaryResponse에 run_mode/요약 평가
    여부를 노출해 UI에서 구분 가능하게 처리
  - 언어 혼용 비율(language_mix)을 런 메타
    에 저장하고 응답에 포함
  - 요약 메트릭 기본 임계값을 응답에 포함하
    거나 별도 옵션 엔드포인트로 제공

  UX/차트/오류 방지 원칙

  - 기본 off + 프리셋 원클릭으로 인지부하
    최소화, 수동 선택은 고급 영역으로 이동
  - 3지표는 단일 카드에 묶고 색상으로 “안
    전/주의/위험”만 강조
  - 트렌드/델타는 요약 탭으로 분리해 RAG 지
    표와 혼동 방지
  - 데이터 미존재는 “미평가”로 표기하고 원
    인/대응 안내를 함께 표시
  - 혼용 언어는 경고 배지 + 툴팁으로 처리,
    본문 텍스트는 최소화

  단계적 적용

  - MVP: 메트릭 옵션 노출 + Evaluation

  다음 단계 제안

  1. 위 기획에 대해 화면별 우선순위 확정
  2. run_mode/language_mix 등 API 스키마 확
     정
  중이야. B 작업까지 끝나면 C와 D가 동시에
  병렬 작업할 거야.
  이걸 감안해서 작업 진행 계획을 만들어줘.
  이것도 문서화해줘.


• I’m outlining a Korean document detailing
  screen priorities, a proposed API schema
  aligned with the existing style, and a
  phased plan marking agent statuses. I
  want to keep changes backward-compatible
  by extending current endpoints or adding
  new ones to avoid breaking the UI. I’m
  thinking of proposing optional fields,
  new query params, or separate endpoints
  for richer metric details. For toggling
  summary evaluation on the UI, I’m
  considering adding a run_mode or
  proposal aligns well.

• Explored
  └ Search run_mode in evalvault
    Read adapter.py

• I'm organizing a detailed document that
  confirms screen priorities, proposes API
  schema changes consistent with the
  project's philosophy, and outlines a
  phased and parallel task timeline
  considering completed and ongoing work.
  This will include clear sections with
  numbered priorities, API endpoint and
  metadata recommendations, and a stepwise
  work schedule avoiding nested bullets for
  clarity.

  Organizing prioritized UI, API schema,
  and phased plan

  I’m preparing a structured document that
  finalizes screen priorities (P0–P3),
  proposes detailed API schema enhancements
  with examples following the project’s
  design philosophy, and lays out a clear
  phased work plan reflecting current Agent
  progress with parallel tasks post-B
  phase. This includes references to
  relevant files and avoids nested bullets
  to keep clarity.

─ Worked for 2m 47s ───────────────────────

• 요청하신 대로 화면별 우선순위 확정 + API
  스키마 제안 + B 완료 후 병렬 진행 계획을
  문서 형태로 정리했습니다.

  화면별 우선순위(확정)

  - P0: 실행 경로 핵심인 frontend/src/
    pages/EvaluationStudio.tsx에 요약 평가
    토글/프리셋과 경고 기준 안내를 먼저 배
    치, 사용자가 “요약 평가 옵션”을 명확히
    인지하고 실수 없이 선택하도록 설계
  - P0: 결과 판단 중심인 frontend/src/
    pages/RunDetails.tsx에 Summary Safety
    카드(3지표/경고/혼용 언어) 추가, 케이스
    상세는 기존 구조 유지하며 요약 메트릭만
    강조
  - P1: 운영 모니터링용 frontend/src/pages/
    Dashboard.tsx에 요약 평가 배지 + 요약
    메트릭 트렌드 탭 추가, 카드 레벨 요약
    정보는 최소 노출
  - P1: 비교 판단용 frontend/src/pages/
    CompareRuns.tsx에 요약 메트릭 델타 섹션
    추가, 경고 기준을 색상으로만 표시
  - P2: 공유/보고용 frontend/src/pages/
    CustomerReport.tsx에 요약 평가 요약 블
    록 추가(기본 접힘)
  - P2: 분석 심화용 frontend/src/pages/
    AnalysisLab.tsx, frontend/src/pages/
    AnalysisResultView.tsx, frontend/src/
    components/PrioritySummaryPanel.tsx에
    요약 메트릭 액션/라벨 보강

  API 스키마 제안(문서 기반, 기존 철학 준
  수)

  - 호환성 유지: 기존 GET /api/v1/runs/
    options/metrics는 list[str]로 유지하고,
    메트릭 메타는 신규 엔드포인트로 추가
  - 신규 메트릭 카탈로그: GET /api/v1/runs/
    options/metrics/catalog 추가, Pydantic
    모델로 명확한 스키마 제공; UI는 카테고
    리/경고 기준을 여기서 소비
  - 실행 요청 확장: POST /api/v1/runs/start
    에 evaluation_task 필드 추가(기본 "qa",
    요약 평가는 "summarization"),
    StartEvaluationRequest에 Optional로 정
    의
  - 런 요약 확장: RunSummaryResponse/
    RunSummary에 evaluation_task와
    language_mix 추가, 리스트와 상세 모두에
    서 사용 가능; 내부 저장은
    tracker_metadata에 기록
  - 경고 기준 분리: 평가 threshold(기본
    0.7)는 그대로 두고, UI 경고용
    alert_threshold를 카탈로그에 둬서 “평가
    통과/사용자 경고” 분리

  {
    "name": "summary_faithfulness",
    "label": "요약 충실도",
    "category": "summary",
    "description": "요약 내 주장 vs 원문 근
  거 일치",
    "threshold_default": 0.7,
    "alert_threshold": 0.9
  }

  {
    "evaluation_task": "summarization",
    "language_mix": { "ko": 0.925, "en":
  0.075, "other": 0.0 }
  }

  작업 진행 계획(Agent 상태 반영)

  1. B 완료: entity_preservation 구현 확정
     + summary_faithfulness 정책/프롬프트
     가이드 확정 + language_mix 메타 산출
     위치 고정
  2. C(백엔드/API): src/evalvault/adapters/
     inbound/api/routers/runs.py에 카탈로그
     엔드포인트 추가,
     StartEvaluationRequest/
     RunSummaryResponse 스키마 확장, src/
     evalvault/adapters/inbound/api/
     adapter.py에서
     evaluation_task·language_mix 저장
  3. D(테스트/문서, B 완료 직후 병렬):
     tests/fixtures/e2e/
     summary_eval_minimal.json 생성, 관련
     EvaluationStudio.tsx 토글/프리셋 +
     frontend/src/pages/RunDetails.tsx
     Summary Safety 카드 반영
  5. C(프론트 P1/P2): Dashboard/Compare/
     CustomerReport/AnalysisLab의 요약 메트
     릭 표기 통합
  6. 통합 검증: 요약 경고 기준 재조정, 회귀
     테스트, 문서 동기화

  다음 단계 제안

  1. 위 우선순위와 API 스키마에 대한 승인/
     수정 포인트 확인
  2. 승인되면 C/D 작업 범위를 구체화해서 구
     현 착수

  추가 내용 반영(요약 메트릭 기본 임계값)

  - 요약 메트릭 기본 임계값은 코드에 하드코딩됨:
    summary_faithfulness 0.9, summary_score 0.85,
    entity_preservation 0.9.
  - dataset.thresholds가 비어 있어도 위 기본값으로
    요약 메트릭이 보수 기준 평가됨.
  - Domain Memory 경로(MemoryAwareEvaluator)도
    default_threshold_for를 사용하므로 동일 기준을
    적용함.

  다음 작업 준비(추가 내용 포함)

  1. MemoryAwareEvaluator 기본 임계값 적용을
     검증하는 단위 테스트 추가 검토
     (tests/unit/test_memory_services.py).
  2. 요약 평가 문서/노출 포인트에 기본 임계값
     안내 문구 추가 위치 확정.
  3. 프론트/응답 스키마에서 임계값 미제공 시
     기본값 표시 방식(카탈로그 vs 상수) 확정.
