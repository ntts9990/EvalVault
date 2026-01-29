# 00. Overview (내부 핸드북)

이 챕터는 EvalVault를 처음 접하는 내부 구성원이 “무엇을/왜/어떻게”를 빠르게 파악하고,
바로 실행-검증-개선 루프에 진입할 수 있도록 만든 완결형 문서다.

## TL;DR (30초 요약)

- EvalVault의 기본 단위는 `run_id`다. 한 번의 평가 실행이 `run_id`로 식별되며, 평가/분석/리포트/아티팩트가 한 덩어리로 묶인다.
- 목표는 “점수 올리기”가 아니라 “변경이 진짜 개선인지”를 재현 가능하게 증명하고, 회귀의 원인을 설명 가능한 수준까지 좁히는 것이다.
- 선택 기능(트레이싱, 실험 추적, 도메인 메모리, 분석 DAG)은 ‘있으면 좋음’이지 필수 전제가 아니다.

## 이 문서의 사용법 (인지 부하 최소화)

이 핸드북은 아래 패턴을 반복한다.

- 먼저: 스캔 가능한 요약(목표/결과물/체크리스트)
- 그다음: 단계별 절차(명령어, 기대 결과, 실패 시 조치)
- 마지막: 기준(합격/실패 정의, 흔한 함정, 자기 점검 질문)

## 미션 (한 문장)

RAG 시스템의 변경이 “진짜 개선”인지 데이터를 기반으로 재현 가능하게 검증하고,
점수 변화의 원인을 모듈/스테이지/메트릭 수준으로 설명 가능한 워크플로를 제공한다.

## 대상 사용자

- RAG를 운영하는 ML/플랫폼/백엔드 엔지니어
- 품질/회귀를 책임지는 QA/PM
- 반복 평가/벤치마크가 필요한 PoC/컨설팅/솔루션 팀

## 핵심 가치 (3)

1) 재현성: 동일한 입력(데이터셋, 설정, 메트릭)으로 동일한 산출물을 다시 만들 수 있다.
2) 진단 가능성: “왜 떨어졌는지”를 아티팩트와 근거로 따라갈 수 있다.
3) 옵션화: 관측/학습/분석은 필요할 때만 켠다(기본 루프를 방해하지 않는다).

## Non-goals (3)

1) RAG 시스템 자체를 대신 구현하거나 운영하지 않는다.
2) 단일 점수 하나로 모든 품질을 대체하지 않는다(다중 메트릭 + 근거).
3) 특정 벤더/모델에 종속되지 않는다(프로필로 교체 가능).

---

## 핵심 개념 (공통 언어)

### run_id

평가 실행의 단일 식별자.

- 저장소(DB)에서 실행을 조회할 때의 키
- 분석/리포트/대시보드/아티팩트 파일명에 포함되는 키
- 비교(A/B), 회귀 게이트, UI 동기화의 기준점

### Dataset (데이터셋)

평가 대상의 집합.

- 최소 구성: 질문/답변/컨텍스트
- 선택 구성: 정답(ground truth), 메타데이터, 메트릭별 임계값

### Metrics (메트릭)

품질을 수치화하는 함수.

- ragas 기반 메트릭 + 커스텀 도메인 메트릭이 공존
- 일부 메트릭은 `ground_truth`가 필요하고, 일부는 컨텍스트만으로 계산된다.

### Stages (스테이지)

RAG 파이프라인을 “단계”로 쪼개 관측 가능하게 만드는 개념.

- 입력/검색/생성 등의 흐름에서 이벤트와 메트릭을 남겨 원인 추적을 돕는다.
- 핵심은 “추정”이 아니라 “근거”다.

### Artifacts (아티팩트)

분석의 근거 자료.

- 사람용 요약(리포트)과 기계용 원본(JSON)을 분리한다.
- 분석 결과는 `index.json`을 통해 “어떤 근거 파일이 어디에 있는지”가 검색 가능하게 정리된다.

### Profiles (프로필)

모델/임베딩/리트리버/추적 옵션을 런타임에서 스위칭하는 구성 방식.

- 코드 수정이 아니라 설정/환경변수로 교체한다.

---

## EvalVault가 해결하는 핵심 질문

이 질문에 “예/아니오 + 근거”로 답할 수 있으면 성공이다.

1) 이번 변경은 실제로 개선인가?
2) 개선/회귀가 발생한 지점은 어디인가(데이터/메트릭/모듈/스테이지)?
3) 다음 액션은 무엇인가(프롬프트, 리트리버, 데이터, 가드레일)?

---

## 최소 실행 (5분 안에 성공하기)

### 전제

- Python/uv 환경이 준비되어 있고, 필요한 LLM 설정이 되어 있다.
- DB 경로는 로컬 파일로 사용한다.

### 실행

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 기대 결과 (무엇이 생기면 성공인가)

- `run_id`가 출력된다.
- 분석 산출물이 생성된다.

대표 산출물(경로는 기본 설정 기준):

- 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
- 보고서(Markdown): `reports/analysis/analysis_<RUN_ID>.md`
- 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

### 실패했을 때 (가장 흔한 3가지)

1) LLM 키/프로필 미설정
2) DB 경로 권한/경로 오류
3) 선택 메트릭이 요구하는 입력(예: ground truth) 부족

---

## CLI와 Web UI가 연결되는 방식

EvalVault는 “같은 실행 데이터(같은 DB)”를 CLI와 Web UI가 함께 보는 구조다.

### 로컬 개발 기준

```bash
# Terminal 1 (API)
uv run evalvault serve-api --reload

# Terminal 2 (Web UI)
cd frontend
npm install
npm run dev
```

핵심 규칙:

- CLI 실행 시 사용한 DB 경로와 Web UI(API)가 바라보는 DB 경로가 같아야 한다.
- 같다면 CLI로 만든 `run_id`가 UI에 즉시 나타난다.

---

## 문서 읽기 순서 (추천)

이 핸드북은 서로 독립적으로 읽어도 되지만, 처음엔 아래 순서가 빠르다.

1) `01_architecture.md` (경계/구조)
2) `02_data_and_metrics.md` (입력/산출/메트릭)
3) `03_workflows.md` (실전 루프)
4) `06_quality_and_testing.md` (회귀 게이트/검증)
5) `04_operations.md` + `05_security.md` (운영/보안)
6) `07_ux_and_product.md` (제품/UX)
7) `08_roadmap.md` (우선순위/계획)

---

## 빠른 체크리스트 (이 챕터를 다 읽었다면)

- [ ] `run_id`가 무엇이며 어디에 쓰이는지 1문장으로 설명할 수 있다.
- [ ] “평가 → 분석 → 비교 → 개선” 루프를 CLI로 한 번 끝까지 돌릴 수 있다.
- [ ] 산출물 3종(요약 JSON, MD 리포트, artifacts/index.json)을 구분할 수 있다.
- [ ] 선택 기능(트레이싱/학습/분석)이 기본 루프의 필수 전제가 아님을 이해한다.

## 자기 점검 질문 (Retrieval Practice)

1) `--auto-analyze`를 켜면 무엇이 추가로 생성되는가?
2) `run_id` 하나로 어떤 것들이 묶이는가?
3) Web UI에서 결과가 안 보일 때 가장 먼저 확인할 것은 무엇인가?

---

## 프로젝트 스냅샷(“지금 우리가 가진 것”)

이 섹션은 “문서가 아니라 코드/설정이 실제로 무엇을 말하고 있는지”를 기준으로 현재 상태를 확인한다.
숫자/해시는 문서에 고정하지 않고, 아래 명령으로 언제든 재생성한다.

```bash
# 현재 커밋(스냅샷의 기준점)
git rev-parse HEAD

# tracked 파일 수(대략적인 규모 파악)
git ls-files | wc -l

# (선택) 문서 파일 수
git ls-files docs | wc -l
```

운영/리뷰에서 권장:

- 장애/회귀/리팩터링 이슈를 남길 때 커밋 해시를 함께 기록한다.
- “문서가 현실과 달라졌다”는 의심이 들면, 커밋 해시를 기준으로 원인(코드/설정 변화)을 좁힌다.

---

## 핸드북 작성 철학(거짓 정보 방지 규칙)

### 1) ‘정답’ 우선순위

EvalVault에서 사실의 우선순위는 아래 순서다.

1) 코드/테스트/CLI 도움말(실행 가능한 진실)
2) 내부 설계 기준 문서(원칙/규칙)
3) 실사용 가이드(운영/사용 루틴)
4) 핸드북(교과서형 설명)

핸드북이 위 항목들과 충돌하면, 핸드북이 아니라 위 항목을 우선한다.

### 2) 책처럼 길게 쓰되, ‘추정’을 섞지 않는다

길이를 늘리는 방식은 두 가지뿐이다.

- 이미 존재하는 사실을 더 구조화/설명/예시/FAQ/실전 절차로 확장
- 추상적인 원칙을 “현장 적용 절차”로 내려서 실용적으로 구체화

반대로 아래는 금지한다.

- 실행해 본 적 없는 출력/수치/성능을 단정
- 존재하지 않는 커맨드/옵션/파일/엔드포인트를 ‘있다’고 기술
- 특정 외부 서비스의 정책/가격/제약을 문서에 고정(변동 가능성이 큼)

---

## 문서 체계(핸드북이 포함할 것, 포함하지 않을 것)

### 핸드북이 포함할 것

- 핵심 개념을 “용어 정의 + 적용 예시 + 흔한 오해”로 정리
- 실행 루프를 “목표/절차/산출물/해석/다음 행동”으로 정리
- 운영과 품질을 “체크리스트/런북/실패 시 조치”로 정리

### 핸드북이 포함하지 않을 것

- 산출물(`reports/` 등) 개별 파일을 장황하게 인용(대부분은 실행의 결과물이며, 매번 달라질 수 있다)
- 내부 시크릿/민감 데이터/실제 고객 데이터

---

## 1주 온보딩 플랜(현실적인 학습 경로)

문서가 길어지면 오히려 학습이 어려워질 수 있다.
그래서 “첫 주에 무엇을 하면 실무 투입이 가능한지”를 시간 축으로 제공한다.

### Day 0: 환경/실행 성공(성공 기준 = run_id 하나 만들기)

목표:

- 로컬에서 `evalvault run`을 실행해 `run_id`를 얻는다.

체크리스트:

- [ ] `uv sync --extra dev`가 성공한다.
- [ ] `.env`를 만들고(커밋 금지), 선택한 프로필에 필요한 값이 채워져 있다.
- [ ] `data/db/evalvault.db`에 저장이 된다.

### Day 1: 분석 산출물까지(성공 기준 = index.json을 열어 근거 파일을 찾기)

목표:

- `--auto-analyze`로 분석 산출물을 만들고, `index.json`을 기준으로 근거 파일을 찾는다.

체크리스트:

- [ ] `reports/analysis/analysis_<RUN_ID>.md`를 읽고 “이번 실행의 문제 1~2개”를 말할 수 있다.
- [ ] `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`에서 근거 파일 경로를 찾을 수 있다.

### Day 2~3: 비교 실험(성공 기준 = 변경 전/후 run 비교)

목표:

- 동일 데이터셋/동일 조건으로 두 번 실행하고 비교한다.

주의:

- 조건이 바뀌면 “개선/회귀”가 아니라 “다른 실험”이다.

### Day 4~5: 운영 감각(성공 기준 = 실패 시 진단 루틴 수행)

목표:

- 실패 케이스를 일부러 만들고(예: 컨텍스트를 비우거나, 메트릭을 바꿔보거나), 진단 루틴을 수행해본다.

---

## 실전: EvalVault 루프를 ‘책 한 장’처럼 끝까지 돌려보기

이 섹션은 실제 팀에서 가장 자주 하는 작업(회귀 판단)을 하나의 흐름으로 묶는다.
핵심은 “명령을 나열”하는 것이 아니라 “의사결정이 가능해지는 지점”까지 안내하는 것이다.

### 시나리오: 변경이 개선인지 검증하기

전제:

- 데이터셋은 동일하다.
- 프로필/메트릭 구성은 동일하다.
- DB 경로는 동일하다.

절차:

1) 기준 실행(baseline) 생성
2) 변경 적용 후 실행(current) 생성
3) 비교로 변화 확인
4) (필요 시) 분석으로 원인 후보 좁히기

여기서 중요한 산출물:

- baseline/current 각각의 `run_id`
- 비교 결과(표 또는 JSON)
- 분석 아티팩트의 `index.json`(근거로 내려가는 출입구)

---

## 흔한 오해(초기 진입에서 가장 많이 막히는 지점)

### 오해 1: “점수 하나만 올리면 된다”

점수는 여러 축의 합성이다.
단일 점수만 올리면, 다른 축(예: 사실성/근거/검색)에서 문제가 생겨도 놓친다.

### 오해 2: “트레이싱이 없으면 못 쓴다”

트레이싱은 진단 속도를 올리지만 필수는 아니다.
기본적으로는 DB/리포트/아티팩트만으로도 충분히 많은 문제를 좁힐 수 있다.

### 오해 3: “UI가 진실이다”

UI는 편의와 탐색을 위한 뷰다.
재현의 기준은 `run_id`와 저장된 산출물이며, UI는 이를 보여주는 한 방식일 뿐이다.

---

## 용어집(초안)

문서가 길어질수록 용어의 일관성이 가장 중요해진다.
아래 용어는 핸드북 전체에서 동일한 의미로 쓴다.

- `run_id`: 평가 실행의 식별자. 비교/분석/저장의 키.
- `dataset`: 테스트 케이스 집합.
- `test case`: 데이터셋의 한 항목. 질문/답/컨텍스트(및 선택적으로 정답/메타데이터)를 포함.
- `metric`: 품질을 수치화하는 함수.
- `threshold`: 메트릭의 합격 기준.
- `artifact`: 분석의 근거 파일(원본 데이터). 사람이 읽는 리포트와 분리.
- `report`: 사람을 위한 요약 문서(보통 Markdown).
- `profile`: 런타임 구성(모델/임베딩/옵션)을 스위칭하는 설정.
- `stage`: 실행을 단계로 분해해 이벤트/메트릭을 남기는 관측 단위.

---

## FAQ(온보딩에서 실제로 나오는 질문들)

### Q1. 왜 DB 경로를 굳이 지정하나요?

CLI와 Web UI가 같은 DB를 바라봐야 결과가 연결된다.
또한 재현/비교는 항상 “같은 저장소에 저장된 실행”을 기반으로 하는 편이 안전하다.

### Q2. `contexts`가 비어 있어도 되나요?

가능은 하지만, 메트릭 해석이 바뀐다.
특히 근거 기반 메트릭은 컨텍스트가 빈 경우 의미가 약해지거나 실패/왜곡될 수 있다.

### Q3. 분석이 왜 필요한가요? 점수만 보면 안 되나요?

점수는 결과이고, 분석은 원인을 좁히는 과정이다.
운영에서 중요한 것은 “다음 액션”이며, 분석은 그 액션을 결정할 근거를 제공한다.

---

## Part 2. 시스템을 “한 장”으로 이해하기(지도)

이 파트는 00장에서 가장 중요하다.
EvalVault를 구성하는 요소를 “기술 스택”이 아니라 “흐름”으로 묶어준다.

### 2.1 두 개의 평면: Data plane vs Control plane

EvalVault는 크게 두 평면을 가진다.

- Data plane: 평가 입력/결과/근거를 저장하는 영역
- Control plane: 평가를 실행하고, 분석하고, 비교하고, 자동화하는 영역

#### Data plane(무엇이 저장되는가)

저장 대상의 기본 단위는 `EvaluationRun`이고 키는 `run_id`다.

- 근거(엔티티): `src/evalvault/domain/entities/result.py#EvaluationRun`
  - `run_id`는 UUID로 생성된다: `src/evalvault/domain/entities/result.py` (`run_id: str = field(default_factory=lambda: str(uuid4()))`)
- 저장소(기본): PostgreSQL + pgvector (RDB + Vector 통합)
- Postgres 설정: `src/evalvault/config/settings.py#Settings.postgres_*`
- 벡터 검색은 pgvector를 사용하며 별도 벡터 DB는 사용하지 않는다
- 저장소(보조): 보고서/아티팩트 디렉터리
  - 분석 기본 디렉터리: `reports/analysis` (출력 경로 resolver의 기본값)
    - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#resolve_output_paths`

#### Control plane(무엇이 실행을 통제하는가)

Control plane의 핵심은 Typer CLI와 FastAPI API다.

- CLI entrypoint: `pyproject.toml#project.scripts` (`evalvault = "evalvault.adapters.inbound.cli:app"`)
- API 서버 실행: `src/evalvault/adapters/inbound/cli/commands/api.py` (`evalvault serve-api`)
- Web UI는 API를 통해 DB를 조회한다.
  - 근거(API의 auth/cors/rate limit 포함): `src/evalvault/adapters/inbound/api/main.py`

---

### 2.2 “정답(SSoT)”의 우선순위(실무 버전)

핸드북/가이드가 길어질수록 문서 드리프트가 생긴다.
EvalVault는 문서 자체가 이를 인정하고, 정답 우선순위를 정해둔다.

권장 우선순위(운영 기준):

1) CLI 구현(옵션/기본값/exit code)
   - 예: `src/evalvault/adapters/inbound/cli/commands/run.py`, `compare.py`, `gate.py`, `regress.py`
2) API 구현(인증/레이트리밋/CORS/경로 제약)
   - 예: `src/evalvault/adapters/inbound/api/main.py`, `src/evalvault/adapters/inbound/api/routers/mcp.py`
3) Settings(환경변수/프로필/비밀 참조/production 검증)
   - 예: `src/evalvault/config/settings.py`
4) docs/guides(사용법/운영)
   - 문서 허브: `docs/INDEX.md`
5) handbook(교과서형)

근거:

- docs 운영 원칙: `docs/INDEX.md` ("코드/테스트/CLI 도움말이 최우선")
- prod profile 검증이 코드로 강제됨: `src/evalvault/config/settings.py#_validate_production_settings`

---

### 2.3 산출물의 “정규 형태”(팀이 공유할 때 표준)

EvalVault의 결과는 크게 3층으로 구분한다.

1) DB(재현/조회)
2) 보고서(사람용)
3) 아티팩트(근거용)

#### 2.3.1 보고서/아티팩트 기본 경로

자동 분석(`--auto-analyze`) 기준으로, prefix 규칙은 아래처럼 고정된다.

- 분석 prefix: `analysis_<RUN_ID>`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py` (auto-analyze에서 `analysis_prefix = f"analysis_{result.run_id}"`)
- 기본 보고서/JSON 경로:
  - `reports/analysis/analysis_<RUN_ID>.md`
  - `reports/analysis/analysis_<RUN_ID>.json`
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#resolve_output_paths`
- 아티팩트 디렉터리:
  - `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#resolve_artifact_dir`

아티팩트는 항상 `index.json`을 엔트리로 갖는다.

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`

실무 규칙(권장):

- Slack/이슈/PR에 `run_id`만 남기지 말고, 최소한 아래 두 경로를 같이 남겨라.
  - `reports/analysis/analysis_<RUN_ID>.md`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

---

### 2.4 최소 성공 루프(“정말로 성공했는지”를 정의)

EvalVault 온보딩에서 중요한 건 “실행했다”가 아니라 “루프가 닫혔다”다.

#### 최소 성공 정의

다음이 모두 되면 “기본 루프 성공”이다.

1) `evalvault run`으로 `run_id`가 생성된다.
2) DB에 저장되어 `evalvault history`에서 다시 조회된다.
3) 자동 분석 또는 수동 분석으로 보고서/아티팩트가 생성된다.
4) 같은 조건으로 한 번 더 실행하고 `compare` 또는 `analyze-compare`가 동작한다.

근거:

- history는 DB에서 run 목록을 조회한다: `src/evalvault/adapters/inbound/cli/commands/history.py`
- compare/analyze-compare는 DB의 두 run을 로드해 비교한다:
  - `src/evalvault/adapters/inbound/cli/commands/compare.py`
  - `src/evalvault/adapters/inbound/cli/commands/analyze.py#analyze_compare`

---

## Part 3. 운영/보안/품질이 만나는 지점(“실무에서 터지는 곳”)

00장은 개념서지만, 운영/보안/품질은 분리할 수 없다.
이 파트는 “어디서 사고가 나는지”를 미리 연결해 둔다.

### 3.1 운영: DB 경로가 흔들리면 모든 것이 흔들린다

DB는 단순 저장소가 아니라 “연결 키”다.

- CLI가 DB에 저장한 run을 API/Web UI도 같은 DB에서 봐야 한다.
- Settings는 기본 DB 경로를 가진다.

근거:

- 기본 DB 경로: `src/evalvault/config/settings.py#Settings.evalvault_db_path`
- API 라우터는 `Settings()`에서 DB 경로를 사용한다(예: MCP 도구): `src/evalvault/adapters/inbound/mcp/tools.py#_resolve_db_path`

### 3.2 보안: prod profile은 “안전하지 않은 설정”을 거부한다

prod profile은 빠르게 실패하도록 설계돼 있다.

- API 토큰이 없으면 prod에서 필수 설정 누락으로 간주될 수 있다.
- prod에서는 CORS 오리진에 localhost를 허용하지 않는다.

근거:

- prod required 설정 검증: `src/evalvault/config/settings.py#_validate_production_settings`

### 3.3 보안: API 인증과 rate limit은 “옵션이지만, 켜면 강제된다”

API 인증은 `API_AUTH_TOKENS`가 비어 있으면 비활성화된다.

- 토큰이 설정된 경우, Bearer 토큰이 없거나 불일치하면 401
  - 근거: `src/evalvault/adapters/inbound/api/main.py#require_api_token`

rate limit은 `RATE_LIMIT_ENABLED`가 true일 때만 `/api/` 경로에 적용된다.

- 근거: `src/evalvault/adapters/inbound/api/main.py#rate_limit_middleware`

### 3.4 보안: secret:// 참조는 “설정 로딩 단계에서” 해석된다

Settings는 특정 필드에서 `secret://...`를 감지하면 secret provider로 값을 해석한다.

- 지원 provider: env/aws/gcp/vault
- secret cache 옵션 존재

근거:

- `src/evalvault/config/settings.py#SECRET_REFERENCE_FIELDS`
- `src/evalvault/config/secret_manager.py`

### 3.5 품질: CI는 “API 키가 없는 상태”를 기본으로 테스트한다

CI는 기본 테스트에서 `requires_openai`/`requires_langfuse` 마커를 제외한다.

- 근거: `.github/workflows/ci.yml` (`-m "not requires_openai and not requires_langfuse"`)
- 마커 정의: `pyproject.toml#[tool.pytest.ini_options].markers`

---

## Part 4. “어디를 먼저 읽어야 하는가”를 더 현실적으로

00장의 추천 읽기 순서는 챕터 중심이었다.
하지만 실무에서는 문제 유형이 먼저다.

### 4.1 상황별 추천 진입점

#### (A) 실행이 안 된다(환경/설정)

- `docs/handbook/CHAPTERS/04_operations.md` (환경/DB/런북)
- `src/evalvault/config/settings.py` (Settings/프로필/필수값)
- `docs/handbook/CHAPTERS/04_operations.md` (런북)

#### (B) 점수가 흔들린다(재현성)

- `docs/handbook/CHAPTERS/03_workflows.md` (조건 고정/비교/exit code)
- `src/evalvault/adapters/inbound/cli/commands/run.py` (mode/preset/metrics 강제 규칙)

#### (C) UI에서 안 보인다(API/DB)

- `src/evalvault/adapters/inbound/api/main.py` (auth/cors)
- `docs/handbook/CHAPTERS/04_operations.md` (로컬 API+frontend)

#### (D) 민감 데이터가 걱정된다(보안)

- `docs/handbook/CHAPTERS/05_security.md`
- `src/evalvault/config/settings.py` (prod validation, secret provider)
- `src/evalvault/adapters/inbound/mcp/tools.py` (허용 경로 제한)

---

## Part 5. 부록: “핵심 파일만” 빠르게 찾기

### 5.1 CLI 진실(명령 구현)

- run: `src/evalvault/adapters/inbound/cli/commands/run.py`
- analyze/analyze-compare: `src/evalvault/adapters/inbound/cli/commands/analyze.py`
- compare: `src/evalvault/adapters/inbound/cli/commands/compare.py`
- gate: `src/evalvault/adapters/inbound/cli/commands/gate.py`
- regress/ci-gate/regress-baseline: `src/evalvault/adapters/inbound/cli/commands/regress.py`
- stage: `src/evalvault/adapters/inbound/cli/commands/stage.py`
- prompts: `src/evalvault/adapters/inbound/cli/commands/prompts.py`
- ops snapshot: `src/evalvault/adapters/inbound/cli/commands/ops.py`

### 5.2 API 진실(auth/cors/rate limit)

- API entry: `src/evalvault/adapters/inbound/api/main.py`

### 5.3 Settings/프로필/시크릿

- Settings: `src/evalvault/config/settings.py`
- 프로필 파일: `config/models.yaml`
- secret provider: `src/evalvault/config/secret_manager.py`

### 5.4 문서 허브(최신화 기준)

- docs 인덱스: `docs/INDEX.md`
- 상태/로드맵(SSoT): `docs/handbook/CHAPTERS/00_overview.md`, `docs/handbook/CHAPTERS/08_roadmap.md`

---

## Part 6. Run을 “데이터 모델”로 이해하기(핵심 엔티티 해부)

00장은 개념서이지만, 실무에서 헷갈리는 대부분은 엔티티 필드의 의미에서 나온다.
이 파트는 코드 정의를 그대로 따라가며, 해석 포인트만 추가한다.

### 6.1 EvaluationRun: 저장/조회/비교의 기준점

`EvaluationRun`은 EvalVault의 최상위 결과 엔티티다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun`

핵심 필드(요약):

- `run_id`: 실행 식별자(UUID 문자열)
- `dataset_name`, `dataset_version`: 어떤 데이터셋에서 나왔는지
- `model_name`: 어떤 모델로 실행했는지
- `started_at`, `finished_at`: 실행 시간
- `results`: 테스트 케이스 결과 리스트
- `metrics_evaluated`: 평가한 메트릭 목록
- `thresholds`: 메트릭별 임계값(최종 적용값)
- `tracker_metadata`: 트래커/스냅샷/부가 메타데이터(프롬프트, 커스텀 메트릭 스냅샷 등)
- `retrieval_metadata`: 리트리버 관련 메타데이터(있을 때)

근거:

- 필드 정의: `src/evalvault/domain/entities/result.py#EvaluationRun`

### 6.2 pass_rate vs metric_pass_rate: 가장 흔한 해석 실수

EvalVault에는 “통과율”이 2종류가 있다.

#### 6.2.1 pass_rate(테스트 케이스 통과율)

`pass_rate`는 “모든 메트릭을 통과한 테스트 케이스의 비율”이다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.pass_rate`

실무 해석:

- 실패한 케이스가 어떤 케이스인지(특정 태그/질문 유형/컨텍스트 품질)로 내려가서 원인을 찾는 지표다.

#### 6.2.2 metric_pass_rate(메트릭 기준 통과율)

`metric_pass_rate`는 “메트릭 평균 점수가 임계값을 넘는 메트릭의 비율”이다.

- 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.metric_pass_rate`

실무 해석:

- ‘메트릭 세트’의 건강도를 보는 지표다.
- 예: 특정 메트릭 하나가 지속적으로 임계값 아래면, 메트릭 정의/프롬프트/입력 데이터가 문제일 수 있다.

### 6.3 thresholds: 최종 적용값을 어디서 신뢰할 것인가

실험에서 가장 위험한 건 “사실 threshold가 바뀌었는데 모르고 비교하는 것”이다.

- `EvaluationRun.thresholds`는 최종 적용 임계값의 스냅샷이다.
  - 근거: `src/evalvault/domain/entities/result.py#EvaluationRun.thresholds`

실무 규칙(권장):

- A/B 비교에서 “thresholds가 동일”하지 않으면, 개선/회귀 결론을 내리기 전에 조건부터 정렬하라.
- 최소한 `evalvault export` 결과(JSON)에서 thresholds를 같이 공유하라.
  - 근거(export가 thresholds 포함): `src/evalvault/adapters/inbound/cli/commands/history.py#export_cmd` (run.to_summary_dict + results 포함)

---

## Part 7. 프로필/설정/시크릿의 분리(운영 현실)

EvalVault 운영에서 가장 중요한 “설정 규칙”은 한 문장으로 요약된다.

- 모델/프로필은 버전 관리되고, 시크릿/인프라는 환경변수로 주입된다.

### 7.1 Settings의 역할: 환경변수 → 런타임 설정

Settings는 `.env`를 읽고(기본), profile을 적용하고, prod에서 필수 값을 검증한다.

- 근거: `src/evalvault/config/settings.py#Settings`, `src/evalvault/config/settings.py#get_settings`

### 7.2 .env.example는 “운영 계약서”다

`.env.example`는 단순 예시가 아니라, 설정 항목을 어떤 의도로 분리했는지를 보여준다.

- 근거: `.env.example` (프로필/LLM/secret manager/API auth/CORS/rate limit 분리 설명)

### 7.3 config/models.yaml는 “모델 프로필의 SSoT”다

Settings의 `apply_profile()`은 `config/models.yaml`에서 모델명만 읽고, 인프라 설정은 `.env`를 유지한다.

- 근거: `src/evalvault/config/settings.py#apply_profile`
- 프로필 파일: `config/models.yaml`

### 7.4 prod profile 검증(강제 실패)

prod에서는 다음이 누락되면 에러로 실패할 수 있다.

- `API_AUTH_TOKENS`가 비어 있음
- `CORS_ORIGINS`가 비어 있음
- `CORS_ORIGINS`에 localhost가 포함됨(금지)

근거:

- `src/evalvault/config/settings.py#_validate_production_settings`

주의:

- 이 정책은 “기본 안전”을 위한 강제다.
- prod profile을 쓰면 운영자가 “명시적으로” API 인증과 CORS 정책을 결정해야 한다.

---

## Part 8. API/Web UI: 보안/운영을 포함한 실행 모델

### 8.1 API 서버는 FastAPI이며, auth/cors/rate limit를 포함한다

API 서버의 진실은 `create_app()`에 있다.

- 근거: `src/evalvault/adapters/inbound/api/main.py#create_app`

핵심 구성:

- 인증(선택): `API_AUTH_TOKENS`가 설정되면 모든 `/api/v1/*` 라우터에 Bearer 인증 적용
  - 근거: `src/evalvault/adapters/inbound/api/main.py#require_api_token` + `app.include_router(... dependencies=auth_dependencies)`
- 레이트 리밋(선택): `RATE_LIMIT_ENABLED`가 true일 때 `/api/` 경로에만 적용
  - 근거: `src/evalvault/adapters/inbound/api/main.py#rate_limit_middleware`
- CORS: `CORS_ORIGINS` 기반
  - 근거: `src/evalvault/adapters/inbound/api/main.py` (CORS middleware 설정)

### 8.2 Web UI는 “별도의 제품”이고, API를 통해 DB를 조회한다

핵심 원칙:

- UI는 CLI의 모든 플래그를 1:1로 노출하지 않는다.

근거:

- UI↔CLI 역할 분담(구현 근거: UI가 CLI 커맨드를 생성/복사하는 탈출구 제공): `frontend/src/utils/cliCommandBuilder.ts`

개발 환경 실행(기본):

```bash
uv run evalvault serve-api --reload
cd frontend && npm install && npm run dev
```

근거:

- `README.md`
- `docs/handbook/CHAPTERS/04_operations.md`
- `src/evalvault/adapters/inbound/cli/commands/api.py` (serve-api 기본 host/port/reload)

### 8.3 CORS에서 가장 흔한 운영 실수

증상:

- UI에서 API 호출이 막히거나(브라우저 CORS 에러), UI가 데이터를 못 불러온다.

원인 후보:

- `CORS_ORIGINS`가 UI 오리진을 포함하지 않음
- prod profile에서 localhost 오리진을 넣어 에러

근거:

- prod 검증에서 localhost 금지: `src/evalvault/config/settings.py#_validate_production_settings`
- API에서 CORS 오리진이 비면 prod에서는 RuntimeError: `src/evalvault/adapters/inbound/api/main.py`

---

## Part 9. MCP/Tooling: 안전한 파일 접근을 강제하는 이유

EvalVault는 MCP(JSON-RPC over HTTP) 엔드포인트를 제공할 수 있다.
이 엔드포인트는 “도구가 임의 경로를 읽어버리는” 사고를 막기 위해, 허용 경로를 강제한다.

### 9.1 MCP 인증

- MCP는 `mcp_enabled`가 false면 404
- MCP는 `mcp_auth_tokens`(없으면 api_auth_tokens) 기반의 Bearer 인증이 필요

근거:

- `src/evalvault/adapters/inbound/api/routers/mcp.py#_require_mcp_token`
- Settings: `src/evalvault/config/settings.py#Settings.mcp_enabled`, `Settings.mcp_auth_tokens`

### 9.2 MCP 도구는 허용 경로(data/tests/fixtures/reports) 밖을 접근하지 못한다

MCP tool 구현은 파일 접근 경로를 제한한다.

- 허용 루트: `data/`, `tests/fixtures/`, `reports/`
- 그 밖 경로는 에러

근거:

- `src/evalvault/adapters/inbound/mcp/tools.py#_ensure_allowed_path`, `src/evalvault/adapters/inbound/mcp/tools.py#_allowed_roots`

실무 포인트:

- 운영에서 “도구가 안전하게 움직인다”는 건 기능이 아니라 보안 요구사항이다.

---

## Part 10. 오프라인(폐쇄망) 운영: 무엇이 포함되고 무엇이 외부 의존인가

오프라인 운영은 운영/보안이 동시에 어려워지는 영역이다.
EvalVault는 이를 위한 compose와 가이드를 별도로 제공한다.

### 10.1 오프라인 Docker 가이드

- 문서: `docs/guides/OFFLINE_DOCKER.md`

핵심 전제(문서 기준):

- 모델 가중치는 포함하지 않으며, EvalVault는 외부 모델 서버(Ollama/vLLM)를 호출

근거:

- `docs/guides/OFFLINE_DOCKER.md`

### 10.2 docker-compose.offline.yml

구성(코드 기준):

- `evalvault-api`: FastAPI backend, `serve-api --host 0.0.0.0 --port 8000`
- `evalvault-web`: nginx + React 정적 서빙, `127.0.0.1:5173:80` 포트 매핑
- (선택) `postgres`: PostgreSQL

근거:

- `docker-compose.offline.yml`

주의:

- `docker-compose.offline.yml`의 CORS 기본값은 `http://localhost:5173,http://127.0.0.1:5173`
  - 근거: `docker-compose.offline.yml` (`CORS_ORIGINS` env)
- OFFLINE_DOCKER 문서의 예시 CORS 기본값은 `http://localhost:8080`처럼 “배포 UI 포트”를 기준으로 설명한다.
  - 근거: `docs/guides/OFFLINE_DOCKER.md`
  - 결론: 실제 배포 포트(8080/5173 등)에 맞춰 CORS를 명시적으로 정해야 한다.

### 10.3 데이터 포함 정책(볼륨 마운트 주의)

오프라인 가이드는 `data/`가 이미지에 포함되지만, 볼륨 마운트 시 이미지 데이터를 가릴 수 있음을 명시한다.

- 근거: `docs/guides/OFFLINE_DOCKER.md` ("/app/data를 볼륨으로 마운트하면 이미지 데이터가 가려짐")

---

## Part 11. CI/릴리즈: 문서가 따라가야 하는 자동화들

### 11.1 CI는 무엇을 검사하는가

CI 워크플로는 크게 3가지 축을 가진다.

- 테스트(여러 OS/Python)
- 린트/포맷 + docs build/link check
- 회귀 게이트

근거:

- `.github/workflows/ci.yml`

### 11.2 CI의 기본 테스트는 “API 키 없이” 돌도록 설계된다

- 기본 test job은 `requires_openai`, `requires_langfuse` 마커를 제외하고 실행한다.

근거:

- `.github/workflows/ci.yml` (pytest `-m "not requires_openai and not requires_langfuse"`)
- 마커 정의: `pyproject.toml#[tool.pytest.ini_options].markers`

### 11.3 회귀 게이트는 별도 워크플로로도 운영된다

회귀 게이트 워크플로는 baseline DB artifact를 저장하고, PR에서 받아서 ci-gate 결과를 PR 코멘트로 남긴다.

근거:

- `.github/workflows/regression-gate.yml`

### 11.4 회귀 스위트 러너(스크립트)

`scripts/ci/run_regression_gate.py`는 config 기반으로 회귀 스위트를 돌리고, github-actions 형식 출력도 지원한다.

근거:

- `scripts/ci/run_regression_gate.py`

---

## Part 12. 보안: “지나치게 말하지 않는” 문서가 강하다

핸드북은 보안을 설명해야 하지만, 보안 정책을 ‘문장으로 고정’하면 오히려 위험해질 수 있다.
따라서 00장에서는 “코드에 있는 정책”만 짚고, 상세 정책은 05장에서 운영 규약으로 다룬다.

### 12.1 로그/트레이스의 PII 마스킹(내장)

tracker adapter들은 payload를 그대로 보내지 않고 sanitize를 적용한다.

- 마스킹 대상(정규식): email/phone/SSN/card
- 길이 제한: max chars, 리스트 항목 제한, 중첩 깊이 제한

근거:

- `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`
- 사용처 예: `src/evalvault/adapters/outbound/tracker/langfuse_adapter.py`, `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`

### 12.2 secret:// 값 해석은 provider를 명시해야 한다

- `SECRET_PROVIDER`가 없으면 provider 구성 자체가 실패한다.

근거:

- provider 미설정 에러: `src/evalvault/config/secret_manager.py#build_secret_provider`
- Settings 해석: `src/evalvault/config/settings.py#Settings._resolve_secret_references`

---

## Part 13. 업데이트 가이드(문서 드리프트 방지)

핸드북이 길어질수록, “언제 무엇을 고쳐야 하는지”를 정의하지 않으면 결국 거짓말이 된다.

### 13.1 문서가 반드시 따라가야 하는 변경

아래 변화가 생기면 handbook의 해당 챕터를 업데이트해야 한다.

1) CLI 옵션/기본값/exit code 변경
   - 근거 파일: `src/evalvault/adapters/inbound/cli/commands/*.py`
2) Settings의 필드/프로필 검증 변경
   - 근거 파일: `src/evalvault/config/settings.py`
3) 산출물 경로 규약 변경
   - 근거 파일: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
4) API auth/cors/rate limit 정책 변경
   - 근거 파일: `src/evalvault/adapters/inbound/api/main.py`
5) CI 워크플로(테스트/회귀) 변경
   - 근거 파일: `.github/workflows/*.yml`, `scripts/ci/run_regression_gate.py`

### 13.2 핸드북의 안전장치(권장)

- 문서에는 “사실 주장”마다 파일 경로를 남긴다.
- 외부 서비스(가격/정책/제약)는 링크만 남기고 문장으로 고정하지 않는다.
- prod 보안 정책은 코드에 있는 강제 규칙만 확정적으로 말한다.

근거:

- docs 운영 원칙: `docs/INDEX.md`
