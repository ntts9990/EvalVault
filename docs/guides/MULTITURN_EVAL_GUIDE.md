# 멀티턴 평가 가이드

이 문서는 멀티턴(대화형) RAG 평가를 **단일 턴 데이터셋 구조** 안에서 운영하는 최소 기준을 정의합니다.

## 핵심 원칙
- 멀티턴은 `test_cases`를 평탄화(flatten)하고, 메타데이터로 세션/턴을 연결합니다.
- 기존 로더/평가/분석 파이프라인을 변경하지 않고, 추가 메타데이터로 멀티턴 집계를 수행합니다.

## 데이터셋 필드 규약 (필수)
`test_cases[].metadata`에 아래 키를 넣습니다.

```json
{
  "metadata": {
    "conversation_id": "conv-001",
    "turn_index": 1,
    "turn_id": "t01"
  }
}
```

### 필드 정의
- `conversation_id`: 동일 대화 세션 식별자
- `turn_index`: 턴 순서(정수)
- `turn_id`: 턴 고유 ID (선택적으로 문자열)

## 실행/분석 흐름
1. `evalvault run`으로 실행 후 `--auto-analyze` 또는 별도 분석 파이프라인 실행
2. 분석 파이프라인의 `multiturn_analyzer` 모듈이 대화/턴 집계를 생성
3. 산출물은 `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`에 등록

## 산출물 요약
`multiturn_analyzer` 모듈 출력:
- `summary`: 대화 수, 평균 턴 수, 대화 단위 통과율, 최초 실패 턴 분포
- `conversations`: 대화별 요약(최악 턴, 메트릭 평균)
- `turns`: 턴 단위 상세
- `coverage`: conversation_id/turn_index 커버리지

## 주의사항
- `turn_index`가 누락되면 대화 순서를 정확히 복원할 수 없습니다.
- `conversation_id`가 없는 케이스는 대화 집계에서 제외됩니다.

## 예시 템플릿
- `docs/templates/dataset_template.json`
- `docs/templates/ragas_dataset_example_ko90_en10.json`
