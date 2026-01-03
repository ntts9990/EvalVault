# EvalVault 병렬 작업 계획서

> **작성일**: 2026-01-03
> **목적**: P2.2, P3, P4.1, P5, P6 병렬 개발

---

## 개요

5개 작업을 병렬로 진행하며, 파일 충돌을 최소화하기 위해 각 작업의 수정 범위를 명확히 정의합니다.

### 작업 요약

| ID | 작업 | 담당 영역 | 예상 규모 |
|----|------|----------|----------|
| P2.2 | Web UI 재구조화 | `adapters/inbound/web/` | ~1,800 LOC 리팩토링 |
| P3 | 성능 최적화 | `domain/services/`, `adapters/outbound/cache/` | 신규 + 개선 |
| P4.1 | CLI UX 개선 | `adapters/inbound/cli/` | ~5,700 LOC 개선 |
| P5 | 테스트 개선 | `tests/` | 1,655 tests → 최적화 |
| P6 | 문서화 개선 | `docs/` | 7 tutorials + API docs |

---

## 충돌 방지 매트릭스

### 수정 가능 영역

| 작업 | 수정 가능 | 수정 금지 |
|------|----------|----------|
| **P2.2** | `adapters/inbound/web/**` | `cli/`, `domain/`, `outbound/` |
| **P3** | `domain/services/cache*.py`, `adapters/outbound/cache/`, `domain/services/batch*.py` | `inbound/`, `entities/` |
| **P4.1** | `adapters/inbound/cli/**` | `web/`, `domain/`, `outbound/` |
| **P5** | `tests/**`, `conftest.py` | `src/evalvault/` (읽기만) |
| **P6** | `docs/**` | `src/`, `tests/` |

### 공유 파일 (조율 필요)

다음 파일은 여러 작업에서 수정할 수 있으므로 **조율 필수**:

- `pyproject.toml` - 의존성 추가 시
- `src/evalvault/__init__.py` - 공개 API 변경 시
- `src/evalvault/config/settings.py` - 설정 추가 시
- `README.md` - 문서화 관련

**조율 방식**: PR 전 충돌 확인, 필요시 rebase

---

## P2.2: Web UI 재구조화

### 현재 상태

```
web/
├── app.py           # 887 LOC (비대)
├── adapter.py       # 790 LOC (비대)
├── session.py       # 109 LOC
├── components/      # 14개 파일
│   ├── history.py   # 375 LOC
│   ├── reports.py   # 477 LOC
│   └── ...
└── pages/           # 4개 파일
```

### 목표

- `app.py` 분리: 라우팅 + 레이아웃만 유지 (300 LOC 이하)
- `adapter.py` 분리: 서비스 레이어 추출
- 공통 컴포넌트 정리

### 세부 태스크

| # | 태스크 | 예상 변경 파일 |
|---|--------|---------------|
| 1 | `app.py`에서 페이지 로직 추출 → `pages/` | `app.py`, `pages/*.py` |
| 2 | `adapter.py`에서 서비스 로직 추출 | `adapter.py`, 신규 `services/` |
| 3 | 공통 UI 패턴 추출 (에러 표시, 로딩 등) | `components/common.py` |
| 4 | 세션 관리 개선 | `session.py` |

### 산출물

- [ ] `app.py` < 300 LOC
- [ ] `adapter.py` < 400 LOC
- [ ] `services/` 디렉토리 신규
- [ ] 컴포넌트 재사용성 향상

---

## P3: 성능 최적화

### 현재 상태

```
domain/services/
├── batch_executor.py      # 기본 배치 처리
├── async_batch_executor.py # 비동기 배치
└── evaluator.py           # 평가 로직

adapters/outbound/cache/
├── hybrid_cache.py        # 12.7K LOC (2-tier 캐시)
└── memory_cache.py        # 3.5K LOC
```

### 목표

- 1000 TC 평가 시간: 30분 → 10분
- 캐시 적중률: 60% → 85%
- 메모리 사용량 최적화

### 세부 태스크

| # | 태스크 | 예상 변경 파일 |
|---|--------|---------------|
| 1 | 배치 크기 자동 조절 로직 | `batch_executor.py`, `async_batch_executor.py` |
| 2 | LRU + TTL 하이브리드 캐시 개선 | `hybrid_cache.py` |
| 3 | 스트리밍 로더 최적화 | `adapters/outbound/dataset/streaming_loader.py` |
| 4 | 캐시 적중률 측정 메트릭 추가 | `hybrid_cache.py`, 신규 `cache_metrics.py` |

### 산출물

- [ ] 적응형 배치 크기 조절
- [ ] 캐시 hit/miss 통계 API
- [ ] 벤치마크 결과 문서

---

## P4.1: CLI UX 개선

### 현재 상태

```
cli/commands/
├── run.py           # 1,811 LOC (가장 큼)
├── analyze.py       # 680 LOC
├── domain.py        # 681 LOC
├── phoenix.py       # 358 LOC
├── kg.py            # 349 LOC
└── ... (16개 파일, 총 5,707 LOC)

cli/utils/
├── formatters.py
├── validators.py
├── options.py
└── console.py
```

### 목표

- 신규 사용자 온보딩 시간: 30분 → 15분
- 일관된 옵션 체계
- 명확한 에러 메시지

### 세부 태스크

| # | 태스크 | 예상 변경 파일 |
|---|--------|---------------|
| 1 | 명령어 별칭 추가 (`-m`, `-l` 등) | `commands/run.py`, `commands/analyze.py` |
| 2 | 프리셋 시스템 구현 | `utils/presets.py` (신규), `commands/run.py` |
| 3 | 에러 메시지 개선 (해결책 제시) | `utils/errors.py` (신규 또는 확장) |
| 4 | 도움말 메시지 개선 | 전체 commands/*.py |
| 5 | `evalvault init` 온보딩 명령어 | `commands/init.py` (신규) |

### 산출물

- [ ] 짧은 옵션 별칭 전체 적용
- [ ] `--preset` 옵션 (production, quick, comprehensive)
- [ ] 사용자 친화적 에러 메시지
- [ ] `evalvault init` 명령어

---

## P5: 테스트 개선

### 현재 상태

```
tests/
├── unit/           # 대부분의 테스트
├── integration/    # 91개 통합 테스트
├── fixtures/       # 테스트 데이터
└── conftest.py

현재: 1,655 tests, 89% coverage
```

### 목표

- 테스트 실행 시간: 현재 → 50% 감소
- 커버리지: 89% → 95%
- 느린 테스트 최적화

### 세부 태스크

| # | 태스크 | 예상 변경 파일 |
|---|--------|---------------|
| 1 | 느린 테스트 식별 및 최적화 | `tests/unit/*.py` |
| 2 | 불필요한 fixture 정리 | `conftest.py`, `fixtures/` |
| 3 | 병렬 테스트 실행 설정 | `pyproject.toml` (pytest-xdist) |
| 4 | 커버리지 미달 영역 테스트 추가 | 신규 테스트 파일 |
| 5 | `@pytest.mark.slow` 마크 정리 | 전체 테스트 파일 |

### 산출물

- [ ] pytest-xdist 적용
- [ ] 테스트 실행 시간 50% 감소
- [ ] 95% 커버리지 달성
- [ ] 테스트 마크 체계화

---

## P6: 문서화 개선

### 현재 상태

```
docs/
├── tutorials/           # 7개 튜토리얼
│   ├── 01-quickstart.md
│   ├── 02-basic-evaluation.md
│   ├── 03-custom-metrics.md
│   ├── 04-phoenix-integration.md
│   ├── 05-korean-rag.md
│   ├── 06-production-tips.md
│   └── 07-domain-memory.md
├── USER_GUIDE.md
├── ARCHITECTURE.md
└── internal/
```

### 목표

- API 문서 자동화 (mkdocs + mkdocstrings)
- 튜토리얼 강화 (실행 가능한 예제)
- 문서 간 일관성

### 세부 태스크

| # | 태스크 | 예상 변경 파일 |
|---|--------|---------------|
| 1 | mkdocs 설정 | `mkdocs.yml` (신규), `pyproject.toml` |
| 2 | API 레퍼런스 자동 생성 | `docs/api/` (신규) |
| 3 | 튜토리얼 코드 검증 스크립트 | `scripts/validate_tutorials.py` (신규) |
| 4 | 문서 스타일 가이드 | `docs/internal/STYLE_GUIDE.md` (신규) |
| 5 | 기존 튜토리얼 업데이트 | `docs/tutorials/*.md` |

### 산출물

- [ ] mkdocs 기반 문서 사이트
- [ ] API 레퍼런스 자동 생성
- [ ] 모든 튜토리얼 코드 검증됨
- [ ] 문서 스타일 가이드

---

## 작업 의존성

```
P2.2 (Web UI)     ───────────────────────→ 독립
P3 (성능)         ───────────────────────→ 독립
P4.1 (CLI UX)     ───────────────────────→ 독립
P5 (테스트)       ─── P3 완료 후 성능 테스트 추가 가능 ───→ 약한 의존
P6 (문서)         ─── 다른 작업 완료 후 API 문서 업데이트 ───→ 약한 의존
```

**결론**: 5개 작업 모두 초기에는 **완전 병렬 실행 가능**

---

## 진행 관리

### 브랜치 전략

```
main
├── feat/p2.2-web-ui-restructure
├── feat/p3-performance-optimization
├── feat/p4.1-cli-ux-improvement
├── feat/p5-test-improvement
└── docs/p6-documentation-improvement
```

### 커밋 메시지 규칙

```
feat(web): Extract service layer from adapter.py     # P2.2
perf(cache): Add adaptive batch sizing               # P3
feat(cli): Add short option aliases                  # P4.1
test(unit): Optimize slow integration tests          # P5
docs: Add API reference generation                   # P6
```

### 완료 체크리스트

각 작업 완료 시:
- [ ] 해당 브랜치의 모든 테스트 통과
- [ ] lint/format 검사 통과
- [ ] PR 생성 및 코드 리뷰
- [ ] main 브랜치 머지
- [ ] 관련 문서 업데이트

---

## 우선순위 및 권장 순서

| 순위 | 작업 | 이유 |
|------|------|------|
| 1 | **P4.1 CLI UX** | 사용자 직접 영향, Quick Win 많음 |
| 2 | **P3 성능** | 핵심 기능 개선 |
| 3 | **P2.2 Web UI** | 코드 품질 개선 |
| 4 | **P5 테스트** | 다른 작업 완료 후 검증 |
| 5 | **P6 문서** | 다른 작업 완료 후 반영 |

단, 모든 작업은 **병렬 시작 가능**하며 위 순서는 리소스 제한 시 참고용입니다.

---

**문서 끝**
