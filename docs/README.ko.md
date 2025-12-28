# EvalVault (한국어)

> RAG(Retrieval-Augmented Generation) 시스템 품질 평가를 위한 올인원 솔루션.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![Ragas](https://img.shields.io/badge/Ragas-v1.0-green.svg)](https://docs.ragas.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../LICENSE.md)
[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?style=for-the-badge&logo=python&logoColor=FFD343)](https://www.python.org/psf/membership/)

English version? See the root [README.md](../README.md).

---

## 개요

EvalVault는 구조화된 데이터셋을 Ragas v1.0 메트릭에 연결해 Typer CLI로 평가를 실행하고,
SQLite 또는 Langfuse에 결과를 저장합니다. OpenAI, Ollama, 폐쇄망 프로필을 모두 지원하며
재현 가능한 RAG 평가 파이프라인을 제공합니다.

## 주요 특징

- Typer 기반 CLI로 평가·비교·내보내기를 한 번에 수행
- OpenAI/Ollama 프로필 기반 의존성 주입
- Langfuse 연동으로 트레이스 단위 분석
- JSON/CSV/Excel 데이터 로더
- Linux·macOS·Windows 호환

## 빠른 시작

```bash
uv pip install evalvault
evalvault run data.json --metrics faithfulness
```

## 핵심 기능

- Ragas v1.0 기반 6가지 표준 메트릭
- 버전 메타데이터를 포함한 JSON/CSV/Excel 데이터셋
- SQLite + Langfuse 자동 결과 저장
- Ollama 프로필을 통한 폐쇄망/온프레미스 지원
- 간결한 CLI UX

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

## 첫 평가 실행

```bash
# 1. 환경 변수 구성
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
| `context_recall` | 필요한 정보를 검색했는지 | 필요 |
| `factual_correctness` | 답변과 정답의 사실적 일치 여부 | 필요 |
| `semantic_similarity` | 답변과 정답의 의미적 유사도 | 필요 |

## CLI 명령어

```bash
evalvault run data.json --metrics faithfulness,answer_relevancy
evalvault run data.json --profile dev --metrics faithfulness    # Ollama
evalvault run data.json -p openai --metrics faithfulness        # OpenAI
evalvault run data.json --metrics faithfulness --langfuse       # Langfuse
evalvault history --limit 10
evalvault compare <run_id1> <run_id2>
evalvault export <run_id> -o result.json
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

> `thresholds`: 메트릭별 통과 기준 (0.0~1.0). 기본값 0.7.

### CSV

```csv
id,question,answer,contexts,ground_truth
tc-001,"보험금은 얼마인가요?","1억원입니다.","[""사망보험금은 1억원입니다.""]","1억원"
```

## 환경 설정

```bash
# .env 예시

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Ollama 설정 (폐쇄망)

1. 설치
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. 모델 다운로드
   ```bash
   ollama pull gemma3:1b
   ollama pull qwen3-embedding:0.6b
   ```
3. 프로필로 실행
   ```bash
   evalvault run data.json --profile dev --metrics faithfulness
   ```

## 모델 프로필 (`config/models.yaml`)

| 프로필 | LLM | Embedding | 용도 |
|--------|-----|-----------|------|
| `dev` | gemma3:1b (Ollama) | qwen3-embedding:0.6b | 개발/테스트 |
| `prod` | gpt-oss-safeguard:20b (Ollama) | qwen3-embedding:8b | 운영 환경 |
| `openai` | gpt-5-nano | text-embedding-3-small | 외부망 |

## 아키텍처

```
EvalVault/
├── config/               # 모델 프로필, 런타임 설정
├── src/evalvault/        # 도메인 · 포트 · 어댑터
├── docs/                 # 가이드, 아키텍처, 로드맵
└── tests/                # unit / integration / e2e_data
```

## 문서

| 문서 | 설명 |
|------|------|
| [USER_GUIDE.md](USER_GUIDE.md) | 설치, 설정, 문제 해결 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 헥사고날 아키텍처 상세 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 기여 가이드 |

## 개발

```bash
pytest tests/ -v
pytest tests/integration/test_e2e_scenarios.py -v   # 외부 API 필요
ruff check src/ tests/
ruff format src/ tests/
```

## 커뮤니티 & PSF 멤버십

EvalVault는 [Python Software Foundation](https://www.python.org/psf/) Supporting Member가
주도하는 프로젝트입니다. 오픈소스 생태계와 파이썬 커뮤니티에 기여하는 것이 목표입니다.

<p align="left">
  <a href="https://www.python.org/psf/membership/">
    <img src="./assets/psf-supporting-member.png" alt="PSF Supporting Member" width="130" />
  </a>
</p>

## 라이선스

Apache 2.0 - [LICENSE.md](../LICENSE.md) 참조.

---

<div align="center">
  <strong>EvalVault</strong> - RAG 평가의 새로운 기준.
</div>
