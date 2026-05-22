# EvalVault — Development Journal

> AI Tool Suite 핸드오프 패킷의 narrative 변경 기록. 머신-리더블 SSoT는
> [`.ai-tool-suite/project-state.json`](../.ai-tool-suite/project-state.json),
> 운영 계약은 [`docs/adapter-contract.md`](./adapter-contract.md).
> 이 저널은 "무엇이/왜 바뀌었고, 무엇이 아직 불안정한지"를 산문으로 설명한다.

- 기준 버전: **v1.77.0** (PyPI), `main = bc88726`
- in-session HEAD: `e9c79f3` (main 대비 **25 커밋 ahead**, 머지 대기)
- 마지막 갱신: 2026-05-22
- 분류: `trusted-runtime` · T-level cap: **T2 (Evaluation Gate)**

작성 규칙: raw chain-of-thought / 사적 추론 트레이스는 기록하지 않는다. 결정·아티팩트 narrative만.

---

## 1. 최근 변경 (What changed recently)

이번 세션은 main에 머지되지 않은 25개 커밋을 세 갈래로 쌓았다. 모두 슬라이스(작은 브랜치) 단위이며 각 슬라이스는 독립적으로 빌드·검증된다.

### 1.1 L-S2 — 의존성 라인 업데이트 (Phase 3.5)

- **L-S2 (`88739ab`)**: LLM 클러스터 동시 bump. `openai 1.40.8 → 2.38.0`, `instructor 1.4.1 → 1.15.1`, `langchain-openai 0.2.2 → 1.2.2`.
  `src/` diff = 0 — LLM 프롬프트 문자열은 byte-identical. 어댑터 경계가 안정적이라는 증거.
- **L-S2-data (`f7ca30c`)**: `mlflow 3.8.1 → 3.12.0`, `arize-phoenix 12.27.0 → 16.0.0`. OpenInference instrumentation은 0.1.57로 끌려옴. Phoenix tracer init은 어댑터 경계에서 변화 없음.

### 1.2 W-Sx — Phase 4 웹 프론트엔드 디자인 시스템 마이그레이션

Claude 디자인 언어 기반 디자인 시스템을 기존 React 19 앱 위에 점진 적용. **수술적(surgical) 마이그레이션** — IA·라우트·컴포넌트 경계는 그대로 두고 시각 atom(alert block, empty state, button, badge)만 디자인 primitive로 치환.

- W-S0/W-S1 (`8fe7c35`, `6d8fe76`): 디자인 토큰 + primitive 토대, `/design-system` 쇼케이스.
- W-S2~W-S5b: Dashboard / EvaluationStudio / AnalysisLab / AiSdkChat / JudgeCalibration / Settings / Visualization 등 페이지별 점진 이행.
- W-S6 (`6220202`): `lucide-react 0.562 → 1.16`, Playwright e2e 18/18 green.
- W-S7 (`8eb0de7` 외): `AuthorityBadge` primitive로 T0~T4 권한 단계 시각 분리 — RunDetails / Dashboard / CompareRuns에 T2 배지 노출.
- W-S3-Phase2 (`37272f3`, `fef4caf`): 고아 컴포넌트 `ComprehensiveAnalysis.tsx`(801 LOC) 삭제 + `analysisRecord` 헬퍼 공유 추출.

### 1.3 핸드오프 / 문서 정리

- `c1b2998`, `20f4d2c`, `c89085f`: 핸드오프 상태 문서 + refactor diagnosis + CLAUDE.md broken link 수정.
- **`e9c79f3`**: `.gitignore`에 로컬 산출물 패턴 4종 추가(`.claude/`, `mlruns/`, Playwright 산출물, `data/exports/`) + 본 AI Tool Suite 요청 문서(`docs/source-project-update-request.md`)를 repo에 기록.
- **이번 패킷 (untracked)**: `.ai-tool-suite/project-state.json`, `docs/adapter-contract.md`, 그리고 이 저널. 요청 §31-37의 3개 산출물.

---

## 2. 왜 바뀌었나 (Why it changed)

- **L-S2 클러스터 bump**: openai/instructor/langchain-openai/rich는 패키지 메타데이터로 **횡적 결합(transitive coupling)** 되어 있어 개별 bump가 불가능하다. 클러스터 전체를 한 슬라이스에서 `uv lock` dry-run으로 검증해야 했다. `src/` diff = 0을 확인하고 나서야 안전 판정.
- **W-Sx 수술적 마이그레이션**: 빅뱅 재작성 대신 슬라이스마다 빌드 + Playwright 검증으로 독립 ship/revert 가능하게 했다. 디자인 시스템을 운영 중인 앱에 리스크 없이 굴리기 위함.
- **핸드오프 패킷**: AI Tool Suite가 EvalVault를 reverse-engineer 하지 않고 어댑터로 통합하도록, 안정 표면(명령·아티팩트·스키마)을 외부화. 현재 AI Tool Suite 타겟은 *Level 2 어댑터 존재 → Level 3 로컬 invoke + no-network guard*.

---

## 3. 아직 불안정한 것 (What remains unstable)

AI Tool Suite가 **아직 의존하면 안 되는** 표면:

- `evalvault analyze` / `analyze-compare` JSON shape — `schema_version: 0.9`, intent classifier가 LLM을 쓸 수 있어 cloud-opt-in. 정제 중.
- Calibration artifact 디렉터리 내부 구조 (`reports/calibration/artifacts/<id>/`) — 파일명은 안정, 하위 구조는 beta.
- `RegressionGateReport.results[].effect_level` enum — 향후 minor에서 level 추가 가능. enum 값 자체에 의존 금지(필드 존재는 안정).
- `history` / `config`의 `--format json` — 동작은 하지만 **필드 안정성 보장은 아직 문서화 안 됨**. 테이블 출력이 1차 표면.
- 구조적 에러 출력 — 현재 실패는 exit code(non-zero) + stderr 텍스트. `--format json` 명령도 **에러는 JSON으로 안 나온다**. 어댑터는 파싱 전 exit code를 먼저 검사할 것.

머지 측면 불안정: HEAD가 main 대비 25 커밋 ahead. main에 머지되어 v1.78.0으로 컷되기 전까지 위 슬라이스는 "in-session" 상태다(§6 참조).

---

## 4. 다른 도구가 배울 점 (What other tools may learn from it)

`project-state.json.reusable_patterns`의 산문 버전:

- **Regression-gate report shape**: frozen dataclass, `status ∈ {passed, failed}` + per-metric 통계 비교. **T3 promote/rollback 문자열을 절대 섞지 않는다.** Tier-2 평가 verdict를 내는 다른 source 프로젝트가 같은 status 어휘를 채택하면 생태계 전반의 결정-emit 코드가 균일해진다. → `src/evalvault/domain/services/regression_gate_service.py`
- **임계값을 픽스처에 co-locate**: 메트릭 threshold를 env가 아닌 데이터셋 JSON에 둔다. 머신·CI 간 회귀 추론이 portable.
- **아티팩트 저장 레이아웃 분리**: 생성물 `reports/<category>/<id>/`, 픽스처 `tests/fixtures/`, raw export `data/exports/`. "픽스처냐 생성물이냐" 혼동을 어댑터/리뷰어 단계에서 차단.
- **비대화형 CLI 계약**: 모든 `evalvault` 명령은 기본 non-interactive, read-path에 `--format json`, profile은 `--profile`/`EVALVAULT_PROFILE`. TTY 가정 없이 stdin/stdout JSON 계약에 의존 가능.
- **T0-T4 anti-conflation**: 같은 표면이 T2 verdict와 T3 문자열을 절대 혼합하지 않는다 — 에러 메시지·UI 배지에서도. Web UI `AuthorityBadge`가 이를 시각적으로 강제.
- **수술적 UI primitive 마이그레이션**: 디자인 시스템을 기존 앱에 빅뱅 없이 굴리는 W-Sx 패턴. 각 PR이 리뷰·revert 가능한 크기.

---

## 5. 공유 계약으로 승격할 후보 (Promote into a shared contract later)

- **RegressionGateReport 스키마(또는 그 strict subset)** 를 AI Tool Suite의 cross-tool "evaluation-gate decision" 계약으로 채택. 단, T2(평가)와 T3(릴리스) verdict를 **필드 레벨에서 섞지 말 것**.
- **공유 closed-network LLM stub**: 결정적 로컬 모델을 AI Tool Suite가 제공하면 각 source 프로젝트가 stub을 재발명하지 않고 `verification_commands.closed_network`를 표준화할 수 있다.
- **closed-network smoke 명령 표준화**: 현재 EvalVault는 cloud 시크릿 없이 SQLite + Ollama 경로를 도는 단일 `evalvault check`가 없다(가장 가까운 건 필터링된 unit test 명령). 이 패턴이 안정화되면 생태계 공통 계약 후보.
- **구조적 에러 JSON** (`--error-format json` 또는 자동 wrap): 어댑터 통합 시 stderr 텍스트 파싱을 없앨 수 있어 next_priorities에 등재.

---

## 6. 머지 대기 (Merge-Pending Slices)

`main = bc88726` 대비 HEAD `e9c79f3`까지 **25 커밋**이 머지 대기. AI Tool Suite는 *현재 main 표면* 과 *이 in-session 표면* 을 구분해야 한다. 아래 표면 계약(adapter-contract.md / project-state.json)은 머지 후 v1.78.0 기준으로 안정 보장된다.

| 갈래 | 슬라이스 | 상태 | 어댑터 영향 |
|---|---|---|---|
| 의존성 (Phase 3.5) | L-S2, L-S2-data | code complete | `src/` diff 0; openai 1.x→2.x는 외부에서 underlying client 직접 생성 시 재확인 권장 |
| 프론트엔드 (Phase 4) | W-S0 ~ W-S7, W-S3-Phase2/2b | code complete, Playwright green | UI 전용; CLI/아티팩트 표면 무영향 |
| 문서/핸드오프 | handoff state, CLAUDE.md 링크 수정, 이 패킷 | in progress | 어댑터 통합 진입점 |

**다음 우선순위 (next_priorities, project-state.json과 동기):**

1. 위 슬라이스를 main에 머지하고 **v1.78.0** 컷.
2. regression-gate를 main의 GitHub Actions **required check** 로 배선 (운영 작업, 코드 아님 — repo가 자가 강제 불가).
3. instructor가 `rich<15` cap을 풀면 `rich → 15.x`.
4. mlflow가 `pandas<3` cap을 풀면 `pandas → 3.x`.
5. AnalysisLab + AnalysisResultView의 `<AnalysisResultBody>` 완전 추출 (W-S3-Phase2c, deferred).
6. closed-network smoke 명령 정제.

---

## 7. 알려진 리스크 (Known Risks)

machine-readable 전체 목록은 `project-state.json.known_risks`. 핵심:

- **P1 regression gate**: 코드는 존재하나 강제는 GitHub branch protection rule(Repo Settings → Branches → main → required check)에 의존. 운영자가 `regression-gate`를 required check에 추가해야 하며 repo가 자가 강제 불가.
- **LLM 클러스터 횡적 결합**: openai/instructor/langchain-openai/rich를 개별 bump 불가. 향후 bump 제안은 클러스터 전체로 `uv lock` dry-run 필수.
- **pandas 3.x 차단**: mlflow가 `pandas<3` cap을 풀기 전까지 채택 불가 (mlflow 3.12.0이 현재 최신).
- **OpenAI 비용**: 기본 judge는 `gpt-5-mini`. closed-network 실행은 ollama/vllm profile fallback 설정 필요.
- **manim dev extra**: Cairo 시스템 라이브러리 의존 — `pkg-config` + Cairo 없는 머신에서 `uv sync --extra dev` 실패. dev extras 슬리밍 검토 중.
- **Ragas 0.4.2 pin**: 메이저 bump 시 RagasEvaluator 변경 필요. pyproject.toml에 방어적 pin 문서화.

---

## 8. 변경 이력 추적

- 본 저널 / adapter-contract.md 자체의 변경: `git log --oneline -- docs/development-journal.md docs/adapter-contract.md`.
- 슬라이스별 narrative: `git log --oneline main..HEAD` (현재 25 커밋).
- 릴리스 단위 변경: git 태그 기반 (python-semantic-release). PyPI 배포 버전 = 최신 태그.
