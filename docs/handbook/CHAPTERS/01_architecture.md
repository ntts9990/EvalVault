# 01. Architecture

## 목표

EvalVault의 아키텍처를 "도메인/포트/어댑터" 관점으로 이해하고, 어디를 확장/교체해야 하는지 빠르게 파악한다.

## 큰 그림

- 핵심 설계 원칙은 `docs/new_whitepaper/02_architecture.md`를 SSoT로 둔다.
- 코드 구조는 헥사고날(Ports & Adapters) 레이아웃을 따른다.

## 코드 지도(핵심 경로)

- 도메인: `src/evalvault/domain/`
- 포트(계약): `src/evalvault/ports/`
- 어댑터(통합): `src/evalvault/adapters/`
- 설정/프로필: `src/evalvault/config/`, `config/models.yaml`

## 참고(근거)

- 내부 백서: `../new_whitepaper/02_architecture.md`
- 문서 운영 원칙: `../INDEX.md`
