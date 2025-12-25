# EvalVault 사용자 가이드

> RAG 시스템 품질 평가를 위한 올인원 솔루션

---

## 목차

1. [EvalVault란?](#evalvault란)
2. [5분 만에 시작하기](#5분-만에-시작하기)
3. [설치 가이드](#설치-가이드)
4. [환경 설정](#환경-설정)
5. [모델 프로필 설정](#모델-프로필-설정)
6. [CLI 사용법](#cli-사용법)
7. [평가 메트릭 이해하기](#평가-메트릭-이해하기)
8. [데이터셋 준비](#데이터셋-준비)
9. [결과 저장 및 추적](#결과-저장-및-추적)
10. [고급 기능](#고급-기능)
11. [문제 해결](#문제-해결)

---

## EvalVault란?

EvalVault는 **RAG(Retrieval-Augmented Generation) 시스템의 품질을 객관적으로 측정**하는 평가 도구입니다.

### 왜 EvalVault인가?

| 문제 | EvalVault 솔루션 |
|------|------------------|
| "우리 RAG가 잘 작동하는지 어떻게 알지?" | 6가지 표준화된 메트릭으로 객관적 측정 |
| "평가 결과를 어디에 저장하지?" | SQLite + Langfuse 자동 저장 |
| "한국어 데이터도 평가 가능?" | 한국어/영어/일본어/중국어 지원 |
| "팀원들과 결과를 공유하고 싶어" | Langfuse 대시보드로 시각화 |

### 핵심 기능

```
📊 6가지 평가 메트릭 (Ragas 기반)
📁 다양한 데이터 포맷 지원 (JSON, CSV, Excel)
💾 자동 결과 저장 (SQLite, PostgreSQL)
📈 실시간 추적 (Langfuse, MLflow)
🔌 확장 가능한 아키텍처 (Hexagonal Architecture)
```

---

## 5분 만에 시작하기

### 전제 조건

- Python 3.12+
- OpenAI API 키

### Step 1: 설치

```bash
# 저장소 클론
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# 의존성 설치 (uv 권장)
uv pip install -e ".[dev]"

# 또는 pip 사용
pip install -e ".[dev]"
```

### Step 2: 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수: OpenAI API 키 설정
echo "OPENAI_API_KEY=sk-your-api-key" >> .env
```

### Step 3: 첫 평가 실행

```bash
# 샘플 데이터셋으로 평가 실행
evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness
```

### Step 4: 결과 확인

```bash
# 평가 히스토리 조회
evalvault history

# 상세 결과 확인
evalvault export <run_id> -o result.json
```

**축하합니다! 첫 RAG 평가를 완료했습니다.**

---

## 설치 가이드

### 방법 1: uv 사용 (권장)

[uv](https://github.com/astral-sh/uv)는 빠른 Python 패키지 관리자입니다.

```bash
# uv 설치 (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 설치
cd EvalVault
uv pip install -e ".[dev]"
```

### 방법 2: pip 사용

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 설치
pip install -e ".[dev]"
```

### 방법 3: Docker (준비 중)

```bash
# 추후 지원 예정
docker run -it evalvault/evalvault:latest
```

### 설치 확인

```bash
# CLI 버전 확인
evalvault --help

# 사용 가능한 메트릭 확인
evalvault metrics
```

---

## 환경 설정

### 필수 설정

`.env` 파일에 다음을 설정합니다:

```bash
# OpenAI API (필수)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-5-nano           # 기본 모델
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 선택적 설정

```bash
# Langfuse 연동 (평가 결과 추적)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # 또는 self-hosted URL
```

> **Note**: 메트릭 임계값(thresholds)은 환경변수가 아닌 **데이터셋 JSON 파일**에 정의합니다. [데이터셋 준비](#데이터셋-준비) 섹션을 참조하세요.

### 설정 확인

```bash
# 현재 설정 상태 확인
evalvault config
```

출력 예시:
```
EvalVault Configuration
========================
OpenAI Model: gpt-5-nano
Embedding Model: text-embedding-3-small
Langfuse: Configured ✓
```

---

## 모델 프로필 설정

EvalVault는 **프로필 기반 모델 설정**을 지원합니다. 개발/운영 환경별로 다른 모델을 사용하거나, 폐쇄망에서 로컬 Ollama 모델을 사용할 수 있습니다.

### 설정 파일 역할 분리

| 파일 | 역할 | Git 관리 |
|------|------|----------|
| `config/models.yaml` | 모델 프로필 정의 (모델명, provider) | ✅ Yes |
| `.env` | 시크릿/인프라 설정 (API 키, 서버 URL) | ❌ No |

### 사용 가능한 프로필

| 프로필 | LLM | Embedding | 용도 |
|--------|-----|-----------|------|
| `dev` | gemma3:1b (Ollama) | qwen3-embedding:0.6b | 개발/테스트 |
| `prod` | gpt-oss:20b (Ollama) | qwen3-embedding:8b | 운영 환경 |
| `openai` | gpt-5-nano (OpenAI) | text-embedding-3-small | 외부망 |

### 프로필 사용 방법

#### 방법 1: .env 파일에서 설정

```bash
# .env
EVALVAULT_PROFILE=dev
```

```bash
# 프로필 자동 적용
evalvault run data.json --metrics faithfulness
```

#### 방법 2: CLI 옵션으로 오버라이드

```bash
# --profile 옵션으로 프로필 선택
evalvault run data.json --profile prod --metrics faithfulness

# 단축 옵션
evalvault run data.json -p openai --metrics faithfulness
```

### 폐쇄망(Air-gapped) 환경 설정

외부 인터넷 접근이 불가능한 환경에서는 Ollama를 사용합니다.

```bash
# .env 설정
EVALVAULT_PROFILE=dev              # 또는 prod
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120
```

```bash
# Ollama 모델 설치 (사전 준비)
ollama pull gemma3:1b
ollama pull qwen3-embedding:0.6b
```

### 프로필 설정 파일 (config/models.yaml)

```yaml
profiles:
  dev:
    description: "개발/테스트용 경량 모델"
    llm:
      provider: ollama
      model: gemma3:1b
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b

  prod:
    description: "운영용 고성능 모델"
    llm:
      provider: ollama
      model: gpt-oss:20b
      options:
        think_level: medium
    embedding:
      provider: ollama
      model: qwen3-embedding:8b

  openai:
    description: "OpenAI API 사용 (외부망)"
    llm:
      provider: openai
      model: gpt-5-nano
    embedding:
      provider: openai
      model: text-embedding-3-small
```

---

## CLI 사용법

### 기본 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `run` | 평가 실행 | `evalvault run data.json --metrics faithfulness` |
| `metrics` | 사용 가능한 메트릭 목록 | `evalvault metrics` |
| `config` | 현재 설정 확인 | `evalvault config` |
| `history` | 평가 히스토리 조회 | `evalvault history --limit 10` |
| `compare` | 두 평가 결과 비교 | `evalvault compare <id1> <id2>` |
| `export` | 결과 내보내기 | `evalvault export <id> -o result.json` |

### 평가 실행 (`run`)

```bash
# 기본 사용
evalvault run <dataset_path> --metrics <metric1,metric2,...>

# 예시: 단일 메트릭
evalvault run data.json --metrics faithfulness

# 예시: 여러 메트릭
evalvault run data.json --metrics faithfulness,answer_relevancy,context_precision

# 예시: 모든 메트릭
evalvault run data.json --metrics faithfulness,answer_relevancy,context_precision,context_recall,factual_correctness,semantic_similarity

# 예시: 프로필 지정 (Ollama dev 환경)
evalvault run data.json --profile dev --metrics faithfulness

# 예시: 프로필 지정 (OpenAI)
evalvault run data.json -p openai --metrics faithfulness

# 예시: Langfuse 연동
evalvault run data.json --metrics faithfulness --langfuse
```

### 히스토리 조회 (`history`)

```bash
# 최근 10개 결과
evalvault history --limit 10

# 특정 데이터셋 필터링
evalvault history --dataset insurance-qa

# 특정 모델 필터링
evalvault history --model gpt-5-nano
```

### 결과 비교 (`compare`)

```bash
# 두 평가 결과 비교
evalvault compare abc123 def456
```

출력 예시:
```
Comparison: abc123 vs def456
============================
                    Run 1      Run 2      Diff
faithfulness        0.85       0.92       +0.07
answer_relevancy    0.78       0.81       +0.03
context_precision   0.90       0.88       -0.02
```

---

## 평가 메트릭 이해하기

EvalVault는 [Ragas](https://docs.ragas.io/) 프레임워크 기반의 6가지 메트릭을 제공합니다.

### 메트릭 한눈에 보기

| 메트릭 | 측정 대상 | Ground Truth 필요 | 임베딩 필요 |
|--------|-----------|-------------------|-------------|
| Faithfulness | 답변이 컨텍스트에 충실한지 | ❌ | ❌ |
| Answer Relevancy | 답변이 질문과 관련있는지 | ❌ | ✅ |
| Context Precision | 검색된 컨텍스트의 정밀도 | ✅ | ❌ |
| Context Recall | 필요한 정보가 검색되었는지 | ✅ | ❌ |
| Factual Correctness | 답변이 정답과 일치하는지 | ✅ | ❌ |
| Semantic Similarity | 답변과 정답의 의미적 유사도 | ✅ | ✅ |

### 상세 설명

#### 1. Faithfulness (충실도)

**"답변이 검색된 컨텍스트에서 벗어나지 않았는가?"**

```
점수 1.0: 답변의 모든 주장이 컨텍스트에서 지원됨
점수 0.0: 답변이 컨텍스트에 없는 내용을 포함 (환각)
```

사용 사례:
- 환각(Hallucination) 감지
- RAG 시스템의 신뢰성 평가

#### 2. Answer Relevancy (답변 관련성)

**"답변이 질문에 적절히 대응하는가?"**

```
점수 1.0: 답변이 질문과 완벽하게 관련됨
점수 0.0: 답변이 질문과 무관함
```

사용 사례:
- 답변 품질 평가
- 주제 이탈 감지

#### 3. Context Precision (컨텍스트 정밀도)

**"검색된 컨텍스트 중 실제로 유용한 것의 비율은?"**

```
점수 1.0: 모든 검색 결과가 유용함
점수 0.0: 검색 결과가 모두 노이즈
```

사용 사례:
- Retriever 품질 평가
- 검색 정밀도 개선

#### 4. Context Recall (컨텍스트 재현율)

**"정답을 도출하는데 필요한 정보가 모두 검색되었는가?"**

```
점수 1.0: 필요한 모든 정보가 검색됨
점수 0.0: 필요한 정보가 누락됨
```

사용 사례:
- Retriever 커버리지 평가
- 검색 누락 감지

#### 5. Factual Correctness (사실적 정확성)

**"답변의 사실적 주장이 정답과 일치하는가?"**

```
점수 1.0: 모든 사실이 정확함
점수 0.0: 사실적 오류 포함
```

사용 사례:
- 사실 검증
- 오답 감지

#### 6. Semantic Similarity (의미적 유사도)

**"답변과 정답이 의미적으로 얼마나 유사한가?"**

```
점수 1.0: 의미가 동일함
점수 0.0: 의미가 완전히 다름
```

사용 사례:
- 답변 품질 종합 평가
- 다양한 표현 허용

### 메트릭 선택 가이드

```
🎯 빠른 평가가 필요할 때:
   → faithfulness (환각 감지)

🎯 Retriever 성능 평가:
   → context_precision + context_recall

🎯 답변 품질 종합 평가:
   → answer_relevancy + semantic_similarity

🎯 정확도 중심 평가:
   → factual_correctness

🎯 전체 파이프라인 평가:
   → 모든 메트릭 사용
```

---

## 데이터셋 준비

### 지원 형식

| 형식 | 확장자 | 특징 |
|------|--------|------|
| JSON | `.json` | 구조화된 데이터, 메타데이터 포함 가능 |
| CSV | `.csv` | 스프레드시트 호환, 간단한 편집 |
| Excel | `.xlsx` | 엑셀에서 직접 편집 가능 |

### JSON 형식 (권장)

```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7,
    "context_precision": 0.7,
    "context_recall": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "이 보험의 보장금액은 얼마인가요?",
      "answer": "보장금액은 1억원입니다.",
      "contexts": [
        "해당 보험의 사망 보장금액은 1억원입니다.",
        "보험료 납입기간은 20년입니다."
      ],
      "ground_truth": "1억원"
    }
  ]
}
```

> **thresholds**: 메트릭별 통과 기준 (0.0~1.0). 미지정 시 기본값 0.7 적용.
> 데이터셋에 포함하여 버전 관리가 가능하고, 팀 간 일관된 SLA 적용이 가능합니다.

### CSV 형식

```csv
id,question,answer,contexts,ground_truth
tc-001,"보장금액은?","1억원입니다.","[""사망 보장금액은 1억원""]","1억원"
```

> **주의**: CSV에서 contexts는 JSON 배열 문자열로 작성합니다.

### Excel 형식

| id | question | answer | contexts | ground_truth |
|----|----------|--------|----------|--------------|
| tc-001 | 보장금액은? | 1억원입니다. | ["사망 보장금액은 1억원"] | 1억원 |

### 필드 설명

| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✅ | 테스트케이스 고유 ID |
| `question` | ✅ | 사용자 질문 |
| `answer` | ✅ | RAG 시스템의 답변 |
| `contexts` | ✅ | 검색된 컨텍스트 (배열) |
| `ground_truth` | ⚠️ | 정답 (일부 메트릭에 필요) |

> ⚠️ `ground_truth`는 context_precision, context_recall, factual_correctness, semantic_similarity 메트릭에 필요합니다.

### 샘플 데이터셋

프로젝트에 포함된 샘플 데이터셋:

```
tests/fixtures/e2e/
├── insurance_qa_korean.json    # 한국어 보험 QA (5개 케이스)
├── insurance_qa_english.json   # 영어 보험 QA (5개 케이스)
└── edge_cases.json             # 엣지 케이스 테스트
```

---

## 결과 저장 및 추적

### 자동 저장 (SQLite)

평가 결과는 자동으로 로컬 SQLite 데이터베이스에 저장됩니다.

```bash
# 기본 저장 위치
data/evaluations.db

# 저장된 결과 조회
evalvault history
```

### Langfuse 연동

[Langfuse](https://langfuse.com/)는 LLM 애플리케이션 추적 플랫폼입니다.

#### 설정 방법

```bash
# .env 파일에 추가
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # 또는 self-hosted
```

#### 사용 방법

```bash
# --langfuse 플래그 추가
evalvault run data.json --metrics faithfulness --langfuse
```

#### Langfuse 대시보드에서 확인 가능한 정보

- 평가 실행별 Trace
- 메트릭 점수 시계열
- 테스트케이스별 상세 결과
- 토큰 사용량 및 비용

### 결과 내보내기

```bash
# JSON으로 내보내기
evalvault export <run_id> -o results.json

# 출력 예시
{
  "run_id": "abc123...",
  "dataset_name": "insurance-qa",
  "pass_rate": 0.8,
  "metrics": {
    "faithfulness": 0.9,
    "answer_relevancy": 0.85
  },
  "results": [...]
}
```

---

## 고급 기능

### 테스트셋 자동 생성

문서에서 자동으로 테스트셋을 생성합니다.

```bash
evalvault generate documents/ -n 10 -o testset.json
```

### 다중 LLM 지원

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

# Anthropic Claude
ANTHROPIC_API_KEY=...
```

### 커스텀 메트릭

보험 도메인 특화 메트릭 예시:

```python
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy

# 보험 용어 정확도 평가
metric = InsuranceTermAccuracy(terms_dictionary="terms.json")
```

---

## 문제 해결

### 자주 발생하는 문제

#### 1. OpenAI API 키 오류

```
Error: OPENAI_API_KEY not set
```

**해결**: `.env` 파일에 API 키가 올바르게 설정되었는지 확인

```bash
cat .env | grep OPENAI_API_KEY
```

#### 2. 메트릭 점수가 모두 0

**원인**: `ground_truth` 필드 누락

**해결**: 데이터셋에 `ground_truth` 필드 추가

#### 3. 평가 시간이 너무 오래 걸림

**해결 방법**:
1. 메트릭 수 줄이기: `--metrics faithfulness`
2. 테스트케이스 수 줄이기
3. 더 빠른 모델 사용: `OPENAI_MODEL=gpt-3.5-turbo`

#### 4. Langfuse 연결 실패

```
Error: Failed to connect to Langfuse
```

**해결**:
1. 자격 증명 확인: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
2. 호스트 URL 확인: `LANGFUSE_HOST`
3. 네트워크 연결 확인

### 로그 확인

```bash
# 상세 로그 출력
evalvault run data.json --metrics faithfulness --verbose
```

### 지원 요청

- GitHub Issues: https://github.com/ntts9990/EvalVault/issues
- 버그 리포트 시 포함할 정보:
  - Python 버전: `python --version`
  - EvalVault 버전: `evalvault --version`
  - 에러 메시지 전체
  - 재현 단계

---

## 부록

### A. 환경 변수 전체 목록

#### 프로필 설정

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `EVALVAULT_PROFILE` | ❌ | - | 모델 프로필 (dev, prod, openai) |
| `LLM_PROVIDER` | ❌ | openai | LLM 제공자 (openai, ollama) |

#### OpenAI 설정 (외부망)

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `OPENAI_API_KEY` | ⚠️ | - | OpenAI API 키 (openai 사용 시 필수) |
| `OPENAI_MODEL` | ❌ | gpt-5-nano | 평가에 사용할 모델 |
| `OPENAI_EMBEDDING_MODEL` | ❌ | text-embedding-3-small | 임베딩 모델 |
| `OPENAI_BASE_URL` | ❌ | - | 커스텀 API 엔드포인트 |

#### Ollama 설정 (폐쇄망)

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `OLLAMA_BASE_URL` | ❌ | http://localhost:11434 | Ollama 서버 URL |
| `OLLAMA_MODEL` | ❌ | gemma3:1b | Ollama LLM 모델 |
| `OLLAMA_EMBEDDING_MODEL` | ❌ | qwen3-embedding:0.6b | Ollama 임베딩 모델 |
| `OLLAMA_TIMEOUT` | ❌ | 120 | 요청 타임아웃 (초) |

#### 추적/모니터링 설정

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `LANGFUSE_PUBLIC_KEY` | ❌ | - | Langfuse 공개 키 |
| `LANGFUSE_SECRET_KEY` | ❌ | - | Langfuse 비밀 키 |
| `LANGFUSE_HOST` | ❌ | cloud.langfuse.com | Langfuse 호스트 |

> **Note**: 메트릭 임계값은 데이터셋 JSON의 `thresholds` 필드에 정의합니다.
> 모델 프로필은 `config/models.yaml`에서 관리하며 Git으로 버전 관리됩니다.

### B. 프로젝트 구조

```
EvalVault/
├── config/
│   └── models.yaml       # 모델 프로필 설정 (Git 관리)
├── src/evalvault/
│   ├── domain/           # 비즈니스 로직
│   │   ├── entities/     # 도메인 엔티티
│   │   ├── services/     # 평가 서비스
│   │   └── metrics/      # 커스텀 메트릭
│   ├── ports/            # 인터페이스 정의
│   ├── adapters/         # 구현체
│   │   ├── inbound/      # CLI
│   │   └── outbound/     # 외부 서비스 연동 (OpenAI, Ollama, ...)
│   └── config/           # Settings, ModelConfig
├── tests/                # 테스트
├── docs/                 # 문서
├── .env                  # 시크릿/인프라 설정 (gitignore)
└── data/                 # 데이터 (gitignore)
```

### C. 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| 0.4.0 | 2025-12-25 | Ollama 지원 (폐쇄망), 프로필 기반 모델 설정, --profile CLI 옵션 |
| 0.3.0 | 2025-12-24 | Phase 6 완료, 6개 메트릭 지원, Ragas v1.0 호환 |
| 0.2.0 | 2024-12-24 | SQLite 저장, CLI 히스토리 기능 |
| 0.1.0 | 2024-12-24 | 초기 릴리스, 4개 기본 메트릭 |

---

<div align="center">

**EvalVault** - RAG 평가의 새로운 기준

[GitHub](https://github.com/ntts9990/EvalVault) · [Issues](https://github.com/ntts9990/EvalVault/issues) · [Langfuse](https://langfuse.com/)

</div>
