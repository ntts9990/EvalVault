# EvalVault 확장 제안서: 데이터 난이도 프로파일링 + 평가 전문 LLM 구축

**버전**: 1.0
**작성일**: 2026년 1월 17일
**대상**: RAG 시스템 품질 관리 체계 고도화를 검토하는 의사결정자

---

## Executive Summary

### 현재 Pain Point (정량화)

| 문제 | 현황 | 비즈니스 영향 |
|------|------|---------------|
| **LLM-as-judge 비용** | 평가 1건당 ₩50-150 (GPT-4o 기준) | 월 10만 건 평가 시 **₩5,000만-1.5억/월** |
| **평가 속도** | 건당 3-8초 (API 호출) | 1만 건 평가에 **8-22시간** 소요 |
| **판정 일관성** | 동일 케이스 재평가 시 10-15% 불일치 | 품질 기준선 신뢰도 저하 |
| **원인 불명** | "점수가 낮다"만 알고 "왜"를 모름 | 개선 방향 설정 불가, 시행착오 반복 |

### 제안 솔루션의 기대 효과

| 지표 | As-Is | To-Be | 개선율 |
|------|-------|-------|--------|
| 평가 비용/건 | ₩50-150 | ₩0.5-2 | **97-99% 절감** |
| 평가 속도/건 | 3-8초 | 0.05-0.2초 | **40-160배 향상** |
| 판정 일관성 | 85-90% | 95%+ | **5-10%p 향상** |
| 원인 진단 가능 | 불가능 | 자동 분류 | **신규 역량** |

---

## 1. 문제 정의: 왜 지금 이것이 필요한가

### 1.1 LLM-as-judge의 구조적 한계

현재 RAG 평가 체계의 표준인 LLM-as-judge는 다음 문제를 내재합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM-as-judge 비용 구조                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [질문] + [컨텍스트 k개] + [답변] + [평가 프롬프트]              │
│         ↓                                                       │
│  평균 입력 토큰: 2,000-4,000 tokens                             │
│  평균 출력 토큰: 200-500 tokens (reasoning 포함)                │
│         ↓                                                       │
│  GPT-4o 기준: $2.5/1M input + $10/1M output                     │
│  = 건당 $0.007-0.015 (₩10-22)                                   │
│         ↓                                                       │
│  3개 메트릭(Faithfulness, Relevancy, Groundedness) 평가 시      │
│  = 건당 $0.021-0.045 (₩30-66)                                   │
│         ↓                                                       │
│  + 재시도/에러 처리 오버헤드 20%                                │
│  = 실질 건당 ₩36-80                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**월간 비용 시뮬레이션** (Hy-NuRI 규모 기준):

| 시나리오 | 일일 평가량 | 월간 평가량 | 월 비용 (GPT-4o) |
|----------|------------|-------------|------------------|
| 개발 단계 | 1,000건 | 30,000건 | ₩1,080만-2,400만 |
| 운영 단계 | 5,000건 | 150,000건 | ₩5,400만-1.2억 |
| 확장 단계 | 20,000건 | 600,000건 | ₩2.16억-4.8억 |

### 1.2 "데이터 탓 vs 모델 탓" 구분 불가 문제

현재 평가 체계의 가장 큰 맹점은 **실패 원인 귀속**이 불가능하다는 점입니다.

```
시나리오: Faithfulness 점수가 0.65로 하락

현재 진단 가능 범위:
├── "점수가 낮다" ← 이것만 알 수 있음
└── "왜?" ← 알 수 없음
    ├── 질문 자체가 모호했나?
    ├── 검색된 컨텍스트가 부적절했나?
    ├── 정답 근거가 원래 없는 데이터였나?
    ├── 모델이 환각을 생성했나?
    └── 평가 LLM이 오판했나?
```

**실제 발생하는 비효율**:

1. **잘못된 최적화 방향**: 모델을 튜닝했지만, 실제 문제는 데이터 품질이었음
2. **과잉 엔지니어링**: 쉬운 질문에도 복잡한 파이프라인 적용
3. **과소 대응**: 어려운 질문을 "모델 한계"로 치부하고 방치

### 1.3 원전 도메인 특수 요구사항

KHNP Hy-NuRI 프로젝트 맥락에서 추가 고려사항:

| 요구사항 | 일반 RAG | 원전 도메인 RAG |
|----------|----------|-----------------|
| 환각 허용도 | 낮음 | **제로 톨러런스** |
| 평가 추적성 | 권장 | **의무** (감사 대응) |
| 응답 근거 | 선택 | **필수** (법적 책임) |
| 평가 빈도 | 배포 시 | **상시** (드리프트 감시) |

---

## 2. 솔루션 1: 데이터 난이도 프로파일링 시스템

### 2.1 핵심 개념

**"모든 테스트 케이스는 평등하지 않다"**

데이터 난이도를 사전에 측정하면:
- 점수 하락 시 "원래 어려운 케이스가 늘었는지" 즉시 확인
- 난이도별 차별화된 품질 기준(threshold) 적용
- 개선 우선순위 결정 (Easy 실패 → 즉시 수정, Hard 실패 → 전략적 접근)

### 2.2 난이도 측정 프레임워크

#### 2.2.1 측정 축 정의

```
┌─────────────────────────────────────────────────────────────────┐
│              Data Difficulty Scoring Framework                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  총점 = Σ(축별 점수 × 가중치) / Σ(가중치)                       │
│                                                                 │
│  ┌─────────────┬────────┬──────────────────────────────────┐   │
│  │ 측정 축     │ 가중치 │ 측정 방법                        │   │
│  ├─────────────┼────────┼──────────────────────────────────┤   │
│  │ 질의 복잡도 │ 0.20   │ 조건절 수, 토큰 수, 암묵 의도   │   │
│  │ 근거 산포도 │ 0.25   │ 정답 근거 chunk 수, 문서 수     │   │
│  │ 추론 깊이   │ 0.25   │ hop 수 (0/1/2+)                 │   │
│  │ 어휘 불일치 │ 0.15   │ 질의-문서 임베딩 유사도 역수    │   │
│  │ 노이즈 밀도 │ 0.15   │ 유사-오답 문서 비율             │   │
│  └─────────────┴────────┴──────────────────────────────────┘   │
│                                                                 │
│  난이도 등급: Easy (0-0.3) / Medium (0.3-0.6) / Hard (0.6-1.0) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 각 축의 구체적 측정 방법

**축 1: 질의 복잡도 (Query Complexity)**

```python
from dataclasses import dataclass
from typing import List
import re

@dataclass
class QueryComplexityScore:
    length_score: float      # 길이 기반
    condition_score: float   # 조건절 기반
    implicit_score: float    # 암묵적 의도 기반
    total: float

def measure_query_complexity(query: str, lang: str = "ko") -> QueryComplexityScore:
    """질의 복잡도 측정 (0-1 스케일)"""

    # 1. 길이 점수 (토큰 수 기반)
    token_count = len(query.split())
    length_score = min(token_count / 50, 1.0)  # 50 토큰 이상이면 최대

    # 2. 조건절 점수 (한국어 패턴)
    condition_patterns = [
        r'만약|경우|때|조건',      # 조건
        r'그리고|또한|및|와',      # 병렬
        r'하지만|그러나|반면',     # 대조
        r'왜|어떻게|무엇|언제',    # 의문사 복합
    ]
    condition_count = sum(
        len(re.findall(p, query)) for p in condition_patterns
    )
    condition_score = min(condition_count / 5, 1.0)

    # 3. 암묵적 의도 점수 (대명사, 생략 탐지)
    implicit_patterns = [
        r'이것|그것|저것',         # 지시대명사
        r'앞서|위에서|이전',       # 문맥 참조
        r'같은|비슷한|유사',       # 비교 (기준 생략 가능)
    ]
    implicit_count = sum(
        len(re.findall(p, query)) for p in implicit_patterns
    )
    implicit_score = min(implicit_count / 3, 1.0)

    # 가중 합산
    total = (
        length_score * 0.3 +
        condition_score * 0.4 +
        implicit_score * 0.3
    )

    return QueryComplexityScore(
        length_score=length_score,
        condition_score=condition_score,
        implicit_score=implicit_score,
        total=total
    )
```

**축 2: 근거 산포도 (Evidence Dispersion)**

```python
from typing import List, Set

@dataclass
class EvidenceDispersionScore:
    chunk_count: int         # 정답에 필요한 chunk 수
    document_count: int      # 정답에 필요한 문서 수
    coverage_ratio: float    # top-k 내 정답 근거 비율
    total: float

def measure_evidence_dispersion(
    ground_truth_chunks: List[str],  # 정답 근거 chunk ID들
    ground_truth_docs: Set[str],     # 정답 근거 문서 ID들
    retrieved_chunks: List[str],     # 검색된 chunk ID들 (순서대로)
    k: int = 10
) -> EvidenceDispersionScore:
    """근거 산포도 측정 - 정답을 위해 필요한 정보가 얼마나 흩어져 있는가"""

    chunk_count = len(ground_truth_chunks)
    document_count = len(ground_truth_docs)

    # top-k 내 정답 근거 커버리지
    retrieved_set = set(retrieved_chunks[:k])
    covered = len(set(ground_truth_chunks) & retrieved_set)
    coverage_ratio = covered / max(len(ground_truth_chunks), 1)

    # 산포도 점수 계산
    # - chunk가 많을수록 어려움
    # - 문서가 많을수록 어려움
    # - 커버리지가 낮을수록 어려움

    chunk_difficulty = min(chunk_count / 5, 1.0)      # 5개 이상이면 최대
    doc_difficulty = min(document_count / 3, 1.0)    # 3개 문서 이상이면 최대
    coverage_difficulty = 1 - coverage_ratio          # 커버리지 역수

    total = (
        chunk_difficulty * 0.3 +
        doc_difficulty * 0.3 +
        coverage_difficulty * 0.4
    )

    return EvidenceDispersionScore(
        chunk_count=chunk_count,
        document_count=document_count,
        coverage_ratio=coverage_ratio,
        total=total
    )
```

**축 3: 추론 깊이 (Reasoning Depth)**

```python
from enum import IntEnum

class ReasoningHop(IntEnum):
    DIRECT_EXTRACTION = 0   # 문서에서 직접 추출
    SINGLE_HOP = 1          # 1단계 추론 (A→B)
    MULTI_HOP = 2           # 다단계 추론 (A→B→C)
    COMPOSITIONAL = 3       # 복합 추론 (여러 사실 조합)

@dataclass
class ReasoningDepthScore:
    hop_level: ReasoningHop
    requires_calculation: bool
    requires_comparison: bool
    total: float

def measure_reasoning_depth(
    query: str,
    answer: str,
    evidence_chunks: List[str]
) -> ReasoningDepthScore:
    """추론 깊이 측정 - 규칙 기반 휴리스틱"""

    # 계산 필요 여부
    calc_patterns = [
        r'합계|총|평균|비율|퍼센트|%',
        r'증가|감소|차이|변화',
        r'최대|최소|가장',
    ]
    requires_calculation = any(
        re.search(p, query) for p in calc_patterns
    )

    # 비교 필요 여부
    compare_patterns = [
        r'비교|차이|다른|같은',
        r'더|덜|보다',
        r'A와 B|versus|vs',
    ]
    requires_comparison = any(
        re.search(p, query) for p in compare_patterns
    )

    # hop 수 추정 (단순화된 휴리스틱)
    if len(evidence_chunks) == 1 and not requires_calculation:
        hop_level = ReasoningHop.DIRECT_EXTRACTION
    elif len(evidence_chunks) <= 2 and not requires_comparison:
        hop_level = ReasoningHop.SINGLE_HOP
    elif requires_comparison or len(evidence_chunks) >= 3:
        hop_level = ReasoningHop.MULTI_HOP
    else:
        hop_level = ReasoningHop.COMPOSITIONAL

    # 총점 계산
    hop_score = hop_level.value / 3  # 0-1 정규화
    calc_score = 0.2 if requires_calculation else 0
    compare_score = 0.2 if requires_comparison else 0

    total = min(hop_score + calc_score + compare_score, 1.0)

    return ReasoningDepthScore(
        hop_level=hop_level,
        requires_calculation=requires_calculation,
        requires_comparison=requires_comparison,
        total=total
    )
```

**축 4 & 5: 어휘 불일치 & 노이즈 밀도 (임베딩 기반)**

```python
import numpy as np
from typing import Tuple

@dataclass
class SemanticDifficultyScore:
    lexical_gap: float       # 질의-근거 어휘 불일치
    noise_density: float     # 유사-오답 문서 비율
    total: float

def measure_semantic_difficulty(
    query_embedding: np.ndarray,
    evidence_embeddings: List[np.ndarray],    # 정답 근거 임베딩
    retrieved_embeddings: List[np.ndarray],   # 검색 결과 임베딩
    similarity_threshold: float = 0.7
) -> SemanticDifficultyScore:
    """의미적 난이도 측정 - 임베딩 기반"""

    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # 1. 어휘 불일치: 질의와 정답 근거 간 평균 유사도의 역수
    if evidence_embeddings:
        query_evidence_sims = [
            cosine_similarity(query_embedding, e)
            for e in evidence_embeddings
        ]
        avg_similarity = np.mean(query_evidence_sims)
        lexical_gap = 1 - avg_similarity  # 유사도가 낮을수록 어려움
    else:
        lexical_gap = 1.0  # 근거가 없으면 최대 난이도

    # 2. 노이즈 밀도: 검색 결과 중 정답 근거가 아닌데 유사한 것의 비율
    evidence_set = set(id(e) for e in evidence_embeddings)

    noise_count = 0
    for i, ret_emb in enumerate(retrieved_embeddings):
        # 정답 근거가 아닌 경우
        is_evidence = any(
            cosine_similarity(ret_emb, e) > 0.95  # 거의 동일
            for e in evidence_embeddings
        )
        if not is_evidence:
            # 질의와 유사한 정도 체크 (노이즈 = 유사하지만 오답)
            sim_to_query = cosine_similarity(query_embedding, ret_emb)
            if sim_to_query > similarity_threshold:
                noise_count += 1

    noise_density = noise_count / max(len(retrieved_embeddings), 1)

    total = (lexical_gap * 0.5 + noise_density * 0.5)

    return SemanticDifficultyScore(
        lexical_gap=lexical_gap,
        noise_density=noise_density,
        total=total
    )
```

#### 2.2.3 통합 난이도 계산기

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class DataDifficultyProfile:
    """단일 테스트 케이스의 난이도 프로파일"""
    case_id: str

    # 개별 점수
    query_complexity: QueryComplexityScore
    evidence_dispersion: EvidenceDispersionScore
    reasoning_depth: ReasoningDepthScore
    semantic_difficulty: SemanticDifficultyScore

    # 종합
    total_score: float
    difficulty_level: DifficultyLevel

    # 메타데이터
    confidence: float  # 측정 신뢰도 (0-1)
    flags: List[str]   # 특이사항 플래그

class DifficultyProfiler:
    """데이터 난이도 프로파일러"""

    WEIGHTS = {
        "query_complexity": 0.20,
        "evidence_dispersion": 0.25,
        "reasoning_depth": 0.25,
        "semantic_difficulty": 0.30,
    }

    THRESHOLDS = {
        "easy": 0.30,
        "medium": 0.60,
        # hard: > 0.60
    }

    def profile(
        self,
        case_id: str,
        query: str,
        answer: str,
        ground_truth_chunks: List[str],
        ground_truth_docs: Set[str],
        retrieved_chunks: List[str],
        query_embedding: np.ndarray,
        evidence_embeddings: List[np.ndarray],
        retrieved_embeddings: List[np.ndarray],
    ) -> DataDifficultyProfile:
        """테스트 케이스 난이도 프로파일 생성"""

        # 개별 측정
        qc = measure_query_complexity(query)
        ed = measure_evidence_dispersion(
            ground_truth_chunks, ground_truth_docs, retrieved_chunks
        )
        rd = measure_reasoning_depth(query, answer, ground_truth_chunks)
        sd = measure_semantic_difficulty(
            query_embedding, evidence_embeddings, retrieved_embeddings
        )

        # 가중 합산
        total_score = (
            qc.total * self.WEIGHTS["query_complexity"] +
            ed.total * self.WEIGHTS["evidence_dispersion"] +
            rd.total * self.WEIGHTS["reasoning_depth"] +
            sd.total * self.WEIGHTS["semantic_difficulty"]
        )

        # 등급 결정
        if total_score <= self.THRESHOLDS["easy"]:
            level = DifficultyLevel.EASY
        elif total_score <= self.THRESHOLDS["medium"]:
            level = DifficultyLevel.MEDIUM
        else:
            level = DifficultyLevel.HARD

        # 플래그 생성
        flags = []
        if ed.coverage_ratio < 0.5:
            flags.append("low_retrieval_coverage")
        if rd.hop_level >= ReasoningHop.MULTI_HOP:
            flags.append("multi_hop_reasoning")
        if sd.noise_density > 0.5:
            flags.append("high_noise_density")

        # 신뢰도 (ground truth 존재 여부에 따라)
        confidence = 1.0 if ground_truth_chunks else 0.6

        return DataDifficultyProfile(
            case_id=case_id,
            query_complexity=qc,
            evidence_dispersion=ed,
            reasoning_depth=rd,
            semantic_difficulty=sd,
            total_score=total_score,
            difficulty_level=level,
            confidence=confidence,
            flags=flags,
        )
```

### 2.3 EvalVault 통합 설계

```
┌─────────────────────────────────────────────────────────────────┐
│                 EvalVault + Difficulty Profiling                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [데이터셋 로드]                                                │
│       ↓                                                         │
│  [난이도 프로파일링] ←── DifficultyProfiler                     │
│       ↓                                                         │
│  [run_id 생성] + 난이도 메타데이터 첨부                         │
│       ↓                                                         │
│  [RAG 파이프라인 실행]                                          │
│       ↓                                                         │
│  [평가 실행] (LLM-as-judge 또는 자체 모델)                      │
│       ↓                                                         │
│  [결과 저장]                                                    │
│   ├── metrics.json: 전체 점수                                   │
│   ├── difficulty_breakdown.json: 난이도별 점수                  │
│   └── failure_analysis.json: 실패 원인 분류                     │
│       ↓                                                         │
│  [리포트 생성]                                                  │
│   ├── 요약: "Hard 케이스에서 주로 실패"                         │
│   ├── 원인: "multi_hop_reasoning 플래그 케이스 집중"            │
│   └── 제안: "리랭킹 또는 쿼리 확장 검토"                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**아티팩트 구조 예시**:

```json
// artifacts/{run_id}/difficulty_breakdown.json
{
  "run_id": "run_20260117_001",
  "dataset_difficulty_distribution": {
    "easy": 0.25,
    "medium": 0.50,
    "hard": 0.25
  },
  "accuracy_by_difficulty": {
    "easy": 0.95,
    "medium": 0.78,
    "hard": 0.52
  },
  "failure_concentration": {
    "primary_difficulty": "hard",
    "primary_flags": ["multi_hop_reasoning", "low_retrieval_coverage"],
    "actionable_insight": "검색 단계에서 관련 문서를 충분히 가져오지 못함"
  }
}
```

### 2.4 기대 효과 (정량화)

| 지표 | 현재 | 도입 후 | 비고 |
|------|------|---------|------|
| 원인 진단 시간 | 4-8시간/이슈 | 10-30분/이슈 | 자동 분류로 시작점 제공 |
| 잘못된 최적화 시도 | ~40% | ~10% | 난이도 탓 vs 모델 탓 분리 |
| 회귀 감지 정확도 | 중간 | 높음 | 난이도 분포 변화 감지 |
| 개선 우선순위 명확성 | 낮음 | 높음 | Easy 실패 = 즉시 수정 대상 |

---

## 3. 솔루션 2: 평가 전문 소형 LLM 파인튜닝

### 3.1 비용 절감 분석 (상세)

#### 3.1.1 현재 비용 구조 (GPT-4o 기준)

```
┌─────────────────────────────────────────────────────────────────┐
│              GPT-4o LLM-as-judge 비용 분석                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  단일 평가 호출 구성:                                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ System prompt (평가 기준)      │  ~500 tokens           │     │
│  │ Question                       │  ~50 tokens            │     │
│  │ Context (top-5 chunks)         │  ~2,000 tokens         │     │
│  │ Answer                         │  ~300 tokens           │     │
│  │ ─────────────────────────────────────────────────────── │     │
│  │ Total Input                    │  ~2,850 tokens         │     │
│  │ Output (score + reasoning)     │  ~400 tokens           │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  GPT-4o 가격 (2026.01 기준):                                    │
│  - Input:  $2.50 / 1M tokens                                    │
│  - Output: $10.00 / 1M tokens                                   │
│                                                                 │
│  단일 평가 비용:                                                │
│  = (2,850 × $2.50 + 400 × $10.00) / 1,000,000                   │
│  = $0.00713 + $0.00400 = $0.01113                               │
│  ≈ ₩16.3 (환율 1,460원 기준)                                    │
│                                                                 │
│  3개 메트릭 평가 시:                                            │
│  = ₩16.3 × 3 = ₩48.9/케이스                                     │
│                                                                 │
│  + API 오류/재시도 오버헤드 (+15%)                              │
│  = ₩56.2/케이스 (실질 비용)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 자체 평가 모델 비용 구조

```
┌─────────────────────────────────────────────────────────────────┐
│           자체 1.5B 평가 모델 비용 분석                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  초기 투자 (1회성):                                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ 학습 데이터 구축      │ 인건비 2주 × 2명 = ₩800만       │     │
│  │ 학습 컴퓨팅           │ RTX 5090 100시간 = ₩50만        │     │
│  │ 검증/튜닝             │ 추가 50시간 = ₩25만             │     │
│  │ ───────────────────────────────────────────────────────│     │
│  │ Total                 │ ~₩875만                         │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  운영 비용 (추론):                                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ 하드웨어: RTX 4090 1대 (24GB VRAM)                      │     │
│  │ 처리량: ~50 평가/초 (배치, 4-bit quantization)          │     │
│  │ 전력: ~400W = 시간당 ₩80 (전기료 ₩200/kWh)             │     │
│  │ ───────────────────────────────────────────────────────│     │
│  │ 시간당 처리량: 180,000 평가                             │     │
│  │ 시간당 비용: ₩80 (전력만)                               │     │
│  │ 평가당 비용: ₩80 / 180,000 = ₩0.00044                   │     │
│  │ ───────────────────────────────────────────────────────│     │
│  │ + 서버 감가상각 (₩500만/3년 = 월 ₩14만)                 │     │
│  │ + 유지보수 (월 ₩10만)                                   │     │
│  │ = 월 고정비 ₩24만                                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  월 15만 건 평가 기준:                                          │
│  = 고정비 ₩24만 + 전력 ₩7만 = ₩31만/월                         │
│  = 평가당 ₩2.1                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.3 비용 비교 및 ROI

```
┌─────────────────────────────────────────────────────────────────┐
│                    비용 비교 분석 (월 15만 건 기준)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┬──────────────┬──────────────┬────────────┐    │
│  │ 항목        │ GPT-4o       │ 자체 모델    │ 절감       │    │
│  ├─────────────┼──────────────┼──────────────┼────────────┤    │
│  │ 평가당 비용 │ ₩56.2        │ ₩2.1         │ 96.3%      │    │
│  │ 월 비용     │ ₩8,430만     │ ₩31만        │ 99.6%      │    │
│  │ 연 비용     │ ₩10.1억      │ ₩372만       │ 99.6%      │    │
│  └─────────────┴──────────────┴──────────────┴────────────┘    │
│                                                                 │
│  손익분기점 분석:                                               │
│  - 초기 투자: ₩875만                                            │
│  - 월 절감액: ₩8,430만 - ₩31만 = ₩8,399만                       │
│  - 손익분기: 875만 / 8,399만 = 0.1개월 = 약 3일                 │
│                                                                 │
│  ※ 월 1만 건 기준으로도 손익분기 1.5개월 내                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 속도 개선 분석

```
┌─────────────────────────────────────────────────────────────────┐
│                    속도 비교 분석                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GPT-4o API:                                                    │
│  - 평균 응답 시간: 3-5초/평가                                   │
│  - 병렬 처리: rate limit으로 제한 (TPM/RPM)                     │
│  - 10,000건 평가: 8-14시간 (최적화 시)                          │
│                                                                 │
│  자체 1.5B 모델 (RTX 4090, 4-bit):                              │
│  - 평균 응답 시간: 0.02-0.05초/평가                             │
│  - 병렬 처리: 배치 사이즈 32-64 가능                            │
│  - 10,000건 평가: 3-10분                                        │
│                                                                 │
│  ┌─────────────┬──────────────┬──────────────┬────────────┐    │
│  │ 평가 규모   │ GPT-4o       │ 자체 모델    │ 개선       │    │
│  ├─────────────┼──────────────┼──────────────┼────────────┤    │
│  │ 1,000건     │ 50-83분      │ 20-50초      │ 60-250배   │    │
│  │ 10,000건    │ 8-14시간     │ 3-10분       │ 48-280배   │    │
│  │ 100,000건   │ 3-6일        │ 30-100분     │ 43-288배   │    │
│  └─────────────┴──────────────┴──────────────┴────────────┘    │
│                                                                 │
│  실무 영향:                                                     │
│  - PR 단위 평가: 수 시간 → 수 분 (CI/CD 통합 가능)              │
│  - 실험 피드백 루프: 하루 1-2회 → 하루 10회+ 가능               │
│  - 운영 모니터링: 샘플링 → 전수 평가 가능                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 모델 선정 및 학습 계획

#### 3.3.1 베이스 모델 비교 평가

```
┌─────────────────────────────────────────────────────────────────┐
│              베이스 모델 후보 비교 (2026.01 기준)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  평가 기준:                                                     │
│  - 크기: 1.5B 이하 (학습/추론 효율)                             │
│  - 한국어: 기본 성능 확보                                       │
│  - 추론: 판단/분류 태스크 적합성                                │
│  - 생태계: Unsloth/MLX 지원                                     │
│                                                                 │
│  ┌────────────────┬──────┬──────┬──────┬──────┬───────────┐    │
│  │ 모델           │ 크기 │ 한국어│ 추론 │ 생태계│ 종합      │    │
│  ├────────────────┼──────┼──────┼──────┼──────┼───────────┤    │
│  │ Qwen2.5-1.5B   │ ★★★ │ ★★★ │ ★★★ │ ★★★ │ 1순위     │    │
│  │ Gemma-2-2B     │ ★★☆ │ ★★☆ │ ★★★ │ ★★★ │ 2순위     │    │
│  │ Llama-3.2-1B   │ ★★★ │ ★★☆ │ ★★☆ │ ★★★ │ 3순위     │    │
│  │ SmolLM2-1.7B   │ ★★★ │ ★☆☆ │ ★★☆ │ ★★★ │ 4순위     │    │
│  │ Phi-3.5-mini   │ ★☆☆ │ ★★☆ │ ★★★ │ ★★☆ │ 5순위     │    │
│  └────────────────┴──────┴──────┴──────┴──────┴───────────┘    │
│                                                                 │
│  ★ 선정: Qwen2.5-1.5B-Instruct                                  │
│  - 다국어 성능 우수 (한국어 포함)                               │
│  - 지시 따르기/판단 태스크에 강점                               │
│  - Unsloth 공식 지원 + MLX 변환 가능                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 학습 데이터 설계

**데이터 구조**:

```json
{
  "id": "eval_train_001",
  "instruction": "당신은 RAG 시스템의 응답 품질을 평가하는 전문가입니다. 주어진 질문, 검색된 컨텍스트, 생성된 답변을 분석하고 평가해주세요.",
  "input": {
    "question": "원자력발전소의 냉각수 순환 시스템에서 1차 계통과 2차 계통의 차이점은 무엇인가요?",
    "context": [
      "[문서1] 1차 계통은 원자로 내부의 핵연료와 직접 접촉하는 냉각수가 순환하는 시스템으로...",
      "[문서2] 2차 계통은 1차 계통의 열을 전달받아 증기를 생성하는 시스템으로...",
      "[문서3] 냉각수 펌프의 정기 점검 주기는..."
    ],
    "answer": "1차 계통과 2차 계통의 주요 차이점은 다음과 같습니다. 1차 계통은 원자로 내부를 직접 순환하며 핵연료의 열을 흡수합니다. 반면 2차 계통은 1차 계통과 물리적으로 분리되어 있으며, 증기발생기를 통해 열만 전달받아 터빈을 구동하는 증기를 생성합니다."
  },
  "output": {
    "faithfulness": {
      "score": 0.95,
      "reasoning": "답변의 모든 주장이 컨텍스트 문서1, 문서2에 근거함. '물리적으로 분리'라는 표현은 문서에 직접 언급되지 않았으나 내용상 추론 가능한 범위."
    },
    "relevancy": {
      "score": 0.90,
      "reasoning": "질문이 요구한 '차이점'을 명확히 설명함. 다만 구체적인 온도/압력 조건 등 추가 정보가 있었다면 더 완전한 답변."
    },
    "groundedness": {
      "score": 0.92,
      "reasoning": "문서1과 문서2를 적절히 종합함. 문서3(펌프 점검)은 질문과 무관하여 올바르게 제외됨."
    },
    "hallucination_detected": false,
    "overall_quality": "good"
  }
}
```

**데이터 수집 전략**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    학습 데이터 수집 계획                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 기존 데이터 활용 (2주)                                │
│  ├── GPT-4o 평가 결과 수집 (기존 운영 로그)      │ 5,000건     │
│  ├── 인간 검토 라벨 (기존 QA 피드백)            │ 1,000건     │
│  └── 합계                                       │ 6,000건     │
│                                                                 │
│  Phase 2: 합성 데이터 생성 (2주)                                │
│  ├── 의도적 환각 삽입 (Negative sampling)       │ 2,000건     │
│  │   - 컨텍스트에 없는 정보 답변                               │
│  │   - 숫자/날짜 변조                                          │
│  │   - 인과관계 왜곡                                           │
│  ├── 난이도별 균형 샘플링                       │ 2,000건     │
│  │   - Easy:Medium:Hard = 2:5:3                                │
│  └── 합계                                       │ 4,000건     │
│                                                                 │
│  Phase 3: 도메인 특화 (1주)                                     │
│  ├── 원전 도메인 특수 케이스                    │ 1,000건     │
│  │   - 안전 규정 관련                                          │
│  │   - 수치/단위 정확성                                        │
│  │   - 절차 순서 정확성                                        │
│  └── 합계                                       │ 1,000건     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  총 학습 데이터: ~11,000건                                      │
│  검증 데이터: ~1,500건 (별도 수집)                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.3 학습 코드 (Unsloth)

```python
# train_eval_judge.py
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import torch

# ============================================================
# 1. 모델 로드
# ============================================================
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-1.5B-Instruct",
    max_seq_length=4096,
    dtype=None,  # auto-detect
    load_in_4bit=True,  # RTX 5090 Laptop (16GB) 대응
)

# ============================================================
# 2. LoRA 설정 (DoRA 포함)
# ============================================================
model = FastLanguageModel.get_peft_model(
    model,
    r=32,                    # LoRA rank
    lora_alpha=64,           # scaling factor
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",  # attention
        "gate_proj", "up_proj", "down_proj",      # FFN
    ],
    use_dora=True,           # Weight-Decomposed LoRA (2025 신기법)
    use_rslora=True,         # Rank-Stabilized LoRA
)

# ============================================================
# 3. 데이터 로드 및 포맷팅
# ============================================================
def format_eval_prompt(example):
    """평가 프롬프트 포맷팅"""
    system = """당신은 RAG 시스템의 응답 품질을 평가하는 전문가입니다.
주어진 질문, 컨텍스트, 답변을 분석하고 JSON 형식으로 평가 결과를 출력하세요.

평가 기준:
- faithfulness (0-1): 답변이 컨텍스트에 근거하는 정도
- relevancy (0-1): 답변이 질문 의도에 부합하는 정도
- groundedness (0-1): 답변이 컨텍스트를 적절히 활용한 정도
- hallucination_detected (true/false): 환각 존재 여부"""

    user = f"""## 질문
{example['input']['question']}

## 컨텍스트
{chr(10).join(example['input']['context'])}

## 답변
{example['input']['answer']}

위 내용을 평가해주세요."""

    assistant = f"""{{"faithfulness": {{"score": {example['output']['faithfulness']['score']}, "reasoning": "{example['output']['faithfulness']['reasoning']}"}}, "relevancy": {{"score": {example['output']['relevancy']['score']}, "reasoning": "{example['output']['relevancy']['reasoning']}"}}, "groundedness": {{"score": {example['output']['groundedness']['score']}, "reasoning": "{example['output']['groundedness']['reasoning']}"}}, "hallucination_detected": {str(example['output']['hallucination_detected']).lower()}, "overall_quality": "{example['output']['overall_quality']}"}}"""

    return {
        "text": tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            tokenize=False,
        )
    }

dataset = load_dataset("json", data_files="eval_train_data.jsonl")
dataset = dataset.map(format_eval_prompt)

# ============================================================
# 4. 학습 설정
# ============================================================
training_args = TrainingArguments(
    output_dir="./eval_judge_model",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # effective batch size = 16
    warmup_ratio=0.1,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=10,
    save_strategy="epoch",
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=42,
    # NEFTune: 임베딩 노이즈로 일반화 성능 향상
    neftune_noise_alpha=5,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    dataset_text_field="text",
    max_seq_length=4096,
    args=training_args,
)

# ============================================================
# 5. 학습 실행
# ============================================================
trainer.train()

# ============================================================
# 6. 모델 저장 (4-bit quantized)
# ============================================================
model.save_pretrained_merged(
    "eval_judge_model_merged",
    tokenizer,
    save_method="merged_4bit_forced",
)

print("✅ 학습 완료!")
```

#### 3.3.4 M2 Pro MLX 학습 (대안)

```python
# train_eval_judge_mlx.py
# Unsloth MLX 지원 (2026년 1월 기준)
from unsloth.mlx import FastLanguageModel

# MLX는 통합 메모리로 32GB 전체 활용
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-1.5B-Instruct",
    max_seq_length=4096,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

# MLX 특화 학습 설정
from unsloth.mlx import MLXTrainer

trainer = MLXTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    batch_size=8,  # MLX는 더 큰 배치 가능
    num_epochs=3,
    learning_rate=2e-4,
)

trainer.train()
```

### 3.4 품질 검증 계획

```
┌─────────────────────────────────────────────────────────────────┐
│                    품질 검증 프레임워크                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  검증 메트릭:                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 메트릭            │ 목표       │ 측정 방법              │   │
│  ├───────────────────┼────────────┼────────────────────────┤   │
│  │ GPT-4o 일치율     │ ≥ 90%      │ 동일 케이스 판정 비교  │   │
│  │ 인간 평가 일치율  │ ≥ 85%      │ Cohen's Kappa ≥ 0.7    │   │
│  │ 자기 일관성       │ ≥ 95%      │ 동일 케이스 3회 평가   │   │
│  │ 환각 탐지 Recall  │ ≥ 90%      │ 의도적 환각 케이스     │   │
│  │ 환각 탐지 Prec.   │ ≥ 85%      │ 정상 케이스 오탐률     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  검증 데이터셋 구성:                                            │
│  - 일반 케이스: 1,000건                                         │
│  - 의도적 환각: 300건                                           │
│  - 경계 케이스 (애매한 판단): 200건                             │
│  - 도메인 특화 (원전): 200건                                    │
│                                                                 │
│  검증 일정:                                                     │
│  - 학습 중: 매 epoch 후 검증셋 평가                             │
│  - 학습 후: 전체 검증셋 + 인간 샘플링 (100건)                   │
│  - 배포 후: 주간 드리프트 모니터링                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 솔루션 3: 최신 파인튜닝 기법 적용 (실험적)

### 4.1 적용 가능 기법 상세 분석

#### 4.1.1 DoRA (Weight-Decomposed LoRA)

```
┌─────────────────────────────────────────────────────────────────┐
│                         DoRA 개요                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  기존 LoRA:                                                     │
│  W' = W + BA  (B: r×d, A: d×r)                                  │
│                                                                 │
│  DoRA:                                                          │
│  W' = m × (W + BA) / ||W + BA||  (m: magnitude vector)          │
│                                                                 │
│  핵심 아이디어:                                                 │
│  - 가중치를 "방향(direction)"과 "크기(magnitude)"로 분해         │
│  - LoRA는 방향만 업데이트, magnitude는 별도 학습                 │
│  - 동일 rank에서 풀 파인튜닝에 더 근접한 성능                   │
│                                                                 │
│  장점:                                                          │
│  - 추가 파라미터 거의 없음 (magnitude vector만 추가)            │
│  - 학습 안정성 향상                                             │
│  - 동일 rank에서 1-3% 성능 향상 (벤치마크 기준)                 │
│                                                                 │
│  Unsloth 적용:                                                  │
│  model = FastLanguageModel.get_peft_model(                      │
│      model, r=32, use_dora=True, ...                            │
│  )                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.1.2 NEFTune (Noisy Embedding Fine-Tuning)

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEFTune 개요                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  원리:                                                          │
│  - 학습 시 입력 임베딩에 균일 노이즈 추가                       │
│  - noise ~ Uniform(-α/√(L×d), +α/√(L×d))                        │
│  - L: 시퀀스 길이, d: 임베딩 차원, α: 노이즈 강도               │
│                                                                 │
│  효과:                                                          │
│  - 과적합 방지 (regularization 효과)                            │
│  - 일반화 성능 향상 (특히 instruction-following)                │
│  - AlpacaEval 기준 15-20% 개선 보고                             │
│                                                                 │
│  권장 설정:                                                     │
│  - α = 5 (일반적)                                               │
│  - α = 10-15 (과적합 심한 경우)                                 │
│  - α = 1-3 (데이터 노이즈가 이미 많은 경우)                     │
│                                                                 │
│  Unsloth 적용:                                                  │
│  TrainingArguments(                                             │
│      neftune_noise_alpha=5,                                     │
│      ...                                                        │
│  )                                                              │
│                                                                 │
│  리스크:                                                        │
│  - 정밀한 수치 판단 태스크에서는 역효과 가능                    │
│  - 원전 도메인처럼 정확성이 중요한 경우 α를 낮게 설정           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.1.3 DPO/ORPO (선호도 최적화)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DPO/ORPO 개요                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DPO (Direct Preference Optimization):                          │
│  - RLHF의 간소화 버전                                           │
│  - 보상 모델 없이 직접 선호도 학습                              │
│  - Loss: -log σ(β × (log π(y_w|x) - log π(y_l|x)))              │
│    (y_w: 선호 응답, y_l: 비선호 응답)                           │
│                                                                 │
│  ORPO (Odds Ratio Preference Optimization):                     │
│  - DPO 개선: 참조 모델 불필요                                   │
│  - SFT와 선호도 학습을 단일 단계로 통합                         │
│  - 학습 효율성 향상                                             │
│                                                                 │
│  평가 모델에 적용 시 이점:                                      │
│  - "좋은 평가 vs 나쁜 평가" 쌍으로 학습                         │
│  - 애매한 케이스에서 더 일관된 판단                             │
│  - 환각 탐지 정밀도 향상                                        │
│                                                                 │
│  데이터 구성 예시:                                              │
│  {                                                              │
│    "prompt": "[질문+컨텍스트+답변]",                            │
│    "chosen": "{"faithfulness": 0.3, "reasoning": "...환각..."}",│
│    "rejected": "{"faithfulness": 0.9, "reasoning": "...정상..."}"│
│  }                                                              │
│  → 환각 케이스를 환각으로 판정하는 응답이 "chosen"              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.1.4 GaLore (Gradient Low-Rank Projection)

```
┌─────────────────────────────────────────────────────────────────┐
│                       GaLore 개요                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  원리:                                                          │
│  - Gradient를 저랭크 부분공간으로 투영하여 메모리 절감          │
│  - LoRA처럼 가중치가 아닌, gradient를 저랭크로 압축             │
│  - 풀 파인튜닝의 표현력 + LoRA의 메모리 효율성                  │
│                                                                 │
│  메모리 절감 효과:                                              │
│  - 7B 모델 풀 파인튜닝: ~60GB → ~16GB (약 73% 절감)             │
│  - 1.5B 모델: ~14GB → ~4GB                                      │
│                                                                 │
│  적용 가능성:                                                   │
│  - M2 Pro 32GB에서 더 큰 배치 사이즈 가능                       │
│  - RTX 5090 Laptop에서 풀 파인튜닝 근사 가능                    │
│                                                                 │
│  리스크:                                                        │
│  - 아직 Unsloth 공식 지원 미확정 (2026.01 기준)                 │
│  - 학습 속도 10-20% 저하 (투영 오버헤드)                        │
│  - 하이퍼파라미터 튜닝 필요 (rank, projection 주기)             │
│                                                                 │
│  권장:                                                          │
│  - DoRA + NEFTune이 안정적 성능을 내지 못할 경우 시도           │
│  - 또는 모델 크기를 2B로 올리고 싶은 경우                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.1.5 KV Cache Distillation (실험적)

```
┌─────────────────────────────────────────────────────────────────┐
│                 KV Cache Distillation 개요                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  아이디어:                                                      │
│  - 큰 모델(GPT-4o, Claude)의 "판단 패턴"을 추출                 │
│  - KV Cache 수준에서 attention 패턴을 증류                      │
│  - 작은 모델이 큰 모델의 "주목 방식"을 학습                     │
│                                                                 │
│  평가 모델에 적용:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Teacher (GPT-4o)                                        │   │
│  │   ├── 입력: [질문, 컨텍스트, 답변]                      │   │
│  │   ├── 출력: 평가 결과                                   │   │
│  │   └── 추출: attention weights (어디를 주목했는가)       │   │
│  │                    ↓                                    │   │
│  │ Student (Qwen2.5-1.5B)                                  │   │
│  │   ├── 기본 학습: 평가 결과 예측                         │   │
│  │   └── 추가 학습: teacher의 attention 패턴 모방          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  기대 효과:                                                     │
│  - "어디를 봐야 하는지" 학습 → 빠른 수렴                        │
│  - 환각 탐지 시 "근거 vs 주장" 대조 패턴 전이                   │
│                                                                 │
│  리스크:                                                        │
│  - 구현 복잡도 높음 (attention 추출 + 증류 로스 설계)           │
│  - GPT-4o의 attention 접근 제한 (OpenAI API 미제공)             │
│  - Claude API도 내부 상태 미공개                                │
│                                                                 │
│  대안:                                                          │
│  - Llama-3.1-70B 같은 오픈 모델을 teacher로 사용                │
│  - 또는 output-level distillation (기존 방식)으로 대체          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 권장 실험 로드맵

```
┌─────────────────────────────────────────────────────────────────┐
│               파인튜닝 기법 실험 로드맵                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Stage 1: 기본선 확립 (1주)                                     │
│  ├── 실험 A: LoRA only (r=32, α=64)                             │
│  ├── 실험 B: LoRA + NEFTune (α=5)                               │
│  └── 측정: GPT-4o 일치율, 자기 일관성                           │
│                                                                 │
│  Stage 2: DoRA 추가 (1주)                                       │
│  ├── 실험 C: DoRA + NEFTune (최적 α 탐색)                       │
│  ├── 실험 D: DoRA + RSLoRA                                      │
│  └── 측정: Stage 1 대비 개선폭                                  │
│                                                                 │
│  Stage 3: 선호도 최적화 (2주)                                   │
│  ├── 데이터: 선호/비선호 쌍 2,000건 구축                        │
│  ├── 실험 E: SFT → DPO (2-stage)                                │
│  ├── 실험 F: ORPO (1-stage)                                     │
│  └── 측정: 환각 탐지 F1, 경계 케이스 일관성                     │
│                                                                 │
│  Stage 4: 고급 실험 (선택적, 2주)                               │
│  ├── 실험 G: GaLore (메모리 한계 시)                            │
│  ├── 실험 H: Output Distillation (Llama-70B → 1.5B)             │
│  └── 측정: 전체 메트릭 비교                                     │
│                                                                 │
│  최종 선택 기준:                                                │
│  1. GPT-4o 일치율 ≥ 90%                                         │
│  2. 환각 탐지 F1 ≥ 0.87                                         │
│  3. 추론 속도 ≤ 0.1초/평가                                      │
│  4. 학습 재현성 (seed 고정 시 ±2% 이내)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 통합 구현 로드맵

### 5.1 전체 일정

```
┌─────────────────────────────────────────────────────────────────┐
│                      12주 구현 로드맵                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 기반 구축 (Week 1-4)                                  │
│  ══════════════════════════════════════════════════════════════ │
│  Week 1-2:                                                      │
│  ├── 난이도 프로파일러 v1 구현 (규칙 기반)                      │
│  ├── 학습 데이터 수집 시작 (기존 로그 + 라벨링)                 │
│  └── Unsloth 환경 세팅 (RTX 5090 / M2 Pro)                      │
│                                                                 │
│  Week 3-4:                                                      │
│  ├── 베이스라인 모델 학습 (LoRA + NEFTune)                      │
│  ├── 난이도 프로파일러 EvalVault 통합                           │
│  └── 품질 검증 프레임워크 구축                                  │
│                                                                 │
│  ✓ 마일스톤 1: 최소 기능 동작 (MVP)                             │
│    - 난이도 3단계 분류 동작                                     │
│    - 평가 모델 GPT-4o 대비 80% 일치율                           │
│                                                                 │
│  Phase 2: 최적화 (Week 5-8)                                     │
│  ══════════════════════════════════════════════════════════════ │
│  Week 5-6:                                                      │
│  ├── DoRA + RSLoRA 실험                                         │
│  ├── 난이도 프로파일러 임베딩 기반 확장                         │
│  └── 합성 데이터 생성 (환각 케이스)                             │
│                                                                 │
│  Week 7-8:                                                      │
│  ├── DPO/ORPO 2-stage 학습                                      │
│  ├── 인간 평가 샘플링 (100건)                                   │
│  └── EvalVault 리포트 템플릿 개선                               │
│                                                                 │
│  ✓ 마일스톤 2: 목표 품질 달성                                   │
│    - GPT-4o 대비 90% 일치율                                     │
│    - 환각 탐지 F1 ≥ 0.87                                        │
│    - 난이도별 정확도 분석 자동화                                │
│                                                                 │
│  Phase 3: 프로덕션 (Week 9-12)                                  │
│  ══════════════════════════════════════════════════════════════ │
│  Week 9-10:                                                     │
│  ├── 추론 최적화 (배치 처리, 양자화)                            │
│  ├── API 서버 구축 (FastAPI + vLLM/llama.cpp)                   │
│  └── CI/CD 파이프라인 통합                                      │
│                                                                 │
│  Week 11-12:                                                    │
│  ├── 운영 모니터링 대시보드                                     │
│  ├── 드리프트 감지 알림 설정                                    │
│  └── 문서화 및 인수인계                                         │
│                                                                 │
│  ✓ 마일스톤 3: 프로덕션 배포                                    │
│    - 99.6% 비용 절감 실현                                       │
│    - 평가 속도 40배+ 향상                                       │
│    - 자동화된 품질 루프 운영                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 리소스 요구사항

```
┌─────────────────────────────────────────────────────────────────┐
│                      리소스 요구사항                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  인력:                                                          │
│  ├── ML 엔지니어: 1명 (풀타임, 12주)                            │
│  ├── 데이터 라벨러: 1명 (파트타임, 4주)                         │
│  └── 검증/QA: 0.5명 (파트타임, 4주)                             │
│                                                                 │
│  하드웨어 (학습):                                               │
│  ├── Option A: RTX 5090 Laptop (이미 보유 가정)                 │
│  └── Option B: M2 Pro 32GB (이미 보유 가정)                     │
│      → 추가 구매 불필요                                         │
│                                                                 │
│  하드웨어 (추론/운영):                                          │
│  ├── RTX 4090 1대: ~₩300만 (신규 구매 시)                       │
│  └── 또는 클라우드: A10G ~$1/시간                               │
│                                                                 │
│  소프트웨어/서비스:                                             │
│  ├── Unsloth Pro (선택): $200/월                                │
│  ├── 클라우드 스토리지: ~₩10만/월                               │
│  └── 모니터링 도구: 기존 인프라 활용                            │
│                                                                 │
│  총 예산 (12주):                                                │
│  ├── 인건비: ~₩3,000만 (내부 인력 기준)                         │
│  ├── 하드웨어: ₩0-300만                                         │
│  ├── 서비스: ~₩100만                                            │
│  └── 합계: ~₩3,100-3,400만                                      │
│                                                                 │
│  vs. 12주 GPT-4o 비용 (월 15만건):                              │
│  = ₩8,430만 × 3개월 = ₩2.5억                                    │
│                                                                 │
│  → 초기 투자 대비 12주 내 ROI: 7-8배                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 리스크 및 완화 전략

### 6.1 기술적 리스크

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| 1.5B 모델 품질 한계 | 중 | 높음 | 앙상블(자체+GPT-4o 샘플링), 불확실 케이스 플래그 |
| MLX 학습 불안정 | 중 | 중간 | CUDA를 primary로, MLX는 추론 전용 |
| 최신 기법 호환성 | 중 | 낮음 | 각 기법을 독립 브랜치로 실험, 안정판 우선 |
| 학습 데이터 부족 | 낮 | 높음 | 합성 데이터 생성 + 능동 학습 |

### 6.2 운영 리스크

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| 모델 드리프트 | 중 | 중간 | 주간 GPT-4o 샘플 비교, 알림 설정 |
| 도메인 변화 | 낮 | 높음 | 신규 도메인 데이터 증분 학습 파이프라인 |
| 하드웨어 장애 | 낮 | 높음 | 백업 추론 서버, GPT-4o 폴백 |

### 6.3 품질 보장 체계

```
┌─────────────────────────────────────────────────────────────────┐
│                    품질 보장 다층 방어                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 모델 수준                                             │
│  ├── 학습 시 검증셋 모니터링                                    │
│  └── Early stopping (과적합 방지)                               │
│                                                                 │
│  Layer 2: 추론 수준                                             │
│  ├── 신뢰도 점수 (모델 출력 확률)                               │
│  ├── 저신뢰 케이스 → GPT-4o 폴백                                │
│  └── 환각 플래그 케이스 → 인간 검토 큐                          │
│                                                                 │
│  Layer 3: 운영 수준                                             │
│  ├── 일간: 자기 일관성 체크 (10% 샘플)                          │
│  ├── 주간: GPT-4o 비교 (5% 샘플)                                │
│  └── 월간: 인간 평가 (100건)                                    │
│                                                                 │
│  Layer 4: 시스템 수준                                           │
│  ├── 난이도 분포 드리프트 감지                                  │
│  ├── 평가 점수 분포 이상 탐지                                   │
│  └── 환각 탐지율 추세 모니터링                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 결론: 왜 지금 해야 하는가

### 7.1 비용 관점

| 시나리오 | 1년 비용 | 비고 |
|----------|----------|------|
| 현행 유지 (GPT-4o) | **₩10.1억** | 평가량 증가 시 비례 증가 |
| 자체 모델 전환 | **₩1,250만** | 초기 투자 ₩875만 + 운영 ₩375만 |
| **절감액** | **₩9.9억** | 98.8% 절감 |

### 7.2 역량 관점

| Before | After |
|--------|-------|
| 평가 = 외부 API 의존 | 평가 = 내부 핵심 역량 |
| 원인 분석 = 수동/감 | 원인 분석 = 자동/체계 |
| 개선 루프 = 느림 | 개선 루프 = 실시간 |
| 도메인 최적화 = 불가 | 도메인 최적화 = 가능 |

### 7.3 전략 관점

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  "평가 역량 내재화"는 RAG 시스템의 지속적 개선을 위한           │
│  필수 인프라입니다.                                             │
│                                                                 │
│  특히 원전 도메인처럼 환각이 법적 리스크로 직결되는 경우,      │
│  외부 API에 의존한 평가는 다음 한계를 가집니다:                 │
│                                                                 │
│  1. 감사 추적성 부족 (판정 근거가 블랙박스)                     │
│  2. 도메인 특화 불가 (일반 모델의 판단 기준)                    │
│  3. 비용 예측 불가 (사용량 비례 과금)                           │
│  4. 속도 병목 (CI/CD 통합 어려움)                               │
│                                                                 │
│  자체 평가 모델 + 난이도 프로파일링은 이 모든 한계를            │
│  해결하며, 12주 내 ROI 7-8배를 달성합니다.                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**다음 단계 제안**:
1. Week 1 킥오프: 환경 세팅 + 데이터 수집 시작
2. Week 2 리뷰: 난이도 프로파일러 v1 데모
3. Week 4 마일스톤: MVP 품질 검증

추가 논의가 필요한 부분이 있으면 말씀해 주세요.
