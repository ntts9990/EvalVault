PRD: LLM 평가 노이즈 분석 통합 프레임워크 (LENA)

문서 버전: v1.0 (재작성)
작성 목적: 통계적으로 올바른 노이즈 분해 + 검정 + 샘플 사이즈 의사결정까지 포함한 “실전형” LLM 평가 신뢰도 모듈 PRD

⸻

1장: LENA 도입 제안 — LLM 평가 신뢰도(Noise) 분석 모듈

부제: 평가 결과에 오차막대(CI)·유의성·노이즈 분해·N/K 추천을 제공하여 “진짜 개선”을 빠르게 판정

현재 문제(의사결정 리스크)
	•	동일 설정에서도 seed/temperature에 따라 점수가 흔들림 → 결론이 뒤집힘
	•	작은 개선(≈0.5~2%p)을 구분하기 어려워 거짓 양성/거짓 음성 발생
	•	무엇을 늘려야 할지(N? K?) 근거가 없어 평가 비용·시간이 증가

LENA가 하는 일(핵심 아이디어)
	•	Total = Data + Prediction 노이즈 분해(총분산 법칙 기반)
	•	Paired 비교(동일 질문)로 데이터 노이즈 상쇄 → 검정력 상승
	•	K회 예측 평균화로 prediction 노이즈 감소
	•	출력: diff, CI, p-value, MDE + (N,K) 추천

기대 효과(바로 쓰는 가치)
	•	“오차막대”가 있는 결과 → 회의/리뷰에서 신뢰 가능한 결론 제시
	•	실험 반복·재평가 감소 → 개발 iteration 속도 상승
	•	목표 신뢰도 대비 최소 비용의 N/K 선택 → 평가 비용 최적화

MVP 산출물(한 줄 요약):
① A/B 비교 리포트(JSON+UI) ② Noise breakdown(Data vs Prediction) ③ (N,K) 추천 + 예상 비용/시간

⸻

2장: 개발 범위, ROI 프레임, 리스크/완화(의사결정 패키지)

부제: MVP는 2~3주: 분석 엔진 + (N,K) 추천 + UI 위젯까지 “바로 쓰게” 제공

MVP 범위(2~3주)
	•	입력: 기존 평가 로그/CSV/JSONL → EvalMatrix(N×K) 생성
	•	분석: Unpaired/Paired 노이즈 + small-K 보정(일관성 보장)
	•	모드: single / mean-K / expected(SE 토글)
	•	UI 위젯 3종: (1) diff+CI (2) noise breakdown (3) N/K 추천

ROI 계산 프레임(예시/템플릿)
	•	평가 비용(대략): Cost ≈ (#Evaluator) × N × K × (API 호출 단가)
	•	목표: MDE(예: 1%p)·power(0.8)·alpha(0.05) 달성에 필요한 최소 비용 (N,K) 추천
	•	파일럿 1회(N0,K0)로 data/pred 노이즈를 추정 → 비용 최적화
	•	효과: “무작정 N만 증가” 또는 “운 좋은 실험 채택”을 방지

리스크 & 완화(신뢰도 확보)
	•	메트릭 타당도(만족도 반영) 문제: LENA는 reliability, validity는 별도 모듈(인간 라벨/보정) 로드맵
	•	LLM-as-judge 편향/오류: bootstrap·sign test 옵션 + (확장) 캘리브레이션
	•	All-pairs 다중비교: FDR(BH) 보정 기본 탑재
	•	중간중단(실시간 모니터링): fixed-horizon 기본, 순차검정은 정책 포함 후 제공

결정 요청(슬라이드 하단):
(1) MVP 개발 승인(2~3주) (2) 파일럿 평가 1회 예산(N0,K0) (3) 결과 기반으로 Phase2(bootstrap/all-pairs) 착수 여부 결정

⸻

60초 발표 스크립트(그대로 읽어도 됨)

“지금 LLM 평가에서 가장 큰 문제는 ‘성능이 아니라 평가의 신뢰도’입니다. 같은 설정도 seed/temperature 때문에 점수가 흔들려서, 작은 개선은 안 보이거나 우연을 개선으로 채택하는 일이 생깁니다. LENA는 평가 점수에 오차막대(CI)와 유의성(p-value)을 붙이고, 노이즈를 데이터 노이즈와 예측 노이즈로 분해해 ‘N을 늘릴지 K를 늘릴지’를 근거 있게 추천합니다. MVP는 2~3주로, 기존 평가 로그를 입력받아 A/B 비교 리포트와 노이즈 breakdown, (N,K) 추천을 UI에 바로 제공하는 범위입니다. 결론적으로 평가를 더 많이 하는 게 아니라 더 똑똑하게 해서 비용과 의사결정 리스크를 동시에 줄이겠습니다.”

⸻

0. 문서 메타데이터
	•	제품명: LLM Eval Noise Analyzer (LENA)
	•	모듈명(우리 시스템 내): eval_reliability.lena
	•	오너:
	•	PM/기획: (TBD)
	•	Tech Lead: (TBD)
	•	대상 시스템:
	•	기존 평가 웹 UI(사내) + 평가 실행 파이프라인(LLM/RAG) + 결과 저장소(DB/파일)
	•	릴리즈 목표:
	•	MVP: A/B 비교의 “신뢰구간·유의성·노이즈 분해·N/K 추천” 제공
	•	확장: All-pairs, Bootstrap, 메타 분석, 실시간 모니터링

⸻

1. 개요

1.1 한 줄 요약

LENA는 LLM 평가 결과에 “오차막대(error bar)”를 달아, 개선이 진짜인지/우연인지와 다음 실험에서 N/K를 얼마나 더 모아야 하는지까지 알려주는 통합 프레임워크다.

1.2 문제 정의

현재 LLM 평가(정확도, LLM-as-judge 점수, RAGAS 등)는 다음 문제를 겪는다.
	•	동일 설정에서도 seed/temperature/샘플링 때문에 점수가 흔들려 **개선이 있어도 안 보이거나(거짓 음성), 우연을 개선으로 착각(거짓 양성)**함
	•	“질문 샘플링(데이터 노이즈)”과 “예측 샘플링(예측 노이즈)”이 섞여 있어 무엇을 늘려야(N? K?) 신뢰도가 오르는지 판단 불가
	•	모델 비교(Inter)와 설정 비교(Intra)가 분리돼 있어 분석 체계가 일관되지 않음

1.3 목표

LENA는 평가 노이즈를 다음 3요소로 분해하고(총분산 분해), 비교 분석을 표준화한다.
	•	Prediction noise: 같은 질문에서 샘플링/파이프라인 랜덤성(생성/검색/심사)으로 점수가 달라지는 변동성
	•	Data noise: 질문 샘플이 바뀌면 평균 성능이 달라지는 변동성(질문 난이도 분포)
	•	Total noise: 위 둘이 합쳐진 전체 불확실성

그리고 아래 결과물을 만든다.
	•	A/B 평균 차이 + 신뢰구간(CI) + p-value + 유의성 판단
	•	노이즈 분해(예측 vs 데이터)와 paired 이득(상관)
	•	목표 MDE/검정력에 맞는 권장 샘플 크기(N 질문 수, K 예측 반복 수) 및 비용 최적화

1.4 비목표(Non-goals)
	•	“메트릭이 사용자 만족도를 얼마나 잘 반영하는가(타당도, validity)” 자체를 자동으로 보장하지 않는다.
	•	단, LENA는 메트릭의 **신뢰도(reliability)**를 정량화한다.
	•	모델 성능을 올리는 알고리즘(학습/추론 개선)을 직접 제공하지 않는다.
	•	온라인 A/B(트래픽 기반 실험) 자체를 대체하지 않는다. (오프라인 평가 신뢰도 모듈)

1.5 성공 지표(Success Metrics)

MVP 성공 기준(정량/정성 혼합):
	•	(정량) 동일 데이터/설정에서 “개선 유무 판단”의 재현성 향상
	•	예: 동일 A/B 실험을 10회 반복했을 때 결론 뒤집힘 비율 ↓
	•	(정량) 동일 목표 MDE에서 필요한 평가 비용(총 API 호출 수) ↓
	•	“무작정 N만 늘리기” 대비 비용 절감
	•	(정성) 엔지니어/리서처가 “이 결과는 믿고 의사결정해도 된다”라고 느끼는 수준의 리포트/UX 제공

⸻

2. 핵심 개념 및 용어 정의

2.1 Evaluator(평가 주체) 추상화

LENA에서 비교 단위는 Evaluator다.

Evaluator = (Model, Config, Prompt, Pipeline, Metric)

	•	Model: gpt-4o, claude, llama 등
	•	Config: temperature, top_p, max_tokens, seed 정책 등
	•	Prompt: system/user 템플릿
	•	Pipeline: (선택) RAG 파이프라인(리트리버/랭커/청킹 등)
	•	Metric: accuracy / exact match / RAGAS submetric / LLM-as-judge 점수 등

2.2 N과 K의 의미(매우 중요)
	•	N: 질문(데이터 포인트) 개수
	•	K: 동일 질문에 대해 반복 예측(샘플링) 횟수

LENA의 모든 통계는 **“질문 단위 평균(질문별 K회 평균)을 다시 N개 질문에 대해 평균낸 값”**을 평가 점수로 본다.
즉, NK를 독립 표본으로 간주하지 않는다.(이걸 잘못하면 유의성이 과대추정된다)

2.3 비교 유형(Inter/Intra 통합)
	•	Inter-Model: Model A vs Model B
	•	Intra-Model: 동일 모델에서 Config/Prompt/RAG 설정 A vs B
	•	Custom: 사용자가 임의로 정의한 Evaluator A vs B

2.4 평가 모드(표준오차 계산 방식)

LENA는 SE(표준오차) 계산/표현을 다음 3가지 모드로 구분한다.
	•	single: 질문당 1회 예측 기준의 불확실성 (리더보드/벤치마크 기본 모드)
	•	mean_k: 질문당 K회 예측을 평균낸 점수의 불확실성 (튜닝/실험 추천 기본값)
	•	expected: K→∞ 가정(예측 노이즈가 완전히 평균화된 “이론적 하한”)

UI에서 이 모드를 명확히 토글할 수 있어야 한다.

⸻

3. 사용자/페르소나 및 주요 유즈케이스

3.1 목표 사용자
	•	ML/AI 엔지니어(튜닝/모델 비교)
	•	RAG 시스템 개발자(검색/프롬프트/랭커 비교)
	•	LLM 평가 담당자(벤치마크 운영)
	•	연구원(실험 설계, 통계 검정)

3.2 핵심 유즈케이스
	1.	프롬프트 A/B: “이 프롬프트 개선이 진짜인가?”
	2.	RAG 설정 A/B: “chunk size/recall@k/랭커 바꿨더니 개선인가?”
	3.	모델 A vs B: “모델 변경 시 성능 차이가 유의미한가?”
	4.	샘플 사이즈 결정: “MDE 1%p를 잡으려면 N과 K를 얼마로?”
	5.	벤치마크 신뢰도 점검: “이 평가셋은 노이즈가 원래 큰가?”

⸻

4. 기능 요구사항

4.1 Must Have (MVP)

ID	기능	설명
M01	다중 예측 수집	동일 질문에 대해 K회 예측 수집(시드/샘플링 정책 포함)
M02	노이즈 분해	Total/Data/Prediction 노이즈 분해(총분산 기반)
M03	Paired 분석	동일 질문 기반 A/B 비교(질문 정렬/매칭 강제)
M04	유의성/신뢰구간	평균, 차이, CI, p-value, 유의성, 효과크기
M05	평가 모드 지원	single / mean_k / expected 모드별 SE 제공
M06	N/K 추천	목표 MDE, power, alpha에 따른 (N,K) 추천 + 비용 추정
M07	결과 시각화(핵심 3종)	(1) CI 바, (2) Noise breakdown, (3) SE vs K/N 곡선

4.2 Should Have (확장 1)

ID	기능	설명
S01	Bootstrap CI	paired bootstrap 기반 CI/분포 시각화(강건 옵션)
S02	Sign test	paired sign test p-value(이진/비정규 분포 대응)
S03	All-Pairs 분석	다수 Evaluator의 모든 쌍 비교
S04	다중비교 보정	All-Pairs 시 FDR(BH) 또는 Bonferroni 제공
S05	메타 분석	여러 평가셋 결과를 통합(z-score 결합 등)
S06	결과 캐시/재현성	실험 버전/데이터 해시/코드 커밋 저장

4.3 Could Have (확장 2)

ID	기능	설명
C01	순차 모니터링	평가 진행 중 CI 수렴 모니터링(정책 포함)
C02	노이즈 이상치 탐지	특정 질문/모델에서 비정상 변동 감지
C03	비용 최적화	API 비용/속도 제약 하 Pareto 최적 (N,K)
C04	LLM-as-judge 분해(선택)	judge seed 반복 시 “judge noise” 별도 분해(계층 분해)


⸻

5. 기술 설계(Technical Spec)

5.1 데이터 구조(권장 스키마)

5.1.1 Config / Question / Prediction

from dataclasses import dataclass
from typing import Dict, Optional, List, Literal
import numpy as np

MetricType = Literal["binary", "continuous"]
SEMode = Literal["single", "mean_k", "expected"]

@dataclass
class EvaluatorConfig:
    evaluator_id: str
    model_name: str
    model_version: Optional[str] = None

    # prompt
    system_prompt: Optional[str] = None
    prompt_template_id: Optional[str] = None

    # sampling
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1024
    seed_supported: bool = True  # provider별 현실 반영

    # rag
    rag_config: Optional[Dict] = None

    # metric
    metric_name: str = "accuracy"
    metric_type: MetricType = "binary"
    metric_bounds: Optional[tuple] = (0.0, 1.0)

    metadata: Optional[Dict] = None

@dataclass
class EvalQuestion:
    question_id: str
    prompt: str
    expected_answer: Optional[str] = None
    metadata: Optional[Dict] = None  # difficulty, category ...

@dataclass
class PredictionResult:
    question_id: str
    evaluator_id: str
    seed: int
    response: str
    metric_value: float
    latency_ms: Optional[float] = None
    token_count: Optional[int] = None
    # RAG contexts, judge info, etc.
    extra: Optional[Dict] = None

5.1.2 평가 행렬(EvalMatrix)
	•	핵심 원칙: 질문(N) × 반복예측(K)

@dataclass
class EvalMatrix:
    evaluator_id: str
    question_ids: List[str]          # length N
    seeds: List[int]                 # length K
    metrics: np.ndarray              # shape (N, K)  (float)

    def validate(self) -> None:
        assert self.metrics.shape == (len(self.question_ids), len(self.seeds))


⸻

5.2 노이즈 분해(수학/추정량) – “small-K 보정 포함”이 필수

5.2.1 정의(기본)
질문 x, 랜덤성 \epsilon에서 메트릭 A(x,\epsilon)
	•	Data variance: \mathrm{Var}_x(\mathbb{E}_\epsilon[A])
	•	Prediction variance: \mathbb{E}_x(\mathrm{Var}_\epsilon[A])
	•	Total variance: \mathrm{Var}_{x,\epsilon}(A)=\text{Data}+\text{Prediction}

5.2.2 Unpaired 추정량(단일 Evaluator)
입력: A ∈ R^{N×K}
	•	b = \frac{1}{K-1} \cdot \mathrm{mean}(\mathrm{var}(A_i))  (질문별 분산 기반 small-K 보정)
	•	data_var = var(mean(A_i)) − b
	•	pred_var = mean(var(A_i)) + b
	•	total_var = var(A)

중요: pred_var에 +b가 반드시 들어가야 Total=Data+Pred 일관성이 맞는다.

5.2.3 Paired 추정량(A vs B)
입력: A ∈ R^{N×KA}, B ∈ R^{N×KB}
	•	b = \frac{1}{KA-1}\mathrm{mean}(\mathrm{var}(A_i)) + \frac{1}{KB-1}\mathrm{mean}(\mathrm{var}(B_i))
	•	data_var(diff) = var(mean(A_i) − mean(B_i)) − b
	•	pred_var(diff) = mean(var(A_i)+var(B_i)) + b
	•	total_var(diff) = var(A)+var(B) − 2·cov(mean(A_i), mean(B_i))

⸻

5.3 표준오차(SE)와 비교 검정 로직(모드별)

5.3.1 평균 성능(질문 단위 평균)
평균 점수는 항상:
	•	질문별 평균: \bar{A}_i = \frac{1}{K}\sum_k A_{i,k}
	•	전체 평균: \bar{A} = \frac{1}{N}\sum_i \bar{A}_i

5.3.2 SE 모드 정의(중요: mean_k에서 pred/K 반영)
	•	expected: \mathrm{SE} = \sqrt{\frac{\text{data\_var}}{N}}
	•	mean_k: \mathrm{SE} = \sqrt{\frac{\text{data\_var} + \text{pred\_var}/K}{N}}
	•	single: \mathrm{SE} = \sqrt{\frac{\text{total\_var}}{N}}

Paired(diff)도 동일하게:
	•	expected: \sqrt{\frac{\text{data\_var(diff)}}{N}}
	•	mean_k: \sqrt{\frac{\text{data\_var(diff)} + \text{pred\_var(diff)}/K}{N}} (KA=KB=K 가정)
	•	single: \sqrt{\frac{\text{total\_var(diff)}}{N}}

MVP에서는 KA=KB를 강제(비교 실행기에서 동일 K로 실행)하는 것을 권장.
KA≠KB 지원은 확장 기능으로 포함.

5.3.3 유의성 검정 기본(빠른 경로)
	•	z-test (양측):
	•	z = \frac{\Delta}{SE}
	•	p = 2(1-\Phi(|z|))

5.3.4 강건 옵션(Should)
	•	paired bootstrap CI(질문 resampling)
	•	sign test(질문별 A>B 여부로)

⸻

5.4 최소 탐지 효과(MDE) 및 샘플 사이즈 추천

5.4.1 MDE 근사(양측, 정규 근사)
목표 power=β(예: 0.8), 유의수준 α=0.05

\mathrm{MDE} \approx (z_{1-\alpha/2} + z_{\text{power}})\cdot SE

5.4.2 추천 알고리즘(제품 로직)
	1.	작은 파일럿으로 (N0,K0) 실행
	2.	data_var, pred_var 추정
	3.	후보 (N,K) 격자 탐색:
	•	예상 SE, MDE 계산
	•	비용(총 API 호출 수) = N×K×(#evaluator)
	4.	목표 MDE 만족하는 최소 비용 조합 추천 + Pareto(비용 vs 신뢰도) 표시

⸻

6. 핵심 분석 API 설계(라이브러리)

6.1 분석 결과 데이터 구조

from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class NoiseComponents:
    total_var: float
    data_var: float
    pred_var: float
    N: int
    K: int

    def se(self, mode: SEMode) -> float:
        if mode == "single":
            return (self.total_var / self.N) ** 0.5
        if mode == "expected":
            return (self.data_var / self.N) ** 0.5
        # mean_k
        return ((self.data_var + self.pred_var / self.K) / self.N) ** 0.5

@dataclass
class PairedNoiseComponents:
    total_var: float
    data_var: float
    pred_var: float
    cov_mean: float
    corr_mean: float
    N: int
    K: int

    def se(self, mode: SEMode) -> float:
        if mode == "single":
            return (self.total_var / self.N) ** 0.5
        if mode == "expected":
            return (self.data_var / self.N) ** 0.5
        return ((self.data_var + self.pred_var / self.K) / self.N) ** 0.5

@dataclass
class ComparisonResult:
    evaluator_a_id: str
    evaluator_b_id: str

    mean_a: float
    mean_b: float
    mean_diff: float

    se_mode: SEMode
    se: float
    z_score: float
    p_value: float
    ci_95: Tuple[float, float]
    is_significant: bool

    noise_a: NoiseComponents
    noise_b: NoiseComponents
    paired_noise: PairedNoiseComponents

    mde_80_power: float
    effect_size: Optional[float] = None

6.2 핵심 클래스(LENA)
	•	analyze_noise(eval_matrix) -> NoiseComponents
	•	compare(eval_a, eval_b, se_mode="mean_k") -> ComparisonResult
	•	recommend_sample_size(target_mde, power=0.8, alpha=0.05, cost_model=...) -> (N,K)

⸻

7. 평가 실행 모듈(Eval Runner) 요구사항

7.1 실행기 설계 원칙
	•	질문×seed 전체를 한 번에 task 리스트로 만들지 말고, 배치/스트리밍 실행(메모리 보호)
	•	질문/seed 인덱스는 dict로 O(1) 매핑
	•	재시도/타임아웃/레이트리밋 대응
	•	결과는 row-level로 저장 후, 행렬은 필요할 때만 구성(대규모 처리)

7.2 Evaluator 인터페이스
	•	predict(question, seed)는 항상 PredictionResult 반환
	•	compute_metric()는 플러그인(accuracy, rouge, ragas, judge 등)

⸻

8. UI/UX 요구사항(기존 웹 UI에 추가되는 화면 기준)

8.1 A/B 비교 화면(필수)
	•	상단: meanA, meanB, diff
	•	모드 토글: single / mean_k / expected
	•	CI bar + p-value + 유의성 배지
	•	Noise breakdown(데이터 vs 예측)
	•	(N,K) 추천 박스: 목표 MDE slider + 비용/시간 추정

8.2 노이즈 탐색 화면(필수)
	•	Evaluator 단독: total/data/pred 추정치 + SE 곡선(K 변화)
	•	질문 히트맵(선택): 질문별 평균 점수(난이도 정렬)

8.3 All-Pairs 화면(Should)
	•	모든 쌍 결과 테이블 + FDR 보정 후 유의성 표시
	•	필터: “의미 없는 비교 제거”, “근접 성능만 보기”

⸻

9. 인터페이스(CLI/REST)

9.1 CLI (MVP)

# A/B 비교
lena compare \
  --eval-a eval_a.jsonl \
  --eval-b eval_b.jsonl \
  --se-mode mean_k \
  --alpha 0.05 \
  --out result.json

# 단일 노이즈 분석
lena noise \
  --eval eval_a.jsonl \
  --out noise.json

# 샘플 사이즈 추천
lena recommend \
  --target-mde 0.01 \
  --power 0.8 \
  --alpha 0.05 \
  --pilot noise.json \
  --out recommend.json

9.2 REST(선택)
	•	/compare, /noise, /recommend, /all_pairs
	•	결과는 ComparisonResult JSON 직렬화

⸻

10. 비기능 요구사항(NFR)

10.1 성능
	•	분석(노이즈/비교): N=10,000, K=50에서 < 1초(NumPy 벡터화 전제)
	•	실행기: 동시 호출(최소 10), 레이트리밋/재시도 지원

10.2 신뢰성/정확성
	•	small-K 보정 포함 분해식 일관성(허용 오차 내): |total - (data+pred)| < tol
	•	bootstrap CI와 분석식 CI 폭이 특정 조건에서 근접(테스트로 보장)

10.3 보안/프라이버시
	•	응답 텍스트/컨텍스트 저장 시 개인정보/민감정보 마스킹 옵션
	•	실험 로그에 모델/프롬프트/데이터 해시를 남겨 재현성 확보

⸻

11. 시각화 요구사항(차트 스펙)

MVP 필수 3종:
	1.	Diff + CI 바 차트(A/B 비교)
	2.	Noise breakdown bar/donut(Data vs Prediction)
	3.	SE 곡선: x축 K(또는 N), y축 SE/MDE

Should:
	•	Bootstrap 분포(히스토그램 + CI)
	•	질문 히트맵(난이도 정렬)

⸻

12. 테스트 요구사항

12.1 단위 테스트(MVP 필수)
	•	분해식: Total ≈ Data + Prediction (K>1에서)
	•	small-K 보정 유무에 따른 상대 오차 비교(보정이 개선해야 함)
	•	SE 모드별 단조성:
	•	K 증가 → mean_k SE 감소
	•	expected SE ≤ mean_k SE ≤ single SE

12.2 시뮬레이션 테스트(강력 추천)
	•	Bernoulli(정답/오답) 생성 모델에서 이론적 SE와 근접
	•	paired bootstrap CI와 분석식 CI 비교

12.3 통합 테스트
	•	Inter-model 비교 end-to-end
	•	Intra-model(프롬프트) 비교 end-to-end
	•	CSV/JSONL 입력 → 분석 → UI 표시까지 smoke test

⸻

13. 구현 로드맵(권장)

Phase 1: Core + Compare + Recommend (MVP)
	•	데이터 로더(JSONL/CSV) + EvalMatrix 생성
	•	NoiseAnalyzer(보정 포함) + compare(se_mode 지원)
	•	샘플 사이즈 추천(격자 탐색)
	•	UI 위젯 3종

Phase 2: 강건 통계 + All-Pairs
	•	bootstrap / sign test
	•	all-pairs + FDR
	•	결과 캐싱/재현성 메타데이터

Phase 3: 운영 기능
	•	실시간 모니터링(정책 포함)
	•	비용 최적화/파레토 프론티어
	•	(선택) judge noise 분해

⸻

14. 리스크 및 대응
	•	다중비교(All-Pairs)로 false positive 증가
→ FDR(BH) 기본 탑재, UI에서 “보정 후 유의”만 강조
	•	중간중간 결과 보고 멈추면(optional stopping) 유의성 왜곡
→ 기본은 fixed-horizon, 순차 모니터링은 정책(α-spending) 명시 후 제공
	•	LLM provider의 seed 비결정성/미지원
→ seed_supported 플래그/경고, 실험 재현성 레벨을 UI에 표시
	•	메트릭 타당도(사용자 만족도 반영)는 별도 문제
→ LENA는 reliability 모듈임을 명시 + (확장) 인간 라벨 캘리브레이션 모듈 로드맵

⸻

15. 부록: “개발자가 바로 구현할 수 있는” 핵심 함수 요약(예시 코드)

아래는 PRD 정의가 실제로 구현 가능한 형태임을 보이기 위한 “reference implementation skeleton”이다.

import numpy as np
from scipy import stats

def _small_k_b(var_per_q: np.ndarray, K: int) -> float:
    if K <= 1:
        return float("nan")
    return float(np.mean(var_per_q) / (K - 1))

def analyze_unpaired(A: np.ndarray) -> NoiseComponents:
    N, K = A.shape
    vq = np.var(A, axis=1, ddof=0)
    b = _small_k_b(vq, K)
    data_var = float(np.var(np.mean(A, axis=1), ddof=0) - b) if K > 1 else float(np.var(np.mean(A, axis=1), ddof=0))
    pred_var = float(np.mean(vq) + b) if K > 1 else float("nan")
    total_var = float(np.var(A, ddof=0))
    if K > 1:
        data_var = max(0.0, data_var)
        pred_var = max(0.0, pred_var)
    return NoiseComponents(total_var=total_var, data_var=data_var, pred_var=pred_var, N=N, K=K)

def analyze_paired(A: np.ndarray, B: np.ndarray) -> PairedNoiseComponents:
    N, KA = A.shape
    NB, KB = B.shape
    assert N == NB
    meanA = np.mean(A, axis=1)
    meanB = np.mean(B, axis=1)

    vAq = np.var(A, axis=1, ddof=0)
    vBq = np.var(B, axis=1, ddof=0)
    b = (np.mean(vAq) / (KA-1) + np.mean(vBq) / (KB-1)) if (KA>1 and KB>1) else float("nan")

    data_var = float(np.var(meanA - meanB, ddof=0) - b) if (KA>1 and KB>1) else float(np.var(meanA - meanB, ddof=0))
    pred_var = float(np.mean(vAq + vBq) + b) if (KA>1 and KB>1) else float("nan")

    cov_mean = float(np.cov(meanA, meanB, ddof=0)[0,1])
    corr_mean = float(np.corrcoef(meanA, meanB)[0,1])
    total_var = float(np.var(A, ddof=0) + np.var(B, ddof=0) - 2.0 * cov_mean)

    if KA>1 and KB>1:
        data_var = max(0.0, data_var)
        pred_var = max(0.0, pred_var)

    # MVP에서는 KA==KB==K 강제 권장
    K = min(KA, KB)
    return PairedNoiseComponents(
        total_var=total_var, data_var=data_var, pred_var=pred_var,
        cov_mean=cov_mean, corr_mean=corr_mean, N=N, K=K
    )

def compare(A: np.ndarray, B: np.ndarray, alpha=0.05, se_mode: SEMode="mean_k") -> tuple[float,float,tuple,bool]:
    paired = analyze_paired(A, B)
    mean_diff = float(np.mean(A) - np.mean(B))
    se = paired.se(se_mode)
    z = mean_diff / se if se > 0 else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    zc = stats.norm.ppf(1 - alpha/2)
    ci = (mean_diff - zc*se, mean_diff + zc*se)
    return mean_diff, p, ci, (p < alpha)


⸻
