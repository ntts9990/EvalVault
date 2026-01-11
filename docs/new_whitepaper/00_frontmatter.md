# EvalVault 개발 백서

> **문서 트랙**: `docs/new_whitepaper/`
>
> **대상**: 내부 개발자
>
> **목적**: EvalVault의 코드/설계/운영을 **재현 가능**하고 **근거 기반**으로 설명한다.

---

## 0. 문서 사용법

- 처음 읽는 경우: [`INDEX.md`](INDEX.md) 순서대로 읽는다.
- 특정 주제를 찾는 경우: 각 장의 TL;DR → “사용자 관점 플로우” → “Evidence” 순으로 본다.
- PDF 변환: Markdown 그대로 작성한 뒤 Bear/Notion 등 전문 렌더러에서 내보낸다.

> **NOTE**: Mermaid 다이어그램은 렌더러에 따라 미지원일 수 있다. 각 장은 다이어그램 없이도 이해 가능한 텍스트 설명을 포함한다.

---

## 1. 이 백서가 답하려는 질문

- EvalVault의 **핵심 사용자 워크플로**(실행→저장→분석→비교)는 무엇인가?
- 시스템은 왜 **Hexagonal Architecture (Ports & Adapters)** 구조인가?
- 평가(Evaluation)·관측(Observability)·표준 연동(Open RAG Trace)·학습(Domain Memory)·분석(Analysis Pipeline)이 어떻게 연결되는가?
- 새로운 기능을 추가할 때 **어디를 고쳐야 안전한가** (확장 지점/경계는 어디인가)?

---

## 2. 독자 수준 정의

- **초급**: EvalVault를 처음 만지는 내부 개발자(온보딩)
- **중급**: 기능/메트릭/어댑터 추가를 하는 개발자
- **고급**: 운영/성능/보안/표준 연동(OpenTelemetry/OpenInference)까지 다루는 개발자

각 장에는 가능한 경우 ‘초급/중급/고급’ 표시를 포함한다.

---

## 3. Evidence(근거) 규칙

- 구현 설명은 반드시 파일 경로를 포함한다.
- 이 백서는 외부 블로그/논문보다 **리포지토리 내 SSoT 문서**를 우선 근거로 삼는다.
- “현상/동작”을 설명할 때는 다음 순서를 선호한다.
  1) 사용자 관점(명령/입출력) 2) 도메인 서비스(정책/흐름) 3) 어댑터(연결/저장/추적)

---

## 4. 빠른 재현(스모크)

> 최소 재현은 “실행 성공 경험”을 먼저 제공하는 것을 목표로 한다.

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

생성되는 산출물 예시(기본 경로):
- `reports/analysis/analysis_<RUN_ID>.json`
- `reports/analysis/analysis_<RUN_ID>.md`
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

---

## 5. 용어(최소 Glossary)

이 백서에서 자주 등장하는 용어를 “내부 개발자 관점”에서 고정한다.

- **Run / `run_id`**: 데이터셋과 설정(프로필/모델/옵션)을 고정한 한 번의 평가 실행 단위.
- **Dataset**: 평가 입력. 테스트 케이스(질문/답변/컨텍스트/정답 등)와 threshold를 포함할 수 있다.
- **Metric**: 품질을 수치화하는 규칙. Ragas 기반 + 커스텀 메트릭이 혼재한다.
- **Analysis Pipeline (DAG)**: “왜 점수가 낮았는지” 같은 질문에 답하기 위해 분석 노드들을 DAG로 실행한다.
- **Artifacts**: 분석/비교 과정에서 노드별 원본 결과를 분리 저장한 파일 묶음.
- **Domain Memory**: 평가 결과로부터 학습한 사실/패턴/행동을 누적하여 다음 평가에 반영하기 위한 레이어.
- **Stage Events**: 실행을 단계(input/retrieval/output 등) 이벤트로 분해해 저장/추적 가능한 형태로 만든 기록.

---

## 6. 문서 유지 전략(내부)

### 6.1 변경이 자주 발생하는 지점

- CLI 옵션/프리셋(`--mode simple/full`, `--auto-analyze`, `--retriever` 등)
- 분석 파이프라인 모듈/노드(DAG 템플릿/모듈 등록)
- 트레이싱(OTel/OpenInference, Phoenix 연동)
- Domain Memory(스키마/추출/검색/진화)

### 6.2 업데이트 원칙

- “설명”은 코드/문서 근거와 함께 갱신한다.
- 동작이 바뀌는 변경(옵션 추가/기본값 변경)은 해당 장(03/06/12/13)을 우선 갱신한다.

---

## 7. 향후 변경 시 업데이트 가이드

새 기능/리팩토링이 들어오면 다음 순서로 문서를 갱신한다.

1. **SSoT 확인**: `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/INDEX.md`
2. **입출력 변화 확인**: CLI/API에서 사용자에게 보이는 변화(플래그/응답/산출물)부터 반영
3. **근거 매핑 갱신**: 해당 기능의 “근거 파일”을 Evidence에 추가
4. **장별 ‘향후 추가’ 섹션 업데이트**: 각 장의 마지막에 있는 “향후 변경 시” 가이드에 체크리스트를 누적

---

## Evidence

- `docs/guides/USER_GUIDE.md` (핵심 워크플로/설치/명령)
- `docs/new_whitepaper/02_architecture.md` (설계 원칙/구조)
- `docs/ROADMAP.md` (현재 방향/우선순위)
- `docs/STATUS.md` (1페이지 상태 요약)
