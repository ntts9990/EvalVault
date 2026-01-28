# EvalVault Run 엑셀 시트/컬럼 요약

대상 파일: `data/db/evalvault_run_197ecbfe-6810-4fe1-a579-ee1f66bce2d1.xlsx`

## Summary
- 컬럼 설명
  - `run_id`: 실행 ID
  - `dataset_name`: 데이터셋 이름
  - `model_name`: 사용 모델
  - `started_at` / `finished_at`: 실행 시작/종료 시각
  - `total_test_cases`: 테스트 케이스 수
  - `total_tokens`: 총 토큰 사용량
  - `total_cost_usd`: 총 비용(USD)
  - `pass_rate`: 통과율
  - `metrics_evaluated`: 평가 메트릭 목록
  - `prompt_set_id` / `prompt_set_name`: 프롬프트 스냅샷 식별자/이름
- 샘플: `run_id=197ecbfe...`, `dataset=ragas_ko90_en10`, `model=ollama/gemma3:1b`, `total_test_cases=30`, `pass_rate=0.6`

## Run
- 컬럼 설명
  - `run_id`: 실행 ID
  - `dataset_name` / `dataset_version`: 데이터셋 이름/버전
  - `model_name`: 사용 모델
  - `started_at` / `finished_at`: 실행 시작/종료 시각
  - `total_tokens` / `total_cost_usd`: 토큰/비용 합계
  - `pass_rate`: 통과율
  - `metrics_evaluated`: 평가 메트릭 목록
  - `thresholds`: 메트릭 임계값(JSON)
  - `langfuse_trace_id`: Langfuse 트레이스 ID
  - `metadata`: 실행 메타데이터(JSON)
  - `retrieval_metadata`: 리트리버 메타데이터(JSON)
  - `created_at`: 저장 시각
- 샘플: `dataset_version=1.1.0`, `thresholds={"answer_relevancy":0.7}`, `metadata.ragas_prompt_overrides={"answer_relevancy":"applied"}`

## TestCases
- 컬럼 설명
  - `id`: 결과 레코드 ID
  - `run_id`: 실행 ID
  - `test_case_id`: 테스트 케이스 ID
  - `tokens_used`: 케이스별 토큰 사용량
  - `latency_ms`: 처리 지연(ms)
  - `cost_usd`: 비용(USD)
  - `trace_id`: 트레이스 ID
  - `started_at` / `finished_at`: 케이스 시작/종료 시각
  - `question` / `answer`: 질문/답변
  - `contexts`: 컨텍스트(JSON)
  - `ground_truth`: 정답/레퍼런스
- 샘플: `test_case_id=tc-001`, `question=서울의 수도는...`, `contexts=[...]`, `ground_truth=대한민국의 수도는 서울입니다.`

## MetricScores
- 컬럼 설명
  - `result_id`: TestCases의 결과 ID
  - `test_case_id`: 테스트 케이스 ID
  - `metric_name`: 메트릭 이름
  - `score`: 점수
  - `threshold`: 임계값
  - `reason`: 점수 근거/사유
- 샘플: `metric_name=answer_relevancy`, `score=0.5987`, `threshold=0.7`

## MetricsSummary
- 컬럼 설명
  - `metric_name`: 메트릭 이름
  - `avg_score`: 평균 점수
  - `pass_rate`: 통과율
  - `samples`: 샘플 수
- 샘플: `avg_score=0.7200`, `pass_rate=0.6`, `samples=30`

## CustomMetrics
- 컬럼 설명
  - `schema_version`: 스냅샷 스키마 버전
  - `metric_name`: 메트릭 이름
  - `source`: 메트릭 출처 (custom)
  - `description`: 메트릭 설명
  - `evaluation_method`: 평가 방식
  - `inputs`: 입력 필드 목록
  - `output`: 점수 범위/판정 규칙
  - `evaluation_process`: 평가 과정 요약
  - `rules`: 키워드/정규식/가중치 등
  - `notes`: 도메인 특화/해석 주의사항
  - `implementation_path`: 구현 파일 경로
  - `implementation_hash`: 구현 파일 해시
- 샘플: `metric_name=entity_preservation`, `evaluation_method=rule-based`

## RunPromptSets
- 컬럼 설명
  - `run_id`: 실행 ID
  - `prompt_set_id`: 프롬프트 세트 ID
  - `created_at`: 저장 시각
- 샘플: `prompt_set_id=c483d949...`

## PromptSets
- 컬럼 설명
  - `prompt_set_id`: 프롬프트 세트 ID
  - `name`: 세트 이름
  - `description`: 설명
  - `metadata`: 메타데이터(JSON)
  - `created_at`: 생성 시각
- 샘플: `name=run-197ecbfe`, `metadata.metrics=["answer_relevancy"]`

## PromptSetItems
- 컬럼 설명
  - `id`: 아이템 ID
  - `prompt_set_id`: 프롬프트 세트 ID
  - `prompt_id`: 프롬프트 ID
  - `role`: 역할(system/user/assistant 등)
  - `item_order`: 순서
  - `metadata`: 메타데이터(JSON)
- 샘플: `role=system`, `item_order=0`

## Prompts
- 컬럼 설명
  - `prompt_id`: 프롬프트 ID
  - `name`: 이름
  - `kind`: 종류
  - `content`: 프롬프트 본문
  - `checksum`: 체크섬
  - `source`: 출처
  - `notes`: 메모
  - `metadata`: 메타데이터(JSON)
  - `created_at`: 생성 시각
- 샘플: `name=system_override`, `source=prompts/system_override.txt`

## Feedback
- 컬럼 설명
  - `id`: 피드백 ID
  - `run_id`: 실행 ID
  - `test_case_id`: 테스트 케이스 ID
  - `satisfaction_score`: 만족도 점수
  - `thumb_feedback`: 좋아요/싫어요
  - `comment`: 코멘트
  - `rater_id`: 평가자 ID
  - `created_at`: 생성 시각
- 샘플: 데이터 없음

## ClusterMaps
- 컬럼 설명
  - `run_id`: 실행 ID
  - `map_id`: 클러스터 맵 ID
  - `test_case_id`: 테스트 케이스 ID
  - `cluster_id`: 클러스터 ID
  - `source`: 생성 소스
  - `metadata`: 메타데이터(JSON)
  - `created_at`: 생성 시각
- 샘플: 데이터 없음

## StageEvents
- 컬럼 설명
  - `id`: 이벤트 ID
  - `run_id`: 실행 ID
  - `stage_id`: 단계 ID
  - `parent_stage_id`: 상위 단계 ID
  - `stage_type`: 단계 유형
  - `stage_name`: 단계 이름
  - `status`: 상태
  - `attempt`: 재시도 횟수
  - `started_at` / `finished_at`: 시작/종료 시각
  - `duration_ms`: 소요 시간(ms)
  - `input_ref` / `output_ref`: 입력/출력 참조
  - `attributes`: 이벤트 속성(JSON)
  - `metadata`: 메타데이터(JSON)
  - `trace_id` / `span_id`: 트레이스/스팬 ID
- 샘플: 데이터 없음

## StageMetrics
- 컬럼 설명
  - `id`: 메트릭 ID
  - `run_id`: 실행 ID
  - `stage_id`: 단계 ID
  - `metric_name`: 메트릭 이름
  - `score`: 점수
  - `threshold`: 임계값
  - `evidence`: 증거(JSON)
- 샘플: 데이터 없음

## AnalysisReports
- 컬럼 설명
  - `report_id`: 리포트 ID
  - `run_id`: 실행 ID
  - `experiment_id`: 실험 ID
  - `report_type`: 리포트 유형
  - `format`: 포맷
  - `content`: 본문
  - `metadata`: 메타데이터(JSON)
  - `created_at`: 생성 시각
- 샘플: 데이터 없음

## PipelineResults
- 컬럼 설명
  - `result_id`: 파이프라인 결과 ID
  - `intent`: 의도
  - `query`: 질의
  - `run_id`: 실행 ID
  - `pipeline_id`: 파이프라인 ID
  - `profile`: 프로필
  - `tags`: 태그(JSON)
  - `metadata`: 메타데이터(JSON)
  - `is_complete`: 완료 여부
  - `duration_ms`: 소요 시간(ms)
  - `final_output`: 최종 출력(JSON)
  - `node_results`: 노드 결과(JSON)
  - `started_at` / `finished_at` / `created_at`: 시각 정보
- 샘플: 데이터 없음

## MultiTurnRun
- 컬럼 설명
  - `run_id`: 멀티턴 실행 ID
  - `dataset_name` / `dataset_version`: 데이터셋 이름/버전
  - `model_name`: 사용 모델
  - `started_at` / `finished_at`: 실행 시작/종료 시각
  - `conversation_count`: 대화 수
  - `turn_count`: 턴 수
  - `metrics_evaluated`: 평가 메트릭 목록
  - `drift_threshold`: 드리프트 임계값
  - `summary`: 요약(JSON)
  - `metadata`: 메타데이터(JSON)
  - `created_at`: 저장 시각
- 샘플: `conversation_count=50`, `drift_threshold=0.1`

## MultiTurnConversations
- 컬럼 설명
  - `run_id`: 멀티턴 실행 ID
  - `conversation_id`: 대화 ID
  - `turn_count`: 대화별 턴 수
  - `drift_score`: 드리프트 점수
  - `drift_threshold`: 드리프트 임계값
  - `drift_detected`: 드리프트 감지 여부
  - `summary`: 대화 요약(JSON)
- 샘플: `drift_detected=1`

## MultiTurnTurns
- 컬럼 설명
  - `id`: 턴 결과 ID
  - `run_id`: 멀티턴 실행 ID
  - `conversation_id`: 대화 ID
  - `turn_id`: 턴 ID
  - `turn_index`: 턴 인덱스
  - `role`: user/assistant
  - `passed`: 턴 통과 여부
  - `latency_ms`: 응답 지연(ms)
  - `metadata`: 턴 메타데이터(JSON)
- 샘플: `role=assistant`, `turn_index=3`

## MultiTurnTurnMetrics
- 컬럼 설명
  - `turn_result_id`: 턴 결과 ID
  - `conversation_id`: 대화 ID
  - `turn_id`: 턴 ID
  - `turn_index`: 턴 인덱스
  - `metric_name`: 메트릭 이름
  - `score`: 점수
  - `threshold`: 임계값
- 샘플: `metric_name=faithfulness`, `score=0.82`
