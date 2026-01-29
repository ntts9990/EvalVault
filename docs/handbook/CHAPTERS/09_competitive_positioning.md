# 09. Competitive Positioning (경쟁 비교: 사용자 효용 기준)

이 챕터는 “EvalVault가 무엇이냐”를 기능 목록이 아니라 **사용자 효용(JTBD)** 관점에서 설명한다.
비교 대상은 크게 3부류다.

- Observability-first: 트레이싱/로그 중심(예: Langfuse, LangSmith, Phoenix, Helicone)
- Eval-first: 평가 프레임워크/메트릭 라이브러리 중심(예: RAGAS, DeepEval, TruLens, OpenAI Evals, lm-eval-harness)
- CI-first: PR/릴리즈 게이팅 중심(예: Promptfoo)

중요한 규칙:

- 외부 서비스의 가격/정책/제약은 문장으로 고정하지 않고, **링크만 남긴다**(변동 가능성이 큼).
- “사용자가 느낀다/말한다” 같은 주장은 공식 문서/가이드/릴리즈 노트 등 **근거가 있을 때만** 적는다.

---

## TL;DR

- Observability 툴은 “왜 이런 결과가 나왔는지”를 **트레이스와 세션/스팬**으로 좁히는 데 강하다.
- Eval 프레임워크는 “어떤 지표로 얼마나 좋아졌나”를 **메트릭 실행/벤치마크**로 정리하는 데 강하다.
- CI-first 툴은 “회귀를 PR에서 자동으로 막는다”에 특화되어 **팀 운영 비용**을 줄인다.
- EvalVault는 (1) `run_id` + DB로 실행 결과를 단일 키로 묶고 (2) artifacts-first로 근거를 보존하며 (3) 회귀 게이트를 코드/워크플로로 내장해 **평가→분석→추적→개선 루프를 닫는 것**을 목표로 한다.

---

## 0) EvalVault의 전제(우리가 고집하는 운영 단위)

### 0.1 단일 키: `run_id`

EvalVault의 UX/저장/재현의 단일 중심축은 `run_id`다.

- 엔티티(저장의 기준점): `src/evalvault/domain/entities/result.py#EvaluationRun`
- 기본 DB 경로(로컬): `src/evalvault/config/settings.py#Settings.evalvault_db_path`

### 0.2 저장의 기본값: DB + artifacts

사람용 요약(보고서)과 기계용 근거(JSON)를 분리하고, 근거는 `index.json`으로 검색 가능하게 만든다.

- 아티팩트 인덱스 생성: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`
- 아티팩트 기본 엔트리: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

### 0.3 “옵션화”된 관측성

Phoenix/Langfuse/MLflow는 필요할 때만 켜는 통합이다.

- 운영 원칙(옵션화 기준): `docs/handbook/CHAPTERS/04_operations.md`
- 트래커 어댑터: `src/evalvault/adapters/outbound/tracker/__init__.py`
- Phoenix/OpenTelemetry/OpenInference 스펙: `docs/architecture/open-rag-trace-spec.md`

---

## 1) 사용자 JTBD (Jobs To Be Done)

이 챕터는 아래 질문을 “도구 선택 기준”으로 쓴다.

1) PR/릴리즈에서 회귀를 자동으로 막고 싶은가?
2) 점수 변화가 났을 때, 원인을 30분 내 1~2개 후보로 좁히고 싶은가?
3) 결과를 팀이 공유/재현 가능한 형태로 저장하고 싶은가?
4) 지표 자체(정의/프롬프트/판정)가 흔들려서 KPI로 못 쓰는가?
5) 온프레미스/폐쇄망에서 평가/분석을 돌려야 하는가?
6) 단일 점수보다 “근거가 남는” 분석과 리포팅이 중요한가?
7) Web UI에서 빠르게 탐색하고, 필요하면 CLI로 정밀 제어/자동화하고 싶은가?

EvalVault는 1~3, 6~7을 “기본 루프”로, 4~5를 “운영 요구”로 취급한다.

---

## 2) 경쟁 카테고리별 ‘사용자 효용’과 트레이드오프

아래는 “어느 도구가 더 좋다”가 아니라 “어느 문제를 풀기 쉽다”를 정리한 것이다.

### 2.1 Observability-first (Langfuse / LangSmith / Phoenix / Helicone)

사용자가 보통 체감하는 효용:

- 요청 단위로 입력/출력/컨텍스트/메타데이터를 따라가며 **디버깅 속도**가 빨라진다.
- 비용/지연/에러 등 운영 지표를 한 화면에서 보고, “어디서 느려졌나/깨졌나”를 좁힌다.
- 프롬프트 버전/실험/세션을 관리하며 재현/리뷰가 쉬워진다(툴별 범위 상이).

대표 트레이드오프(일반형):

- “평가 기준(메트릭/threshold)과 게이트(통과/실패)”를 팀 규약으로 고정하는 문제는 별도 설계가 필요하다.
- 저장/재현의 SSoT가 트레이스/세션 쪽으로 기울면, “데이터셋 기반 회귀” 관점이 약해질 수 있다.

공식 문서(링크는 외부 변동 가능):

- Langfuse: https://langfuse.com/docs
- LangSmith: https://docs.smith.langchain.com/
- Arize Phoenix: https://docs.arize.com/phoenix
- Helicone: https://docs.helicone.ai

### 2.2 Eval-first (RAGAS / DeepEval / TruLens / OpenAI Evals / lm-eval-harness)

사용자가 보통 체감하는 효용:

- 메트릭/벤치마크 실행이 표준화되어 “어떤 지표로 좋아졌나”를 빠르게 계산한다.
- 평가 파이프라인이 코드/테스트(예: pytest)로 들어가면 PR에서 반복 실행이 쉬워진다.
- 프롬프트 오버라이드/LLM-as-judge 등을 포함해 “지표 설계 공간”을 빠르게 탐색할 수 있다(프레임워크별 차이).

대표 트레이드오프(일반형):

- 점수 변동(LLM 기반 판정/임베딩 기반 유사도)은 운영에서 해석이 어렵고, “진짜 사용자 만족”과 괴리가 날 수 있다.
  - 관련 내부 논의/완화 루프(인간 피드백 보정): `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`

공식 문서(링크는 외부 변동 가능):

- RAGAS: https://docs.ragas.io
- DeepEval (Confident AI): https://docs.confident-ai.com
- TruLens: https://www.trulens.org
- OpenAI Evals: https://platform.openai.com/docs/guides/evals , https://github.com/openai/evals
- lm-eval-harness: https://github.com/EleutherAI/lm-evaluation-harness

### 2.3 CI-first (Promptfoo 등)

사용자가 보통 체감하는 효용:

- PR에서 “이 변경이 위험하다”를 자동으로 표시/차단하는 게 쉬워진다.
- 테스트 케이스/프롬프트/기대값을 버전 관리하며, 리뷰가 코드 리뷰처럼 된다.

대표 트레이드오프(일반형):

- 게이트가 강해질수록 “왜 실패했는지” 근거를 함께 제공하지 않으면 운영 반발이 생긴다.

공식 문서(링크는 외부 변동 가능):

- Promptfoo CI/CD: https://www.promptfoo.dev/docs/integrations/ci-cd/
- Promptfoo GitHub Actions: https://www.promptfoo.dev/docs/integrations/github-action/

---

## 3) EvalVault의 차별점(‘느끼는 효용’으로 매핑)

### 3.1 PR에서 회귀를 막는 “내장된” 루트

EvalVault는 회귀 게이트를 별도 아이디어가 아니라, 워크플로/서비스/CLI로 연결된 경로로 갖는다.

- GitHub Actions: `.github/workflows/regression-gate.yml`
- 회귀 판단 로직: `src/evalvault/domain/services/regression_gate_service.py`
- CI 통합 커맨드: `src/evalvault/adapters/inbound/cli/commands/regress.py`

사용자 효용:

- “사람이 매번 판단”하지 않아도 PR에서 자동으로 회귀를 드러낸다.
- 실패 시 근거(요약/표/아티팩트)로 내려가면 원인 파악이 빨라진다.

주의:

- “병합 자동 차단”은 GitHub 브랜치 보호(required checks)까지 포함해야 완성된다.
  - 근거/주의 문서화: `docs/handbook/CHAPTERS/08_roadmap.md`

### 3.2 artifacts-first: 점수보다 근거를 남기는 설계

사용자 효용:

- 회귀가 났을 때 “어떤 케이스/어떤 근거 파일”로 내려갈 수 있다.
- 리포트(MD)와 근거(JSON)가 분리되어, 비개발자 공유와 개발자 디버깅이 같이 가능하다.

근거:

- 출력 경로/인덱스: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

### 3.3 UI는 탐색, CLI는 정밀 제어: 안전한 탈출구

Web UI가 CLI의 모든 옵션을 1:1로 노출하지 않는다는 전제를 인정하고, UI→CLI로 “조건을 복제”하는 경로를 제공한다.

- CLI 커맨드 빌더: `frontend/src/utils/cliCommandBuilder.ts`
- 클립보드 유틸: `frontend/src/utils/clipboard.ts`
- 관련 UX 원칙: `docs/handbook/CHAPTERS/07_ux_and_product.md`

사용자 효용:

- UI로 조건을 잡고, 고급 옵션/자동화는 CLI로 이어서 할 수 있다.
- 재현/공유는 run_id + 명령어(또는 DB 경로)로 수렴한다.

### 3.4 표준 트레이스(OpenTelemetry/OpenInference)로 “도구 갈아타기 비용” 최소화

사용자 효용:

- 트레이싱/관측성은 특정 벤더의 SDK에 잠기지 않고, 표준 포맷으로 연결된다.

근거:

- 스펙: `docs/architecture/open-rag-trace-spec.md`
- Collector 가이드: `docs/architecture/open-rag-trace-collector.md`

### 3.5 오프라인/폐쇄망 운영: 기본 루프를 유지한 채로

사용자 효용:

- 내부망에서 평가/분석을 돌리는 요구(보안/규정)를 만족하면서도, run_id/DB/artifacts 기반 워크플로를 유지한다.

근거:

- 오프라인 가이드: `docs/guides/OFFLINE_DOCKER.md`
- compose: `docker-compose.offline.yml`

---

## 4) 어떤 상황에서 무엇을 선택할까(실무 기준)

아래는 “대체재”라기보다 “조합” 관점이다.

- 먼저 Eval-first로 메트릭/벤치마크를 정의하고(정의가 없으면 아무것도 자동화할 수 없다)
- CI-first 또는 EvalVault의 회귀 게이트로 PR에서 자동 차단하고
- Observability-first(또는 Phoenix+OTel)로 실패 원인을 트레이스 레벨로 좁힌다

EvalVault는 이 조합에서 “run_id + DB + artifacts + gate”로 실행 데이터를 묶어,
도구가 늘어도 팀이 공유하는 기준점을 유지하는 역할을 한다.

---

## 5) 업데이트 가이드(문서 드리프트 방지)

이 챕터는 “외부 도구의 기능”이 아니라 “EvalVault의 포지션”을 설명한다.
따라서 아래가 바뀌면 이 챕터도 업데이트해야 한다.

- 회귀 게이트 워크플로/커맨드 변경: `.github/workflows/regression-gate.yml`, `src/evalvault/adapters/inbound/cli/commands/regress.py`
- artifacts/index 규약 변경: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- Open RAG Trace 스펙 변경: `docs/architecture/open-rag-trace-spec.md`
- Web UI의 UI→CLI 탈출구 변경: `frontend/src/utils/cliCommandBuilder.ts`, `frontend/src/utils/clipboard.ts`

---

## 6) 남아있는 문서/UX 정리 메모

- `reports/README.md`에서 `../docs/STRUCTURE_REVIEW.md` 링크가 깨져 있을 가능성이 높다(파일 부재).
- `docs/handbook/appendix-file-inventory.md`는 전수 인벤토리 성격이라, 본문 링크 수정 시점과 불일치(스냅샷 드리프트)가 생길 수 있다.
