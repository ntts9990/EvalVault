# 배포 체크리스트 & 릴리즈 노트 템플릿

EvalVault 배포 전에 필수로 확인해야 할 항목과 릴리즈 노트 초안을 빠르게 만드는
템플릿을 정리했습니다. 팀 내 공유/운영 시 그대로 복사해 사용할 수 있도록
상위 단계부터 하위 단계까지 순서대로 구성했습니다.

---

## 0. 범위/전제

- **배포 대상**: EvalVault API + Web UI + 평가 파이프라인
- **기본 DB**: PostgreSQL + pgvector (SQLite는 `--db` 또는 `DB_BACKEND=sqlite`로 선택)
- **LLM 제공자**: UI에서 provider 선택 (Ollama/OpenAI/vLLM/기타)

---

## 1. 사전 점검 (릴리즈 계획 수립)

- 이번 배포 범위(기능/버그/문서)를 5줄 이내로 요약한다.
- 릴리즈 타입(기능/수정/문서)을 Conventional Commit 규칙에 맞게 분류한다.
- 외부 의존성(LLM 서버, DB, 옵저버빌리티) 변경 여부를 명확히 한다.

---

## 2. 환경/설정 체크 (공통 → 제공자별)

### 공통

- `.env`가 최신인가?
- `EVALVAULT_PROFILE`이 올바른가? (`config/models.yaml` 기준)
- Postgres 연결 설정(`POSTGRES_*` 또는 `POSTGRES_CONNECTION_STRING`)이 올바른가?
- SQLite를 쓰는 경우 `EVALVAULT_DB_PATH`가 운영 환경 경로와 일치하는가?

### Ollama

- `ollama list`에 필요한 모델이 모두 있는가?
- Tool/function calling이 필요한 메트릭(`factual_correctness`) 사용 시
  `OLLAMA_TOOL_MODELS`에 해당 모델이 포함되어 있는가?
- 임베딩 메트릭(`answer_relevancy`, `semantic_similarity`) 사용 시
  `ollama pull qwen3-embedding:0.6b`가 되어 있는가?

### OpenAI

- `OPENAI_API_KEY`가 유효한가?
- Web UI에서 OpenAI 모델 목록(`gpt-5-mini`, `gpt-5.1`, `gpt-5.2`, `gpt-5-nano`)이 노출되는지 확인

### vLLM (OpenAI-compatible)

- `VLLM_BASE_URL`, `VLLM_MODEL`이 설정되어 있는가?
  - 예: `VLLM_MODEL=gpt-oss-120b`
- 임베딩이 필요한 경우 `VLLM_EMBEDDING_MODEL` 및 `/v1/embeddings`가
  정상 동작하는가?

---

## 3. 데이터/DB 체크

- SQLite를 쓰는 경우 파일 백업을 준비했는가? (`cp data/db/evalvault.db data/db/evalvault.db.bak`)
- Postgres 사용 시 스키마가 최신인지 확인했는가?
- `pipeline_results`에 `profile/tags/metadata` 컬럼이 존재하는가?
  - 기존 DB는 어댑터 초기화 시 자동 마이그레이션됨.

---

## 4. 기능별 검증 항목

### API/CLI

- `uv run evalvault config`로 설정 확인
- `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`

### Web UI

- Provider 전환 시 모델 목록이 정상인지 확인
  - Ollama: `ollama list` 기반으로 표시됨
  - OpenAI: `gpt-5-mini`, `gpt-5.1`, `gpt-5.2`, `gpt-5-nano`
- Tool 필요 메트릭 선택 시 경고 배너가 뜨는지 확인
- 분석 결과 저장 시 `profile/tags/metadata` 입력이 정상 동작하는지 확인
- 분석 히스토리 필터/비교 화면이 정상 동작하는지 확인

---

## 5. 품질 게이트 (테스트/린트)

- `uv run ruff check src/ tests/`
- `uv run ruff format src/ tests/`
- `uv run pytest tests -v`
- 메트릭/스코어링 변경 시:
  - `uv run pytest --cov=src --cov-report=term`

---

## 6. 릴리즈 노트 템플릿 (복사용)

```markdown
# Release <버전> / <날짜>

## 변경 요약
- 요약 1
- 요약 2

## 신규 기능
- ...

## 개선/수정
- ...

## 설정/환경 변경
- ...

## 데이터/마이그레이션
- ...

## 알려진 이슈
- ...

## 테스트/검증
- ruff check/format
- pytest -v
- 기타 수동 검증 항목

## 롤백/리스크
- 롤백 경로
- 잠재 리스크 및 대응책
```

---

## 7. 배포 후 체크

- API/웹 기본 화면 정상 로드 확인
- `runs`, `analysis history` 조회가 정상인지 확인
- 옵저버빌리티(Phoenix/Langfuse) 트레이스 기록 확인
- 사용자/내부 피드백 수집 및 이슈 기록
