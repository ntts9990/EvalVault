# Docs Cleanup Worklog (2026-01-29)

목표: `docs/handbook`을 canonical로 두고, `docs/` 내 중복/구식 문서를 정리(통합/삭제)하며, 부록(appendix) 정합성과 링크를 점검한다.

## 진행 로그

### 2026-01-29

- 01: 문서 정리 작업 시작. `docs/handbook` 구조/부록(coverage, taxonomy, inventory) 확인.
- 02: 정리 방식 결정: 링크 깨짐(404) 방지를 위해, 다수의 구식/중복 문서는 **삭제 대신 “handbook으로 통합됨” 스텁(짧은 리다이렉트 문서)** 으로 치환.
- 03: 중복/로그/계획 성격 문서 대량 정리.
  - `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md`, `docs/guides/RAG_CLI_WORKFLOW_TEMPLATES.md`를 deprecated 스텁으로 치환.
  - `docs/guides/*PLAN*`, `docs/guides/*REPORT*`, `docs/guides/*WORKLOG*` 일부를 deprecated 스텁으로 치환.
  - `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/getting-started/INSTALLATION.md`를 deprecated 스텁으로 치환.
  - `docs/new_whitepaper/INDEX.md` 및 `docs/new_whitepaper/STYLE_GUIDE.md`에 deprecated 헤더 추가.

- 04: handbook 내부 링크/근거를 deprecated 문서에서 분리.
  - handbook 챕터에서 `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/getting-started/INSTALLATION.md`, `docs/guides/{USER_GUIDE,DEV_GUIDE}.md`, `docs/new_whitepaper/**`를 “근거”로 직접 인용하던 부분을 제거하고, 코드/설정/README/handbook 내부 링크로 치환.
  - 변경 대상: `docs/handbook/CHAPTERS/00_overview.md`, `docs/handbook/CHAPTERS/03_workflows.md`, `docs/handbook/CHAPTERS/04_operations.md`, `docs/handbook/CHAPTERS/06_quality_and_testing.md`, `docs/handbook/CHAPTERS/07_ux_and_product.md`, `docs/handbook/CHAPTERS/08_roadmap.md`, `docs/handbook/CHAPTERS/09_competitive_positioning.md`.

- 05: `docs/new_whitepaper/**` 트랙을 전면 스텁(redirect)으로 통일.
  - 과거 링크 호환은 유지하되, 본문은 제거하고 handbook의 대응 챕터로 안내.
  - 포함: `docs/new_whitepaper/00_frontmatter.md` ~ `docs/new_whitepaper/14_roadmap.md`, `docs/new_whitepaper/INDEX.md`, `docs/new_whitepaper/STYLE_GUIDE.md`.

- 06: `docs/api/**`에서 deprecated 링크 제거.
  - `docs/api/adapters/inbound.md`, `docs/api/domain/metrics.md`, `docs/api/ports/outbound.md`의 User Guide / Developer Whitepaper 링크를 handbook 링크로 교체.

- 07: handbook 부록 스냅샷 문서에 최신화 노트 추가(재생성 없이).
  - `docs/handbook/appendix-coverage-matrix.md`, `docs/handbook/appendix-file-inventory.md`에 “스냅샷 기준 + 일부 docs는 이후 deprecated/아카이브로 변할 수 있음 + 최신 SSoT는 handbook” 주석 추가.

- 08: handbook이 deprecated 스텁 문서에 다시 의존하지 않도록 추가 정리.
  - `docs/handbook/CHAPTERS/07_ux_and_product.md`에서 `docs/guides/WEBUI_CLI_ROLLOUT_PLAN.md` 근거를 코드/라우팅 근거(`frontend/src/App.tsx`, 각 페이지, runs API)로 교체.
  - `docs/handbook/CHAPTERS/03_workflows.md`에서 `docs/guides/RAG_CLI_WORKFLOW_TEMPLATES.md` 참조를 실행 가능한 픽스처/예시(`tests/fixtures/e2e/`, `examples/`)로 교체.

## 원칙

- `docs/handbook/**`가 최신이며 우선.
- `docs/`의 다른 문서는:
  - handbook에 이미 반영된 내용이면 삭제 후보
  - 부분적으로 유효하면 handbook에 흡수(최신화) 후 원본 삭제 후보
  - 운영/규정/스펙 성격으로 handbook 부록에 남기는 편이 합리적이면 부록으로 이동/링크

## 체크포인트

- [ ] 삭제/이동 전: handbook에 해당 내용이 반영되었는지 확인
- [ ] 삭제/이동 후: `docs/INDEX.md` 및 handbook 링크 정합성 재점검
- [ ] appendix 관련: `docs/handbook/appendix-coverage-matrix.md` 및 `docs/handbook/appendix-taxonomy.md`와 충돌/누락 없도록 조정
