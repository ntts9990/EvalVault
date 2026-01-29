# EvalVault 목적/미션 정의 및 RAG 성능 분석·개선 제안서

> 본 문서는 EvalVault의 “목적/미션(Why)”을 명확히 정의하고, RAG 시스템의 성능을 **측정 가능하게 분석**한 뒤, **개선 루프(평가→관측→개선→재검증)**를 실행하기 위한 실행 가능한 제안을 제시한다.
> 핵심 설계 정렬: **Hexagonal Architecture(Ports & Adapters)**, **`run_id` 중심 실행 단위**, **Artifacts-first(원본 산출물 보존)**.

---

## 0. TL;DR (요약)

- EvalVault의 미션은 RAG 개발/운영에서 가장 어려운 질문인 “**진짜 좋아졌나? 왜? 재현 가능한가?**”에 답하는 것이다.
- 성능 관리는 “점수 1개”가 아니라 **품질(정확·근거·관련)** + **검색(리트리벌) 품질** + **운영(비용·지연·안정성)** + **인간(해석·의사결정)**의 동시 최적화다. ([R14], [R15], [R16], [R33])
- EvalVault는 이를 `run_id`로 묶어 **DB(히스토리/비교)** + **아티팩트(원본/재현)** + **트레이싱(관측)**을 연결한다. (내부 근거: `docs/handbook/CHAPTERS/00_overview.md`, `docs/handbook/CHAPTERS/01_architecture.md`, `docs/handbook/CHAPTERS/03_workflows.md`)

---

## 1. 목적/미션 정의 (Purpose / Mission)

### 1.1 목적(Purpose)
RAG 시스템의 개선이 “감(感)”이 아니라 **데이터·근거·재현성**으로 누적되도록 하는 평가/분석/관측 플랫폼을 제공한다.

- 평가(Evaluation): 데이터셋+메트릭+threshold로 “합격/위험”을 정의
- 분석(Analysis): 점수의 원인을 설명 가능한 형태로 분해(리트리벌/생성/구성요소별)
- 관측(Observability): 병목/오류/품질 문제를 단계(Stage)로 추적
- 개선(Improvement Loop): 프롬프트/리트리벌/구성 변경을 실험으로 관리하고 회귀를 차단

### 1.2 미션(Mission)
**“RAG 성능 개선을 반복 가능하게 만든다.”**
구체적으로는 아래 4가지를 동시에 만족시키는 워크플로를 제공한다.

1. **측정 가능성**: 변화(모델/프롬프트/리트리버)가 KPI로 드러난다. ([R14], [R15], [R16])
2. **원인 규명 가능성**: 점수 하락이 “어디서/왜” 발생했는지 추적한다. ([R18], [R19], [R20], [R33])
3. **재현 가능성**: 동일 입력/설정/산출물을 `run_id`와 아티팩트로 다시 확인한다. (내부 근거: `docs/handbook/CHAPTERS/03_workflows.md`)
4. **운영 가능성**: 비용/지연/안정성을 함께 관리해 “좋은 데모”가 “좋은 서비스”가 되게 한다. ([R17], [R33], [R34])

---

## 2. RAG 성능 문제를 “시스템”으로 정의하기

### 2.1 RAG 성능의 4축
RAG 품질 저하는 대체로 4개 축에서 발생한다.

- **Retrieval 실패**: 필요한 근거를 못 찾음(Recall 문제) 또는 노이즈가 과다(Precision 문제) ([R17], [R21], [R22])
  - (노이즈 저감 원칙) **SNR(신호/잡음) 개선**을 목표로 한다: 무관 문서 제거(필터/리랭킹), 중복/과다 컨텍스트 축소(chunk/길이/개수 제한), 실험 변경은 `run_id`로 분리해 비교한다.
- **Grounding 실패(환각/왜곡)**: 컨텍스트 밖 주장, 법/의료 등 고위험 도메인에서 치명적 ([R28], [R34], [R35])
- **Task/Intent 불일치**: 답변이 질문 의도를 벗어남(Answer relevancy 저하) ([R14], [R16])
- **운영 품질 저하**: 지연/비용/불안정(타임아웃/레이트리밋/일시적 품질 변동) ([R33], [R18], [R19], [R20])

> 따라서 “성능 개선”은 **리트리벌/생성/운영**을 동시에 다루는 **평가·관측·실험 체계**가 필요하다.

### 2.2 멀티턴 RAG의 추가 난점
멀티턴에서는 단일 질의보다 다음 문제가 증폭된다.

- 대화 맥락 누적에 따른 **질의 드리프트/오해**
- 턴 간 근거 연결 실패(“앞에서 말한 것”이 무엇인지)
- 장기 대화에서 비용/지연 증가

멀티턴 평가/벤치마크 관점은 별도 설계가 필요하다. ([R3])

---

## 3. EvalVault 아키텍처 정렬: Hexagonal + `run_id` + Artifacts

### 3.1 Hexagonal Architecture(Ports & Adapters)로 “정책 vs 연결” 분리
EvalVault는 외부 의존성(LLM/DB/Tracker)을 **어댑터로 격리**하고, 도메인 규칙은 `domain`에 유지한다.
이 구조는 “측정/비교/재현”이라는 정책이 외부 도구 변경에 흔들리지 않게 만든다.

- Adapters → Ports → Domain 방향 유지 (내부 근거: `docs/handbook/CHAPTERS/01_architecture.md`)

### 3.2 `run_id`는 “실행 단위의 단일 진실”
`run_id`는 다음을 하나로 묶는 키다.

- 평가 결과(메트릭/테스트케이스)
- 단계 이벤트(Stage Events)
- 분석 산출물(리포트/아티팩트)
- 트레이싱/외부 관측 메타데이터

즉, RAG 시스템의 개선은 “버전”이 아니라 “**run의 비교**”로 관리된다.

### 3.3 Artifacts-first는 “설명 가능성”을 만든다
점수만 저장하면 원인 분석이 불가능해진다. EvalVault는 다음 원칙을 따른다.

- **요약 리포트(사람이 읽는 결과)**와 **노드별 아티팩트(원본/재현)**를 분리 저장
- `index.json`을 중심으로 아티팩트를 탐색 (내부 근거: `docs/handbook/CHAPTERS/03_workflows.md`)

이 방식은 “지표가 왜 떨어졌는지”를 **구체 산출물**로 역추적 가능하게 한다.

---

## 4. KPI 설계: “측정 가능한 개선”으로 바꾸기

### 4.1 KPI 설계 원칙
- KPI는 “모델 점수”만이 아니라 **품질·검색·운영·인간**을 포함한다. ([R14], [R15], [R16], [R33])
- KPI는 `run_id` 단위로 저장·비교 가능해야 한다.
- KPI는 **Gate(합격 기준)**로 쓸 수 있어야 한다(회귀 방지).

### 4.2 권장 KPI 세트(예시)
아래는 “프로덕션 RAG”에서 일반적으로 유효한 KPI 묶음이며, 도메인별로 threshold를 조정한다.

| KPI 그룹 | KPI(예시) | 정의/의미 | 측정 포인트(권장) |
|---|---|---|---|
| End-to-End 품질 | Answer relevancy | 질문 의도 정렬 | LLM-as-judge + 샘플 인간평가 혼합 ([R16], [R14]) |
| Grounding/안전 | Faithfulness / Hallucination rate(근사) | 근거 기반 답변 여부 | 근거-주장 정합성, 환각 탐지 규칙/분류기 ([R28], [R35]) |
| Retrieval 품질 | Context precision/recall, NDCG/MRR/Hit@K | 검색이 답변에 “쓸모 있는가” | 오프라인 벤치(정답 근거 존재 시) + 온라인 로그 ([R17], [R15]) |
| 운영 | p95 latency, cost/run, timeout rate | 지연·비용·안정성 | stage/trace 기반 계측 + 실행 메타데이터 ([R33], [R20]) |
| 안정성 | score variance(분산), judge agreement | 점수 흔들림/심판 신뢰도 | 리샘플링/반복 run + judge calibration ([R16], [R15]) |

> LLM-as-judge는 강력하지만 편향/불안정 가능성이 있어, **캘리브레이션(표준 예제/다중 judge/휴먼 샘플링)**이 필요하다. ([R16], [R15])

---

## 5. 평가 프로토콜(권장): EvalVault에 맞춘 실행 규칙

### 5.1 기본 프로토콜: “데이터셋 → Run → 아티팩트 → 비교”
1. **데이터셋 고정**: 같은 데이터셋/버전으로 비교(실험 간 데이터 드리프트 차단)
2. **실험 단위는 `run_id`**: 모델/프롬프트/리트리버 변경마다 새로운 run 생성
3. **Auto-analyze(권장)**: 리포트+아티팩트를 자동 생성해 원인 분석 비용을 낮춤
4. **A/B 비교**: run 간 비교 리포트로 회귀를 명확히 표시 (내부 근거: `docs/handbook/CHAPTERS/03_workflows.md`)

### 5.2 프로토콜 강화: 멀티턴/고위험 도메인
- 멀티턴 RAG는 턴 기반 평가가 필요하며, 벤치마크를 분리 설계한다. ([R3])
- 법/규정/의료 등 고위험 도메인은 환각 리스크를 “품질 문제”가 아니라 “안전 문제”로 다룬다. ([R35], [R28])

### 5.3 LLM-as-judge 운영 가드레일(권장)
- Judge는 **동일 프롬프트/동일 모델/동일 샘플**로 캘리브레이션
- “판정 근거(reason)”를 아티팩트로 남겨 감사 가능하게 설계
- 정기적으로 소규모 인간평가로 judge drift를 감시 ([R16], [R33])

---

## 6. RAG 성능 분석 프레임: “증상 → 원인 → 처방”을 표준화

### 6.1 실패 유형(Taxonomy) 정의
분석의 첫 단계는 실패를 분류해 “개선 레버”로 연결하는 것이다.

1. **Retrieval miss**: 필요한 문서/근거 자체가 없음(Recall 부족) → 인덱싱/쿼리/리랭킹 개선
2. **Retrieval noise**: 컨텍스트 과다/무관 → chunk/필터링/리랭킹/하이브리드
3. **Grounding failure**: 컨텍스트와 무관한 주장 → 환각 탐지/출력 제약/검증
4. **Instruction mismatch**: 포맷/정책 위반 → 시스템 프롬프트/정책 레이어 개선
5. **Multi-turn drift**: 턴 누적으로 오해 → 대화 상태 모델/메모리 설계 개선 ([R3])

### 6.2 진단에 필요한 “최소 아티팩트”
Artifacts-first 원칙에 맞춰, 최소한 아래 산출물이 존재해야 한다.

- 입력(질문/대화 히스토리/메타데이터)
- Retrieval 결과(top-k 문서, 점수, 리랭킹 결과)
- 노이즈 진단 산출물(필터링/리랭킹 전·후 top-k 비교, 문서 유사도/점수 분포 등)
- 생성 결과(답변) + 판정 근거(가능하다면 claim-level)
- stage/trace(지연/오류/재시도)

> **탐색 규칙**: 노이즈/원인 분석은 `run_id`를 기준으로 DB 기록과 `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`을 함께 보며, 비교 분석은 `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/index.json`을 기준으로 역추적한다.

관측/트레이싱 체계가 있어야 실제 운영 문제(지연·병목)까지 연결된다. ([R18], [R19], [R20], [R33])

---

## 7. 개선 제안(Engineering): RAG 성능 개선 레버를 “실험 가능”하게 만들기

> 아래 제안은 EvalVault의 `run_id`/아티팩트/트레이싱 체계로 “변화 → 측정 → 분석”이 가능하도록 구성한다.

### 7.1 Retrieval 개선 (정확도·비용 동시 최적화)

#### A. 리랭킹(Reranking) 도입/고도화
- 리랭킹은 상위 문서 품질을 올려 **Grounding 기반 메트릭**을 직접 개선할 가능성이 높다.
- 마이크로서비스 형태 리랭킹은 비용/확장성 측면에서 운영 설계가 가능하다. ([R17])

**EvalVault 적용 포인트**
- 리랭킹 on/off를 실험 플래그로 두고 `run_id`별 비교
- 리랭킹 전/후 top-k 및 점수를 아티팩트로 저장

#### B. GraphRAG(그래프 기반 RAG) 실험
- GraphRAG는 단순 top-k 문서 묶음보다 “관계/구조”를 통해 근거를 조직화하려는 접근이다. ([R21], [R22])
- 특히 “엔티티/관계”가 중요하고 질문이 복합적인 도메인에서 가치가 커질 수 있다.

**EvalVault 적용 포인트**
- GraphRAG 구성요소(엔티티 추출/관계 구축/그래프 탐색)를 stage로 분해해 계측
- Graph 기반 컨텍스트 생성 산출물을 아티팩트로 남김

#### C. 멀티턴 평가/개선 체계
- 대화형 RAG는 턴 단위 벤치마크 및 메트릭 설계가 중요하다. ([R3])

**EvalVault 적용 포인트**
- “턴”을 테스트케이스 단위의 하위 축으로 다루거나, 턴별 stage 이벤트로 관측

---

## 8. 챗봇 하이브리드 품질 테스트 시나리오 (실행용)

### 8.1 목적
- 하이브리드(BM25 + Dense) 리트리벌이 **실제 응답 품질**을 개선하는지 검증
- `run_id` 기준으로 **요약/아티팩트/리포트** 컨텍스트가 제대로 활용되는지 확인

### 8.2 사전 준비
- 동일 데이터셋/프로필로 2회 실행
  - A: `EVALVAULT_RAG_USE_HYBRID=false` (BM25 only)
  - B: `EVALVAULT_RAG_USE_HYBRID=true` (Hybrid)
- 동일한 질문 세트(10~30개) 사용

### 8.3 CLI 실행 예시
```bash
# A: BM25 only
EVALVAULT_RAG_USE_HYBRID=false \
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness

# B: Hybrid
EVALVAULT_RAG_USE_HYBRID=true \
EVALVAULT_RAG_VECTOR_STORE=pgvector \
EVALVAULT_RAG_EMBEDDING_PROFILE=dev \
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness
```

### 8.4 검증 체크리스트
- 두 run의 `pass_rate` 차이 확인
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`에서
  - `retrieval` 관련 산출물이 기록되었는지 확인
  - 상위 컨텍스트가 질문 의도에 맞는지 샘플링 검토

### 8.5 성공 기준(권장)
- Hybrid가 BM25 대비 **pass_rate +2%p 이상** 또는
  **retrieval 관련 메트릭(precision/recall/NDCG)** 개선
- 동일 질문에 대한 **근거/답변 일관성**이 향상됨

---

### 7.2 Grounding/환각 리스크 저감 (Safety + Quality)

#### A. 환각 탐지/분류 기반 운영 가드레일
- RAG 기반 시스템에서 환각은 탐지/감시 대상이며, 운영 정책(차단/완화/재질의)과 결합된다. ([R28], [R34], [R35])

**권장 운영 패턴**
- “높은 환각 확률”이면:
  - 답변 보류 + 근거 재검색
  - 사용자에게 근거 부족 알림 + 추가 질문 유도
  - 고위험 도메인에서는 안전 문구/인간 검토 트리거

#### B. 법/규정 영역의 안전성 요구 반영
- 법적 문서/컴플라이언스는 “그럴듯함”이 아니라 “근거/정확성”이 핵심이며, 환각은 법적 리스크로 직결된다. ([R35])

---

### 7.3 평가 체계 고도화 (Metrics + Bench + Tooling)

#### A. 메트릭 체계는 “단일 지표”가 아니라 “대시보드”
- RAG 평가는 메트릭, 벤치마크, 방법론의 조합으로 접근해야 한다. ([R14], [R15])
- RAG triad류 지표는 retrieval/grounding/answer 축을 동시에 보게 해준다. ([R16])

#### B. 도구 생태계 연결(상호검증)
- 메트릭/평가 프레임워크는 다양하며, 상호검증이 회귀를 줄인다.
  - RAGAS: [R37]
  - DeepEval: [R38]
  - OpenAI Evals: [R39]
  - TruLens: [R40]
  - Phoenix: [R41]
  - Promptfoo: [R42]
  - LlamaIndex: [R43]
  - Awesome-RAG-Evaluation: [R44]

**EvalVault 관점 제안**
- EvalVault 내부 메트릭과 외부 프레임워크 산출물을 “아티팩트”로 함께 보존해, 결과 불일치 시 원인 추적 가능하게 한다.

---

### 7.4 데이터 난이도 프로파일링 + 커스텀 Judge 모델(비판적 검토)

#### A. 데이터 난이도 프로파일링: 가능하지만 “근거 데이터”가 핵심
- 난이도는 **추론 깊이/시맨틱 거리/리트리벌 난이도**와 강한 상관이 있다는 근거가 있다. ([R60], [R63], [R64])
- 하지만 IRT·PVI류 방식은 **대량의 시도 데이터(모델/사람 응답 로그)**가 있어야 안정적이다. 데이터가 부족하면 난이도 추정이 흔들린다. ([R61], [R62])
- 실제 운영에서는 “난이도 지표가 품질 문제를 설명하는지”를 먼저 검증해야 한다. 난이도 자체가 **프록시 지표**이기 때문이다.

**현실적 적용 제안(단계적)**
1. **v0 (휴리스틱 기반)**: 질의 길이, 멀티턴/멀티홉 플래그, retrieval complexity, evidence dispersion을 최소 지표로 시작
2. **v1 (정량화 강화)**: 샘플링된 운영 로그로 IRT/난이도 매트릭스 적용, 오류율 상관 검증
3. **운영**: 난이도 분포 드리프트를 KPI로 관리, 난이도 구간별 threshold를 별도 운영

#### B. 커스텀 Judge 모델: 비용 절감은 가능, “일반화”가 약점
- 경량 judge의 실용성은 검증 사례가 있다(ARES의 경량 분류기, JudgeLM의 파인튜닝). ([R65], [R66])
- 그러나 **일반화·공정성·도메인 이동성**은 GPT-4급 대비 취약하다는 실증도 존재한다. ([R68], [R67])
- LLM-as-judge는 **편향/불확실성/일관성** 이슈가 구조적으로 존재한다. ([R69], [R70], [R71])

**현실적 운영 가드레일(권장)**
- **캐스케이드 평가**: 소형 judge로 대량 처리 → 저신뢰/경계 케이스만 상위 모델로 승격
- **캘리브레이션**: 소량 인간 라벨(예: 3–5%)로 점수 보정 및 신뢰 구간 제공
- **편향 완화**: 위치/형식/지식 편향에 대한 swap/format 랜덤화 테스트
- **증분 학습**: 도메인 데이터 변화 시 재학습 대신, 우선 drift 감지 후 제한적 재학습

#### C. 파인튜닝/지식주입 기법: “평가 품질”과 직접 연결되는지 확인
- QLoRA/LoftQ/LoRA+는 **메모리 효율**을 크게 올리지만, 평가 정확도 향상은 **데이터 품질과 캘리브레이션**에 더 좌우된다. ([R72], [R73], [R74])
- LongLoRA, Cartridges, MQA는 **장문 컨텍스트/서빙 효율**에 유리하나, judge 품질 그 자체를 보장하지 않는다. ([R75], [R76], [R77])
- DPO/SLiC-HF/GaLore는 학습 안정성 또는 효율성 측면 이점이 있으나, **태스크/도메인 적합성** 검증 없이는 성능 이득이 불확실하다. ([R78], [R79], [R80])

**현실적 선택 가이드(권장)**
1. **우선순위**: QLoRA + LoRA(또는 LoRA+)로 시작하고, 데이터/평가 안정성 확보 후 확장
2. **장문 최적화는 별도 과제**: LongLoRA/Cartridges는 “응답 생성 품질” 개선과 직접 연동될 때만 적용
3. **학습 기법보다 캘리브레이션 우선**: judge 품질은 모델 크기보다 **라벨 품질/보정**이 결정적

> 결론적으로 난이도 프로파일링과 커스텀 judge는 **효과가 “조건부”**다. 운영 데이터와의 상관 검증, 캘리브레이션, 드리프트 대응이 없다면 기대 효과가 과대평가될 수 있다.

---

## 8. Observability/운영 설계: “성능 개선”을 서비스 품질로 연결

### 8.1 관측성은 ‘옵션’이 아니라 ‘품질 루프의 기반’
- RAG는 단순 API가 아니라, 검색/재랭킹/LLM 호출로 구성된 파이프라인이며, 관측 없이 운영하면 병목/비용/품질 문제의 원인을 찾기 어렵다. ([R18], [R19], [R20])

### 8.2 권장 운영 시나리오(도구 선택지)
- Langfuse 기반 평가/관측: 실험/트레이스/피드백 루프 구축 ([R18])
- Splunk 기반 E2E 관측: 운영 환경에 맞는 로그/트레이스 통합 ([R19])
- Elastic + OpenTelemetry: 트레이싱 표준화 및 수집 파이프라인 ([R20])
- 모니터링 관점 요약(실무 프레임): [R33]

### 8.3 운영 KPI(SLO) 예시(제안)
- p95 latency(전체/단계별), timeout rate, cost/run
- retrieval 단계의 hit@k 추세(드리프트 감지)
- judge agreement / human audit pass rate 추세

---

## 9. Expert Lenses(전문가 관점)로 “문서/플랫폼/운영” 품질을 끌어올리기

> 참고: 본 제안서는 handbook의 문서 운영 원칙/택소노미를 따른다. (`docs/handbook/appendix-taxonomy.md`)

### 9.1 인지심리학(Cognitive Psychology): 인지부하를 줄이는 평가/리포트 UX
- 평가지표/리포트는 “전문가에게만 유용한 대시보드”가 되기 쉽다. 초급/중급 개발자가 빠르게 결정을 내리게 하려면 인지부하를 관리해야 한다.
- 적응형 피드백/인지부하 관리 설계(AR 맥락이지만 원리 전이 가능): [R46]
- 학습 설계에서 “전문가-초보자”가 필요로 하는 정보가 다르며, 과도한 안내는 숙련자 성능을 떨어뜨릴 수 있다(전문성 역전 효과): [R47]
- 메타인지(자기점검/전략 선택) 프레임은 “실험→해석→다음 실험”의 품질을 올린다: [R50]

**EvalVault 적용 제안**
- 리포트에 “초급(요약/다음 행동)”과 “고급(아티팩트/근거/드릴다운)” 경로를 분리
- 체크리스트 기반 리뷰(근거/재현/변경 영향)를 기본 탑재

### 9.2 신경과학/인지과학(Neuroscience): 예측-오차 기반 개선 루프
- 예측 처리(Predictive Processing) 관점에서 시스템은 예측과 오차(오류 신호)를 통해 업데이트된다. RAG 품질 루프 역시 “오류 신호를 구조화”할수록 학습/개선이 빨라진다. ([R54])
- 사람의 학습·기억·주의/피드백 메커니즘 연구는 “어떤 피드백이 행동을 바꾸는가”에 힌트를 준다. ([R45], [R51], [R52], [R53], [R55])

**EvalVault 적용 제안**
- 단순 점수보다 “오류 유형(원인)”을 먼저 보여주고, 다음 액션(프롬프트/리트리벌/데이터)을 제안하는 UI/리포트 설계

### 9.3 UX/UI: 사용성 휴리스틱으로 도구를 “업무 도구”로 만들기
- Nielsen의 10가지 사용성 휴리스틱은 내부 개발 도구에도 유효하다. ([R48])
- 휴리스틱 평가 방법론을 통해 “기능은 있는데 못 쓰는” 상태를 줄인다. ([R49])

**EvalVault 적용 제안**
- run 히스토리/비교/아티팩트 탐색 흐름에 대해 정기적 휴리스틱 평가 수행
- 오류 메시지/재시도/설정 누락 안내(키/엔드포인트 등)를 “사용자 통제/복구 가능성” 원칙으로 개선

### 9.4 인지공학(Cognitive Engineering): Human-in-the-loop와 복원력
- 고위험 도메인에서 RAG는 “자동화”가 아니라 “의사결정 지원”이며, 인간 개입 지점을 설계해야 한다. ([R35], [R28])
- 인간 피드백(정답/오류 라벨)은 품질 루프의 핵심 데이터이며, 추적 가능하게 저장해야 한다. ([R33])

**EvalVault 적용 제안**
- 고위험 케이스 자동 플래그(환각 가능성 높음/근거 부족/리트리벌 실패)를 워크플로에 포함
- 피드백을 `run_id`에 강결합하여 회귀 테스트에 재사용

### 9.5 DevOps/Developer Operations: 평가를 CI·운영 게이트로
- RAG 시스템은 배포 후에도 지식/데이터/모델/프롬프트가 변하며 품질이 드리프트한다. 모니터링과 릴리즈 게이트가 필요하다. ([R33], [R18], [R19], [R20])
- 산업 적용 사례는 “효율/품질” 개선이 운영 지표와 연결될 때 지속 가능해진다는 점을 보여준다. ([R36])

**EvalVault 적용 제안**
- PR/릴리즈 단계에서 “핵심 데이터셋 회귀 평가”를 자동 수행(OpenAI Evals/Promptfoo류와 상호보완): [R39], [R42]
- 비용/지연 예산(Guardrail)을 함께 통과해야 배포 가능하도록 정책화

---

## 10. 로드맵(단기/중기/장기): 측정과 운영을 함께 올리기

> **정합성 메모**: 이 섹션의 기간/우선순위는 “실행 가능한 제안”을 위한 예시이며, 내부 우선순위/DoD는 handbook의 로드맵 챕터를 기준으로 한다. (`docs/handbook/CHAPTERS/08_roadmap.md`)

### 10.1 단기(0–4주): “측정 가능성” 확보
- KPI 기준선(baseline) 확정: triad + retrieval + ops + stability
- `run_id` 기반 A/B 비교 루틴 정착(표준 데이터셋/표준 리포트)
- 관측성 최소 세팅(OTel/트레이싱 중 1개 선택) 및 지연/비용 계측 시작 ([R20], [R18])
- 환각 고위험 규칙(간단한 룰+판정) 도입, 고위험 케이스 플래그 ([R28], [R35])
- 난이도 프로파일링 v0(휴리스틱) 도입 및 난이도 분포/오류율 상관 측정 시작 ([R64])
- judge 캐스케이드 v0: 소형 judge로 대량 처리 후 경계 케이스 상위 모델 승격

**완료 기준(예시)**
- 매 변경(모델/프롬프트/리트리버)마다 비교 리포트 1개 생성 (템플릿: run 비교 요약 + 난이도 분포 + 오류 유형 Top)
- p95 latency, cost/run 추세 대시보드 생성 (템플릿: stage별 latency 표 + 비용 분해)
- 난이도 분포 변화가 오류율 변화와 연동되는지 1회 이상 검증 (리포트에 상관 요약 포함)

### 10.2 중기(1–3개월): “원인 규명”과 “개선 레버” 체계화
- 리랭킹 실험(ON/OFF, 모델별) 및 비용-정확도 트레이드오프 정량화 ([R17])
- 멀티턴 벤치마크/평가 설계 및 운영 적용 ([R3])
- LLM-as-judge 캘리브레이션(표준 예제·다중 judge·휴먼 샘플링) 프로세스 수립 ([R16], [R15])
- 휴리스틱 평가를 통한 UI/리포트 정보 구조 개선 ([R48], [R49])
- 난이도 프로파일링 v1(RC/정량화) 적용 및 난이도 구간별 threshold 운영 ([R64])

**완료 기준(예시)**
- “실패 유형별 Top 원인”이 아티팩트로 자동 요약 (템플릿: 실패 유형 분포 + 근거 링크)
- 회귀가 발생하면 어떤 레버를 조정해야 하는지 제안이 리포트에 포함 (템플릿: 원인-레버 매핑)
- judge 캘리브레이션 리포트(인간 라벨 상관/불확실성)가 분기 1회 이상 생성 (템플릿: 상관/편향/불확실성 표)

### 10.3 장기(3–12개월): “도메인 최적화(학습)”와 “표준 확장”
- GraphRAG/구조화 근거(엔티티-관계) 기반 컨텍스트 생성의 실험·운영화 ([R21], [R22])
- Domain Memory 기반의 지속적 개선(도메인 규칙/사실 축적)과 threshold 정책 고도화(내부 축과 정렬)
- 운영 모니터링 고도화(드리프트 탐지/경보/자동 완화) ([R33])
- 오픈 표준 기반 외부 RAG 시스템 수집/분석 확대(OTel/OpenInference 계열) ([R20], [R41])

**완료 기준(예시)**
- 데이터/지식 업데이트에도 품질 회귀가 자동 감지되고, 개선 루프가 반자동으로 실행 (템플릿: 회귀 감지 리포트 + 권장 조치)

---

## 11. 범위(Non-goals) 및 리스크

### 11.1 Non-goals(명시)
- “단일 점수로 모든 것을 대표”하려는 시도(오히려 잘못된 최적화 유도)
- LLM-as-judge 결과를 인간 검증 없이 절대화(편향/드리프트 리스크) ([R16])

### 11.2 주요 리스크와 대응
- **데이터셋 대표성 부족** → 운영 로그 기반 샘플링 + 주기적 벤치 확장 ([R15], [R33])
- **관측성 부재로 병목 미해결** → 최소 OTel/트레이싱 도입 ([R20])
- **환각 리스크 과소평가** → 고위험 도메인 정책/검토 루프 강화 ([R35], [R28])

---

## 12. 내부 근거(Repo 내 문서 정렬)
- `docs/handbook/CHAPTERS/00_overview.md`: 5대 축(평가·관측·표준·학습·분석)과 `run_id` 중심 철학
- `docs/handbook/CHAPTERS/01_architecture.md`: Hexagonal(Ports & Adapters) 경계/규칙
- `docs/handbook/CHAPTERS/03_workflows.md`: 실행→저장→분석→비교, artifacts/index.json 중심 탐색 규칙
- `docs/handbook/CHAPTERS/07_ux_and_product.md`: UX/문서/제품 일관성 원칙

---

## References (외부 근거 URL, 15개 이상)

### RAG 평가/벤치마크/메트릭
- [R1] https://aclanthology.org/2025.findings-naacl.157/
- [R2] https://arxiv.org/abs/2501.03468
- [R3] https://research.ibm.com/publications/mtrag-a-multi-turn-conversational-benchmark-for-evaluating-retrieval-augmented-generation-systems
- [R4] https://arxiv.org/abs/2506.07671
- [R5] https://aclanthology.org/2025.findings-acl.875/
- [R6] https://arxiv.org/abs/2505.04847
- [R7] https://arxiv.org/abs/2502.17163
- [R8] https://arxiv.org/abs/2503.14649
- [R9] https://dl.acm.org/doi/10.1145/3695053.3731093
- [R10] https://arxiv.org/html/2503.23013
- [R11] https://openreview.net/pdf?id=56DSmK9GnS
- [R12] https://arxiv.org/abs/2506.21638
- [R13] https://arxiv.org/abs/2509.00520
- [R14] https://www.statsig.com/perspectives/rag-evaluation-metrics-methods-benchmarks
- [R15] https://www.evidentlyai.com/blog/rag-benchmarks
- [R16] https://www.snowflake.com/en/engineering-blog/benchmarking-LLM-as-a-judge-RAG-triad-metrics/
- [R23] https://arxiv.org/abs/2507.03608
- [R24] https://arxiv.org/abs/2506.15862
- [R25] https://openreview.net/pdf?id=bwGaZOVo0c
- [R27] https://arxiv.org/abs/2511.03900
- [R29] https://arxiv.org/abs/2504.14891
- [R30] https://arxiv.org/abs/2504.07803
- [R31] https://arxiv.org/abs/2511.04696
- [R51] https://arxiv.org/html/2407.19098v2
- [R52] https://arxiv.org/abs/2504.07971
- [R60] https://aclanthology.org/2025.findings-emnlp.236/
- [R61] https://aclanthology.org/2021.acl-long.92.pdf
- [R62] https://arxiv.org/abs/2110.08420
- [R63] https://arxiv.org/abs/2409.18433
- [R64] https://arxiv.org/abs/2406.03592
- [R65] https://arxiv.org/abs/2311.09476
- [R66] https://arxiv.org/abs/2310.17631
- [R67] https://aclanthology.org/2025.findings-acl.306/
- [R68] https://arxiv.org/abs/2406.18403
- [R69] https://arxiv.org/abs/2509.18658
- [R70] https://arxiv.org/abs/2412.12509
- [R71] https://llm-judge-bias.github.io/
- [R72] https://arxiv.org/abs/2305.14314
- [R73] https://arxiv.org/abs/2310.08659
- [R74] https://arxiv.org/abs/2402.12354
- [R75] https://arxiv.org/abs/2309.12307
- [R76] https://arxiv.org/abs/2506.06266
- [R77] https://arxiv.org/abs/1911.02150
- [R78] https://arxiv.org/abs/2305.18290
- [R79] https://arxiv.org/abs/2305.10425
- [R80] https://arxiv.org/abs/2403.03507

### Retrieval 개선(리랭킹/GraphRAG)
- [R17] https://developer.nvidia.com/blog/how-using-a-reranking-microservice-can-improve-accuracy-and-costs-of-information-retrieval/
- [R21] https://microsoft.github.io/graphrag/
- [R22] https://memgraph.com/blog/graphrag-vs-standard-rag-success-stories

### 환각 탐지/안전
- [R28] https://aws.amazon.com/blogs/machine-learning/detect-hallucinations-for-rag-based-systems/
- [R35] https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf

### 관측성/운영(Observability)
- [R18] https://langfuse.com/blog/2025-10-28-rag-observability-and-evals
- [R19] https://www.splunk.com/en_us/blog/artificial-intelligence/how-we-built-end-to-end-llm-observability-with-splunk-and-rag.html
- [R20] https://www.elastic.co/observability-labs/blog/openai-tracing-elastic-opentelemetry
- [R33] https://research.aimultiple.com/rag-monitoring/
- [R36] https://aws.amazon.com/solutions/case-studies/georgia-pacific-optimizes-operator-efficiency-case-study

### 평가/관측 도구 생태계(레퍼런스 구현)
- [R37] https://github.com/vibrantlabsai/ragas
- [R38] https://github.com/confident-ai/deepeval
- [R39] https://github.com/openai/evals
- [R40] https://github.com/truera/trulens
- [R41] https://github.com/Arize-ai/phoenix
- [R42] https://github.com/promptfoo/promptfoo
- [R43] https://github.com/run-llama/llama_index
- [R44] https://github.com/YHPeter/Awesome-RAG-Evaluation

### 인지심리/UX/신경과학(Expert Lenses 근거)
- [R45] https://pmc.ncbi.nlm.nih.gov/articles/PMC11852728/
- [R46] https://resolve.cambridge.org/core/journals/design-science/article/designing-adaptive-feedback-systems-for-managing-cognitive-load-in-augmented-reality/B2F5BA55D92F60D587BFDB9EE776BE22
- [R47] https://www.innerdrive.co.uk/blog/expertise-reversal-effect-scaffolding/
- [R48] https://www.nngroup.com/articles/ten-usability-heuristics/
- [R49] https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/
- [R50] https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/metacognition
- [R54] https://marksprevak.com/pdf/paper/SprevakSmith--Introduction%20to%20Predictive%20Processing.pdf
- [R53] https://www.nature.com/articles/s41467-024-50388-9
- [R55] https://www.nature.com/articles/s41598-021-95603-5
- [R56] https://pmc.ncbi.nlm.nih.gov/articles/PMC8389058/
- [R57] https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3002373
- [R58] https://link.springer.com/article/10.1007/s11023-024-09701-0
- [R59] https://link.springer.com/article/10.1145/3544548.3581197
- [R26] https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2025.1635381/full
