# EvalVault 상태 요약 (Status)

> Audience: 사용자 · 개발자 · 운영자
> Last Updated: 2026-01-11

EvalVault의 목표는 **RAG 평가/분석/추적을 하나의 Run 단위로 연결**해, 실험→회귀→개선 루프를 빠르게 만드는 것입니다.

## 지금 가능한 것 (핵심)

- **CLI 평가/저장/비교**: `evalvault run`, `history`, `analyze`, `analyze-compare`
- **Web UI**: FastAPI + React로 평가 실행/히스토리/리포트 확인
- **Observability**: Phoenix(OpenTelemetry/OpenInference) 및 (선택) Langfuse/MLflow
- **프로필 기반 모델 전환**: `config/models.yaml` + `.env`로 OpenAI/Ollama/vLLM/Anthropic 등
- **Open RAG Trace 표준**: 외부/내부 RAG 시스템을 표준 스키마로 계측/수집

## 현재 제약 (투명 공개)

- Web UI의 기능은 CLI의 모든 플래그/옵션을 1:1로 노출하지 않습니다. (고급 옵션은 CLI 우선)
- 일부 고급 분석/인사이트는 CLI 출력이 우선이며, UI 패널/비교 뷰는 단계적으로 보강됩니다.

## 어디부터 읽으면 좋은가

- 설치/실행: `getting-started/INSTALLATION.md`
- 사용법/운영: `guides/USER_GUIDE.md`
- 개발/기여: `guides/DEV_GUIDE.md`
- 설계/운영 원칙(백서): `new_whitepaper/INDEX.md`
- 트레이싱 표준: `architecture/open-rag-trace-spec.md`
