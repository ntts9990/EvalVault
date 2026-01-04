# 커스텀 메트릭 추가 가이드

> Ragas 커스텀 메트릭을 작성하고 EvalVault에 통합하는 방법을 배웁니다.

---

## 목차

1. [커스텀 메트릭이란?](#커스텀-메트릭이란)
2. [메트릭 클래스 구조](#메트릭-클래스-구조)
3. [예제: 보험 용어 정확도 메트릭](#예제-보험-용어-정확도-메트릭)
4. [EvalVault에 통합하기](#evalvault에-통합하기)
5. [고급 기법](#고급-기법)

---

## 커스텀 메트릭이란?

EvalVault는 Ragas의 6가지 표준 메트릭 외에 **도메인 특화 메트릭**을 지원합니다.

### 언제 커스텀 메트릭이 필요한가?

| 상황 | 표준 메트릭 | 커스텀 메트릭 |
|------|-------------|---------------|
| 일반적인 RAG 품질 평가 | 적합 | - |
| 환각 감지 | `faithfulness` | - |
| 도메인 용어 정확성 | - | 필요 |
| 규정 준수 여부 | - | 필요 |
| 특정 포맷 검증 | - | 필요 |

### EvalVault의 커스텀 메트릭 예시

```
src/evalvault/domain/metrics/
├── __init__.py
├── insurance.py              # InsuranceTermAccuracy 메트릭
└── terms_dictionary.json     # 보험 용어 사전
```

---

## 메트릭 클래스 구조

커스텀 메트릭은 다음 인터페이스를 따릅니다:

```python
class CustomMetric:
    """커스텀 메트릭 기본 구조.

    Attributes:
        name: 메트릭 고유 이름 (snake_case)
    """

    name = "custom_metric_name"

    def __init__(self, **kwargs):
        """메트릭 초기화.

        Args:
            **kwargs: 메트릭별 설정 옵션
        """
        pass

    def score(self, answer: str, contexts: list[str], **kwargs) -> float:
        """점수 계산.

        Args:
            answer: RAG 시스템의 답변
            contexts: 검색된 컨텍스트 목록
            **kwargs: 추가 인자 (question, ground_truth 등)

        Returns:
            0.0 ~ 1.0 사이의 점수
        """
        pass
```

### 필수 요소

1. **`name` 속성**: 메트릭 고유 식별자
2. **`score()` 메서드**: 점수 계산 로직

### 선택 요소

| 메서드 | 설명 |
|--------|------|
| `__init__()` | 설정 파일, 사전 등 초기화 |
| `_normalize_text()` | 텍스트 전처리 |
| `_validate_input()` | 입력 검증 |

---

## 예제: 보험 용어 정확도 메트릭

EvalVault에 포함된 `InsuranceTermAccuracy` 메트릭을 분석합니다.

### 목적

답변에 사용된 보험 용어가 컨텍스트에 근거하는지 평가합니다.

### 점수 기준

- **1.0**: 답변의 모든 보험 용어가 컨텍스트에서 확인됨
- **0.5**: 절반의 용어만 확인됨
- **0.0**: 답변의 보험 용어가 컨텍스트에 없음

### 구현 코드

**파일**: `src/evalvault/domain/metrics/insurance.py`

```python
"""Insurance domain-specific evaluation metrics."""

import json
import re
from pathlib import Path


class InsuranceTermAccuracy:
    """보험 용어 정확성 메트릭.

    답변에 사용된 보험 용어들이 주어진 컨텍스트에 근거하고 있는지 평가합니다.
    """

    name = "insurance_term_accuracy"

    def __init__(self, terms_dict_path: str | Path | None = None):
        """Initialize InsuranceTermAccuracy metric.

        Args:
            terms_dict_path: Path to terms dictionary JSON file.
                           If None, uses default dictionary.
        """
        if terms_dict_path is None:
            terms_dict_path = Path(__file__).parent / "terms_dictionary.json"
        else:
            terms_dict_path = Path(terms_dict_path)

        with open(terms_dict_path, encoding="utf-8") as f:
            self.terms_dict = json.load(f)

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace."""
        text = re.sub(r"\s+", "", text)
        return text

    def _find_term_matches(self, text: str) -> set[str]:
        """Find all insurance terms (canonical forms) in text."""
        matched_terms = set()
        text_lower = text.lower()
        text_normalized = self._normalize_text(text)

        for canonical_term, term_data in self.terms_dict.items():
            # Check canonical form
            if canonical_term in text or canonical_term in text_normalized:
                matched_terms.add(canonical_term)
                continue

            # Check Korean variants
            for variant in term_data["variants"]:
                variant_normalized = self._normalize_text(variant)
                if variant in text or variant_normalized in text_normalized:
                    matched_terms.add(canonical_term)
                    break

            # Check English variants (case-insensitive)
            if "english" in term_data:
                for eng_term in term_data["english"]:
                    if eng_term.lower() in text_lower:
                        matched_terms.add(canonical_term)
                        break

        return matched_terms

    def score(self, answer: str, contexts: list[str]) -> float:
        """Calculate insurance term accuracy score.

        Args:
            answer: The answer text to evaluate
            contexts: List of context strings

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        # Find terms in answer
        answer_terms = self._find_term_matches(answer)

        # If no insurance terms in answer, return perfect score
        if not answer_terms:
            return 1.0

        # If contexts are empty, return 0 (can't verify)
        if not contexts:
            return 0.0

        # Find terms in all contexts (union)
        context_terms = set()
        for context in contexts:
            context_terms.update(self._find_term_matches(context))

        # Calculate how many answer terms are supported by contexts
        verified_terms = answer_terms.intersection(context_terms)
        accuracy = len(verified_terms) / len(answer_terms)

        return accuracy
```

### 용어 사전 형식

**파일**: `src/evalvault/domain/metrics/terms_dictionary.json`

```json
{
  "보험금": {
    "canonical": "보험금",
    "variants": ["보험금", "보험 금액", "지급금", "보상금", "보험급여"],
    "english": ["insurance benefit", "insurance payout", "claim amount"]
  },
  "보험료": {
    "canonical": "보험료",
    "variants": ["보험료", "납입료", "월 보험료", "연 보험료"],
    "english": ["premium", "insurance premium", "monthly premium"]
  },
  "피보험자": {
    "canonical": "피보험자",
    "variants": ["피보험자", "보험 대상자", "피보험인"],
    "english": ["insured", "insured person", "policyholder"]
  }
}
```

### 사용 예시

```python
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy

# 메트릭 인스턴스 생성
metric = InsuranceTermAccuracy()

# 평가 실행
answer = "이 보험의 보험금은 1억원이며, 보험료는 월 10만원입니다."
contexts = [
    "해당 보험의 사망 보험금은 1억원입니다.",
    "월 보험료는 10만원입니다."
]

score = metric.score(answer, contexts)
print(f"Insurance Term Accuracy: {score}")  # 1.0 (모든 용어 확인됨)
```

---

## EvalVault에 통합하기

### Step 1: 메트릭 클래스 작성

`src/evalvault/domain/metrics/` 디렉토리에 새 파일을 생성합니다.

```python
# src/evalvault/domain/metrics/my_metric.py

class MyCustomMetric:
    """나만의 커스텀 메트릭."""

    name = "my_custom_metric"

    def __init__(self, config_path: str | None = None):
        # 설정 로드
        pass

    def score(self, answer: str, contexts: list[str], **kwargs) -> float:
        # 점수 계산 로직
        return 1.0
```

### Step 2: `__init__.py` 업데이트

```python
# src/evalvault/domain/metrics/__init__.py

from evalvault.domain.metrics.insurance import InsuranceTermAccuracy
# MyCustomMetric 파일을 생성한 뒤 아래 라인을 추가하세요.
# from evalvault.domain.metrics.my_metric import MyCustomMetric

__all__ = ["InsuranceTermAccuracy", "MyCustomMetric"]
```

### Step 3: Python 코드에서 사용

```python
from evalvault.domain.metrics import MyCustomMetric

metric = MyCustomMetric()
score = metric.score(answer="답변 텍스트", contexts=["컨텍스트"])
print(f"Score: {score}")
```

---

## 고급 기법

### 1. LLM 기반 메트릭

복잡한 판단이 필요한 경우 LLM을 활용할 수 있습니다.

```python
from openai import OpenAI


class LLMBasedMetric:
    """LLM을 활용한 커스텀 메트릭."""

    name = "llm_based_metric"

    def __init__(self):
        self.client = OpenAI()

    def score(self, answer: str, contexts: list[str], question: str) -> float:
        prompt = f"""
다음 답변이 질문에 적절한지 0.0~1.0 점수로 평가하세요.

질문: {question}
답변: {answer}
컨텍스트: {contexts}

점수만 출력하세요 (예: 0.85)
"""
        response = self.client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.0
```

### 2. 형태소 분석 기반 메트릭 (한국어)

한국어 특화 메트릭은 Kiwi 형태소 분석기를 활용합니다.

```python
from kiwipiepy import Kiwi


class KoreanKeywordMetric:
    """한국어 키워드 정확도 메트릭."""

    name = "korean_keyword_accuracy"

    def __init__(self):
        self.kiwi = Kiwi()

    def _extract_keywords(self, text: str) -> set[str]:
        """명사 키워드 추출."""
        tokens = self.kiwi.tokenize(text)
        # 명사 태그: NNG(일반명사), NNP(고유명사)
        nouns = {t.form for t in tokens if t.tag in ("NNG", "NNP")}
        return nouns

    def score(self, answer: str, contexts: list[str]) -> float:
        answer_keywords = self._extract_keywords(answer)

        if not answer_keywords:
            return 1.0

        context_keywords = set()
        for ctx in contexts:
            context_keywords.update(self._extract_keywords(ctx))

        matched = answer_keywords.intersection(context_keywords)
        return len(matched) / len(answer_keywords)
```

### 3. 정규식 기반 포맷 검증 메트릭

특정 포맷 준수 여부를 검증합니다.

```python
import re


class FormatComplianceMetric:
    """포맷 준수 메트릭."""

    name = "format_compliance"

    def __init__(self, patterns: list[str]):
        """
        Args:
            patterns: 필수 포맷 패턴 목록 (정규식)
        """
        self.patterns = [re.compile(p) for p in patterns]

    def score(self, answer: str, contexts: list[str]) -> float:
        if not self.patterns:
            return 1.0

        matches = sum(1 for p in self.patterns if p.search(answer))
        return matches / len(self.patterns)


# 사용 예시
metric = FormatComplianceMetric(patterns=[
    r"\d+원",           # 금액 포함
    r"\d+년|개월|일",   # 기간 포함
])
```

### 4. 복합 메트릭

여러 메트릭을 조합합니다.

```python
class CompositeMetric:
    """복합 메트릭."""

    name = "composite_metric"

    def __init__(self, metrics: list, weights: list[float] | None = None):
        self.metrics = metrics
        self.weights = weights or [1.0] * len(metrics)

    def score(self, answer: str, contexts: list[str], **kwargs) -> float:
        total = 0.0
        for metric, weight in zip(self.metrics, self.weights):
            total += metric.score(answer, contexts, **kwargs) * weight
        return total / sum(self.weights)


# 사용 예시
from evalvault.domain.metrics import InsuranceTermAccuracy

composite = CompositeMetric(
    metrics=[InsuranceTermAccuracy(), FormatComplianceMetric([r"\d+원"])],
    weights=[0.7, 0.3]
)
```

---

## 테스트 작성

커스텀 메트릭은 반드시 테스트를 작성하세요.

```python
# tests/unit/test_custom_metric.py

import pytest
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy


class TestInsuranceTermAccuracy:
    """InsuranceTermAccuracy 메트릭 테스트."""

    @pytest.fixture
    def metric(self):
        return InsuranceTermAccuracy()

    def test_all_terms_verified(self, metric):
        """모든 용어가 컨텍스트에서 확인될 때."""
        answer = "보험금은 1억원입니다."
        contexts = ["사망 보험금은 1억원입니다."]

        score = metric.score(answer, contexts)

        assert score == 1.0

    def test_no_terms_verified(self, metric):
        """용어가 컨텍스트에 없을 때."""
        answer = "보험금은 1억원입니다."
        contexts = ["날씨가 좋습니다."]

        score = metric.score(answer, contexts)

        assert score == 0.0

    def test_partial_match(self, metric):
        """일부 용어만 확인될 때."""
        answer = "보험금과 보험료를 확인하세요."
        contexts = ["보험금은 1억원입니다."]

        score = metric.score(answer, contexts)

        assert 0.0 < score < 1.0

    def test_no_insurance_terms(self, metric):
        """보험 용어가 없는 답변."""
        answer = "감사합니다."
        contexts = ["보험금은 1억원입니다."]

        score = metric.score(answer, contexts)

        assert score == 1.0  # 용어가 없으면 완벽한 점수
```

테스트 실행:

```bash
uv run pytest tests/unit/test_custom_metric.py -v
```

---

## 다음 단계

| 주제 | 튜토리얼 |
|------|----------|
| Phoenix 연동하기 | [04-phoenix-integration.md](04-phoenix-integration.md) |
| 한국어 RAG 최적화 | [05-korean-rag.md](05-korean-rag.md) |
| 프로덕션 배포 가이드 | [06-production-tips.md](06-production-tips.md) |

---

<div align="center">

[이전: 기본 평가](02-basic-evaluation.md) | [다음: Phoenix 통합](04-phoenix-integration.md)

</div>
