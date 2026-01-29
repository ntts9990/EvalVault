# 01. Architecture (구조와 경계)

이 장은 EvalVault 코드베이스를 "안전하게 바꾸는 법"을 아키텍처 경계 관점에서 설명한다.
핵심은 "기능을 어디에 넣어야 장기적으로 유지보수/실험/운영이 쉬운가"다.

이 문서는 "외부 문서 없이도" 결정을 내릴 수 있게 작성한다.
단, 사실 주장은 코드/구성 파일의 근거 경로를 함께 제시한다.

## TL;DR

- EvalVault는 Ports & Adapters(헥사고날) 스타일로 경계를 잡는다: `src/evalvault/domain`, `src/evalvault/ports`, `src/evalvault/adapters`.
- 도메인의 바깥(LLM/DB/HTTP/트레이싱)은 "포트(계약)" 뒤로 숨기고, 구현은 어댑터에 둔다.
- 런타임에서 실제 구현을 주입하는 "조립 지점(composition root)"이 있다.
  - Web UI/FastAPI 쪽: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter` + `src/evalvault/adapters/inbound/api/main.py#lifespan`.
- CLI 쪽: `src/evalvault/adapters/inbound/cli/commands/` 아래에서 설정/어댑터를 만들고 도메인 서비스를 호출한다(예: `src/evalvault/adapters/inbound/cli/commands/run.py`).
- 새 기능 추가의 기본 순서(대부분의 경우): (1) 도메인 엔티티/서비스 (2) 포트 정의/수정 (3) 어댑터 구현 (4) 설정/조립 지점 연결.

## 이 장을 읽는 법(실무용)

1) 지금 하는 작업이 "정책(Policy)"인지 "연결(Integration)"인지부터 분류한다.
2) 정책이면 `src/evalvault/domain/`, 연결이면 `src/evalvault/adapters/`에서 시작한다.
3) 도메인이 외부 구현을 필요로 하면 `src/evalvault/ports/`에 계약을 만들고 어댑터에서 구현한다.

## 목차

- 1. EvalVault의 경계 설계 목표
- 2. 코드 구조 지도(레포에서 실제로 확인 가능한 경로)
- 3. 레이어별 책임: Domain / Ports / Adapters / Config
- 4. 의존성 규칙(예시 포함)과 경계 붕괴 신호
- 5. 조립 지점(composition roots): Web API, CLI
- 6. Outbound 통합: LLM, Storage, Tracing(Tracker/Tracer)
- 7. Inbound 통합: CLI, FastAPI(Web UI)
- 8. 분석 파이프라인 아키텍처(DAG 오케스트레이터)
- 9. 확장 플레이북(새 LLM/새 저장소/새 분석 모듈/새 API 엔드포인트)
- 10. 안티패턴/흔한 실수(어떻게 빨리 감지하는가)
- 11. 리뷰 체크리스트(아키텍처 관점)
- 12. FAQ / 자기 점검 질문
- 13. 실전 시나리오 워크스루(변경 단위별)
- 14. 변경 후 검증 루틴(최소 세트)
- 15. 리팩터링 레시피(경계 유지)
- 16. 퀵 레퍼런스(어디에 무엇을 넣나)

---

## 1. EvalVault의 경계 설계 목표

EvalVault는 "평가/분석"을 반복해서 돌리며 모델/프롬프트/리트리버를 바꾸는 제품이다.
이런 제품에서 가장 흔한 실패는 "실험 코드"와 "운영 코드"가 섞여서, 바꾸기 어려워지는 것이다.

이 레포에서 경계를 강하게 잡는 이유는 대체로 아래 3가지로 요약된다.

### 1) 교체 가능성: 같은 정책을 다른 인프라에서 돌려야 한다

- LLM 제공자(예: openai/ollama/vllm/azure/anthropic)는 바뀔 수 있다.
  - 근거: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`가 provider별로 어댑터를 선택한다.
- 저장소는 PostgreSQL + pgvector로 통합한다.
  - 근거: `src/evalvault/ports/outbound/storage_port.py`(계약) + `src/evalvault/adapters/outbound/storage/postgres_adapter.py`(구현).

### 2) 테스트 가능성: 도메인을 인프라 없이 검증할 수 있어야 한다

도메인이 DB/HTTP/벤더 SDK를 직접 호출하면, 테스트는 "통합 테스트"로만 가능해진다.
그 결과 회귀를 빠르게 잡지 못하고, 리팩터링 비용이 폭증한다.

### 3) 운영 안전성: prod에서 강제해야 하는 설정 규칙이 있다

prod 프로필에서 필요한 시크릿/보안 설정은 애초에 오류로 막아야 한다.
근거: `src/evalvault/config/settings.py#_validate_production_settings`.

---

## 2. 코드 구조 지도(레포에서 실제로 확인 가능한 경로)

EvalVault는 큰 그림에서 아래 구조로 읽으면 된다.

```text
src/evalvault/
  domain/           # "정책": 엔티티/서비스/메트릭/오케스트레이션
  ports/            # "계약": inbound/outbound 포트(Protocol/ABC)
  adapters/         # "구현": CLI/FastAPI + LLM/Storage/Tracker 등 외부 연동
  config/           # "구성": settings, profile 적용, secret resolver

config/models.yaml  # 모델 프로필(선택적). settings가 적용한다.
```

빠른 근거 파일(조립 지점/경계 설명을 볼 때 바로 여는 파일):

- `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`
- `src/evalvault/adapters/inbound/api/main.py#lifespan`
- `src/evalvault/config/settings.py#get_settings`
- `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`
- `src/evalvault/ports/outbound/storage_port.py`
- `src/evalvault/adapters/outbound/storage/postgres_adapter.py`
- `src/evalvault/ports/outbound/tracer_port.py`
- `src/evalvault/ports/outbound/tracker_port.py`

---

## 3. 레이어별 책임: Domain / Ports / Adapters / Config

이 절은 "결정을 내리기 위한 규칙"이다.
파일을 어디에 만들지 애매할 때, 아래 체크를 통과하면 대체로 맞다.

### 3.1 Domain (`src/evalvault/domain/`)

도메인은 "어떻게 평가하고(평가 규칙), 어떻게 분석하고(분석 규칙), 무엇을 저장해야 하는가(데이터 모델)"를 담는다.

근거 예:

- 평가 오케스트레이션(메트릭 실행, 점수/메타데이터 수집 등): `src/evalvault/domain/services/evaluator.py#RagasEvaluator`.
- 분석 파이프라인 오케스트레이터(DAG 실행): `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator`.

도메인에서 "해도 되는 것":

- 정책/규칙을 코드로 표현하기(임계값 판단, 스코어 집계, 실행 순서 등)
- 포트(Protocol/ABC)를 통해 외부 세계를 요청하기
- 도메인 엔티티(데이터 구조) 정의/변환

도메인에서 "하면 안 되는 것"(경계 붕괴):

- DB에 직접 접속하거나 파일 I/O를 직접 수행하기
- FastAPI/Typer 같은 프레임워크 타입을 도메인 모델로 끌고 들어오기
- 특정 벤더 SDK(openai/requests 등)의 구체 구현에 직접 의존하기

주의(현실적인 예외/절충):

- 도메인은 "완전 무의존" 레이어가 아니라, 제품 핵심 로직을 담는 레이어다.
  예를 들어 평가를 위해 `ragas` 같은 평가 라이브러리를 사용할 수 있다.
  핵심은 "LLM 호출/저장/트레이싱" 같은 인프라를 포트 뒤로 감추는 것이다.
  - 근거: `src/evalvault/domain/services/evaluator.py`는 메트릭을 구성하지만, 실제 LLM 호출은 `LLMPort`/`LLMFactoryPort`로 추상화된다.

### 3.2 Ports (`src/evalvault/ports/`)

포트는 "도메인이 외부에 무엇을 요구하는지"(outbound)와 "외부가 도메인에 무엇을 요청할 수 있는지"(inbound)를 계약으로 정의한다.

- Outbound 예: LLM 호출 계약 `src/evalvault/ports/outbound/llm_port.py#LLMPort`.
- Outbound 예: 저장 계약 `src/evalvault/ports/outbound/storage_port.py#StoragePort`.
- Outbound 예: 트레이싱 스팬 계약 `src/evalvault/ports/outbound/tracer_port.py#TracerPort`.
- Inbound 예(Web UI): `src/evalvault/ports/inbound/web_port.py#WebUIPort`.

포트의 규칙:

- 포트는 가능한 한 "기술 스택"을 모른다.
  예: FastAPI Request/Response 타입을 포트에 넣지 않는다.
- 포트는 "도메인 엔티티"와 "프리미티브"를 주로 사용한다.
- 포트는 구현 디테일을 강제하지 않는다(필요한 계약만 제공).

### 3.3 Adapters (`src/evalvault/adapters/`)

어댑터는 포트를 특정 기술 스택으로 구현하고, inbound에서는 외부 입력을 도메인 호출로 변환한다.

Outbound 어댑터 예:

- LLM provider 선택 및 구현: `src/evalvault/adapters/outbound/llm/`.
- Storage 구현(Postgres + pgvector): `src/evalvault/adapters/outbound/storage/postgres_adapter.py`.

Inbound 어댑터 예:

- FastAPI app lifecycle에서 조립: `src/evalvault/adapters/inbound/api/main.py#lifespan`.
- Web UI 어댑터 조립: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`.
- CLI 명령: `src/evalvault/adapters/inbound/cli/commands/run.py`.

어댑터의 규칙:

- 어댑터는 "연결"을 담당한다.
- 어댑터가 도메인 규칙을 임의로 해석해서 정책을 중복하면, 정책 변경 시 깨지기 쉽다.

### 3.4 Config (`src/evalvault/config/` + `config/`)

설정은 "어떤 구현을 쓸지"와 "런타임에서 필요한 값을 어떻게 로드/검증할지"를 담당한다.

- 환경변수/.env 로딩 + 프로필 적용: `src/evalvault/config/settings.py#get_settings`, `src/evalvault/config/settings.py#apply_profile`.
- 모델 프로필 정의: `config/models.yaml`.

---

## 4. 의존성 규칙(예시 포함)과 경계 붕괴 신호

### 4.1 허용되는 의존(대원칙)

- Domain -> Ports: 가능(도메인은 계약을 정의/사용할 수 있다)
- Adapters -> Ports: 가능(어댑터는 계약을 구현한다)
- Adapters -> Domain: 가능(어댑터는 도메인 서비스를 호출한다)

### 4.2 피해야 하는 의존(경계 붕괴)

- Domain -> Adapters: 금지(도메인이 구현을 알면 교체가 어렵다)
- Ports -> Adapters: 금지(계약이 구현을 알면 계약이 깨진다)

### 4.3 레포에서 확인 가능한 "좋은" 의존 예시

Web UI 조립 지점은 어댑터에서 도메인 서비스/포트를 모아 구성한다.

- `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`
  - 설정 로딩: `from evalvault.config.settings import get_settings`
- Storage 구현 주입: `from evalvault.adapters.outbound.storage.postgres_adapter import PostgresStorageAdapter`
  - LLM 구현 선택: `from evalvault.adapters.outbound.llm import get_llm_adapter`
  - 도메인 서비스 생성: `from evalvault.domain.services.evaluator import RagasEvaluator`

즉, 도메인 서비스는 "여기서" 생성되고, 외부 구현(LLM/DB)은 "여기서" 주입된다.

### 4.4 경계 붕괴의 빠른 감지 신호(코드 냄새)

아래 중 하나라도 보이면, 대체로 레이어가 잘못된 것이다.

- 도메인 파일에서 `evalvault.adapters...` import가 보인다.
- 도메인 파일에서 `fastapi`, `typer` 같은 프레임워크 import가 보인다.
- 도메인 로직에서 DB/HTTP/벤더 SDK를 직접 호출한다.
- 어댑터가 임계값/합격 판정 같은 정책 로직을 자체 구현한다(도메인과 중복).

### 4.5 경계 규칙을 스스로 점검하는 빠른 방법(로컬)

"경계가 깨졌다"는 건 보통 diff 몇 줄에서 시작한다. PR이 커지기 전에 빨리 걸러내는 게 가장 싸다.
아래는 코드베이스에서 바로 실행할 수 있는 탐지 방법이다(정책이 아니라, 디버깅/리뷰 보조용).

1) 도메인이 어댑터를 import하는지 확인

```bash
uv run python -c "import pathlib, re; p=pathlib.Path('src/evalvault/domain');\
bad=[];\
for f in p.rglob('*.py'):\
  t=f.read_text(encoding='utf-8');\
  if re.search(r'\bfrom\s+evalvault\.adapters\b|\bimport\s+evalvault\.adapters\b', t):\
    bad.append(str(f));\
print('domain->adapters imports:', len(bad));\
print('\\n'.join(bad[:50]));"
```

2) 도메인이 프레임워크를 직접 import하는지 확인(예: fastapi, typer)

```bash
uv run python -c "import pathlib, re; p=pathlib.Path('src/evalvault/domain');\
bad=[];\
for f in p.rglob('*.py'):\
  t=f.read_text(encoding='utf-8');\
  if re.search(r'\bimport\s+(fastapi|typer)\b|\bfrom\s+(fastapi|typer)\b', t):\
    bad.append(str(f));\
print('domain framework imports:', len(bad));\
print('\\n'.join(bad[:50]));"
```

3) 도메인에서 I/O를 직접 호출하는 흔한 실수 확인(정규식 기반, 오탐 가능)

```bash
uv run python -c "import pathlib, re; p=pathlib.Path('src/evalvault/domain');\
pat=re.compile(r'\b(psycopg|requests|httpx|open\(|Path\(|aiohttp)\b');\
hits=[];\
for f in p.rglob('*.py'):\
  t=f.read_text(encoding='utf-8');\
  if pat.search(t):\
    hits.append(str(f));\
print('domain potential IO refs:', len(hits));\
print('\\n'.join(hits[:50]));"
```

주의:

- 위 스크립트는 "진짜 위반"을 증명하지 않는다. 다만 빠르게 스캔해서 리뷰 포인트를 잡는 데 유용하다.
- 진짜 판단은 "의존성 방향"과 "책임"(정책 vs 연결)을 기준으로 한다.

---

## 5. 조립 지점(composition roots): Web API, CLI

"조립 지점"은 의존성 그래프를 바깥에서 안쪽으로 꽂는 곳이다.
여기서만 "무엇을 실제로 쓸지"(Postgres+pgvector, OpenAI vs Ollama 등)를 결정한다.

### 5.1 Web UI/FastAPI 조립

FastAPI는 lifespan에서 adapter를 만들어 앱 상태로 보관한다.

- 근거: `src/evalvault/adapters/inbound/api/main.py#lifespan`.

Web UI 어댑터 인스턴스는 `create_adapter()`에서 만들어진다.

- 근거: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`.

이 함수는 다음을 수행한다.

- `get_settings()`로 런타임 설정 로딩
- Storage를 기본 Postgres(+pgvector)로 생성
- 설정에 따라 LLM 어댑터를 생성(실패 시 warning 처리)
- `RagasEvaluator` 같은 도메인 서비스를 구성
- 위를 묶어 `WebUIAdapter`를 반환

이 구성은 "기본값"이다.
만약 Web UI에서도 Postgres를 쓰게 만들고 싶다면, 해당 변경은 조립 지점에서 일어나야 한다.
(도메인 서비스 내부에서 DB 분기하면 경계가 붕괴한다.)

### 5.2 CLI 조립

CLI는 command 모듈이 런타임 설정을 읽고, 필요한 어댑터를 직접 초기화한다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/run.py`.

CLI가 하는 일의 본질은 다음 두 가지다.

- 사용자 입력/옵션을 "정규화"해서 설정/요청 모델로 만든다.
- 도메인 서비스/어댑터를 조립하고 실행한다.

### 5.3 Settings의 생명주기: 어디서 로드되고 어떻게 덮어씌워지는가

EvalVault의 설정은 크게 3단계를 거친다.

1) BaseSettings로 환경변수/.env 로딩

- 근거: `src/evalvault/config/settings.py#Settings.model_config`는 `.env`를 읽도록 설정한다.

2) post init에서 경로/시크릿/URL을 정규화

- DB 경로는 repo root(탐색) 기준으로 절대경로로 해석될 수 있다.
  - 근거: `src/evalvault/config/settings.py#_detect_repo_root`, `src/evalvault/config/settings.py#_resolve_storage_path`.
- `secret://` 레퍼런스는 provider를 통해 해석될 수 있다.
  - 근거: `src/evalvault/config/settings.py#Settings._resolve_secret_references`.
- URL 스킴이 없으면 http:// 를 붙여준다(예: Ollama base URL).
  - 근거: `src/evalvault/config/settings.py#_ensure_http_scheme`.

3) 프로필 적용(선택): 모델명/프로바이더만 YAML에서 가져오고, 인프라 URL/타임아웃은 .env 값을 유지

- 근거: `src/evalvault/config/settings.py#apply_profile`.
- 프로필 소스: `config/models.yaml`.

실무에서 중요한 의미:

- "모델 전환"은 profile을 통해 반복 가능하게 만들고, "인프라 전환"(호스트/네트워크)은 환경변수로 관리하는 쪽으로 설계돼 있다.
- prod에서는 누락되면 안 되는 설정을 강제한다.
  - 근거: `src/evalvault/config/settings.py#_validate_production_settings`.

---

## 6. Outbound 통합: LLM, Storage, Tracing(Tracker/Tracer)

### 6.1 LLM 통합: `LLMPort` + provider 선택

LLM 호출은 포트로 추상화돼 있다.

- 근거(계약): `src/evalvault/ports/outbound/llm_port.py#LLMPort`.

실제 구현 선택은 settings의 `llm_provider`에 의해 결정된다.

- 근거(선택): `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`.
- 지원 provider 문자열: openai, ollama, vllm, azure, anthropic.

추가 포인트:

- LLM 팩토리는 fallback용 모델 선택 로직을 갖는다.
  - 근거: `src/evalvault/adapters/outbound/llm/factory.py#SettingsLLMFactory`.
- 이 팩토리는 provider/model 적용 시 settings 객체를 변경(mutate)한다.
  따라서 같은 settings 인스턴스를 여러 컨텍스트에서 공유하는 코드에서는 의도치 않은 영향이 생길 수 있다.
  - 근거: `src/evalvault/adapters/outbound/llm/factory.py#create_llm_adapter_for_model`.

#### 6.1.1 `LLMPort` 계약을 "기능 단위"로 읽는 방법

LLMPort는 "Ragas 메트릭 실행"에 필요한 최소 기능과, "리포트/기타"를 위한 텍스트 생성 기능을 분리해 둔다.

- 모델 식별자: `get_model_name()`
- Ragas 호환 객체: `as_ragas_llm()` / (옵션) `as_ragas_embeddings()`
- 토큰 사용량 계측: `get_token_usage()` 계열(어댑터가 지원할 때)
- 텍스트 생성: `generate_text()` / `agenerate_text()` (리포트 생성 등)
- 추론/생각 모드(프로바이더별 차이 흡수): `get_thinking_config()` / `supports_thinking()`

근거: `src/evalvault/ports/outbound/llm_port.py#LLMPort`.

실무 팁:

- "메트릭 평가"는 `as_ragas_llm()` 중심으로 통합되고,
  "리포트 생성"은 `generate_text()`에 몰리기 쉽다.
  두 경로를 섞으면(예: Ragas용 LLM 객체로 리포트를 생성) provider별 차이가 터질 수 있으니 계약을 기준으로 분리한다.

#### 6.1.2 provider 선택 로직은 어디까지가 책임인가

`get_llm_adapter(settings)`는 provider 문자열을 보고 구현 클래스를 선택한다.

- 근거: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`.

이 선택 로직은 "인프라"에 속한다.
따라서 도메인 서비스는 "OpenAIAdapter" 같은 구현명을 알면 안 되고,
오직 `LLMPort`(계약)와 `LLMFactoryPort`(필요 시)만 알아야 한다.

### 6.2 Storage 통합: `StoragePort` + Postgres(+pgvector)

Storage 계약은 매우 넓다(평가 결과, 피드백, 실험, 파이프라인 결과 등).

- 근거(계약): `src/evalvault/ports/outbound/storage_port.py#StoragePort`.

이 레포의 기본 저장소는 Postgres이며, 벡터 검색도 같은 DB(pgvector)로 통합한다.

- 근거(구현): `src/evalvault/adapters/outbound/storage/postgres_adapter.py`.

#### 6.2.1 `StoragePort` 계약의 폭: 무엇이 저장의 "정책 경계"인가

`StoragePort`가 커 보이는 이유는, EvalVault가 run 단위를 중심으로 많은 산출물을 일관되게 연결하기 때문이다.

대표 카테고리(계약 파일에서 직접 확인 가능):

- 평가 실행 저장/조회: `save_run`, `get_run`, `list_runs`, `delete_run`
- 멀티턴 실행 저장/엑셀: `save_multiturn_run`, `export_multiturn_run_to_excel`
- 프롬프트/프롬프트셋: `save_prompt_set`, `get_prompt_set`, `link_prompt_set_to_run`
- 스테이지 이벤트/메트릭: `save_stage_events`, `list_stage_events`, `save_stage_metrics`, `list_stage_metrics`
- 피드백/집계: `save_feedback`, `list_feedback`, `get_feedback_summary`
- 실험: `save_experiment`, `get_experiment`, `list_experiments`, `update_experiment`
- 분석 히스토리: `save_pipeline_result`, `list_pipeline_results`, `get_pipeline_result`, `save_analysis_report`, `list_analysis_reports`
- 데이터셋 특성 분석 저장/조회: `save_dataset_feature_analysis`, `get_dataset_feature_analysis`
- 회귀 베이스라인: `set_regression_baseline`, `get_regression_baseline`

근거: `src/evalvault/ports/outbound/storage_port.py#StoragePort`.

정책 vs 연결로 다시 나누면:

- 정책: 어떤 데이터를 저장해야 "재현/비교"가 가능한가(도메인 요구)
- 연결: 어떤 DB에 어떤 스키마로 저장하나(어댑터 구현)

#### 6.2.2 Postgres(+pgvector) 운영 포인트

- pgvector 확장이 활성화되어 있어야 한다.
- 스키마/마이그레이션은 Postgres 기준으로 적용된다.
  - 근거: `src/evalvault/adapters/outbound/storage/postgres_schema.sql`.

이 동작을 이해해야 하는 이유:

- 운영 환경별 extension/권한 차이로 초기화 단계에서 실패할 수 있다.
- 스키마 불일치는 분석/검색 재현성을 깨뜨린다.

### 6.3 Tracing: TracerPort vs TrackerPort

이 레포에는 "트레이싱" 성격의 포트가 두 가지가 있다.

1) 도메인 서비스가 사용하는 "스팬" 중심 포트

- 근거: `src/evalvault/ports/outbound/tracer_port.py#TracerPort`.
- 특징: context manager 기반 스팬(`span()`)과 attribute 부착(`set_span_attributes()`)을 제공한다.

2) 평가 실행 결과를 외부 시스템에 기록하는 "트래커" 포트

- 근거: `src/evalvault/ports/outbound/tracker_port.py#TrackerPort`.
- 특징: trace 시작/스팬 추가/스코어 기록/아티팩트 저장/end 등 "run 로그"를 다룬다.

둘을 분리하면 좋은 이유:

- TracerPort는 "도메인 내부 타이밍/단계"를 추적하는 최소 계약이 될 수 있다.
- TrackerPort는 Langfuse/MLflow 같은 시스템 통합의 표면적을 포트로 감싼다.

#### 6.3.1 실무 기준: 언제 TracerPort를 쓰고, 언제 TrackerPort를 쓰나

하나의 규칙으로 정리하면 아래와 같다.

- TracerPort: "이 도메인 함수/단계"가 어느 정도 걸렸는지, 어떤 속성으로 분류할지(내부 관측)
- TrackerPort: "이 run"을 외부 시스템에서 다시 찾아볼 수 있게, 점수/아티팩트를 구조적으로 남기기(외부 관측)

혼용의 위험:

- TrackerPort를 도메인 깊숙이 끌고 들어오면, 도메인이 외부 트래커의 데이터 모델/제약을 따라가게 된다.
- TracerPort만으로 끝내면, 사용자/팀이 run 단위로 결과를 찾아 재현하기 어려워진다.

---

## 7. Inbound 통합: CLI, FastAPI(Web UI)

### 7.1 Web UI inbound 계약: `WebUIPort`

Web UI가 할 수 있는 기능(평가 실행/목록/리포트 생성/스테이지 이벤트 조회 등)은 inbound 포트로 정의돼 있다.

- 근거: `src/evalvault/ports/inbound/web_port.py#WebUIPort`.

이 포트는 "프레임워크 타입" 대신 dataclass 요청/응답 모델을 쓴다.
예: `EvalRequest`, `RunSummary`, `RunFilters`.

이 패턴의 장점:

- FastAPI의 request/response 스키마가 바뀌어도 도메인 호출면을 유지하기 쉽다.
- CLI/Web UI가 같은 도메인 서비스를 공유하기 쉬워진다.

### 7.2 FastAPI 라이프사이클

FastAPI 앱은 lifespan에서 adapter를 초기화하고 `app.state`에 보관한다.

- 근거: `src/evalvault/adapters/inbound/api/main.py#lifespan`.

추가로, 특정 사전 작업을 시도한다(실패하면 warning).

- 근거: `src/evalvault/adapters/inbound/api/main.py`에서 `warm_rag_index()` 호출.

---

## 8. 분석 파이프라인 아키텍처(DAG 오케스트레이터)

EvalVault의 분석은 "노드/엣지"로 구성된 DAG 파이프라인으로 실행될 수 있다.

도메인에 오케스트레이터가 있고, 분석 모듈은 포트로 추상화된다.

- 근거(오케스트레이터): `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator`.
- 근거(모듈 계약): `src/evalvault/ports/outbound/analysis_module_port.py` (오케스트레이터는 이 포트를 타입으로 참조).

오케스트레이터가 제공하는 핵심 기능:

- 모듈 등록(register_module)
- 의도(intent)와 템플릿에 따라 파이프라인 빌드(build_pipeline)
- 위상 정렬로 노드 실행(execute)
- 의존 노드 실패 시 스킵 처리(Dependency failed)

이 구조의 중요한 함정:

- 노드가 실패했을 때 "어디까지를 실패로 볼지"는 정책이다.
  오케스트레이터가 최소한의 정책(의존 실패 시 스킵)을 갖고 있으므로,
  추가 정책을 넣을 때는 도메인에 넣을지(정책) 어댑터에 넣을지(연결) 의식적으로 결정해야 한다.

### 8.1 실행 의미론: 오케스트레이터를 "리트머스 테스트"로 읽기

PipelineOrchestrator의 execute 흐름은 "아키텍처가 원하는 실패 모델"을 그대로 드러낸다.

- 위상 정렬로 노드 실행: `pipeline.topological_order()`
- 의존 노드 실패 시 현재 노드를 SKIPPED 처리
- 리프 노드들의 출력(final_output)을 수집
- 리프 노드가 없으면 마지막 실행 노드 출력 사용

근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator.execute`.

이 의미론을 문서화하는 이유:

- 분석 결과가 "왜 비었는지"(리프 없음 vs 실패 스킵) 설명할 수 있어야 한다.
- 노드를 추가/재배치할 때, 결과 수집 정책이 바뀌는지 확인해야 한다.

### 8.2 모듈 등록/메타데이터: 템플릿 기반 시스템의 함정

오케스트레이터는 모듈을 dict로 보관하고, 모듈이 metadata를 제공하면 catalog에 등록한다.

- 근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator.register_module`.

실무에서 흔한 실수:

- 모듈 구현만 추가하고 등록을 빼먹어서 `Module not found: ...`가 뜬다.
- 템플릿에서 참조하는 module_id와 실제 구현의 module_id가 달라서 런타임에만 실패한다.

이런 실패를 줄이는 방법(원칙):

- module_id는 "코드"와 "템플릿"의 조인 키다. 이름 변경은 API 변경에 준하는 비용이 든다.
- 따라서 module_id 변경이 필요하면, 일시적으로 alias/호환 레이어를 두는 쪽이 안전하다.

---

## 9. 확장 플레이북(새 LLM/새 저장소/새 분석 모듈/새 API 엔드포인트)

이 절은 "어디에 무엇을 추가하는가"를 절차로 정리한다.
각 플레이북은 (1) 바꿀 파일, (2) 금지사항, (3) 실패 시 흔한 원인을 포함한다.

### 9.1 새 LLM provider 추가

목표: settings의 provider 선택으로 새로운 구현을 주입할 수 있게 한다.

바꿀/추가할 곳(최소):

- 새 어댑터 구현: `src/evalvault/adapters/outbound/llm/` 아래에 파일 추가
- 선택 로직 연결: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`
- 필요한 설정 키 추가(필요할 때만): `src/evalvault/config/settings.py#Settings`

금지사항:

- 도메인 서비스가 provider별 분기를 직접 갖게 만들지 말 것.
  provider 분기는 조립 지점/어댑터 선택에서 끝나야 한다.

실패 패턴(자주 보는 문제):

- provider 문자열 불일치(소문자 정규화 필요)
- 인증키/URL 같은 설정값이 prod 검증 로직에 반영되지 않음
  - 근거: `src/evalvault/config/settings.py#_validate_production_settings`

### 9.2 새 저장소(또는 저장 정책 변경)

저장은 `StoragePort` 계약을 중심으로 움직인다.

바꿀/추가할 곳:

- 계약을 변경해야 한다면: `src/evalvault/ports/outbound/storage_port.py`.
- 구현을 추가한다면: `src/evalvault/adapters/outbound/storage/`.
- 런타임에서 실제 구현을 선택하는 위치를 찾아 조립한다.
  - Web UI 기본 조립은 `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`.

금지사항:

- 도메인 서비스 내부에서 DB 백엔드를 직접 선택하지 말 것.
- 스키마/마이그레이션은 어댑터 책임으로 둘 것.
  - Postgres 스키마는 `postgres_schema.sql`을 기준으로 유지한다.
    근거: `src/evalvault/adapters/outbound/storage/postgres_schema.sql`.

### 9.3 새 분석 모듈(파이프라인 노드) 추가

대원칙: 파이프라인 오케스트레이터는 "노드를 실행"할 뿐이며, 모듈은 등록되어야 한다.

바꿀/추가할 곳(일반적):

- 모듈 구현(포트 구현체): `src/evalvault/adapters/outbound/analysis/` 또는 해당 도메인에 맞는 위치
- 모듈 등록: 오케스트레이터를 생성/조립하는 위치에서 `register_module()` 호출
  - 근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator.register_module`

주의:

- 분석 모듈이 외부 라이브러리에 강하게 의존한다면, 도메인에 두기보다 어댑터에 두는 것이 경계 유지에 유리하다.
  다만 "정책"이 된다면 도메인 쪽에 인터페이스/핵심 규칙을 남겨야 한다.

### 9.4 새 API 엔드포인트 추가

바꿀/추가할 곳:

- FastAPI 라우터: `src/evalvault/adapters/inbound/api/routers/` 아래
- 필요한 기능은 `WebUIPort` 또는 다른 inbound 포트로 표현하고, 어댑터가 이를 구현/호출한다.

금지사항:

- 라우터 함수에서 바로 DB/LLM을 호출하지 말 것.
  (라우터는 inbound 어댑터의 "얇은" 층이어야 한다.)

---

## 10. 안티패턴/흔한 실수(어떻게 빨리 감지하는가)

### 10.1 도메인에서 인프라를 직접 호출

증상:

- 도메인 서비스에 psycopg/openai SDK/requests 호출이 섞임

결과:

- 교체 비용 증가(벤더 변경 시 도메인 로직까지 침범)
- 테스트가 느려짐/불안정해짐

대안:

- 포트 계약을 만들고 어댑터에서 구현

### 10.2 어댑터가 정책을 소유

증상:

- API/CLI에서 임계값 판단, pass/fail 정책을 자체 구현

결과:

- 정책이 분기별로 달라져 결과 비교가 어려워짐

대안:

- 정책은 도메인 서비스로 이동시키고, 어댑터는 입력/출력 변환으로 제한

### 10.3 설정 하드코딩

증상:

- 코드에 URL/키/모델명을 직접 넣음

대안:

- `src/evalvault/config/settings.py`에 설정 필드 추가
- 모델 프로필은 `config/models.yaml`을 사용

---

## 11. 리뷰 체크리스트(아키텍처 관점)

아래 체크리스트는 PR 리뷰에서 그대로 복사해 쓰는 것을 의도한다.

### 11.1 경계/의존성

- [ ] 도메인(`src/evalvault/domain/`)에서 `evalvault.adapters`를 import하지 않는가?
- [ ] 도메인에서 DB/HTTP/벤더 SDK 직접 호출이 없는가?
- [ ] 포트(`src/evalvault/ports/`)가 구현(어댑터)을 알지 않는가?

### 11.2 조립 지점

- [ ] 새 구현 선택 로직이 도메인 안으로 들어오지 않았는가?
- [ ] Web UI 조립(`src/evalvault/adapters/inbound/api/adapter.py#create_adapter`) 또는 CLI 조립에서 주입하는가?

### 11.3 설정/보안

- [ ] prod 프로필에서 필수 설정 누락을 막는가?
  - 근거: `src/evalvault/config/settings.py#_validate_production_settings`
- [ ] 시크릿이 코드/문서에 하드코딩되지 않는가?

### 11.4 변경의 최소화(특히 버그픽스)

- [ ] 버그 수정인데 리팩터링/재배치가 같이 들어오지 않았는가?
- [ ] 계약(포트) 변경이 있다면, 구현 어댑터/조립 지점/호출부가 모두 함께 업데이트됐는가?

---

## 12. FAQ / 자기 점검 질문

### FAQ

Q1. "이 로직은 도메인인가 어댑터인가?"를 빠르게 가르는 기준은?

- 정책(평가 규칙, 임계값 판단, DAG 실행 규칙)이라면 도메인.
- 외부 연동(LLM/DB/HTTP/트레이싱/파일 I/O)이라면 어댑터.
- 도메인이 외부 연동이 필요하면 포트를 만들고 어댑터에서 구현.

Q2. "포트"는 언제 새로 만들어야 하나?

- 도메인 서비스가 외부 세계에 "새로운 능력"을 요구하는데, 기존 포트로 표현이 어렵다면.
- 단순히 구현을 하나 더 붙이는 정도(새 LLM provider)는 기존 포트 아래 어댑터만 추가하면 될 때가 많다.
  - 근거: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`는 같은 `LLMPort` 아래 구현을 교체한다.

Q3. 도메인이 아웃바운드 구현을 알게 되면 어떤 문제가 생기나?

- 교체 비용이 도메인까지 전염된다.
- 테스트가 느려지고(통합 테스트 강제), 운영 환경에서만 재현되는 버그가 늘어난다.

### 자기 점검 질문

1) 내가 추가하려는 코드는 "정책"인가 "연결"인가? 둘 다면 어떻게 분리할 것인가?
2) 지금 PR에서 조립 지점은 어디인가(`create_adapter`, CLI command 등)?
3) 포트 계약이 바뀌면, 어떤 어댑터가 깨질지(최소 2개) 떠올릴 수 있는가?

---

## 13. 실전 시나리오 워크스루(변경 단위별)

이 절은 "설명을 읽고도 여전히 막히는" 상황을 줄이기 위해 만든, 구체적 워크스루다.
아래 시나리오는 실제 레포의 경로/함수명을 근거로 삼되, 특정 구현을 단정하지 않고 "변경 설계" 관점으로만 안내한다.

### 13.1 시나리오 A: 저장소 구성을 바꾸고 싶다 (Postgres+pgvector 유지)

상황:

- 운영 복잡도를 줄이기 위해 RDB와 벡터 스토리지를 Postgres+pgvector로 통합했다.

현재 관찰(근거):

- Web UI 조립 지점은 storage factory를 사용한다.
  - 근거: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`에서 `build_storage_adapter` 호출.
- Postgres 연결 설정 키는 settings에 있다.
  - 근거: `src/evalvault/config/settings.py#Settings`의 `postgres_*` 필드.

설계 원칙:

- 이 변경은 "도메인 정책"이 아니라 "조립/연결"이다.
- 따라서 변경 포인트는 `create_adapter()` 같은 composition root에 있어야 한다.

권장 접근(절차):

1) Postgres 연결 설정을 확정한다.

- `POSTGRES_CONNECTION_STRING` 또는 `POSTGRES_HOST/PORT/USER/PASSWORD`를 사용한다.

2) 조립 지점에서 Postgres 어댑터를 생성한다.

- 후보 위치: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`.

주의:

- prod에서 Postgres를 켤 때는 `src/evalvault/config/settings.py#_validate_production_settings`의 검증과 충돌이 없는지 확인해야 한다.

실패/장애 패턴:

- 잘못된 DSN/권한으로 인해 startup 시점에 앱이 뜨지 않음
- pgvector 확장이 활성화되지 않아 벡터 기능이 실패함

이때의 원칙:

- 도메인/포트는 고치지 않는다.
- 문제가 나면 adapter/설정/DB 스키마 계층에서 해결한다.

### 13.2 시나리오 B: 새 LLM provider를 추가하고 싶다

상황:

- 기존 provider(openai/ollama/vllm/azure/anthropic) 외의 새로운 provider를 붙이고 싶다.

현재 관찰(근거):

- provider 선택은 `get_llm_adapter(settings)`에서 일어난다.
  - 근거: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`.
- 도메인 서비스는 `LLMPort`를 통해 LLM 기능을 사용한다.
  - 근거: `src/evalvault/ports/outbound/llm_port.py#LLMPort`.

설계 원칙:

- 도메인에 provider 분기를 넣지 않는다.
- 새로운 구현은 `LLMPort`를 구현하는 어댑터로 추가한다.

권장 접근(절차):

1) 어댑터 파일 추가

- 위치: `src/evalvault/adapters/outbound/llm/<new_provider>_adapter.py`
- 해야 하는 일: `LLMPort` 계약 메서드 구현

의사 코드(인터페이스 중심):

```python
# src/evalvault/adapters/outbound/llm/new_provider_adapter.py
from evalvault.ports.outbound.llm_port import LLMPort

class NewProviderAdapter(LLMPort):
    def __init__(self, settings: Settings) -> None:
        ...

    def get_model_name(self) -> str:
        ...

    def as_ragas_llm(self):
        ...
```

2) 선택 로직에 provider 추가

- 위치: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`

3) settings에 필요한 설정 키 추가(필요 시)

- 위치: `src/evalvault/config/settings.py#Settings`
- prod 검증 로직 업데이트(필요 시)
  - 위치: `src/evalvault/config/settings.py#_validate_production_settings`

4) 조립 지점에서 실제로 동작하는지 확인

- Web UI: `src/evalvault/adapters/inbound/api/adapter.py#create_adapter`가 `get_llm_adapter()`를 호출한다.
- CLI: 여러 command가 `get_llm_adapter(settings)`를 호출한다(예: `src/evalvault/adapters/inbound/cli/commands/run.py`).

실패 패턴:

- `llm_provider` 문자열 불일치(대소문자/공백)
- `as_ragas_llm()`이 Ragas가 기대하는 타입/계약과 불일치

### 13.3 시나리오 C: 도메인 정책을 바꾸고 싶은데, 어디부터 고쳐야 할지 모르겠다

여기서 말하는 "정책"은 예를 들어 아래 같은 것들이다.

- 점수 집계 방식
- 임계값 적용/우선순위
- 평가 실행의 단계/순서
- 분석 DAG의 실패 처리 규칙

시작점(대부분):

- 평가 오케스트레이션: `src/evalvault/domain/services/evaluator.py#RagasEvaluator`
- 분석 오케스트레이션: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator`

진단 질문(이 질문에 답하면 파일이 정해진다):

1) 이 정책은 "입력/출력 형식"을 바꾸는가?
   - 바꾼다면: inbound 포트 dataclass(`src/evalvault/ports/inbound/web_port.py#EvalRequest` 등)까지 영향이 갈 수 있다.

2) 이 정책은 "외부 호출"의 의미를 바꾸는가?
   - 바꾼다면: 포트 계약이 바뀔 수 있다.
   - 단, 단지 "어떤 구현을 쓰느냐"면 포트가 아니라 조립 지점 문제일 가능성이 크다.

3) 이 정책은 "저장되는 데이터"를 바꾸는가?
   - 바꾼다면: 도메인 엔티티 + StoragePort 계약 + 저장 어댑터까지 연쇄적으로 바뀐다.

원칙:

- 정책 변경과 연결 변경을 한 PR에서 섞으면 회귀 분석이 어려워진다.
- 특히 버그픽스는 "최소 변경"으로 끝낸다.

### 13.4 시나리오 D: 파이프라인 노드를 하나 추가했는데 런타임에서만 깨진다

가장 흔한 원인:

- module_id 불일치(템플릿에서 참조한 문자열과 구현체의 module_id가 다름)
- register_module() 호출 누락

관찰 포인트(근거):

- 등록이 빠지면 오케스트레이터는 `Module not found: ...`로 실패시킨다.
  - 근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator._execute_node`.

디버깅 접근:

- 오케스트레이터가 "등록된 모듈 목록"을 제공한다.
  - 근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator.list_registered_modules`.
- 의도된 템플릿이 선택되는지 확인한다.
  - 근거: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator.build_pipeline`는 template_registry에서 템플릿을 가져온다.

---

## 14. 변경 후 검증 루틴(최소 세트)

아키텍처 변경은 "기능이 된다"보다 "다음 변경이 안전하다"가 더 중요하다.
최소 검증 세트는 아래와 같다(레포 가이드 기준).

### 14.1 정적 검사/포맷

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### 14.2 테스트

```bash
uv run pytest tests -v
```

주의:

- 외부 API가 필요한 통합 테스트는 환경설정이 없으면 스킵될 수 있다(레포 가이드 참고).

### 14.3 "경계" 관점의 수동 체크(짧지만 효과 큼)

- 도메인 변경이면: `src/evalvault/domain/`에서 인프라 import가 새로 생기지 않았는지 확인
- 포트 변경이면: 영향을 받는 어댑터 구현이 모두 업데이트됐는지 확인
- 조립 지점 변경이면: Web UI(`create_adapter`), CLI command 경로에서 모두 동작하는지 확인

실무 팁:

- boundary 회귀는 대개 "작은 import 한 줄"로 시작한다. diff에서 import 블록을 먼저 본다.

---

## 15. 리팩터링 레시피(경계 유지)

이 절은 "기능 추가"가 아니라 "이미 들어간 변경"을 정리할 때 쓰는 실전 레시피다.
모든 레시피는 경계(Policy vs Integration)를 다시 복원하는 것을 목표로 한다.

### 15.1 어댑터에 스며든 정책을 도메인으로 이동하기

증상:

- `src/evalvault/adapters/`에서 임계값 비교, pass/fail 판정, 스코어 집계가 발생한다.
- CLI와 Web UI가 같은 데이터를 다르게 해석한다(정책이 중복되었기 때문).

원칙:

- 정책은 도메인 서비스로 옮긴다.
- 어댑터는 "입력 정규화"와 "출력 포맷팅"에 집중한다.

절차(권장):

1) 정책 코드가 사용하는 입력/출력을 명확히 적는다(프리미티브/도메인 엔티티).
2) 그 입력/출력을 받아 처리하는 도메인 함수를 만든다.
3) 어댑터에서는 그 함수를 호출하도록 바꾼다.
4) 정책 코드가 외부 I/O를 직접 하고 있었다면, 포트로 분리한다.

"어디에 둘지" 힌트:

- 평가/스코어/임계값: `src/evalvault/domain/services/` 또는 `src/evalvault/domain/metrics/`
- 분석 DAG 실행 규칙: `src/evalvault/domain/services/pipeline_orchestrator.py`

### 15.2 도메인이 외부 능력을 필요로 할 때: 포트 도입하기

증상:

- 도메인 로직이 "저장"이나 "외부 호출"이 필요한데, 임시로 어댑터를 import하거나 SDK를 직접 부른다.

원칙:

- 도메인 -> 포트(계약)만 알게 만들고, 구현은 어댑터로 내린다.

절차(권장):

1) 도메인이 "무엇을" 원하나를 문장으로 먼저 쓴다.
   - 예: "Run 결과를 저장하고 run_id를 반환해라".
2) `src/evalvault/ports/outbound/`에 Protocol/ABC로 계약을 만든다.
3) 도메인 서비스는 그 계약(타입)만 의존하도록 바꾼다.
4) 어댑터에서 계약을 구현한다.
5) 조립 지점에서 구현을 주입한다.

실제 계약의 좋은 참고:

- LLM: `src/evalvault/ports/outbound/llm_port.py#LLMPort`
- Storage: `src/evalvault/ports/outbound/storage_port.py#StoragePort`
- Tracer: `src/evalvault/ports/outbound/tracer_port.py#TracerPort`

### 15.3 포트를 변경해야 할 때(호환 유지)

포트 변경은 사실상 "API 변경"이다. 영향이 광범위하므로 절차를 지키는 게 중요하다.

권장 전략:

1) 새 메서드를 추가하고, 기존 메서드는 당분간 유지한다.
2) 구현 어댑터를 모두 업데이트한다.
3) 호출부(도메인 서비스)를 새 메서드로 옮긴다.
4) 일정 기간 후(또는 같은 PR에서) 기존 메서드를 제거한다.

주의:

- 한 번에 "계약 변경 + 구현 변경 + 호출 변경"을 동시에 크게 하면 리뷰가 불가능해진다.
- 가능하면 두 단계로 나누고(호환 단계 -> 정리 단계), 중간에 테스트로 안전망을 만든다.

### 15.4 Settings를 바꿀 때의 함정(글로벌 싱글톤)

관찰(근거):

- settings는 전역 캐시를 가진다.
  - 근거: `src/evalvault/config/settings.py`의 `_settings` + `get_settings()`.

이 구조에서 생길 수 있는 문제:

- 테스트에서 settings가 오염되면 다음 테스트에 영향을 준다.
- 런타임에서 설정을 부분 업데이트할 때, 어떤 키가 모델 프로필을 무효화하는지 이해해야 한다.
  - 근거: `src/evalvault/config/settings.py#apply_runtime_overrides`의 `model_override_keys` 처리.

레시피:

- 테스트라면 settings 캐시를 리셋하는 유틸을 쓰는 쪽이 안전하다.
  - 근거: `src/evalvault/config/settings.py#reset_settings`.

### 15.5 provider 분기를 "한 곳"으로 모으기

증상:

- 여러 파일에서 provider 문자열을 비교하며 분기한다.
- provider가 늘어날수록 누락/불일치가 증가한다.

원칙:

- provider 분기는 어댑터 선택 함수(예: `get_llm_adapter`) 또는 조립 지점으로 몰아 넣는다.

근거(레포의 의도된 형태):

- LLM provider 분기: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`

체크리스트:

- [ ] provider 문자열 비교가 도메인/포트에 들어오지 않았는가?
- [ ] 분기가 필요한 경우, "설정 -> 구현 선택" 단 하나의 함수로 수렴시킬 수 없는가?

---

## 16. 퀵 레퍼런스(어디에 무엇을 넣나)

이 절은 "파일을 어디에 만들지" 30초 안에 결정하기 위한 표다.

### 16.1 결정 트리(간단 버전)

1) 외부 시스템과 통신/저장/계측이 필요한가?

- Yes -> `src/evalvault/adapters/` (필요하면 포트부터)
- No -> 2로

2) 정책/규칙(점수/임계값/실행 순서)을 바꾸는가?

- Yes -> `src/evalvault/domain/`
- No -> 3로

3) 단지 API/CLI 입력/출력 포맷을 바꾸는가?

- Yes -> `src/evalvault/adapters/inbound/`
- No -> 도메인/어댑터 중 애매하면 "정책 vs 연결"로 다시 분류

### 16.2 레이어별 "허용 import" 감각(짧은 규칙)

Domain (`src/evalvault/domain/`):

- OK: `evalvault.domain.*`, `evalvault.ports.*`, 표준 라이브러리, 평가/분석 라이브러리(필요 시)
- NO: `evalvault.adapters.*`, `fastapi`, `typer`, DB 드라이버/HTTP 클라이언트 직접 사용

Ports (`src/evalvault/ports/`):

- OK: `typing`, `dataclasses`, 도메인 엔티티(필요 최소)
- NO: 어댑터 구현 import

Adapters (`src/evalvault/adapters/`):

- OK: 포트/도메인 import, 벤더 SDK/DB 드라이버/프레임워크
- NO(권장): 도메인 정책을 재구현

Config (`src/evalvault/config/`):

- OK: pydantic settings, secret resolver, 모델 프로필 로딩
- NO(권장): 도메인 정책 로직(설정은 선택/검증까지만)

### 16.3 자주 쓰는 "근거 파일" 인덱스

LLM:

- 계약: `src/evalvault/ports/outbound/llm_port.py`
- 구현 선택: `src/evalvault/adapters/outbound/llm/__init__.py`
- fallback 팩토리: `src/evalvault/adapters/outbound/llm/factory.py`

Storage:

- 계약: `src/evalvault/ports/outbound/storage_port.py`
- Postgres(+pgvector) 구현: `src/evalvault/adapters/outbound/storage/postgres_adapter.py`

Tracing:

- span 포트: `src/evalvault/ports/outbound/tracer_port.py`
- tracker 포트: `src/evalvault/ports/outbound/tracker_port.py`

Web UI/FastAPI:

- 조립: `src/evalvault/adapters/inbound/api/adapter.py`
- lifespan: `src/evalvault/adapters/inbound/api/main.py`
- inbound 계약: `src/evalvault/ports/inbound/web_port.py`

Analysis pipeline:

- 오케스트레이터: `src/evalvault/domain/services/pipeline_orchestrator.py`

Settings:

- settings 정의/검증/프로필 적용: `src/evalvault/config/settings.py`
- 모델 프로필: `config/models.yaml`
