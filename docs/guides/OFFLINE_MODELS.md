# 오프라인 모델 캐시 준비 가이드

EvalVault 오프라인 환경에서 NLP 분석용 모델을 미리 다운로드/배포하는 절차입니다.

## 대상 모델

기본 한국어 NLP 모델 (Hugging Face):

- dragonkue/BGE-m3-ko
- upskyy/bge-m3-korean
- BAAI/bge-m3
- jhgan/ko-sroberta-multitask
- intfloat/multilingual-e5-large

추가 모델을 포함하려면 MODELS에 콤마로 지정하세요. (예: ModernBERT/mmBERT)

## 1) 온라인에서 모델 캐시 생성

```bash
uv sync --extra korean

# 기본 모델 세트 다운로드
OUTPUT_TAR=dist/evalvault_model_cache.tar \
  CACHE_ROOT=model_cache \
  INCLUDE_KIWI=1 \
  ./scripts/offline/bundle_model_cache.sh
```

### 모델을 직접 지정하려면

```bash
MODELS="dragonkue/BGE-m3-ko,jhgan/ko-sroberta-multitask" \
  OUTPUT_TAR=dist/evalvault_model_cache.tar \
  CACHE_ROOT=model_cache \
  ./scripts/offline/bundle_model_cache.sh
```

## 2) 오프라인으로 전달

다음 파일을 폐쇄망으로 전달합니다:

- dist/evalvault_model_cache.tar
- dist/evalvault_model_cache.tar.sha256

## 3) 오프라인에서 복원

```bash
./scripts/offline/restore_model_cache.sh dist/evalvault_model_cache.tar
```

## 4) 컨테이너에 캐시 마운트

호스트에 생성된 `model_cache/`를 컨테이너에 마운트하세요.

```yaml
services:
  evalvault-api:
    environment:
      HF_HOME: /app/model_cache/hf
      HF_HUB_CACHE: /app/model_cache/hf/hub
      TRANSFORMERS_CACHE: /app/model_cache/hf/hub
      SENTENCE_TRANSFORMERS_HOME: /app/model_cache/sentence-transformers
      HF_HUB_OFFLINE: "1"
      TRANSFORMERS_OFFLINE: "1"
    volumes:
      - ./model_cache:/app/model_cache
```

## vLLM 임베딩 사용 (옵션)

vLLM 서버에 임베딩 모델을 올려둔 경우, 프로필을 vllm으로 설정하면
Ollama 없이도 임베딩을 사용합니다.

```bash
EVALVAULT_PROFILE=vllm
VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
```

## 5) 검증

```bash
uv run evalvault analyze <RUN_ID> --nlp
```

NLP 분석이 인터넷 없이 동작하면 정상입니다.
