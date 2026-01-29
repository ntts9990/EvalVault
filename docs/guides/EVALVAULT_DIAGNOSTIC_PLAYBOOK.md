# EvalVault 진단 플레이북 (Diagnostic Playbook)
> EvalVault의 분석(Analysis) 기능을 “문제 → 분석 선택 → 실행 → 아티팩트 해석 → 개선 실험”으로 연결하는 한국어 진단 실행서

---

## 1) 목적 / 범위

### 목적
- 평가 점수의 “좋고 나쁨”을 넘어 **왜 그런지(원인)와 무엇을 바꿔야 하는지(액션)**를 재현 가능한 흐름으로 정리한다.
- CLI/Web UI에서 동일한 DB를 공유하는 전제 하에 **run_id 중심**으로 진단을 표준화한다.

### 범위(포함)
- 단일 실행(run_id) 진단: 통계/NLP/인과/플레이북/가설/네트워크/시계열
- A/B 비교(run_id A vs B): 통계 비교 + 변경 탐지 + 비교 보고서
- 검색/임베딩/형태소 “검증” 루틴(데이터 품질·전처리·리트리버 품질 확인)
- 산출물(보고서/아티팩트) 구조 및 해석 기준
- 반복 개선 루프 및 품질 체크리스트

### 범위(제외)
- 본 문서는 코드 변경/새 기능 설계를 포함하지 않는다.
- 외부 링크/URL은 참조하지 않는다.

### 전문가 관점 체크(문서 구조 기준)
- **인지과학자**: 평가 가이드의 모호성/편향을 줄이고, 진단 단계에서 인지 부하를 줄이는 흐름(결정 트리 → 실행 → 해석)을 유지한다.
- **편집자**: 보고서/아티팩트 해석 순서가 일관되는지(요약 → 근거 → 액션) 확인한다.
- **국문학자**: 한국어 표현/톤 관련 문제는 `verify_morpheme` 결과와 함께 판단하고, 문체 기준이 분명한지 점검한다.
- **소프트웨어 개발자**: 아티팩트 경로와 run_id 재현성이 항상 남는지, 실패 시 원인 추적이 가능한지 확인한다.
- **아키텍트**: 진단 단계에서 모듈 간 의존성이 과도하지 않은지(단일 축 변경 원칙 유지) 점검한다.
- **UI/UX 전문가**: 사용자가 “다음 액션”을 바로 이해할 수 있도록 핵심 아티팩트/결론 노출 순서를 고정한다.

---

## 2) 전제조건(필수) / 준비물

### 실행 환경(Extras)
- `analysis`: 통계/분석 모듈 기반(예: scikit-learn, xgboost)
- `timeseries`: 시계열 고급 분석 기반(예: aeon, numba)
- `dashboard`: 대시보드 출력 기반(예: matplotlib)
- (권장) `korean`: 한국어 형태소/검색 기반(예: kiwipiepy, rank-bm25, sentence-transformers)

### 필수 입력/식별자
- `DB`: 기본 Postgres(`POSTGRES_*`), SQLite 사용 시 `--db` 또는 `EVALVAULT_DB_PATH`
- `run_id`: 평가/분석/아티팩트가 묶이는 단위 식별자
- `metrics`: 예) `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`

### 핵심 산출물 경로(고정 패턴)
- 단일 실행 자동 분석:
  - `reports/analysis/analysis_<RUN_ID>.json`
  - `reports/analysis/analysis_<RUN_ID>.md`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`
- A/B 비교:
  - `reports/comparison/comparison_<RUN_A>_<RUN_B>.json`
  - `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`

---

## 3) 분석 도구 지형도(분류)

### 3.1 “의도(AnalysisIntent)” 분류(실행 선택의 기준)
의도 열거형: `src/evalvault/domain/entities/analysis_pipeline.py`

| 카테고리 | Intent 값 | 한 줄 용도 | 기본 템플릿 핵심 노드(요약) |
|---|---|---|---|
| 검증 | `verify_morpheme` | 한국어 형태소 처리 품질 점검 | `data_loader → morpheme_analyzer → morpheme_quality_checker → verification_report` |
| 검증 | `verify_embedding` | 임베딩 분포/품질 점검 | `data_loader → embedding_analyzer → embedding_distribution → verification_report` |
| 검증 | `verify_retrieval` | 검색 컨텍스트 품질 점검 | `data_loader → retrieval_analyzer → retrieval_quality_checker → verification_report` |
| 비교 | `compare_search` | BM25/Dense/Hybrid 검색 비교 | `data_loader → (bm25/embedding/hybrid) → search_comparator → comparison_report` |
| 비교 | `compare_models` | 모델별 성능 비교 | `run_loader → model_analyzer → statistical_comparator → comparison_report` |
| 비교 | `compare_runs` | 실행(run) 단위 비교 | `run_loader → run_analyzer → statistical_comparator → comparison_report` |
| 분석 | `analyze_low_metrics` | 낮은 점수 원인 분석(종합) | `ragas_evaluator/low_performer_extractor/diagnostic_playbook/causal/root_cause/priority_summary/llm_report` |
| 분석 | `analyze_patterns` | 패턴(키워드/질문유형) 중심 | `data_loader → nlp_analyzer → pattern_detector → (priority/llm_report)` |
| 분석 | `analyze_trends` | 실행 이력 기반 추세 | `run_loader → time_series_analyzer → trend_detector → llm_report` |
| 분석 | `analyze_statistical` | 통계 요약/상관 | `data_loader → statistical_analyzer` |
| 분석 | `analyze_nlp` | NLP 요약(키워드/유형) | `data_loader → nlp_analyzer` |
| 분석 | `analyze_causal` | 인과 단서(상관 기반 힌트 포함) | `data_loader → statistical_analyzer → causal_analyzer` |
| 분석 | `analyze_network` | 메트릭 상관 네트워크 | `data_loader → statistical_analyzer → network_analyzer` |
| 분석 | `analyze_playbook` | 플레이북 기반 진단(간단) | `data_loader → diagnostic_playbook` |
| 분석 | `detect_anomalies` | 이상 탐지(시계열) | `run_loader → timeseries_advanced(mode=anomaly)` |
| 분석 | `forecast_performance` | 성능 예측(시계열) | `run_loader → timeseries_advanced(mode=forecast)` |
| 분석 | `generate_hypotheses` | 가설 생성(자동) | `data_loader → statistical_analyzer → ragas_evaluator → low_performer_extractor → hypothesis_generator` |
| 벤치마크 | `benchmark_retrieval` | 검색 벤치마크 | `retrieval_benchmark` |
| 보고서 | `generate_summary` | 요약 보고서 | `data_loader/statistical/priority_summary → llm_report(report_type=summary)` |
| 보고서 | `generate_detailed` | 상세 보고서(종합) | `통계+RAGAS+진단+NLP+패턴+인과+원인+추세 → llm_report(report_type=analysis)` |
| 보고서 | `generate_comparison` | 비교 보고서(종합) | `run_loader → run_metric_comparator + run_change_detector → llm_report(report_type=comparison)` |

> 템플릿 정의 근거: `src/evalvault/domain/services/pipeline_template_registry.py`
> 모듈 등록 근거: `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`

---

### 3.2 “모듈(module_id)” 지도(실제 실행 단위)
모듈은 `pipeline_factory.py`에서 등록되며, 각 모듈은 `module_id`를 가진다.

| module_id | 파일(근거) | 역할 | 주로 쓰이는 의도/상황 |
|---|---|---|---|
| `data_loader` | `src/evalvault/adapters/outbound/analysis/data_loader_module.py` | 데이터/런 로드 | 단일 실행 기반 대부분 |
| `run_loader` | `src/evalvault/adapters/outbound/analysis/run_loader_module.py` | DB에서 run 로드 | 비교/추세/시계열 |
| `statistical_analyzer` | `src/evalvault/adapters/outbound/analysis/statistical_analyzer_module.py` | 평균/분산/상관/통과율 | “원인 분석의 시작점” |
| `nlp_analyzer` | `src/evalvault/adapters/outbound/analysis/nlp_analyzer_module.py` | 키워드/질문유형 요약 | 패턴·분포 확인 |
| `causal_analyzer` | `src/evalvault/adapters/outbound/analysis/causal_analyzer_module.py` | 인과 단서 생성 | 원인 가설 강화 |
| `diagnostic_playbook` | `src/evalvault/adapters/outbound/analysis/diagnostic_playbook_module.py` | 메트릭별 진단/개선 힌트 | 저점수 신속 대응 |
| `root_cause_analyzer` | `src/evalvault/adapters/outbound/analysis/root_cause_analyzer_module.py` | 진단+인과 단서를 원인으로 집계 | 액션 후보 정리 |
| `pattern_detector` | `src/evalvault/adapters/outbound/analysis/pattern_detector_module.py` | 키워드/유형 패턴 요약 | 재현 조건 찾기 |
| `retrieval_analyzer` | `src/evalvault/adapters/outbound/analysis/retrieval_analyzer_module.py` | 검색 요약 통계 | 검색 품질 검증 |
| `retrieval_quality_checker` | `src/evalvault/adapters/outbound/analysis/retrieval_quality_checker_module.py` | 검색 품질 체크(휴리스틱) | “검색이 문제인지” 빠른 판정 |
| `embedding_analyzer` | `src/evalvault/adapters/outbound/analysis/embedding_analyzer_module.py` | 임베딩 분포 통계 | 임베딩 드리프트/품질 |
| `morpheme_analyzer` | `src/evalvault/adapters/outbound/analysis/morpheme_analyzer_module.py` | 형태소 분석 | 한국어 쿼리/토큰화 |
| `morpheme_quality_checker` | `src/evalvault/adapters/outbound/analysis/morpheme_quality_checker_module.py` | 형태소 품질 체크 | 한국어 분석 신뢰성 |
| `time_series_analyzer` | `src/evalvault/adapters/outbound/analysis/time_series_analyzer_module.py` | 실행 이력 요약 | 추세 파악 |
| `timeseries_advanced` | `src/evalvault/adapters/outbound/analysis/timeseries_advanced_module.py` | 이상탐지/예측 | 릴리즈 회귀 감지 |
| `trend_detector` | `src/evalvault/adapters/outbound/analysis/trend_detector_module.py` | 추세 감지 | 회귀 시점 탐색 |
| `network_analyzer` | `src/evalvault/adapters/outbound/analysis/network_analyzer_module.py` | 상관 네트워크 | 메트릭 구조 파악 |
| `hypothesis_generator` | `src/evalvault/adapters/outbound/analysis/hypothesis_generator_module.py` | 가설 자동 생성 | 다음 실험 설계 |
| `run_metric_comparator` | `src/evalvault/adapters/outbound/analysis/run_metric_comparator_module.py` | A/B 메트릭 비교 상세 | 비교 스코어카드 |
| `run_change_detector` | `src/evalvault/adapters/outbound/analysis/run_change_detector_module.py` | 데이터/설정/프롬프트 변경 탐지 | “뭐가 바뀌었나” |
| `llm_report` | `src/evalvault/adapters/outbound/analysis/llm_report_module.py` | 요약/상세/비교 리포트 | 사람 읽는 결론화 |

---

## 4) 진단 결정 트리(문제 → 분석 선택)

### 4.1 0단계: “진단 가능 상태” 체크(실패 원인 제거)
- [ ] Postgres 연결 설정이 올바른가 (`POSTGRES_*` 또는 `POSTGRES_CONNECTION_STRING`)
- [ ] SQLite를 쓰는 경우 `--db` 또는 `EVALVAULT_DB_PATH`가 올바른가
- [ ] 대상 `run_id`가 DB에 존재하는가 (`evalvault history`로 확인)
- [ ] 데이터셋에 `thresholds`가 포함되어 있는가(또는 기본 기준을 알고 있는가)
- [ ] 메트릭 실행 조건(임베딩 필요 메트릭 등)을 충족하는가

### 4.2 1단계: 증상 기반 선택(가장 빠른 분기)
아래 표에서 “현재 문제”를 고르고, 권장 Intent/명령으로 바로 진입한다.

| 문제(증상) | 1차 목표 | 권장 Intent(또는 명령) | 우선 확인 아티팩트 |
|---|---|---|---|
| 특정 메트릭이 임계치 미달(전반적 저점수) | “왜 낮은지” 원인 후보 만들기 | `analyze_low_metrics` 또는 `analyze_playbook` | `analysis_<RUN_ID>.md`, `diagnostic_playbook.json`, `root_cause_analyzer.json` |
| `faithfulness` 낮음 | 근거/인용/컨텍스트 정합 문제 분리 | `analyze_low_metrics` + `verify_retrieval` | `retrieval_quality_checker.json`, `ragas_evaluator.json` |
| `answer_relevancy` 낮음 | 의도 파악/프롬프트 정렬 점검 | `analyze_low_metrics` + `analyze_patterns` | `nlp_analyzer.json`, `pattern_detector.json` |
| `context_precision` 낮음 | 불필요 컨텍스트/노이즈 | `verify_retrieval` + (필요 시) `compare_search` | `retrieval_analyzer.json`, `search_comparator.json` |
| `context_recall` 낮음 | top_k/쿼리 확장/청킹 이슈 | `verify_retrieval` + `benchmark_retrieval` | `retrieval_benchmark.json`, `retrieval_quality_checker.json` |
| 임베딩 기반 메트릭이 불안정/이상 | 임베딩 백엔드/분포 점검 | `verify_embedding` | `embedding_analyzer.json`, `embedding_distribution.json` |
| 한국어에서 토큰화/검색이 이상 | 형태소 기반 파이프라인 점검 | `verify_morpheme` | `morpheme_quality_checker.json` |
| 릴리즈 이후 점수가 갑자기 하락 | 하락 시점/원인 변경 추적 | `analyze_trends` + `generate_comparison` | `trend_detector.json`, `run_change_detector.json` |
| A/B 비교에서 개선이 애매함 | 유의성/변경점 정리 | `evalvault analyze-compare` 또는 `generate_comparison` | `comparison_<A>_<B>.md`, `run_metric_comparator.json` |
| 스테이지 병목/지연/트레이스 누락 | 실행 단계/추적 문제 분리 | `evalvault stage` + `evalvault debug report` | debug report 출력, stage metrics 리스트 |
| 상관 구조가 바뀜(메트릭 간 연동) | 상관/네트워크 구조 확인 | `analyze_network` | `network_analyzer.json` |
| 다음 실험 설계를 못하겠음 | 가설 자동 생성 | `generate_hypotheses` | `hypothesis_generator.json` |

---

## 5) 핵심 플레이북 시나리오(최소 8개)

> 공통 원칙: 각 시나리오는 **(1) 문제 정의 → (2) 실행 경로 → (3) 아티팩트 판독 → (4) 다음 실험** 순서로 처리한다.

### 시나리오 1) “전체 통과율이 낮다” (원인 후보를 빠르게 만든다)
- 트리거: `analysis_<RUN_ID>.md`에서 전체 통과율이 낮음(예: 0.7 미만)
- 실행(CLI):
  - `uv run evalvault analyze <RUN_ID> --db data/db/evalvault.db --nlp --causal --playbook --enable-llm`
- 실행(Web UI):
  - Reports에서 run 선택 → Analysis Lab에서 “분석(통계/NLP/인과/플레이북)” 실행
- 확인 아티팩트:
  - `reports/analysis/artifacts/analysis_<RUN_ID>/diagnostic_playbook.json`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/root_cause_analyzer.json`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/priority_summary.json`
- 해석 기준:
  - `diagnostics`의 `gap(임계치-점수)`가 큰 메트릭부터 우선순위.
  - `root_cause_analyzer`의 추천(recommendations) 중 “반복적으로 등장하는 조치”를 1차 실험 후보로 채택.
- 다음 액션:
  - 프롬프트/검색(top_k, 리랭킹)/데이터 정제 중 **1개 축만** 바꿔 재실행(run) 후 비교.

---

### 시나리오 2) “faithfulness가 낮다” (검색 문제 vs 생성 문제 분리)
- 트리거: `faithfulness`가 임계치 미달
- 실행(권장 흐름):
  1) 검색 품질 검증 → 2) 저점수 원인 분석(종합)
- 실행(파이프라인 Intent):
  - 1) `verify_retrieval`
  - 2) `analyze_low_metrics`
- 실행(CLI 예시):
  - `uv run evalvault pipeline analyze "검색 품질 검증" --run-id <RUN_ID> --db data/db/evalvault.db`
  - `uv run evalvault pipeline analyze "낮은 메트릭 원인 분석" --run-id <RUN_ID> --db data/db/evalvault.db`
- 확인 아티팩트(핵심):
  - `retrieval_quality_checker.json`의 `passed` 및 체크 항목(빈 컨텍스트 비율/평균 컨텍스트 토큰/키워드 겹침/ground_truth hit)
  - `diagnostic_playbook.json`의 `faithfulness` 관련 진단/권고
- 해석 기준:
  - `verify_retrieval` 체크 실패이면: 생성(LLM)보다 **검색/컨텍스트 구성**이 1차 병목.
  - 체크 통과인데 faithfulness만 낮으면: **답변의 근거 인용/출처 정렬(프롬프트/후처리)**를 우선 점검.
- 다음 액션:
  - 검색 체크 실패 시: 리랭킹/노이즈 필터/컨텍스트 최소 토큰 확보부터.
  - 검색 체크 통과 시: 시스템 프롬프트에 “근거 인용/컨텍스트 밖 주장 금지” 등 정렬 강화.

---

### 시나리오 3) “answer_relevancy가 낮다” (의도/질문유형 패턴으로 좁힌다)
- 트리거: `answer_relevancy`가 임계치 미달
- 실행(Intent): `analyze_patterns` + (필요 시) `analyze_low_metrics`
- 확인 아티팩트:
  - `nlp_analyzer.json` (top_keywords, question_types)
  - `pattern_detector.json` (상위 키워드/질문유형 요약)
- 해석 기준:
  - 특정 질문유형(예: 절차형/정의형/비교형)이 과대표집되어 있고 해당 유형에서 점수가 낮으면 → **유형별 프롬프트 분기** 후보.
- 다음 액션:
  - 질문유형별 템플릿/가드레일을 분리한 뒤 동일 데이터셋으로 재평가.

---

### 시나리오 4) “context_precision이 낮다” (노이즈 컨텍스트를 줄인다)
- 트리거: `context_precision`이 낮고, 컨텍스트가 길거나 많음
- 실행(Intent): `verify_retrieval` → (대안 비교) `compare_search`
- 확인 아티팩트:
  - `retrieval_analyzer.json` 요약(컨텍스트 개수/토큰/빈 컨텍스트 비율/키워드 겹침)
  - `compare_search` 결과(하이브리드 방식 비교 시)
- 해석 기준:
  - 키워드 겹침이 낮고 컨텍스트 토큰이 크면: “긴데 관련 없음” 패턴 → **리랭킹/필터링** 우선.
- 다음 액션:
  - top_k를 무작정 늘리기보다, 불필요 컨텍스트 제거(precision 확보)부터 적용 후 재평가.

---

### 시나리오 5) “context_recall이 낮다” (찾아야 할 근거를 못 찾는다)
- 트리거: `context_recall`이 낮고, ground_truth가 존재하는 데이터셋
- 실행(Intent): `verify_retrieval` + `benchmark_retrieval`
- 확인 아티팩트:
  - `retrieval_quality_checker.json`의 `ground_truth_hit_rate`
  - `retrieval_benchmark.json`(벤치마크 결과)
- 해석 기준:
  - `ground_truth_hit_rate`가 낮으면: 쿼리/청킹/인덱싱 단계의 재현율 병목 가능성이 큼.
- 다음 액션:
  - 청킹 전략/쿼리 확장/검색 방식(하이브리드) 실험을 1개씩 분리 실행.

---

### 시나리오 6) “임베딩 기반 지표가 흔들린다/이상하다” (백엔드/분포 확인)
- 트리거: `semantic_similarity` 등 임베딩 기반 결과가 불안정하거나 NaN/실패가 잦음
- 실행(Intent): `verify_embedding`
- 확인 아티팩트:
  - `embedding_analyzer.json` 요약(backend/model/dimension/avg_norm/norm_std/mean_cosine_to_centroid)
  - `embedding_distribution.json`(분포 점검 결과)
- 해석 기준:
  - `norm_std`가 지나치게 낮거나 `mean_cosine_to_centroid`가 지나치게 높으면: 임베딩이 한 방향으로 붕괴/클러스터링 가능성.
  - backend 오류가 있으면: 임베딩 지표 해석 전에 환경/모델을 먼저 안정화.
- 다음 액션:
  - 임베딩 백엔드/모델을 고정한 뒤(프로필/설정) 재평가하여 변동성부터 제거.

---

### 시나리오 7) “한국어에서 진단 자체가 믿기 어렵다” (형태소/토크나이저 검증)
- 트리거: 한국어 질문/컨텍스트에서 키워드/검색 결과가 부자연스럽거나 분석 품질이 낮다고 의심됨
- 실행(Intent): `verify_morpheme`
- 확인 아티팩트:
  - `morpheme_quality_checker.json`의 `tokenizer_backend`(예: kiwi) 및 토큰/어휘 크기 체크
- 해석 기준:
  - 형태소 품질 체크 실패 시: 키워드/검색/분류 기반 분석 결과의 신뢰도가 동반 하락할 수 있음.
- 다음 액션:
  - 한국어 extra 및 토크나이저 백엔드를 먼저 정상화한 뒤, NLP/검색 관련 분석을 재실행.

---

### 시나리오 8) “릴리즈 이후 성능이 회귀했다” (시점+변경점으로 좁힌다)
- 트리거: 최근 run들의 성능이 하락 추세
- 실행(Intent):
  - 1) `analyze_trends` (하락 시점 탐색)
  - 2) `generate_comparison` (대표 run A/B 선택 후 변경점+비교 보고서)
- 실행(CLI 예시):
  - `uv run evalvault pipeline analyze "추세 분석" --db data/db/evalvault.db`
  - `uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db --test t-test|mann-whitney`
- 확인 아티팩트:
  - `trend_detector.json` (추세 감지 결과)
  - `run_change_detector.json` (데이터셋/설정/프롬프트 변경)
  - `comparison_<A>_<B>.md` (비교 보고서)
- 해석 기준:
  - “변경 탐지”에서 데이터셋이 바뀌었다면 비교 해석이 왜곡될 수 있으므로 **동일 데이터셋 조건**을 우선 확보.
- 다음 액션:
  - 변경이 1개 축(프롬프트/모델/검색)으로 수렴되도록 실험 설계를 재정렬.

---

### 시나리오 9) “스테이지 병목/트레이스 누락” (실행 단계 진단)
- 트리거: 응답 지연/타임아웃, stage metric 누락, Phoenix/Langfuse 링크 없음
- 실행(CLI):
  - `uv run evalvault stage compute-metrics <RUN_ID> --db data/db/evalvault.db`
  - `uv run evalvault debug report <RUN_ID> --db data/db/evalvault.db`
- 확인 아티팩트:
  - debug report의 stage summary/bottlenecks/recommendations/failing metrics
  - trace 링크(phoenix/langfuse)가 있으면 해당 run에서 스팬 흐름 확인
- 해석 기준:
  - 특정 stage에 병목이 집중되면 그 단계(검색/생성/후처리) 개선 우선
  - trace 링크가 없으면 트레이싱 설정/환경 변수 우선 점검
- 다음 액션:
  - `PHOENIX_ENABLED`, `PHOENIX_ENDPOINT` 및 Open RAG Trace 계측(어댑터/데코레이터) 확인

---

### 시나리오 10) “A/B 개선이 애매하다” (유의성/노이즈 관점으로 판단을 강화)
- 트리거: 평균 차이는 있으나 결론이 흔들림(샘플이 적거나 변동이 큼)
- 실행(현재 제공 흐름):
  - `uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db --test t-test|mann-whitney`
  - 파이프라인 비교 보고서: `AnalysisIntent.GENERATE_COMPARISON` (내부에서 사용)
- 보강(신뢰도 진단 프레임):
  - `docs/guides/PRD_LENA.md`의 노이즈 분해/신뢰구간/표본수(N,K) 추천 개념을 적용해 “추가 샘플이 필요한지” 판단한다.
- 해석 기준(운영 규칙):
  - 효과가 작고 표본이 작으면: 결론을 내리기보다 **N(문항 수) 또는 K(반복 수)** 확대가 우선.
- 다음 액션:
  - 동일 데이터셋 조건 유지, 평가 비용 대비 효과가 큰 방향으로 N/K를 늘리는 계획을 수립한다.

---

### 시나리오 11) “자동 지표가 사용자 만족과 어긋난다” (인간 피드백 보정 루프)
- 트리거: 이해관계자가 RAGAS 점수를 KPI로 신뢰하지 않음
- 적용 프레임:
  - `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`의 절차(대표 샘플링 → 인간 평가 → 보정 모델 → 전체 적용 → 반복 개선)를 운영 루프로 연결한다.
- 운영 해석 기준:
  - 자동 지표는 “재현 가능한 신호”로 유지하되, 만족도 정합은 보정 루프로 관리한다.
- 다음 액션:
  - “불일치 케이스(자동 지표는 높지만 만족은 낮음 / 반대)”를 우선 라벨링 대상으로 선정한다.

---

## 6) CLI / Web UI 실행 경로(치트시트)

### 6.1 CLI(가장 빠른 시작)
- 평가 + 자동 분석:
  - `uv run evalvault run <DATASET> --metrics <M1,M2,...> --db data/db/evalvault.db --auto-analyze`
- 단일 run 상세 분석(옵션 조합형):
  - `uv run evalvault analyze <RUN_ID> --db data/db/evalvault.db --nlp --causal --playbook --enable-llm`
  - (선택) `--dashboard`, `--anomaly-detect`, `--forecast`, `--network`, `--generate-hypothesis`
- A/B 비교:
  - `uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db --test t-test|mann-whitney`
- 스테이지/디버그 진단:
  - `uv run evalvault stage compute-metrics <RUN_ID> --db data/db/evalvault.db`
  - `uv run evalvault debug report <RUN_ID> --db data/db/evalvault.db`
- 쿼리 기반 파이프라인:
  - `uv run evalvault pipeline analyze "<자연어 쿼리>" --run-id <RUN_ID> --db data/db/evalvault.db`
- 파이프라인 가시화:
  - `uv run evalvault pipeline intents`
  - `uv run evalvault pipeline templates`

### 6.2 Web UI(메뉴 기반 운영)
- 실행:
  - API: `uv run evalvault serve-api --reload`
  - 프론트: `cd frontend && npm install && npm run dev`
- 메뉴 구조(이관 계획 기준):
  - 기초 통계 / 시계열(이상·예측) / 구조·원인(인과·네트워크) / 지능형(가설·플레이북) / 비교

---

## 7) 산출물/아티팩트(무엇을 어디서 보나)

### 7.1 “요약 보고서” vs “아티팩트”
- 요약 보고서(`analysis_<RUN_ID>.md`, `comparison_<A>_<B>.md`): 의사결정용 결론/요약
- 아티팩트(`artifacts/.../<node_id>.json`): **원본 근거**(재현/디버깅/자동화에 필요)

### 7.2 아티팩트 인덱스 활용
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`에는 노드별 결과 파일 경로가 구조화되어 있다.
- 운영 원칙: “보고서로 결론을 보고 → 인덱스로 근거 노드를 찾아 → 노드 JSON으로 확인” 순서를 고정한다.

---

## 8) 해석 기준 / 주의사항(오판 방지)

### 8.1 비교 분석 주의
- A/B 비교는 **동일 데이터셋 조건**에서 수행해야 해석이 안전하다.
- `run_change_detector`에서 데이터셋/설정/프롬프트 변경이 다수 발견되면, 결론을 내리기 전에 변경 축을 줄인다.

### 8.2 지표 해석 주의
- `thresholds`는 데이터셋에 포함되며, “점수 0.8이 항상 합격” 같은 단일 기준을 가정하지 않는다.
- 임베딩 기반 지표는 임베딩 백엔드/모델 상태에 민감하므로, `verify_embedding`으로 환경 안정성을 먼저 확인한다.

### 8.3 한국어 특화 주의
- 형태소/토큰화 품질이 낮으면 키워드/검색 기반 분석이 왜곡될 수 있다.
- `verify_morpheme` 결과가 실패인 상태에서 NLP/검색 결과를 과신하지 않는다.

---

## 9) 반복 개선 루프(운영 표준)

### 9.1 루프(고정 절차)
1. **기준 run 확보**: `evalvault run ... --db ... --auto-analyze`
2. **문제 분류**: 결정 트리로 Intent 선택(1차 진단)
3. **근거 확인**: 아티팩트 인덱스 → 핵심 노드 JSON 확인
4. **가설/액션 1개 선택**: 한 번에 한 축만 변경
5. **재실행(run)**: 동일 데이터셋/메트릭 유지
6. **비교(analyze-compare)**: 변화의 방향/유의성/변경점 확인
7. **기록/공유**: 비교 보고서를 “결정 기록”으로 남긴다

### 9.2 “한 번에 하나” 원칙(실험 설계)
- 한 번에 여러 요소(프롬프트+모델+검색)를 바꾸면 원인 추적이 불가능해진다.
- 원인 분석이 목적이면 변경을 최소화하고, 개선이 목적이면 변경은 하되 “비교 보고서로 변경점을 문서화”한다.

---

## 10) 품질 체크리스트(진단 완료 조건)

### 10.1 진단의 완결성
- [ ] 문제(증상)가 “메트릭/구간/범위”로 명확히 정의되었는가
- [ ] 선택한 Intent/모듈이 문제와 직접 연결되는가(근거 노드가 존재하는가)
- [ ] 보고서 결론이 아티팩트(노드 JSON)로 추적 가능한가

### 10.2 재현성
- [ ] `DB 경로`, `run_id`, `metrics`, `profile`이 기록되었는가
- [ ] 산출물 경로(`reports/...`)가 run_id 기준으로 정리되었는가
- [ ] 비교 시 동일 데이터셋 조건을 확인했는가

### 10.3 실행 안정성(환경)
- [ ] `analysis/timeseries/dashboard` extras가 설치되어 필요한 기능이 실행 가능한가
- [ ] 임베딩/한국어 토크나이저 환경이 `verify_embedding/verify_morpheme`로 확인되었는가

### 10.4 액션 품질
- [ ] 다음 실험이 “하나의 변경 축”으로 정의되었는가
- [ ] 성공/실패 판정 기준이 threshold 및 비교 보고서로 정의되었는가

---

## 부록 A) 빠른 매핑(“무슨 문제에 뭘 쓰나”)

| 의도(Intent) | 대표 질문(운영자가 던지는 질문) | 핵심 모듈(module_id) |
|---|---|---|
| `analyze_low_metrics` | “점수가 왜 낮지? 당장 뭘 바꿔야 하지?” | `ragas_evaluator`, `diagnostic_playbook`, `root_cause_analyzer`, `llm_report` |
| `verify_retrieval` | “검색이 문제인가?” | `retrieval_analyzer`, `retrieval_quality_checker` |
| `verify_embedding` | “임베딩이 정상인가?” | `embedding_analyzer`, `embedding_distribution` |
| `verify_morpheme` | “한국어 토큰화가 정상인가?” | `morpheme_analyzer`, `morpheme_quality_checker` |
| `generate_comparison` | “A/B에서 뭐가 바뀌었고 뭐가 유의미하지?” | `run_metric_comparator`, `run_change_detector`, `llm_report` |
| `analyze_trends` | “언제부터 나빠졌지?” | `time_series_analyzer`, `trend_detector` |
| `generate_hypotheses` | “다음 실험 가설을 자동으로 만들 수 있나?” | `hypothesis_generator` |
| `analyze_network` | “메트릭 구조(연동)가 어떻게 바뀌었나?” | `network_analyzer` |

> 스테이지/디버그 진단은 Intent 분류 없이 `evalvault stage`, `evalvault debug report`로 실행한다.
