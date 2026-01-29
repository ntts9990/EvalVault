# RAG 평가 노이즈 저감 정리서

## 목적
RAG 평가에서 발생하는 **데이터 노이즈**와 **모델 노이즈**를 줄이기 위해, 이미 적용된 방법과 앞으로 적용할 계획을 한 문서에 정리한다.

---

## 1) 노이즈 정의
- 데이터 노이즈: 입력 품질 편차(빈 필드, 컨텍스트 중복/과다, 레퍼런스 부족)로 인해 점수가 흔들리거나 평가가 실패하는 문제
- 모델 노이즈: LLM-as-judge의 출력 변동, 언어 불일치, NaN/비정상 결과로 점수 신뢰도가 낮아지는 문제

---

## 2) 현재 적용된 노이즈 저감 방법 (Implemented)

### 2.1 데이터 전처리 가드레일
- 근거: `src/evalvault/domain/services/dataset_preprocessor.py`
- 적용 내용
  - 빈 질문/답변/컨텍스트 처리
  - 컨텍스트 정규화(공백/중복 제거, 길이/개수 제한)
  - 레퍼런스 보완(필요 메트릭에서 답변/컨텍스트 기반 보완)
- 효과
  - 입력 편차를 줄여 RAGAS 점수 분산과 실패율을 낮춤

### 2.2 한국어 프롬프트 정렬
- 근거: `src/evalvault/domain/services/evaluator.py`, `README.md`
- 적용 내용
  - 데이터셋 언어 감지 후 한국어 프롬프트 기본 적용
  - AnswerRelevancy, FactualCorrectness 등에 한국어 템플릿 사용
- 효과
  - 언어 불일치로 인한 judge 변동/오판을 완화

### 2.3 NaN/비정상 점수 방어 및 Faithfulness 폴백
- 근거: `src/evalvault/domain/services/evaluator.py`, `README.md`
- 적용 내용
  - 비숫자/NaN 점수는 0.0 처리
  - Faithfulness 실패 시 LLM 폴백 재시도
  - 한국어 claim-level faithfulness 폴백 경로 제공
- 효과
  - 평가 파이프라인 중단을 방지하고 점수 안정성 확보

### 2.4 Stage 메트릭 기반 원인 분리
- 근거: `src/evalvault/domain/services/stage_metric_service.py`
- 적용 내용
  - retrieval/rerank/output 단계별 메트릭 분리
  - 점수 하락의 원인을 단계별로 분석 가능
- 효과
  - 점수 변동의 원인을 분해해 “해석 노이즈”를 줄임

### 2.5 휴먼 피드백 기반 캘리브레이션 가이드
- 근거: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- 적용 내용
  - 대표 샘플링 → 인간 평가 → 보정 모델 적용 절차 문서화
- 효과
  - LLM-as-judge 점수의 신뢰도 보정 및 운영 기준 강화

---

## 3) 병렬 개발 작업 계획 (에이전트 충돌 방지)

아래 계획은 평가 실행의 병렬화가 아니라, **노이즈 저감 기능을 개발할 때 병렬 작업이 충돌하지 않도록** 작업 범위를 분리하고 의존성을 명확히 하기 위한 것이다.

### 3.1 병렬 작업 스트림(충돌 최소화)
- Stream A: 데이터 전처리/가드레일 개선
  - 대상: `src/evalvault/domain/services/dataset_preprocessor.py`
- Stream B: 평가 로직 안정화(언어 정렬/폴백)
  - 대상: `src/evalvault/domain/services/evaluator.py`
- Stream C: Stage 메트릭/관측 지표
  - 대상: `src/evalvault/domain/services/stage_metric_service.py`
- Stream D: 캘리브레이션/운영 가이드
  - 대상: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- Stream E: 정책/로드맵 정합성 문서
- 대상: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/handbook/CHAPTERS/00_overview.md`

### 3.2 병렬 작업 규칙(합의 사항)
- 서로 다른 파일에서 작업
- 공유 스키마/출력 포맷 변경은 사전 합의
- 문서 오너 지정(각 문서 1명)
- 겹치는 내용은 한쪽 문서에서만 관리
- 아티팩트 경로/JSON 스키마 변경은 반드시 문서 업데이트 동반

### 3.3 CLI 병렬 기능 스펙과의 비겹침 확인
- 문서 경로 분리
  - 노이즈 저감: `docs/guides/RAG_NOISE_REDUCTION_GUIDE.md`
  - CLI 병렬 스펙: `docs/guides/CLI_PARALLEL_FEATURES_SPEC.md`
- 코드 변경 범위 분리
  - 노이즈 저감: `src/evalvault/domain/services/dataset_preprocessor.py`, `src/evalvault/domain/services/evaluator.py`, `src/evalvault/domain/services/stage_metric_service.py`
  - CLI 스펙(추후 구현): `src/evalvault/adapters/inbound/cli/commands/*`, `src/evalvault/domain/services/async_batch_executor.py`
- 역할 분리 원칙
  - 노이즈 저감 문서는 정책/로직 개선 중심
  - CLI 스펙 문서는 실행 인터페이스/출력 규격 중심
  - 공통 스키마 변경은 별도 합의 후 반영
- 연계 정보는 이 문서에만 기록하고, CLI 스펙 문서는 침범하지 않음
- 병렬 에이전트 실행 계획(참조용 요약)
  - compare / calibrate-judge / profile-difficulty / regress / artifacts lint / ops snapshot
  - 각 명령은 1명 오너가 end-to-end로 담당
  - 공유 파일(`commands/__init__.py`, 공통 스키마)은 사전 합의 필요

### 3.4 순서 불명 입력 처리 정책(Stage Metrics)
- 목적: 순서가 깨진 입력에서도 결과를 유지하고, 장기적으로 strict 전환 가능하게 근거를 남긴다.
- 처리 방식
  - `doc_ids`/`scores`가 set 등 순서 없는 타입이면 ordering_warning 메트릭을 기록한다.
  - `scores`가 있으면 점수 내림차순 + doc_id tie-break로 순서를 복원한다.
  - 복원 여부와 원본 상태를 evidence에 기록한다.
- 활용 가이드
  - ordering_warning이 있으면 해당 run을 “순서 복원 적용”으로 표시한다.
  - 비교 리포트에서는 ordering_warning 비율을 함께 확인한다.
  - ordering_warning이 발생한 케이스는 원본 stage 이벤트(`doc_ids`, `scores`)를 점검한다.
  - evidence에 기록된 `unordered_input`/`order_reconstructed`는 재현 분석용으로 보존한다.
- 후속 활용
  - ordering_warning이 있는 케이스만 추적해 strict 기준(순서 강제)으로 전환 가능

### 3.5 ordering_warning 런북(비율/분포 확인)
- 목적: ordering_warning의 빈도와 영향 범위를 주기적으로 확인한다.
- 확인 대상(권장)
  - 최근 N회 run의 ordering_warning 비율
  - 데이터셋별 ordering_warning 분포
  - ordering_warning이 있는 케이스의 precision/recall 변동
- 실행 절차(예시)
  - 비교 리포트에 ordering_warning 비율을 추가로 기록한다.
  - ordering_warning이 1% 이상이면 원본 stage 이벤트를 샘플링 확인한다.
  - 경고가 반복되는 데이터셋은 입력 파이프라인에서 list/tuple 유지 여부를 점검한다.

### 3.6 strict 전환 기준(권장)
- 전환 목표: 순서 복원 대신 “입력 순서 강제”로 품질 게이트를 강화한다.
- 기준(예시)
  - 최근 3회 run에서 ordering_warning 비율이 1% 미만
  - 같은 데이터셋에서 ordering_warning이 반복적으로 발생하지 않음
  - 주요 메트릭(precision/recall)의 분산이 안정화됨
- 전환 방식
  - strict 전환 후 ordering_warning이 발생하면 해당 메트릭은 실패 처리하고, 원인 분석 리포트를 남긴다.
- 운영 가이드 연결
  - strict 전환 시 `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`의 라벨 노이즈 체크리스트와 함께 점검한다.

---

## 4) 전처리 노이즈 규칙 확장(정의)
- 목적: 데이터 입력 단계에서 발생하는 노이즈를 일관된 규칙으로 차단한다.
- 확장 규칙(정의)
  - 숫자만 존재하는 필드(예: "0000")는 노이즈 후보로 표시
  - 특수문자 반복("====", "----")은 노이즈로 제거
  - 동일 토큰 반복("테스트 테스트 테스트")은 중복 제거 후 길이 제한 적용
- 적용 원칙
  - 실제 값과 혼동될 수 있는 경우(보험약관 번호 등)는 제거하지 않고 태깅만 한다.
  - 규칙 적용 시 원본 값을 evidence로 남긴다.

## 5) 향후 적용 계획 (Planned)

### 5.1 Judge 캐스케이드 평가
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 소형 judge로 대량 평가 후 경계 케이스만 상위 모델로 승격
- 기대 효과
  - 비용 절감 + 평가 변동성 완화
- 병렬 개발 연계
  - Stream B(평가 로직)와 Stream D(캘리브레이션) 분리

### 5.2 난이도 프로파일링
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - v0 휴리스틱 기반 난이도 지표 도입
  - v1 정량화 및 난이도 구간별 threshold 운영
- 기대 효과
  - 데이터 난이도 변화로 인한 점수 변동을 분리/설명 가능
- 병렬 개발 연계
  - Stream A(데이터 전처리)와 Stream C(메트릭) 분리

### 5.3 Judge 캘리브레이션 표준화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 표준 예제/다중 judge/휴먼 샘플링을 정례화
- 기대 효과
  - judge drift를 감시하고 점수 신뢰도 향상
- 병렬 개발 연계
  - Stream D(가이드) 단독 진행, Stream B는 API/데이터 포맷만 공유

### 5.4 멀티턴 평가 체계
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 턴 단위 벤치마크/메트릭 설계 및 운영 적용
- 기대 효과
  - 대화형 RAG에서 노이즈 증폭을 억제
- 병렬 개발 연계
  - Stream A(데이터셋 구조)와 Stream B(평가 로직) 협업 필요

### 5.5 Observability 고도화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/handbook/CHAPTERS/00_overview.md`
- 계획
  - 운영 KPI(p95 latency/cost/timeout)와 품질 지표의 결합
  - run_id 기반 관측/비교 자동화
- 기대 효과
  - 운영 환경에서 발생하는 변동 원인을 계측으로 고정
- 병렬 개발 연계
  - Stream C(메트릭)와 Stream E(문서) 병행

---

## 5) 의존성/순서 (병렬 작업 기준)
1. Stream A/B/C는 병렬 시작 가능(서로 다른 파일)
2. Stream D/E는 문서 업데이트로 병렬 진행 가능
3. 공통 스키마 변경이 필요할 때만 순차 합의

---

## 6) WebUI 적용 계획 (ordering_warning 중심)

### 6.1 데이터 소스 위치(Frontend)
- Stage Metrics: `frontend/src/services/api.ts` → `fetchStageMetrics`
- Run 상세: `frontend/src/pages/RunDetails.tsx`
- Run 비교: `frontend/src/pages/CompareRuns.tsx`
- 분석 요약: `frontend/src/pages/AnalysisLab.tsx`

### 6.2 UI 적용 항목
- RunDetails: ordering_warning 배지 + 복원 방식(`order_reconstructed`) 표시
- CompareRuns: base/target ordering_warning 비율 노출
- AnalysisLab: 개선 요약 카드에 ordering_warning 상태 표시
- 운영 문서 링크: ordering_warning 런북 섹션 안내 링크

### 6.3 구현 순서(안전)
1. RunDetails ordering_warning 섹션 추가
2. CompareRuns ordering_warning 비율 표시
3. AnalysisLab 요약 카드에 경고 연결
4. (선택) API 확장: run summary에 ordering_warning_ratio 추가

---

## 7) 적용 우선순위 (권장)

### 6.1 Judge 캐스케이드 평가
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 소형 judge로 대량 평가 후 경계 케이스만 상위 모델로 승격
- 기대 효과
  - 비용 절감 + 평가 변동성 완화

### 6.2 난이도 프로파일링
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - v0 휴리스틱 기반 난이도 지표 도입
  - v1 정량화 및 난이도 구간별 threshold 운영
- 기대 효과
  - 데이터 난이도 변화로 인한 점수 변동을 분리/설명 가능

### 6.3 Judge 캘리브레이션 표준화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 표준 예제/다중 judge/휴먼 샘플링을 정례화
- 기대 효과
  - judge drift를 감시하고 점수 신뢰도 향상

### 6.4 멀티턴 평가 체계
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 턴 단위 벤치마크/메트릭 설계 및 운영 적용
- 기대 효과
  - 대화형 RAG에서 노이즈 증폭을 억제

### 6.5 Observability 고도화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/handbook/CHAPTERS/00_overview.md`
- 계획
  - 운영 KPI(p95 latency/cost/timeout)와 품질 지표의 결합
  - run_id 기반 관측/비교 자동화
- 기대 효과
  - 운영 환경에서 발생하는 변동 원인을 계측으로 고정

---

## 8) 적용 우선순위 (권장)
1. 데이터 전처리 고정 및 기준선 유지
2. 언어 정렬(한국어 프롬프트 기본 적용)
3. NaN/폴백 경로 안정화
4. Stage 메트릭 기반 원인 분리
5. 휴먼 피드백 캘리브레이션 프로세스 실행
6. Judge 캐스케이드/난이도 프로파일링/멀티턴 체계 순차 도입

---

## 9) Evidence Index
- 데이터 전처리: `src/evalvault/domain/services/dataset_preprocessor.py`
- 언어 정렬/폴백: `src/evalvault/domain/services/evaluator.py`
- Stage 메트릭: `src/evalvault/domain/services/stage_metric_service.py`
- 캘리브레이션 가이드: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- 개선 로드맵: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 시스템 개요: `docs/handbook/CHAPTERS/00_overview.md`
