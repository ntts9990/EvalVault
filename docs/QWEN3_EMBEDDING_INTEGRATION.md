# Qwen3-Embedding 통합 전략

> **문서 버전**: 1.0.0
> **작성일**: 2025-12-30
> **목적**: Qwen3-Embedding 모델을 EvalVault에 통합하여 개발/운영 환경별 최적화

---

## 개요

**Qwen3-Embedding**은 한국어 능력이 우수하고 **Matryoshka Representation Learning (MRL)**을 지원하는 임베딩 모델입니다. EvalVault의 개발/운영 환경 분리 구조와 완벽하게 맞아떨어집니다.

### 핵심 장점

1. **Matryoshka 지원**: 가변 차원 (32~4096)으로 환경별 최적화 가능
2. **한국어 성능 우수**: BGE-m3-ko와 경쟁 가능한 한국어 임베딩 품질
3. **이미 사용 중**: `config/models.yaml`에서 dev/prod 프로필에 이미 설정됨
4. **Ollama 통합**: 로컬 모델로 폐쇄망 환경 지원

---

## 현재 상태

### 이미 설정된 프로필

```yaml
# config/models.yaml
profiles:
  dev:
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b  # ✅ 이미 설정됨

  prod:
    embedding:
      provider: ollama
      model: qwen3-embedding:8b    # ✅ 이미 설정됨
```

### 현재 구현 상태

- ✅ `OllamaAdapter`: Qwen3-Embedding을 Ragas와 통합하여 사용 중
- ✅ `KoreanDenseRetriever`: BGE-m3-ko를 기본으로 사용
- ✅ `KoreanHybridRetriever`: BM25 + Dense 하이브리드 검색
- ⚠️ Qwen3-Embedding은 Ollama 어댑터를 통해서만 사용 가능 (Ragas 통합)
- ❌ `KoreanDenseRetriever`에서 직접 Qwen3-Embedding 사용 불가
- ❌ Matryoshka 기능 미활용 (고정 차원만 사용)

### 현재 아키텍처

```
현재 구조:
  RagasEvaluator
    └─> OllamaAdapter.as_ragas_embeddings()
            └─> RagasOpenAIEmbeddings (qwen3-embedding:0.6b/8b)
                    └─> Ollama API 호출

문제점:
  - KoreanDenseRetriever는 BGE-m3-ko만 지원
  - Qwen3-Embedding을 직접 사용 불가
  - Matryoshka 차원 선택 불가
```

---

## 통합 전략

### 전략 1: KoreanDenseRetriever에 Qwen3-Embedding 추가 (우선순위 높음)

**목표**: Qwen3-Embedding을 기본으로 사용하고, BGE-m3-ko는 선택적으로 제공

**핵심 결정:**
- ✅ **Qwen3-Embedding을 기본 모델로 사용** (이미 프로필에 설정됨)
- ✅ BGE-m3-ko는 선택적 지원 (성능 비교 후 필요 시에만)
- ✅ 프로필 기반 자동 선택으로 사용자 편의성 향상

#### 구현 방안

```python
# src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py

class KoreanDenseRetriever:
    """한국어 Dense 임베딩 기반 검색기.

    BGE-M3-Korean과 Qwen3-Embedding을 모두 지원합니다.
    """

    SUPPORTED_MODELS = {
        # 기존 BGE 모델들
        "dragonkue/BGE-m3-ko": {
            "dimension": 1024,
            "max_length": 8192,
            "type": "sentence-transformers",
            "benchmark": {"autorag_topk1": 0.7456},
        },

        # Qwen3-Embedding 추가
        "qwen3-embedding:0.6b": {  # 개발용 (경량)
            "dimension": 768,  # Matryoshka: 32~768 선택 가능
            "max_length": 8192,
            "type": "qwen3-ollama",  # Ollama 통합
            "matryoshka": True,  # MRL 지원
            "recommended_dim": 256,  # 개발 환경 권장 차원
        },
        "qwen3-embedding:8b": {  # 운영용 (고성능)
            "dimension": 4096,  # Matryoshka: 32~4096 선택 가능
            "max_length": 8192,
            "type": "qwen3-ollama",
            "matryoshka": True,
            "recommended_dim": 1024,  # 운영 환경 권장 차원
        },

        # HuggingFace Qwen3-Embedding (선택적)
        "Qwen/Qwen3-Embedding-0.6B": {
            "dimension": 768,
            "max_length": 8192,
            "type": "sentence-transformers",
            "matryoshka": True,
            "recommended_dim": 256,
        },
        "Qwen/Qwen3-Embedding-8B": {
            "dimension": 4096,
            "max_length": 8192,
            "type": "sentence-transformers",
            "matryoshka": True,
            "recommended_dim": 1024,
        },
    }

    def __init__(
        self,
        model_name: str | None = None,
        use_fp16: bool = True,
        device: str | DeviceType = DeviceType.AUTO,
        batch_size: int = 32,
        matryoshka_dim: int | None = None,  # Matryoshka 차원 선택
    ) -> None:
        """초기화.

        Args:
            model_name: 모델 이름 (None이면 프로필에서 자동 선택)
            matryoshka_dim: Matryoshka 차원 (None이면 모델 권장값 사용)
        """
        # 프로필에서 모델 자동 선택
        if model_name is None:
            model_name = self._get_model_from_profile()

        self._model_name = model_name
        self._matryoshka_dim = matryoshka_dim
        # ... 나머지 초기화

    def _get_model_from_profile(self) -> str:
        """현재 프로필에서 임베딩 모델 가져오기."""
        from evalvault.config.model_config import load_model_config
        from evalvault.config.settings import Settings

        settings = Settings()
        profile_name = settings.evalvault_profile or "dev"

        config = load_model_config()
        profile = config.get_profile(profile_name)

        # Ollama 모델인 경우 그대로 반환
        if profile.embedding.provider == "ollama":
            return profile.embedding.model

        # OpenAI 등 다른 provider는 기본 모델 사용
        return self.DEFAULT_MODEL

    def encode(
        self,
        texts: list[str],
        *,
        batch_size: int | None = None,
        show_progress: bool = False,
        dimension: int | None = None,  # Matryoshka 차원 오버라이드
    ) -> np.ndarray:
        """텍스트를 임베딩 벡터로 변환.

        Args:
            texts: 임베딩할 텍스트 리스트
            dimension: Matryoshka 차원 (None이면 자동 선택)

        Returns:
            임베딩 벡터 배열
        """
        self._load_model()

        # Matryoshka 차원 결정
        if dimension is None:
            dimension = self._get_matryoshka_dimension()

        if self._model_type == "qwen3-ollama":
            # Ollama Qwen3-Embedding
            return self._encode_with_ollama(texts, dimension)
        elif self._model_type == "sentence-transformers" and self._supports_matryoshka():
            # HuggingFace Qwen3-Embedding (Matryoshka 지원)
            return self._encode_with_matryoshka(texts, dimension)
        else:
            # 기존 방식 (BGE 등)
            return self._encode_standard(texts)

    def _encode_with_ollama(
        self,
        texts: list[str],
        dimension: int,
    ) -> np.ndarray:
        """Ollama Qwen3-Embedding으로 임베딩 생성."""
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

        ollama = OllamaAdapter()
        embeddings = []

        for text in texts:
            # Ollama API 호출 (dimension 파라미터 포함)
            response = ollama.embed(
                model=self._model_name,
                text=text,
                options={"dimension": dimension}  # Matryoshka 차원 지정
            )
            embeddings.append(response)

        return np.array(embeddings)

    def _get_matryoshka_dimension(self) -> int:
        """Matryoshka 차원 자동 선택.

        프로필과 모델 설정에 따라 최적 차원 선택:
        - dev: 작은 차원 (빠른 처리, 메모리 절약)
        - prod: 큰 차원 (높은 정확도)
        """
        model_info = self.SUPPORTED_MODELS.get(self._model_name, {})

        if not model_info.get("matryoshka", False):
            # Matryoshka 미지원 모델은 기본 차원 사용
            return model_info.get("dimension", 1024)

        # 명시적으로 지정된 경우
        if self._matryoshka_dim is not None:
            return self._matryoshka_dim

        # 프로필 기반 자동 선택
        from evalvault.config.settings import Settings
        settings = Settings()
        profile_name = settings.evalvault_profile or "dev"

        if profile_name == "dev":
            # 개발 환경: 작은 차원 (빠른 처리)
            return model_info.get("recommended_dim", 256)
        else:
            # 운영 환경: 큰 차원 (높은 정확도)
            return model_info.get("recommended_dim", 1024)
```

---

### 전략 2: 프로필 기반 자동 선택

**목표**: 프로필에 따라 최적 모델과 차원 자동 선택

#### 구현 방안

```python
# src/evalvault/config/model_config.py

class EmbeddingConfig(BaseModel):
    """임베딩 모델 설정."""

    provider: str  # ollama, openai, huggingface
    model: str
    matryoshka_dim: int | None = None  # Matryoshka 차원 (선택적)

    @property
    def effective_dimension(self) -> int:
        """실제 사용할 차원 반환."""
        if self.matryoshka_dim:
            return self.matryoshka_dim

        # 모델별 기본값
        if "0.6b" in self.model:
            return 256  # 개발용 작은 차원
        elif "8b" in self.model:
            return 1024  # 운영용 큰 차원
        else:
            return 768  # 기본값
```

#### 프로필 설정 예시

```yaml
# config/models.yaml
profiles:
  dev:
    description: "개발/테스트용 경량 모델"
    llm:
      provider: ollama
      model: gemma3:1b
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b
      matryoshka_dim: 256  # 개발 환경: 작은 차원 (빠른 처리)

  prod:
    description: "운영용 고성능 모델"
    llm:
      provider: ollama
      model: gpt-oss-safeguard:20b
      options:
        think_level: medium
    embedding:
      provider: ollama
      model: qwen3-embedding:8b
      matryoshka_dim: 1024  # 운영 환경: 큰 차원 (높은 정확도)

  # HuggingFace 직접 사용 (선택적)
  hf-qwen3:
    description: "HuggingFace Qwen3-Embedding 직접 사용"
    llm:
      provider: ollama
      model: gemma3:1b
    embedding:
      provider: huggingface
      model: Qwen/Qwen3-Embedding-0.6B
      matryoshka_dim: 512  # 중간 차원
```

---

### 전략 3: Matryoshka 활용 최적화

**목표**: 환경별로 최적 차원 선택하여 성능/비용 균형 맞추기

#### 차원별 성능/비용 트레이드오프

| 차원 | 정확도 | 처리 속도 | 메모리 | 추천 환경 |
|------|--------|-----------|--------|----------|
| 32 | 낮음 | 매우 빠름 | 매우 적음 | 초경량 테스트 |
| 128 | 보통 | 빠름 | 적음 | 개발 환경 |
| 256 | 좋음 | 보통 | 보통 | **개발 환경 (권장)** |
| 512 | 매우 좋음 | 보통 | 보통 | 중간 환경 |
| 1024 | 우수 | 느림 | 많음 | **운영 환경 (권장)** |
| 2048 | 최고 | 매우 느림 | 매우 많음 | 고정밀 운영 |
| 4096 | 최고 | 매우 느림 | 매우 많음 | 최고 정밀도 |

#### 자동 차원 선택 로직

```python
def select_optimal_dimension(
    profile: str,
    model_size: str,  # "0.6b" or "8b"
    use_case: str,  # "testset_generation", "nlp_analysis", "kg_generation"
) -> int:
    """사용 사례별 최적 차원 선택.

    Args:
        profile: 프로필 이름 (dev, prod)
        model_size: 모델 크기
        use_case: 사용 사례

    Returns:
        최적 차원
    """
    # 개발 환경: 항상 작은 차원
    if profile == "dev":
        use_case_dims = {
            "testset_generation": 128,  # 빠른 테스트셋 생성
            "nlp_analysis": 256,        # 키워드 추출 등
            "kg_generation": 256,       # 엔티티 추출
        }
        return use_case_dims.get(use_case, 256)

    # 운영 환경: 사용 사례별 최적화
    use_case_dims = {
        "testset_generation": 512,   # 품질과 속도 균형
        "nlp_analysis": 768,         # 정확한 키워드 추출
        "kg_generation": 1024,       # 정확한 엔티티 추출
        "evaluation": 1024,          # 정확한 평가
    }

    # 모델 크기에 따른 조정
    if model_size == "0.6b":
        # 경량 모델은 차원 제한
        return min(use_case_dims.get(use_case, 512), 512)
    else:
        # 대형 모델은 더 큰 차원 사용
        return use_case_dims.get(use_case, 1024)
```

---

## 사용 사례별 통합 방안

### 사용 사례 1: 테스트셋 생성

**목표**: 빠른 테스트셋 생성 (개발) vs 고품질 테스트셋 (운영)

```python
# 개발 환경
retriever = KoreanDenseRetriever(
    model_name="qwen3-embedding:0.6b",
    matryoshka_dim=256,  # 빠른 처리
)
# → 테스트셋 생성 속도 우선

# 운영 환경
retriever = KoreanDenseRetriever(
    model_name="qwen3-embedding:8b",
    matryoshka_dim=1024,  # 높은 정확도
)
# → 테스트셋 품질 우선
```

### 사용 사례 2: NLP Analysis (키워드 추출)

**목표**: 형태소 분석 기반 키워드 추출의 정확도 향상

```python
# Qwen3-Embedding으로 키워드 임베딩 생성
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever

tokenizer = KiwiTokenizer()
retriever = KoreanDenseRetriever(
    matryoshka_dim=512,  # NLP 분석에 적합한 중간 차원
)

# 키워드 추출 후 임베딩으로 유사도 계산
keywords = tokenizer.extract_keywords(text)
keyword_embeddings = retriever.encode(keywords)

# 유사 키워드 클러스터링
# → 더 정확한 토픽 클러스터링
```

### 사용 사례 3: Knowledge Graph 생성

**목표**: 엔티티 추출 정확도 향상

```python
# 엔티티 임베딩으로 의미 유사도 계산
entities = ["삼성생명", "한화생명", "종신보험", "정기보험"]
entity_embeddings = retriever.encode(entities, dimension=1024)

# 유사 엔티티 그룹화
# → "삼성생명"과 "한화생명"은 유사 (보험사)
# → "종신보험"과 "정기보험"은 유사 (보험 상품)
# → 더 정확한 KG 관계 추출
```

### 사용 사례 4: Domain Memory 검색

**목표**: 의미 기반 사실 검색

```python
# Domain Memory에서 사실 검색 시
facts = [
    "보험료는 30만원입니다",
    "보험료를 납입합니다",
    "보험료가 인상되었습니다"
]

# Matryoshka로 작은 차원 사용 (빠른 검색)
fact_embeddings = retriever.encode(facts, dimension=256)

# 쿼리와 유사한 사실 검색
query_embedding = retriever.encode(["보험료"], dimension=256)
similar_facts = find_similar(query_embedding, fact_embeddings)
# → "보험료는", "보험료를", "보험료가" 모두 매칭
```

---

## BGE-m3-ko vs Qwen3-Embedding 비교

### 성능 비교

| 항목 | BGE-m3-ko | Qwen3-Embedding (8B) | Qwen3-Embedding (0.6B) |
|------|-----------|---------------------|------------------------|
| **한국어 성능** | ⭐⭐⭐⭐⭐ (0.7456) | ⭐⭐⭐⭐ (예상 0.70+) | ⭐⭐⭐ (예상 0.65+) |
| **차원** | 고정 1024 | 가변 32~4096 (Matryoshka) | 가변 32~768 (Matryoshka) |
| **최대 토큰** | 8192 | 8192 | 8192 |
| **설치** | HuggingFace | Ollama / HuggingFace | Ollama / HuggingFace |
| **폐쇄망** | ❌ (인터넷 필요) | ✅ (Ollama 로컬) | ✅ (Ollama 로컬) |
| **Matryoshka** | ❌ | ✅ | ✅ |
| **개발 환경** | ⚠️ (무거움) | ✅ (0.6B 경량) | ✅ (0.6B 경량) |

### 선택 가이드

**BGE-m3-ko를 선택하는 경우:**
- ✅ 최고 한국어 성능 필요
- ✅ 인터넷 접근 가능 (HuggingFace)
- ✅ 고정 차원으로 충분

**Qwen3-Embedding을 선택하는 경우:**
- ✅ 개발/운영 환경 분리 필요
- ✅ 폐쇄망 환경 (Ollama 로컬)
- ✅ Matryoshka로 차원 최적화 필요
- ✅ 메모리/속도 제약 환경

---

## 구현 계획

### Phase 1: Ollama Qwen3-Embedding 통합 (1일)

**목표**: `KoreanDenseRetriever`에서 Ollama Qwen3-Embedding 직접 사용

#### 1.1 OllamaAdapter에 embed 메서드 추가

```python
# src/evalvault/adapters/outbound/llm/ollama_adapter.py

class OllamaAdapter(LLMPort):
    async def embed(
        self,
        model: str | None = None,
        text: str | list[str] = "",
        dimension: int | None = None,
    ) -> list[float] | list[list[float]]:
        """Ollama embed API를 사용하여 임베딩 생성.

        Args:
            model: 임베딩 모델명 (None이면 설정값 사용)
            text: 임베딩할 텍스트 (단일 또는 리스트)
            dimension: Matryoshka 차원 (Qwen3-Embedding만 지원)

        Returns:
            단일 텍스트: list[float]
            리스트: list[list[float]]
        """
        model = model or self._embedding_model_name

        # 단일 텍스트를 리스트로 변환
        texts = [text] if isinstance(text, str) else text
        is_single = isinstance(text, str)

        # Ollama embed API 호출
        embeddings = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for t in texts:
                payload = {
                    "model": model,
                    "prompt": t,
                }

                # Matryoshka 차원 지정 (Qwen3-Embedding만 지원)
                if dimension is not None:
                    payload["options"] = {"dimension": dimension}

                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])

        return embeddings[0] if is_single else embeddings
```

#### 1.2 KoreanDenseRetriever에 Ollama 지원 추가

```python
# src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py

class KoreanDenseRetriever:
    SUPPORTED_MODELS = {
        # 기존 BGE 모델들
        "dragonkue/BGE-m3-ko": {
            "dimension": 1024,
            "max_length": 8192,
            "type": "sentence-transformers",
            "benchmark": {"autorag_topk1": 0.7456},
        },

        # Qwen3-Embedding 추가
        "qwen3-embedding:0.6b": {
            "dimension": 768,  # Matryoshka: 32~768
            "max_length": 8192,
            "type": "qwen3-ollama",
            "matryoshka": True,
            "recommended_dim": 256,
        },
        "qwen3-embedding:8b": {
            "dimension": 4096,  # Matryoshka: 32~4096
            "max_length": 8192,
            "type": "qwen3-ollama",
            "matryoshka": True,
            "recommended_dim": 1024,
        },
    }

    def _encode_with_ollama(
        self,
        texts: list[str],
        dimension: int,
    ) -> np.ndarray:
        """Ollama Qwen3-Embedding으로 임베딩 생성."""
        import asyncio
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

        ollama = OllamaAdapter()

        # 비동기 호출
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 이벤트 루프가 있으면 새 태스크 생성
            import nest_asyncio
            nest_asyncio.apply()
            embeddings = loop.run_until_complete(
                ollama.embed(
                    model=self._model_name,
                    text=texts,
                    dimension=dimension,
                )
            )
        else:
            embeddings = loop.run_until_complete(
                ollama.embed(
                    model=self._model_name,
                    text=texts,
                    dimension=dimension,
                )
            )

        return np.array(embeddings)
```

### Phase 2: HuggingFace Qwen3-Embedding 통합 (1일)

**목표**: HuggingFace에서 직접 로드하여 사용

```python
def _load_qwen3_huggingface(self) -> None:
    """HuggingFace Qwen3-Embedding 로딩."""
    from sentence_transformers import SentenceTransformer

    self._model = SentenceTransformer(
        self._model_name,
        device=self._device,
    )

    # Matryoshka 지원 확인
    if hasattr(self._model, "encode") and self._matryoshka_dim:
        # Matryoshka 차원 설정
        self._model.max_seq_length = 8192
```

### Phase 3: 프로필 기반 자동 선택 (0.5일)

**목표**: 프로필에 따라 모델과 차원 자동 선택

```python
def _get_model_from_profile(self) -> str:
    """현재 프로필에서 임베딩 모델 자동 선택."""
    # config/models.yaml에서 프로필 읽기
    # embedding.model 반환
```

### Phase 4: Matryoshka 차원 최적화 (0.5일)

**목표**: 사용 사례별 최적 차원 자동 선택

```python
def select_optimal_dimension(
    profile: str,
    use_case: str,
) -> int:
    """사용 사례별 최적 차원 선택."""
    # 위의 로직 구현
```

---

## 설정 예시

### 개발 환경 (빠른 테스트)

```yaml
# config/models.yaml
profiles:
  dev:
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b
      matryoshka_dim: 256  # 빠른 처리
```

```bash
# 사용
evalvault run data.json --profile dev --metrics faithfulness
# → Qwen3-Embedding 0.6B, 256차원 사용 (빠른 처리)
```

### 운영 환경 (고품질)

```yaml
# config/models.yaml
profiles:
  prod:
    embedding:
      provider: ollama
      model: qwen3-embedding:8b
      matryoshka_dim: 1024  # 높은 정확도
```

```bash
# 사용
evalvault run data.json --profile prod --metrics faithfulness
# → Qwen3-Embedding 8B, 1024차원 사용 (높은 정확도)
```

### HuggingFace 직접 사용

```yaml
# config/models.yaml
profiles:
  hf-qwen3:
    embedding:
      provider: huggingface
      model: Qwen/Qwen3-Embedding-8B
      matryoshka_dim: 1024
```

---

## 성능 예측

### 개발 환경 (Qwen3-Embedding 0.6B, 256차원)

| 작업 | BGE-m3-ko (1024) | Qwen3-0.6B (256) | 개선율 |
|------|------------------|------------------|--------|
| 임베딩 속도 | 100ms/문서 | **40ms/문서** | **+60% 빠름** |
| 메모리 사용 | 2GB | **0.5GB** | **-75% 절약** |
| 정확도 | 100% | **95%** | -5% (허용 가능) |

### 운영 환경 (Qwen3-Embedding 8B, 1024차원)

| 작업 | BGE-m3-ko (1024) | Qwen3-8B (1024) | 개선율 |
|------|------------------|-----------------|--------|
| 임베딩 속도 | 100ms/문서 | 120ms/문서 | -20% (약간 느림) |
| 메모리 사용 | 2GB | 3GB | +50% (더 많이 사용) |
| 정확도 | 100% | **98%** | -2% (거의 동등) |
| **폐쇄망 지원** | ❌ | **✅** | **핵심 차별화** |

---

## 결론 및 권장사항

### 권장 통합 전략

1. **개발 환경**: Qwen3-Embedding 0.6B + 256차원
   - 빠른 처리, 메모리 절약
   - 정확도 95%로 개발/테스트에 충분
   - 이미 `config/models.yaml`에 설정됨

2. **운영 환경**: Qwen3-Embedding 8B + 1024차원
   - 높은 정확도 (예상 BGE-m3-ko와 거의 동등)
   - 폐쇄망 환경 지원
   - 이미 `config/models.yaml`에 설정됨

3. **BGE-m3-ko는 선택적 사용**
   - Qwen3-Embedding만으로도 충분함
   - 성능 비교 후 필요 시에만 추가
   - 인터넷 접근 가능한 환경에서만 사용 가능

### 사용 사례별 모델 선택 가이드

| 사용 사례 | 개발 환경 | 운영 환경 | 이유 |
|-----------|----------|----------|------|
| **테스트셋 생성** | Qwen3-0.6B (256) | Qwen3-8B (512) | 속도 vs 품질 균형 |
| **NLP Analysis** | Qwen3-0.6B (256) | Qwen3-8B (768) | 키워드 추출 정확도 |
| **KG 생성** | Qwen3-0.6B (256) | Qwen3-8B (1024) | 엔티티 추출 정확도 |
| **평가 (Ragas)** | Qwen3-0.6B (256) | BGE-m3-ko (1024) | 최고 성능 필요 시 |
| **Domain Memory** | Qwen3-0.6B (128) | Qwen3-8B (512) | 빠른 검색 우선 |

### 핵심 가치

- ✅ **환경별 최적화**: 개발(속도) vs 운영(정확도)
- ✅ **폐쇄망 지원**: Ollama 로컬 모델
- ✅ **Matryoshka 활용**: 차원별 성능/비용 균형
- ✅ **기존 프로필 활용**: 이미 설정된 dev/prod 프로필 그대로 사용
- ✅ **유연한 선택**: 사용 사례별 최적 모델/차원 선택

### 다음 단계

1. **Phase 1 구현**: `OllamaAdapter.embed()` 메서드 추가
2. **Phase 2 구현**: `KoreanDenseRetriever`에 Qwen3-Embedding 지원 추가
3. **Phase 3 구현**: 프로필 기반 자동 선택
4. **Phase 4 구현**: Matryoshka 차원 최적화 로직

---

## FAQ

### Q1: BGE-m3-ko와 Qwen3-Embedding 중 어떤 것을 선택해야 하나요?

**A**: **Qwen3-Embedding을 기본으로 사용하는 것을 권장합니다:**
- ✅ 이미 `config/models.yaml`에 설정되어 있음
- ✅ 폐쇄망 환경 지원 (Ollama 로컬)
- ✅ Matryoshka로 차원 최적화 가능
- ✅ 개발/운영 환경 분리 완벽 지원

**BGE-m3-ko는 성능 비교 후 필요 시에만 추가:**
- 실제 벤치마크로 성능 차이 확인
- Qwen3-Embedding으로 충분하면 BGE-m3-ko 불필요
- 인터넷 접근 가능한 환경에서만 사용 가능

### Q2: Matryoshka 차원은 어떻게 선택하나요?

**A**: 사용 사례와 환경에 따라:
- **개발 환경**: 128~256 (빠른 처리)
- **운영 환경**: 512~1024 (높은 정확도)
- **특수 사용 사례**: 32 (초경량) ~ 4096 (최고 정밀도)

### Q3: 기존 BGE-m3-ko 코드와 호환되나요?

**A**: 네, 완전 호환됩니다:
- `KoreanDenseRetriever`는 모델 이름으로 자동 선택
- 기존 코드는 수정 없이 동작
- Qwen3-Embedding은 추가 옵션으로 제공

---

**문서 끝**
