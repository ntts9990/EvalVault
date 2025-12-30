# Web UI 실제 분석 및 결과 확인 기능 구현 계획

## 개요

EvalVault Web UI에서 실제 RAG 평가를 실행하고 결과를 확인할 수 있도록 구현하는 계획입니다.

## 현재 상태 분석

### 문제점

| 구분 | 현재 상태 | 위치 |
|------|----------|------|
| 의존성 주입 | `create_adapter()`가 빈 `WebUIAdapter()` 반환 | `adapter.py:437-443` |
| 평가 실행 | "평가 실행 기능은 아직 구현 중입니다." 메시지 | `app.py:384-386` |
| 리포트 점수 | mock 메트릭 점수(0.8) 사용 | `app.py` Reports 페이지 |

### 정상 동작 중

- Home, History, Improve 페이지 UI
- 파일 업로드 검증 (CSV/JSON/Excel)
- 메트릭 선택 UI
- CLI를 통한 평가 (`evalvault run`)

## 구현 계획

### Step 1: `create_adapter()` 의존성 주입 구현

**파일:** `src/evalvault/adapters/inbound/web/adapter.py`

**현재 코드 (line 437-443):**
```python
def create_adapter() -> WebUIAdapter:
    """WebUIAdapter 인스턴스 생성 팩토리."""
    # TODO: 실제 설정에서 저장소와 서비스 로드
    return WebUIAdapter()
```

**변경 내용:**
- Settings 로드 (`get_settings()`)
- SQLiteStorageAdapter 생성
- LLM adapter 생성 (API 키 없으면 graceful 처리)
- RagasEvaluator 생성
- 모든 의존성을 WebUIAdapter에 주입

---

### Step 2: 파일 업로드 → Dataset 변환 메서드 추가

**파일:** `src/evalvault/adapters/inbound/web/adapter.py`

**새 메서드:**
```python
def create_dataset_from_upload(
    self,
    filename: str,
    content: bytes,
) -> Dataset:
    """업로드된 파일에서 Dataset 생성.

    Args:
        filename: 원본 파일명 (확장자로 형식 판단)
        content: 파일 내용 (bytes)

    Returns:
        Dataset 인스턴스
    """
```

**지원 형식:**
- JSON: 직접 파싱하여 Dataset 생성
- CSV: csv.DictReader로 파싱
- Excel: 임시 파일 저장 후 기존 loader 사용

---

### Step 3: Dataset으로 직접 평가하는 메서드 추가

**파일:** `src/evalvault/adapters/inbound/web/adapter.py`

**새 메서드:**
```python
def run_evaluation_with_dataset(
    self,
    dataset: Dataset,
    metrics: list[str],
    thresholds: dict[str, float] | None = None,
    on_progress: Callable[[EvalProgress], None] | None = None,
) -> EvaluationRun:
    """데이터셋 객체로 직접 평가 실행.

    Args:
        dataset: 평가할 데이터셋
        metrics: 평가 메트릭 목록
        thresholds: 메트릭별 임계값 (선택)
        on_progress: 진행 상황 콜백 (선택)

    Returns:
        EvaluationRun 결과
    """
```

**동작:**
1. evaluator가 없으면 RuntimeError 발생
2. asyncio.run()으로 evaluator.evaluate() 호출
3. 결과를 storage에 저장
4. EvaluationRun 반환

---

### Step 4: Evaluate 페이지 평가 실행 구현

**파일:** `src/evalvault/adapters/inbound/web/app.py`

**현재 코드 (line 384-386):**
```python
if st.button("🚀 평가 실행", type="primary", disabled=not can_run):
    st.info("평가 실행 기능은 아직 구현 중입니다.")
    # TODO: 실제 평가 실행 로직
```

**변경 내용:**
1. LLM adapter 설정 확인 (없으면 에러 메시지)
2. `adapter.create_dataset_from_upload()` 호출
3. 선택된 메트릭과 threshold 수집
4. `adapter.run_evaluation_with_dataset()` 호출
5. 결과 표시 (통과율, 테스트 케이스 수, 소요 시간)
6. 세션 상태 업데이트

---

### Step 5: Reports 페이지 실제 메트릭 점수 사용

**파일:** `src/evalvault/adapters/inbound/web/app.py`

**현재 코드:**
```python
# 메트릭 점수 (Mock - 실제로는 adapter에서 조회)
metrics = dict.fromkeys(selected_run.metrics_evaluated, 0.8)
```

**변경 내용:**
```python
run_details = adapter.get_run_details(selected_run.run_id)
metrics = {
    m: run_details.get_avg_score(m) or 0.0
    for m in run_details.metrics_evaluated
}
```

---

## 수정 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `src/evalvault/adapters/inbound/web/adapter.py` | `create_adapter()` 구현, `create_dataset_from_upload()` 추가, `run_evaluation_with_dataset()` 추가 |
| `src/evalvault/adapters/inbound/web/app.py` | Evaluate 페이지 평가 실행 로직, Reports 페이지 실제 점수 조회 |

## 참조 파일

| 파일 | 참조 내용 |
|------|----------|
| `src/evalvault/adapters/inbound/cli.py` | CLI 의존성 주입 패턴 |
| `src/evalvault/domain/services/evaluator.py` | RagasEvaluator.evaluate() API |
| `src/evalvault/domain/entities/dataset.py` | Dataset, TestCase 엔티티 |
| `src/evalvault/domain/entities/result.py` | EvaluationRun 엔티티 |

## 테스트 시나리오

1. **Streamlit 앱 시작**
   ```bash
   uv run streamlit run src/evalvault/adapters/inbound/web/app.py
   ```

2. **Evaluate 페이지 테스트**
   - 샘플 CSV/JSON 파일 업로드
   - 메트릭 선택 (faithfulness, answer_relevancy)
   - 평가 실행 버튼 클릭
   - 결과 확인 (통과율, 테스트 케이스 수)

3. **History 페이지 테스트**
   - 저장된 평가 결과 조회
   - 검색 및 필터 기능 확인

4. **Reports 페이지 테스트**
   - 실제 점수로 리포트 생성
   - Markdown/HTML 다운로드

## 예상 결과

구현 완료 후:
- Web UI에서 파일 업로드 → 메트릭 선택 → 평가 실행 → 결과 확인 전체 플로우 동작
- History 페이지에서 이전 평가 결과 조회 가능
- Reports 페이지에서 실제 점수 기반 리포트 생성 가능
