# 프롬프트 후보 평가·추천(옵션 C) 설계 문서

## 1) 목표
- 내부 중심으로 프롬프트 후보를 **자동/수동으로 수집**하고, **Ragas 기반 평가**와 **사용자 가중치 스코어링**으로 **Top-N 추천**을 제공한다.
- 기존 EvalVault의 프롬프트 스냅샷/분석 흐름과 일관된 CLI/아티팩트 경로를 유지한다.

## 2) 범위
- 포함: 후보 생성(자동/수동), 데이터 분리(dev/holdout), 평가/스코어링, CLI 출력, 보고서/아티팩트 저장
- 제외: UI, 실시간 서비스화, 외부 도구 연동의 강제 의존성

## 3) CLI 설계 (기존 패턴 유지)
### 3.1 명령어
- `evalvault prompts suggest <run_id>`

### 3.2 옵션 제안
- `--role system|<metric_name>`: 기본 `system` (또는 첫 role)
- `--metrics faithfulness,answer_relevancy`: 기본 `run.metrics_evaluated`
- `--weights faithfulness=0.5,answer_relevancy=0.5`: 사용자 가중치 (없으면 균등)
- `--candidates 5`: 자동 후보 수 기본값 5
- `--prompt "<manual candidate>"`: 수동 후보 문자열 (복수 가능)
- `--prompt-file <path>`: 수동 후보 파일 (복수 가능)
- `--auto/--no-auto`: 자동 후보 생성 on/off (기본 on)
- `--holdout-ratio 0.2`: 데이터 분리 비율 (B안)
- `--seed 42`: 샘플링 재현성
- `--output <path> --report <path> --analysis-dir <path>`: 분석 출력 패턴 일관성

## 4) 저장 위치 (기존 규칙 준수)
- JSON: `reports/analysis/prompt_suggestions_<RUN_ID>.json`
- 리포트: `reports/analysis/prompt_suggestions_<RUN_ID>.md`
- 아티팩트: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/`

## 5) 데이터 분리 정책 (B안)
- 기존 평가 데이터셋을 **dev/holdout**으로 분리
- `holdout`에서만 최종 스코어/랭킹 산출
- 분리 방식:
  - 기본: 단순 랜덤 샘플링
  - 옵션: 라벨/난이도 기반 층화는 후속 확장
- 분리 비율 기본값 0.2 (holdout 20%)

## 6) 후보 수집/생성 플로우
### 6.1 수동 후보
- CLI `--prompt`, `--prompt-file`로 입력
- 여러 후보를 리스트로 누적

### 6.2 자동 후보
- LLM 기반 후보 생성 (기본 5개)
- 입력: 대상 role(system 또는 metric prompt), 실패 사례/가이드 요약, 메트릭 목표
- 출력: 후보 텍스트 리스트

## 7) 평가 및 스코어링
- 기본 평가: Ragas 메트릭(이미 사용 중)
- 사용자 가중치 합산 스코어:
  - `weighted_score = Σ (metric_score * weight)`
  - 가중치 미지정 시 균등 분배
- 출력:
  - 후보별 메트릭 스코어
  - 가중치 반영 총점
  - Top-N 추천 목록

## 8) 내부 아키텍처 설계
### 8.1 도메인/서비스 계층
- 신규 서비스: `PromptSuggestionService`
  - 후보 수집/생성 → 평가 → 랭킹
- 기존 연계:
  - `RagasEvaluator` (평가)
  - `PromptSetBundle`/`PromptInput` (프롬프트 구조)

### 8.2 저장/아티팩트
- DB 스키마 변경 없이 JSON/리포트 파일로 저장
- 필요 시 `analysis_reports` 테이블에 리포트 경로 등록 가능(옵션)

## 9) 출력 데이터 모델 (JSON)
```json
{
  "run_id": "...",
  "role": "system",
  "metrics": ["faithfulness", "answer_relevancy"],
  "weights": {"faithfulness": 0.5, "answer_relevancy": 0.5},
  "candidates": [
    {
      "candidate_id": "cand-001",
      "source": "auto|manual",
      "content": "...",
      "scores": {"faithfulness": 0.78, "answer_relevancy": 0.82},
      "weighted_score": 0.80
    }
  ],
  "ranking": ["cand-003", "cand-001", "cand-002"],
  "holdout_ratio": 0.2,
  "metadata": {"seed": 42}
}
```

## 10) 외부 연동(선택)
- `promptfoo`(MIT): CI 회귀/레드팀/보안 스캔
- `DeepEval`(Apache-2.0): Pytest 기반 평가
- 내부 파이프라인을 깨지 않도록 **옵션 플래그 기반 연동**

## 11) 리스크 및 제약
- 자동 후보는 비용/편향/안전성 리스크
- 데이터 분리 없이 최적화하면 과적합 위험 증가
- Prompt snapshot과 run linkage는 기존 `prompts show/diff`를 덮지 않도록 분리 저장 권장

## 12) 검증 계획
- CLI 실행 샘플 1회 (기본 후보 5개)
- 수동 후보 + 자동 후보 병합 확인
- 가중치 변화 시 랭킹이 기대대로 변하는지 확인
- JSON/리포트/아티팩트 경로 일관성 점검

## 13) 단계별 구현 계획 (요약)
1. CLI 엔트리 추가 (`prompts suggest`)
2. 후보 생성/수집 모듈 구현
3. dev/holdout 분리 및 평가 파이프라인 연결
4. 스코어링/랭킹/보고서 생성
5. 파일 출력 및 아티팩트 정리
6. (선택) 외부 연동 플래그 추가

## 14) 병렬 작업 계획 (4개 에이전트/워크트리 기준)
### 14.1 작업 분할
- 에이전트 A: CLI/입출력/리포트
  - `prompts suggest` 명령 추가
  - 옵션 파싱/검증, 출력/리포트 경로 처리
- 에이전트 B: 후보 생성/수집
  - 자동 후보 생성 로직
  - 수동 후보 병합/정규화
- 에이전트 C: 평가/스코어링
  - dev/holdout 분리 로직
  - Ragas 평가 실행 + 가중치 합산 스코어
- 에이전트 D: 저장/아티팩트
  - JSON/리포트/아티팩트 생성
  - (선택) 분석 결과 DB 저장 연동

### 14.2 브랜치/워크트리 규칙
- 브랜치 예시: `feat/prompt-suggest-cli`, `feat/prompt-suggest-candidates`, `feat/prompt-suggest-scoring`, `feat/prompt-suggest-output`
- 각 에이전트는 **자신의 워크트리/브랜치에서만** 변경
- 충돌 방지: 공통 파일(`prompts.py`, `analysis_io.py`)은 담당자 1인만 수정

### 14.3 인터페이스 고정점
- 입력/출력 JSON 스키마는 본 문서 9절 기준
- 후보 데이터 모델: `candidate_id`, `source`, `content`, `scores`, `weighted_score`
- 스코어 계산식: `Σ(metric_score * weight)`
- 기본 후보 수: 5, 기본 holdout 비율: 0.2

### 14.4 통합 순서
1. A/B/C/D 각 브랜치 구현 완료
2. C → A: 스코어링 결과 구조 합의
3. B → A: 후보 데이터 구조 합의
4. A가 최종 통합(merge) 및 CLI 플로우 검증

### 14.5 병렬 개발 체크리스트
- [ ] 공통 구조체/스키마 합의 완료
- [ ] 충돌 파일 담당자 확정
- [ ] 브랜치별 테스트/검증 결과 공유

## 15) 인터페이스 시그니처 (충돌 방지용 고정안)
### 15.1 공통 데이터 모델
파일: `src/evalvault/domain/entities/prompt_suggestion.py`
```python
@dataclass(frozen=True)
class PromptCandidate:
    candidate_id: str
    source: str  # "auto" | "manual"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class PromptCandidateScore:
    candidate_id: str
    scores: dict[str, float]
    weighted_score: float

@dataclass(frozen=True)
class PromptSuggestionResult:
    run_id: str
    role: str
    metrics: list[str]
    weights: dict[str, float]
    candidates: list[PromptCandidate]
    scores: list[PromptCandidateScore]
    ranking: list[str]
    holdout_ratio: float
    metadata: dict[str, Any]
```

### 15.2 에이전트 A (CLI) 서명
```python
def suggest_prompts_cli(
    run_id: str,
    role: str | None,
    metrics: list[str] | None,
    weights: dict[str, float] | None,
    candidates: int,
    manual_prompts: list[str],
    manual_prompt_files: list[Path],
    auto: bool,
    holdout_ratio: float,
    seed: int | None,
    output_path: Path | None,
    report_path: Path | None,
    analysis_dir: Path | None,
) -> None: ...
```

### 15.3 에이전트 B (후보 생성/수집)
파일: `src/evalvault/domain/services/prompt_candidate_service.py`
```python
class PromptCandidateService:
    def build_candidates(
        self,
        *,
        base_prompt: str,
        role: str,
        metrics: list[str],
        manual_prompts: list[str],
        manual_prompt_files: list[Path],
        auto: bool,
        auto_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> list[PromptCandidate]: ...
```

### 15.4 에이전트 C (분리/평가/스코어링)
파일: `src/evalvault/domain/services/holdout_splitter.py`
```python
def split_dataset_holdout(
    *,
    dataset: Dataset,
    holdout_ratio: float,
    seed: int | None,
) -> tuple[Dataset, Dataset]: ...
```

파일: `src/evalvault/domain/services/prompt_scoring_service.py`
```python
class PromptScoringService:
    def score_candidates(
        self,
        *,
        base_run: EvaluationRun,
        dev_dataset: Dataset,
        holdout_dataset: Dataset,
        candidates: list[PromptCandidate],
        metrics: list[str],
        weights: dict[str, float],
    ) -> list[PromptCandidateScore]: ...
```

### 15.5 에이전트 D (저장/리포트)
파일: `src/evalvault/domain/services/prompt_suggestion_reporter.py`
```python
class PromptSuggestionReporter:
    def render_json(self, result: PromptSuggestionResult) -> dict[str, Any]: ...
    def render_markdown(self, result: PromptSuggestionResult) -> str: ...
    def write_outputs(
        self,
        *,
        result: PromptSuggestionResult,
        output_path: Path,
        report_path: Path,
        artifacts_dir: Path,
    ) -> None: ...
```

### 15.6 통합 흐름(고정)
1. A가 `run_id`로 base prompt 로드
2. B가 후보 리스트 생성
3. C가 holdout 분리 + 후보 평가 + 스코어링
4. D가 JSON/MD/아티팩트 저장
5. A가 CLI 요약 출력
