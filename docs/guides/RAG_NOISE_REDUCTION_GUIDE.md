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
  - 대상: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/new_whitepaper/01_overview.md`

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

### 3.4 순서 불명 입력 처리 정책(Stage Metrics)
- 목적: 순서가 깨진 입력에서도 결과를 유지하고, 장기적으로 strict 전환 가능하게 근거를 남긴다.
- 처리 방식
  - `doc_ids`/`scores`가 set 등 순서 없는 타입이면 ordering_warning 메트릭을 기록한다.
  - `scores`가 있으면 점수 내림차순 + doc_id tie-break로 순서를 복원한다.
  - 복원 여부와 원본 상태를 evidence에 기록한다.
- 후속 활용
  - ordering_warning이 있는 케이스만 추적해 strict 기준(순서 강제)으로 전환 가능

---

## 4) 향후 적용 계획 (Planned)

### 4.1 Judge 캐스케이드 평가
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 소형 judge로 대량 평가 후 경계 케이스만 상위 모델로 승격
- 기대 효과
  - 비용 절감 + 평가 변동성 완화
- 병렬 개발 연계
  - Stream B(평가 로직)와 Stream D(캘리브레이션) 분리

### 4.2 난이도 프로파일링
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - v0 휴리스틱 기반 난이도 지표 도입
  - v1 정량화 및 난이도 구간별 threshold 운영
- 기대 효과
  - 데이터 난이도 변화로 인한 점수 변동을 분리/설명 가능
- 병렬 개발 연계
  - Stream A(데이터 전처리)와 Stream C(메트릭) 분리

### 4.3 Judge 캘리브레이션 표준화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 표준 예제/다중 judge/휴먼 샘플링을 정례화
- 기대 효과
  - judge drift를 감시하고 점수 신뢰도 향상
- 병렬 개발 연계
  - Stream D(가이드) 단독 진행, Stream B는 API/데이터 포맷만 공유

### 4.4 멀티턴 평가 체계
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 턴 단위 벤치마크/메트릭 설계 및 운영 적용
- 기대 효과
  - 대화형 RAG에서 노이즈 증폭을 억제
- 병렬 개발 연계
  - Stream A(데이터셋 구조)와 Stream B(평가 로직) 협업 필요

### 4.5 Observability 고도화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/new_whitepaper/01_overview.md`
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

## 6) 적용 우선순위 (권장)

### 3.1 Judge 캐스케이드 평가
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 소형 judge로 대량 평가 후 경계 케이스만 상위 모델로 승격
- 기대 효과
  - 비용 절감 + 평가 변동성 완화

### 3.2 난이도 프로파일링
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - v0 휴리스틱 기반 난이도 지표 도입
  - v1 정량화 및 난이도 구간별 threshold 운영
- 기대 효과
  - 데이터 난이도 변화로 인한 점수 변동을 분리/설명 가능

### 3.3 Judge 캘리브레이션 표준화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 표준 예제/다중 judge/휴먼 샘플링을 정례화
- 기대 효과
  - judge drift를 감시하고 점수 신뢰도 향상

### 3.4 멀티턴 평가 체계
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 계획
  - 턴 단위 벤치마크/메트릭 설계 및 운영 적용
- 기대 효과
  - 대화형 RAG에서 노이즈 증폭을 억제

### 3.5 Observability 고도화
- 근거: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/new_whitepaper/01_overview.md`
- 계획
  - 운영 KPI(p95 latency/cost/timeout)와 품질 지표의 결합
  - run_id 기반 관측/비교 자동화
- 기대 효과
  - 운영 환경에서 발생하는 변동 원인을 계측으로 고정

---

## 4) 적용 우선순위 (권장)
1. 데이터 전처리 고정 및 기준선 유지
2. 언어 정렬(한국어 프롬프트 기본 적용)
3. NaN/폴백 경로 안정화
4. Stage 메트릭 기반 원인 분리
5. 휴먼 피드백 캘리브레이션 프로세스 실행
6. Judge 캐스케이드/난이도 프로파일링/멀티턴 체계 순차 도입

---

## 5) Evidence Index
- 데이터 전처리: `src/evalvault/domain/services/dataset_preprocessor.py`
- 언어 정렬/폴백: `src/evalvault/domain/services/evaluator.py`
- Stage 메트릭: `src/evalvault/domain/services/stage_metric_service.py`
- 캘리브레이션 가이드: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
- 개선 로드맵: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- 시스템 개요: `docs/new_whitepaper/01_overview.md`
