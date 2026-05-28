> **Canonical source:** `ntts9990/solution-orchestrator` → `docs/strategy/per-repo-development-plans.v3.1.md` (main). 본 파일은 mirror — 편집 시 canonical을 먼저 갱신하고 일괄 동기화. solution-platform 메타 레포 신설 후 canonical은 그쪽으로 이전 예정.

# EvidenceOps Platform — 레포별 개발 계획 (v3.1 통합 / adjusted)
> **문서 성격:** v3.1 Final 전략에 따라 **각 레포 담당 에이전트가 작성한 상세 개발 계획**을 *요약 없이 그대로* 통합한 문서. 앞쪽 §0 최종요약만 신규 작성.
> **기준 전략:** `docs/strategy/all-repos-consolidation-strategy.v3.1.execution-reference.md` (owner v3.1 Final canonical).
> **기준 인벤토리:** `docs/code-census/all-repos-code-census.md` (2026-05-27).
> **수록 계획 14개:** Contracts 2(evidenceops-contracts, solution-platform) · Platform 7(solution-orchestrator, EvalVault, reverra-gate, ai-tool-suite, llm-research-vault, PromptOptimizer, ai-agent-harness-optimization) · Applications 5(verbera, grounded-workspace-os, aia-classification-design, aia-awesome-novel-studio, reverra-lab).
> **작성일:** 2026-05-27 · **조정일:** 2026-05-28 · **상태:** 실행 계획(proposal 단계, 동시 편집 에이전트 있음).
> **이번 조정(adjusted):** §0 요약을 v3.1 전략·14개 레포별 본문과 정합화하는 8개 미세 조정. 본문(§A/§B/§C)의 레포별 계획은 *변경 없음*(각 에이전트 소유). §0.7에 조정 사항 매트릭스, §0.8에 외부 SOTA(AlphaProof Nexus) PROPOSAL 5건, §0.9에 외부 SOTA(Epicure) PROPOSAL 5건, §0.10에 외부 SOTA(AutoScientists) PROPOSAL 5건 추가.
---
## 0. 최종요약 (신규)
### 0.1 한 줄
14개 계획은 모두 같은 척추를 공유한다 — **C1(evidence-contract)과 S1(project-state)을 먼저 발행하고, 가장 성숙한 3개 엔진(EvalVault T2 → reverra-gate T3 → ai-tool-suite)을 AI Change Certification MVP로 잇고, 미성숙 레포를 domain pack/optimizer substrate/공용 계약 seed로 정리**한다. 새 아키텍처 발명이 아니라 코드에 반복된 패턴의 표준화·발행.
### 0.2 의존 척추 (critical path) — 무엇이 무엇을 막나
- **C1 evidence-contract (EPIC-001)** = 보편 차단자. GWS가 canonical seed, SO `ClaimRef`·LRV `to_evidence_ref`·RG `AuditEvidence`가 mirror. C1 없이 GWS/LRV/verbera/aia의 EvidenceRef emit·MVP의 reference integrity 불가.
- **S1 project-state** = 두 번째 보편물. **12개 레포 전부 발행**(Phase 0에 schema skeleton + project-state.json *초안*, Q2에 v0.1.0 schema 정식 발행과 12 레포 정식 발행 완료 — §0.7-3 참조). S1 없이는 SO/ATS의 두 control plane 분리가 코드 수준에서 강제 불가.
- **C2(+Evaluation Annex) → C3(decision-contract) → MVP(EPIC-002)**: EvalVault RegressionGateReport(T2 어휘) → reverra-gate GateDecision(C3, source hash) → ATS DecisionArtifact(gate hash) → CertificationReport(bundle hash). C2/C3는 별도 패키지.
- **C4 eval-stats**는 **AHO 재구성(EPIC-003)** 에 종속(run_single_task stub 제거·contracts↔runtime 통합·테스트 30+·fallback 통일 선행).
- **PromptOptimizer(EPIC-004, Q3)** 는 C1/C2/C3/C4 + AHO + 3 엔진 wiring **모두**에 종속 → **가장 늦은 노드**.
- **verbera GraphStore 단일화(EPIC-005, Q3)** 는 C1 emit 의존(EvidenceRef mirror adapter는 Q3W3) + EPIC-001 발행 선행이나 EPIC-004와 **독립 병렬**(§16 의존 그래프). PO/MVP를 차단하지 않으며 Q3 capacity의 별도 슬롯.
- **AIA classification runtime 통합(EPIC-006, Q2 병렬)** 은 EPIC-001/002와 병렬 가능 — C1·C2 정합은 EPIC-001 발행 후 mirror로 합류.
### 0.3 분기별 실행 골격 (계획들의 합의)
- **Phase 0(이번 주, §17 7개 액션 + 본문 합의):** ① solution-platform 메타 레포 생성(README, ADR 0001-0008 skeleton, integration skeleton) / ② evidenceops-contracts 생성(C1 SPEC + S1 schema skeleton) / ③ 9개 전략결정 단일 문서(`decisions/0001-strategic-questions.md`, §0.7-8) / ④ **자산경계 4종**(asset-boundary/brand-usage/oss-policy/repo-ownership) 초안 + Bespin 책임자 합의절차 시작 / ⑤ **C1 field diff matrix** 작성(GWS canonical seed↔SO/LRV/RG/ATS) / ⑥ AHO runner stub 제거 PR 착수(`run_single_task` None 제거 + HostRunner Protocol + FakeHostRunner 최소판) / ⑦ AIA "LLM beam search primary" ADR 작성. **부가**(본문 합의, §17 7개와 병행): reverra-gate mock HMAC production 차단 startup-fail 구현(P0/P1, Appendix F#17) · **12 레포 S1 schema skeleton + project-state.json 초안 발행**(skeleton 단계, v0.1.0 정식은 Q2) · SO STATUS:proposal 4건(`contracts/change_differential.py`·`harness_run_evidence.py`·`engine/evidence_normalizer.py`·`engine/harness_registry.py`) owner 지정·confirmed 전환.
- **Q2 (시점별 동시 active ≤3 준수, §19 Capacity Rule):**
  - **W1:** EPIC-001(C1 v0.1.0 발행 본작업, Phase0+W1) · SO C2 consumer 전환 착수 · EvalVault C2 annex schema 합의 — active 3.
  - **W2-W4:** EPIC-002(MVP, W2-5) + EPIC-003(AHO 재구성, W3-4 병렬) + EPIC-006(AIA runtime 통합, Q2 병렬) — 시점에 따라 active 2~3.
  - **W5:** EPIC-002 완료 · EvalVault 보험 pack 분리 착수 — active 2.
  - **상시:** S1 v0.1.0 schema 정식 발행 + 12 레포 정식 발행 완료(Phase 0 skeleton 승격) · offline gate 기본 통과 · production HMAC enforcement DoD 충족.
- **Q3:** C3/C4 발행 + EPIC-004(PromptOptimizer 1 cycle, 4주) + **EPIC-005(verbera GraphStore 단일화, 3주, 병렬)** + LRV 스크립트층 흡수 + reverra-lab 3-way 분할(자산경계 합의 후) + Operator Console skeleton. **동시 active ≤3:** EPIC-004와 EPIC-005를 병렬 슬롯으로 두고 LRV 흡수·reverra-lab 분할은 *작은 작업*으로 그 사이 swap. 분기 중간 추가 금지(§19).
- **Q4:** C5(ko-text)/C6(llm-rest)/C7(authority-tiers) 추출 + EvalVault 도메인 pack 분리 완료 + GWS 영속화 + ATS 정책 외부화 + 프론트 typed client + Release Stage 2/3 준비.
### 0.4 레포별 처리결정 한 장 맵
| 레이어 | 레포 | 결정 | 핵심 한 줄 |
|---|---|---|---|
| Contracts | evidenceops-contracts | 신규 | C1~C7+S1 단일 발행처(OSS 후보) |
| Contracts/Meta | solution-platform | 신규 | ADR·통합테스트·MVP·거버넌스 메타 레포 |
| Platform | solution-orchestrator | 유지·강화 | dev-time CP#1; durability 구현·S1 채택·proposal owner |
| Platform | EvalVault | 유지·정돈 | T2 hub; 보험 pack 분리·C2 annex·promote 금지 |
| Platform | reverra-gate | 유지·강화 | T3 gate; C3 reference integrity·mock HMAC 차단·CLI 분해 |
| Platform | ai-tool-suite | 유지·강화 | runtime CP#2; DecisionArtifact/CertificationReport·S1·정책 외부화 |
| Platform | llm-research-vault | 유지·집약 | 스크립트층 흡수·opensearch-py 통일·C1 provenance mirror |
| Platform | PromptOptimizer | 신규 구현 | verifier-driven only; C1~C4+AHO 의존 |
| Platform | ai-agent-harness-optimization | 재구성 | C4 seed; stub 제거·contracts 통합·테스트 |
| Applications | verbera | 유지·집약 | GraphStore 단일화(RetrievalQuerySpec)·SQL 파라미터화 |
| Applications | grounded-workspace-os | 유지·집약 | C1 canonical seed·OAuth/세션 영속화 |
| Applications | aia-classification-design | 통합·정리 | LLM beam search primary·stub 제거·taxonomy single source |
| Applications | aia-awesome-novel-studio | 유지·정돈 | Eval pack; regression_gate 분해·deps 선언·C4/C5 seed |
| Applications | reverra-lab | 분할 | scan(Option B D5-only)/reader(auth)/tools(deslop→PO verifier). S1 단위: 분할 전 1개, 분할 완료 후 scan/reader/tools 각 1개씩 3개(총 발행 단위 12→14, §0.7-5) |
### 0.5 공용 계약 seed 기여 맵
- **C1**: GWS(canonical seed) ← LRV·SO·RG·verbera·aia mirror.
- **C2/C6**: SO `contracts/`(OSS-추출 설계) seed.
- **C3**: ATS `packages/artifacts/`(`DecisionArtifact`/`ConflictReport` — conservative resolution `rollback>needs-human>hold>promote` 기구현) + reverra-gate `core/decision.decide_outcome`(`DecisionOutcome.{PROMOTE,HOLD,ROLLBACK}`) seed.
- **C4 eval-stats**: AHO seed(선행 정비) + ANS `stats.py`·aia `statistics.py` 기여.
- **C5 ko-text**: LRV(Nori)·aia `korean_morph`·ANS(ner/jamo/ko_numbers)·verbera analyzer.
- **C6 llm-rest**: LRV gemini plumbing·RL reader providers.
- **C7 authority-tiers**: LRV/RG/ATS/SO에 산재한 `SourceTier T0-T4`·`tier/decision_scope`·`CallerLayer` 재정의 수렴.
- **S1 project-state**: ATS `packages/registry/models.py`(`ProjectState`/`StableSurface`) seed + SO `adapters/_state_io.py` consumer side. 12(분할 후 14) 레포 전부 producer.
- **deslop_eval(reverra-lab tools) → PromptOptimizer 문체 verifier** (§0.7-7 EPIC-004 작업 목록에 명시 필요).
### 0.6 모든 계획이 강제하는 불변식
T2(passed/failed/inconclusive) ↔ T3(promote/hold/rollback) 어휘 분리 · evidence producer는 release 결정 금지 · PromptOptimizer 자동 promotion 금지 · conservative conflict(rollback>needs-human>hold>promote) · Release Stage(live write는 Stage 3 + parent_approval_id+T3+operator) · offline/closed-network gate · mirror-not-fork · 수평 import 금지 · 빅뱅 금지(발행→레포별 점진 마이그레이션, active integration ≤3).
### 0.7 정합성 조정 사항 (2026-05-28 adjusted)
v3.1 전략 및 14개 레포별 본문 계획과의 정합 검증으로 도출된 8개 미세 조정. **본문(§A/§B/§C)의 레포별 계획은 각 에이전트가 작성한 그대로 보존**한다. 아래는 §0 요약의 정합화와, 본문에 *이미 명시되어 있으나 §0 골격에서 누락되었던 항목*의 cross-reference 매트릭스다.
| # | 영역 | 조정 내용 | 근거(본문 cross-ref) | §0 반영 위치 | 본문 반영 필요? |
|---|---|---|---|---|---|
| 1 | C3·S1·C7 seed 기여 | C3 seed = ATS `packages/artifacts/`(DecisionArtifact·ConflictReport 보수해소 기구현) + reverra-gate `core/decision`. S1 seed = ATS `packages/registry/models.py`(ProjectState/StableSurface). C7 seed = LRV/RG/ATS/SO 재정의 수렴. | ai-tool-suite §2·§5 / reverra-gate §3 / evidenceops-contracts §3 C7 / SO §2 | §0.5 보강 완료 | 본문 이미 명시 — 추가 작업 없음 |
| 2 | EPIC-005 critical path | EPIC-004가 가장 늦은 노드. EPIC-005는 C1 emit 의존(Q3W3) + EPIC-004와 독립 병렬. PO/MVP 비차단. | verbera §6·§16 의존 그래프 | §0.2 보강 완료 | 본문 이미 명시 — 추가 작업 없음 |
| 3 | "12 레포 S1 발행" 단계 구분 | Phase 0 = schema skeleton + project-state.json 초안. Q2 = v0.1.0 정식 schema 발행과 12 레포 정식 발행 완료. "Phase 0 완료 기준 = 12 레포 발행"은 *skeleton 단계 발행*을 의미. | evidenceops-contracts §2(S1 schema skeleton, Phase 0) / 각 레포 시퀀싱의 S1 발행 시점 | §0.2·§0.3 보강 완료 | 본문 §11 ATS DoD·EvalVault §6 등에서 "S1 발행" 시점을 명시할 때 skeleton/v0.1.0 구분 권장 |
| 4 | Q2 동시 active ≤3 시점별 명시 | W1 = EPIC-001 + SO C2 + EvalVault annex(3) · W2-W5 = EPIC-002 + EPIC-003(W3-4) + EPIC-006(병렬)(시점에 따라 2~3) · W5 = EPIC-002 완료 + EvalVault 보험 pack(2). 카운트 위반 없음. | solution-platform §5 / 각 EPIC 시퀀싱 | §0.3 보강 완료 | 본문 이미 시점 명시 — 추가 작업 없음 |
| 5 | reverra-lab S1 발행 단위 | 분할 전 1개 S1, 분할 완료(Q3) 후 scan/reader/tools 각 1개씩. 총 발행 단위 12 → 14로 증가. | reverra-lab §4 "scan/reader/tools 단위로 S1 노출" | §0.4 보강 완료 | 본문 §17 Phase 0 액션의 "12 레포 S1 발행"이 후속 분기에 14로 자동 갱신됨을 ADR-0009로 기록 권장 |
| 6 | §17 Phase 0 액션 list 완비 | 본문은 mock HMAC 차단(reverra-gate §4 P0/P1) · 12 레포 S1 skeleton 발행 · SO STATUS:proposal 4건 정리를 Phase 0 작업으로 명시하나 §0.3 골격이 부분만 표시. | reverra-gate §4 / SO §3·§4 / 각 레포 시퀀싱 Phase 0 | §0.3 보강 완료 | 본문 이미 명시 — 추가 작업 없음 |
| 7 | EPIC-004 작업에 deslop_eval verifier wiring 명시 | reverra-lab §3·§6과 PromptOptimizer §3 verifier 정의에 등장하나 **PromptOptimizer §4 EPIC-004 작업 목록에 항목 부재**. SkillOpt wiring 표상 `deslop-writing` 스킬 1순위 파일럿 verifier. | reverra-lab §3·§6 / PromptOptimizer §3 verifier 정의 / `docs/proposals/skillopt-verifier-wiring.md` | §0.5 cross-ref 추가 | **본문 PromptOptimizer §4 EPIC-004 작업 목록에 "deslop_eval verifier wiring(reverra-lab tools)" 1줄 추가 권장**(에이전트 owner에게 PR 요청) |
| 8 | 9개 전략결정 파일명 규약 | solution-platform §2 디렉토리: `decisions/Q1-brand.md ... Q9-korean-first.md`(9파일 분리). v3.1 ADR: `decisions/0001-strategic-questions.md`(1파일 통합). | solution-platform §2 vs §17 액션 3 / v3.1 §17.1 | §0.3 액션 ③ "단일 문서" 명시 완료 | **본문 solution-platform §2 디렉토리 트리에서 9파일 분리 → 1파일(`0001-strategic-questions.md`) + 운영 결정 `0002+` 형식으로 정정 권장**(에이전트 owner에게 PR 요청) |
**조정 우선순위:**
- §0 갱신(#1-#6, #8 부분): *이 문서의 §0에 이미 반영됨*. 본문 변경 없음.
- 본문 PR 요청(#7, #8 본문 부분): 각 owner에게 1줄/디렉토리 트리 정정 요청. Phase 0 W1 안에 수렴 가능.
**조정 후 §0 신뢰도:** v3.1 전략 §0.2/§8/§16/§17/§19와 본문 14개 레포 계획의 §1-§7 모두와 정합.
### 0.8 외부 SOTA 반영 — AlphaProof Nexus (PROPOSAL, 2026-05-28)
**Source:** Tsoukalas et al., *Advancing Mathematics Research with AI-Driven Formal Proof Search* (arXiv:2605.22763, Google DeepMind 2026). Lean kernel을 ground-truth verifier로 두고 LLM은 candidate generator로만 쓰는 agent. **결과:** 9/353 open Erdős 문제 해결(문제당 *몇백 달러*), 44/492 OEIS conjecture 증명, 조합론·최적화·그래프이론·대수기하·양자광학 연구실에 배포 중. **핵심 추상:** Agent A(독립 prover subagent들이 "Ralph loop"로 Lean proof sketch를 search-and-replace 정제) → Agent D(위에 *population + Elo* evolutionary search와 *AlphaProof RL prover를 sub-goal 전용 도구로* 호출 + *sub-goal 결과 population 공유 캐시* 추가).
**적용 가능한 패턴 → 우리 컴포넌트 매핑**
| # | AlphaProof Nexus 패턴 | 우리 매핑 | 본문 cross-ref | 상태 |
|---|---|---|---|---|
| A | Population + Elo ranking + Ralph-loop search-and-replace + sub-result cache (Agent D) | **PromptOptimizer outer-loop 확장** — single-candidate 순차→population N + Elo, top survivor를 search-and-replace 변이, candidate 간 공유 prompt fragment는 EvalVault 결과를 content_hash 키로 캐시 | PO §3 (`candidate.py`/`mutation.py`/`optimizer.py`) / PO §4 EPIC-004 / §0.5 C1 canonical_id (cache key 인프라) | PROPOSAL — EPIC-004 1 cycle 실증 후 follow-up(Q3+) |
| B | Tiered verifier cascade (cheap Lean → expensive AlphaProof) | **PO dispatch 계단화**: Tier1=deslop_eval·verbera.validate(결정적, sub-second) → Tier2=EvalVault smoke fixture → Tier3=EvalVault full regression + reverra-gate GateDecision + ATS DecisionArtifact. Tier N 통과만 N+1 진입 | PO §3 (`eval_client.py`/`gate_client.py` 사이 dispatch policy 1장) / reverra-lab §6 deslop_eval → PO verifier wiring | PROPOSAL — A와 병행 가능 |
| C | Premise retrieval over formal library (lemma 재사용) | **LRV ↔ PO 통합** — PO candidate 생성 직전 LRV hybrid search(BM25 Nori + kNN + RRF + rerank)로 (a) 과거 유사 task의 CertificationReport, (b) 동일 verifier 통과 prompt fragment, (c) 관련 evidence 검색해 C1 EvidenceRef로 wrap한 뒤 generation context에 주입 | LRV §3 EPIC(스크립트층 흡수와 정합) / PO §3 (`candidate.py` retrieval seam) / C1 EvidenceRef mirror | PROPOSAL — Q3 LRV 작업과 합치면 추가 비용 0 |
| D | Cost transparency per solved problem (논문이 "$few hundred/Erdős" 공개 메트릭으로 사용) | **CertificationReport에 `cost_estimate` 블록 추가** — LLM token cost(provider별 prompt/completion), retrieval cost(LRV OpenSearch query 수), gate cost(RG HMAC audit 수·ATS 정규화), total + per-stage breakdown. Stage 3 승인 기준에 비용 임계 추가 가능 | solution-platform §3 산출물(`certification-report.json`) / §6 EPIC-002 DoD / §19 Integration Capacity Rule | PROPOSAL — additive minor (§19 patch+1 repo 승인) |
| E | Verifier = ground-truth authority, LLM = candidate only (Lean kernel 외 자기평가 불신) | **§5 권위 사슬·§8 C3 Literal lock 설계의 외부 검증** — 본문 변경 없음. SOTA 결과로 우리 설계 철학(T2/T3 분리, evidence producer는 release 결정 금지, PO 자동 promotion 금지, C3 Reference Integrity hash 강제)이 외부에서 입증됨을 ADR로 기록 | §5 권위 / §8 C3 / PO §2 불변식 / reverra-gate §2 Reference Integrity | DESIGN 검증 — ADR-0010 권장(본문 변경 0) |
**권장 착수 순서:** **E(즉시 ADR-0010 작성, 1시간)** → **D(EPIC-002 MVP 완료 후 additive minor, Q2W5+)** → **C(Q3 LRV 스크립트층 흡수와 합치기)** → **A·B(Q3 EPIC-004 1 cycle 실증 직후 follow-up EPIC)**. 각 항목은 task-bank regression으로 before/after 측정 후 EPIC화 — proposal §5(자기평가 이득=0 회피, held-out 강제)와 정합.
**비차단성·정합성:**
- 본 5건은 모두 **추가 작업**이며 v3.1 critical path(C1 → S1 → C2/C3 → EPIC-002 MVP → EPIC-004 PO)를 차단하지 않는다.
- §19 Integration Capacity Rule 준수: A·B는 EPIC-004 follow-up 슬롯, C는 LRV EPIC과 합산, D는 EPIC-002 minor 확장, E는 문서 0.
- §15.6 Offline gate, mirror-not-fork, 권위 어휘 불변식 모두 보존.
**연동 효과(보너스):** A의 sub-result cache는 C1 canonical_id를 cache key로 그대로 사용 → §0.5의 "C1 = 보편 차단자" 가치를 한 번 더 회수. B의 tier 분할은 §15 Evaluation Gate가 요구하는 통계 엄밀성(pair 수·CI·correction)을 expensive tier에 집중시켜 비용 효율을 통계 효율로 환원. C의 LRV 주입은 GWS C1 canonical seed → PO candidate context까지 evidence chain을 1차선으로 연결.
### 0.9 외부 SOTA 반영 — Epicure (PROPOSAL, 2026-05-28)
**Source:** Radzikowski & Chen, *Epicure: Navigating the Emergent Geometry of Food Ingredient Embeddings* (arXiv:2605.22391, KAIKAKU.AI 2026). 4.14M multilingual recipe 코퍼스 → 1,790 canonical ingredient + 3 sibling Metapath2Vec 임베딩(walk-schema만 다름, 나머지 동일)으로 *chemistry-vs-recipe-context*를 조절 가능한 design axis로 노출. **핵심 추상:** ① **Sibling embeddings at controlled mixing**(Cooc/Core/Chem — 동일 hyperparam, walk 템플릿만 다름), ② **LLM-augmented canonicalisation pipeline**(~200k raw → 1,790 canonical, Claude 결정적 디코딩 + Gemini 임베딩 클러스터링 + manual 큐레이션), ③ **Dual operator family on same 300-D embedding**(nearest-neighbour/mode-membership lookup + SLERP direction arithmetic with continuous angle θ), ④ **Multi-seed-stable FastICA + GMM mode atlas**(Hungarian matching, split-half cosine > 0.6, BIC-selected K, 150–200 named modes per model, coherence 5–6× random baseline), ⑤ **4-strata stratified direction quality**(probe를 학습신호로부터 점진 decouple — baked-in CF → held-out CF → 외부 nutrient → cuisine). §0.8의 verifier 중심 패턴과 *상보적*으로 **표현 공간(embedding)** 중심 패턴.
**적용 가능한 패턴 → 우리 컴포넌트 매핑**
| # | Epicure 패턴 | 우리 매핑 | 본문 cross-ref | 상태 |
|---|---|---|---|---|
| F | Sibling embeddings at controlled mixing (walk-schema만 다름) | **LRV**: pure-semantic vs. provenance-graph(C1 EvidenceRef edges) vs. mixed 3 sibling을 retrieval engine에 노출 — provenance-vs-semantic을 조절 가능 axis로 / **verbera**: 이미 InMemory vs Postgres backend가 sibling 구조 — EPIC-005 표면(`RetrievalQuerySpec`)을 일반화해 향후 typed-edge sibling 추가 여지 / **PO**: §0.8 #A population을 *1축*이 아니라 sibling(verifier 가중 다름)으로 분기 | LRV §2/§3 / verbera §2/§3 EPIC-005 / PO §3 (`optimizer.py`) / §0.8 #A 확장 | PROPOSAL — §0.8 #A 연동 |
| G | LLM-augmented canonicalisation pipeline (Claude + 임베딩 클러스터링 + manual) | **aia-classification**: census/본문이 지적한 *taxonomy 3중 정의*(`data.LabelPath` / `taxonomy_loader` / `graph.py`)를 single canonical authority로 통합(EPIC-006 §11 DoD "taxonomy single source"와 동일) / **ANS**: STT `contracts.py` L0–L10 한국어 hardcoded prompt + `regression_gate._extract_semantic_criteria` 한국어 criteria를 데이터·canonical로 외부화(C5 ko-text seed 강화) / **LRV**: evidence collection vocabulary canonical | aia §3 EPIC-006 (taxonomy single source) / ANS §2 C5 seed·§3 정돈 / LRV §3 / §0.5 C5 ko-text | PROPOSAL — Q2(ANS deps) / Q2 EPIC-006 / Q3 LRV와 합산 |
| H | SLERP direction arithmetic (continuous angle θ, supervised pole + emergent mode pole) | **LRV**: SourceTier(T0–T4)·permission_scope를 supervised pole로 두고 retrieval query를 회전("T0 canonical 방향으로 30°") / **aia**: 대→중→소 hard cascade beam을 supervised pole 간 SLERP soft traverse로 보완 / **PO**: random mutation → 방향성 SLERP mutation(§0.8 #A의 search-and-replace를 임베딩 공간 회전으로 일반화) | LRV §3 retrieval / aia §3 EPIC-006 / PO §3 (`mutation.py`) / §0.8 #A | PROPOSAL — §0.8 #A·#C와 병행 |
| I | Multi-seed-stable FastICA + GMM mode atlas (150–200 named modes, Claude 라벨링) | **LRV**: 우리 evidence corpus에 적용 → 이름 붙은 latent topic mode 자동 발견, mode-membership을 **§0.8 #C premise retrieval의 retrieval 입력으로** 사용(top-K cosine 대비 한 단계 풍부) / **PO**: 누적 candidate 임베딩에 적용 → "task-잘-통하는 prompt mode" 자동 발견 후 mode pole을 SLERP target으로 재투입(self-improvement 루프 — **held-out 강제 §15 Evaluation Gate**) | LRV §3 retrieval / PO §3 (`candidate.py`) / §0.8 #A·#C | PROPOSAL — §0.8 #C 확장 |
| J | 4-strata stratified direction quality probe (학습신호 decoupling 단계별 분리) | **EvalVault**: C2 Evaluation Annex에 *probe strata 메타데이터 옵션* 추가 — baked-in vs held-out vs external vs categorical를 보고 시 분리(§15 Evaluation Gate의 metric direction 필드 확장) / **aia·ANS**: 회귀 평가 신뢰도 — beam search/통계 진단을 4-strata로 reporting하여 분기별 leakage 검출 | EvalVault §2 produces·§5 DoD / aia §3 / ANS §3 / §15 Evaluation Gate | PROPOSAL — additive minor (§19 patch+1 repo 승인) |
**권장 착수 순서:** **J(EvalVault C2 annex stratum 옵션, additive minor, EPIC-002 MVP 이후 Q2W5+)** → **G(aia EPIC-006 taxonomy single source와 합쳐 진행 + ANS C5 seed 분리와 합산, Q2 병렬)** → **F·H·I(Q3 LRV 스크립트층 흡수·§0.8 #A·#C와 같은 EPIC 묶음)**. 각 항목은 taskbank regression(LRV retrieval recall@k/nDCG, PO candidate 채택률, aia classification accuracy)으로 before/after 측정 후 EPIC화.
**비차단성·정합성:**
- 본 5건은 모두 **추가 작업**이며 v3.1 critical path(C1 → S1 → C2/C3 → EPIC-002 MVP → EPIC-004 PO) 비차단.
- §19 Integration Capacity Rule 준수: J는 EvalVault 단독 minor, G는 aia EPIC-006/ANS 정돈 슬롯에 합산, F·H·I는 LRV EPIC + §0.8 묶음에 합산. 신규 active integration 0 증가.
- §15 Evaluation Gate held-out 강제(F·I) — Epicure §5 limitation의 "self-generated 이득=0 회피" 원칙과 일치.
- 권위 어휘 분리 보존 — LRV/aia/ANS는 evidence·metric만 발행(§5), release decision 금지.
**§0.8과의 결합·비교:**
- **§0.8 (AlphaProof Nexus)** = *verifier-driven candidate search* 중심. PO outer-loop와 verifier 사슬 강화(A/B/C/D/E).
- **§0.9 (Epicure)** = *embedding geometry + canonicalisation* 중심. LRV 표현 공간과 vocabulary 정합 강화(F/G/H/I/J).
- 연결고리: **F·H는 §0.8 #A**(population·mutation)를, **I는 §0.8 #C**(premise retrieval)를, **J는 §0.8 #B·#D**(verifier·cost)를 *각각 한 단계 풍부화*. 두 §은 별개 EPIC 묶음이 아니라 *동일 Q3 EPIC 안에서 보완적으로 통합 가능*.
- 공통 메타원칙: **외부 SOTA가 우리 §5 권위 분리·§15 게이트 설계를 외부에서 입증** — §0.8 #E와 동일 ADR-0010 근거 강화.
### 0.10 외부 SOTA 반영 — AutoScientists (PROPOSAL, 2026-05-28)
**Source:** *AutoScientists — Self-Organizing Agent Teams for Long-Running Scientific Experimentation* (openscientist.ai 2026). **n개 long-running agent**가 *중앙 orchestrator 없이* single shared state **S = {champion p\*, log L, structured forum F, per-team queues Qk, cross-team readable dead-end registries Dk}** 를 통해 자율 조율. **두 phase 교대**: discussion(팀 구성 + 제안 비평/필터링) ↔ execution(팀별 병렬 실험). **Stagnation 감지 시 자동 re-discussion + 재조직**. **Analyst** 역할이 L+F를 읽어 **effect size로 제안 랭킹**, Qk에 기록, hypothesis 문서 + dead-end registry 소유. **결과:** BioML-Bench 74.4%(+8.33%), GPT training 1.9× 가속, ProteinGym ACE2–Spike +12.5% Spearman (217 assay 평균 +6.5%). **§0.8/§0.9와 상보**: verifier 사슬(§0.8)·embedding geometry(§0.9)에 *agent 자율 조직·champion 추적·실패 경험 누적* 차원 추가.
**적용 가능한 패턴 → 우리 컴포넌트 매핑**
| # | AutoScientists 패턴 | 우리 매핑 | 본문 cross-ref | 상태 |
|---|---|---|---|---|
| K | Champion `p*` + dead-end registry `Dk` (cross-team readable, 누적) | **PO outer-loop에 명시적 champion + C1 EvidenceRef로 wrap한 dead-end artifact**. dead-end key = (verifier_id, content_hash), 동일 시도 즉시 skip(LRU eviction 없음). §0.9 #I mode atlas가 "tried-and-failed mode" vs "promising mode" 분리 표현 | PO §3 (`optimizer.py`·`candidate.py`·`mutation.py`) / §0.5 C1 canonical_id (cache key 인프라) / §0.8 #A 강화 / §0.9 #I 라벨 확장 | PROPOSAL — §0.8 #A 직접 확장 |
| L | Pre-execution discussion phase (peer-critique before any verifier) | **Tier 0 verifier 신설** — judge agent가 hypothesis quality를 peer-critique, 통과만 deslop_eval(Tier 1) 진입. SkillsBench self-generated 이득=0(§0.8 #A 리스크) 추가 방어선. SO `engine/judge.py` 추상화를 PO 진입 단계로 재사용 | PO §3 (`runner.py` 앞단 dispatch policy) / §0.8 #B (3→4 tier 확장) / SO §2 권위 어휘 `judged` | PROPOSAL — §0.8 #B 직접 확장 |
| M | Structured forum `F` + Analyst (effect-size 랭킹·hypothesis 소유·dead-end registry 운영) | **SO + AHO 통합** — F = cross-repo 가시 forum artifact(제안·비평·통계 누적), Analyst = AHO C4 stats(effect size/Cohen's d/bootstrap CI)를 입력으로 candidate 랭킹. AHO C4 승격(§16 EPIC-003) 후 AHO를 **Analyst service**로 노출 | SO §2 / AHO §2·§3 EPIC-003 / §0.8 #D cost_estimate(forum에 비용 메트릭 포함) / §0.7 #3 S1 발행 단계 | PROPOSAL — EPIC-003 직후 |
| N | Stagnation → re-discussion + reorganization 자동 트리거 | **PO**: champion effect size CI가 N cycle 0 포함 + dead-end 비율 임계 초과 시 sibling diversification 자동 시작(§0.9 #F sibling을 적응 분기). **ATS**: adapter DecisionArtifact가 `needs_human` 수렴 시 SO에 reorganization 신호 발행(다른 harness로 dispatch 재라우팅). 메커니즘 = C4 통계 그대로 활용 | PO §3 (`optimizer.py`) / §0.9 #F 적응 트리거 / ATS §3 (`decision_service`) / §15 Evaluation Gate | PROPOSAL — Q3 PO·ATS 안정화 후 |
| O | Long-running agent state checkpoint (cycle 간 working memory + dead-end view 보존) | **agent runtime은 도입 안 함** — solution-platform `agents/SPEC.md`에 **`session-state` schema 추가**(C1-compliant artifact, SessionId 참조로 이전 cycle 자동 로드). 안티패턴 "SPEC 사후작성"(§17 Phase 0) 방어와 정합. Claude Code 세션·자동 스케줄 작업 양쪽에 동일 표면 | solution-platform §2 (`agents/SPEC.md`) / §17 Phase 0 (agent SPEC 선행 작성 원칙) | PROPOSAL — solution-platform Phase 0과 합산 |
**권장 착수 순서:** **K(즉시, §0.8 #A EPIC-004 follow-up에 직접 합산)** → **L(K와 같은 dispatch policy 1장에 Tier 0 1줄 추가)** → **O(solution-platform Phase 0 `agents/SPEC.md` 작성 시 함께, 작은 작업)** → **N(Q3 PO·ATS 안정화 후 stagnation detector)** → **M(AHO C4 승격 §16 EPIC-003 직후, AHO를 Analyst service로 노출)**. 각 항목 task-bank regression(PO candidate 채택률·dead-end hit rate·effect size CI 변화)으로 effect 측정 후 EPIC화.
**비차단성·정합성:**
- 본 5건은 모두 **추가 작업**, v3.1 critical path(C1 → S1 → C2/C3 → EPIC-002 MVP → EPIC-004 PO) 비차단.
- §19 Integration Capacity Rule 준수: K·L·N은 **PO 1개 EPIC에 합산**(§0.8 #A follow-up), M은 **AHO 1개 EPIC**(§16 EPIC-003 직후 minor), O는 **solution-platform Phase 0**. 신규 active integration **0 증가**.
- §15.6 Offline gate, mirror-not-fork, 권위 어휘 불변식 보존.
**선택적 적용 — 명시적 채택 제외:**
- **"중앙 orchestrator 없음"** 원칙은 §4 *two-control-plane 명시 분리*(SO dev-time + ATS runtime) 권위 분담과 **정면 충돌** → **제외**. AutoScientists 패턴은 CP 안의 하위 루프(PO outer-loop, AHO Analyst, SO judge)에만 적용. **meta-level self-organization 금지**(§19 거버넌스·rollback 책임 owner 위반).
- **n long-running agent runtime**은 인프라 비용·복잡도 ↑ → **O는 runtime 도입이 아니라 session-state artifact 포맷만 채택**(작은 surface, C1 정합).
**§0.8·§0.9와의 결합·비교:**
- **§0.8 (AlphaProof Nexus)** = *verifier-driven candidate search* 중심
- **§0.9 (Epicure)** = *embedding geometry + canonicalisation* 중심
- **§0.10 (AutoScientists)** = *agent 자율 조직 + champion 추적 + 실패 경험 누적* 중심
- 연결: **K는 §0.8 #A + §0.9 #I**(dead-end가 mode atlas 라벨에 합류), **L은 §0.8 #B**(3→4 tier 확장), **M은 §0.8 #D**(forum이 cost 통계 누적·랭킹 신호), **N은 §0.9 #F**(sibling 적응 트리거), **O는 solution-platform 거버넌스 표면 확장**.
- 공통 메타원칙: **§0.8 #E ADR-0010(verifier-as-authority)에 SOTA 3건 외부 입증 인용 추가** — verifier 권위 분리·champion 외부 평가·계약 hash 강제가 세 paper 모두에서 핵심으로 등장.
**보너스 연동:** K의 dead-end artifact는 §0.8 #C(LRV ↔ PO premise retrieval)의 retrieval 입력에 자동 합류 — "이 mode는 이미 verifier_X에서 실패함" 메타데이터를 retrieval 시 노출해 PO가 동일 dead-end로 회귀하지 못하게 함. §0.7 #5 reverra-lab `deslop_eval`은 K의 dead-end 기록 시점에 결정적 grader로 직접 사용.
---

# A. Contracts Layer

## evidenceops-contracts (신규) — 개발 계획

### 1. 역할·목표 위치 (Contracts Layer) — solution-platform과 분리하는 이유
evidenceops-contracts는 §3 3-Layer의 최하단 **Contracts Layer**를 단독으로 소유한다. C1~C7 공용 계약 + S1 supporting schema + 언어 바인딩(Python 우선, TS 후속) + contract test + fixture + migration cookbook + version policy의 **단일 출처(canonical host)**다. §3.2 결합 규칙상 의존은 Applications→Platform→Contracts 하향만 허용되며, 이 레포는 **어떤 Platform/Application도 import하지 않는다**(deps 0, vendor import 0). 결정 §0.2-5·§6.2·Q3·Appendix F-5에 따라 solution-platform(ADR·통합테스트·에이전트 작업서·배포·거버넌스 *정책*·실행)과 물리적으로 분리한다. 근거: 계약은 §23 Q8의 **OSS 공개 후보**이므로 내부 ADR/배포 자산과 같은 레포에 두면 자산경계(§17-4) 정리 전 공개가 막히고, 계약의 안정성 요구(버전 정책·breaking-change 감시)와 메타 레포의 변경 속도가 충돌한다. solution-platform은 이 레포의 *consumer*이며 통합테스트로 계약을 검증할 뿐 계약을 호스팅하지 않는다.

### 2. 패키지 구조 (§6.2.2 구체화)
```
evidenceops-contracts/
  pyproject.toml            # package=true, deps=[] (런타임 vendor 0; dev: pytest/ruff/jsonschema/mypy/import-linter)
  packages/python/evidenceops_contracts/
    c1_evidence/    models.py (EvidenceRef, Claim, ClaimRef, NormalizedEvidence, SourceTier), canonical_id.py, __init__.py
    c2_harness/     run.py (HarnessRunRequest/Snapshot/RunEvidence, RunMode), annex.py (EvaluationRun, RegressionGateReport)
    c3_decision/    models.py (GateDecision, DecisionArtifact, ConflictReport, CertificationReport), integrity.py
    c4_eval_stats/  bootstrap.py, mcnemar.py, fdr.py, effect_size.py, power.py
    c5_ko_text/     tokenizer.py, bm25.py, jamo.py, pii.py, nori_align.py
    c6_llm_rest/    client.py (provider-neutral REST/SSE/structured JSON), offline_stub.py
    c7_authority/   tiers.py (SourceTier T0–T4, CallerLayer L2–L7, decision_scope mapping)
  schemas/          c1/evidence-ref.schema.json, claim.schema.json, normalized-evidence.schema.json
                    c2/harness-run-request.schema.json, evaluation-run.schema.json, regression-gate-report.schema.json
                    c3/gate-decision.schema.json, decision-artifact.schema.json, conflict-report.schema.json, certification-report.schema.json
                    s1/project-state.schema.json
  fixtures/         c1/{gws,so,lrv,rg,ats}/*.json  c2/...  c3/...  s1/<repo>.json  (12 repo)
  tests/            test_c1_canonical_id.py, test_c1_roundtrip.py, test_c2_annex_no_t3_vocab.py,
                    test_c3_literal_lock.py, test_c3_reference_integrity.py, test_schema_drift.py,
                    test_no_vendor_import.py, test_breaking_change_detection.py, test_offline_network_block.py
  docs/migration-cookbook/  c1.md … c7.md, s1.md, versioning-policy.md, compatibility-matrix.md
  .github/ PULL_REQUEST_TEMPLATE.md  (변경분류 patch/minor/major 필드)
```
S1 `project-state.schema.json`은 §8.S1 필드를 강제: `schema_version`, `repo{name,role,maturity,source_path}`, `capabilities[]`, `contracts{produces,consumes}`, `artifacts[]`, `entrypoints[]`, `test_status`, `risk_flags[]`, 그리고 §18.5 DoD의 현재 Stage 노출 필드. **schema-only(패키지 아님)** — 코드 바인딩 없이 JSON Schema로만 발행.

### 3. 계약별 발행 계획 (canonical seed·필드·DoD)
- **C1 evidence-contract** — seed=GWS `packages/schemas/evidence.py` EvidenceRef/Claim(§4.3 canonical). 필드: EvidenceRef{source_app, object_id, observed_at(ISO-8601 UTC), permission_scope, source_tier, content_hash, confidence∈[0,1]}, Claim{fact/inference/recommendation/uncertainty, evidence_refs|unsupported=true}. `canonical_id = sha256(canonical_json({source_app,object_id,observed_at,permission_scope,source_tier,content_hash}))`(key sort, UTF-8, NFC). v0.1.0=`canonical_id()` helper(Option B) + NormalizedEvidence export 시 evidence_id materialize. DoD(§8/§73): JSON Schema·Python binding·no vendor dep·GWS/SO/LRV/RG/ATS 3+ fixture roundtrip·unsupported claim 표현·source_tier 필수·1 consumer migration·`test_c1_canonical_id`(deterministic·동일입력→동일 id·content_hash 변경→id 변경)·C3가 C1 evidence_id 참조 integration test.
- **C2 harness-run + Evaluation Annex** — seed=SO `contracts/`(HarnessRunRequest/Snapshot/RunEvidence) + EvalVault `regression_gate_service`(annex). RunMode(dry_run/evaluation/candidate_generation/verification), `parent_approval_id` 없는 live mutation 금지, PO candidate·SO·AHO 동일 schema. Annex `evaluation-run.schema.json`/`regression-gate-report.schema.json`은 **status=passed|failed|inconclusive만, promote/hold/rollback·decision 필드 금지**(T2 권위). RegressionGateReport는 C3 GateDecision 입력일 뿐 그 자체는 release decision 아님. DoD: `test_c2_annex_no_t3_vocab`(어휘 grep)·RG mapper RegressionGateReport→ImportedEvalIR→GateDecision·C2/C3 boundary test.
- **C3 decision-contract**(C2와 별도 패키지 필수) — seed=ATS `DecisionArtifact`/`ConflictReport` + reverra-gate `decide`. **Type-level Literal 잠금**: `GateDecision.authority=Literal["T3"]`, `DecisionArtifact.producer=Literal["ai-tool-suite"]`, `ConflictReport.resolution=Literal["rollback","needs_human","hold","promote"]`(보수해소 순서 §5). **Reference Integrity**: GateDecision←RegressionGateReport{id,schema_version,content hash}+evidence_refs(C1 id); DecisionArtifact{source_gate_decision_id,hash,normalized_evidence_index,conflict_resolution_policy}; CertificationReport{change_id, eval/gate/decision ref+hash, artifact_bundle_hash}. DoD: 독립 package·Literal 잠금 test·EvalVault output schema에 GateDecision 타입 없음·각 단계 hash 보존·**hash mismatch 시 certification invalid(re-run 강제)**.
- **C4 eval-stats** — seed=AHO `compare_ab/bootstrap_ci/quality_check`. 단, §76 선행조건(pyproject·contracts runtime 통합·`run_single_task` stub 제거·테스트 30+·deterministic fake runner·scipy 미설치 fallback·sample paired benchmark) 충족 후 승격. stdlib-first + optional scipy, §5 L2 fallback 불일치 통일.
- **C5 ko-text** — seed=EVꞏAIACꞏANSꞏLRV(Nori) 수렴. kiwipiepy 싱글톤+사전 주입, 형태소 BM25, jamo 유사도, PII 마스킹, Nori alignment. 오프라인 사전 미러.
- **C6 llm-rest** — seed=LRV gemini plumbing + RL reader provider strategy. provider-neutral REST/SSE/structured JSON + offline stub. SDK lazy import.
- **C7 authority-tiers** — seed=LRV/RG/ATS/SO 재정의 수렴. T0–T4 + caller-layer L2–L7 + decision_scope 매핑 1벌.
- **S1 project-state** — producer=각 repo, consumer=SO/ATS. macOS 절대경로→repo-relative, read-only(write target 아님). DoD: SO/ATS 동일 schema validate·drift test·**12 레포 전부 발행(Phase 0 완료 기준)**. S1 없으면 두 control plane 분리가 코드 수준에서 강제 불가.

### 4. 발행 순서 (L1→L6→L2→L4→L3→L5 정합) 및 Phase 배치
§5 추출 순서(레버리지×안전)에 정렬: **L1=C1 → L6=C2 → L2=C4 → L4=C6 → L3=C5 → L5=C7**(C3는 C2 직후 별도 발행, S1은 C1과 병행). 시점: **Phase 0**(§17) — 레포 생성 + C1 SPEC + S1 schema skeleton + C1 field diff matrix(GWS/SO/LRV/RG/ATS). **Q2** — EPIC-001로 C1 v0.1.0 정식 발행(2주, Phase0+Q2W1) → C2 core+annex → C3. **Q3** — C4 승격(AHO 선행조건 충족 후, EPIC-003 의존) + C6. **Q4** — C5 + C7. 모든 발행은 *발행→1 레포 마이그레이션→계약 테스트* 단위, 빅뱅 금지(안티패턴).

### 5. Contract Governance (§19)
변경분류 **patch/minor/major**. 승인규칙: patch(contracts owner+1 repo) / minor(+2 repo) / major(+Platform owner+repo owners, migration plan+deprecation window). 원칙: required field 추가·enum 제거·source tier 의미 변경=major; `schema_version` 없는 artifact invalid; deprecated field 최소 1 minor 유지. 산출물 DoD: `docs/migration-cookbook/versioning-policy.md`, C1~C7+S1 각 cookbook, `compatibility-matrix.md`, `.github/PULL_REQUEST_TEMPLATE.md`에 변경분류 필드, 그리고 `tests/test_breaking_change_detection.py` — 직전 릴리스 schema와 diff하여 required 추가/enum 제거/tier 의미 변경 시 major 미표기면 CI fail.

### 6. DoD
EPIC-001 DoD(§122): package 생성·GWS/SO/LRV/RG/ATS diff matrix·canonical_id Python model·JSON Schema export·fixture roundtrip·canonical_id deterministic test·첫 consumer migration·cookbook. 추가로 §15 게이트: Contract Gate(schema validate·model roundtrip·canonical serialization·backward compat·schema_version 필수), Evidence Gate(evidence_refs|unsupported·confidence∈[0,1]·source_tier·permission_scope·content_hash canonical·evidence_id deterministic). `test_no_vendor_import.py`(import-linter+grep로 deps 0 강제)·`test_schema_drift.py`(SO/ATS S1 동일 schema)·§15.6 `test_offline_network_block.py`(unit CI가 public internet 없이 통과).

### 7. 의존성 (mirror-not-fork)
계약 consumer/migrator(§4.3·§11): **C1**→GWS(seed·adapter)·SO(`ClaimRef` mirror 폐기→import)·LRV(`to_evidence_ref`)·RG(`AuditEvidence`)·ATS. **C2**→SO·AHO·EvalVault(annex 발행)·PO(candidate). **C3**→ATS(DecisionArtifact)·RG(GateDecision·Reference Integrity)·EvalVault(GateDecision 타입 *없음* 검증). **C4**→AHO·EvalVault·AIAC·ANS·RG. **C5**→EV·AIAC·ANS·VB·LRV. **C6**→LRV·RG·RL·EV·GWS. **S1**→12 레포 전부 producer, SO·ATS consumer. 각 레포는 내부 복사본 금지·adapter로 mapping만(§3.2). 선행: Phase0→C1→C2→C3(EPIC-002 의존). 병렬: S1 12레포 발행, EPIC-003(AHO→C4), EPIC-006(AIA).

### 8. 리스크·완화
(1) **canonical_id 비결정성**(NFC/key sort/timezone 누락) → `test_c1_canonical_id` 황금 fixture + content_hash 변경→id 변경 단언. (2) **C2/C3 어휘 누수**(T2가 promote 반환=breaking) → annex 어휘 grep test + C3 Literal 잠금. (3) **vendor import 잠입** → import-linter+grep CI 차단. (4) **계약 과잉설계**(안티패턴) → v0.1.0 최소 발행, Option B helper 우선. (5) **동시 active integration >3**(§19 Capacity) → WIP board ≤3, Phase별 scope freeze. (6) **OSS 자산경계 미정** 공개 차단 → §17-4 자산경계 합의 전까지 private, 코드 구조만 OSS 가능하게(deps 0) 유지.

---

## solution-platform (신규) — 개발 계획

### 1. 역할·목표 위치 + evidenceops-contracts와의 분리 근거

solution-platform은 EvidenceOps Platform의 **메타 레포(중심 레포 #1)**다. 코드 자산이 아니라 **시스템 통합·운영 의사결정**을 담는다: (1) **ADR**(아키텍처 결정 기록 0001-0008), (2) **통합테스트**(여러 mature 엔진을 가로지르는 cross-repo integration test + fixtures), (3) **에이전트 작업서**(EPIC SPEC, EPIC-001~006 task 정의), (4) **배포 자산**(docker-compose.local, closed-network profile, helm), (5) **문서**(거버넌스·release stage·ownership), (6) **거버넌스 정책**(Contract Governance, Integration Capacity Rule). 즉 §6.2.1의 "ADR·통합테스트·에이전트 작업서·배포·문서·거버넌스 정책"을 호스팅한다.

**evidenceops-contracts와의 분리 근거(§0.2-5, §6, §23-Q8):** 계약(C1~C7+S1: JSON Schema + Python/TS 바인딩 + contract test + fixtures + migration cookbook + version policy)은 **OSS 공개 후보**(자산 경계 합의 후 공개)이므로 vendor-neutral·내부 정보 없는 청정 상태를 유지해야 한다. 반면 solution-platform은 내부 ADR·배포 시크릿·운영 거버넌스·repo-ownership 등 **내부 자산**을 담는다. 둘을 합치면 OSS 공개가 불가능해지고, 계약의 안정성(외부 의존성 SLA)이 내부 운영 변경에 오염된다. 따라서 분리는 불변 원칙이다(§3.2 하향 의존만, Contracts→Platform 역방향 금지).

### 2. 디렉터리 구조 (§6.2.1 구체화)

```
solution-platform/
  README.md                         # 메타 레포 목적, 레이어맵, Stage 모델 요약
  adr/
    0001-internal-identity-evidenceops.md
    0002-polyrepo-two-central-repos.md
    0003-contracts-host-separation.md          # solution-platform↔evidenceops-contracts
    0004-two-control-planes-not-merged.md       # SO(dev) vs ATS(runtime)
    0005-c1-evidence-contract-first.md          # canonical_id/evidence_id 규칙
    0006-c3-decision-contract-separation.md     # Reference Integrity
    0007-release-stage-model.md                 # Stage 0→3, live write Stage3-only
    0008-offline-closed-network-gate.md         # §15.6
  decisions/                        # 9개 전략결정 1파일 통합 + 운영 결정 0002+
    0001-strategic-questions.md       # Q1~Q9 전략결정 통합(§0.7-8, v3.1 §17.1)
    0002-*.md                         # 그 외 운영 결정
  integration/
    fixtures/                       # change-spec.yaml, eval smoke fixture, RegressionGateReport 샘플
    tests/
      test_evalvault_to_reverra_gate.py
      test_reverra_gate_to_ai_tool_suite.py
      test_certification_pipeline_e2e.py
      test_offline_network_block.py
  deploy/
    docker-compose.local/           # EvalVault/reverra-gate/ATS 로컬 통합 스택
    closed-network/                 # 폐쇄망 profile(HMAC enforce·audit·retention)
    helm/                           # Q4 클러스터 배포 차트(skeleton)
  agents/
    SPEC.md                         # 에이전트 작업 규약·DoD 템플릿·완료 기준
    tasks/
      EPIC-001-c1-evidence-contract.md
      EPIC-002-ai-change-certification-mvp.md
      ... EPIC-003 ~ EPIC-006
  docs/
    governance/contract-governance.md, integration-capacity-rule.md
    governance/repo-ownership.md
    release/release-stage-model.md
    asset-boundary/asset-boundary.md, brand-usage.md, oss-policy.md
  cli/                              # `solution certify` 진입점(메타 CLI)
```

### 3. 첫 MVP 통합 — AI Change Certification Pipeline (§9)

**흐름:** `change-spec.yaml → EvalVault(T2: passed|failed|inconclusive) → reverra-gate(T3: promote|hold|rollback) → ai-tool-suite(DecisionArtifact 정규화) → certification report`. 초기 포함: EvalVault·reverra-gate·ai-tool-suite·solution-platform integration test·S1(read-only). 초기 제외: Operator Console·PromptOptimizer full loop·Grounded Agent Runtime·Domain Pack marketplace.

**`solution certify` CLI 명세:**
```
solution certify --repo <r> --change <change-spec.yaml> \
                 --eval-profile <p> --gate-profile <p> --dry-run
```
`--dry-run`이 **default**(Stage 0). EvalVault smoke fixture로 RegressionGateReport(T3 어휘 금지) 생성 → reverra-gate RG mapper가 `RegressionGateReport → ImportedEvalIR → GateDecision`(source RegressionGateReport의 {id, schema_version, content hash} 보존) → ai-tool-suite가 GateDecision hash 참조한 DecisionArtifact 정규화 → CertificationReport({change_id, eval/gate/decision artifact ref+hash, artifact_bundle_hash}).

**산출(`artifacts/certifications/<change_id>/`):** `certification-report.json`, `certification-report.md`, `decision-artifact.json`, `gate-decision.json`, `normalized-evidence.json`, `operator-summary.md`. 모든 artifact는 schema validate 통과, promote/hold/rollback 중 1개만 명확히 출력.

**Integration test 목록:**
- `test_evalvault_to_reverra_gate.py` — RegressionGateReport→ImportedEvalIR→GateDecision 변환, T2 출력에 T3 어휘 없음 검증.
- `test_reverra_gate_to_ai_tool_suite.py` — GateDecision→DecisionArtifact, `source_gate_decision_id` + gate hash 보존, ConflictReport conservative 순서(rollback>needs_human>hold>promote).
- `test_certification_pipeline_e2e.py` — change-spec → CertificationReport 전체, `artifact_bundle_hash` 재현 가능, 동일 입력→동일 bundle hash.
- `test_offline_network_block.py` — socket 차단 하에 `solution certify --dry-run`이 외부 호출 없이 통과(§15.6).

**Reference integrity / bundle hash 검증:** 각 단계 artifact가 직전 단계 산출의 content hash를 참조하고, hash mismatch 시 certification invalid → re-run 강제(§8 C3 DoD). bundle hash는 전체 artifact 집합의 결정적 해시로, CI offline 재현에서 동일해야 한다.

### 4. 거버넌스 문서 (§19, §18.5)

- **Contract Governance:** 변경 분류 patch/minor/major. 승인 — patch(contracts owner+1 repo), minor(+2 repo), major(+Platform owner+repo owners, migration plan + deprecation window). 원칙: required field 추가·enum 제거·source tier 의미 변경 = major; schema_version 없는 artifact invalid; deprecated field 최소 1 minor 유지. 산출: versioning-policy, migration-cookbook(C1~C7+S1), compatibility matrix, breaking-change detection test, PR template 변경분류 필드.
- **Integration Capacity Rule:** 팀 capacity 20~30%만 통합, 동시 active integration 레포 ≤3, P0/P1 외 분기 중 추가 금지, EPIC당 owner+reviewer+fallback, 완료는 "작동 데모" 또는 "계약 발행" 단위. WIP board ≤3, 분기 scope freeze, capacity 회고.
- **Release Stage Model(§18.5):** Stage 0(Dry-run, write 금지) / 1(Read-only integration) / 2(Sandbox write) / 3(Production gated write: parent_approval_id + T3 decision + operator approval). write path는 stage-aware, Stage 0/1에서 write path 미실행을 테스트로 강제, Stage 전환은 ADR 기록, 각 repo는 현재 Stage를 S1에 노출.
- **repo-ownership:** 12 레포 각각 owner/reviewer/fallback 지정(Integration Capacity Rule DoD).

### 5. 시퀀싱

- **Phase 0(이번 주, §17):** ① solution-platform 메타 레포 생성(README, ADR 0001-0008 skeleton, integration skeleton). ② 9개 전략결정 단일 문서(`decisions/0001-strategic-questions.md`). ③ 자산경계 4종(asset-boundary/brand-usage/oss-policy/repo-ownership) 초안 + 합의절차 시작. evidenceops-contracts 생성·C1 diff matrix·AHO stub 제거 PR·AIA ADR는 별도 레포 에이전트와 협업.
- **Q2(MVP):** EPIC-001 의존 위에 EPIC-002 AI Change Certification MVP 4주(Q2W2-5). `solution certify` 구현, integration test 4종, artifacts 산출, offline gate.
- **Q3:** Operator Console skeleton(§18-18: Console은 Q3+), EPIC-004 PromptOptimizer MVP / EPIC-005 verbera 병렬.
- **Q4:** helm 배포 자산 정착, Stage 1→2 전환 검토, 추가 통합.

### 6. DoD

- **EPIC-002 DoD(§16):** change spec·EvalVault smoke fixture·RegressionGateReport(T3 어휘 없음)·RG ImportedEvalIR 변환(source hash)·GateDecision(reference integrity)·ATS DecisionArtifact(gate hash)·cert report.md(bundle hash).
- **MVP DoD(§9.6):** dry-run default · 모든 artifact schema validate · promote/hold/rollback 1개 명확 출력 · markdown summary · integration test · T2/T3 불변식 검증 · CI offline 재현 · 모든 artifact reference integrity(source hash) 포함 · artifact_bundle_hash 재현 가능.
- **§15.6 Offline gate:** `test_offline_network_block.py` 존재 · default CI가 public internet 없이 통과 · live는 명시 profile 없이 미실행 · closed-network에서 `solution certify` dry-run 통과.
- **Release Stage 0→1 전환:** C1/C2/C3/S1 validate · dry-run MVP 통과 · offline gate 통과(이 3개 충족 시 Stage 0→1 전환 ADR 기록).

### 7. 의존성

solution-platform MVP는 **evidenceops-contracts의 C1 evidence-contract(evidence_id/canonical_id), C2 harness-run-contract(Evaluation Annex), C3 decision-contract(Reference Integrity), S1 project-state.schema.json 발행에 의존**한다(Phase 0→EPIC-001→EPIC-002 체인). 또한 mature 엔진 연결에 의존: **EvalVault**(T2 RegressionGateReport, regression_gate_service), **reverra-gate**(T3 GateDecision, RG mapper, Store reference integrity), **ai-tool-suite**(DecisionArtifact decision_service, conflict_service). 이 엔진들은 census상 Mature이므로 신규 구현이 아니라 계약 경계로 wiring한다. S1은 read-only consume(SO/ATS 동일 schema).

### 8. 리스크·완화 (§20 관점)

- **dev 관점:** C1/C2/C3 미발행 시 MVP 차단 → Phase 0에서 contracts skeleton 우선, EPIC-001 의존 명시, contract 미완 구간은 fixture stub로 대체하되 reference integrity test는 처음부터 작성. hash mismatch 회귀 방지를 위해 bundle hash 재현 테스트를 CI 필수로.
- **agent 관점:** SPEC 사후작성·과도 일반화 안티패턴 → agents/SPEC.md를 작업 착수 전 선행 작성, EPIC당 owner+reviewer+fallback 지정, 동시 active integration ≤3(빅뱅 통합 방지). 에이전트 runaway 방지를 위해 모든 write path는 Stage 0 dry-run으로 고정.
- **ops 관점:** 두 control plane 합치기 유혹 → SO(dev-time)와 ATS(runtime) 분리를 ADR 0004로 잠그고 통합은 S1+C3 계약 강화로만 수행. 폐쇄망 미준수 → closed-network profile + offline gate를 DoD에 포함, mock HMAC key 프로덕션 차단(P0/P1), Stage 0/1에서 production write 미실행을 테스트로 강제. Reference Integrity 없는 C3·hash 검증 없는 certification은 명시적 금지 안티패턴.

---

# B. Platform Layer

## solution-orchestrator — 개발 계획

### 1. 역할·목표 위치 (Platform / Dev-time control plane #1)

처리 결정은 **유지·강화**다(전략 §11 SO row). solution-orchestrator는 EvidenceOps Platform Layer의 **Dev-time control plane #1**으로 고정된다(§4). 시점은 Dev-time, 입력은 requirement·repo-catalog·harness registry·S1 project-state, 출력은 plan·DAG·dry-run dispatch·judge verdict이다. 근거: census §2.1이 확인한 코드 실체 — `engine/planner.py`(catalog→substring 매칭→`consumes` 전이확장→`ContractDelta`→Kahn topo-sort DAG), `engine/state_machine.py`(plan→simulate→normalize→report, `dry_run=True` 강제), `engine/dispatcher.py`(유일 게이트 핸드오프), `engine/judge.py`(snapshot→RepoVerdict→`release|fix-loop|block|escalate`)가 control plane #1의 본질을 이미 구현한다. 성숙도는 Scaffold(전부 dry-run/HELD, durability·live dispatch 미구현)이므로 "재구성"이 아니라 "강화"가 맞다. **ai-tool-suite(control plane #2, Runtime certifier)와 분리 유지**는 불변 규칙이다(§4·§32 census 1.2): SO=Dev-time(어떤 작업을 어떤 게이트로), ATS=Runtime(어떤 증거가 어떤 판단을 정당화). 합치기 금지 근거는 감사우회·권위혼선·rollback 책임불명·agent runaway 방지(§4). 통합은 두 plane을 코드로 합치는 것이 아니라 **S1 + C3 계약을 강화**하는 것이다.

### 2. 계약 입출력

**Consumes (read-only):** S1 project-state(sibling repo의 operational manifest — `adapters/_state_io.py`·`scaffold/fixtures/*.project-state.json` 경로), `catalog/repo-catalog.yaml`(repo-catalog), `control-plane/harness-registry.yaml`(harness registry). SO는 sibling을 절대 직접 읽고-쓰지 않으며 S1은 write target이 아니다(§8 S1 DoD: read-only).

**Produces:** plan/DAG(`Plan`/`TaskNode`/`ContractDelta`), dry-run dispatch(`HarnessRunSnapshot`), judge verdict(`JudgeReport.recommendation`), 그리고 **HarnessRunEvidence(C2)** — `contracts/harness_run_evidence.py`. C2 어휘는 `RunMode(dry_run/evaluation/candidate_generation/verification)`로 정렬하고, dry_run↔production_write를 분리하며, `parent_approval_id` 없는 live mutation을 금지한다(§8 C2 core). **C2 consumer 전환**: 현재 `contracts/models.py`의 `HarnessRunRequest/Snapshot`는 SO 자생 정의이므로, evidenceops-contracts의 C2 패키지가 발행되면 SO는 자체 정의를 버리고 C2 consumer가 된다(mirror-not-fork, §3.2). SO `contracts/`는 이미 import-linter로 OSS-추출 가능하게 설계되어 있어(census §1.2·§5 L6) **C2/C6(harness-run-contract) 승격에 seed로 기여**한다.

**권위 어휘·금지(§5):** SO 어휘는 `planned|held|dispatched|judged`만 사용한다. judge의 `release|fix-loop|block|escalate`는 내부 recommendation일 뿐 T3 어휘(promote/hold/rollback)나 ATS 어휘(certified/...)로 누수되어서는 안 된다. **금지: sibling write/promote/rollback/runtime certification.** Breaking change 정의(§5): "SO가 sibling write"는 명시 위반이다.

### 3. EPIC 매핑 + 레포-특화 작업

- **EPIC-002 (AI Change Certification MVP, Q2W2-5):** SO는 **dry-run plan + integration entry point** 역할로 참여한다. MVP 흐름(`change-spec.yaml → EvalVault(T2) → reverra-gate(T3) → ATS → cert report`)에서 SO는 dispatch 계획·DAG·dry-run을 제공하고 `solution certify --dry-run` 진입점을 연결한다(§9 CLI).
- **STATUS:proposal 파일 owner 지정 (Phase 0):** census §2.1·grep 확인 4건 — `contracts/change_differential.py`, `contracts/harness_run_evidence.py`, `engine/evidence_normalizer.py`, `engine/harness_registry.py`(+`control-plane/harness-registry.yaml`)가 STATUS:proposal·owner 미확정이다. 각 파일에 owner+reviewer+fallback을 §19 repo-ownership에 등록하고 헤더를 confirmed로 전환한다. 안티패턴 "STATUS:proposal 방치"(§154) 해소.
- **durability(WorkflowEngine) 구현:** `contracts/protocols.py`의 `WorkflowEngine` Protocol(`plan`/`run`) 뒤에 crash/resume/retry를 가진 durable impl(LangGraph 또는 Temporal-backed)을 슬롯-인한다. `engine/state_machine.py`는 현재 plain-JSON·`durable:false`이며 데이터 계약/adapter를 건드리지 않고 교체 가능하도록 설계되어 있으므로, 신규 engine을 Protocol 구현체로만 추가한다(census 리스크: durability 미구현 stub).
- **planner substring 매칭 정밀화:** `engine/planner.py::_named_repos`가 `repo_id.lower() in haystack` 단순 substring이라 과/소매칭 위험(census §2.1). word-boundary/alias 테이블·명시 repo-id token화로 정밀화한다.
- **S1 schema 채택:** `adapters/_state_io.py`가 evidenceops-contracts S1 `project-state.schema.json`을 validate하도록 전환, macOS 절대경로→repo-relative(§8 S1 DoD).
- **harness_registry/change_differential/evidence_normalizer 승격:** proposal→confirmed로 승격하고 C2 어휘에 정렬.

### 4. 시퀀싱

- **Phase 0 (이번 주):** S1 schema 채택(validate seam), STATUS:proposal 4건 owner 지정·confirmed 전환, AHO runner stub 제거 PR 협력(§17). 12 레포 S1 발행 기준 충족.
- **Q2:** EPIC-002 MVP에 dry-run plan + integration entry point로 참여(EPIC-001 C1 의존). planner 정밀화·C2 consumer 전환 착수.
- **Q3:** durability(WorkflowEngine LangGraph/Temporal) 구현. EPIC-004 PromptOptimizer가 SO의 HarnessRunRequest seam을 candidate 경로로 재사용하므로 그 의존을 지원.
- **Q4:** Stage 전환(0→1) 안정화, Stage2 sandbox write 설계(production 아님), 거버넌스 정돈.

### 5. DoD

§11 SO DoD: **dry-run MVP 참여**, **schema drift test 통과**(census 테스트 12 중 contract roundtrip/schema drift 항목 확장). §15 gates: Contract Gate(schema validate·roundtrip·`schema_version` 필수), Offline Gate §15.6(`test_offline_network_block.py`, default CI public internet 없이 통과, SDK lazy import). **§18.5 Stage(엄격 적용 대상 — SO는 dispatch live mutation 위험):** 모든 write/action path는 Stage-aware. Stage0(Dry-run)/Stage1(Read-only integration)에서 **write path 미실행을 테스트로 강제**(현재 `dispatch_policy._check_write_profile_approval`·`harness_registry.policy_for(production_write:false→empty branch allowlist)`가 기반 — 이를 Stage gate로 명시). **Stage3(Production gated write)에서만 `parent_approval_id` + T3 decision + operator approval 후 write 허용**. 현재 Stage를 S1에 노출(§18.5 DoD). Stage 전환 ADR 기록.

### 6. 의존성

**선행:** C2(harness-run-contract — SO `contracts/`가 seed) 및 S1(project-state schema) 발행이 C2 consumer 전환·S1 채택의 선행조건. **MVP(EPIC-002):** EvalVault(T2 regression report)·reverra-gate(T3 GateDecision)·ai-tool-suite(DecisionArtifact)와 `solution certify` dry-run entry point를 연결(§9). C1(EPIC-001)은 `ClaimRef`/`NormalizedEvidence` 형태 정렬에 선행. §19 Integration Capacity Rule: 동시 active integration ≤3, EPIC당 owner+reviewer+fallback.

### 7. 리스크·완화 (census 근거)

- **durability 미구현 stub** → WorkflowEngine Protocol 뒤 durable impl(Q3), 데이터 계약 불변 유지로 회귀 차단. 완화 전까지 `durable:false`를 run record에 명시 유지.
- **planner 과/소매칭** → substring→word-boundary/alias 정밀화 + planner unit test 확장(과매칭·소매칭 케이스 골든).
- **STATUS:proposal 다수(4건)** → Phase 0 owner 지정·confirmed 전환을 P0로, 동시 편집 에이전트 충돌은 §19 거버넌스 변경분류로 흡수.
- **dispatch live mutation 위험** → Stage-aware write path, Stage0/1 write 미실행 테스트, Stage3 `parent_approval_id` 강제로 "Stage0/1서 production write" 안티패턴(§155) 차단.

---

## EvalVault — 개발 계획

### 1. 역할·목표 위치 (Platform / T2 Eval Hub) · 처리결정 · 근거
EvalVault는 EvidenceOps Platform의 **Platform Layer / T2 Eval Hub**(전략 §3.1, §11 Platform 표)로 고정한다. 코드상 이미 엄격 헥사고날(ports&inbound 5 / outbound ~45, `domain/services` 90모듈, `RagasEvaluator`, `regression_gate_service`, 다중 tracker, CLI/FastAPI/MCP, React 프론트 19.5k LOC)을 갖춘 Large/Mature 레포(census §2.4)이므로 처리결정은 **유지·정돈(keep & tidy)**이다. 재작성·모노레포 흡수는 안티패턴(§154-155). 근거: census가 표준 seam·통계 엄밀성·헥사고날을 이미 보유했다고 확인했고(§1.2), 재정의는 발명이 아니라 수렴(§3-관찰)이므로 코어 구조는 보존하고 (a) 권위 불변식 명시화, (b) 도메인 누수 제거, (c) C2/C4 계약 정합만 수행한다.

**권위 위치(전략 §5):** EvalVault=**T2**. 허용 어휘는 `passed|failed|inconclusive`뿐. **promote/hold/rollback 반환은 금지(Breaking change, §54)** — release 결정은 reverra-gate(T3) 권한이다. EvalVault의 RegressionGateReport는 GateDecision의 *입력*일 뿐 그 자체가 release decision이 아니다(§74).

### 2. 계약 입출력
**produces** — `RegressionGateReport` / `EvaluationRun` (C2 **Evaluation Annex**: `regression-gate-report.schema.json`, `evaluation-run.schema.json`). 현재 `regression_gate_service.RegressionGateReport.status`는 `"failed" if regression_detected else "passed"`만 반환(line 84-86) → **`inconclusive` 추가**(공유 메트릭 부재·통계 비유의·데이터 부족 시)하여 §5 T2 어휘 3종을 완비한다. `to_dict()`(line 88-100)와 새 JSON Schema에는 `decision` 필드·promote/hold/rollback 값이 **절대 없어야** 한다(§74, §15 Evaluation Gate). status 외에 pair 수·statistical method·seed·CI·p-value correction·metric direction을 직렬화에 포함(§116 Evaluation Gate 요건).
**consumes** — datasets(CSV/Excel/JSON, thresholds in dataset)·외부 RAG traces(Open-RAG-Trace/OTel), baseline/candidate `EvaluationRun`(storage `get_run`).
**C4 eval-stats** — 현재 통계는 `domain/entities/analysis.ComparisonResult`(paired t-test, Cohen's d, EffectSizeLevel, p_value) 내부 구현. C4(AHO seed 승격, §76) 발행 후 bootstrap CI·McNemar·FDR·Cohen's d·power/MDE를 C4로 **마이그레이션**하되, EvalVault는 C4 consumer로서 adapter 매핑(mirror-not-fork, §29). C4 미승격 동안은 현 구현 유지.
**T2 권위 불변식 준수** — output schema/모델에 **GateDecision 타입 없음**(§75 C3 DoD), promote/rollback 경로 미존재. `test_t2_invariant`로 코드 수준 강제.

### 3. EPIC 매핑 + 레포-특화 작업
**EPIC-002 (AI Change Certification MVP, Q2W2-5, EPIC-001 의존, §123):**
- EvalVault **smoke fixture** + `change-spec.yaml` 소비 경로.
- **RegressionGateReport 생성**(baseline vs candidate → t-test/Cohen's d → status) + **reverra-gate로 전달 with hash**: report에 `{id, schema_version, content_hash}` 부여(reverra-gate RG mapper가 `RegressionGateReport→ImportedEvalIR(reverra.imported/0.1.0)→GateDecision` 변환 시 source hash 보존, §74). 현재 reverra/ImportedEvalIR 참조가 코드에 **0건**이므로 boundary는 schema+hash로만 정의(수평 import 금지, §27).
- **T3 어휘 없음** 검증(EPIC-002 DoD).

**정돈(census §2.4 / §279 P2 / §11):**
- **보험 metric domain pack 분리** — `domain/metrics/insurance.py`(`InsuranceTermAccuracy`, `terms_dictionary.json`)·`config/domains/insurance/`(memory.yaml, terms_dictionary_ko/en.json)·registry의 `category="domain"` insurance 항목(line 224-229, 180/198 entity/risk 설명의 "insurance" 하드코딩)을 **korean/insurance domain pack**으로 추출. core 메트릭 레지스트리는 pluggable pack 인터페이스로만 의존(core에 insurance 0건, §90 DoD).
- **domain/services 그룹화** — census 68모듈(실측 90개)을 책임별 서브패키지(eval/gate/analysis/generation/domain-learning)로 그룹화(thick orchestration 완화).
- **ragas monkey-patch 격리** — `RagasEvaluator`의 ragas 0.4.2 내부 패치를 단일 adapter 경계(예: `instructor_factory`/`evaluator` 인접)에 격리, pin 취약성 봉쇄.
- **C4로 통계 추출** — analysis 통계를 C4 consumer로 전환(§2).
- **프론트 api.ts 계약 자동생성** — `frontend/src/services/api.ts`(1287 LOC, 202 export, 51콜이 백엔드 스키마 미러)를 FastAPI OpenAPI/C2 스키마에서 **typed client 자동생성**으로 대체(§284, 백엔드 강결합 제거).

### 4. 시퀀싱
- **Q2** — C2 **Evaluation Annex 발행 참여**(`regression-gate-report`/`evaluation-run` schema, status 3종, T3 어휘 금지) + **EPIC-002 MVP**(RegressionGateReport→reverra-gate with hash, smoke fixture, T2 invariant test). EPIC-006(AIA) 병렬에서 EvalVault-compatible export 호환 확인.
- **Q3** — **C4 migration**(AHO C4 승격 후 통계 어댑터 전환), domain/services 그룹화·ragas 격리 착수. PromptOptimizer(EPIC-004)가 EvalVault submit 경로 소비 — eval submit seam 안정화.
- **Q4** — **도메인 pack 분리 완료**(insurance→korean/insurance pack, core 누수 0) + **typed client**(api.ts 자동생성) 전환.

### 5. DoD
**§11 EvalVault DoD:** (1) 보험 코드 core 0건(`grep insurance src/evalvault/domain core`=0, 모두 pack 격리). (2) **T2 invariant test** — output에 promote/hold/rollback·GateDecision 타입 부재 강제. (3) **RegressionGateReport에 T3 어휘 없음** — schema·`to_dict`·status 모두 `passed|failed|inconclusive`만.
**EPIC-002 DoD(§123):** smoke fixture·RegressionGateReport(T3 어휘 없음)·RG로 source hash 전달·dry-run default.
**§15 Evaluation Gate:** pair 수·statistical method·seed·CI·p-value correction·metric direction 직렬화·status에 T3 어휘 없음.
**§15 Contract Gate:** schema validate·roundtrip·canonical serialization·backward compat·schema_version 필수.
**§15.6 Offline Gate:** 현재 offline 테스트 부재 → `test_offline_network_block.py` 추가, SDK lazy import, default CI가 public internet 없이 통과.

### 6. 의존성
- **C1 evidence-contract**(EPIC-001) + **C2 harness-run-contract/Evaluation Annex**(§74) **발행 선행** — EvalVault는 C2 consumer로 RegressionGateReport/EvaluationRun을 발행.
- **reverra-gate RG mapper boundary** — EvalVault는 reverra-gate를 **import하지 않음**(수평 결합 금지 §27). RG가 `RegressionGateReport→ImportedEvalIR` mapping을 소유하고, EvalVault는 hash가 포함된 schema-validated report만 제공. C2/C3 boundary test로 계약 검증(§74).
- **C4 eval-stats** — AHO seed 선행조건(§76) 충족 후 승격 시 통계 마이그레이션.

### 7. 리스크·완화
- **services 비대**(census: 68→실측 90모듈, thick orchestration): 빅뱅 분할 금지, 책임별 서브패키지 점진 그룹화 + 기존 ~2,200 테스트를 회귀 안전망으로 DoD화.
- **ragas pin 취약**(monkey-patch on 0.4.2): 패치를 단일 adapter 경계로 격리해 blast radius 축소, fallback 경로 테스트.
- **도메인 누수**(insurance가 core에): pluggable pack + import-linter/grep 강제로 core 0건 유지(§154 "도메인 코드 core에" 안티패턴).
- **프론트 결합**(api.ts 1287 LOC/202 export, 51콜 미러): OpenAPI/C2 기반 typed client 자동생성으로 수작업 미러 제거, schema drift test.
- **T2 권위 오염 리스크**: status에 `inconclusive` 추가 시 T3 어휘 유입을 막기 위해 enum 잠금 + invariant test로 promote/hold/rollback 반환을 컴파일/테스트 단계에서 차단.

---

## reverra-gate — 개발 계획

### 1. 역할·목표 위치 + 처리결정(유지·강화) + 근거
reverra-gate는 EvidenceOps Platform의 **Platform Layer T3 release gate + content-addressed Store**다(전략 §5/§11/census §2.3). 권위 불변식상 reverra-gate만 `promote|hold|rollback` 어휘를 발행하며, T2(EvalVault)가 산출한 `passed|failed|inconclusive`를 release 결정으로 끌어올린다(§5). 코드 근거: `adapters/level3-manifest.json`이 `tier="T3"`, `decision_scope="release-gate"`로 선언, `core/decision.decide_outcome`이 `DecisionOutcome.{PROMOTE,HOLD,ROLLBACK}`만 반환, `core/audit.build_audit_event`이 OCSF 6003 HMAC `AuditEvent`(`AuditEvidence`=sha256+hmac_sha256+key_id+`RetentionPolicy.NOT_STORED`)를 생성, `store/content.py`가 Decimal canonical-hash truth-side 모델, `store/projection.py`가 Store ComparisonPlan을 동일 gate IR로 투영. 이미 mature engine이므로 **처리결정 = 유지·강화**(§11): 신규 발명이 아니라 (a) C3 reference-integrity 발행, (b) production HMAC enforcement, (c) god-dispatcher·Store seam 정돈으로 *수렴/표준화*한다. 근거: 결정 사슬(producers→T3 gate→ATS)에서 reverra-gate가 단일 권위 지점이며, mock HMAC 기본키·skeletal Store가 production write(Stage 3) 전환을 코드 수준에서 막고 있음(census 리스크, §18.5 2→3 전환조건).

### 2. 계약 입출력
**소비:** EvalVault가 발행하는 `RegressionGateReport`(C2 Evaluation Annex, `regression-gate-report.schema.json`; status는 `passed|failed|inconclusive`만, T3 어휘 없음)를 입력으로 받아 RG mapper가 `ImportedEvalIR`(`reverra.imported/0.1.0`, `gate/ir.py`)로 변환한다. 변환 시 입력 RegressionGateReport의 **{id, schema_version, content hash}를 source_artifact로 보존**한다(§8 C3, §15 Release Gate "source_artifact_hash 보존"). 현재 `gate/adapters/generic.py`의 lenient→strict 변환을 RegressionGateReport 전용 mapper로 확장하되 strict IR validation은 유지.

**발행:** `GateDecision`(C3 decision-contract; C2와 분리된 독립 package). Type-level 잠금: `GateDecision.authority = Literal["T3"]`(§8 C3). Reference Integrity 필드: `source_artifact_id` + `source_artifact_schema_version` + `source_artifact_hash`(소비한 RegressionGateReport의 위 3종), `evidence_refs`(C1 `evidence_id` 목록), `audit_event_id`(생성된 HMAC `AuditEvent.event_id` 참조). decision 값은 기존 `DecisionOutcome`와 1:1 매핑(`promote|hold|rollback`).

**불변식 준수:** T3 권위 유지(원천 metric 임의생성 금지 — §5), conservative conflict resolution(`rollback > needs-human > hold > promote`, §5)을 GateDecision 산출 로직과 hold 우선 정책에 반영. T2 어휘 누수 차단 테스트로 RegressionGateReport에 promote/rollback 값이 들어오면 거부.

### 3. EPIC 매핑 + 레포-특화 작업
**EPIC-002 (AI Change Certification MVP, Q2W2-5):** reverra-gate는 흐름 `EvalVault(T2)→reverra-gate(T3)→ATS` 중간 노드(§9). 구체 작업:
1. **RG ImportedEvalIR 변환 with source hash** — RegressionGateReport→ImportedEvalIR mapper(source {id/schema_version/hash} 캡처). `gate/adapters/`에 `evalvault_regression.py` 신설, `gate/ir.py` 확장 없이 기존 strict IR 재사용.
2. **GateDecision with Reference Integrity** — `core/decision.py`의 `decide_outcome` 결과를 C3 `GateDecision` 모델로 포장하는 발행 레이어 추가(`core/gate_decision.py` 신설 제안); `authority=Literal["T3"]`, evidence_refs(C1 id), audit_event_id, source_artifact_hash 채움. 산출물은 MVP의 `artifacts/certifications/<change_id>/gate-decision.json`(§9 산출).
3. **C3 발행 참여** — `artifact_contracts.py`에 C3 GateDecision contract 등록, schema_version 필수·canonical serialization(§15 Contract Gate).

**CLI god-dispatcher 분해 (§11 주요작업, census 리스크):** `cli.py`(1284줄)가 demo/store/gate/feedback/server 거의 전 패키지를 import. command별 모듈(`reverra/commands/{run,demo,import_,check,store,...}.py`)로 분리하고 `cli.py`는 argparse 라우팅+dispatch만 보유. import-linter 규칙으로 역방향·수평 import 금지(§3.2).

**mock HMAC key production 차단 (P0/P1, startup fail — Appendix F#17, §15 Security Gate):** `core/audit.py:61-62`의 `os.environ.get("REVERRA_HMAC_KEY", "phase1-mock-secret")` / `"reverra-phase1-mock-2026q2"` 기본키를 **stage-aware fail-fast**로 교체. closed-network/production profile(§15.6)에서 `REVERRA_HMAC_KEY` 미설정 또는 mock sentinel 값이면 startup에서 예외(write path 진입 차단). Stage 0/1(dry-run, read-only)에서는 mock 허용하되 audit_event에 `retention_class="phase1-mock-7d"` 표식 유지. `.env.example`의 placeholder도 sentinel 검출 대상에 포함.

**Store seam 정리 (§11 주요작업):** `store/content.py`(Decimal truth-side, canonical hash)와 `store/models.py`(projection-only skeleton, 명시적으로 "skeleton: only fields the gate consumes") 사이 seam을 정돈. `projection.py`의 두 경로(`project_to_ir` 표면 모델 / `project_store_evaluation` persisted artifact)를 단일 truth→IR 경로로 수렴시키고, projection이 source artifact hash(`content_digest`)를 GateDecision reference integrity로 전파하도록 연결.

### 4. 시퀀싱
- **P0/P1 (Phase 0 / EPIC 착수 전):** mock HMAC key production 차단(startup fail) — Appendix F#17, §18.5 2→3 전환조건. S1 `project-state` 발행(현재 Stage 노출, §8/§17). C1 field diff matrix 참여(§17.5: RG `AuditEvidence`↔EvidenceRef).
- **Q2 (EPIC-002, W2-5):** RegressionGateReport→ImportedEvalIR mapper(source hash) → GateDecision(C3 reference integrity) 발행 → MVP dry-run 흐름에 wiring → offline gate(`test_offline_network_block.py`, §15.6) 통과.
- **Q3 (확장·정돈):** C3 GateDecision 발행 확장(PromptOptimizer 루프 source-hash chaining 지원, §12), CLI god-dispatcher 분해 완료, Store seam 단일화. 이 순서는 census 우선순위(P0 차단해소→P2 god-dispatcher/HMAC 정돈)와 §16 EPIC 의존(EPIC-001→002→004)을 따른다.

### 5. DoD
- §11 DoD: **production HMAC enforcement**(production/closed-network profile서 mock key startup fail, 단위테스트로 강제) + **source_artifact_hash 보존**(GateDecision이 입력 RegressionGateReport의 {id, schema_version, hash} 보유).
- EPIC-002: RegressionGateReport→ImportedEvalIR(source hash)→GateDecision(reference integrity) 경로가 MVP `gate-decision.json` 산출, T2/T3 불변식 검증(입력에 T3 어휘 없음·출력 authority=T3).
- §15 Release Gate: T2만으로 promote 금지·T3 GateDecision 필수·conservative conflict·gate rule version 기록·HMAC audit·source_artifact_hash 보존.
- §15 Security Gate: mock HMAC production 차단·raw reasoning 미저장(`RetentionPolicy.NOT_STORED` 유지).
- **C3 reference integrity test:** GateDecision.authority=Literal["T3"] 잠금, source hash mismatch 시 certification invalid(re-run 강제, §8 C3 DoD), evidence_refs가 C1 evidence_id 참조 integration test, audit_event_id 역추적 가능.
- §15.6: default CI가 public internet 없이 통과, closed-network서 `solution certify` dry-run 통과.

### 6. 의존성
- **선행 C1 evidence-contract**(EPIC-001): GateDecision.evidence_refs가 C1 stable `evidence_id`를 참조하므로 C1 발행이 선행. RG `AuditEvidence`가 C1 diff matrix 대상(§17.5).
- **선행 C2 harness-run-contract / RegressionGateReport**(C2 Evaluation Annex): EvalVault가 T3 어휘 없는 RegressionGateReport를 발행해야 RG mapper 입력 성립(§8 C2 DoD).
- **C3 decision-contract** package(C2와 분리, §0.2#8): GateDecision 타입·Literal 잠금·Reference Integrity 정의를 evidenceops-contracts에서 가져와 mirror(내부 fork 금지, §3.2).
- **Boundary — EvalVault:** 직접 import 금지(§3.2 수평 import 금지); C2 artifact(schema)로만 결합. reverra-gate가 EvalVault.core를 import하지 않음.
- **Boundary — ai-tool-suite:** ATS가 reverra-gate GateDecision을 소비해 DecisionArtifact(gate hash 보존)로 정규화; reverra-gate는 ATS를 모름(하향 의존만, ATS adapters/reverra_gate가 mapper 소유).

### 7. 리스크·완화 (census 근거)
- **`cli.py` god-dispatcher 결합**(거의 전 패키지 import): 분해 중 import-linter 규칙으로 회귀 방지, command별 모듈화로 EPIC-002 wiring 표면 최소화. 분해는 Q3로 미뤄 MVP 차단 회피.
- **mock 기본키 production 위험**(`phase1-mock-secret`): P0/P1 startup fail로 즉시 차단. sentinel 값 명시 검출(환경변수+`.env.example`), Stage-aware 허용 범위 테스트.
- **Store skeletal**(`models.py` projection-only 부분집합 vs `content.py` truth): seam을 truth→IR 단일 경로로 수렴하고, reference integrity가 `content_digest`(canonical Decimal hash)에 의존하므로 projection이 hash를 누락 없이 전파하는지 계약 테스트로 강제.
- **langfuse/phoenix scale 추론 휴리스틱**(`_metric_scale` value-기반 추정→binary/ordinal/continuous): GateDecision의 통계 결정 정합성에 영향. RegressionGateReport 경로는 EvalVault가 명시한 scale을 신뢰하고, 휴리스틱 경로는 추정 출처를 source_location으로 기록해 audit 추적성 확보. 추정 결과가 stat-plan(RVR-* 규칙)과 충돌하면 conservative하게 hold.

---

## ai-tool-suite — 개발 계획

### 1. 역할·목표 위치 (Runtime Certifier / control plane #2)

전략 §4·§11이 부여한 정체성은 **Runtime Certifier 허브, control plane #2**다. 처리 결정은 **유지·강화(keep & harden)**. 근거: 코드 census §2.2가 확인하듯 본 레포는 평가기가 아니라 폐쇄망 인증 허브로 이미 성숙하다 — 런타임 deps 0, 8.9k src/26 test, `packages/artifacts/models.py`(1,653줄)의 frozen dataclass + `validate()` 직렬화 강제, `decision_service`·`conflict_service`·`capability_inventory`가 sibling project-state를 read-only로 ingest → 어댑터를 authority class + T0–T4 tier로 인증 → 이종 증거를 중립 `DecisionArtifact`로 정규화 → 보수적 충돌해소 체인을 갖춘다. 발명이 아니라 계약 강화 대상이다.

solution-orchestrator(#1, Dev-time)와의 분리는 §4·§4.4·안티패턴이 명령하는 불변식이다. ATS는 **런타임**(S1·evidence·gate decision 입력 → DecisionArtifact/ConflictReport/CertificationReport 출력)에 한정하며 작업계획·DAG·dispatch·judge에 절대 진입하지 않는다. ATS 금지: 원천 metric 생성, gate decision 대체, sibling 임의수정(§4·§5). 두 plane을 합치지 않는 근거는 감사우회·권위혼선·rollback 책임불명·agent runaway 방지이며, 통합 수단은 코드 병합이 아니라 **S1 + C3 계약 강화**다(§4·§0.2.9).

### 2. 계약 입출력 (C3 producer + Reference Integrity)

**소비(consumes):** reverra-gate가 발행한 **GateDecision(C3)** + 그 reference integrity 블록({id, schema_version, content hash}, evidence_refs(C1 id)), 하위 evidence, **S1 project-state**(현재 `packages/registry/models.py`의 `ProjectState`/`StableSurface`). C3 reference integrity는 소비 시 hash를 재검증하며, **hash mismatch 시 certification invalid(re-run 강제)**(§8 C3 DoD·§9.6·안티패턴).

**생산(produces):**
- **DecisionArtifact (C3)** — 현재 `DecisionArtifact`는 `source_adapter: str`만 가지므로 강화 필요: `producer=Literal["ai-tool-suite"]` 추가(C3 type-level enforcement §8), `{source_gate_decision_id, hash}`를 보존하는 reference 블록, `normalized_evidence_index`, `conflict_resolution_policy` 필드. gate hash는 from-mapper 전 구간 보존된다(§12·§16 EPIC-002).
- **ConflictReport** — `conflict_service._resolve`가 이미 구현한 **conservative resolution**(rollback > needs-human > hold > promote, §5와 정확히 일치). `resolution=Literal["rollback","needs_human","hold","promote"]` 타입 잠금으로 강화.
- **CertificationReport** — 신규: `{change_id, eval/gate/decision artifact ref+hash, artifact_bundle_hash}`. 현재 레포에 부재(grep 결과 0건)하므로 모델·렌더러(JSON + markdown)를 신설하고 bundle hash가 재현 가능해야 한다(§9.6).

### 3. EPIC 매핑 + 레포-특화 작업

**EPIC-002 (AI Change Certification MVP, Q2W2-5)** 가 본 레포의 주 EPIC이다. 레포-특화 작업:

1. **ATS DecisionArtifact with gate hash** — `adapters/reverra_gate/mapper.py`·`decision_service.decide_with_adapter`를 확장해 입력 GateDecision의 `{source_gate_decision_id, hash}`를 DecisionArtifact에 보존; `producer=Literal["ai-tool-suite"]` 잠금.
2. **CertificationReport 렌더** — `change_id`별 `{certification-report.json,.md, decision-artifact.json, gate-decision.json, normalized-evidence.json, operator-summary.md}` 산출(§9.2). `artifact_bundle_hash` 계산·재현.
3. **S1 schema 채택** — `packages/registry/models.py`를 evidenceops-contracts S1 `project-state.schema.json`(필드: schema_version, repo{name,role,maturity,source_path}, capabilities, contracts{produces,consumes}, artifacts, entrypoints, test_status, risk_flags)에 정렬; SO와 동일 schema validate + drift test(§8 S1 DoD).
4. **macOS 절대경로 → config화** — `adapters/*/manifest.json` 7개의 `source_path: "/Users/sungyub/Documents/Projects/..."` 와 `references/project-states/**`의 절대경로를 repo-relative + 외부 config로 전환(census §2.2 리스크, §8 S1 DoD).
5. **하드코딩 정책 외부화** — `capability_inventory._GATE_NOTES`, `skillopt_readiness._CANDIDATES`(+`_CANDIDATE_FIXTURES`)를 코드에서 config/data로 분리.
6. **decide mapper 확장** — 현재 `decision_service.DECISION_MAPPERS`는 `{evalvault, reverra_gate}` 2개만 wired. 나머지 5개 어댑터(aia_awesome_novel_studio, cswind_poc, llm_research_vault, local_llm_bench, verbera)는 parser만 있고 mapper.py가 없는 **evidence-only** 상태(`ls adapters/*/` 확인). 정책상 정당한 어댑터에 decide mapper 추가.
7. **7 adapter evidence-only 이상 wired** — §11 DoD를 충족하도록 7개 어댑터 전부를 최소 evidence-only 이상으로 일관 wiring하고 catalog/inventory에 반영.

### 4. 시퀀싱

- **Q2 (MVP·S1):** EPIC-002 핵심 — DecisionArtifact의 C3 강화(producer Literal·gate hash 보존·reference integrity), CertificationReport 신설·렌더, S1 schema 채택 + drift test, dry-run MVP에서 `solution certify` 통과. 절대경로 config화는 S1 정렬과 함께 선행(census S1 DoD 차단요인).
- **Q3 (mapper 확장):** decide mapper를 정책상 정당한 어댑터로 확장, 7 adapter wired 완성, EPIC-004 PromptOptimizer가 ATS cert read를 호출하는 wiring 수용.
- **Q4 (정책 외부화):** `_GATE_NOTES`/`_CANDIDATES` 외부화, governance/versioning 정돈(census P2).

### 5. DoD

- **§11 DoD:** 7개 adapter가 evidence-only 이상으로 wired.
- **EPIC-002:** GateDecision→ATS DecisionArtifact(gate hash 보존)→cert report.md(bundle hash 재현). 모든 산출 artifact가 schema validate, promote/hold/rollback 1개 명확 출력, markdown summary, integration test, T2/T3 불변식 검증, CI offline 재현(§9.6).
- **§15 Contract/Release Gate:** Contract Gate(JSON Schema validate·model roundtrip·canonical serialization·schema_version 필수); Release Gate(T2만으로 promote 금지·T3 GateDecision 필수·conservative conflict·gate rule version 기록·source_artifact_hash 보존).
- **C3 reference integrity 소비:** 각 단계 hash 보존, **hash mismatch 시 certification invalid(re-run 강제)**.
- **§15.6 Offline:** `test_offline_network_block.py` 유지, default CI가 public internet 없이 통과, closed-network에서 `solution certify` dry-run 통과(런타임 deps 0 유지).

### 6. 의존성

- **선행:** C1(evidence-contract, evidence_id/canonical_id) → C3(decision-contract, GateDecision/DecisionArtifact/ConflictReport/CertificationReport + Reference Integrity Literal 잠금) → S1(project-state.schema.json). C3는 C2와 별도 package이며 EvalVault output schema에 GateDecision 타입이 없어야 한다(§8). C3 없이 DecisionArtifact 강화 불가, S1 없이 control plane 분리가 코드 수준에서 강제 불가(안티패턴).
- **입력 소스:** reverra-gate의 **GateDecision**(T3, source_artifact_hash 보존)이 ATS DecisionArtifact의 정규 입력. reverra-gate의 Reference Integrity 구현(§11 reverra-gate row)이 선행 의존이다.

### 7. 리스크·완화 (census 기반)

- **하드코딩 정책(`_GATE_NOTES`/`_CANDIDATES`)** — 정책이 코드에 박혀 governance/감사가 어렵다. 완화: config/data 외부화 + 변경분류(Contract Governance §19) 적용, Q4 분리.
- **절대 macOS source_path** — 7 manifest + project-state 스냅샷이 `/Users/sungyub/...` 종속. 완화: repo-relative + config 주입으로 전환, S1 drift test로 회귀 방지(§8 S1 DoD).
- **service DAG cascade** — 13 서비스가 `packages/artifacts/models.py`(1,653줄) 단일 모델에 강결합되어 C3 강화 시 연쇄 변경 위험. 완화: producer Literal·reference integrity 필드를 후방호환(additive minor) 추가 + roundtrip/계약 테스트로 cascade 봉쇄, 빅뱅 금지·한 어댑터씩 점진 마이그레이션(§19 Integration Capacity Rule, 동시 active ≤3).

---

## llm-research-vault — 개발 계획

### 1. 역할·목표 위치 + 처리결정·근거

**Platform Layer / Graph RAG evidence producer engine.** 전략 §3에서 LRV는 Platform 레이어의 "Graph RAG Engine"이며, 권위 불변식(§5)상 **Evidence Producer**다 — retrieval evidence를 생성하고 metric을 보고하되 release 결정(promote/hold/rollback)은 절대 하지 않는다. census(§2.5)가 확인하듯 코드 실체는 "수집→tier evidence→hybrid(BM25 Nori+kNN+RRF k=60)+rerank→T0-gated answer"의 한국어-first Graph RAG 엔진이고, `serve`가 `/chat` SSE, `eval`이 KO/EN IR 벤치+taskbank를 제공한다.

**처리결정 = 유지·집약(§11).** 새 발명이 아니라 §3 "수렴/표준화"와 census §1.3의 "통합 1순위" 진단에 따라, 비대한 스크립트층을 라이브러리로 흡수하고 공용 계약(C1/C5/C6)에 맞춘다. **근거:** lib 6,108 LOC 대비 scripts 17,478 LOC/43파일(3×)로 로직 중복이 심하고(census §2.5 리스크), `provenance.to_evidence_ref`·`SourceTier T0–T4`·Nori·Gemini plumbing이 이미 멀티레포 mirror 관계(§4.3, §5 L1/L4/L5)에 있어 집약 안전성·레버리지가 모두 높다.

### 2. 계약 입출력

- **Produces:** retrieval evidence(`RetrievalUnit` 중립 atom, `can_support_answer=T0만`) + **EvidenceRef** — `graph_rag/provenance.py:to_evidence_ref()`가 Drive 사이드카 provenance를 `{source_app, source_object_id, uri, observed_at, actor_ids, permission_scope, summary}`로 매핑한다. 전략 §8 C1: 이는 **C1 evidence-contract의 mirror**이며 fork 금지(§3.2). C1 발행 후 `to_evidence_ref`는 C1 binding을 호출하는 adapter로 재배선하고, `canonical_id = sha256(canonical_json({source_app, object_id, observed_at, permission_scope, source_tier, content_hash}))` 규칙(§8)을 materialize한다. `flatten_provenance_fields`/`citation_from_source`는 C1 NormalizedEvidence 투영과 정합시킨다.
- **Consumes/contributes C5 ko-text:** Nori 형태소 정합이 `opensearch_runtime`(custom `research_vault_nori` analyzer, `NORI_SMOKE_TERMS`), `retrieval`, `rerank`, `verify`, `loader`, `contracts`에 분산돼 있다 — §8 C5(Nori alignment/형태소)의 **seed 제공자이자 consumer**. analyzer 정의·smoke 토큰·Nori 정합 검증을 C5 패키지로 추출 기여하고 LRV는 C5 adapter로 소비한다.
- **Consumes/contributes C6 llm-rest:** Gemini plumbing이 **둘로 분기**돼 있다 — `gemini_embedding.py`는 google-genai SDK(`embed_content`), `gemini_answer.py`는 urllib 직접(`https://generativelanguage.googleapis.com/v1beta` REST, 구조화 JSON, 제공 evidence에 없는 anchor 거부). 스크립트(`call_gemini_answer` 등)가 또 한 겹 재래핑한다. §8 C6(provider-neutral REST/SSE/structured JSON + offline stub)로 **통일**해 두 경로를 하나의 provider-neutral 클라이언트로 수렴시킨다(LRV는 C6의 contributor 겸 consumer).
- **권위(불변):** **T0-gated answer 유지** — 최종 사실 주장은 `SourceTier.T0_CANONICAL_STRUCTURED` 근거로만 합성(`retrieval.py`의 answer gate, `gemini_answer`의 anchor 거부). LRV는 evidence/metric만 내보내고 게이트 판정은 EvalVault(T2)/reverra-gate(T3)에 위임한다.

### 3. EPIC 매핑 + 레포-특화 작업

주 작업은 §11 LRV 행(scripts층 흡수·opensearch-py 통일·dim/model config화)이며, 공용 계약 측면은 **EPIC-001(C1)**과 §5 L1/L4/L5 추출에 연결된다(전용 EPIC 없음 → §11 정돈 + 공용 추출 기여).

1. **scripts층(17.5k, 43파일) library 흡수** — 25개 스크립트의 `sys.path.insert` 부트스트랩과 스크립트별 Gemini 재래핑(`call_gemini_answer` 등)을 제거하고, 공통 로직을 `graph_rag`/`serve`/`eval` 라이브러리 함수로 끌어올린다. `report_*`/`verify_*`/`demo_*`/`smoke_*`는 라이브러리 호출만 하는 얇은 CLI 진입점으로 환원한다. Gemini 호출은 전부 C6 클라이언트 경유로 단일화(§5 L4).
2. **opensearch-py 통일** — `opensearch_runtime.py`의 urllib 직접 호출(`_request_json`, `urlopen`, `_bulk`, `_analyze`, `_index_exists`)을 선언된 opensearch-py 클라이언트로 교체. TLS·인증·재시도를 클라이언트에 위임해 census가 지적한 drift/TLS 미처리를 제거. `INDEX_SCHEMA`/Nori analyzer 정의는 보존하되 C5와 정합.
3. **1536/model id config화** — 하드코딩 3곳(`opensearch_runtime.EMBEDDING_DIMENSION=1536`, `gemini_embedding.GEMINI_EMBEDDING_DIMENSION=1536`/`GEMINI_EMBEDDING_MODEL`, `contracts.assert_production_equivalent`의 `dimension != 1536`)과 답변 모델(`gemini_answer.DEFAULT_GEMINI_ANSWER_MODEL="gemini-3.1-flash-lite"`)을 단일 설정(`env`/config)으로 외부화. `assert_production_equivalent`는 고정 1536 대신 설정 차원과 일치 검사로 변경.
4. **C1 provenance mirror** — `provenance.to_evidence_ref`를 C1 evidence-contract binding으로 재배선(§8 mirror). source_tier·permission_scope·content_hash 필수 필드를 채워 C1 fixture roundtrip에 LRV를 1개 consumer migration으로 등록(EPIC-001 DoD §8.4의 "3+ repo fixture").
5. **page provenance(census borrowables)** — `docs/references/rag-multimodal-borrowables.md` #3(높음)에 따라 provenance dict에 `page`/`page_anchor`(#page=N 딥링크) 칸을 추가 고려. taskbank regression으로 before/after 측정 후 반영(PROPOSAL 유지).

### 4. 시퀀싱

- **Q2:** C1 발행(EPIC-001) 합류 — provenance→C1 mirror 재배선 + LRV fixture roundtrip 등록. dim/model id config화(저위험·선행 안전).
- **Q3:** scripts 흡수 본작업 — sys.path 부트스트랩·Gemini 재래핑 제거, report/verify/demo를 라이브러리 호출로 환원, opensearch-py 통일. §11 LOC 30% 감소 목표 달성.
- **Q4:** C5(ko-text)/C6(llm-rest) 추출 기여 — Nori analyzer·형태소 정합을 C5 seed로, 통합된 Gemini 클라이언트를 C6 consumer로 마이그레이션. page provenance 옵션 평가.

### 5. DoD

- **§11 DoD:** scripts LOC **30% 감소**(17.5k 기준 ≈12.2k 이하), 라이브러리 로직 중복·sys.path 부트스트랩 제거.
- **§15 Contract Gate:** C1 JSON Schema validate·model roundtrip·canonical serialization·schema_version 필수.
- **§15 Evidence Gate:** EvidenceRef에 source_tier·permission_scope·content_hash(canonical rule)·**evidence_id deterministic**.
- **§15.6 Offline Gate:** `test_offline_network_block.py` 신설(현재 부재), Gemini/OpenSearch SDK lazy import + offline stub, network 차단서 contract/unit test 통과(default CI public internet 없이), live는 `integration-live` profile 분리.
- **provenance→C1 roundtrip:** 동일 입력→동일 canonical_id, content_hash 변경→id 변경 test 통과.

### 6. 의존성

- **C1 선행(필수):** provenance mirror 재배선은 EPIC-001 C1 evidence-contract 발행에 의존(§16). C1 없이는 mirror가 아니라 fork가 됨(§3.2 위반).
- **C5/C6 양방향:** LRV는 Nori 정합(C5)과 Gemini plumbing(C6)의 **seed 제공자이자 consumer** — 추출 패키지에 검증된 구현을 기여하고, 발행 후 adapter로 소비. §5 추출 순서(L1→…→L4→L5)상 C6/C5는 후행이므로 Q4 정합.

### 7. 리스크·완화

- **스크립트층 3× 비대(census):** 빅뱅 흡수 금지(§안티패턴). 스크립트 단위로 점진 흡수 + 각 스크립트의 기존 출력(report/verify 산출물)을 golden으로 회귀 고정.
- **urllib drift·TLS 미처리:** opensearch-py 전환을 작은 PR로 분리, `collect_runtime_report`/`bulk_ingest_units`부터 교체하고 INDEX_SCHEMA·Nori 토큰 smoke를 회귀로 보존.
- **하드코딩 상수(1536/model id):** config화 전·후 production_equivalent 검사 결과를 fixture로 고정, 차원 불일치가 조용히 통과하지 않도록 `assert_production_equivalent` 테스트 강화.
- **eval 백엔드가 공유 인덱스 rebuild:** `eval/backends.index_corpus_to_opensearch`가 `create_or_update_index(rebuild=True)`로 **공유 프로덕션 인덱스를 재빌드**(코드 내 WARNING 존재). 완화 — eval 전용 인덱스명/URL 강제, 프로덕션 인덱스 대상 rebuild를 코드 수준 가드로 차단, offline `LexicalBackend`를 default로 두고 OpenSearch 백엔드는 `integration-local` profile에서만.

---

## PromptOptimizer (신규 구현) — 개발 계획

### 1. 역할·목표 위치 (Platform / Verifier-driven Optimizer)

PromptOptimizer(PO)는 EvidenceOps Platform의 **Platform Layer**에 위치하는 **verifier-driven optimizer**다(census §2.12 = EMPTY, 전략 §11 = 신규 구현, §0.2-11/§23-Q6 = verifier-driven only). 정체성은 명확하다: **PO는 자동 생성기/자동 승격기가 아니다.** 후보 프롬프트(또는 스킬 문서)를 생성하고 평가에 제출할 뿐, 무엇이 승격되는지의 **최종 권위는 항상 외부에 있다** — 평가 권위는 EvalVault(T2), 게이트 권위는 reverra-gate(T3), 인증 권위는 ai-tool-suite(ATS)다. PO 어휘는 §5에 못박힌 `candidate_generated | submitted_for_eval | submitted_for_gate`만 사용하며, `promote/hold/rollback`(T3)·`passed/failed/inconclusive`(T2)·`certified/needs_human`(ATS) 어휘는 절대 반환·생성하지 않는다(혼용은 §5 breaking change). SkillOpt 패턴(skillopt-verifier-wiring.md)의 "validation-gated 편집"을 그대로 따라 self-generated 이득=0 문제를 구조적으로 회피한다.

### 2. 표준 루프 + 불변식 (§12)

표준 루프(§12 verbatim 보존):
`candidate → HarnessRunRequest(C2) → EvalVault → RegressionGateReport(C2 Evaluation Annex) → C4 stats → reverra-gate GateDecision(C3, source hash) → ATS DecisionArtifact(C3, gate hash) → promote 가능 후보 기록`.

단계별 계약 충실성:
- **candidate**: search_space에서 mutation으로 생성된 프롬프트 후보. 상태 `candidate_generated`.
- **HarnessRunRequest(C2)**: PO candidate도 SO·AHO와 **동일 schema**로 표현(§8 C2 core). `RunMode=candidate_generation`, `dry_run↔production_write 분리`, `parent_approval_id 없는 live mutation 금지`. 상태 `submitted_for_eval`.
- **EvalVault → RegressionGateReport(C2 annex)**: EvalVault가 baseline vs candidate를 평가해 RegressionGateReport 산출. **status는 `passed|failed|inconclusive`만**, decision/promote·hold·rollback 필드 없음(T2 권위, §8 C2 annex). RegressionGateReport는 GateDecision 입력일 뿐 release decision 아님.
- **C4 stats**: paired bootstrap CI·McNemar·Cohen's d·FDR로 후보 우월성 통계 검증.
- **reverra-gate GateDecision(C3)**: RG mapper가 RegressionGateReport→ImportedEvalIR→GateDecision. GateDecision은 input RegressionGateReport의 `{id, schema_version, content hash}` + evidence_refs(C1 id)를 보존(Reference Integrity, §8 C3). 상태 `submitted_for_gate`.
- **ATS DecisionArtifact(C3)**: `{source_gate_decision_id, hash}` 보존.
- **promote 가능 후보 기록**: PO는 결과를 read-only artifact로 **기록만** 한다.

불변식(§12 verbatim):
- **PO는 promote/live mutation 안 함.**
- **dry-run default.**
- **T3 gate 없이 승격 불가.**
- **DecisionArtifact 없이 운영반영 불가.**
- 추가(§5): PO가 gate 없이 promote = breaking change.

### 3. 최소 구조 (§12.4)

```
PromptOptimizer/
  pyproject.toml          # Python ≥3.11, uv, package=false, runtime deps 최소(pydantic+pyyaml), contracts는 dep 0
  SPEC.md                 # 사후작성 금지 — 구현 전 작성(안티패턴 회피)
  src/prompt_optimizer/
    contracts.py          # C1/C2/C3/C4 adapter mapping(mirror-not-fork, 내부 복사본 금지)
    candidate.py          # PromptCandidate 모델 + candidate_generated 상태
    search_space.py       # 변이 공간 정의(add/delete/replace 편집축, SkillOpt 패턴)
    mutation.py           # offline mutation(production 런타임 자기변이 금지)
    runner.py             # AHO HostRunner Protocol 사용 → HarnessRunRequest(C2) 생성
    eval_client.py        # EvalVault submit → RegressionGateReport 수신(submitted_for_eval)
    gate_client.py        # reverra-gate submit → GateDecision 수신(submitted_for_gate)
    cert_client.py        # ATS DecisionArtifact read(운영반영 권위 확인용, read-only)
    optimizer.py          # outer-loop: held-out validation gated 채택(textual learning rate)
    cli.py                # dry-run default, offline-by-default 엔트리
  tests/
    test_candidate_generation.py
    test_no_live_mutation_without_gate.py   # 핵심: T3 gate 없이 live mutation 불가 강제
    test_eval_submission.py
    test_gate_required.py
    test_offline_network_block.py            # §15.6 offline gate
```

**verifier 정의**: EvalVault taskbank/deslop_eval(주관 도메인 grader) + EvalVault regression gate(T2) + reverra-gate gate(T3). SkillOpt wiring 표(proposal §3)대로 검색/답변 verifier=taskbank recall@k/nDCG, 문체 verifier=deslop_eval.py.

### 4. EPIC 매핑 — EPIC-004 (Q3, 001/002/003 의존)

EPIC-004 PromptOptimizer MVP(4주, Q3) 작업 목록(§16 verbatim):
- **SPEC** 작성(구현 전).
- **candidate / search_space** 구현.
- **offline mutation** 구현(add/delete/replace).
- **AHO runner** 연결(EPIC-003가 제공하는 HostRunner Protocol + deterministic fake runner 사용).
- **EvalVault submit**(RegressionGateReport 수신).
- **RG submit**(GateDecision 수신, source hash 보존).
- **ATS cert read**(DecisionArtifact 참조).
- **deslop_eval verifier wiring**(reverra-lab tools — `deslop-writing` 스킬 1순위 파일럿 verifier; SkillOpt wiring 표/`docs/proposals/skillopt-verifier-wiring.md` §3·§4).
- **no-live-mutation test**.

### 5. 시퀀싱

- **Phase 0 (이번 주)**: 빈 슬롯 확인만. census §2.12대로 PO는 코드 0(README+.gitignore)임을 확정하고, S1 project-state.schema.json을 발행해 "계획만, 미구축" 상태를 노출(§8 S1 DoD: 12 레포 모두 발행 = Phase 0 완료 기준). PO는 Phase 0에서 코드 작성하지 않음 — **선행 EPIC(001/002/003) 완료가 전제**(§16 의존: Phase0→EPIC-001→EPIC-002→EPIC-004; EPIC-003→C4 승격).
- **Q3 (EPIC-004, 1 cycle)**: C1/C2/C3 발행 완료 + AHO 재구성(EPIC-003) 완료 후, 위 §3 최소 구조를 4주에 구현해 candidate→eval→gate→cert 단일 cycle을 실증. Integration Capacity Rule(§19): 동시 active integration ≤3 준수, EPIC당 owner+reviewer+fallback 지정.

### 6. DoD (Definition of Done)

- **§11 DoD**: **1 cycle 실증**(candidate 1개가 표준 루프 전체를 통과해 promote 가능 후보로 기록되거나 reject됨).
- **EPIC-004 DoD(§16)**: candidate gen · eval submit · gate submit · no-live-mutation · **dry-run default** · 1 cycle.
- **§18.5 Stage DoD**: PO는 **production prompt swap 리스크**가 명시된 엄격 적용 대상(§18.5). 따라서 모든 write/action path는 **Stage-aware**여야 하고, **Stage0/1에서 write path 미실행을 테스트로 강제**(`test_no_live_mutation_without_gate.py`). Stage3 production prompt swap은 `parent_approval_id + T3 decision + operator approval` 후에만 가능. 현재 Stage를 S1에 노출.
- **§15.6 Offline Gate**: `test_offline_network_block.py` 존재, default CI가 public internet 없이 통과.

### 7. 의존성

선행 발행이 **모두** 필요:
- **C1 evidence-contract**(EPIC-001) — evidence_id/canonical_id 참조.
- **C2 harness-run-contract + Evaluation Annex**(EPIC-002) — HarnessRunRequest + RegressionGateReport.
- **C3 decision-contract**(EPIC-002) — GateDecision/DecisionArtifact + Reference Integrity.
- **C4 eval-stats** — AHO를 seed로 승격(§8 C4 선행조건 충족 후).
- **AHO(EPIC-003)** — HostRunner Protocol + deterministic fake runner를 PO runner가 substrate로 사용(census §2.10).
- **EvalVault / reverra-gate / ATS wiring** — 세 verifier·gate·certifier가 동작 가능하게 선행 wired(AI Change Certification MVP, EPIC-002).

수평 직접 import 금지(§3.2): PO는 Platform 끼리 직접 import하지 않고 C1~C4 계약·S1 manifest·각 서비스 공개 인터페이스로만 결합한다.

### 8. 리스크·완화

- **Optimizer runaway**: outer-loop가 무한 후보 생성/평가 호출. **완화** — dry-run default + Integration Capacity Rule + outer-loop를 offline-only로 제한(production 자기변이 금지, proposal §5) + cycle budget·후보 수 상한. PO가 어떤 경우에도 promote/live mutation 못 함(§12 불변식).
- **Verifier 과적합**: 후보가 평가셋에만 맞춰짐(SkillsBench self-generated 이득=0 문제). **완화** — **held-out** 강제: 최적화 셋 ≠ 평가 셋, EvalVault capability/regression held-out 분리(proposal §5). 2026-05 SkillOpt preprint 외부 점수 맹신 금지, 내부 eval로 검증 후 채택.
- **Production prompt swap**(§18.5): Stage-aware write path + no-live-mutation test로 gate 없는 swap 차단.

---

## ai-agent-harness-optimization — 개발 계획

### 1. 역할·목표 위치 + 처리결정 + 근거
- **플랫폼 위치(전략 §11 Platform):** 이 레포의 목표 위치는 **Shared reference implementation**이며, 정비 후 **C4 eval-stats(§8 표)의 seed**로 승격된다. 코드 상 정체성은 census §2.10이 규정한 대로 "외부 에이전트 하니스에 임베드되는 결정적 측정·분석 control plane"(스크립트가 측정/계산→JSON/CSV, LLM이 해석)이며 *러닝 제품이 아닌 reference scaffold*다. 따라서 §3.2 결합 규칙상 Contracts Layer(C4) 기여자이자 Platform 공용 통계 라이브러리의 canonical 정의처가 된다.
- **처리결정: 재구성(§11).** census가 식별한 세 결함 — (a) `skills/contracts.py`의 pydantic 스키마를 어느 런타임 스크립트도 import하지 않는 **schema↔runtime 단절**, (b) `run_benchmark.run_single_task`가 `None`만 반환하는 **통합 seam stub**(전체 파이프라인이 실수치를 못 냄 = 최대 갭), (c) **테스트 0 + pyproject/빌드 부재** — 때문에 기능 추가가 아니라 골격 재구성이 선행돼야 한다.
- **근거:** "테스트0 레포에 기능추가"는 §안티패턴 위반이고, §8 C4가 "AHO를 seed로 하되 선행조건 충족 후 승격"으로 명시. 핵심 IP(promote/rerun/reject threshold)가 무검증 상태이므로 검증 substrate를 먼저 세운다.

### 2. 계약 입출력
- **Produces(C4 eval-stats):** statistical comparison 산출물 — paired bootstrap CI(`bootstrap_ci.py`의 stdlib 10k 리샘플), paired Cohen's d + paired t + 95% CI(`compare_ab.py`), 그리고 §8 C4가 요구하나 현재 **미구현**인 **exact McNemar / FDR(Holm·Bonferroni) / power·MDE**(현 코드는 McNemar 부재, FDR는 `quality_check.py` 문자열 안내뿐). 이들을 C4 표면으로 정식 구현·노출한다.
- **계약 통합:** 현재 산출물은 느슨한 dict/CSV(`statistical_summary.json`, `bootstrap_ci.json`)다. `contracts.py`의 `AnalysisRequest`/`AnalysisResult`/`ExperimentPlan`/`QualityGateResult`/`RoutingDecision` pydantic 모델을 **런타임 스크립트가 실제 입출력으로 import**하여 schema↔runtime 단절을 해소(census §2.10, P0). 산출 JSON은 모델 직렬화로 검증되며 C2 Evaluation Annex(`evaluation-run.schema.json`)와 어휘를 정렬한다 — 단 **status는 passed|failed|inconclusive만**, T3 어휘(promote/hold/rollback) 금지(§5/§15 Evaluation Gate). 현 `interpret`/`QualityGateResult`의 `promote/rerun/insufficient_evidence/reject` 어휘는 T2-내부 판정이며 release decision이 아님을 문서·테스트로 고정한다.
- **C4 consumer:** EvalVault(T2 regression gate 통계 백엔드), reverra-gate(T3 `comparator`의 paired bootstrap/McNemar 검증), AIA(`aia-classification` statistics, ANS `stats`). 즉 §5 statistical evaluation이 T2/T3로 피드한다.

### 3. EPIC 매핑 + 레포-특화 작업 (EPIC-003, Q2W3-4 병렬)
- **pyproject 추가:** Python ≥3.11, `package=true`, 런타임 deps는 stdlib-first + optional `scipy`/`sklearn` extras. uv·ruff·pytest·mypy·pip-audit CI(SO/ATS 선례). 현재 빌드 부재 해소.
- **contracts.py 런타임 통합:** `run_benchmark`/`compare_ab`/`quality_check`/`bootstrap_ci`/`orchestrate`가 `contracts` 모듈을 import해 입력 검증·출력 직렬화. 느슨 dict 제거.
- **run_single_task stub 제거 + HostRunner Protocol:** `run_single_task`의 `None`-반환 TODO를 제거하고 `HostRunner` Protocol(`run(task_id, config, seed) -> TaskResult`)을 정의. `run_paired_benchmark`가 주입된 runner를 호출하도록 의존성 역전 → 호스트 하니스(SO·PromptOptimizer)가 실제 러너를 구현/주입.
- **deterministic fake runner:** seed 고정 합성 결과를 내는 `FakeHostRunner` 제공(오프라인·재현 가능). `compare_ab`/`bootstrap`/`quality_check` 테스트와 sample benchmark가 이를 substrate로 사용(§3.2 offline-by-default, §15.6).
- **테스트:** `compare_ab`(pair_results, cohens_d, paired_t, interpret 4분기: rerun/promote/insufficient/reject), `bootstrap_ci`(seed 재현, CI excludes-zero), `quality_check`(7검사) + 신규 McNemar/FDR/power·MDE 테스트. 30+ 목표.
- **scipy fallback 통일(§5 L2 불일치):** 현 `compare_ab.confidence_interval_t`의 `t_crit = 1.96 if n>=30 else 2.0 + 4.0/n`(부정확)과 `p_value = None`("scipy_required") 분기를 **stdlib 정확 t-분포 근사(Student-t inverse CDF) 단일 구현**으로 교체, scipy 유무에 무관하게 동일 결과를 보장. ml-optimizer의 `sklearn 미설치 KNN fallback`도 동일 원칙(silent 열등 fallback 제거, fallback 사실을 산출에 명시). → census가 지목한 "silent 열등 fallback" 해소.
- **C4로 정리:** 통일된 통계 함수를 `eval-stats` 표면(bootstrap/McNemar/FDR/Cohen's d/power·MDE)으로 추출·문서화하여 승격 후보로 정리.

### 4. 시퀀싱
- **Phase 0 (이번 주, §17 액션 6):** **runner stub 제거 PR 착수** — `run_single_task` `None` 제거 + `HostRunner` Protocol + `FakeHostRunner` 최소판. 동시에 S1 `project-state.json` 발행(test_status·risk_flags 노출, §8 S1 / 12 레포 전원 발행 기준). pyproject 골격.
- **Q2 (EPIC-003, Q2W3-4 병렬, EPIC-001/002와 병행):** contracts 런타임 통합, fallback 통일, McNemar/FDR/power·MDE 구현, 테스트 30+, sample paired benchmark.
- **Q3 (C4 승격):** 선행조건 전부 green 후 `eval-stats`를 evidenceops-contracts(C4)로 추출·발행, 한 consumer(reverra-gate comparator 또는 EvalVault analysis)부터 점진 마이그레이션(빅뱅 금지). EPIC-004 PromptOptimizer가 AHO runner를 소비.

### 5. DoD
- **§11 레포 DoD:** sample benchmark 성공(FakeHostRunner로 end-to-end 실수치 산출) + coverage **60%+**.
- **EPIC-003 DoD:** `run_single_task` stub 제거 · `HostRunner` Protocol 존재 · deterministic fake runner · 테스트 **30+** · sample benchmark · coverage 60%+.
- **C4 선행조건(§8) 전부 충족:** pyproject · contracts↔runtime 통합 · stub 제거 · 테스트 30+ · deterministic fake runner · scipy 미설치 fallback 통일 · sample paired benchmark.
- **부가:** Evaluation Gate(§15) — pair 수·method·seed·CI·multiple-comparison correction·metric direction 기록, **status에 T3 어휘 없음**. §15.6 `test_offline_network_block.py` 통과(러너·통계 모두 네트워크 0).

### 6. 의존성
- **자기 선행(self-precondition):** C4 승격은 이 레포 정비(§8 7개 선행조건)에 의존 — 외부 의존이 아니라 내부 정비가 게이트.
- **하향 의존(§3.2):** C4는 Contracts Layer이므로 Platform/Applications가 단방향 소비. **PromptOptimizer(EPIC-004)가 C4 통계 + AHO `HostRunner` runner를 소비**(§12 루프: candidate→HarnessRunRequest→EvalVault→RegressionGateReport→**C4 stats**→reverra-gate). 따라서 EPIC-004는 003에 의존(§16 의존 그래프).
- **상류 정렬:** C2 Evaluation Annex 어휘(EvalVault 발행)와 산출 schema 정합 유지.

### 7. 리스크·완화 (census 근거)
- **테스트 0 → 핵심 IP 무검증:** threshold(n≥10·p<0.05·d≥0.2·CI≠0)가 회귀 없이 바뀔 위험. **완화:** EPIC-003 테스트 30+를 기능 추가의 전제로(테스트0 레포 기능추가 금지 안티패턴).
- **통합 seam stub:** `run_single_task` `None` → 전 파이프라인 무실측. **완화:** Protocol 역전 + fake runner로 seam을 테스트로 강제.
- **silent 열등 fallback:** scipy 없을 때 부정확 t_crit/누락 p-value, sklearn 없을 때 KNN. **완화:** stdlib 정확 단일 구현으로 통일, fallback 사실을 산출 필드에 명시(silent 금지).
- **파일규약 결합(brittle):** 스크립트가 `raw_results.csv`/파일명 규약으로만 연결, 공유 import 없음. **완화:** `contracts` 모델을 단일 데이터 계약으로 삼아 파일명 결합을 schema 결합으로 대체.
- **무관 자산·보안:** `docs/.../papers` fetcher가 SSL 검증 끔 → C4 추출 범위에서 배제, 패키지 경계 밖으로 격리.

---

# C. Applications Layer

## verbera — 개발 계획

### 1. 역할·목표 위치 + 처리결정·근거
**목표 위치: Applications Layer / Workflow Action Kernel** (전략 §3.2, §11 Applications 행). verbera는 그래프-그라운드 governed-action 에이전트로, `router.QueryRouter`(LLM 없는 3경로 키워드/사전 라우팅: document_lookup/relationship_process_lookup/action_request) → `LocalRetriever`(route→`GraphStore` 호출) → `propose.StubActionProposer` → `execute.run_action_workflow`(validate→blocked/paused/ready, 멱등 ledger 예약→상태전이→outbox→audit)로 구성된다. **처리결정 = 유지·집약**(§11): 라우팅(휴리스틱·회복가능)/검증(결정적·고정순서)/실행(멱등 상태머신·outbox) 분리 커널은 가치가 높아 유지하되, census(§1.3, §2.6)가 지목한 **GraphStore 이중구현(InMemory Python set + Postgres SQL CTE의 3채널 RRF 두 벌)** 을 단일 retrieval Protocol로 집약한다. **근거(코드)**: `adapters/graph_store/base.py`의 ~28 추상메서드를 `in_memory.py`·`postgres.py`가 수작업으로 미러링하며, 특히 `search_documents`(in_memory 146–213, postgres 190–309)가 동일 3채널(lex 형태소교집합 / dom 사전가중 / trg overlap)을 두 언어로 중복 표현해 drift가 최대(§5 P1, drift L3). verbera는 evidence producer로서 권위 사슬(§5)에서 release 결정권이 없는 Applications 계층 커널이다.

### 2. 계약 입출력
**Produces**: workflow/action evidence(§4.2 producers VB2). 현 `domain/models.py`의 `TextEvidence`/`GraphPathEvidence`/`StateEvidence`/`ActionRuleEvidence`/`RetrievalBundle`(fusion_breakdown), `ActionExecutionLedgerEntry`, `SideEffectOutboxEntry`, `ValidationVerdict`가 워크플로 증거다. C1(evidence-contract)에 대해 **mirror, not fork**(§3.2)로 `EvidenceRef`/`Claim` adapter를 추가해 emit한다 — verbera 내부 evidence 형태를 canonical C1(`source_app=verbera`, `object_id`, `observed_at` ISO-8601 UTC, `permission_scope`, `source_tier`, `content_hash` → `canonical_id` Option B helper, §8 C1)로 매핑한다. canonical seed는 GWS이므로 verbera는 소비·미러만 한다(내부 복사본 금지). **Consumes/contributes C5 ko-text**: `lexical/analyzer.py`의 `KiwiAnalyzer`(kiwipiepy try/except gated)와 `RegexAnalyzer`, `lexical/scoring.py`의 한국어 BM25-계열 RRF(형태소 lex 채널)가 C5 후보. **C7 authority-tiers**: validate.py가 `actor_roles`/`allowed_roles`(RBAC) 결정적 검증을 수행하나 이는 도메인 RBAC이며 C7 source-tier와 분리 매핑한다. **권위 불변식(§5 강제)**: verbera는 routing(회복가능)과 validation(결정적, `VALIDATION_DISPATCH` 고정순서 RBAC→State→Provenance→Evidence→Risk→Idempotency→Temporal, 첫 non-None short-circuit)을 분리 유지하며 **promote 안 함** — evidence/verdict만 생산하고 release decision(T3)은 reverra-gate, 인증은 ai-tool-suite가 담당한다. C1 emit 시 verdict status(blocked/paused/ready/duplicate/executed)에 T3 어휘(promote/hold/rollback) 혼입 금지.

### 3. EPIC 매핑 + 레포-특화 작업 (EPIC-005, Q3 / §16)
**(a) `RetrievalQuerySpec` + `GraphStore.execute_retrieval` Protocol 도입**: `base.py`에 backend-중립 `RetrievalQuerySpec`(expanded_tokens, matched_canonicals, normalized_query, limit, channel weights)와 `execute_retrieval(spec) -> list[ChannelRow]`(채널별 document_id/raw_score/rank만 반환)을 추가한다. **RRF 단일화**: 현재 RRF 융합 자체는 `lexical/scoring.py:reciprocal_rank_fusion`/`RankingWeights(lex1.0/dom1.5/trg0.3/vec0.0, k=60)`로 공유되지만 **채널 후보 산출·랭킹**이 두 벌이다(in_memory `search_documents` Python set 교집합 + 정렬, postgres 동일 로직 SQL CTE lex/dom/trg). 두 `search_documents`를 공유 `search_documents(spec)` 단일 메서드로 끌어올려 `execute_retrieval`만 backend-특화로 남기고, RRF·TextEvidence 조립·provenance(`retrieval_route`/`source_document_ids`/`matched_canonicals`)는 base/공유 모듈에서 1벌로 수행한다. **(b) SQL parameterization**: `postgres.py`의 `_sql_literal`/`_sql_text_array` 문자열 인터폴레이션(34–38행) + `psql` subprocess(`_psql` 106–119)를 파라미터 바인딩 + connection pooling 기반(예: psycopg, offline-lazy import §3.2)으로 교체한다 — 현 `transition_request_state`/`record_action_execution_reservation`/outbox UPDATE 등 모든 mutation·select가 대상. **(c) Homebrew psql 경로 제거**: `config.py:18`·`postgres.py:88`(`/opt/homebrew/opt/postgresql@16/bin/psql`)·`test_support.py:32-34`의 하드코딩 절대경로를 env/config 기반 DSN으로 외부화(§2.6 환경 하드코딩, §11 ATS 절대경로 패턴과 동형). **(d) embeddings/vec stub 처리**: `embeddings.py`(32-d SHA256 placeholder)·RankingWeights.vec=0.0·`default_fusion_breakdown`의 vector 0.0을 inert로 명시 문서화·테스트로 잠그고(미활성 채널 = 0 기여), `execute_retrieval` Protocol에 vec 채널 hook만 예약(활성화는 deferred). **(e) C1 EvidenceRef mirror**: §2의 adapter 추가(EPIC-005 산출물에 evidence emit slice 포함).

### 4. 시퀀싱
**Q3 중심 = EPIC-005**(3주, §16). W1: `RetrievalQuerySpec`/`execute_retrieval` Protocol 설계 + base 공유 RRF 추출(채널 산출만 backend별) + InMemory 우선 마이그레이션. W2: Postgres `execute_retrieval` 구현 + SQL parameterization·pooling·Homebrew 경로 제거. W3: golden parity 고정 + embeddings/vec stub 잠금 + C1 EvidenceRef mirror adapter. **Q2 병렬·경량**: S1 project-state 발행(§8 S1, schema_version/role=Workflow Action Kernel/maturity=Prototype/source_path repo-relative/현재 Stage 노출) + C1 정렬 준비(EvidenceRef adapter 스펙, EPIC-001 fixture roundtrip 참여). EPIC-001(C1) 발행이 §2 mirror의 선행이므로 Q2에 C1 diff matrix 기여만 하고 본 emit은 Q3 W3로 정렬.

### 5. DoD
- **§11 DoD: InMemory/Postgres golden parity** — 동일 query/scenario에 대해 두 backend `search_documents` 결과(document_id 순서, RRF score, provenance)와 모든 evidence/ledger/outbox 메서드 출력이 byte-동일. 기존 `tests/unit/test_graph_store.py`·`tests/unit/test_validation_verdict_parity.py`·`tests/integration/test_postgres_backend.py`를 parity golden로 확장.
- **EPIC-005 DoD(§16)**: 단일 RRF 구현(채널 산출 외 중복 0건, grep으로 강제), SQL 전건 parameterization(`_sql_literal`/`_sql_text_array` 호출 0건 또는 안전 바인딩 전환), Homebrew 절대경로 0건, vec/embeddings stub 명시·잠금.
- **§18.5 Stage DoD**: 모든 workflow action write path(`execute.run_action_workflow`·`_execute_ready_action`의 `transition_request_state`/`record_*`/outbox)는 **stage-aware**. Stage0(dry-run)/Stage1(read-only)에서 mutation 미실행 테스트 강제. **멱등 실행은 Stage2/3 경계** — 현 `checkpoints.reserve_action_execution`(sha256 canonical idempotency-key dedupe) + ledger `ON CONFLICT DO NOTHING`은 Stage2(sandbox/isolated branch) 진입 조건이며, Stage3 production gated write는 `parent_approval_id`+T3 decision+operator approval 필수(verbera는 T3 미보유 → Stage3 write는 외부 gate 통과 후에만). 현재 Stage를 S1에 노출.
- **회귀**: 169 test green 유지, `python3 -m compileall src verbera` 통과, milestone_1_bilingual_eval `top_3_hit_rate ≥ 0.90` 불변, `.omx` continuity(`release_contract.py`/`release_bundle.py`) 보존.

### 6. 의존성
- **선행**: EPIC-001 C1(evidence-contract) 발행 — §2 EvidenceRef/Claim mirror의 선행(Q3 W3 emit 전 C1 package·canonical_id helper 필요). C5 ko-text·C7 authority-tiers 추출은 verbera analyzer/RBAC 코드가 기여(병렬, blocking 아님 — verbera는 stdlib-only core 유지하며 lazy import).
- **병렬**: EPIC-005는 Q3에서 다른 EPIC과 독립 병렬(§16 의존도). S1 발행은 Phase 0/Q2 병렬.
- **하향 의존만(§3.2)**: verbera → (C1/C5/C7 contracts). reverra-gate/ai-tool-suite로의 수평 import 금지 — evidence는 S1/C1 형태로만 노출. ATS·SO는 verbera project-state를 read-only 소비(§4.1).

### 7. 리스크·완화
- **GraphStore 이중구현 drift(census 최대 리스크, L3)**: 두 `search_documents`/~28 메서드 미러가 silent 분기. 완화 = `execute_retrieval` Protocol로 backend-특화 표면 최소화 + golden parity 테스트가 회귀 gate(병합 차단).
- **문자열 SQL(`_sql_literal` injection·풀링 없음·subprocess 오버헤드)**: parameterized 바인딩 + connection pool로 전환, offline gate(§15.6) 충족 위해 SDK lazy import·offline stub·network 차단 테스트 추가. 마이그레이션은 빅뱅 금지 — 메서드 단위 점진 전환, 각 단계 parity 통과를 DoD로.
- **embeddings/vec stub(가짜 의미검색 위장)**: 32-d SHA placeholder·vec=0.0을 inert로 명시·테스트 잠금, fusion_breakdown vector 0.0 불변 검증으로 "활성화된 척" 방지. 활성화는 별도 EPIC으로 deferred.
- **KiwiAnalyzer 게이트 회귀(C5)**: `store_factory`가 regex-only 강제(legal gate). C5 추출 시 analyzer를 contract로 올리되 stdlib-only core·try/except 게이트·라이선스 ADR(`docs/adr/lexical-analyzer-license-gate.md`) 유지.
- **Stage 경계 누수**: workflow action이 Stage0/1에서 write할 위험 → write path stage-aware 가드 + 테스트 강제(§18.5 엄격 적용 대상 verbera).

---

## grounded-workspace-os — 개발 계획

### 1. 역할·목표 위치 + 이중지위 + 처리결정

grounded-workspace-os(GWS)는 EvidenceOps Platform 3-Layer 중 **Applications Layer**에 속하는 **Workspace Certified Tool**이다(전략 §3.2·§11 Applications 표). 코드 근거(census §2.7): Google Workspace-native 근거기반 에이전트 백엔드 — `tool_gateway`가 googleapis 유일 egress, `evidence_kernel`이 미지원 claim을 거부하고 risk≥3 승인을 강제하며, `write_previews`→`write_execute`가 단일사용 승인토큰+payload digest로 쓰기를 게이트한다. 부모 시스템(SO dispatch, ATS 인증)이 오케스트레이션하도록 설계된, ai-tool-suite가 인증·소비하는 폐쇄망 인증팩이다.

**이중지위**(§11 "GWS 이중지위"): (a) Applications의 certified tool인 동시에, (b) **C1 evidence-contract의 canonical seed 기여자**다. census §4.3·전략 §8이 명시하듯 `packages/schemas/evidence.py`의 `EvidenceRef`/`Claim`이 SO `ClaimRef`(mirror), LRV `provenance.to_evidence_ref`, RG `AuditEvidence`가 수렴하는 canonical 정의처다. 단 §11 단서대로 **GWS 전체를 Platform core로 승격하지 않는다** — seed로서 형태(shape)만 evidenceops-contracts C1으로 추출하고, GWS 자신은 Application으로 남아 발행된 C1을 mirror로 역소비한다.

**처리결정 = 유지·집약(§11):** 신규 작성·재구성이 아니라, 코드는 유지하되 in-memory 상태를 영속화로 집약하고 evidence 모델을 C1과 정합한다.

### 2. 계약 입출력

**C1 canonical seed 제공(권위 발행 측):** `EvidenceRef`(id/source_app/source_object_id/observed_at/collected_at/permission_scope/confidence)와 `Claim`(text/claim_type∈{fact,inference,recommendation,uncertainty}/evidence_ids/confidence)을 evidenceops-contracts C1 seed로 제공한다. **현 코드 갭**: evidence.py에 `source_tier`(C7/T0–T4), `content_hash`, `canonical_id`가 없다. 전략 §8 C1 규칙 `canonical_id = sha256(canonical_json({source_app, object_id, observed_at(ISO-8601 UTC), permission_scope, source_tier, content_hash}))`(key sort/UTF-8/NFC)을 흡수하려면 GWS가 이 필드들을 C1 seed 사양에 기여하고, v0.1.0의 `canonical_id()` helper(Option B) + NormalizedEvidence export 시 `evidence_id` materialize 규약을 따른다.

**produces:** `GroundedRecommendation`(claims/evidence/unknowns/conflicts/proposed_actions/risk_level 0–4/execution)과 그 안의 `EvidenceRef`. 이는 ATS가 인증·정규화할 산출 evidence다(원천 evidence producer 권위, §5).

**consumes:** C1 발행 후, GWS는 자체 evidence.py를 **mirror로 전환**해 발행된 C1 binding을 import하고 내부 복사본을 제거한다(§3.2 "mirror, not fork"). 역방향(Contracts→GWS) 의존은 금지.

**권위 불변식:** GWS는 evidence producer이며 **release 결정을 내리지 않는다**(§5). 승인-게이트 쓰기(`write_previews`/`write_execute`/`evidence_gate`)는 그대로 유지하되, 실제 promote/hold/rollback 판단은 상위(T3 RG/ATS)에 위임한다.

### 3. EPIC 매핑 + 레포-특화 작업

**EPIC-001(C1 evidence-contract) 기여:** Phase 0 액션 5의 **C1 field diff matrix(GWS/SO/LRV/RG/ATS)**에 GWS가 canonical 정의처로 참여한다. 작업: (a) evidence.py 필드 인벤토리를 SO `ClaimRef`·LRV `to_evidence_ref`·RG `AuditEvidence`와 대조한 diff matrix 제출, (b) C1 SPEC에 `source_tier`/`content_hash`/`canonical_id` 규칙(§8)을 seed로 기여, (c) 3+ repo fixture roundtrip을 위한 GWS fixture 제공.

**§11 정돈 작업(census §2.7 리스크 해소):**
- **OAuth/session 영속화 (DoD 핵심):** `tool_gateway/oauth.py`의 `_TOKEN_STORE`/`_TOKEN_OBTAINED_AT` in-memory dict와 `api_gateway/chat_state.py`의 `_MEMORY_FLOW`/`_MEMORY_DAILY_START_SEEN`/`_MEMORY_LAST_INTENT`를 persistent store로 전환(수평확장 가능). 이미 존재하는 `FirestoreApprovalStore`/Firestore idempotency store 패턴을 재사용해 OAuth token store와 chat session state에 동일한 Protocol+Firestore impl seam을 적용한다. Secret Manager 영속 경로(`_persist_token_secret`)는 token용으로 유지하되 production에서 in-memory가 active store가 되지 못하도록 강제한다.
- **followups 다국어 draft를 데이터로:** `api_gateway/followups.py`(813 LOC)·`agent_runtime/reply_draft.py`의 하드코딩된 다국어 draft/template를 policy/recipes YAML 데이터로 외부화(census "다국어 draft 하드코딩").
- **evidence_kernel gate를 C1 정합:** `evidence_kernel/gate.py`의 unsupported-claim 거부·risk≥3 승인강제 로직이 C1 evidence_gate 규칙(§15: claim은 evidence_refs 또는 unsupported=true, confidence∈[0,1], source_tier 필수, permission_scope 필수)과 정합하도록 검증을 확장한다.

### 4. 시퀀싱

- **Phase 0(이번 주):** C1 field diff matrix(액션 5)에 GWS 참여 + C1 seed 사양 기여(`source_tier`/`content_hash`/`canonical_id`). 코드 변경 없이 SPEC·fixture·diff 산출. S1 project-state 발행(12 레포 공통, 현재 Stage 노출 §18.5 포함).
- **Q2:** evidenceops-contracts C1 v0.1.0 발행 후 GWS의 **C1 mirror 전환** — evidence.py 내부 모델을 발행 binding import로 교체, contract test(roundtrip/canonical_id deterministic) 통과. 이는 EPIC-001 첫 consumer migration 후보(§16).
- **Q4:** **OAuth/session 영속화** 완료 — Firestore/persistent store 전환, in-memory production state 0건 달성, runtime guard를 token/session 경로로 확장.

### 5. DoD

- **§11 DoD:** **in-memory production state 0건.** 현 `write_actions/runtime_guard.py`가 approval/idempotency in-memory를 차단하는 패턴을 OAuth `_TOKEN_STORE`·chat `_MEMORY_*`로 확장하여, production 프로필에서 in-memory active store가 거부되는 테스트를 추가한다(`GROUNDING_ALLOW_IN_MEMORY_*` override는 비-production 한정).
- **§15 Security/Evidence Gate:** **OAuth/token in-memory production 금지**(Security Gate 명시) + raw reasoning 미저장·retention 명시 + operator action audit. Evidence Gate: claim은 evidence_refs 또는 unsupported=true, source_tier·permission_scope 필수, content_hash canonical rule, evidence_id deterministic.
- **§18.5 Stage:** 모든 write path는 stage-aware. **Workspace write → Stage 3 전용** — `parent_approval_id` + T3 decision + operator approval 후에만 production write. Stage 0/1에서 write path 미실행을 테스트로 강제(현 `test_live_write_smoke.py`/`test_write_execute.py` 확장), 현재 Stage를 S1에 노출.

### 6. 의존성

- **C1 발행에 seed로 기여(양방향):** GWS는 C1 canonical seed 제공자이자, 발행 후 C1을 mirror로 역소비하는 첫 consumer다(§16 EPIC-001 첫 consumer migration). evidenceops-contracts(C1)와 GWS 간 양방향 관계.
- **ATS가 GWS를 소비:** ai-tool-suite가 GWS를 **인증 대상 adapter**(census §2.2 7개 어댑터, evidence-only 이상 wired)로 ingest·인증한다. GWS는 S1 project-state를 read-only로 발행해 SO/ATS가 소비하게 한다(§8 S1).
- **수평 import 금지(§3.2):** GWS는 다른 Application/Platform 레포를 직접 import하지 않으며 Contracts(C1/C7)에만 하향 의존한다.

### 7. 리스크·완화

- **in-memory state(census 최대 리스크):** OAuth token·chat session이 기본 in-memory → 수평확장 불가·production 부적합. **완화:** Firestore/persistent Protocol seam(이미 approval/idempotency에 존재) 재사용, runtime guard 확장, in-memory production 0건 테스트. (단계적 마이그레이션, 빅뱅 금지.)
- **cross-router private helper import(census §2.7):** `api_gateway` 내부 라우터 간 private helper import가 레이어 경계를 흐림. **완화:** `test_architecture_policy.py`의 Forbidden Imports 검증을 router-간 private import 차단으로 강화하고 공유 로직을 명시적 공용 모듈로 추출.
- **demo.py 비대(1375 LOC):** 데모 코드가 production 경로와 혼재. **완화:** demo를 `apps/` 데모 entrypoint로 격리하고 production 서비스 코드에서 분리, followups 다국어 template 외부화와 병행.

위 모든 정돈은 GWS 기존 게이트(strict mypy, layered boundary 테스트 296함수, offline-by-default §15.6) 통과를 DoD로 한다.

---

## aia-classification-design — 개발 계획

### 1. 역할·목표 위치 (Applications / Korean STT Domain Pack) + 처리결정 + 근거

본 레포는 EvidenceOps 3-Layer(§3) 중 **Applications Layer**에 속하며, 전략 §11·§23 Q5의 결정대로 **Korean STT Domain Pack**으로 자리한다. 코드 실체는 `aia-stt-classification-poc/src/aia_stt_poc`이며, 한국어 보험-STT 상담 발화를 `대 → 중 → 소` 경로로 계층 분류하는 PoC다(`data.LabelPath`, 그래프 ROOT→large(42)→mid(288)→small(467), `graph.py`).

처리 결정은 **통합·정리**(§11 aia-classification 행). 근거는 census §2.8이 적시한 두 분류 경로의 미통합 상태다: (A) 동작하는 LLM-prompting 분류기 `evaluate._classify_hierarchical`(대→중→소 top-down **beam search**+`_rerank_path`, `prompting.py`, `llm.OpenAICompatibleClient`)와 (B) capability/adapter 런타임 스켈레톤(`capabilities/base.CapabilityResolver`가 `configs/model_registry.yaml`로 어댑터 해소). 후자의 핵심 어댑터들은 stub이다 — `classifier_roberta_hierarchical.py`/`classifier_rule_retrieval_baseline.py`는 하드코딩 라벨·score를 반환하고, `embedding_bge_m3.py`/`embedding_kure_v1.py`는 `[0.0]*1024` zero-vector를 반환한다. `runtime/classify_batch.py`·`runtime/train.py`·`runtime/evaluate.py`는 전부 `"""TODO(impl)..."""` 1줄 stub이다. §11.3 결정은 이 모순을 **LLM beam search = primary runtime / capability·ensemble = experimental·deferred / stub 제거(또는 fake namespace) / taxonomy single source / EvalVault-compatible export**로 해소한다.

### 2. 계약 입출력

**produces — classification evidence.** 본 레포는 §5 권위 불변식상 **Evidence Producer**다(evidence 생성·metric 보고 허용, release 결정 금지). 분류 결과를 C1 evidence-contract(§8) 형태로 발행한다: 각 예측을 `EvidenceRef`(canonical seed=GWS, §8 C1) + `Claim`(분류 path = inference claim, `confidence∈[0,1]`, `source_tier` 필수)으로 **mirror**(직접 fork 금지, §3.2). 현 `reports.write_report`가 내보내는 `report.json`(`schema_version:"1.0.0"`, `artifact_kind:"evaluate_report"`, `metrics`, `review_routing`, `output_policy.raw_transcript_in_report=False`)이 그 seed이며, 여기에 C1 `EvidenceRef/Claim` 미러 레이어를 더한다.

**EvalVault-compatible export.** §11/§16 EPIC-006 DoD 핵심. `PredictionRecord`(exact/large/medium/small match, confidence, review_required/reasons) 집합을 EvalVault가 소비 가능한 형태(EvalVault `TestCaseResult`/`EvaluationRun` shape, C2 Evaluation Annex `evaluation-run.schema.json`와 호환)로 변환·export한다. **불변식: status는 `passed|failed|inconclusive`만, T3 어휘(promote/hold/rollback) 금지**(§5, §15 Evaluation Gate). 본 레포는 release 판단을 내리지 않는다.

**consumes/contributes — C5 ko-text·C4 stats.** `analysis/korean_morph.py`(kiwipiepy 싱글톤 `_kiwi()`, content-POS 필터, `preprocessing/steps/entity_correction.py`·`coverage_augmentation.py`·`analysis/stt_quality.py`에서 사용)는 **C5 ko-text seed**로 기여한다(§8 C5: kiwipiepy, jamo, Korean BM25, PII). `statistics.py`의 `mcnemar_test`(statsmodels)·`paired_bootstrap_ci`(numpy 10k)는 **C4 eval-stats** 정합 대상이다(§8 C4: bootstrap/McNemar). **권위: evidence producer** — 어느 출력도 gate decision을 대체하지 않는다.

### 3. EPIC 매핑 + 레포-특화 작업 (EPIC-006, Q2 병렬)

§16 **EPIC-006 (AIA classification runtime 통합, 2주, Q2 병렬)** 전체가 본 레포에 매핑된다.

- **runtime/classify_batch가 LLM beam search 호출(primary runtime).** `runtime/classify_batch.py` 1줄 stub을 실제 entrypoint로 구현해 `evaluate.evaluate_cases`/`classify_text`(strategy="hierarchical", `_classify_hierarchical` beam+rerank)를 호출하게 한다. 즉 capability/ensemble 경로가 아니라 **동작하는 LLM beam search가 batch 런타임의 단일 진입점**이 된다. `runtime/train.py`·`runtime/evaluate.py` stub도 같은 원칙으로 정리(LLM-prompting에 training 단계 없음 → 제거 또는 명시적 not-applicable 문서화).
- **capability/ensemble path = experimental/deferred.** `capabilities/base.CapabilityResolver`, `capabilities/classifier_ensemble.py`(`PathScoreWeights` leaf.45/medium.20/large.15/retrieval.10/rule_cue.10/inconsistency-.30), `configs/model_registry.yaml`의 `aia.classifier.ensemble` 계열을 `status: experimental`로 강등하고 primary runtime 경로에서 분리(deferred). 삭제하지 않되 런타임 기본 경로에서 제외.
- **roberta/rule-baseline/embedding zero-vector stub 제거(또는 fake namespace).** `classifier_roberta_hierarchical.py`·`classifier_rule_retrieval_baseline.py`(하드코딩 라벨 "보험금청구상담>..." score)와 `embedding_bge_m3.py`·`embedding_kure_v1.py`(`[0.0]*1024`)를 **제거**하거나, 테스트 전용 `fakes`/`testing` namespace로 명시 이동해 "어댑터로 위장한 stub"을 종식한다(census §2.8 리스크). registry에서 대응 component를 제거하거나 fake로 라벨링.
- **taxonomy single source.** 현재 taxonomy 정의 3중: (1) `data.py`의 `LabelPath`+`build_taxonomy`(eval case에서 도출), (2) `taxonomy/taxonomy_loader.py`의 `TaxonomyEntry`+`hierarchy_json`/`authority_workbook` 로더·audit, (3) `graph.py`의 networkx DiGraph(`hierarchy_full.json`). 이미 존재하는 `taxonomy_loader.build_taxonomy_audit_report`(count mismatch·only-left/right path diff·reconciliation candidates)와 `runtime/audit_taxonomy.py`를 활용해 **단일 권위 소스(authority_workbook 또는 hierarchy_full.json 중 1)** 를 정하고 나머지를 그로부터 파생(`path_validator.py`·beam candidate generator가 동일 소스 참조)하게 통합한다.
- **EvalVault-compatible result export 추가.** `reports.write_report`에 EvalVault export 경로를 추가(§2).

### 4. 시퀀싱

- **Phase 0 (이번 주, §17 액션 7):** **"AIA LLM beam search = primary runtime" ADR** 작성·기록(`.omc/adr/`에 기존 ADR-001 옆에). capability/ensemble deferred·stub 제거 범위·taxonomy 권위 소스 선택을 ADR로 확정. 동시에 S1 `project-state` 발행(§8 S1, 12 레포 모두 — Phase 0 완료 기준): role=Applications/Korean STT Domain Pack, maturity=PoC, contracts.produces=[C1 classification evidence], consumes=[C4,C5], current Stage 노출.
- **Q2 (EPIC-006, 병렬):** §3 작업 순서 — (a) taxonomy single source 통합 + audit 통과 → (b) `runtime/classify_batch`가 beam search 호출하도록 구현 + 실측 batch 실행 → (c) stub 어댑터 제거/fake namespace + ensemble experimental 강등 → (d) EvalVault-compatible export. 모든 외부 LLM 호출은 §15.6 offline gate 준수(SDK lazy import, offline stub, `OpenAICompatibleClient` loopback-only governance `EndpointConfig`).

### 5. DoD

§11 aia-classification DoD + §16 EPIC-006 DoD 합산:
1. **`runtime/classify_batch` 실측 결과** — 1줄 stub 제거, beam search 호출, 큐레이션 데이터셋에서 실제 `PredictionRecord` 산출·`report.json` 생성(§11 "runtime/classify_batch 실측 결과").
2. **stub 제거** — roberta/rule-baseline/embedding zero-vector 어댑터가 primary 경로·registry에서 제거되거나 fake namespace로 격리(어댑터 위장 0건).
3. **taxonomy single source** — `audit_taxonomy`가 권위 소스 대비 count_mismatch 0(또는 명시 reconciliation), 3중 정의→단일 파생.
4. **EvalVault-compatible export** — export 산출물이 EvalVault `TestCaseResult` shape·C2 annex로 검증 통과, status에 T3 어휘 없음(§15 Evaluation Gate).
5. **EPIC-006 추가 DoD** — capability/ensemble `experimental` 마킹, offline network block test 통과(§15.6), 기존 43 테스트 회귀 없음 + 신규 classify_batch/export 테스트.

### 6. 의존성

- **C5 ko-text**: `analysis/korean_morph.py`(kiwipiepy)가 C5 **seed** — C5 발행 시 본 레포가 첫 기여자이자 향후 소비자(mirror-not-fork).
- **C4 eval-stats**: `statistics.py`(McNemar/bootstrap)가 C4 정합 — C4 승격(§8, AHO seed) 시 본 레포 통계를 단일 구현으로 수렴.
- **EvalVault export 호환**: EvalVault `regression_gate_service`/`EvaluationRun` shape + C2 Evaluation Annex와의 schema 호환에 의존.
- **C1 mirror**: EvidenceRef/Claim canonical(GWS seed) 발행에 의존하며 adapter로 미러(EPIC-001 산출물 소비).

### 7. 리스크·완화

- **두 분류 경로 미통합**(census §2.8): §11.3대로 LLM beam search를 단일 primary로 확정하고 `classify_batch`를 그 유일 진입점으로 — ADR(Phase 0)로 결정 고정해 재발 차단.
- **stub이 어댑터로 위장**(하드코딩 라벨·zero-vector): 제거 또는 fake namespace 격리 + registry 정합 테스트로 "동작하는 척하는 어댑터"가 evidence를 오염시키지 못하게 한다.
- **taxonomy 3중**: `audit_taxonomy`/`build_taxonomy_audit_report`의 기존 diff 인프라를 DoD 게이트로 승격해 단일 소스 강제.
- **analysis 4.4k 리포트 생성기**(src ⅓): primary runtime·export와 무관한 리포트 코드가 통합 범위를 키우지 않도록 EPIC-006 scope에서 분리(분석 모듈은 deferred 정돈 P2). 통합 범위는 classify_batch·stub·taxonomy·export 4개로 한정해 §19 Integration Capacity Rule(active ≤3, scope freeze) 준수.

---

## aia-awesome-novel-studio — 개발 계획

### 1. 역할·목표 위치 + 처리결정 + 근거

- **목표 위치(전략 §3 Applications / §11):** 본 레포는 EvidenceOps **Applications Layer**의 **Korean Dialogue/STT Eval Pack**(도메인 팩)이다. 처리 결정은 §11 Applications 표의 **유지·정돈(verbatim)**.
- **정체성 정정(census §2.9 / §0):** 레포명·플러그인(`skills/`·`agents/` 63 MD, `.claude-plugin/plugin.json` v1.2.0)은 "소설 스튜디오"를 표방하나 **코드상 그것이 아니다.** 실제 코드는 `tools/llm_eval/`(평가킷 ~18k), `tools/llm_eval_gui/`(FastAPI+React GUI ~3.2k+8k ts), `tools/stt_pipeline/`(L0–L10 STT 증강 ~2.2k)로, **한국어 금융도메인 대화/STT 응답 오프라인 replay A/B 평가킷**이다. "novel studio" 정체성은 비-코드 Claude 플러그인 레이어에만 존재. 계획은 **코드 기준** — 평가킷으로 다룬다.
- **근거:** census §1.2 DNA #5(kiwipiepy 형태소 NLP 반복), #6(paired bootstrap·McNemar·FDR/Holm 통계 엄밀성 반복) — 본 레포가 그 반복의 한 노드. 따라서 §5 추출표 **L2 eval-stats(C4)·L3 ko-text(C5)** 의 seed 후보로 등록되며, 처리결정은 폐기·통합이 아닌 정돈이다.

### 2. 계약 입출력 (produces / consumes / 권위)

- **Produces(증거 생산자):** 한국어 대화/STT 평가 evidence. `run.py` 산출(`ReplayRecord` JSONL v1.0, stages[])과 `regression_gate.py`의 A/B gate report가 산출물. **C2 Evaluation Annex 호환** 대상 — 즉 `evaluation-run.schema.json`/`regression-gate-report.schema.json` 형태로 정렬한다(§8 C2). **status 어휘는 `passed|failed|inconclusive`만**(T2 권위). RegressionGateReport는 C3 GateDecision **입력일 뿐** 그 자체가 release decision이 아님.
- **T3 어휘 금지(§15 Evaluation Gate):** 현 코드 `winner.py`는 `🟢 clear_win/🟡 numeric_better/🔴 regression/⚪ inconclusive` 플래그를 쓰고 `regression_gate.evaluate_gate`는 PASS/FAIL_REGRESSION/BLOCKED를 낸다. status·report 필드 어디에도 **`promote|hold|rollback`(T3) 가 없어야** 한다. winner/decision flag는 T2 어휘로 한정(자체 winner 판정도 T2 어휘로만).
- **Consumes/Contributes(양방향 seed):**
  - **C4 eval-stats:** `tools/llm_eval/stats.py`(`paired_bca_bootstrap`, `wilcoxon_paired`, `rank_biserial_paired`, `cles`, `adjust_pvalues`=BH/Holm, `min_sample_for_effect`=MDE, `paired_compare`, `bootstrap_is_stable`)은 **C4 seed 후보**. 발행 후 C4를 consume(내부 복사 금지, adapter mapping).
  - **C5 ko-text:** `ner.py`(338, kiwipiepy)·`jamo_fuzzy.py`(190)·`ko_numbers.py`(208) + classical_metrics/clustering/summary_quality의 kiwipiepy 사용은 **C5 seed**. 발행 후 C5를 consume.
- **권위(§5 불변식):** 본 레포는 **Evidence Producer** — evidence 생성·metric 보고만 허용, **release 결정 금지.** EvalVault(T2)·reverra-gate(T3)와의 어휘 정합을 깨면 breaking change.

### 3. EPIC 매핑 + 레포-특화 작업

본 레포는 §16 6개 EPIC의 직접 owner가 아니다(§6 로드맵 P2 + §5 L2/L3 seed 기여). EPIC-001(C1)·EPIC-002(MVP) 직접 대상 아님. 기여 경로: **C4/C5 추출(§5 L2/L3)** 의 seed 제공·마이그레이션, EvalVault C2 annex(§11 EvalVault DoD)와의 status 어휘 정합.

§11 정돈 4작업(verbatim 근거):
1. **`regression_gate.py`(1,914 LOC) 분해** — 단일 파일이 LLM 생성(`_run_llm_generation`, `run_ab_eval`, `_calibrate_timeout`), 통계/diff(`compute_ab_diff`, `evaluate_gate`), 리포트/Excel(`generate_gate_report`, `_print_summary`, `export_excel` 연동), CLI(`_build_parser`, `main`/`_main_inner`, run-state I/O)를 한데 묶고 있음. **LLM / stats / Excel·report / CLI 4모듈로 분리**(stats 부분은 C4 seed로 재사용, 한국어 criteria 추출 `_extract_semantic_criteria`는 C5 정렬).
2. **fastapi/uvicorn pyproject 선언** — `pyproject.toml`(19 deps)·`requirements.txt` 어디에도 fastapi/uvicorn/sse가 없으나 `backend/app.py` + 8+ API 모듈(`runs.py`·`models.py`의 `StreamingResponse` 등)이 fastapi를 import. GUI 의존을 `[project.optional-dependencies]`에 `gui` extra로 명시 선언(SSE 라이브러리 포함).
3. **frontend smoke test 도입** — React SPA(10페이지: Dashboard/NewRun 1024/Influence 742/ConfigBuilder 977) **무테스트.** 최소 빌드+렌더 smoke test(Vitest 등)로 백엔드 계약 미러 깨짐 조기 검출.
4. **GUI↔엔진 stderr 로그결합 완화** — `run_manager`가 `python -m tools.llm_eval.run` subprocess spawn 후 stderr를 SSE phase로 파싱(fragile). stderr 텍스트 포맷 파싱 대신 **구조화 phase 이벤트**(JSON line)로 엔진↔GUI 계약을 분리.

추가: **C4/C5 추출 기여** — stats.py/ko-text 모듈을 §5 발행물의 seed로 제출하고, 발행 후 한 모듈씩 마이그레이션 + 계약 테스트(빅뱅 금지).

### 4. 시퀀싱

- **Q2 (deps 선언·C5/C4 정렬):** ① fastapi/uvicorn(+sse) `gui` extra 선언(저위험·즉시) — census P2 미선언 deps 해소. ② stats.py를 **C4 seed**로, ner/jamo/ko_numbers를 **C5 seed**로 정렬(인터페이스 식별·중복 출처 등록, §5 L2 2순위·L3). ③ status/winner 어휘를 T2(`passed|failed|inconclusive`)로 점검, T3 어휘 부재 확인(§15 Evaluation Gate). EvalVault C2 annex 발행과 status 어휘 정합.
- **Q4 (regression_gate 분해·frontend test·domain pack 정착):** ④ `regression_gate.py` LLM/stats/Excel/CLI 4모듈 분해(module당 500 LOC 이하). ⑤ frontend smoke test 도입 + GUI↔엔진 stderr 결합 완화(구조화 이벤트). ⑥ Korean Dialogue/STT Eval Pack을 Applications domain pack으로 정착(C2 annex export·C4/C5 마이그레이션 완료).

### 5. DoD

- **§11 DoD(verbatim): module당 500 LOC 이하** — `regression_gate.py` 분해 후 각 신규 모듈 ≤500 LOC(현 1,914 → 4모듈). 함수 경계(20–1638행)가 이미 LLM/stats/report/CLI로 군집화돼 있어 자연 분할.
- **§15 Evaluation Gate:** pair 수·statistical method·seed(B=10000/seed42/alpha0.05/fdr_bh)·CI·p-value correction·metric direction 기록 + **status에 T3 어휘 없음**(winner/decision flag 포함).
- **§15.6 Offline Gate:** `test_offline_network_block.py` 존재, default CI가 public internet 없이 통과(현 dev extra의 pytest-socket 활용), live(Ollama/OpenAI)는 별도 integration profile. SDK lazy import.
- fastapi/uvicorn 선언으로 GUI가 깨끗한 환경에서 설치·기동; frontend smoke test 통과; 기존 백엔드 ~342 test 회귀 없음.

### 6. 의존성

- **C4/C5 추출 양방향(seed):** 본 레포는 C4(eval-stats)·C5(ko-text)의 seed 제공자이자 발행 후 소비자. 단방향 의존 아님 — 발행물 인터페이스 합의에 본 레포 stats.py/ko-text 형태가 입력으로 반영(§5 L2/L3 중복 출처에 ANS 명시). C4는 AHO seed와 통합 정확도 통일 필요(census §5 L2 fallback 불일치 경고).
- **EvalVault 평가 어휘 정합:** EvalVault RegressionGateReport(§11 DoD: T3 어휘 없음)와 본 레포 gate report가 **동일 C2 Evaluation Annex 어휘**를 공유해야 함. status enum·field 정합 필수.
- **수평 import 금지(§3.2):** 다른 Application/Platform 레포 직접 import 금지 — C4/C5/C2 계약 패키지를 통해서만 연결(mirror not fork).

### 7. 리스크·완화 (census §2.9 근거)

- **1,914 LOC monolith:** 분해 중 회귀 위험 → 함수 단위 추출 + 분해 전후 동일 gate report golden 비교 테스트로 행위 동등 보존.
- **미선언 deps(fastapi/uvicorn):** 깨끗한 환경에서 GUI ImportError → `gui` extra 명시 + CI에서 extra 설치 후 backend import smoke.
- **프론트 무테스트:** 백엔드 스키마 미러(`schemas.py`↔프론트) drift 무검출 → smoke test + 가능 시 백엔드 스키마에서 타입 생성.
- **stderr 결합(fragile):** 로그 포맷 변경이 GUI phase 파싱을 무음 파손 → 구조화 phase 이벤트(JSON)로 계약화, stderr 파싱은 fallback로 강등.
- **한국어 프롬프트 하드코딩:** STT `contracts.py`(L0–L10 VariationSpec) 및 `regression_gate._extract_semantic_criteria`의 한국어 프롬프트가 코드에 박힘(§23 Q9 한국어-first/i18n 후속) → 데이터/설정으로 외부화, C5 ko-text 정렬 시 프롬프트 자산 분리.

---

## reverra-lab — 개발 계획

### 1. 역할·목표 위치 (처리결정: 분할)

reverra-lab은 코드상 서로 결합도가 낮은 세 단위로 이미 물리 분리되어 있으며(`reverra-v7/`, `reader/`, `tools/`), 전략 §11·§23-Q7·Appendix F #16의 결정에 따라 **3-way 분할**로 처리한다. 각 산출 레포의 목표 위치:

- **reverra-scan (assurance)** — `reverra-v7/code/src/reverra_scan/`. Applications 계층의 op-assurance 평가 방법론. golden set → action-family P/R → FP1–FP7 진단 → 처방 → maturity grade를 산출하는 **증거 생산자(evidence producer)** 후보. 단, 현재는 `ScanReport`만 내보내며 C1/C2 정합은 미구현.
- **reader (consumer app)** — `reader/` Next.js 16.2.3 챗앱. Applications 계층의 **소비자-facing mirror**. `prompts/fragments/`의 4차원 교정(`locus`/`ladder`/`transfer`/`behavior`)이 reverra-scan assurance 차원의 대화형 표현. `package.json` name이 `mcr-init`로 불일치, `api/chat/route.ts`가 `apiKey`를 요청 body로 받는 BYO-key·무인증·`localStorage`(`storage.ts`) 구조.
- **tools (book·humanize·deslop)** — `tools/`. book_research/writing/verify/pipeline/chapter/finalize + humanize-helpers + harness_codex. 평가 플랫폼이 아닌 **저술·문체 유틸리티 군집**. 단 `deslop_eval.py`는 결정적 slop grader로 EvidenceOps PromptOptimizer(SkillOpt) verifier로 연결 가치가 있음(§6 의존성).

**자산경계 회색지대(§7)**: 본 레포는 "Reverra" 외부 브랜드, 책 *거울과 회로*(개인 저작 자산, `docs/book/**`), 회사 평가 IP(reverra-scan/assurance 방법론)가 한 git 트리에 혼재한다. 전략 §0.2-2·§23-Q1·Appendix F #2는 외부 브랜드 Reverra 확정을 **자산경계 합의 이후로 deferred**한다. 따라서 본 레포 owner는 분할 실행 전 자산경계 4종 문서 합의에 **참여**해야 하며, 분할 자체는 "내부 EvidenceOps 정체성 고정 / 외부 브랜드 미확정" 원칙과 충돌하지 않도록 패키지명·디렉터리명에 Reverra 브랜드 고착을 신규 추가하지 않는다.

### 2. 분할 계획

**reverra-scan — Option B(D5-only 축소 후 참고구현) 권장.** 현 코드는 README/spec이 D1–D6를 광고하나 `scanner.scan`은 D5만 계산한다(`dimension_scores={"D5": ...}`, `maturity_grade`도 D5 가중합 단일식). 또 `judges/integrations/profiles/reports/storage` 5개 패키지가 `__init__.py`만 있는 빈 stub이고, `JudgeAssuranceReport`는 항상 0값으로 생성되어 `compute_grade_confidence`가 사실상 항상 `LOW`를 반환한다. 작업:

1. **빈 stub 패키지 5개 제거** 또는 `NotImplementedError` 명시 placeholder로 정직화(census 리스크 "D1–D6 주장 vs D5 구현 괴리" 해소).
2. **D5-only로 범위 명시 축소** — README/CLAUDE.md/spec의 D1–D6 주장을 실제 구현(D5 assurance + FP 진단)에 맞춰 정정. 문서-코드 드리프트(`main.py`/`python -m reverra_scan` 엔트리 불일치)도 코드 기준으로 정렬.
3. **JudgeAssurance 실측 or 제거** — judge bias 측정을 실제 구현하거나, 미구현이면 `judge_assurance`/`grade_confidence`를 산출에서 제외해 "항상 LOW" 허위 신호를 없앤다.
4. **(필요시) D1–D6 확장**은 후속 옵션으로 보류(참고구현 포지션). 확장 시에도 빅뱅 금지·차원별 점진 추가.

**reader.** (a) `package.json` name `mcr-init` → 의미 있는 이름으로 정리(브랜드는 §7 합의 후). (b) **auth 추가** — 현 `api/chat/route.ts`는 `apiKey`만 검사하고 인증·rate-limit 부재. §15 Security Gate의 "BYO-key localStorage production 금지"에 따라 인증 게이트(세션/토큰) + key의 서버측 비저장 경계를 도입. Stage 모델상 production write가 아니므로 Stage 1 read-only 소비자 앱으로 유지.

**tools.** 평가 코어가 아니므로 **유틸리티화**(별도 레포/디렉터리로 분리, 플랫폼 계약 비참여). 단 `deslop_eval.py`는 `--self-test`·exit 0/1 게이트를 가진 결정적 grader이므로 **PromptOptimizer verifier로 연결**(EPIC-004, `docs/proposals/skillopt-verifier-wiring.md` §3·§4 — `deslop-writing` 스킬의 1순위 파일럿 verifier). 연결은 deslop_eval을 호출 가능한 인터페이스로 노출하는 선에서, tools 자체의 외부 의존(아래)은 분리 유지.

### 3. 계약 입출력

- **reverra-scan = evidence producer** — C1(evidence-contract)/C2(harness-run evaluation annex) **정합 시에 한해** 증거 생산자로 편입. `AssuranceReport`/`DiagnosisReport`를 C1 EvidenceRef/Claim 형태로 매핑(mirror-not-fork), 평가 산출은 C2 evaluation-run/regression-gate-report 어휘(status=passed|failed|inconclusive)로 표현하며 **promote/hold/rollback 어휘 금지**(T2/T3 불변식). 정합 전까지는 독립 `ScanReport` 산출만 유지.
- **deslop_eval = PromptOptimizer verifier** — candidate(문체 산출) → deslop_eval 결정적 점수 → 임계 미만 fail. PO 루프(C2 HarnessRunRequest → EvalVault → RG → ATS)의 주관 도메인 grader 슬롯. PO는 promote/live mutation 안 함.
- **tools = 외부 의존 명시** — humanize-helpers/`humanize_book.sh`·book_chapter.py·harness_codex.py는 un-vendored `tools/im-not-ai` 스킬 + `codex` CLI(shell-out)에 의존하며, 미설치 시 **inert**. 플랫폼 계약에 들이지 않고 외부 의존을 문서화·격리한다.

### 4. 시퀀싱

- **Phase 0 (이번 주)**: 3-way 분할 결정 확정에 참여 + 자산경계 4종(asset-boundary/brand-usage/oss-policy/repo-ownership) 초안·합의절차 참여(§17-4). S1 project-state.json 발행(12 레포 공통, repo role=Applications, scan/reader/tools 단위·maturity·entrypoints·risk_flags 노출). 이 단계에서 코드 변경 없음(분할·경계 결정 우선).
- **Q3**: 분할 반영(레포 물리 분리 또는 디렉터리 경계 확정) + **scan scope 결정(Option B: D5-only 축소)** 실행. reader auth, tools utility화, deslop_eval↔PromptOptimizer wiring(EPIC-004, Q3)을 동일 분기에 배치.

### 5. DoD

- **§11 DoD: 3-way 분리 결정 반영** — scan/reader/tools 경계가 코드·문서·S1에 명시되고, scan scope(Option B) 결정이 기록됨.
- reverra-scan: 빈 stub 5개 제거/정직화, D1–D6 광고→D5-only 정정, JudgeAssurance 실측 또는 제거(허위 LOW 신호 제거), 문서-코드 엔트리 드리프트 해소, 기존 테스트(test_core.py) 통과 유지.
- reader: `mcr-init` 명칭 정리, auth 게이트 추가, BYO-key 서버 비저장 경계 확인.
- tools: 외부 의존(im-not-ai/codex) 명시·격리, deslop_eval verifier 인터페이스 노출.
- **자산경계 4종 문서 참여** 완료(브랜드/IP/개인저작 경계 합의에 owner 서명).

### 6. 의존성

- **자산경계 합의(§7) 선행** — 분할·브랜드·디렉터리 명명, reader/scan 공개 가능 여부 결정의 전제(특히 외부 Reverra 브랜드·개인 책 자산 분리).
- **deslop_eval ↔ PromptOptimizer (EPIC-004)** — PO MVP는 EPIC-001/002/003 의존(Q3). deslop_eval verifier wiring은 PO 측 일정에 종속.
- **reverra brand/IP 합의** — reverra-scan IP(회사) ↔ "거울과 회로" 책(개인) ↔ Reverra 외부 브랜드의 소유·라이선스 귀속 명확화(oss-policy·brand-usage 문서).

### 7. 리스크·완화

- **D1–D6 주장 vs D5 구현 괴리**: README/spec/CLAUDE.md가 6차원·"20/20 통과·80% coverage"를 광고하나 코드는 D5만 계산. → Option B로 범위 정정·과대광고 제거.
- **외부 의존 inert**: humanize/book_*가 `im-not-ai`·`codex` CLI 없으면 동작 불가. → 외부 의존 명시·격리, 플랫폼 계약 미편입, 오프라인 fallback 또는 명시적 skip.
- **docs/book 경로 하드코딩**: book_* 도구가 `docs/book/**`를 하드코딩 → 분할 시 경로 깨짐. → tools 분리 시 경로를 config/인자화하거나 동일 트리 유지 결정.
- **reader BYO-key/무인증/localStorage**: §15 Security Gate 위반 소지. → auth 게이트 + key 서버 비저장.
- **개인 자산 ↔ 회사 자산 혼합**: 책(개인) + reverra-scan IP(회사) + Reverra 브랜드가 한 레포에. → 자산경계 4종 합의로 귀속 분리 후 분할 실행, 합의 전 브랜드 고착 신규 추가 금지.
