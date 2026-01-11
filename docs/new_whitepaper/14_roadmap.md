# 14. 로드맵 및 향후 계획

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault의 “지금 상태”와 “다음에 무엇을 할지”를 내부 개발자/리뷰어가 빠르게 파악하게 한다.
- **독자**: 내부 개발자/리뷰어
- **선행 지식**: 없음

---

## TL;DR

- 공개 로드맵: `docs/ROADMAP.md`
- 상태 요약(1페이지): `docs/STATUS.md`
- 이 백서는 “개발자 온보딩/확장/운영” 관점의 기준 문서이며, 로드맵의 상세 항목을 대체하지 않는다.

---

## 1) 문서들의 역할 분담(SSoT)

- `docs/STATUS.md`
  - “지금 어디까지 왔나”를 1페이지로 공유
- `docs/ROADMAP.md`
  - 전체 개발 방향과 우선순위(외부 공유용)
- `docs/new_whitepaper/*`
  - 신규 합류자가 “실제 코드/경계/운영 루틴”을 빠르게 이해하도록 돕는 개발 백서

---

## 2) 로드맵을 읽는 방법(내부 개발자용)

### 2.1 큰 흐름

- `docs/ROADMAP.md`는
  - Phase 1~14(핵심 시스템) 완료 상태를 기반으로
  - 현재는 R1~R4 같은 “리팩토링/통합/품질 개선” 트랙을 중심으로 정리한다.

### 2.2 리뷰 시 확인 포인트

- “로드맵의 항목이 구현으로 연결되는가?”
  - 코드 근거: 해당 기능의 핵심 모듈/포트/어댑터
  - 테스트 근거: 관련 단위/통합 테스트
  - 산출물 근거: 리포트/아티팩트/벤치마크 스모크

---

## 3) 문서 업데이트 루틴(이 백서 유지보수)

### 3.1 변경이 들어왔을 때 어디를 갱신할까

- 메트릭/평가 로직이 바뀌면
  - `docs/new_whitepaper/08_customization.md` (메트릭 추가 절차)
  - `docs/new_whitepaper/09_quality.md` (변경 유형별 검증)
  - 필요 시 `docs/new_whitepaper/07_advanced.md` (Domain Memory/관측성 연결)

- 분석(DAG 파이프라인)이 바뀌면
  - `docs/new_whitepaper/07_advanced.md` (검색 비교/벤치마크 의도)
  - `docs/new_whitepaper/08_customization.md` (모듈/템플릿/등록)
  - `docs/new_whitepaper/12_operations.md` (운영 런북: pipeline/아티팩트)

- Domain Memory가 바뀌면
  - `docs/new_whitepaper/07_advanced.md` (저장소/스키마/동학)
  - `docs/new_whitepaper/08_customization.md` (포트/스키마 변경 체크리스트)

- 관측성/트레이싱이 바뀌면
  - `docs/new_whitepaper/07_advanced.md` (Stage/Phoenix/Open RAG Trace)
  - `docs/new_whitepaper/12_operations.md` (운영 런북)
  - `docs/new_whitepaper/13_standards.md` (표준/Collector)

### 3.2 “최소 업데이트” 원칙

- (1) 실행 명령/경로가 바뀌었으면 반드시 수정
- (2) 근거(Evidence) 파일 경로가 바뀌었으면 반드시 수정
- (3) 산출물 스키마가 바뀌었으면 “어디에서 확인할지”를 반드시 수정

---

## 4) 이 백서의 확장 방향(우선순위 힌트)

- 단순 소개보다 “운영/디버깅/회귀 방지” 레시피를 우선한다.
- 새로운 기능은
  - Port 계약
  - Adapter 구현
  - CLI/API 표면
  - 테스트/품질 루틴
  - 아티팩트/관측성 연결
  을 하나의 묶음으로 문서화한다.

---

## Evidence

- `docs/STATUS.md`
- `docs/ROADMAP.md`

---

## 전문가 관점 체크리스트

- [ ] 신규 개발자가 “지금 뭘 하고 있는지” 5분 안에 파악 가능한가
- [ ] 로드맵과 내부 상태(SSoT)의 역할이 혼동되지 않게 정리되었는가
- [ ] 로드맵 항목이 코드/테스트/산출물로 연결되는가

---

## 향후 변경 시 업데이트 가이드

- 로드맵/상태 SSoT 파일 경로가 바뀌면:
  - 이 장의 **1장 Evidence**와 링크를 즉시 갱신한다.

- 이 백서의 장 구성이 바뀌면:
  - `docs/new_whitepaper/INDEX.md`와 함께 이 장의 **3장(업데이트 루틴)**을 갱신한다.
