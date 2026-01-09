# 프롬프트 변경/관리 방법

EvalVault는 **시스템 프롬프트**와 **Ragas 메트릭 프롬프트**를 실행 단위로 스냅샷 저장하고,
실행 간 변경점을 비교할 수 있도록 설계되어 있습니다. 이 문서는 변경/관리 흐름을 간단히 정리합니다.

---

## 1. 저장되는 프롬프트 범위

- **시스템 프롬프트**: 대상 LLM에 실제로 주입한 시스템 메시지
- **Ragas 메트릭 프롬프트**: faithfulness 등 평가 메트릭용 프롬프트 오버라이드
- **Prompt Set 스냅샷**: 위 프롬프트들을 `run_id`와 함께 DB에 저장 (비교/회귀 추적용)

> **중요**: Prompt Set 저장은 `--db` 옵션이 있어야 동작합니다.

---

## 2. 시스템 프롬프트 등록

### 텍스트 직접 입력

```bash
uv run evalvault run data.json \
  --system-prompt "당신은 보험 약관 전문가입니다..." \
  --prompt-set-name "sys-v2" \
  --db data/db/evalvault.db
```

### 파일로 입력

```bash
uv run evalvault run data.json \
  --system-prompt-file agent/prompts/system.txt \
  --system-prompt-name sys-v2 \
  --prompt-set-name "sys-v2" \
  --db data/db/evalvault.db
```

---

## 3. Ragas 프롬프트 YAML 오버라이드

### YAML 예시

```yaml
faithfulness: |
  너는 답변의 근거가 컨텍스트에 있는지 평가한다...

answer_relevancy: |
  질문 의도와 답변의 연관성을 평가한다...
```

### 실행 예시

```bash
uv run evalvault run data.json \
  --ragas-prompts config/ragas_prompts.yaml \
  --prompt-set-name "ragas-v3" \
  --db data/db/evalvault.db
```

> YAML에 있는 메트릭이 `--metrics`에 없으면 경고가 출력됩니다.

---

## 4. 저장된 프롬프트 확인/비교

### 스냅샷 보기

```bash
uv run evalvault prompts show RUN_ID --db data/db/evalvault.db
```

### 두 실행 간 비교

```bash
uv run evalvault prompts diff RUN_A RUN_B --db data/db/evalvault.db
```

### 비교 분석 보고서에서 자동 반영

```bash
uv run evalvault analyze-compare RUN_A RUN_B --db data/db/evalvault.db
```

`analyze-compare` 결과에는 **프롬프트 변경 요약 + 메트릭 변화**가 함께 포함됩니다.

---

## 5. 운영 팁

- **Prompt Set 이름 규칙화**: `sys-v3`, `ragas-v2`, `release-2025-02` 등으로 관리
- **A/B 비교 시 데이터셋 고정**: 데이터셋이 바뀌면 비교 해석이 왜곡됩니다
- **Prompt Manifest 활용**: Phoenix Prompt Playground와 연결하려면
  `docs/guides/OBSERVABILITY_PLAYBOOK.md`의 Prompt Manifest 절을 참고하세요.
