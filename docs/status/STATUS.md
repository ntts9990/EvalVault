# EvalVault 상태 요약 (Status)

> Audience: 개발자 · 운영자 · 리뷰어
> Purpose: “지금 EvalVault가 어디까지 왔고, 무엇을 하고 있는지”를 1페이지로 공유
> Last Updated: 2026-01-07

---

## 현재 상태 (요약)

- **Current Version**: 릴리스는 git tag 기준 (pyproject 버전은 자동 업데이트되지 않음)
- **Core Focus**: 병렬 리팩토링 단계 (R1~R4, D1 샘플/리포트 확보)
- **Tests**: 약 1.3k+ (unit 1,261 + integration 91 기준)

테스트 수 확인(재현 가능):

```bash
uv run pytest tests --collect-only -q
```

---

## 지금 “활발히 쓰는” 핵심 기능

- **평가 실행/저장/비교**: Typer CLI + SQLite/PostgreSQL 저장소
- **Web UI**: Streamlit 기반 Evaluate/History/Reports
- **관측성(Observability)**: Phoenix(OpenTelemetry/OpenInference) 중심, 필요 시 Langfuse/MLflow 병행
- **Domain Memory**: 평가 결과 학습 → threshold 보정/컨텍스트 보강/트렌드 분석
- **분석 파이프라인**: Query → Intent 분류 → DAG 모듈 실행(요약/검증/비교/분석)

---

## 현재 작업의 성격 (시점/우선순위)

병렬 에이전트가 작업한 결과를 리팩토링/통합하는 단계입니다.

- **병렬 리팩토링**: R1~R4 산출물 정합성/경로 최신화
  - 기준 문서: [internal/plans/PARALLEL_WORK_PLAN.md](../internal/plans/PARALLEL_WORK_PLAN.md)
- **문서 통합/최신화**: 유사 문서 통합 후 최신화 진행
  - 작업 계획: [internal/plans/DOCS_REFACTOR_PLAN.md](../internal/plans/DOCS_REFACTOR_PLAN.md)
- **CLI/Web/성능 리팩토링**: P2.2, P3, P4.1 단계 정비
  - 로드맵: [ROADMAP.md](ROADMAP.md)

---

## 문서/작업 추적에서의 "정답" 위치

- **내부 상태 SSoT**: [internal/status/STATUS.md](../internal/status/STATUS.md)
- **병렬 작업 기준**: [internal/plans/PARALLEL_WORK_PLAN.md](../internal/plans/PARALLEL_WORK_PLAN.md)
- **문서 허브**: [INDEX.md](../INDEX.md)
- **계획/백로그**: [ROADMAP.md](ROADMAP.md)
- **개발 가이드**: [internal/reference/DEVELOPMENT_GUIDE.md](../internal/reference/DEVELOPMENT_GUIDE.md)
- **배포/사용자 문서**: [README.ko.md](../../README.ko.md), [USER_GUIDE.md](../guides/USER_GUIDE.md), `tutorials/`
- **아카이브 (완료 기록)**: `../internal/archive/`
