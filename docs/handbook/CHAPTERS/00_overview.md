# 00. Overview

> 내부용 본편(상세). 외부 공개 요약은 `docs/handbook/EXTERNAL.md`에 별도 작성.

---

## TL;DR

- EvalVault는 **평가(Evaluation) → 분석(Analysis) → 비교(Compare) → 개선 루프**를 `run_id` 단위로 연결한다.
- 실행 결과는 DB와 아티팩트로 남아 재현 가능하며, Web UI는 같은 DB를 바라볼 때 즉시 이어진다.
- 관측(Phoenix/Langfuse), 표준(Open RAG Trace), 학습(Domain Memory), 분석 파이프라인(DAG)은 **옵션화**되어 필요할 때만 켠다.

## 미션(1문장)

RAG 시스템의 변경이 **진짜 개선인지**를 데이터셋·메트릭·(선택)트레이싱 관점에서 **재현 가능하게** 검증하고, 왜/어디서 깨지는지까지 설명 가능한 워크플로를 제공한다.

## 대상 사용자(3)

1) RAG를 운영하는 ML/플랫폼/백엔드 엔지니어
2) 품질/회귀를 책임지는 QA/PM
3) 반복 평가/벤치마크가 필요한 외부 사용자(컨설팅/솔루션/고객사 PoC)

## 핵심 가치(3)

1) 재현성: run 단위로 평가/분석/아티팩트/트레이스를 묶고 비교할 수 있다.
2) 진단 가능성: 점수 변화의 원인을 모듈/스테이지/메트릭 레벨로 추적할 수 있다.
3) 운영 옵션화: Phoenix/Langfuse/MLflow 같은 관측은 필요할 때만 켠다.

## Non-goals(3)

1) RAG 시스템 자체를 대신 구현/호스팅하지 않는다.
2) 단일 점수 하나로 모든 품질을 대체하지 않는다(다중 메트릭/근거 기반).
3) 특정 벤더/모델에 종속되지 않는다(OpenAI/Ollama/vLLM 등 옵션화).

---

## 핵심 개념 요약(공통 언어)

- **run_id**: 평가 실행의 단일 식별자. 평가/분석/아티팩트/트레이스가 이 키로 묶인다.
- **Artifacts**: 요약 리포트와 모듈별 원본 결과를 분리 저장한다.
- **Stages**: 입력/검색/출력 단계를 이벤트와 메트릭으로 남겨 원인 추적을 가능하게 한다.
- **Profiles**: `config/models.yaml`과 `.env`로 모델/임베딩을 바꾼다.
- **Analysis Pipeline**: 의도 기반 DAG로 “왜”를 설명하는 분석을 실행한다.

---

## 최소 실행 시나리오(내부 개발자 기준)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

이 실행으로 생성되는 대표 산출물:

- 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
- 보고서(Markdown): `reports/analysis/analysis_<RUN_ID>.md`
- 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

---

## CLI ↔ Web UI 연결

```bash
# Terminal 1
uv run evalvault serve-api --reload

# Terminal 2
cd frontend
npm install
npm run dev
```

- CLI와 Web UI가 **같은 DB 경로**를 바라보면, CLI 실행 결과가 Web UI에 바로 노출된다.

---

## 문서 지도(다음으로 어디를 읽을지)

- 구조/경계: `01_architecture.md`
- 데이터/메트릭: `02_data_and_metrics.md`
- 실행 흐름: `03_workflows.md`
- 운영 런북: `04_operations.md`
- 보안 경계: `05_security.md`
- 품질/테스트: `06_quality_and_testing.md`
- UX/제품: `07_ux_and_product.md`
- 로드맵: `08_roadmap.md`

## 근거 링크(3+)

- 프로젝트 정의/핵심 개념: `../../README.md`
- 상태/제약: `../STATUS.md`
- 로드맵: `../ROADMAP.md`
- 내부 백서(개요): `../new_whitepaper/01_overview.md`
- 문서 운영 원칙: `../INDEX.md`

---

## 전문가 관점 체크리스트

- [ ] run_id/아티팩트/트레이스가 하나의 흐름으로 설명되는가
- [ ] 최소 실행 시나리오가 재현 가능한가
- [ ] 옵션 기능(Phoenix/Langfuse/Domain Memory/DAG)이 “필수”처럼 서술되지 않는가
