# EvalVault

> RAG(Retrieval-Augmented Generation) 시스템 품질 평가를 위한 올인원 솔루션

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![Ragas](https://img.shields.io/badge/Ragas-v1.0-green.svg)](https://docs.ragas.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

---

## Overview (English)

EvalVault is an end-to-end evaluation harness for Retrieval-Augmented Generation (RAG)
systems. It plugs into structured datasets, runs Ragas v1.0 metrics, and ships results to
SQLite or Langfuse for longitudinal tracking.

### Highlights

- Batteries-included Typer CLI for running, comparing, and exporting evaluation runs
- Profile-driven model wiring with OpenAI and Ollama defaults
- Optional Langfuse integration for trace-level inspection
- Dataset loaders for JSON, CSV, and Excel sources
- Cross-platform support (Linux, macOS, Windows)

### Quick Start (EN)

```bash
uv pip install evalvault
evalvault run data.json --metrics faithfulness
```

## 핵심 기능

- **6가지 평가 메트릭**: Ragas v1.0 기반 표준화된 RAG 평가
- **다중 데이터 포맷**: JSON, CSV, Excel 지원
- **자동 결과 저장**: SQLite (로컬) + Langfuse (클라우드/셀프호스팅)
- **폐쇄망 지원**: Ollama 기반 로컬 LLM 평가 (프로필 기반 설정)
- **CLI 인터페이스**: 간편한 명령줄 도구
- **크로스 플랫폼**: Linux, macOS, Windows 지원

## 설치

### PyPI (권장)

```bash
uv pip install evalvault
```

### 개발 환경

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv pip install -e ".[dev]"
```

## 빠른 시작

```bash
# 1. 환경 설정
cp .env.example .env
echo "OPENAI_API_KEY=sk-your-key" >> .env

# 2. 평가 실행
evalvault run data.json --metrics faithfulness

# 3. 결과 확인
evalvault history
```

## 지원 메트릭

| 메트릭 | 설명 | Ground Truth |
|--------|------|--------------|
| `faithfulness` | 답변이 컨텍스트에 충실한지 (환각 감지) | 불필요 |
| `answer_relevancy` | 답변이 질문과 관련있는지 | 불필요 |
| `context_precision` | 검색된 컨텍스트의 정밀도 | 필요 |
| `context_recall` | 필요한 정보가 검색되었는지 | 필요 |
| `factual_correctness` | 답변이 정답과 사실적으로 일치하는지 | 필요 |
| `semantic_similarity` | 답변과 정답의 의미적 유사도 | 필요 |

## CLI 명령어

```bash
# 평가 실행
evalvault run data.json --metrics faithfulness,answer_relevancy

# 프로필 지정 (Ollama)
evalvault run data.json --profile dev --metrics faithfulness

# 프로필 지정 (OpenAI)
evalvault run data.json -p openai --metrics faithfulness

# Langfuse 연동
evalvault run data.json --metrics faithfulness --langfuse

# 히스토리 조회
evalvault history --limit 10

# 결과 비교
evalvault compare <run_id1> <run_id2>

# 결과 내보내기
evalvault export <run_id> -o result.json

# 설정 확인
evalvault config
```

## 데이터 형식

### JSON (권장)

```json
{
  "name": "my-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "보험금은 얼마인가요?",
      "answer": "1억원입니다.",
      "contexts": ["사망보험금은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

> **thresholds**: 메트릭별 통과 기준 (0.0~1.0). 미지정 시 기본값 0.7

### CSV

```csv
id,question,answer,contexts,ground_truth
tc-001,"보험금은?","1억원입니다.","[""사망보험금은 1억원""]","1억원"
```

## 환경 설정

```bash
# .env 파일

# OpenAI 설정
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano               # 선택 (기본값)

# Ollama 설정 (폐쇄망)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# Langfuse 연동 (선택)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Ollama 설정 (폐쇄망)

폐쇄망 환경에서 로컬 LLM을 사용하려면 Ollama를 설치해야 합니다.

### 1. Ollama 설치

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# https://ollama.com/download 에서 설치 파일 다운로드
```

### 2. 모델 다운로드

```bash
# 개발용 (dev 프로필)
ollama pull gemma3:1b
ollama pull qwen3-embedding:0.6b

# 운영용 (prod 프로필) - 사내 모델 예시
ollama pull gpt-oss-safeguard:20b
ollama pull qwen3-embedding:8b
```

### 3. 프로필로 실행

```bash
# Ollama dev 프로필 사용
evalvault run data.json --profile dev --metrics faithfulness
```

### 모델 프로필 (config/models.yaml)

| 프로필 | LLM | Embedding | 용도 |
|--------|-----|-----------|------|
| `dev` | gemma3:1b (Ollama) | qwen3-embedding:0.6b | 개발/테스트 |
| `prod` | gpt-oss-safeguard:20b (Ollama) | qwen3-embedding:8b | 운영 환경 |
| `openai` | gpt-5-nano | text-embedding-3-small | 외부망 |

## 아키텍처

```
EvalVault/
├── config/
│   └── models.yaml       # 모델 프로필
├── src/evalvault/
│   ├── domain/           # 비즈니스 로직
│   │   ├── entities/     # TestCase, Dataset, EvaluationRun
│   │   ├── services/     # RagasEvaluator
│   │   └── metrics/      # 커스텀 메트릭
│   ├── ports/            # 인터페이스
│   │   ├── inbound/      # EvaluatorPort
│   │   └── outbound/     # LLMPort, StoragePort, TrackerPort
│   ├── adapters/         # 구현체
│   │   ├── inbound/      # CLI (Typer)
│   │   └── outbound/     # OpenAI, Ollama, SQLite, Langfuse
│   └── config/           # Settings, ModelConfig
└── .env                  # 환경 변수 (gitignore)
```

## 문서

| 문서 | 설명 |
|-----|------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | 설치, 설정, 메트릭 설명, 문제 해결 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hexagonal Architecture 상세 설명 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여 가이드라인 |

## 개발

```bash
# 테스트 실행
pytest tests/ -v

# E2E 테스트 (실제 API 호출)
pytest tests/integration/test_e2e_scenarios.py -v

# 린트
ruff check src/
ruff format src/
```

## 라이선스

Apache 2.0 - See [LICENSE.md](LICENSE.md)

---

<div align="center">

**EvalVault** - RAG 평가의 새로운 기준

</div>
