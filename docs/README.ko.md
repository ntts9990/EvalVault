# EvalVault (한국어)

> RAG(Retrieval-Augmented Generation) 시스템 품질 평가를 위한 올인원 솔루션.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![Ragas](https://img.shields.io/badge/Ragas-v1.0-green.svg)](https://docs.ragas.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../LICENSE.md)
[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?logo=python&logoColor=FFD343)](https://www.python.org/psf/membership/)

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
# PyPI를 통한 설치
uv pip install evalvault
evalvault run data.json --metrics faithfulness

# 또는 소스에서 설치 (개발 환경 권장)
git clone https://github.com/ntts9990/EvalVault.git && cd EvalVault
uv sync --extra dev
uv run evalvault run tests/fixtures/sample_dataset.json --metrics faithfulness
```

> **왜 uv인가?** EvalVault는 빠르고 안정적인 의존성 관리를 위해 [uv](https://docs.astral.sh/uv/)를 사용합니다. 소스에서 실행할 때는 모든 명령어 앞에 `uv run`을 붙여야 합니다.

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

### 개발 환경 (소스에서 설치)

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

> **참고**: `.python-version` 파일이 Python 3.12를 지정합니다. uv가 Python 3.12를 자동으로 다운로드하여 사용합니다.

---

## 완전 설정 가이드 (git clone → 평가 저장 완료)

이 섹션은 저장소 클론부터 Langfuse 추적 및 SQLite 저장을 포함한 평가 실행까지 모든 단계를 안내합니다.

### 사전 요구사항

| 요구사항 | 버전 | 설치 방법 |
|----------|------|-----------|
| **Python** | 3.12.x | uv가 자동 설치 |
| **uv** | 최신 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Docker** | 최신 | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Ollama** | 최신 | `curl -fsSL https://ollama.com/install.sh \| sh` |

### 1단계: 클론 및 의존성 설치

```bash
# 저장소 클론
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# 의존성 설치 (.python-version으로 Python 3.12 자동 선택)
uv sync --extra dev

# Python 버전 확인
uv run python --version
# 예상 출력: Python 3.12.x
```

### 2단계: Ollama 설정 (로컬 LLM)

EvalVault는 폐쇄망/로컬 LLM 평가를 위해 Ollama를 사용합니다. Ollama 서버를 시작하고 필요한 모델을 다운로드하세요:

```bash
# Ollama 서버 시작 (백그라운드 실행)
ollama serve &

# dev 프로필에 필요한 모델 다운로드
ollama pull gemma3:1b              # 평가용 LLM
ollama pull qwen3-embedding:0.6b   # 임베딩 모델

# 설치된 모델 확인
ollama list
```

**예상 출력:**
```
NAME                    SIZE
gemma3:1b               815 MB
qwen3-embedding:0.6b    639 MB
```

### 3단계: Langfuse 시작 (평가 추적)

Langfuse는 트레이스 레벨 검사 및 평가 실행의 이력 비교를 제공합니다.

```bash
# Docker Compose로 Langfuse 시작
docker compose -f docker-compose.langfuse.yml up -d

# 모든 컨테이너가 healthy 상태인지 확인
docker compose -f docker-compose.langfuse.yml ps
```

**예상 컨테이너:**
| 컨테이너 | 포트 | 상태 |
|----------|------|------|
| langfuse-web | 3000 | healthy |
| langfuse-worker | 3030 | healthy |
| postgres | 5432 | healthy |
| clickhouse | 8123 | healthy |
| redis | 6379 | healthy |
| minio | 9090 | healthy |

### 4단계: Langfuse 프로젝트 및 API 키 생성

1. 브라우저에서 http://localhost:3000 열기
2. **Sign Up** - 계정 생성 (이메일 + 비밀번호)
3. **New Organization** - 조직 생성 (예: "EvalVault")
4. **New Project** - 프로젝트 생성 (예: "RAG-Evaluation")
5. **Settings → API Keys** - 새 API 키 생성
6. **Public Key** (`pk-lf-...`)와 **Secret Key** (`sk-lf-...`) 복사

### 5단계: 환경 변수 설정

설정 파일 `.env`를 생성합니다:

```bash
# 예제 파일 복사
cp .env.example .env
```

`.env` 파일을 편집합니다:

```bash
# EvalVault 설정
EVALVAULT_PROFILE=dev

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# Langfuse 설정 (여기에 키를 붙여넣으세요)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3000
```

### 6단계: 첫 번째 평가 실행

```bash
# 샘플 데이터셋으로 평가 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy

# 예상 출력:
# ╭───────────────────────────── Evaluation Results ─────────────────────────────╮
# │ Evaluation Summary                                                           │
# │   Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                               │
# │   Dataset: test_dataset v1.0.0                                               │
# │   Model: ollama/gemma3:1b                                                    │
# │   Duration: ~45s                                                             │
# │ Results                                                                      │
# │   Total Test Cases: 4                                                        │
# │   Passed: 4                                                                  │
# │   Pass Rate: 100.0%                                                          │
# ╰──────────────────────────────────────────────────────────────────────────────╯
```

### 7단계: 저장 옵션을 포함한 평가 실행

결과를 Langfuse와 SQLite 모두에 저장합니다:

```bash
# Langfuse 추적 + SQLite 저장으로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy \
  --langfuse \
  --db evalvault.db

# 예상 출력에 포함되는 내용:
# Logged to Langfuse (trace_id: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
# Results saved to database: evalvault.db
# Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 8단계: 저장된 결과 확인

**SQLite 이력:**
```bash
uv run evalvault history --db evalvault.db

# ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
# ┃ Run ID      ┃ Dataset    ┃ Model       ┃ Started At ┃ Pass Rate ┃ Test Cases ┃
# ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
# │ 51f0286a... │ test_data… │ ollama/gem… │ 2025-12-29 │    100.0% │          4 │
# └─────────────┴────────────┴─────────────┴────────────┴───────────┴────────────┘
```

**Langfuse 대시보드:**
- http://localhost:3000 열기
- **Traces** 탭으로 이동
- 각 평가 실행의 상세 트레이스 정보 확인

### 빠른 참조

| 작업 | 명령어 |
|------|--------|
| 평가 실행 | `uv run evalvault run data.json --metrics faithfulness` |
| 저장 옵션 포함 실행 | `uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db` |
| 이력 조회 | `uv run evalvault history --db evalvault.db` |
| 메트릭 목록 | `uv run evalvault metrics` |
| 설정 확인 | `uv run evalvault config` |
| Langfuse 중지 | `docker compose -f docker-compose.langfuse.yml down` |

---

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

> **참고**: 소스에서 실행할 때는 모든 명령어 앞에 `uv run`을 붙이세요. PyPI로 설치한 경우 `evalvault`만 사용합니다.

```bash
# 평가 실행
uv run evalvault run data.json --metrics faithfulness,answer_relevancy

# Langfuse 추적 + SQLite 저장으로 실행
uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db

# 병렬 평가 (대용량 데이터셋에 효과적)
uv run evalvault run data.json --metrics faithfulness --parallel --batch-size 10

# Ollama 프로필 선택
uv run evalvault run data.json --profile dev --metrics faithfulness

# OpenAI 프로필 선택
uv run evalvault run data.json -p openai --metrics faithfulness

# 이력 조회
uv run evalvault history --db evalvault.db --limit 10

# 실행 비교
uv run evalvault compare <run_id1> <run_id2> --db evalvault.db

# 결과 내보내기
uv run evalvault export <run_id> -o result.json --db evalvault.db

# 설정 확인
uv run evalvault config

# 사용 가능한 메트릭 목록
uv run evalvault metrics
```

## A/B 테스트 가이드

EvalVault는 모델, 프롬프트, 설정 등을 비교하는 A/B 테스트를 지원합니다. 이 가이드는 실험의 전체 과정을 안내합니다.

### 1단계: 실험 생성

```bash
uv run evalvault experiment-create \
  --name "모델 비교" \
  --hypothesis "큰 모델이 answer_relevancy에서 더 높은 점수를 받을 것" \
  --db experiment.db
```

출력:
```
Created experiment: 20421536-e09a-4255-89a3-c402b2b80a2d
  Name: 모델 비교
  Status: draft
```

> 실험 ID를 저장해두세요. 이후 단계에서 사용합니다.

### 2단계: 그룹 추가 (A/B)

비교할 두 그룹을 생성합니다:

```bash
# 그룹 A: 기준 모델
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "baseline" \
  -d "gemma3:1b (1B 파라미터)" \
  --db experiment.db

# 그룹 B: 도전 모델
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "challenger" \
  -d "gemma3n:e2b (4.5B 파라미터)" \
  --db experiment.db
```

### 3단계: 평가 실행

각 그룹에 대해 다른 설정으로 평가를 실행합니다:

```bash
# 그룹 A: 기준 모델로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3:1b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# 출력에서 Run ID를 저장 (예: 34f364e9-cd28-4cf9-a93d-5c706aaf9f14)

# 그룹 B: 도전 모델로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3n:e2b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# 출력에서 Run ID를 저장 (예: 034da928-0f74-4205-8654-6492712472b3)
```

### 4단계: 실행 결과를 그룹에 연결

평가 실행을 해당 그룹에 연결합니다:

```bash
# 기준 모델 실행을 그룹 A에 추가
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "baseline" \
  -r <baseline-run-id> \
  --db experiment.db

# 도전 모델 실행을 그룹 B에 추가
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "challenger" \
  -r <challenger-run-id> \
  --db experiment.db
```

### 5단계: 결과 비교

비교 테이블을 확인합니다:

```bash
uv run evalvault experiment-compare --id <experiment-id> --db experiment.db
```

출력:
```
Experiment Comparison

모델 비교
Hypothesis: 큰 모델이 answer_relevancy에서 더 높은 점수를 받을 것

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric           ┃ baseline ┃ challenger ┃ Best Group ┃ Improvement ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ faithfulness     │    1.000 │      1.000 │  baseline  │       +0.0% │
│ answer_relevancy │    0.908 │      0.957 │ challenger │       +5.4% │
└──────────────────┴──────────┴────────────┴────────────┴─────────────┘
```

### 6단계: 실험 결론 기록

결론을 기록합니다:

```bash
uv run evalvault experiment-conclude \
  --id <experiment-id> \
  --conclusion "도전 모델이 answer_relevancy에서 5.4% 개선, 단 2배의 지연 시간 트레이드오프" \
  --db experiment.db
```

### 추가 명령어

```bash
# 실험 요약 보기
uv run evalvault experiment-summary --id <experiment-id> --db experiment.db

# 모든 실험 목록
uv run evalvault experiment-list --db experiment.db
```

### 빠른 참조

| 단계 | 명령어 |
|------|--------|
| 실험 생성 | `experiment-create --name "..." --hypothesis "..."` |
| 그룹 추가 | `experiment-add-group --id <exp> -g "이름" -d "설명"` |
| 평가 실행 | `run dataset.json --model <model> --db experiment.db` |
| 실행 연결 | `experiment-add-run --id <exp> -g "그룹" -r <run>` |
| 결과 비교 | `experiment-compare --id <exp>` |
| 결론 기록 | `experiment-conclude --id <exp> --conclusion "..."` |

---

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
# 테스트 (항상 uv run 사용)
uv run pytest tests/ -v
uv run pytest tests/integration/test_e2e_scenarios.py -v   # 외부 API 필요

# 린트 & 포맷팅
uv run ruff check src/ tests/
uv run ruff format src/ tests/
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
