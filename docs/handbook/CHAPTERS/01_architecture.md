# 01. Architecture

## 목표

EvalVault의 헥사고날(Ports & Adapters) 구조를 이해하고, 어떤 경계를 유지해야 확장/교체가 안전한지 정리한다.

## 설계 원칙

- SSoT는 `docs/new_whitepaper/02_architecture.md`이며, 구현은 문서에 맞춘다.
- 도메인은 순수하게 유지하고, 인프라 의존은 포트/어댑터로 분리한다.
- 어댑터는 포트(계약)에 맞춰 교체 가능해야 한다.
- 설정과 런타임 선택은 코드가 아니라 프로필/환경 변수로 처리한다.

## 코드 지도(핵심 경로)

- 도메인 엔티티/서비스: `src/evalvault/domain/`
- 포트(계약): `src/evalvault/ports/`
- 어댑터(통합): `src/evalvault/adapters/`
- 런타임 설정/프로필: `src/evalvault/config/`, `config/models.yaml`

## 경계와 의존성 규칙

- 도메인 -> 포트는 의존 가능, 포트 -> 도메인은 인터페이스만 유지
- 어댑터 -> 포트 의존, 어댑터 -> 도메인 직접 의존은 최소화
- 구성/프로필은 런타임에 주입하며 하드코딩 금지

## 확장/교체 가이드

1) 포트 정의: `src/evalvault/ports/outbound/` 또는 `src/evalvault/ports/inbound/`
2) 어댑터 구현: `src/evalvault/adapters/outbound/` 또는 `src/evalvault/adapters/inbound/`
3) 설정 연결: `src/evalvault/config/` 및 `config/models.yaml`

예시 확장 포인트:
- LLM 어댑터: `src/evalvault/adapters/outbound/llm/`
- 트래커/관측: `src/evalvault/adapters/outbound/tracker/`
- 스토리지: `src/evalvault/adapters/outbound/storage/`
- 아티팩트 FS: `src/evalvault/adapters/outbound/artifact_fs.py`
- 분석 파이프라인: `src/evalvault/adapters/outbound/analysis/`

## 아키텍처 흐름(요약)

1) CLI/API 입력 -> 도메인 서비스 호출
2) 도메인 서비스 -> 포트를 통해 LLM/저장소/트래커 접근
3) 실행 결과 -> run_id 기준 저장 및 분석/리포트로 연결

## 참고(근거)

- 내부 백서(SSoT): `../new_whitepaper/02_architecture.md`
- 아키텍처/표준 관련: `../new_whitepaper/13_standards.md`
- 포트/어댑터 문서: `../api/ports/inbound.md`, `../api/adapters/inbound.md`, `../api/adapters/outbound.md`
