# EvalVault 상태 요약 (Status)

> Audience: 개발자 · 운영자 · 리뷰어
> Purpose: “지금 EvalVault가 어디까지 왔고, 무엇을 하고 있는지”를 1페이지로 공유
> Last Updated: 2026-01-03

---

## 현재 상태 (요약)

- **Current Version**: 1.5.0
- **Core Phases**: Phase 1–14 완료 (기반 기능 100%)
- **Tests**: 1,671 tests collected (`pytest --collect-only`, 2026-01-03 기준)

테스트 수 기준(재현 가능):

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

Phase 1–14 이후의 작업은 "새 기능 폭증"보다는 아래에 집중합니다.

- **코드 품질/구조 개선**: 중복 제거, 모듈 분리, 공통 옵션/도움말 표준화
  - 자세한 계획: [internal/DEVELOPMENT_GUIDE.md](internal/DEVELOPMENT_GUIDE.md)
- **운영 자동화/옵저버빌리티 표준화**: Drift 감시 → Gate → 릴리즈 노트 자동화
  - 실행 절차: [OBSERVABILITY_PLAYBOOK.md](OBSERVABILITY_PLAYBOOK.md)
- **문서/온보딩 정리**: 튜토리얼+가이드의 역할을 분리하고 SSoT를 고정
  - 문서 허브: [README.md](README.md)

---

## 문서/작업 추적에서의 "정답" 위치

- **현재 상태(이 문서)**: [STATUS.md](STATUS.md)
- **전체 인덱스**: [README.md](README.md)
- **계획(분기/백로그)**: [ROADMAP.md](ROADMAP.md)
- **개발 가이드**: [internal/DEVELOPMENT_GUIDE.md](internal/DEVELOPMENT_GUIDE.md)
- **배포/사용자 문서**: [README.ko.md](README.ko.md), [USER_GUIDE.md](USER_GUIDE.md), `tutorials/`
- **아카이브 (완료 기록)**: `internal/archive/`
