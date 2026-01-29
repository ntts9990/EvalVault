# 02. Data & Metrics (입력, 점수, 합격 판정, 산출물)

이 장은 EvalVault를 "데이터 -> 메트릭 -> 임계값 -> 산출물" 관점에서 끝까지 풀어쓴다.
평가의 신뢰도는 결국 아래 4가지에서 나온다.

- 입력(데이터셋)이 무엇을 의미하는지 명확함
- 점수(메트릭)가 무엇을 측정하는지 명확함
- 합격 판정(임계값/우선순위)이 일관됨
- 산출물(리포트/아티팩트)이 재현 가능한 근거를 남김

이 문서는 "외부 문서 없이도" 데이터 설계/메트릭 선택/게이트 기준을 결정할 수 있게 작성한다.
사실 주장은 코드/템플릿 경로로 근거를 남긴다.

## TL;DR

- 데이터셋은 `Dataset`(test_cases + thresholds)로 모델링된다.
  - 근거: `src/evalvault/domain/entities/dataset.py#Dataset`.
- JSON/CSV/Excel을 지원하고, 파일 확장자 기반으로 로더가 선택된다.
  - 근거: `src/evalvault/adapters/outbound/dataset/loader_factory.py#get_loader`.
- JSON thresholds는 0.0~1.0 범위 숫자로 검증된다.
  - 근거: `src/evalvault/adapters/outbound/dataset/json_loader.py`.
- CSV/Excel thresholds는 `threshold_*` 컬럼(예: `threshold_faithfulness`)에서 추출된다.
  - 근거: `src/evalvault/adapters/outbound/dataset/thresholds.py#THRESHOLD_COLUMN_MAP`, `extract_thresholds_from_rows`.
- 도메인 평가 실행에서 임계값 우선순위는 "요청값 > 데이터셋 > 기본"이다.
  - 근거: `src/evalvault/domain/services/evaluator.py#RagasEvaluator.evaluate`의 threshold resolve.
- Web/CLI 레이어에서는 threshold profile을 추가로 적용해 "추천 기준"을 덮어쓸 수 있다.
  - 근거: `src/evalvault/domain/services/threshold_profiles.py#apply_threshold_profile`, `src/evalvault/adapters/inbound/api/adapter.py`(threshold_profile 적용), `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_resolve_thresholds`.
- 분석 아티팩트는 per-node JSON + `index.json`(목차)로 저장된다.
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.
- 아티팩트 디렉터리는 lint로 검증 가능하다.
  - 근거: `src/evalvault/domain/services/artifact_lint_service.py#ArtifactLintService`.

## 목차

- 1. 데이터 모델: Dataset/TestCase/Run/MetricScore
- 2. 데이터셋 파일 포맷: JSON/CSV/Excel
- 3. contexts/ground_truth/metadata 설계 원칙
- 4. 메트릭 카탈로그(레지스트리)와 선택 전략
- 5. 임계값(Threshold): 어디서 오고, 어떤 우선순위로 적용되는가
- 6. pass_rate의 의미: 어떤 "합격"을 말하는가
- 7. 산출물 계층: 리포트 vs 아티팩트
- 8. `artifacts/index.json` 스키마와 활용
- 9. 실패 모드/디버깅 가이드
- 10. 체크리스트 / FAQ / 자기 점검 질문
- 11. 데이터셋 가드레일: 전처리(DatasetPreprocessor)
- 12. CSV/Excel 파싱 디테일: contexts/metadata/thresholds
- 13. 컨텍스트가 없을 때: retriever로 채우기(메타데이터 포함)
- 14. 메트릭 카탈로그(상세): 의미/입력/실패 모드/해석
- 15. 임계값(Threshold) 운영 플레이북: 기본값/프로필/오버라이드/실수 방지
- 16. 산출물/아티팩트 심화: index.json, lint, MCP로 조회
- 17. 실전 레시피: QA/요약/검색 태스크별 데이터 설계
- 18. 부록: 자주 쓰는 명령/템플릿/자가 점검(확장)
- 19. 평가 실행의 데이터 플로우: Dataset -> Run -> Score -> Gate
- 20. 메트릭별 디버깅 플레이북(상세)
- 21. 토큰/비용/지연시간: 무엇을 믿고 무엇을 의심할까
- 22. 재현성 설계: run_id, dataset_version, tracker_metadata
- 23. 고급(짧게): Stage Events/Stage Metrics는 무엇이고 어디에 두나
- 24. 데이터셋 제작 워크샵: "좋은 케이스"를 만드는 체크리스트
- 25. 메트릭 조합 패턴(권장): 목적별 최소/표준/심화 세트
- 26. Threshold 튜닝 워크플로: 안전하게 바꾸고, 의미 있게 비교하기
- 27. 실습: 데이터셋/메트릭/threshold를 스스로 설계해보기
- 28. 미니 용어사전(데이터/메트릭)
- 29. Evidence 인덱스(근거 경로 모음)

---

## 1. 데이터 모델: Dataset/TestCase/Run/MetricScore

EvalVault에서 데이터 설계는 "파일 포맷"이 아니라 "도메인 엔티티"부터 읽는 게 가장 안전하다.
파일 포맷은 로더가 바꿔줄 수 있지만, 엔티티는 제품의 계약이기 때문이다.

### 1.1 Dataset/TestCase

`TestCase`는 single-turn 평가의 최소 단위이며, Ragas 샘플과 매핑된다.

- 근거: `src/evalvault/domain/entities/dataset.py#TestCase`.

핵심 필드:

- `id`: 비교/회귀/클러스터링/피드백의 조인 키
- `question`: user_input
- `answer`: response(모델 출력)
- `contexts`: retrieved_contexts
- `ground_truth`(optional): reference
- `metadata`(optional): 분석/필터링/진단에 쓰는 확장 필드

Ragas 입력으로는 아래처럼 변환된다.

- 근거: `src/evalvault/domain/entities/dataset.py#TestCase.to_ragas_dict`.

```python
{
  "user_input": question,
  "response": answer,
  "retrieved_contexts": contexts,
  # ground_truth가 있으면 "reference"로 포함
}
```

`Dataset`은 test_cases + dataset-level thresholds를 가진다.

- 근거: `src/evalvault/domain/entities/dataset.py#Dataset`.

### 1.2 EvaluationRun/TestCaseResult/MetricScore

평가 결과는 run 단위로 묶인다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun`.

중요한 점:

- `EvaluationRun.thresholds`는 "이번 run에서 실제로 사용된 임계값"이다.
- 각 `TestCaseResult`는 metric별 `MetricScore` 리스트를 갖고, `MetricScore.threshold`를 포함한다.
  - 근거: `src/evalvault/domain/services/evaluator.py`에서 MetricScore 생성 시 threshold를 채워 넣는다.

---

## 2. 데이터셋 파일 포맷: JSON/CSV/Excel

EvalVault는 파일 확장자에 따라 로더를 선택한다.

- 근거: `src/evalvault/adapters/outbound/dataset/loader_factory.py#get_loader`.

### 2.1 JSON

JSON은 표현력이 높다(리스트/객체/metadata 확장에 유리).

템플릿:

- `docs/templates/dataset_template.json`

로더는 최소 `test_cases`를 필수로 요구하고, 각 test_case는 `id/question/answer/contexts`를 필수로 요구한다.

- 근거: `src/evalvault/adapters/outbound/dataset/json_loader.py#JSONDatasetLoader.load`.

thresholds 검증 규칙:

- 숫자여야 한다(int|float)
- 0.0 <= value <= 1.0 범위여야 한다

- 근거: `src/evalvault/adapters/outbound/dataset/json_loader.py`의 thresholds 파싱.

추가 현실 포인트:

- 윈도우 환경에서 흔한 UTF-8 BOM을 처리하기 위해 `utf-8-sig` -> `utf-8` 순서로 읽기를 시도한다.
  - 근거: `src/evalvault/adapters/outbound/dataset/json_loader.py#_read_json_with_bom_handling`.

### 2.2 CSV

CSV는 사람이 편집하기 쉽다. 대신 "문자열 한 칸"에 배열/객체를 넣어야 할 때 규칙이 필요하다.

CSV 로더의 기대 컬럼:

- `id`, `question`, `answer`, `contexts`(필수)
- `ground_truth`(optional)
- `threshold_*`(optional)

- 근거: `src/evalvault/adapters/outbound/dataset/csv_loader.py#CSVDatasetLoader.load` docstring.

thresholds 추출 규칙:

- 상단 N개 행(기본 50행)에서 처음으로 등장하는 non-empty threshold 값을 메트릭별로 채운다.
  - 근거: `src/evalvault/adapters/outbound/dataset/thresholds.py#extract_thresholds_from_rows`.

지원 threshold 컬럼(현재 코드 기준):

- `threshold_faithfulness` -> `faithfulness`
- `threshold_answer_relevancy` -> `answer_relevancy`
- `threshold_context_precision` -> `context_precision`
- `threshold_context_recall` -> `context_recall`
- `threshold_factual_correctness` -> `factual_correctness`
- `threshold_semantic_similarity` -> `semantic_similarity`

- 근거: `src/evalvault/adapters/outbound/dataset/thresholds.py#THRESHOLD_COLUMN_MAP`.

CSV 인코딩 호환:

- UTF-8(BOM 포함) -> UTF-8 -> CP949 -> EUC-KR -> Latin-1 순서로 시도
- 가능하면 chardet가 있으면 먼저 감지 시도

- 근거: `src/evalvault/adapters/outbound/dataset/csv_loader.py#ENCODING_FALLBACKS` + `_read_csv_with_encoding_fallback`.

### 2.3 Excel

Excel 로더는 pandas를 사용하며, 확장자에 따라 엔진을 선택한다.

- `.xlsx`: `openpyxl`
- `.xls`: `xlrd`(없으면 설치 안내 오류)

- 근거: `src/evalvault/adapters/outbound/dataset/excel_loader.py#ExcelDatasetLoader`.

thresholds 추출 규칙은 CSV와 동일하다.

- 근거: `src/evalvault/adapters/outbound/dataset/excel_loader.py`에서 `extract_thresholds_from_rows` 사용.

---

## 3. contexts/ground_truth/metadata 설계 원칙

이 절은 "어떤 필드를 넣어야 점수가 의미가 있는가"를 설명한다.

### 3.1 contexts: "점수"보다 먼저 품질을 결정하는 입력

많은 메트릭이 contexts에 강하게 의존한다.

- faithfulness 계열: contexts가 "근거"가 아니면 점수/진단 모두 왜곡될 수 있다.
- 요약 계열(summary_score/summary_faithfulness): contexts는 요약의 근거가 된다.

실무 규칙(권장):

- contexts는 "정답을 포함"하는 게 아니라, "답변이 정당화될 수 있는 근거"를 포함해야 한다.
- contexts 노이즈(무관 문장)가 많으면 LLM judge가 흔들리고, 회귀 비교에서 분산이 커진다.

### 3.2 ground_truth: 언제 필요하고, 언제 위험한가

ground_truth는 메트릭의 요구사항에 의해 필요해진다.

- 메트릭별 요구사항은 레지스트리에서 확인 가능하다.
  - 근거: `src/evalvault/domain/metrics/registry.py#MetricSpec.requires_ground_truth`.

ground_truth를 넣을 때의 함정:

- QA에서 "정답"은 단일 문장으로 고정하기 어렵다.
- ground_truth가 불완전하면, factual_correctness/semantic_similarity 같은 메트릭이 모델 개선을 "나쁜 방향"으로 유도할 수 있다.

따라서 ground_truth 기반 메트릭을 gate로 쓰려면, ground_truth의 품질 관리가 필요하다.

### 3.3 metadata: 분석/운영을 위해 꼭 필요한 최소 구조

metadata는 "점수"가 아니라 "왜"를 위한 인덱스다.

- 태그(도메인/언어/난이도)
- 요약 태스크라면 summary_intent/summary_tags 같은 분류 키
  - 근거: CSV/Excel 로더는 `summary_tags`, `summary_intent` 컬럼을 metadata로 흡수할 수 있다.
    - `src/evalvault/adapters/outbound/dataset/csv_loader.py`, `src/evalvault/adapters/outbound/dataset/excel_loader.py`.

원칙:

- metadata는 "필터링/그룹핑"에 쓸 수 있게, 문자열/리스트/플랫한 딕셔너리 중심으로 유지한다.
- 너무 자유롭게 중첩시키면 나중에 UI/리포트에서 쓰기 어려워진다.

---

## 4. 메트릭 카탈로그(레지스트리)와 선택 전략

EvalVault는 "가능한 메트릭"과 "메트릭의 요구사항"을 레지스트리로 관리한다.

- 근거: `src/evalvault/domain/metrics/registry.py`.

### 4.1 MetricSpec의 의미

MetricSpec은 최소한 아래 정보를 제공한다.

- name
- description
- requires_ground_truth
- requires_embeddings
- source: ragas/custom
- category: qa/summary/retrieval/domain
- signal_group: groundedness/intent_alignment/... 등

- 근거: `src/evalvault/domain/metrics/registry.py#MetricSpec`.

이 정보는 "데이터셋 설계"로 바로 이어진다.

- requires_ground_truth=True이면: dataset의 test_cases에 ground_truth를 넣어야 한다.
- requires_embeddings=True이면: embedding 설정/어댑터가 준비되어야 하고, 일부 환경에서는 비용/성능 영향을 고려해야 한다.

### 4.2 메트릭 선택 3단계(레포 기준으로 구체화)

1) 태스크 분류: qa vs summary vs retrieval

- category는 레지스트리에 있다.
  - 근거: `src/evalvault/domain/metrics/registry.py`.

2) 입력 요구사항 확인

- ground_truth 요구
- embeddings 요구

3) 신호 그룹(signal_group)으로 "겹치는 메트릭"을 피한다

- 같은 signal_group을 여러 개 gate로 두면 같은 실패를 중복해서 측정할 수 있다.
- 예: groundedness 계열 2개를 동시에 gate로 두는 건 의도적으로 하고 있는지 확인해야 한다.

---

## 5. 임계값(Threshold): 어디서 오고, 어떤 우선순위로 적용되는가

임계값은 "점수"를 "결정"으로 바꾸는 스위치다.
같은 점수라도 threshold가 바뀌면 합격/불합격이 바뀐다.

### 5.1 도메인 평가 실행에서의 기본 우선순위

도메인 서비스(`RagasEvaluator.evaluate`)에서 thresholds 해석은 아래 순서다.

1) 요청으로 전달된 thresholds dict
2) dataset.thresholds
3) 메트릭별 기본값(default_threshold_for)

- 근거: `src/evalvault/domain/services/evaluator.py#RagasEvaluator.evaluate`.

중요:

- 즉, 도메인 서비스 관점에서는 "프로필"이 기본 우선순위에 포함되지 않는다.
- 프로필은 CLI/Web 레이어에서 thresholds를 미리 계산해서 도메인에 전달하는 방식으로 붙는다.

### 5.2 threshold profile: 추천 기준을 "일괄 적용"하는 메커니즘

threshold profile은 목적별 추천 임계값 세트다.

- 근거: `src/evalvault/domain/services/threshold_profiles.py#THRESHOLD_PROFILES`.

현재 제공되는 프로필(코드 기준):

- `qa`
- `summary`

- 근거: `src/evalvault/domain/services/threshold_profiles.py`.

프로필 적용 방식:

- 주어진 metrics 목록에 포함된 항목만 덮어쓴다.
- profile 문자열은 소문자/trim으로 정규화된다.
- unknown profile이면 예외가 난다(available 목록 포함).

- 근거: `src/evalvault/domain/services/threshold_profiles.py#apply_threshold_profile`.

CLI에서의 적용 예:

- dataset.thresholds를 기반으로 metric별 기본(0.7)로 채우고, profile을 덮어쓴다.
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_resolve_thresholds`.

Web API에서의 적용 예:

- dataset.thresholds를 base로, 요청 thresholds를 덮고, profile을 덮는다.
  - 근거: `src/evalvault/adapters/inbound/api/adapter.py`의 threshold resolution.

### 5.3 dataset thresholds vs profile: 무엇을 "진실"로 둘 것인가

팀/운영 관점에서 선택지가 있다.

1) dataset에 thresholds를 박아두고, profile은 최소만 사용

- 장점: 데이터셋 자체가 "정의"가 된다. 재현/공유가 쉽다.
- 단점: threshold 변경이 dataset 변경으로 이어져 PR이 잦아질 수 있다.

2) profile을 기준으로 운영하고, dataset thresholds는 비워두기

- 장점: 목적(qa vs summary)별로 일관된 정책 적용이 쉽다.
- 단점: 프로필/환경에 따라 같은 dataset이 다른 결과가 날 수 있어, 비교 시 혼동이 생길 수 있다.

EvalVault는 둘 다 지원한다. 중요한 건 "팀에서 기준을 고정"하는 것이다.

---

## 6. pass_rate의 의미: 어떤 "합격"을 말하는가

EvalVault에는 "합격" 개념이 2개가 공존한다.
이 둘을 혼동하면 리포트/게이트가 서로 다른 말을 하게 된다.

### 6.1 test-case 기준 pass_rate

`EvaluationRun.pass_rate`는 "모든 메트릭을 통과한 test case 비율"이다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.pass_rate` + `passed_test_cases`.

해석:

- 메트릭이 3개면, 한 test case가 3개 모두 threshold를 넘을 때만 합격 카운트가 올라간다.

### 6.2 metric 기준 metric_pass_rate

`EvaluationRun.metric_pass_rate`는 "각 메트릭 평균이 threshold를 넘는 비율"이다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.metric_pass_rate`.

해석:

- test case 개별 합격과는 다른 신호다.
- 운영에서 "어느 메트릭이 전반적으로 위험한가"를 빠르게 보는 지표로 유용할 수 있다.

---

## 7. 산출물 계층: 리포트 vs 아티팩트

EvalVault는 결과를 "사람용"과 "근거용"으로 분리해 남기는 방향을 택한다.

### 7.1 사람용: 요약 JSON/Markdown

사람용 산출물은 빠르게 훑고 공유하고 의사결정하기 위한 결과다.
반대로 사람용만 남기면, 왜 그런 결론이 나왔는지 재현하기 어렵다.

### 7.2 근거용: 아티팩트 디렉터리

분석 파이프라인은 노드별 결과를 JSON으로 남기고, 그 목차를 index.json으로 남긴다.

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

### 7.3 (추가) DB에 저장되는 분석 결과: `analysis_results`

아티팩트는 “파일 기반 근거”이고, DB는 “조회/히스토리/연동(UI/API)”를 위한 저장소다.
EvalVault는 run 단위로 다양한 분석 결과를 DB에 저장하며, 대표 테이블이 `analysis_results`다.

- 스키마: `src/evalvault/adapters/outbound/storage/postgres_schema.sql` (Postgres + pgvector)

`analysis_results.analysis_type`는 문자열 enum처럼 쓰이며, 대표 값은 아래와 같다.

- `statistical`
- `nlp`
- `causal`
- `data_quality`
- `dataset_features`
  - 근거(enum): `src/evalvault/domain/entities/analysis.py#AnalysisType`

특히 `dataset_features`(데이터셋 특성 분석)는 파이프라인 노드 `dataset_feature_analysis`의 출력(dict)을 JSON으로 저장한다.

- 저장(best-effort, CLI): `src/evalvault/adapters/inbound/cli/commands/pipeline.py` (`save_dataset_feature_analysis` 호출)
- 저장 구현(Postgres): `src/evalvault/adapters/outbound/storage/postgres_adapter.py#save_dataset_feature_analysis`

artifact 파일 이름 규칙(안전한 파일명으로 sanitize):

- node_id에서 알파벳/숫자/._- 외 문자는 _로 치환
- 비어 있으면 "artifact"로 대체

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#_safe_artifact_name`.

---

## 8. `artifacts/index.json` 스키마와 활용

### 8.1 index.json이 담는 것

index.json은 "파이프라인 결과를 탐색하는 목차"다.

필드(코드 기준):

- pipeline_id
- intent
- duration_ms
- started_at / finished_at
- nodes: [{node_id, status, duration_ms, error, path}, ...]
- final_output_path(optional)

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

### 8.2 lint: index.json을 신뢰할 수 있게 만드는 안전장치

아티팩트는 "있어야 할 파일이 사라졌을 때"가 가장 위험하다.
리포트는 남아 있는데 근거 파일이 없는 상태가 되면, 다음 분석/디버깅이 불가능해진다.

ArtifactLintService는 아래를 검증한다.

- artifacts_dir 존재/디렉터리 여부
- index.json 존재 여부
- index.json이 JSON object인지
- pipeline_id 존재
- nodes가 list인지
- 각 node의 path가 존재하는지(absolute/relative 해석)

- 근거: `src/evalvault/domain/services/artifact_lint_service.py#ArtifactLintService`.

strict 모드 의미:

- 파일이 없을 때 warning이 아니라 error로 처리한다.
- 근거: `src/evalvault/domain/services/artifact_lint_service.py`의 `_validate_path`.

---

## 9. 실패 모드/디버깅 가이드

### 9.1 "점수가 이상하다"의 80%는 입력 문제다

- contexts가 비어 있음/무관함/중복됨
- question/answer가 비어 있음
- ground_truth 품질이 낮음

평가 전처리 결과는 run 메타데이터에 남을 수 있다.

- 근거: `src/evalvault/domain/services/evaluator.py`에서 dataset_preprocess finding을 tracker_metadata에 기록.

### 9.2 thresholds가 기대와 다르게 적용된다

가능한 원인:

- 도메인 서비스는 profile을 모른다(이미 계산된 thresholds dict만 본다).
- CLI/Web 레이어에서 profile을 덮어쓴 값이 최종 thresholds가 된다.

따라서 디버깅 순서는 아래가 안전하다.

1) dataset.thresholds가 무엇인지 확인
2) 요청 thresholds(dict)가 무엇인지 확인
3) profile이 적용됐는지 확인
4) 최종 run.thresholds를 확인

- 근거: `src/evalvault/domain/services/evaluator.py`, `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_resolve_thresholds`, `src/evalvault/adapters/inbound/api/adapter.py`.

---

## 10. 체크리스트 / FAQ / 자기 점검 질문

### 체크리스트(데이터/메트릭)

- [ ] test_case `id`가 안정적이고 유일한가?
- [ ] 선택한 메트릭의 requires_ground_truth/embeddings 요구사항을 충족하는가?
- [ ] thresholds 출처/우선순위(요청 vs dataset vs profile vs default)가 팀에서 고정돼 있는가?
- [ ] pass_rate를 볼 때 "test-case pass"인지 "metric pass"인지 구분했는가?

### 체크리스트(아티팩트)

- [ ] 분석 파이프라인 노드별 JSON이 남는가?
- [ ] `artifacts/index.json`이 존재하고 nodes/path가 유효한가?
- [ ] 아티팩트 lint를 돌렸을 때 경고/오류를 이해할 수 있는가?

### FAQ

Q1. JSON/CSV/Excel 중 무엇을 기준 포맷으로 써야 하나?

- JSON: 확장/중첩 데이터/metadata에 유리(표현력)
- CSV/Excel: 협업 편집에 유리(스프레드시트)

EvalVault는 로더로 통일된 `Dataset` 엔티티로 변환한다.
팀이 "변경/리뷰"하기 쉬운 포맷을 기준으로 고르면 된다.

Q2. thresholds는 dataset에 넣는 게 맞나, profile을 쓰는 게 맞나?

둘 다 가능하지만, 중요한 건 팀 기준을 고정하는 것이다.
혼용하면 회귀 비교에서 "왜 점수가 달라졌나"를 사람이 설명하기 어려워진다.

Q3. index.json이 왜 중요한가?

아티팩트는 많아질수록 "찾을 수 있어야" 가치가 생긴다.
index.json은 탐색/자동화(MCP/CLI 도구)에서 목차로 쓰기 위한 최소 계약이다.

### 자기 점검 질문

1) 내가 선택한 메트릭은 contexts/ground_truth/embeddings 중 무엇을 요구하는가?
2) pass_rate를 보고 "어떤 실패"를 의미하는지 말로 설명할 수 있는가?
3) thresholds가 바뀌었을 때, 결과 해석/게이트 의미가 어떻게 바뀌는가?
4) index.json 없이도 노드별 근거를 1분 안에 찾을 수 있는가?

---

## 11. 데이터셋 가드레일: 전처리(DatasetPreprocessor)

EvalVault는 데이터가 "완벽"하다고 가정하지 않는다.
실무 데이터셋은 아래 문제가 자주 섞인다.

- 질문/답변/컨텍스트가 공백, placeholder("N/A", "TODO")로 채워짐
- contexts에 빈 문자열/기호만 있는 문자열이 섞임
- 같은 contexts가 중복됨(데이터 수집 파이프라인의 중복)
- ground_truth가 비어 있는데, ground_truth가 필요한 메트릭을 선택함

이 상태로 LLM judge 기반 메트릭을 돌리면, 점수의 분산이 커지고 회귀 비교가 깨진다.
그래서 도메인 평가 실행은 데이터셋을 전처리해 "불안정성"을 낮춘다.

근거:

- 전처리 구현: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessor`.
- evaluator가 전처리를 적용하고, finding을 tracker_metadata에 기록: `src/evalvault/domain/services/evaluator.py`.

### 11.1 무엇을 전처리하나(행동 목록)

전처리 로직은 크게 3가지다.

1) 텍스트 정규화

- `\u00a0` 같은 공백 변종을 일반 공백으로 치환
- 연속 공백을 하나로 축약
- 앞뒤 공백 제거

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessor._normalize_text`.

2) 노이즈/placeholder 제거

- 기호만 있는 텍스트는 제거
- placeholder 목록("n/a", "todo", "unknown" 등)과 일치하면 제거

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py`의 `_PUNCT_ONLY_RE`, `_PLACEHOLDER_TEXT`, `_is_noise_text`.

3) contexts 정규화

- 빈/노이즈 context 삭제
- 중복 contexts 제거(설정에 따라)
- 너무 긴 context는 자르기
- contexts 개수 제한

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessor._normalize_contexts`.

### 11.2 ground_truth를 언제 어떻게 보정하나

중요: EvalVault는 "항상" ground_truth가 필요하다고 가정하지 않는다.
하지만 일부 메트릭은 reference(ground_truth)가 필요하다.

reference가 필요한 메트릭 집합:

- `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#REFERENCE_REQUIRED_METRICS`.

이 메트릭들이 선택된 경우, ground_truth가 비어 있으면 보정(채우기)을 시도할 수 있다.

- answer에서 채우기: `fill_reference_from_answer`
- contexts에서 채우기: `fill_reference_from_context`

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessConfig`.

주의:

- 이 보정은 "ground_truth가 없는 상태에서 평가가 완전히 불가능해지는 것"을 줄이는 안전장치다.
- 하지만 ground_truth 기반 메트릭을 gate로 쓰는 팀이라면,
  보정에 기대기보다 ground_truth를 명시적으로 관리하는 게 회귀/품질 측면에서 안전하다.

### 11.3 전처리 리포트는 무엇을 말해주나

전처리 결과는 요약 카운터로 남는다.

- dropped_cases, empty_questions, empty_contexts
- contexts_removed/deduped/truncated/limited
- references_missing/short/filled/truncated

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessReport`.

실무 해석 가이드(권장):

- dropped_cases가 생겼다: 비교/회귀에서 표본이 달라질 수 있다(같은 dataset이라도 결과가 바뀜).
- references_filled_from_answer가 크다: reference 기반 메트릭의 의미가 약해질 수 있다.
- contexts_deduped가 크다: 상위 k가 중복되어 "실질적인 근거 다양성"이 부족했을 수 있다.

---

## 12. CSV/Excel 파싱 디테일: contexts/metadata/thresholds

이 절은 "스프레드시트 입력"을 운영하는 팀이 반드시 알아야 하는 규칙을 설명한다.
스프레드시트는 편집은 쉽지만, 암묵적 규칙이 없으면 평가가 불안정해진다.

### 12.1 contexts 셀 포맷: JSON 배열 vs 파이프(|) 구분자

CSV/Excel 로더는 contexts를 문자열로 읽고 리스트로 바꾼다.

지원 포맷:

- JSON 배열: `["ctx1", "ctx2"]`
- 파이프 구분자: `ctx1|ctx2|ctx3`

- 근거: `src/evalvault/adapters/outbound/dataset/base.py#BaseDatasetLoader._parse_contexts`.

실무 규칙(권장):

- 팀에서 contexts 포맷을 하나로 고정한다.
- JSON 배열을 쓴다면, 문자열 안의 따옴표/이스케이프가 깨지지 않게 주의한다.
- 파이프 구분자를 쓴다면, context 본문 안에 | 문자가 등장하지 않도록 주의한다.

### 12.2 metadata 셀 포맷: JSON object만 허용

CSV/Excel에서 metadata를 넣고 싶다면, 셀에 JSON object 문자열을 넣을 수 있다.

- 근거: `src/evalvault/adapters/outbound/dataset/base.py#BaseDatasetLoader._parse_metadata_cell`.

규칙:

- 유효한 JSON이어야 한다
- root는 object여야 한다(list/primitive는 불가)

이 규칙이 중요한 이유:

- metadata가 object여야만 나중에 UI/리포트에서 키 기반 필터링/그룹핑이 가능하다.
- "문자열 하나"로 때우면 일관된 분석이 어려워진다.

### 12.3 summary_tags / summary_intent: 스프레드시트 친화적 확장

CSV/Excel 로더는 `summary_tags`, `summary_intent` 컬럼을 별도로 읽어 metadata에 병합할 수 있다.

- 근거: `src/evalvault/adapters/outbound/dataset/csv_loader.py`, `src/evalvault/adapters/outbound/dataset/excel_loader.py`.

summary_tags 파싱 규칙:

- list 그대로도 가능
- JSON 배열 문자열도 가능
- 콤마(,) 또는 파이프(|)가 들어 있으면 분리
- 모두 소문자로 정규화

- 근거: `src/evalvault/adapters/outbound/dataset/base.py#BaseDatasetLoader._parse_summary_tags_cell`.

### 12.4 dataset thresholds: threshold_* 컬럼에서 추출

스프레드시트 기반 thresholds는 컬럼 이름이 사실상 계약이다.

- 근거: `src/evalvault/adapters/outbound/dataset/thresholds.py#THRESHOLD_COLUMN_MAP`.

실무 규칙(권장):

- threshold 컬럼은 "파일 헤더"에 고정하고, 값은 첫 50행 중 어딘가(보통 첫 행)에만 채운다.
- 여러 행에 서로 다른 값이 섞이면, 무엇이 선택될지 사람이 직관적으로 알기 어렵다.
  (추출 로직은 메트릭별로 첫 non-empty 값을 채우는 방식이다.)

- 근거: `src/evalvault/adapters/outbound/dataset/thresholds.py#extract_thresholds_from_rows`.

### 12.5 CSV 인코딩: 실패 모드가 치명적이어서 방어 로직이 존재한다

CSV는 운영 환경에서 "인코딩"이 가장 자주 깨진다.
EvalVault는 BOM/UTF-8 뿐 아니라 CP949/EUC-KR도 시도한다.

- 근거: `src/evalvault/adapters/outbound/dataset/csv_loader.py#ENCODING_FALLBACKS`.

실무 팁:

- 한 번 깨진 CSV는 사람이 눈으로 봐도 "그럴듯"하게 보이는 경우가 많다.
- 따라서 팀 표준은 UTF-8로 고정하고, PR에서 인코딩이 바뀐 파일이 들어오면 즉시 의심한다.

---

## 13. 컨텍스트가 없을 때: retriever로 채우기(메타데이터 포함)

RAG 평가에서 contexts는 근거다.
그런데 실제 운영에서는 "질문/답"만 있고 contexts가 없는 로그 기반 데이터가 자주 등장한다.
EvalVault는 retriever 포트로 contexts를 채울 수 있다.

근거:

- 구현: `src/evalvault/domain/services/retriever_context.py#apply_retriever_to_dataset`.

### 13.1 동작 요약

- dataset의 각 test_case에 대해 contexts가 비어 있으면 retriever.search(question)를 호출
- 결과에서 document/content를 추출해 contexts에 추가
- retrieval 메타데이터를 run.retrieval_metadata에 남김

- 근거: `src/evalvault/domain/services/evaluator.py`에서 `apply_retriever_to_dataset` 호출.

### 13.2 retrieval_metadata에 무엇이 남나

test_case_id별로 다음이 저장될 수 있다.

- doc_ids: 결과별 문서 ID(또는 doc_1 같은 fallback)
- top_k
- retrieval_time_ms
- scores(모든 결과가 score를 제공할 때만)
- graph_nodes/graph_edges/subgraph_size/community_id(그래프 관련 metadata가 있을 때만)

- 근거: `src/evalvault/domain/services/retriever_context.py`.

여기서 중요한 점:

- contexts는 "그냥 텍스트"로 채워지기 때문에, 이 단계에서는 품질 보증이 없다.
- 그래서 retriever를 붙인 평가에서는 retrieval_metadata를 반드시 함께 보고,
  contexts가 정말 근거로서 적절한지 확인해야 한다.

### 13.3 doc_ids 매핑: retriever가 숫자 인덱스를 반환하는 경우

RetrieverResultProtocol의 doc_id가 int인 경우, doc_ids 배열로 매핑될 수 있다.
그렇지 않으면 raw doc_id를 문자열로 쓰고, 없으면 doc_{rank}로 만든다.

- 근거: `src/evalvault/domain/services/retriever_context.py#_resolve_doc_id`.

---

## 14. 메트릭 카탈로그(상세): 의미/입력/실패 모드/해석

이 절은 "메트릭 이름"을 보고 데이터 요구사항/해석/실패 모드를 즉시 떠올릴 수 있게 만드는 것을 목표로 한다.
메트릭의 최종 진실은 레지스트리와 구현이다.

- 메트릭 레지스트리(요구사항): `src/evalvault/domain/metrics/registry.py`.
- 일부 커스텀 메트릭 구현: `src/evalvault/domain/metrics/`.

### 14.1 한 장 표: MetricSpec으로 보는 입력 요구

아래 표는 레지스트리의 MetricSpec을 사람이 읽기 쉽게 요약한 것이다.

- 근거: `src/evalvault/domain/metrics/registry.py#MetricSpec` + `_METRIC_SPECS`.

표를 읽는 법:

- requires_ground_truth=True면 test_case.ground_truth가 사실상 필수다.
- requires_embeddings=True면 embedding 설정이 필요하고, 실행 비용/시간이 증가할 수 있다.

| metric | category | source | requires_ground_truth | requires_embeddings | signal_group |
| --- | --- | --- | --- | --- | --- |
| faithfulness | qa | ragas | False | False | groundedness |
| answer_relevancy | qa | ragas | False | True | intent_alignment |
| context_precision | qa | ragas | True | False | retrieval_effectiveness |
| context_recall | qa | ragas | True | False | retrieval_effectiveness |
| factual_correctness | qa | ragas | True | False | groundedness |
| semantic_similarity | qa | ragas | True | True | intent_alignment |
| mrr | retrieval | custom | True | False | retrieval_effectiveness |
| ndcg | retrieval | custom | True | False | retrieval_effectiveness |
| hit_rate | retrieval | custom | True | False | retrieval_effectiveness |
| summary_score | summary | ragas | False | False | summary_fidelity |
| summary_faithfulness | summary | ragas | False | False | summary_fidelity |
| turn_faithfulness | qa | custom | False | False | groundedness |
| context_coherence | qa | custom | False | False | intent_alignment |
| drift_rate | qa | custom | False | False | intent_alignment |
| turn_latency | qa | custom | False | False | efficiency |
| entity_preservation | summary | custom | False | False | summary_fidelity |
| summary_accuracy | summary | custom | False | False | summary_fidelity |
| summary_risk_coverage | summary | custom | False | False | summary_fidelity |
| summary_non_definitive | summary | custom | False | False | summary_fidelity |
| summary_needs_followup | summary | custom | False | False | summary_fidelity |
| insurance_term_accuracy | domain | custom | False | False | groundedness |
| contextual_relevancy | qa | custom | False | False | retrieval_effectiveness |

주의:

- 표는 코드 기준으로 작성됐으며, 레지스트리 변경 시 최신화가 필요하다.
- 실제 실행은 evaluator의 METRIC_MAP/CUSTOM_METRIC_MAP에 의해 결정된다.
  - 근거: `src/evalvault/domain/services/evaluator.py#RagasEvaluator.METRIC_MAP`, `CUSTOM_METRIC_MAP`.

### 14.2 QA 계열(groundedness/intent_alignment)

#### 14.2.1 faithfulness

의미:

- 답변이 contexts에 의해 뒷받침되는지(근거 충실도)

입력:

- contexts가 사실상 필수(비어 있으면 의미가 약해짐)

실패 모드:

- contexts가 노이즈거나 질문과 무관하면, 낮은 점수가 "모델 문제"가 아니라 "검색/데이터 문제"일 수 있다.

#### 14.2.2 answer_relevancy

의미:

- 답이 질문 의도에 맞는지

특이점:

- embeddings가 필요할 수 있다(requires_embeddings=True)
  - 근거: `src/evalvault/domain/metrics/registry.py`.
- 한국어 데이터에서 프롬프트 언어 불일치 문제가 생길 수 있어, evaluator에 한국어 지시문/예시가 포함돼 있다.
  - 근거: `src/evalvault/domain/services/evaluator.py`의 ANSWER_RELEVANCY_KOREAN_* 상수.

#### 14.2.3 factual_correctness / semantic_similarity

의미:

- ground_truth 기준으로 답의 사실성/유사도를 본다.

실무 주의:

- ground_truth 품질이 낮으면, 모델을 "정답에 맞추는" 방향으로 잘못 최적화할 수 있다.
- 따라서 ground_truth 기반 메트릭을 gate로 쓰려면, ground_truth 생성/리뷰 프로세스가 필요하다.

### 14.3 Retrieval 계열(custom): MRR/NDCG/HitRate

이 레포의 retrieval 커스텀 메트릭은 "문서 ID"가 아니라 "ground_truth 텍스트"를 기준으로 contexts의 관련성을 계산한다.

- 근거: `src/evalvault/domain/metrics/retrieval_rank.py`의 `_calculate_relevance(context, ground_truth)`.

즉, 요구사항은 다음과 같이 다시 읽어야 한다.

- contexts: 검색 결과 텍스트 리스트(순서가 중요)
- ground_truth: 정답/기대 답 텍스트(컨텍스트가 포함해야 할 핵심 토큰의 근거)

#### 14.3.1 MRR

- 첫 번째 "관련" context가 몇 번째에 등장하는지를 본다.
- 기본 관련성 임계값은 0.3이다.

- 근거: `src/evalvault/domain/metrics/retrieval_rank.py#MRR`.

실패 모드:

- ground_truth가 짧거나 추상적이면, 토큰 overlap 기반 관련성 판단이 흔들린다.
- contexts에 정답 토큰이 있지만 형태가 크게 다르면, 관련성 점수가 낮을 수 있다.

#### 14.3.2 NDCG/HitRate

- 구현/정의는 동일 파일에 있다.
- 어떤 기준으로 "관련"을 정의하는지는 `_calculate_relevance`와 threshold에 의존한다.

- 근거: `src/evalvault/domain/metrics/retrieval_rank.py`.

실무 팁:

- retrieval 메트릭은 "컨텍스트 생성/정규화"가 흔들리면 바로 신뢰도가 떨어진다.
- 따라서 retriever로 contexts를 채우는 경우(13장), retrieval_metadata까지 함께 저장/검토하는 것이 중요하다.

### 14.4 Summary 계열: summary_score / summary_faithfulness + 커스텀 규칙 메트릭

요약 태스크는 QA와 실패 모드가 다르다.

- QA: 질문 의도에 맞는 답을 했는가
- Summary: 컨텍스트의 핵심을 놓치지 않고(coverage) 왜곡 없이(faithfulness) 정리했는가

#### 14.4.1 summary_score / summary_faithfulness

- 레지스트리: `src/evalvault/domain/metrics/registry.py`.

임계값 기본값(도메인 레벨):

- summary_score: 0.85
- summary_faithfulness: 0.9

- 근거: `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

#### 14.4.2 insurance_term_accuracy

보험 도메인 특화 규칙 기반 메트릭.

- 답변에 등장한 보험 용어가 contexts에서 확인되는지 계산한다.
- 답변에 용어가 없으면 1.0, contexts가 비어 있으면 0.0을 반환한다.

- 근거: `src/evalvault/domain/metrics/insurance.py#InsuranceTermAccuracy`.

이 메트릭을 해석할 때의 포인트:

- 1.0이 항상 "좋다"는 의미가 아니다(답변이 지나치게 단순/회피적이라 용어가 없을 수도 있음).
- contexts 품질이 나쁘면 0.0이 "모델 환각"이 아니라 "검색 실패"일 수 있다.

#### 14.4.3 contextual_relevancy

의미:

- question과 contexts의 정합성을 본다("contexts vs question")
- ground_truth가 없어도 동작하도록 설계된 reference-free 메트릭이다.

- 근거: `src/evalvault/domain/metrics/contextual_relevancy.py`.

기본 threshold(도메인 레벨):

- contextual_relevancy: 0.35

- 근거: `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

---

## 15. 임계값(Threshold) 운영 플레이북: 기본값/프로필/오버라이드/실수 방지

임계값은 "성공" 정의다.
임계값이 흔들리면, 평가의 의미가 흔들리고, 회귀 게이트가 무력해진다.

### 15.1 임계값의 3계층: default / dataset / run

1) default thresholds

- DEFAULT_THRESHOLD_FALLBACK = 0.7
- 일부 메트릭은 더 엄격한 기본값을 가진다(summary_* 등)

- 근거: `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

2) dataset thresholds

- JSON: thresholds object
- CSV/Excel: threshold_* columns

- 근거: `src/evalvault/adapters/outbound/dataset/json_loader.py`, `src/evalvault/adapters/outbound/dataset/thresholds.py`.

3) run thresholds(실제로 사용된 값)

- evaluator가 resolve한 thresholds가 `EvaluationRun.thresholds`로 저장된다.

- 근거: `src/evalvault/domain/services/evaluator.py`에서 EvaluationRun 생성 시 thresholds=resolved_thresholds.

실무에서 중요한 규칙:

- "재현"은 항상 run.thresholds를 기준으로 해야 한다.
- dataset.thresholds만 보고 "이게 기준"이라고 말하면, profile/override가 있었을 때 틀린 결론이 된다.

### 15.2 threshold profile은 "정책 프리셋"이다

threshold profile은 목적별 추천 임계값 묶음이다.

- 근거: `src/evalvault/domain/services/threshold_profiles.py#THRESHOLD_PROFILES`.

현재 제공되는 프로필(코드 기준):

- qa
- summary

프로필 적용 규칙:

- metrics 목록에 포함된 항목만 덮어쓴다.
- unknown profile이면 오류

- 근거: `src/evalvault/domain/services/threshold_profiles.py#apply_threshold_profile`.

중요한 설계 포인트:

- 도메인 평가 서비스는 profile을 직접 적용하지 않는다.
- profile은 inbound 레이어(CLI/Web)에서 thresholds를 계산해 넘기는 방식으로 적용된다.
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_resolve_thresholds`, `src/evalvault/adapters/inbound/api/adapter.py`.

### 15.3 API adapter에서의 해석: "요청 thresholds"와 "profile"이 있을 때만 resolve

Web API에서는 request.thresholds 또는 request.threshold_profile이 있을 때만,
dataset thresholds와 결합하여 resolved_thresholds를 만든다.

- 근거: `src/evalvault/adapters/inbound/api/adapter.py`의 threshold resolution 블록.

실무 해석:

- Web UI/API에서 "threshold를 안 건드리면" evaluator가 dataset/default로 처리한다.
- 반대로 "threshold를 조금이라도 건드리면" request/dataset/profile 결합이 발동된다.

### 15.4 실수 방지 규칙(권장)

아래는 팀에서 기준을 고정할 때 유용한 규칙이다.

1) "gate로 쓰는 메트릭"은 반드시 threshold의 소유자를 정한다.

- dataset 소유(데이터셋이 기준): dataset file 변경으로만 바뀐다.
- profile 소유(환경/목적이 기준): profile 변경으로 바뀐다.

2) thresholds를 변경하는 PR에는 반드시 다음을 포함한다.

- 왜 바꿨는지(운영/품질 목표)
- 어떤 실패 모드를 더 엄격히 잡으려는지
- 어떤 데이터셋/태스크에 영향이 있는지

3) "하나의 숫자"로 팀을 속이지 말기

- pass_rate가 올라갔다고 해서 좋아졌다고 결론내리면 안 된다.
- 어떤 메트릭이 올랐는지, 어떤 케이스가 통과했는지, contexts 품질이 어떤지까지 함께 봐야 한다.

---

## 16. 산출물/아티팩트 심화: index.json, lint, MCP로 조회

02장의 앞부분에서 아티팩트/index.json의 기본 개념을 설명했다.
여기서는 "운영에서 실제로 쓸 수 있게" 구체적인 도구/계약을 정리한다.

### 16.1 pipeline artifacts 작성: per-node JSON + index.json

파이프라인 아티팩트는 노드별로 JSON을 쓰고, index.json에 목차를 만든다.

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

특징:

- node_id를 파일명으로 쓰기 위해 sanitize한다.
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#_safe_artifact_name`.
- final_output이 있으면 final_output.json을 쓴다.

### 16.2 artifacts lint: index.json과 파일 존재성 검증

ArtifactLintService는 index.json의 최소 스키마와 파일 존재성을 점검한다.

- 근거: `src/evalvault/domain/services/artifact_lint_service.py#ArtifactLintService`.

CLI로 실행할 수 있다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`.

```bash
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID>
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID> --strict
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID> --output reports/analysis/artifacts/analysis_<RUN_ID>/lint.json
```

주의:

- strict 모드에서는 "파일이 없으면" error로 처리한다.
- CI에서 아티팩트 무결성을 보장하고 싶다면 strict를 고려할 수 있다.

### 16.3 MCP에서 artifacts 경로를 조회하기(get_artifacts)

EvalVault는 MCP 도구에서 아티팩트 경로를 조회하는 기능을 제공한다.

- 근거: `src/evalvault/adapters/inbound/mcp/tools.py#get_artifacts`.

조회되는 경로:

- report_path
- output_path
- artifacts_dir
- artifacts_index_path

특징(보안/안전):

- base_dir는 기본적으로 `reports/analysis` 또는 `reports/comparison`으로 해석된다.
- 허용 루트 밖 경로는 접근할 수 없다.
  - 허용 루트: data/, tests/fixtures/, reports/
  - 근거: `src/evalvault/adapters/inbound/mcp/tools.py#_ensure_allowed_path` + `_allowed_roots`.

이 규칙의 의미:

- UI/자동화가 임의 파일을 읽는 보안 사고를 막기 위한 최소 안전장치다.
- 운영 환경에서 MCP를 켤 때는 "어떤 파일이 외부로 노출될 수 있는지"를 이 기준으로 역추적해야 한다.

---

## 17. 실전 레시피: QA/요약/검색 태스크별 데이터 설계

이 절은 "추상 설명"이 아니라 "만드는 방법"을 제공한다.
다만 없는 기능/거짓 정보는 넣지 않는다. 아래 레시피는 레포의 데이터 모델과 로더 규칙만 사용한다.

### 17.1 QA 평가 데이터셋 레시피(기본)

목표:

- 질문-답-근거 컨텍스트를 평가하고, faithfulness/answer_relevancy로 최소 게이트를 만든다.

필수 필드:

- id, question, answer, contexts

권장 필드:

- metadata: domain/language/tags
- thresholds: 최소한 gate 메트릭에 대해서는 명시

템플릿:

- JSON: `docs/templates/dataset_template.json`
- CSV/Excel: `docs/templates/dataset_template.csv`, `docs/templates/dataset_template.xlsx`

실무 체크:

- contexts는 빈 리스트라도 "형식상" 가능하지만, faithfulness의 의미가 약해진다.
- answer는 모델 출력인지, baseline 출력인지(비교 목적) 명확히 해야 한다.

### 17.2 요약 평가 데이터셋 레시피

요약 태스크는 question이 "지시문"이 될 수 있다.
EvalVault의 데이터 모델은 question/answer/contexts를 기본으로 하므로,
요약에서는 question을 "요약 요청"으로, answer를 "요약 결과"로 넣는 방식이 된다.

권장:

- metadata에 summary_intent/summary_tags를 넣어, 분석에서 그룹핑 가능하게 만든다.
  - CSV/Excel에서는 summary_tags/summary_intent 컬럼을 사용할 수 있다.
    - 근거: `src/evalvault/adapters/outbound/dataset/csv_loader.py`, `src/evalvault/adapters/outbound/dataset/excel_loader.py`.

임계값 기본값 참고:

- summary_score 0.85
- summary_faithfulness 0.9

- 근거: `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

### 17.3 Retrieval 평가 데이터셋 레시피(텍스트 기반)

이 레포의 MRR/NDCG/HitRate 구현은 contexts(순서 포함)와 ground_truth 텍스트를 사용한다.

- 근거: `src/evalvault/domain/metrics/retrieval_rank.py`.

따라서 retrieval 평가용 데이터셋에서 중요한 것은 "정답 문서 ID"가 아니라
"ground_truth에 담긴 핵심 토큰이 contexts에 얼마나 빨리/많이 등장하는가"다.

레시피:

- contexts: retriever의 top-k 문서 텍스트(또는 문서 요약)
- ground_truth: 기대 답(핵심 토큰을 포함)
- thresholds: 필요하면 dataset 또는 profile로 고정

주의:

- 토큰 overlap 기반이므로, 표현이 크게 바뀌면 점수가 낮아질 수 있다.
- 한국어에서는 조사/어미 처리(스트리핑)가 들어가지만, 완전한 형태소 분석은 아니다.
  - 근거: `src/evalvault/domain/metrics/retrieval_rank.py#_strip_korean_endings`.

### 17.4 "컨텍스트가 없다" 레시피: retriever로 채우고, 메타데이터를 같이 저장

contexts가 비어 있는 로그 기반 데이터라면, retriever로 contexts를 채울 수 있다.

- 근거: `src/evalvault/domain/services/retriever_context.py#apply_retriever_to_dataset`.

하지만 이 경우 평가 결과의 해석은 반드시 retrieval_metadata와 함께 해야 한다.

- retrieval_time_ms가 튀는가?
- scores가 비어 있는가(스코어 제공이 일관되는가)?
- doc_ids가 안정적인가?

---

## 18. 부록: 자주 쓰는 명령/템플릿/자가 점검(확장)

### 18.1 템플릿 생성/다운로드 관점

레포에는 템플릿 파일이 있고, 코드로도 템플릿 payload를 만든다.

- 템플릿 파일: `docs/templates/dataset_template.json`, `docs/templates/dataset_template.csv`, `docs/templates/dataset_template.xlsx`
- 코드 템플릿 빌더: `src/evalvault/adapters/outbound/dataset/templates.py`

이 파일은 "데이터셋 설계의 기준"으로 쓰기 좋다.
특히 CSV/Excel 헤더(threshold_* 포함)를 표준화하는 데 유용하다.

### 18.2 artifacts lint 명령(운영 기본기)

```bash
uv run evalvault artifacts lint <ARTIFACTS_DIR>
uv run evalvault artifacts lint <ARTIFACTS_DIR> --strict
```

### 18.3 데이터 품질 자가 점검 질문(확장)

1) 이 데이터셋은 "모델"을 평가하는가, "검색"을 평가하는가, "둘 다"인가?
2) contexts가 정말 근거인가? 아니면 단순히 관련 텍스트 모음인가?
3) ground_truth를 gate로 쓸 만큼 신뢰할 수 있는가(작성/검증 프로세스가 있는가)?
4) thresholds의 소유자는 누구인가(dataset vs profile vs run override)?
5) 전처리로 dropped_cases가 생겼을 때, 비교/회귀의 표본 일관성이 깨지지 않는가?

---

## 19. 평가 실행의 데이터 플로우: Dataset -> Run -> Score -> Gate

이 절은 "데이터가 어디서 변형되는지"를 추적한다.
데이터/메트릭에서 가장 위험한 버그는 계산 자체가 아니라 "데이터 의미가 슬쩍 바뀌는 것"이다.

### 19.1 Dataset 입력은 결국 TestCase.to_ragas_dict로 요약된다

`TestCase`는 Ragas 입력으로 변환되는 매핑을 가진다.

- question -> user_input
- answer -> response
- contexts -> retrieved_contexts
- ground_truth(optional) -> reference

- 근거: `src/evalvault/domain/entities/dataset.py#TestCase.to_ragas_dict`.

이 매핑이 중요한 이유:

- 데이터셋을 무엇으로 작성하든(JSON/CSV/Excel), 결국 이 네 가지 슬롯으로 들어간다.
- 즉, "문서 ID"나 "리트리브 로그" 같은 구조화된 데이터는 기본 데이터 모델에 직접 들어가지 않는다.
  그런 데이터는 metadata로 들어가거나, 별도 수집 경로(Stage/OTel 등)로 들어가는 쪽이 자연스럽다.

### 19.2 전처리로 데이터가 바뀔 수 있다(표본/텍스트/contexts)

평가 전에 DatasetPreprocessor가 적용되면:

- question/answer/ground_truth가 정규화(공백/placeholder 제거)
- contexts가 정규화(중복/길이/개수 제한)
- 빈 question 등을 가진 케이스는 drop될 수 있다

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py#DatasetPreprocessor.apply`.

따라서 "같은 파일"을 평가했는데 결과가 달라졌다면,
우선 전처리 리포트(kept/dropped, contexts_deduped 등)를 확인해야 한다.

### 19.3 thresholds는 evaluator에서 최종 resolve되어 Run에 저장된다

evaluator는 thresholds를 다음 순서로 resolve하고, 결과를 `EvaluationRun.thresholds`에 저장한다.

1) 입력 thresholds(dict)
2) dataset.thresholds
3) default_threshold_for(metric)

- 근거: `src/evalvault/domain/services/evaluator.py#RagasEvaluator.evaluate`.

즉 "진짜 기준"은 run.thresholds다.
dataset.thresholds는 원천값일 뿐이다.

### 19.4 MetricScore.threshold와 TestCaseResult.all_passed

각 test case 결과는 metric별 MetricScore를 갖고, MetricScore는 threshold를 포함한다.
`TestCaseResult.all_passed`는 모든 MetricScore.passed가 True인지로 정의된다.

- 근거: `src/evalvault/domain/entities/result.py#TestCaseResult.all_passed`.

이 정의가 gate에 미치는 영향:

- 메트릭을 1개 더 추가하면 pass_rate가 떨어질 가능성이 매우 높다.
  (새 메트릭이 "통과" 조건을 하나 더 추가하기 때문)

### 19.5 pass_rate(케이스 기준) vs metric_pass_rate(메트릭 평균 기준)

`EvaluationRun.pass_rate`:

- 모든 메트릭을 통과한 test case 비율

`EvaluationRun.metric_pass_rate`:

- 메트릭 평균 점수가 threshold를 넘는 메트릭 비율

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.pass_rate`, `metric_pass_rate`.

실무 해석:

- gate/회귀는 대체로 pass_rate(케이스 기준)을 보는 게 직관적이다.
- "어느 축이 무너졌나"를 빠르게 보려면 metric_pass_rate가 도움이 될 수 있다.

---

## 20. 메트릭별 디버깅 플레이북(상세)

이 절은 "점수만 보고 추측하지 않기"를 목표로 한다.
메트릭은 실패 모드가 다르고, 각 실패 모드에 맞는 디버깅 순서가 있다.

### 20.1 공통 진단 순서(모든 메트릭 공통)

1) 입력이 비어 있지 않은가?

- question/answer/contexts/ground_truth(필요한 경우)

2) 전처리로 무엇이 바뀌었나?

- dropped_cases, contexts_removed/deduped/truncated

3) thresholds가 무엇이었나?

- run.thresholds가 진실

4) 이 점수는 "모델"을 말하나 "검색"을 말하나?

- faithfulness 낮음: 모델 환각일 수도, contexts가 나쁠 수도
- contextual_relevancy 낮음: 검색/데이터 문제일 가능성이 큼

### 20.2 faithfulness가 낮을 때

먼저 확인:

- contexts가 질문과 관련이 있나?
- contexts가 너무 길거나 중복되어 judge가 흔들릴 만한가?

근거가 되는 입력:

- contexts는 "근거"다. 근거가 나쁘면 faithfulness는 모델을 벌주지 못한다.

실전 수정 레버:

- 데이터셋: contexts 품질 개선(정확한 근거, 중복 제거)
- retriever: top_k 조정/문서 정규화/필터링
- 메트릭: faithfulness를 gate로 쓰는 경우, contexts 품질 기준을 별도로 두는 것이 현실적이다

### 20.3 answer_relevancy가 낮을 때

answer_relevancy는 질문-답 정합성이다.
실패 모드는 크게 두 가지로 나뉜다.

1) 모델이 질문을 회피/모호하게 답함
2) 모델은 명확히 답했는데, 메트릭이 그걸 인식하지 못함

이 레포에는 한국어 데이터에서 언어 정렬을 돕는 지시문/예시가 포함돼 있다.

- 근거: `src/evalvault/domain/services/evaluator.py`의 ANSWER_RELEVANCY_KOREAN_*.

실전 수정 레버:

- 데이터셋: question을 더 구체화(의도/조건 포함)
- 프롬프트: 시스템 프롬프트를 조정해 "회피"를 줄임

### 20.4 factual_correctness/semantic_similarity가 낮을 때

가장 흔한 원인:

- ground_truth가 부정확/불완전/모호함
- ground_truth와 answer의 표현 차이가 커서 유사도가 낮게 나옴

이 메트릭들은 requires_ground_truth=True다.

- 근거: `src/evalvault/domain/metrics/registry.py`.

실전 수정 레버:

- ground_truth를 "단일 정답"으로 유지할 수 없는 태스크라면, 이 메트릭을 gate로 쓰지 않는다.
- 쓰더라도, ground_truth 생성/리뷰/버전 관리 프로세스가 필요하다.

### 20.5 retrieval 메트릭(MRR/NDCG/HitRate)이 낮을 때

먼저 확인:

- contexts 순서가 진짜 retrieval 순서인가?
- ground_truth가 핵심 토큰을 충분히 포함하는가?

이 레포의 구현은 token overlap 기반이다.

- 근거: `src/evalvault/domain/metrics/retrieval_rank.py`의 `_tokenize`, `_calculate_relevance`.

실전 수정 레버:

- contexts: 문서 텍스트가 너무 길면 핵심 토큰이 묻힐 수 있다(필요 시 문서 요약/정규화).
- ground_truth: 핵심 토큰을 포함하도록 정리(단, 거짓 정보를 넣지 말 것)

### 20.6 insurance_term_accuracy가 낮을 때

가능한 원인:

- answer에 도메인 용어가 많고, contexts에 해당 용어가 없거나 다른 표현으로만 있음
- contexts가 비어 있음(이 경우 0.0)

- 근거: `src/evalvault/domain/metrics/insurance.py#InsuranceTermAccuracy`.

실전 수정 레버:

- 데이터셋: contexts를 "약관 근거"로 정제
- 모델 출력: 불필요한 용어 나열을 줄이도록 프롬프트/가이드 조정

### 20.7 contextual_relevancy가 낮을 때

contextual_relevancy는 question-context 정합성이다.
즉, 검색 품질 또는 데이터 구축 품질의 신호로 보는 게 합리적이다.

- 근거: `src/evalvault/domain/metrics/contextual_relevancy.py`.

실전 수정 레버:

- retriever 설정/문서 인덱싱 품질
- 질문 전처리(불필요한 토큰 제거)

---

## 21. 토큰/비용/지연시간: 무엇을 믿고 무엇을 의심할까

EvalVault는 가능하면 "비용"과 "시간"을 결과에 같이 남기려 한다.
하지만 이 값들은 어댑터/환경에 따라 가용성이 달라질 수 있다.

### 21.1 Run에 저장되는 리소스 필드

- total_tokens
- total_cost_usd(계산 가능할 때)

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun`.

### 21.2 LLMPort는 토큰 사용량 인터페이스를 가진다(선택 구현)

LLMPort는 토큰 사용량 관련 메서드를 정의하지만, 기본 구현은 NotImplementedError다.

- get_token_usage / get_and_reset_token_usage / reset_token_usage

- 근거: `src/evalvault/ports/outbound/llm_port.py#LLMPort`.

실무 의미:

- "토큰/비용"을 운영 지표로 쓰려면, 사용하는 LLM 어댑터가 이 메서드를 구현하는지 확인해야 한다.

### 21.3 evaluator의 MODEL_PRICING: 코드에 포함된 추정치라는 점을 명시

evaluator에는 모델별 토큰 단가 추정 테이블이 존재한다.

- 근거: `src/evalvault/domain/services/evaluator.py#MODEL_PRICING`.

주의:

- 주석에 "Estimated pricing"라고 되어 있고, 일부 항목은 가상의 모델로 표시돼 있다.
- 따라서 이 값은 제품 외부의 공식 가격표로 간주하면 안 된다.
  (운영에서는 최신 가격 정책/계약을 별도로 관리해야 한다.)

### 21.4 latency는 어디서 오나

TestCaseResult는 latency_ms를 가진다.

- 근거: `src/evalvault/domain/entities/result.py#TestCaseResult.latency_ms`.

실무 해석:

- latency가 길어졌을 때, 모델/네트워크/배치 크기/리트리버 여부 등 변수가 많다.
- 따라서 성능 회귀를 다룰 때는 "실행 설정 스냅샷"과 함께 봐야 한다.

---

## 22. 재현성 설계: run_id, dataset_version, tracker_metadata

데이터/메트릭의 목적은 "개선"이 아니라 "재현 가능한 개선"이다.
재현이 안 되면, 팀은 결국 감으로 의사결정하게 된다.

### 22.1 run_id는 모든 산출물의 조인 키다

EvaluationRun은 run_id를 가진다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.run_id`.

실무 의미:

- 리포트/아티팩트/트레이싱/엑셀 내보내기 등은 run_id를 중심으로 묶인다.

### 22.2 dataset_name/dataset_version은 "데이터의 정체"를 고정한다

Dataset은 name/version을 가진다.

- 근거: `src/evalvault/domain/entities/dataset.py#Dataset`.

실무 규칙(권장):

- dataset 파일 경로가 아니라 name/version을 기준으로 변경을 추적한다.
- 버전은 사람이 의미 있게 올린다(데이터 분포/스키마/임계값 변경 등).

### 22.3 tracker_metadata는 "설정/스냅샷"을 저장하는 장소다

evaluator는 실행 중 다양한 메타데이터를 tracker_metadata에 남길 수 있다.

- dataset_preprocess 요약
- ragas_config
- ragas_prompt_overrides / prompt_snapshots
- custom_metric_snapshot

- 근거: `src/evalvault/domain/services/evaluator.py` 내 tracker_metadata 할당.

실무 의미:

- 동일한 run_id라도, 메타데이터가 없다면 "왜 점수가 달라졌는지"를 설명할 수 없다.
- 그래서 운영에서는 메트릭 점수뿐 아니라, 어떤 설정으로 실행했는지를 같이 저장하는 게 중요하다.

### 22.4 thresholds는 요약 딕셔너리로도 노출된다

EvaluationRun.to_summary_dict는 thresholds를 포함해 요약을 만든다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.to_summary_dict`.

---

## 23. 고급(짧게): Stage Events/Stage Metrics는 무엇이고 어디에 두나

EvalVault에는 "데이터셋 기반 평가" 외에도, 실행 파이프라인의 stage 이벤트를 수집/요약하는 경로가 있다.
이는 데이터 모델/메트릭 선택과 관련은 있지만, 운영(runbook) 성격이 강하다.

- Stage CLI: `src/evalvault/adapters/inbound/cli/commands/stage.py`

02장에서는 다음만 기억하면 충분하다.

- Stage 이벤트는 별도 데이터 소스다(데이터셋의 TestCase 모델로는 표현되지 않는 실행 로그).
- threshold JSON/프로필 같은 개념이 별도로 존재할 수 있다.

상세 운영 절차(ingest/list/compute-metrics/guide)는 04장(Operations)에서 다룬다.

---

## 24. 데이터셋 제작 워크샵: "좋은 케이스"를 만드는 체크리스트

이 절은 실제로 데이터셋을 만들 때 가장 자주 겪는 난관(정의/경계/품질)을 해결하기 위한 워크샵이다.
핵심은 "케이스 하나"를 완성도 있게 만드는 방법을 반복하는 것이다.

### 24.1 케이스 하나를 설계하는 질문(가장 중요)

아래 질문에 답하지 못하면, 데이터셋은 결국 "이상한 숫자"를 만들고 끝난다.

1) 이 케이스는 어떤 실패를 잡으려는가?

- 환각(근거 없는 주장)
- 질문과 무관한 답
- 검색이 엉뚱한 문서를 줌
- 요약이 중요한 조건/예외를 누락함

2) 이 케이스에서 contexts는 "근거"인가 "힌트"인가?

- 근거라면: contexts에 답변을 정당화할 수 있는 문장을 포함해야 한다.
- 힌트라면: faithfulness 계열 해석은 조심해야 한다.

3) ground_truth는 "단일 정답"으로 고정 가능한가?

- 가능하면: factual_correctness/semantic_similarity를 고려할 수 있다.
- 어렵다면: ground_truth 기반 메트릭은 gate에서 제외하는 것이 안전할 수 있다.

### 24.2 TestCase.id를 설계하는 방법(재현성의 핵)

`id`는 단순한 식별자가 아니라, 모든 비교/집계/피드백의 조인 키다.

권장 규칙:

- 사람이 보고 이해 가능한 형태
- 데이터가 바뀌지 않는 한 id는 바뀌지 않음
- 케이스가 분해/병합될 때만 id가 바뀜

예시(패턴만):

- `ins_qa_0001`
- `policy_exclusion_001`
- `summ_eligibility_010`

주의:

- id를 "행 번호"에 의존하면(스프레드시트 정렬/필터), 비교/회귀가 쉽게 깨진다.

### 24.3 question 설계: 평가 가능한 입력으로 만들기

question은 단지 "문장"이 아니라, 평가의 기준축이다.

권장:

- 조건/제약을 포함해 의도를 명확히 한다.
- 여러 질문을 한 번에 묻지 않는다.
- 요약 태스크에서는 question이 "요약 지시문" 역할을 하도록 명확히 한다.

실무 팁:

- 모호한 질문은 answer_relevancy를 흔들고, 모델과 judge의 분산을 키운다.

### 24.4 contexts 설계: 길이/중복/정확성

contexts는 평가에서 가장 비싼 자원이다.

- 너무 짧으면 근거가 부족하다.
- 너무 길면 judge가 흔들리고 비용이 증가한다.
- 중복이 많으면 신호가 약해진다.

EvalVault는 중복/길이를 전처리에서 다룰 수 있다.

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py`.

하지만 전처리는 "마지막 방어"다.
좋은 데이터셋은 애초에 contexts를 깔끔하게 만든다.

### 24.5 ground_truth 설계: 가능한 경우에만 강하게

ground_truth가 필요한 메트릭을 선택했는데 ground_truth가 비면,
전처리에서 보정을 시도할 수 있다.

- 근거: `src/evalvault/domain/services/dataset_preprocessor.py`.

하지만 이 보정은 연구/운영에 따라 위험할 수 있다.

권장:

- ground_truth 기반 gate를 쓸 팀이라면, ground_truth는 사람이 리뷰 가능한 형태로 관리한다.
- ground_truth가 불안정하면, 그 메트릭은 "참고"로만 사용한다.

### 24.6 metadata 설계: 최소한의 분류 키부터 시작

metadata는 "나중에 분석할 때"를 위한 보험이다.

최소 권장 키:

- `domain`: 예: insurance
- `language`: 예: ko
- `tags`: 예: ["exclusion", "limit", "eligibility"]

요약 태스크라면:

- `summary_intent`
- `summary_tags`

스프레드시트에서는 summary_tags/summary_intent 컬럼을 사용할 수 있다.

- 근거: `src/evalvault/adapters/outbound/dataset/base.py#_parse_summary_tags_cell`, `_parse_summary_intent_cell`.

### 24.7 dataset.version을 올리는 기준(팀 규칙)

version은 단지 문자열이 아니라 "비교 가능한 기준"이다.

권장 규칙:

- thresholds가 바뀌면 version을 올린다(게이트 의미가 바뀜).
- 케이스가 추가/삭제되면 version을 올린다(표본이 바뀜).
- 질문/컨텍스트가 의미 있게 바뀌면 version을 올린다(실험 대상이 바뀜).

---

## 25. 메트릭 조합 패턴(권장): 목적별 최소/표준/심화 세트

이 절의 목표는 "메트릭을 많이 돌리기"가 아니라 "의미 있는 신호를 최소 비용으로 얻기"다.
아래는 레지스트리/입력 요구사항에 기반한 조합 패턴이다.

근거(가능 메트릭/요구사항): `src/evalvault/domain/metrics/registry.py`.

### 25.1 QA 태스크

최소 세트(빠른 회귀 감지):

- `faithfulness`
- `answer_relevancy`

이유:

- groundedness + intent_alignment 축을 최소로 커버

표준 세트(근거/정답을 갖춘 평가):

- 최소 세트 + `factual_correctness` 또는 `semantic_similarity`

주의:

- ground_truth 품질이 없으면 오히려 독이 될 수 있다.

### 25.2 요약 태스크

최소 세트:

- `summary_faithfulness`
- `summary_score`

표준 세트(도메인 규칙까지):

- 최소 세트 + `entity_preservation` + `summary_accuracy`

주의:

- 요약 태스크는 "누락"이 치명적일 수 있어 threshold를 엄격히 가져가게 된다.
  (기본값도 summary 계열이 더 높다.)
  - 근거: `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

### 25.3 Retrieval 태스크

최소 세트:

- `contextual_relevancy`

표준 세트(정답 텍스트 기반):

- `mrr` / `ndcg` / `hit_rate` 중 목적에 맞는 1~2개

주의:

- 이 레포 구현은 ground_truth 텍스트 토큰 overlap 기반이므로,
  retrieval을 "문서 정답" 기준으로 평가하고 싶다면 데이터 표현 자체를 다시 설계해야 한다.
  (그 경우 Stage/OTel 같은 다른 데이터 소스가 더 적합할 수 있다.)

---

## 26. Threshold 튜닝 워크플로: 안전하게 바꾸고, 의미 있게 비교하기

threshold는 제품의 "품질 정의"다.
그래서 threshold 튜닝은 사실상 제품 정책 변경이다.

### 26.1 바꾸기 전에 해야 하는 일(권장)

1) 왜 바꾸는지 문장으로 먼저 쓴다.

- "환각을 더 강하게 잡고 싶다" -> faithfulness threshold 강화
- "검색 품질이 들쭉날쭉하다" -> contextual_relevancy threshold 도입/강화

2) 어떤 리스크가 있는지 쓴다.

- false negative(좋은 답인데 탈락)
- 데이터 분포/contexts 품질에 대한 의존

3) 기준 데이터셋/버전을 명시한다.

- dataset_name + dataset_version

### 26.2 바꾸는 방식: dataset thresholds vs profile

팀의 현실에 따라 선택한다.

- dataset thresholds: 데이터가 정책을 내장(재현/공유에 유리)
- profile: 목적별 정책을 중앙에서 관리(운영 전환에 유리)

EvalVault는 둘 다 지원한다.

- 근거: thresholds는 dataset에도 있고(`Dataset.thresholds`), profile 적용도 있다(`apply_threshold_profile`).

### 26.3 비교할 때 반드시 고정해야 하는 것

1) thresholds(최종 run 기준)

- run.thresholds가 같은지 확인

2) 표본

- 전처리로 dropped_cases가 달라지지 않는지 확인

3) 메트릭 목록

- 메트릭이 바뀌면 pass_rate 정의 자체가 바뀐다

### 26.4 변경 후 확인해야 하는 것

1) 어떤 케이스가 새로 떨어졌나?

- "모델이 나빠졌다"가 아니라, "정의가 바뀌었다"일 수 있다.

2) 그 케이스의 contexts가 충분히 근거였나?

- contexts가 나쁘면, threshold 강화는 모델이 아니라 데이터를 벌준다.

3) threshold를 바꿨는데도 원하는 실패가 잡히지 않나?

- 그 경우 threshold가 아니라 메트릭 선택 자체가 틀렸을 수 있다.
  (예: 환각을 잡고 싶은데 answer_relevancy만 보고 있었다)

---

## 27. 실습: 데이터셋/메트릭/threshold를 스스로 설계해보기

이 절은 "읽고 끝"이 아니라, 팀이 같은 언어로 의사결정할 수 있게 만드는 연습 문제다.
정답은 하나가 아니다. 중요한 건 "근거"와 "일관성"이다.

### 27.1 실습 A: 최소 QA 데이터셋 만들기

목표:

- 10개 내외 test_case로 QA 데이터셋을 만든다.
- 메트릭은 `faithfulness`, `answer_relevancy`만 사용한다.

제약:

- 모든 test_case는 contexts를 가진다.
- contexts는 1~3개로 제한한다(너무 길게 만들지 않기).

템플릿:

- `docs/templates/dataset_template.json`

체크 질문:

- contexts가 정말 "근거"인가, 아니면 단순 관련 텍스트인가?
- 답변(answer)이 contexts에 의해 지지되는가?

### 27.2 실습 B: retrieval 메트릭을 추가해보기

목표:

- 위 데이터셋에서 5개 케이스를 골라 ground_truth를 작성한다.
- 메트릭에 `mrr` 또는 `hit_rate`를 추가한다.

근거:

- 이 레포의 retrieval 메트릭은 contexts와 ground_truth 토큰 overlap을 사용한다.
  - `src/evalvault/domain/metrics/retrieval_rank.py`

체크 질문:

- ground_truth가 너무 짧아서 토큰 overlap 기반 판단이 불안정하지 않은가?
- contexts의 순서가 실제 retrieval 순서를 반영하는가?

### 27.3 실습 C: threshold profile과 dataset thresholds를 비교해보기

목표:

- 동일 데이터셋에 대해
  1) dataset.thresholds를 채운 실행
  2) dataset.thresholds는 비우고 profile로만 맞춘 실행
  을 설계해보고, 무엇이 더 운영에 적합한지 토론한다.

근거:

- profile 적용은 `src/evalvault/domain/services/threshold_profiles.py`.
- 도메인 기본 threshold는 `src/evalvault/domain/services/evaluator.py#DEFAULT_METRIC_THRESHOLDS`.

체크 질문:

- 팀이 "정책 변경"을 어디에서 리뷰하고 싶은가(데이터 PR vs 설정 PR)?
- 같은 dataset이 환경에 따라 다른 결과가 나오는 것을 허용할 수 있는가?

### 27.4 실습 D: artifacts/index.json을 신뢰할 수 있게 만들기

목표:

- 분석 실행 후 artifacts 디렉터리를 확보했다고 가정한다.
- `index.json`을 열어 nodes/path가 실제 파일과 매칭되는지 확인한다.
- lint를 돌려 보고 경고/오류를 해석한다.

근거:

- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`
- `src/evalvault/domain/services/artifact_lint_service.py#ArtifactLintService`
- `src/evalvault/adapters/inbound/cli/commands/artifacts.py`

---

## 28. 미니 용어사전(데이터/메트릭)

- `Dataset`: test_cases + thresholds를 담는 평가 입력 단위. 근거: `src/evalvault/domain/entities/dataset.py`.
- `TestCase`: 단일 평가 케이스. question/answer/contexts/ground_truth/metadata. 근거: `src/evalvault/domain/entities/dataset.py`.
- `contexts`: retrieved_contexts로 Ragas에 전달되는 근거 텍스트 리스트.
- `ground_truth`: reference로 Ragas에 전달되는 기대 답(필요한 메트릭에서만).
- `MetricSpec`: 메트릭 요구사항/분류 메타데이터. 근거: `src/evalvault/domain/metrics/registry.py`.
- `threshold`: 점수를 pass/fail로 바꾸는 기준값.
- `threshold profile`: 목적별 추천 threshold 묶음(qa/summary). 근거: `src/evalvault/domain/services/threshold_profiles.py`.
- `EvaluationRun`: 한 번의 평가 실행 결과. thresholds/metrics/결과 리스트를 포함. 근거: `src/evalvault/domain/entities/result.py`.
- `MetricScore`: 한 메트릭의 점수+threshold+pass 여부. 근거: `src/evalvault/domain/entities/result.py`(및 evaluator에서 생성).
- `pass_rate`: 모든 메트릭을 통과한 test case 비율. 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.pass_rate`.
- `metric_pass_rate`: 메트릭 평균이 threshold를 넘는 메트릭 비율. 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.metric_pass_rate`.
- `artifacts/index.json`: 분석 노드 산출물 목차. 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`.

---

## 29. Evidence 인덱스(근거 경로 모음)

데이터 모델:

- `src/evalvault/domain/entities/dataset.py`
- `src/evalvault/domain/entities/result.py`

데이터 로더/템플릿:

- `src/evalvault/adapters/outbound/dataset/loader_factory.py`
- `src/evalvault/adapters/outbound/dataset/base.py`
- `src/evalvault/adapters/outbound/dataset/json_loader.py`
- `src/evalvault/adapters/outbound/dataset/csv_loader.py`
- `src/evalvault/adapters/outbound/dataset/excel_loader.py`
- `src/evalvault/adapters/outbound/dataset/thresholds.py`
- `src/evalvault/adapters/outbound/dataset/templates.py`
- `docs/templates/dataset_template.json`
- `docs/templates/dataset_template.csv`
- `docs/templates/dataset_template.xlsx`

평가/threshold:

- `src/evalvault/domain/services/evaluator.py`
- `src/evalvault/domain/services/threshold_profiles.py`
- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py`
- `src/evalvault/adapters/inbound/api/adapter.py`

메트릭 레지스트리/구현:

- `src/evalvault/domain/metrics/registry.py`
- `src/evalvault/domain/metrics/retrieval_rank.py`
- `src/evalvault/domain/metrics/contextual_relevancy.py`
- `src/evalvault/domain/metrics/insurance.py`

아티팩트/index/lint:

- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- `src/evalvault/domain/services/artifact_lint_service.py`
- `src/evalvault/adapters/inbound/cli/commands/artifacts.py`
- `src/evalvault/adapters/inbound/mcp/tools.py#get_artifacts`

Stage(고급, 상세는 04장):

- `src/evalvault/adapters/inbound/cli/commands/stage.py`

---

## 30. FAQ(심화): 팀에서 실제로 자주 싸우는 지점

Q1. contexts를 "정답이 포함된 문서"로만 제한해야 하나?

- 이 레포의 기본 모델은 contexts를 "근거"로 본다.
- 하지만 운영에서는 contexts가 종종 "관련 문서"(정답을 포함하지 않을 수도 있음)로 들어온다.
  이 경우 faithfulness 계열을 gate로 쓰면, 모델이 아니라 검색 파이프라인을 벌줄 수 있다.

권장:

- contexts가 근거인지 힌트인지 팀 정의를 먼저 고정한다.
- 근거가 아니라면, contextual_relevancy 같은 "검색 정합성" 지표를 별도 gate로 두는 것이 더 정직하다.

Q2. 전처리가 데이터를 바꾸면, 재현성에 나쁜 것 아닌가?

- 전처리는 재현성을 깨기 위한 것이 아니라, "불안정한 입력"이 점수 분산을 키우는 문제를 줄이기 위한 것이다.
- 하지만 dropped_cases가 발생하면 표본이 바뀌므로, 그 자체가 중요한 변화다.

권장:

- 전처리 리포트를 run 메타데이터로 저장하고(가능한 경우), 비교에서 함께 본다.
- dropped_cases가 생기는 데이터셋은 원천 데이터를 개선해, 전처리에 덜 의존하게 만든다.

Q3. metric_pass_rate는 왜 0.7로 비교하는가?

- metric_pass_rate는 각 메트릭 평균과 해당 threshold를 비교한다.
- 다만 일부 로직(예: scorecard 등)에서 pass_rate를 0.7 기준으로 risk로 표시하는 케이스가 있을 수 있다.
  이런 부분은 "표현"(리포트/UI) 계층일 가능성이 크므로, 운영 의사결정은 run.thresholds를 기준으로 한다.

Q4. 메트릭이 많은데, 레지스트리/구현 중 무엇을 먼저 봐야 하나?

- 레지스트리로 입력 요구사항(requires_ground_truth/embeddings)을 먼저 확인한다.
- 그 다음 해당 메트릭의 구현(또는 evaluator의 사용 방식)을 확인한다.

근거:

- 레지스트리: `src/evalvault/domain/metrics/registry.py`
- evaluator: `src/evalvault/domain/services/evaluator.py`

---

## 31. 자기 점검(추가): 데이터/메트릭 리뷰 미팅에서 던질 질문

아래 질문은 "정답"을 요구하지 않는다.
대신 팀이 같은 전제를 공유하고 있는지 확인하는 체크포인트다.

1) 지금 보고 있는 pass_rate는 케이스 기준인가, 메트릭 기준인가?
2) contexts는 근거인가, 힌트인가?
3) contexts가 비어 있는 케이스가 있다면, 그 케이스는 무엇을 평가하고 있는가?
4) ground_truth는 누가, 어떤 프로세스로 만들었나?
5) ground_truth 기반 메트릭을 gate로 쓸 때, false negative를 어떻게 다룰 것인가?
6) thresholds의 소유자는 어디인가(dataset/profile/run override)?
7) thresholds를 바꿀 때, dataset_version을 올릴 규칙이 있는가?
8) 전처리에서 dropped_cases가 생겼다면, 표본 변화는 허용 가능한가?
9) embeddings가 필요한 메트릭을 추가할 때, 비용/지연 회귀를 어떻게 감시할 것인가?
10) retrieval 메트릭의 ground_truth는 "정답 텍스트"인가 "문서"인가? 우리 팀의 정의는 무엇인가?
11) 보험 도메인 메트릭(insurance_term_accuracy)을 gate로 쓸 때, "용어가 없어서 1.0"인 케이스를 어떻게 해석할 것인가?
12) artifacts/index.json이 없거나 깨졌을 때, 우리 팀은 결과를 신뢰할 수 있는가?
13) lint 경고/오류를 CI에서 fail로 만들 것인가? (strict 모드 적용 여부)
14) 동일 run_id 비교에서 "설정 스냅샷"(tracker_metadata)이 없다면 무엇을 포기해야 하나?
15) metric 조합을 늘릴수록 pass_rate가 떨어지는 것을, "품질 하락"으로 착각하지 않겠다는 합의가 있는가?
16) contexts의 최대 길이/개수 제한은 어디에서 적용되며(전처리), 팀이 그 값을 바꿔야 할 때는 언제인가?
17) CSV 인코딩이 깨졌을 때(가끔은 조용히 깨짐), 이를 발견할 수 있는 프로세스가 있는가?
18) dataset thresholds와 profile thresholds가 충돌할 때(서로 다른 숫자), 어떤 것이 이길지 팀이 알고 있는가?
19) retrieval_metadata를 남기고 있는가? 남기지 않는다면 retrieval 관련 실패를 어떻게 디버깅할 것인가?
20) 새로운 메트릭을 추가할 때, 레지스트리(MetricSpec)도 함께 업데이트해야 한다는 합의가 있는가?

마지막으로, 이 장의 모든 규칙은 "더 좋은 숫자"를 만들기 위함이 아니라
"같은 실험을 다시 돌렸을 때 같은 결론이 나오는가"를 보장하기 위함이다.
데이터/메트릭/threshold/아티팩트 중 하나라도 흔들리면, 결론은 흔들린다.

운영에서 문제가 생겼을 때는 순서를 고정하자:
입력(데이터) -> 기준(threshold) -> 계산(메트릭) -> 근거(아티팩트).
이 순서를 거꾸로 가면, 대부분 시간을 낭비한다.
