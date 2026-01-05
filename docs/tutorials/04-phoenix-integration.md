# Phoenix 통합 가이드

> Phoenix를 설치하고 EvalVault와 연동하여 RAG 시스템을 관찰합니다.

---

## 목차

1. [Phoenix란?](#phoenix란)
2. [Phoenix 설치](#phoenix-설치)
3. [EvalVault 연동 설정](#evalvault-연동-설정)
4. [대시보드 활용법](#대시보드-활용법)
5. [고급 기능](#고급-기능)

---

## Phoenix란?

[Phoenix](https://docs.arize.com/phoenix)는 Arize AI에서 만든 **오픈소스 LLM 옵저버빌리티 플랫폼**입니다.

### Langfuse 대비 장점

| 기능 | Phoenix | Langfuse |
|------|---------|----------|
| 검색 품질 자동 분석 | Precision@K, NDCG 자동 계산 | 수동 구현 필요 |
| 임베딩 시각화 | UMAP 기반 시각화 내장 | 미지원 |
| OpenTelemetry 표준 | 네이티브 지원 | 미지원 |
| Ragas 통합 | 네이티브 지원 | 지원 |
| 로컬 설치 | Docker로 간편 설치 | Self-hosted 옵션 |

### EvalVault + Phoenix 조합

```
┌─────────────────┐      ┌────────────────┐      ┌─────────────────┐
│   EvalVault     │─────>│    Phoenix     │─────>│   Dashboard     │
│  (Ragas 평가)   │ OTLP │  (트레이스 수집) │      │   (시각화)      │
└─────────────────┘      └────────────────┘      └─────────────────┘
```

---

## Phoenix 설치

### 방법 1: Docker (권장)

```bash
# Phoenix 서버 실행
docker run -d --name phoenix -p 6006:6006 arizephoenix/phoenix:latest

# 실행 확인
docker ps | grep phoenix
```

대시보드 접속: http://localhost:6006

### 방법 2: Docker Compose

```yaml
# docker-compose.phoenix.yaml
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"
    volumes:
      - phoenix_data:/data
    environment:
      - PHOENIX_WORKING_DIR=/data
    restart: unless-stopped

volumes:
  phoenix_data:
```

```bash
docker compose -f docker-compose.phoenix.yaml up -d
```

### 방법 3: Python 패키지

```bash
# Phoenix 설치
pip install arize-phoenix

# 로컬 서버 실행
uv run python -m phoenix.server.main serve
```

### 설치 확인

```bash
# 헬스체크
curl http://localhost:6006/v1/traces
```

정상 응답: `{"status":"ok"}` 또는 빈 응답

---

## EvalVault 연동 설정

### Step 1: 의존성 설치

```bash
# OpenTelemetry 의존성 설치
uv sync --extra dev
```

또는 직접 설치:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

### Step 2: 환경 변수 설정

`.env` 파일에 추가:

```bash
# Phoenix 설정
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
```

### Step 3: 평가 실행

```bash
# --tracker phoenix로 Phoenix 추적 활성화 (--phoenix-max-traces로 per-case 제한 조정)
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness --tracker phoenix --phoenix-max-traces 200
```

또는 환경 변수로 기본 활성화:

```bash
export PHOENIX_ENABLED=true
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness
```

### Step 4: Dataset/Experiment 동기화

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-dataset-description "보험 QA v2025.01" \
  --phoenix-experiment gemma3-ko-baseline \
  --phoenix-experiment-description "Gemma3 vs OpenAI 비교"
```

- `--phoenix-dataset`: EvalVault 데이터셋(문제/답변/컨텍스트/threshold/메타데이터)을 Phoenix Dataset으로 업로드합니다. 설명을 생략하면 `"{name} v{version}"` 또는 `metadata.description`이 자동 적용됩니다.
- `--phoenix-experiment`: 업로드된 Dataset과 연결된 Experiment를 생성하고 EvalVault 점수, Pass Rate, Domain Memory 상태를 Phoenix 메타데이터로 포함합니다.
- 두 결과 모두 `result.tracker_metadata["phoenix"]`에 dataset/experiment URL을 저장하므로 CLI JSON 출력이나 후속 자동화에서 Phoenix 화면으로 바로 이동할 수 있습니다.

### 연동 확인

1. Phoenix 대시보드 접속: http://localhost:6006
2. Traces 탭에서 `evalvault` 서비스 확인
3. 평가 트레이스 클릭하여 상세 정보 확인

---

## 대시보드 활용법

### 1. Traces 탭

모든 평가 실행의 트레이스를 확인합니다.

```
evaluation-run-abc123
├── test-case-tc-001
│   ├── input.question: "보장금액은?"
│   ├── input.answer: "1억원입니다."
│   ├── metric.faithfulness.score: 0.95
│   └── metric.faithfulness.passed: true
├── test-case-tc-002
│   └── ...
└── test-case-tc-003
```

**필터링 옵션**:

| 필터 | 설명 |
|------|------|
| `service.name = evalvault` | EvalVault 트레이스만 표시 |
| `metadata.dataset_name = insurance-qa` | 특정 데이터셋 필터링 |
| `score.avg_faithfulness > 0.8` | 점수 기준 필터링 |

### 2. 메트릭 분석

각 평가 실행의 메트릭 점수를 분석합니다.

**확인 가능한 정보**:

- 메트릭별 평균 점수
- 통과율 (Pass Rate)
- 개별 테스트 케이스 점수
- 실패한 테스트 케이스 상세

### 3. 토큰 사용량 분석

LLM 호출별 토큰 사용량을 추적합니다.

```
evaluation-run-abc123
├── total_tokens: 15,000
├── duration_seconds: 45.2
└── total_cost_usd: 0.015
```

### 4. 레이턴시 분석

각 단계의 처리 시간을 분석합니다.

```
evaluation-run-abc123 (45.2s)
├── test-case-tc-001 (2.1s)
│   ├── faithfulness evaluation (1.8s)
│   └── answer_relevancy evaluation (0.3s)
└── ...
```

### 5. Embeddings 분석

Phoenix 12.27.0의 Embeddings 뷰(UMAP + HDBSCAN)는 Dataset/Experiment를 업로드한 즉시 활성화됩니다.

- **Drift/Query Distance 시계열**: 기본(Primary) vs 참조(Reference) 임베딩 사이의 유클리드 거리를 시간 축으로 살펴보고 이상 구간을 클릭해 원인 분석을 시작합니다.
- **드리프트 순 클러스터 리스트**: HDBSCAN으로 자동 생성된 클러스터를 드리프트가 큰 순서대로 정렬해 저성과/이상치 영역을 빠르게 찾을 수 있습니다.
- **3D 포인트 클라우드 컬러링**: 정확도, 태그, 세그먼트, Domain Memory 표시 여부 등을 색상으로 지정해 문제 영역을 시각적으로 파악합니다.

Dataset/Experiment 링크는 CLI 출력(`tracker_metadata["phoenix"]`)에 함께 제공되므로 클릭 한 번으로 Embeddings 탭을 열 수 있습니다.

---

## 고급 기능

### RAG 트레이스 수집

검색(Retrieval) + 생성(Generation) 단계를 분리하여 추적합니다.

```python
from evalvault.adapters.outbound.tracker import PhoenixAdapter
from evalvault.domain.entities import RAGTraceData, RetrievalData, GenerationData

# Phoenix 어댑터 초기화
adapter = PhoenixAdapter(endpoint="http://localhost:6006/v1/traces")

# RAG 트레이스 데이터 생성
rag_trace = RAGTraceData(
    query="보험 보장금액은 얼마인가요?",
    retrieval=RetrievalData(
        query="보험 보장금액",
        retrieval_method="hybrid",
        top_k=5,
        candidates=[
            {"rank": 1, "score": 0.95, "content": "사망 보장금액은 1억원..."},
            {"rank": 2, "score": 0.87, "content": "보험료 납입기간..."},
        ],
    ),
    generation=GenerationData(
        model="gpt-5-nano",
        prompt="다음 컨텍스트를 바탕으로 질문에 답하세요...",
        response="보장금액은 1억원입니다.",
        input_tokens=150,
        output_tokens=20,
    ),
    total_time_ms=1500,
)

# 트레이스 기록
trace_id = adapter.log_rag_trace(rag_trace)
print(f"Trace ID: {trace_id}")
```

### 검색 품질 메트릭

Phoenix에서 자동으로 계산되는 검색 품질 메트릭:

| 메트릭 | 설명 |
|--------|------|
| Precision@K | 상위 K개 중 관련 문서 비율 |
| Recall@K | 전체 관련 문서 중 상위 K개에 포함된 비율 |
| NDCG | 순위 기반 관련성 점수 |
| MRR | 첫 번째 관련 문서의 역순위 |

### 임베딩 시각화

Phoenix의 Embeddings Analysis(UMAP + HDBSCAN) 기능을 활용합니다.

1. 대시보드에서 **Embeddings** 탭 클릭
2. 질문/답변/컨텍스트 임베딩을 선택하고 Primary/Reference 그룹을 지정
3. **Drift** 시계열로 유클리드 거리 변화를 추적하고, 자동 정렬된 클러스터 리스트에서 이상치 구간을 찾습니다.
4. 포인트 클라우드를 정확도·태그·세그먼트 등으로 컬러링해 실패 패턴을 시각적으로 확인합니다.

### Prompt Playground Loop

Phoenix Prompt Playground에서 튜닝한 프롬프트를 EvalVault 실행에 연결하려면 manifest와 전용 CLI를 사용합니다.

1. Prompt ↔ Phoenix ID 매핑

```bash
uv run evalvault phoenix prompt-link agent/prompts/baseline.txt \
  --prompt-id pr-428 \
  --experiment-id exp-20250115 \
  --notes "Gemma3 baseline"
```

2. 릴리즈 전 diff 확인

```bash
uv run evalvault phoenix prompt-diff \
  agent/prompts/baseline.txt agent/prompts/system.txt \
  --manifest agent/prompts/prompt_manifest.json \
  --format table  # json으로 기계 처리 가능
```

3. 평가 실행에 Prompt 상태 주입

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness \
  --tracker phoenix \
  --prompt-files agent/prompts/baseline.txt,agent/prompts/system.txt \
  --prompt-manifest agent/prompts/prompt_manifest.json
```

이렇게 실행하면 `result.tracker_metadata["phoenix"]["prompts"]`에 파일별 status/checksum/diff가 저장되어 Release Notes, History CLI, Web UI에서 Prompt 변화와 Phoenix Trace/Dataset/Experiment 링크를 함께 확인할 수 있습니다.

### 커스텀 속성 추가

평가에 커스텀 메타데이터를 추가합니다.

```python
from evalvault.adapters.outbound.tracker import PhoenixAdapter

adapter = PhoenixAdapter()

# 트레이스 시작 시 메타데이터 추가
trace_id = adapter.start_trace(
    name="custom-evaluation",
    metadata={
        "experiment_name": "v2-retriever-test",
        "model_version": "1.2.0",
        "environment": "staging",
    }
)

# 점수 기록
adapter.log_score(trace_id, "custom_metric", 0.85, comment="Custom evaluation")

# 트레이스 종료
adapter.end_trace(trace_id)
```

### 알림 설정

Phoenix Cloud 또는 Slack 웹훅을 통한 알림 설정:

```python
# 평가 점수가 임계값 미만일 때 알림
if run.pass_rate < 0.8:
    # Slack 웹훅 호출
    send_slack_alert(f"Pass rate dropped to {run.pass_rate:.1%}")
```

---

## 문제 해결

### Phoenix 연결 실패

```
Error: Failed to initialize Phoenix tracer
```

**해결**:

1. Phoenix 서버 실행 확인:
   ```bash
   docker ps | grep phoenix
   curl http://localhost:6006/v1/traces
   ```

2. 엔드포인트 확인:
   ```bash
   echo $PHOENIX_ENDPOINT
   # 기본값: http://localhost:6006/v1/traces
   ```

3. 네트워크 확인:
   ```bash
   telnet localhost 6006
   ```

### 트레이스가 나타나지 않음

**원인**: 배치 처리로 인한 지연

**해결**: 평가 완료 후 몇 초 대기 후 대시보드 새로고침

### 메모리 부족

대규모 평가 시 Phoenix 메모리 부족:

```yaml
# docker-compose.phoenix.yaml
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    deploy:
      resources:
        limits:
          memory: 4G
```

---

## 환경 변수 요약

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PHOENIX_ENABLED` | `false` | Phoenix 추적 활성화 |
| `PHOENIX_ENDPOINT` | `http://localhost:6006/v1/traces` | Phoenix OTLP 엔드포인트 |
| `PHOENIX_SAMPLE_RATE` | `1.0` | Phoenix Trace 샘플링 비율 (0.0~1.0) |
| `PHOENIX_API_TOKEN` | *(빈값)* | Phoenix Cloud API 토큰 (선택) |

---

## 다음 단계

| 주제 | 튜토리얼 |
|------|----------|
| 한국어 RAG 최적화 | [05-korean-rag.md](05-korean-rag.md) |
| 프로덕션 배포 가이드 | [06-production-tips.md](06-production-tips.md) |

---

<div align="center">

[이전: 커스텀 메트릭](03-custom-metrics.md) | [다음: 한국어 RAG](05-korean-rag.md)

</div>
