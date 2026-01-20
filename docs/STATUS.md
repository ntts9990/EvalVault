# EvalVault 상태 요약 (Status)

> Audience: 사용자 · 개발자 · 운영자
> Last Updated: 2026-01-18

EvalVault의 목표는 **RAG 평가/분석/추적을 하나의 Run 단위로 연결**해, 실험→회귀→개선 루프를 빠르게 만드는 것입니다.

## 지금 가능한 것 (핵심)

- **CLI 평가/저장/비교**: `evalvault run`, `history`, `analyze`, `analyze-compare`
- **Web UI**: FastAPI + React로 평가 실행/히스토리/리포트 확인
- **Observability**: Phoenix(OpenTelemetry/OpenInference) 및 (선택) Langfuse/MLflow
- **프로필 기반 모델 전환**: `config/models.yaml` + `.env`로 OpenAI/Ollama/vLLM/Anthropic 등
- **Open RAG Trace 표준**: 외부/내부 RAG 시스템을 표준 스키마로 계측/수집
- **성능 개선 프레임**: `guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`에 KPI/평가/로드맵 정리

## 최근 완료 사항

- **CLI 병렬 명령군 완료**: compare/calibrate-judge/profile-difficulty/regress/artifacts lint/ops snapshot
- **노이즈 저감 파이프라인 강화**: dataset_preprocessor/evaluator/stage_metric_service 개선
- **ordering_warning 도입**: 순서 복원/경고 메트릭 + 런북/strict 기준 문서화
- **Web UI 반영**: RunDetails/CompareRuns/AnalysisLab에 경고 표시 및 런북 링크 추가

## 품질/검증 상태

- Python unit smoke: dataset_preprocessor/evaluator_comprehensive/stage_metric_service PASS
- Frontend lint/build: eslint PASS, vite build PASS (bundle size warning only)

## 현재 제약 (투명 공개)

- Web UI의 기능은 CLI의 모든 플래그/옵션을 1:1로 노출하지 않습니다. (고급 옵션은 CLI 우선)
- 일부 고급 분석/인사이트는 CLI 출력이 우선이며, UI 패널/비교 뷰는 단계적으로 보강됩니다.

## 어디부터 읽으면 좋은가

- 설치/실행: `getting-started/INSTALLATION.md`
- 사용법/운영: `guides/USER_GUIDE.md`
- 개발/기여: `guides/DEV_GUIDE.md`
- 설계/운영 원칙(백서): `new_whitepaper/INDEX.md`
- 트레이싱 표준: `architecture/open-rag-trace-spec.md`
