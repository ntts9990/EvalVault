# 데이터 종합 분석 방법 & 평가 → 분석 전체 흐름

평가 결과는 항상 동일한 구조로 저장됩니다. EvalVault는 이 고정된 결과를 기반으로
**통계/NLP/원인/트렌드/프롬프트 변경**까지 한 번에 분석하고 LLM 보고서를 생성합니다.

---

## 1. 자동 분석 (옵션 방식)

### 평가 후 자동 실행

```bash
uv run evalvault run data.json \
  --metrics faithfulness,answer_relevancy \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 기본 저장 위치

- JSON 결과: `reports/analysis/analysis_<run_id>.json`
- Markdown 보고서: `reports/analysis/analysis_<run_id>.md`

### 저장 위치 커스터마이즈

```bash
uv run evalvault run data.json \
  --db data/db/evalvault.db \
  --auto-analyze \
  --analysis-dir reports/custom \
  --analysis-json reports/custom/run_001.json \
  --analysis-report reports/custom/run_001.md
```

---

## 2. 단일 실행 분석 (수동)

```bash
uv run evalvault analyze RUN_ID \
  --db data/db/evalvault.db \
  --nlp --causal
```

필요 시 `--output`, `--report`로 파일 저장 가능합니다.

---

## 3. A/B 직접 비교 분석 (확장)

```bash
uv run evalvault analyze-compare RUN_A RUN_B \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test
```

기본 저장 위치:

- JSON 결과: `reports/comparison/comparison_<run_a>_<run_b>.json`
- Markdown 보고서: `reports/comparison/comparison_<run_a>_<run_b>.md`

비교 보고서는 **프롬프트 변경 요약 + 통계 비교 + 개선 제안**을 자동으로 포함합니다.

---

## 4. 분석 결과에 포함되는 내용

- **통계 요약**: 평균/분산/상관관계/통과율
- **Ragas 요약**: 메트릭별 평균, 케이스별 점수
- **저성과 케이스**: 낮은 점수 샘플, 우선순위 케이스
- **진단/원인 분석**: 문제 원인 가설 + 개선 힌트
- **패턴/트렌드**: 키워드/질문 유형 패턴, 실행 이력 추세
- **A/B 변경 사항**: 시스템 프롬프트, Ragas 프롬프트, 모델/옵션 차이
- **LLM 종합 보고서**: 원인 분석 + 개선 방향 + 다음 실험 제안

---

## 5. 평가 → 분석 전체 흐름

1) **평가 실행**
   - `evalvault run data.json --db ...`
2) **자동 분석 (옵션)**
   - `--auto-analyze`로 즉시 보고서 생성
3) **추가 분석**
   - 필요 시 `evalvault analyze`로 상세 분석
4) **A/B 비교**
   - `evalvault analyze-compare`로 비교 보고서 생성
5) **프롬프트/메트릭 개선**
   - 보고서의 개선 제안을 반영해 다음 실행

---

## 6. 품질 확보 팁

- A/B 비교는 **데이터셋 동일** 조건에서 수행하세요.
- 프롬프트 변경은 `docs/guides/PROMPT_MANAGEMENT.md` 흐름대로 스냅샷 저장하세요.
- 비교 결과가 애매하면 샘플 수를 늘리고 재실행하세요.
