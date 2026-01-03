# 프로덕션 배포 가이드

> EvalVault를 프로덕션 환경에서 안정적으로 운영하는 방법을 배웁니다.

---

## 목차

1. [환경 변수 관리](#환경-변수-관리)
2. [대규모 평가 처리](#대규모-평가-처리)
3. [모니터링 설정](#모니터링-설정)
4. [보안 고려사항](#보안-고려사항)
5. [Docker 배포](#docker-배포)
6. [CI/CD 통합](#cicd-통합)

---

## 환경 변수 관리

### 환경별 설정 분리

```bash
# 개발 환경: .env.development
EVALVAULT_PROFILE=dev
OLLAMA_BASE_URL=http://localhost:11434
PHOENIX_ENABLED=false

# 스테이징 환경: .env.staging
EVALVAULT_PROFILE=prod
OLLAMA_BASE_URL=http://ollama-staging:11434
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://phoenix-staging:6006/v1/traces

# 프로덕션 환경: .env.production
EVALVAULT_PROFILE=prod
OLLAMA_BASE_URL=http://ollama-prod:11434
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://phoenix-prod:6006/v1/traces
```

### 환경 변수 로드

```bash
# 환경별 .env 파일 로드
cp .env.production .env
uv run evalvault run data.json --metrics faithfulness
```

또는:

```bash
# 환경 변수 직접 지정
EVALVAULT_PROFILE=prod uv run evalvault run data.json --metrics faithfulness
```

### 시크릿 관리

**권장하지 않는 방법**:
```bash
# .env 파일에 직접 API 키 저장 (비권장)
OPENAI_API_KEY=sk-...
```

**권장 방법**:

1. **환경 변수로 주입**:
   ```bash
   export OPENAI_API_KEY=$(vault kv get -field=api_key secret/openai)
   ```

2. **시크릿 관리 서비스 사용**:
   ```python
   # AWS Secrets Manager
   import boto3

   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='evalvault/openai')
   os.environ['OPENAI_API_KEY'] = secret['SecretString']
   ```

3. **Kubernetes Secrets**:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: evalvault-secrets
   type: Opaque
   data:
     OPENAI_API_KEY: <base64-encoded-key>
   ```

### 필수 환경 변수 체크리스트

| 환경 변수 | 필수 | 기본값 | 설명 |
|-----------|------|--------|------|
| `EVALVAULT_PROFILE` | 권장 | - | 모델 프로필 (dev, prod, openai) |
| `OPENAI_API_KEY` | 조건부 | - | OpenAI 사용 시 필수 |
| `OLLAMA_BASE_URL` | 조건부 | localhost:11434 | Ollama 사용 시 |
| `PHOENIX_ENABLED` | 권장 | false | 모니터링 활성화 |
| `PHOENIX_ENDPOINT` | 조건부 | localhost:6006 | Phoenix 사용 시 |
| `PHOENIX_SAMPLE_RATE` | 선택 | 1.0 | Phoenix Trace 샘플링 비율 (0.0~1.0) |
| `PHOENIX_API_TOKEN` | 선택 | *(빈값)* | Phoenix Cloud API 토큰 (선택) |

---

## 대규모 평가 처리

### 병렬 평가

```bash
# 병렬 평가 활성화
uv run evalvault run large_data.json --metrics faithfulness --parallel

# 배치 크기 조정
uv run evalvault run large_data.json --metrics faithfulness --parallel --batch-size 20
```

### 배치 크기 가이드

| 데이터셋 크기 | 권장 배치 크기 | 예상 시간 |
|---------------|----------------|-----------|
| < 100건 | 10 | < 5분 |
| 100-500건 | 20 | 10-30분 |
| 500-1000건 | 50 | 30-60분 |
| > 1000건 | 100 | 1시간+ |

### 메모리 최적화

```python
# 스트리밍 평가 (대용량 데이터셋)
from evalvault.domain.services.evaluator import RagasEvaluator

evaluator = RagasEvaluator(llm_adapter=llm)

# 청크 단위로 처리
for chunk in chunked(test_cases, chunk_size=100):
    results = evaluator.evaluate(chunk, metrics=["faithfulness"])
    save_results(results)
    del results
    gc.collect()
```

### 타임아웃 설정

```bash
# 환경 변수로 타임아웃 설정
OLLAMA_TIMEOUT=300  # 5분
OPENAI_TIMEOUT=120  # 2분
```

### 재시도 로직

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def evaluate_with_retry(dataset, metrics):
    return evaluator.evaluate(dataset, metrics)
```

---

## 모니터링 설정

### Phoenix 모니터링

```bash
# .env.production
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://phoenix:6006/v1/traces
```

#### Phoenix Dataset / Experiment 파이프라인

- 프로덕션 데이터셋을 Phoenix에 업로드하여 Embeddings/Cluster 시각화를 유지합니다.
- Experiment를 생성해 모델/프롬프트 릴리즈마다 비교 가능한 Run을 고정합니다.

```bash
uv run evalvault run data.json \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --phoenix-dataset prod-insurance-qa \
  --phoenix-experiment release-2025w02
```

CI에서 JSON 출력의 `tracker_metadata["phoenix"]`를 파싱해 Experiment URL을 릴리즈 노트나 Slack 알림에 포함시키면 운영자가 Phoenix에서 즉시 임베딩 시각화와 Drift 알림을 확인할 수 있습니다.

### 로깅 설정

```python
# 로깅 레벨 설정
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evalvault.log'),
        logging.StreamHandler()
    ]
)
```

### CLI 상세 로그

```bash
# 상세 로그 출력
uv run evalvault run data.json --metrics faithfulness --verbose
```

### 메트릭 수집

```python
# Prometheus 메트릭
from prometheus_client import Counter, Histogram, start_http_server

evaluations_total = Counter(
    'evalvault_evaluations_total',
    'Total number of evaluations',
    ['dataset', 'metric']
)

evaluation_duration = Histogram(
    'evalvault_evaluation_duration_seconds',
    'Evaluation duration',
    ['metric']
)

# 메트릭 서버 시작
start_http_server(8000)

# 평가 시 메트릭 수집
with evaluation_duration.labels(metric='faithfulness').time():
    results = evaluator.evaluate(dataset, ['faithfulness'])
    evaluations_total.labels(dataset='insurance-qa', metric='faithfulness').inc()
```

### 알림 설정

```python
# Slack 알림
import requests

def send_slack_alert(message: str, webhook_url: str):
    requests.post(webhook_url, json={"text": message})

# 평가 완료 시 알림
if run.pass_rate < 0.8:
    send_slack_alert(
        f"Warning: Pass rate dropped to {run.pass_rate:.1%}",
        os.environ['SLACK_WEBHOOK_URL']
    )
```

---

## 보안 고려사항

### API 키 보호

```python
# API 키 마스킹
def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

# 로그에서 API 키 제거
logging.info(f"Using API key: {mask_api_key(api_key)}")
```

### 데이터 보호

```python
# PII 제거
import re

def remove_pii(text: str) -> str:
    # 전화번호 마스킹
    text = re.sub(r'\d{3}-\d{3,4}-\d{4}', '[PHONE]', text)
    # 이메일 마스킹
    text = re.sub(r'[\w.-]+@[\w.-]+', '[EMAIL]', text)
    # 주민번호 마스킹
    text = re.sub(r'\d{6}-\d{7}', '[SSN]', text)
    return text
```

### 네트워크 보안

```yaml
# docker-compose.yaml
services:
  evalvault:
    networks:
      - internal

  phoenix:
    networks:
      - internal
    ports:
      - "127.0.0.1:6006:6006"  # 로컬만 접근 가능

networks:
  internal:
    driver: bridge
```

### 접근 제어

```python
# API 키 검증
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ['EVALVAULT_API_KEY']:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated
```

---

## Docker 배포

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# uv 설치
RUN pip install uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# 소스 복사
COPY src/ ./src/
COPY config/ ./config/

# 실행
ENTRYPOINT ["uv", "run", "evalvault"]
```

### Docker Compose

```yaml
# docker-compose.yaml
services:
  evalvault:
    build: .
    environment:
      - EVALVAULT_PROFILE=prod
      - OLLAMA_BASE_URL=http://ollama:11434
      - PHOENIX_ENABLED=true
      - PHOENIX_ENDPOINT=http://phoenix:6006/v1/traces
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama
      - phoenix

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"
    volumes:
      - phoenix_data:/data

volumes:
  ollama_data:
  phoenix_data:
```

### 실행

```bash
# 빌드 및 실행
docker compose up -d

# 평가 실행
docker compose run evalvault run /app/data/test.json --metrics faithfulness

# 로그 확인
docker compose logs -f evalvault
```

---

## CI/CD 통합

### GitHub Actions

```yaml
# .github/workflows/evaluation.yaml
name: RAG Evaluation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 매일 자정

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run evaluation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
            --metrics faithfulness,answer_relevancy \
            --output results.json

      - name: Check pass rate
        run: |
          PASS_RATE=$(jq '.pass_rate' results.json)
          if (( $(echo "$PASS_RATE < 0.8" | bc -l) )); then
            echo "Pass rate is below threshold: $PASS_RATE"
            exit 1
          fi

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: results.json
```

### 정기 평가 및 알림

```yaml
# .github/workflows/scheduled-evaluation.yaml
name: Scheduled Evaluation

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시

jobs:
  evaluate-and-report:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # ... 평가 실행 ...

      - name: Send Slack notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Weekly RAG Evaluation Results",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Pass Rate:* ${{ steps.evaluate.outputs.pass_rate }}\n*Faithfulness:* ${{ steps.evaluate.outputs.faithfulness }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### PR 평가 게이트

```yaml
# .github/workflows/pr-evaluation.yaml
name: PR Evaluation Gate

on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/fixtures/**'

jobs:
  evaluate-pr:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # ... 평가 실행 ...

      - name: Compare with baseline
        run: |
          # 기준 결과 다운로드
          gh run download -n baseline-results -D baseline/

          # 비교
          uv run evalvault compare baseline/results.json results.json --output comparison.md

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const comparison = fs.readFileSync('comparison.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comparison
            });
```

---

## 요약 체크리스트

### 배포 전 체크리스트

- [ ] 환경 변수 설정 완료
- [ ] 시크릿 관리 서비스 연동
- [ ] Phoenix 모니터링 설정
- [ ] 로깅 설정
- [ ] 알림 설정 (Slack/Email)
- [ ] Docker 이미지 빌드 테스트
- [ ] CI/CD 파이프라인 테스트

### 운영 체크리스트

- [ ] 일일 평가 결과 모니터링
- [ ] Pass Rate 임계값 알림 설정
- [ ] 토큰 사용량 모니터링
- [ ] 로그 로테이션 설정
- [ ] 백업 정책 수립

---

## 다음 단계

모든 튜토리얼을 완료하셨습니다. 추가 정보가 필요하시면:

- [사용자 가이드](../USER_GUIDE.md) - 상세 기능 설명
- [아키텍처 가이드](../ARCHITECTURE.md) - 시스템 구조 이해
- [로드맵](../ROADMAP.md) - 향후 계획

---

<div align="center">

[이전: 한국어 RAG](05-korean-rag.md) | [처음으로: 빠른 시작](01-quickstart.md)

</div>
