# EvalVault 개선 계획서

> Last Updated: 2026-01-01
> Version: 2.0
> Focus: 코드 품질 개선, 사용성 향상, 성능 최적화

---

## 목차

1. [개요](#개요)
2. [현재 상태 분석](#현재-상태-분석)
3. [개선 계획](#개선-계획)
   - [P1: 코드 통합 및 중복 제거](#p1-코드-통합-및-중복-제거)
   - [P2: 복잡한 모듈 분리](#p2-복잡한-모듈-분리)
   - [P3: 성능 최적화](#p3-성능-최적화)
   - [P4: 사용성 개선](#p4-사용성-개선)
   - [P5: 테스트 개선](#p5-테스트-개선)
   - [P6: 문서화 개선](#p6-문서화-개선)
4. [실행 로드맵](#실행-로드맵)
5. [Quick Wins](#quick-wins)

---

## 개요

EvalVault는 현재 Phase 1-14가 완료되어 안정적인 기반을 갖추었습니다. 이제 코드 품질 개선과 사용성 향상에 집중하여 더 나은 사용자 경험을 제공하고자 합니다.

### 핵심 원칙

1. **KISS (Keep It Simple, Stupid)**: 복잡성 최소화
2. **DRY (Don't Repeat Yourself)**: 코드 중복 제거
3. **YAGNI (You Aren't Gonna Need It)**: 필요한 것만 구현
4. **빠른 피드백**: 작은 단위로 빠르게 개선 및 검증

### 목표

- **개발자 경험 (DX) 향상**: 명확한 코드, 쉬운 온보딩
- **사용자 경험 (UX) 향상**: 직관적인 CLI, 명확한 에러 메시지
- **유지보수성 향상**: 모듈화, 테스트 커버리지 증가
- **성능 향상**: 불필요한 계산 제거, 캐싱 활용

---

## 현재 상태 분석

### 강점

| 영역 | 설명 |
|------|------|
| **아키텍처** | Hexagonal Architecture로 잘 구조화됨 |
| **테스트** | 1352개 테스트, 89% 커버리지 |
| **기능 완성도** | Phase 1-14 완료, 핵심 기능 모두 구현 |
| **확장성** | Port/Adapter 패턴으로 쉬운 확장 |
| **문서화** | 상세한 ROADMAP, USER_GUIDE 제공 |

### 개선 필요 영역

| 영역 | 문제점 | 우선순위 |
|------|--------|----------|
| **코드 중복** | 유사한 로직이 여러 곳에 산재 | 🔥 High |
| **복잡한 모듈** | 일부 모듈이 너무 크고 복잡함 | 🟡 Medium |
| **성능** | 대규모 데이터셋 처리 시 느림 | 🟡 Medium |
| **CLI UX** | 일부 명령어가 직관적이지 않음 | 🔥 High |
| **에러 메시지** | 에러 메시지가 불명확한 경우 있음 | 🔥 High |
| **설정 복잡도** | 설정 파일이 여러 곳에 분산됨 | 🟢 Low |

### 코드베이스 통계

```
총 코드 라인: 59,073 LOC
테스트 수: 1,352개
커버리지: 89%
모듈 수: ~200개
CLI 명령어: 15개
```

---

## 개선 계획

### P1: 코드 통합 및 중복 제거

> **Priority**: 🔥 High
> **Duration**: 2-3주
> **목표**: 코드 중복 30% 감소

#### 1.1 LLM Adapter 통합

**현재 문제**:
- `OpenAIAdapter`, `AzureOpenAIAdapter`, `AnthropicAdapter`가 유사한 로직 반복
- 토큰 추적, 에러 핸들링 로직이 중복됨

**개선 방안**:
```python
# 공통 베이스 클래스 생성
class BaseLLMAdapter(ABC):
    """LLM Adapter 공통 로직"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._token_tracker = TokenTracker()
        self._error_handler = LLMErrorHandler()

    @abstractmethod
    def _create_client(self) -> Any:
        """각 어댑터별 클라이언트 생성"""
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        """공통 생성 로직 (토큰 추적, 에러 핸들링 포함)"""
        try:
            client = self._create_client()
            with self._token_tracker.track():
                response = self._call_api(client, prompt, **kwargs)
            return response
        except Exception as e:
            return self._error_handler.handle(e)
```

**작업 항목**:
1. `BaseLLMAdapter` 생성 (1일)
2. 기존 어댑터 리팩토링 (2일)
3. 테스트 업데이트 (1일)

**예상 효과**:
- 코드 중복 제거: ~300 LOC 감소
- 유지보수성 향상: 버그 수정 1곳에서 처리
- 새 LLM 추가 시간: 2시간 → 30분

#### 1.2 Storage Adapter 통합

**현재 문제**:
- `SQLiteAdapter`와 `PostgreSQLAdapter`가 거의 동일한 SQL 쿼리 사용
- 스키마 관리 로직이 중복됨

**개선 방안**:
```python
# 공통 SQL 쿼리 추출
class SQLQueries:
    """공통 SQL 쿼리 집합"""

    @staticmethod
    def save_run() -> str:
        return """
        INSERT INTO evaluation_runs (run_id, dataset_name, ...)
        VALUES (?, ?, ...)
        """

    @staticmethod
    def get_run() -> str:
        return "SELECT * FROM evaluation_runs WHERE run_id = ?"

# 공통 베이스 어댑터
class BaseSQLAdapter(ABC):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queries = SQLQueries()

    @abstractmethod
    def _execute(self, query: str, params: tuple) -> Any:
        """DB별 실행 로직"""
        pass

    def save_run(self, run: EvaluationRun) -> None:
        query = self.queries.save_run()
        self._execute(query, self._to_params(run))
```

**작업 항목**:
1. `SQLQueries` 클래스 생성 (1일)
2. `BaseSQLAdapter` 생성 (1일)
3. 기존 어댑터 리팩토링 (2일)

**예상 효과**:
- 코드 중복 제거: ~400 LOC 감소
- 스키마 변경 시 수정 범위 축소
- 새 DB 지원 추가 시간: 4시간 → 1시간

#### 1.3 Analysis Adapter 통합

**현재 문제**:
- NLP, Causal, Statistical 어댑터들이 유사한 데이터 처리 로직 반복
- 결과 집계 로직이 중복됨

**개선 방안**:
```python
# 공통 데이터 처리 유틸리티
class AnalysisDataProcessor:
    """분석 어댑터 공통 데이터 처리"""

    @staticmethod
    def extract_metrics(run: EvaluationRun) -> pd.DataFrame:
        """메트릭 데이터프레임 추출"""
        pass

    @staticmethod
    def aggregate_results(results: list) -> dict:
        """결과 집계"""
        pass

# 공통 베이스 어댑터
class BaseAnalysisAdapter(ABC):
    def __init__(self):
        self.processor = AnalysisDataProcessor()

    @abstractmethod
    def analyze(self, run: EvaluationRun) -> AnalysisResult:
        """분석 로직 (각 어댑터별 구현)"""
        pass
```

**작업 항목**:
1. `AnalysisDataProcessor` 생성 (1일)
2. `BaseAnalysisAdapter` 생성 (1일)
3. 기존 어댑터 리팩토링 (3일)

**예상 효과**:
- 코드 중복 제거: ~200 LOC 감소
- 데이터 처리 로직 일관성 향상

---

### P2: 복잡한 모듈 분리

> **Priority**: 🟡 Medium
> **Duration**: 2-3주
> **목표**: 모듈 복잡도 50% 감소

#### 2.1 CLI 모듈 분리

**현재 문제**:
- `src/evalvault/adapters/inbound/cli.py`가 1,500+ LOC로 너무 큼
- 모든 명령어가 한 파일에 있어 유지보수 어려움

**개선 방안**:
```
src/evalvault/adapters/inbound/cli/
├── __init__.py
├── app.py              # Typer 앱 정의
├── commands/
│   ├── run.py          # evalvault run
│   ├── analyze.py      # evalvault analyze
│   ├── history.py      # evalvault history, compare, export
│   ├── generate.py     # evalvault generate
│   ├── domain.py       # evalvault domain
│   ├── gate.py         # evalvault gate
│   ├── web.py          # evalvault web
│   └── pipeline.py     # evalvault pipeline
├── utils/
│   ├── formatters.py   # 출력 포맷팅 유틸리티
│   ├── validators.py   # 입력 검증 유틸리티
│   └── errors.py       # CLI 에러 핸들링
```

**작업 항목**:
1. 디렉토리 구조 생성 (0.5일)
2. 명령어별 파일 분리 (2일)
3. 공통 유틸리티 추출 (1일)
4. 테스트 리팩토링 (1일)

**예상 효과**:
- 파일당 평균 LOC: 1,500 → 150
- 명령어 추가/수정 시간: 50% 감소
- 코드 가독성 향상

#### 2.2 Web UI 컴포넌트 재구조화

**현재 문제**:
- `src/evalvault/adapters/inbound/web/adapter.py`가 700+ LOC
- UI 로직과 비즈니스 로직이 혼재됨

**개선 방안**:
```
src/evalvault/adapters/inbound/web/
├── adapter.py          # 100 LOC (진입점만)
├── services/
│   ├── evaluation_service.py   # 평가 실행 비즈니스 로직
│   ├── report_service.py       # 보고서 생성 비즈니스 로직
│   └── history_service.py      # 히스토리 관리 비즈니스 로직
├── components/         # UI 컴포넌트 (변경 없음)
├── pages/              # 페이지 라우팅 (변경 없음)
└── utils/
    ├── session.py      # 세션 관리
    └── formatters.py   # 데이터 포맷팅
```

**작업 항목**:
1. 서비스 레이어 생성 (2일)
2. 비즈니스 로직 이동 (2일)
3. 어댑터 슬림화 (1일)
4. 테스트 업데이트 (1일)

**예상 효과**:
- `adapter.py` LOC: 700 → 100
- 비즈니스 로직 재사용성 증가
- 테스트 작성 용이성 향상

#### 2.3 Domain Services 분리

**현재 문제**:
- 일부 서비스가 너무 많은 책임을 가짐
- 예: `ExperimentManager`가 비교, 통계, 보고서 생성 모두 담당

**개선 방안**:
```python
# 현재 (1 서비스 = 모든 기능)
class ExperimentManager:
    def create_experiment(self): ...
    def compare_groups(self): ...
    def calculate_statistics(self): ...
    def generate_report(self): ...

# 개선 (1 서비스 = 1 책임)
class ExperimentRepository:
    """실험 CRUD"""
    def create(self, experiment): ...
    def get(self, experiment_id): ...

class ExperimentComparator:
    """실험 비교"""
    def compare_groups(self, groups): ...

class ExperimentStatisticsCalculator:
    """통계 계산"""
    def calculate(self, results): ...

class ExperimentReportGenerator:
    """보고서 생성"""
    def generate(self, comparison): ...
```

**작업 항목**:
1. 책임 분석 및 설계 (1일)
2. 새 서비스 클래스 생성 (2일)
3. 기존 코드 리팩토링 (2일)
4. 테스트 업데이트 (1일)

**예상 효과**:
- 단일 책임 원칙 (SRP) 준수
- 테스트 작성 용이
- 코드 재사용성 증가

---

### P3: 성능 최적화

> **Priority**: 🟡 Medium
> **Duration**: 2주
> **목표**: 평가 속도 30% 향상

#### 3.1 평가 파이프라인 최적화

**현재 문제**:
- 대규모 데이터셋(1000+ 테스트 케이스) 평가 시 느림
- 불필요한 중간 변환 과정

**개선 방안**:
```python
# 현재: 순차적 처리
for test_case in dataset:
    result = evaluate(test_case)
    results.append(result)

# 개선: 배치 처리 + 병렬화
async def evaluate_batch(test_cases: list, batch_size: int = 10):
    batches = chunk(test_cases, batch_size)
    tasks = [evaluate_batch_async(batch) for batch in batches]
    results = await asyncio.gather(*tasks)
    return flatten(results)
```

**작업 항목**:
1. 배치 처리 로직 구현 (2일)
2. 비동기 평가 파이프라인 구현 (2일)
3. 캐싱 메커니즘 추가 (1일)
4. 성능 벤치마크 (1일)

**예상 효과**:
- 1000 테스트 케이스 평가 시간: 30분 → 10분
- CPU 사용률 향상: 30% → 70%

#### 3.2 데이터 로딩 최적화

**현재 문제**:
- 대용량 JSON/CSV 파일 로딩 시 메모리 과다 사용
- 전체 데이터를 메모리에 로드

**개선 방안**:
```python
# 현재: 전체 로드
def load_dataset(file_path: str) -> Dataset:
    data = json.load(open(file_path))  # 전체 메모리 로드
    return Dataset.from_dict(data)

# 개선: 스트리밍 로드
def load_dataset_streaming(file_path: str) -> Iterator[TestCase]:
    with open(file_path) as f:
        for line in f:
            test_case = TestCase.from_json(line)
            yield test_case
```

**작업 항목**:
1. 스트리밍 로더 구현 (2일)
2. 기존 로더와 호환성 유지 (1일)
3. 대용량 파일 테스트 (1일)

**예상 효과**:
- 10MB 파일 로딩 메모리: 100MB → 10MB
- 로딩 시간: 5초 → 2초

#### 3.3 캐싱 개선

**현재 문제**:
- `MemoryCacheAdapter`가 TTL만 지원, LRU 캐시 효율 낮음
- 평가 결과 캐싱이 제한적

**개선 방안**:
```python
# LRU + TTL 하이브리드 캐시
class HybridCache:
    def __init__(self, max_size: int, default_ttl: int):
        self._lru = LRUCache(max_size)
        self._ttl_map = {}

    def get(self, key: str) -> Any:
        if key in self._ttl_map and self._is_expired(key):
            self._lru.pop(key)
            del self._ttl_map[key]
            return None
        return self._lru.get(key)
```

**작업 항목**:
1. 하이브리드 캐시 구현 (1일)
2. 기존 캐시 어댑터 교체 (1일)
3. 캐시 hit rate 측정 (1일)

**예상 효과**:
- 캐시 hit rate: 60% → 85%
- 반복 평가 시간: 50% 감소

---

### P4: 사용성 개선

> **Priority**: 🔥 High
> **Duration**: 2주
> **목표**: CLI UX 개선, 에러 메시지 명확화

#### 4.1 CLI 명령어 개선

**현재 문제**:
- 일부 명령어 옵션이 직관적이지 않음
- 도움말 메시지가 불충분함

**개선 방안**:

**현재**:
```bash
evalvault run data.csv --metrics faithfulness,answer_relevancy
```

**개선**:
```bash
# 더 직관적인 옵션 이름
evalvault run data.csv \
  --metrics faithfulness answer_relevancy \
  --llm openai \
  --tracker langfuse

# 짧은 별칭 제공
evalvault run data.csv -m faithfulness -l openai -t langfuse

# 프리셋 지원
evalvault run data.csv --preset production
# production: faithfulness, answer_relevancy, context_precision, context_recall
```

**작업 항목**:
1. 명령어 옵션 재설계 (1일)
2. 별칭 추가 (0.5일)
3. 프리셋 시스템 구현 (1일)
4. 도움말 메시지 개선 (1일)
5. 사용자 테스트 (0.5일)

**예상 효과**:
- 신규 사용자 온보딩 시간: 30분 → 10분
- 명령어 입력 오류율: 50% 감소

#### 4.2 에러 메시지 개선

**현재 문제**:
- 에러 메시지가 불명확하거나 기술적임
- 해결 방법이 제시되지 않음

**개선 방안**:

**현재**:
```
Error: The api_key client option must be set
```

**개선**:
```
❌ Error: OpenAI API key not found

📝 How to fix:
   1. Create a .env file in your project root
   2. Add: OPENAI_API_KEY=your-key-here
   3. Or set environment variable: export OPENAI_API_KEY=your-key

💡 Get your API key: https://platform.openai.com/api-keys

For more help, visit: https://github.com/ntts9990/EvalVault#configuration
```

**작업 항목**:
1. 에러 메시지 템플릿 시스템 구현 (2일)
2. 모든 에러 케이스 재작성 (3일)
3. 해결 방법 문서 작성 (1일)

**예상 효과**:
- 사용자 지원 요청: 40% 감소
- 자가 해결률: 60% → 85%

#### 4.3 Progress Indicator 개선

**현재 문제**:
- 평가 진행률이 보이지 않아 답답함
- 대규모 평가 시 멈춘 것처럼 보임

**개선 방안**:
```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

def evaluate_with_progress(dataset: Dataset):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("[cyan]Evaluating...", total=len(dataset))

        for test_case in dataset:
            result = evaluate(test_case)
            progress.update(task, advance=1)
            results.append(result)
```

**작업 항목**:
1. Rich 라이브러리 통합 (0.5일)
2. Progress bar 구현 (1일)
3. ETA 표시 추가 (0.5일)

**예상 효과**:
- 사용자 만족도 향상
- 평가 중단율 감소

---

### P5: 테스트 개선

> **Priority**: 🟡 Medium
> **Duration**: 1-2주
> **목표**: 테스트 실행 시간 50% 단축

#### 5.1 느린 테스트 최적화

**현재 문제**:
- 전체 테스트 실행 시간: 14분 24초
- 일부 통합 테스트가 너무 느림

**개선 방안**:
```python
# 현재: 실제 LLM API 호출
@pytest.mark.integration
def test_real_evaluation():
    result = evaluate_with_llm(test_case)  # 5초 소요
    assert result.score > 0.7

# 개선: Mock LLM 사용
@pytest.mark.unit
def test_evaluation_logic():
    llm = MockLLM()  # 0.1초 소요
    result = evaluate_with_llm(test_case, llm=llm)
    assert result.score > 0.7

# 실제 LLM 테스트는 별도 마크
@pytest.mark.slow
@pytest.mark.requires_llm
def test_real_llm_integration():
    ...
```

**작업 항목**:
1. 느린 테스트 식별 (1일)
2. Mock 객체 개선 (2일)
3. 테스트 마커 정리 (1일)

**예상 효과**:
- 테스트 실행 시간: 14분 → 7분
- CI/CD 파이프라인 속도 향상

#### 5.2 테스트 커버리지 향상

**현재 커버리지**: 89%
**목표 커버리지**: 95%+

**미커버 영역**:
- 에러 핸들링 경로
- 엣지 케이스
- CLI 대화형 입력

**작업 항목**:
1. 커버리지 리포트 분석 (0.5일)
2. 미커버 영역 테스트 작성 (3일)
3. 엣지 케이스 추가 (1일)

**예상 효과**:
- 프로덕션 버그 발생률: 20% 감소
- 코드 신뢰도 향상

---

### P6: 문서화 개선

> **Priority**: 🟢 Low
> **Duration**: 1주
> **목표**: 사용자 가이드 강화, API 문서 자동화

#### 6.1 API 문서 자동화

**현재 문제**:
- API 문서가 수동으로 작성되어 업데이트 누락
- 코드와 문서 불일치

**개선 방안**:
```python
# Sphinx + autodoc으로 자동 생성
from sphinx.ext.autodoc import ...

# pyproject.toml
[tool.sphinx]
source_dir = "docs"
build_dir = "docs/_build"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Google/NumPy docstring 지원
    "sphinx_rtd_theme",
]
```

**작업 항목**:
1. Sphinx 설정 (1일)
2. Docstring 스타일 통일 (2일)
3. ReadTheDocs 배포 (0.5일)

**예상 효과**:
- API 문서 업데이트 자동화
- 개발자 참조 편의성 향상

#### 6.2 튜토리얼 강화

**현재 문제**:
- 초보자를 위한 단계별 튜토리얼 부족
- 실습 예제가 제한적

**개선 방안**:
```markdown
# docs/tutorials/
├── 01-quickstart.md          # 5분 빠른 시작
├── 02-basic-evaluation.md    # 기본 평가 실행
├── 03-custom-metrics.md      # 커스텀 메트릭 추가
├── 04-web-ui-guide.md        # Web UI 사용법
├── 05-korean-rag.md          # 한국어 RAG 최적화
└── 06-production-tips.md     # 프로덕션 배포 가이드
```

**작업 항목**:
1. 튜토리얼 구조 설계 (0.5일)
2. 튜토리얼 작성 (3일)
3. 스크린샷/GIF 추가 (0.5일)

**예상 효과**:
- 신규 사용자 온보딩 성공률: 70% → 90%
- 지원 요청 감소

---

## 실행 로드맵

### 2026 Q1 (1-3월)

#### Week 1-2: P1 코드 통합
- [ ] LLM Adapter 통합
- [ ] Storage Adapter 통합
- [ ] 테스트 업데이트

#### Week 3-4: P2 모듈 분리 (Part 1)
- [ ] CLI 모듈 분리
- [ ] 명령어별 파일 분리
- [ ] 공통 유틸리티 추출

#### Week 5-6: P4 사용성 개선
- [ ] CLI 명령어 개선
- [ ] 에러 메시지 개선
- [ ] Progress Indicator 추가

### 2026 Q2 (4-6월)

#### Week 7-8: P2 모듈 분리 (Part 2)
- [ ] Web UI 컴포넌트 재구조화
- [ ] Domain Services 분리

#### Week 9-10: P3 성능 최적화
- [ ] 평가 파이프라인 최적화
- [ ] 데이터 로딩 최적화
- [ ] 캐싱 개선

#### Week 11-12: P5 & P6 테스트/문서화
- [ ] 느린 테스트 최적화
- [ ] 테스트 커버리지 향상
- [ ] API 문서 자동화
- [ ] 튜토리얼 강화

---

## Quick Wins

다음은 즉시 실행 가능한 빠른 개선 사항들입니다:

### QW1: 에러 메시지 개선 (1일)

```python
# src/evalvault/utils/errors.py
class UserFriendlyError:
    """사용자 친화적 에러 메시지"""

    @staticmethod
    def missing_api_key(provider: str) -> str:
        return f"""
❌ Error: {provider} API key not found

📝 How to fix:
   1. Create .env file
   2. Add: {provider.upper()}_API_KEY=your-key

💡 Get key: {PROVIDER_URLS[provider]}
"""

# 사용
raise ValueError(UserFriendlyError.missing_api_key("openai"))
```

### QW2: Progress Bar 추가 (0.5일)

```bash
pip install rich

# CLI에 즉시 적용
from rich.progress import track

for test_case in track(dataset, description="Evaluating..."):
    result = evaluate(test_case)
```

### QW3: 명령어 별칭 추가 (0.5일)

```python
# CLI 옵션에 짧은 별칭 추가
@app.command()
def run(
    dataset: str,
    metrics: str = typer.Option(..., "-m", "--metrics"),  # -m 추가
    llm: str = typer.Option("openai", "-l", "--llm"),      # -l 추가
    tracker: str = typer.Option(None, "-t", "--tracker"),  # -t 추가
):
    ...
```

### QW4: 설정 검증 (1일)

```python
# 시작 시 설정 자동 검증
class ConfigValidator:
    def validate(self) -> list[str]:
        """설정 검증 및 문제점 반환"""
        issues = []

        if not os.getenv("OPENAI_API_KEY"):
            issues.append("OPENAI_API_KEY not set")

        if not os.path.exists(".env"):
            issues.append(".env file not found")

        return issues

# CLI 시작 시 자동 실행
validator = ConfigValidator()
if issues := validator.validate():
    print("⚠️ Configuration issues:")
    for issue in issues:
        print(f"   - {issue}")
```

---

## 성공 지표

| 지표 | Baseline | 목표 |
|------|----------|------|
| 코드 중복률 | 15% | 10% |
| 평균 모듈 크기 | 300 LOC | 150 LOC |
| 평가 속도 (1000 TC) | 30분 | 20분 |
| 테스트 실행 시간 | 14분 | 7분 |
| 신규 사용자 온보딩 시간 | 30분 | 15분 |
| 사용자 지원 요청 | 10건/주 | 5건/주 |
| 테스트 커버리지 | 89% | 95% |

---

## 마무리

이 개선 계획은 실용적이고 점진적인 접근 방식을 따릅니다. 각 개선 사항은 독립적으로 실행 가능하며, 빠른 피드백을 통해 검증할 수 있습니다.

### 핵심 원칙

1. **작은 단위로 빠르게**: PR당 1-2일 작업량 유지
2. **테스트 우선**: 모든 리팩토링에 테스트 커버리지 유지
3. **사용자 중심**: 개발자가 아닌 사용자 관점에서 개선
4. **측정 가능**: 모든 개선 사항은 측정 가능한 지표로 검증

### 다음 단계

1. Quick Wins (QW1-QW4) 즉시 실행
2. P1 코드 통합부터 시작
3. 주간 리뷰 회의로 진행 상황 점검
4. 분기별 회고를 통한 계획 조정
