# RAG 평가 분석 보고서

## 요약
* **비교 대상** – `ollama/gpt-oss-safeguard:20b` (Run A) vs `gpt-oss-safeguard:20b` (Run B)
* **데이터셋** – `test_dataset v1.0.0` (변경 없음)
* **총 테스트 케이스** – 4
* **Pass‑Rate** – Run A: 50 % (2/4), Run B: 0 % (0/4) – **차이: –50 %**
* **평균 점수** – Run A: 0.692, Run B: 0.000 – 차이: –0.692
* **주요 차이** – `answer_relevancy`는 대규모 감소(100 % 저하, p = 5.8 × 10⁻⁹), `faithfulness`는 비선형적(불충분한 증거 → “추가 데이터 필요”).

---

## 변경 사항 요약
| 항목 | 설명 | 영향 |
|------|------|------|
| **모델 명** | `ollama/gpt-oss-safeguard:20b` → `gpt-oss-safeguard:20b` | 모델 사양이 달라질 가능성(오픈소스 vs. 로컬 람다) |
| **데이터셋** | 동일 (`test_dataset v1.0.0`) | 없음 |
| **프롬프트 스냅샷** | 없어서 추적 불가 | **추가 데이터 필요** |
| **기타 구성** | 없음 | — |

*프롬프트 스냅샷이 없다는 것은 Run B에서 실제 프롬프트가 달라졌을 가능성을 시사한다. “Prompt snapshot을 찾을 수 없습니다.”라는 메시지가 기록돼 있다.*

---

## 지표 비교

| Metric | Run A | Run B | Diff | Significance | Effect Size |
|--------|-------|-------|------|--------------|-------------|
| Faithfulness | 0.50 | 0.00 | –0.50 | ❌ (p = 0.134) | Large (−1.41) |
| Answer Relevancy | 0.88 | 0.00 | –0.88 | ✅ (p = 5.81 × 10⁻⁹) | Large (−38.8) |

**주요 통계**
* `answer_relevancy`은 Run B에서 100 % 저하가 관찰되었다.
* `faithfulness`는 차이가 크지만 통계적으로 유의미하지 않아 “추가 데이터 필요”이다.

**증거 예시**
* **Run A** – `A1`, `A2`, `A3`에서 relevancy가 0.83 ~ 0.91, faithfulness는 0 ~ 1로 분포.
* **Run B** – `B1`, `B2`, `B3`에서는 모든 측정값이 0.0.

---

## 원인 분석

1. **모델 구버전/버전 불일치**
   * `gpt-oss-safeguard:20b`는 Ollama에서 제공하는 버전이 아닌 독립 실행형이라 파라미터 세팅이 달라질 수 있다.
   * Model name 차이가 존재함으로써, 내부 엔진, 토크나이저 혹은 사전 학습 파라미터가 다를 가능성이 높다. `[A1/A2/A3]` vs `[B1/B2/B3]`에서 동일한 컨텍스트를 사용했음에도 불구하고, Run B의 출력이 전혀 일치하지 않음.

2. **프롬프트 불일치**
   * Prompt snapshot이 없다는 경고가 발생해 Run B가 사용한 실제 프롬프트를 파악할 수 없으며, 이는 결과 차이의 주요 원천일 수 있다.

3. **시스템 환경/파이프라인 오류**
   * Run B에서 평균 점수가 0점인 것으로 보면, 추출 단계(리트리버) 혹은 응답 생성 단계에서 완전히 실패한 것처럼 보인다.
   * 예시 `B1`–`B3`의 `answer_relevancy`이 0.0으로 표시된 것은 RAG가 전혀 동작하지 않았음을 의미한다.

---

## 개선 제안

| 영역 | 제안 내용 | 근거 |
|------|----------|------|
| **모델 일관성** | `ollama/gpt-oss-safeguard:20b`와 동일한 이미지를 재배포 또는 복사해 사용 | `config_changes`에서 모델명이 변경됨 `[A1]` |
| **프롬프트 스냅샷 확보** | `--db`, `--system-prompt`, `--ragas-prompts` 옵션 사용 후 저장 | `prompt_changes`에서 “missing” 경고 |
| **다중 테스트 케이스** | 4개 대신 10~20개의 케이스를 추가, `faithfulness`의 통계적 유의성을 확보 | `faithfulness` 차이가 통계적으로 미미 |
| **RAG 파이프라인 점검** | Retriever와 Vector Store 설정 재검토, 성능 로깅 | `B1`–`B3`에서 0.0 점수 발생 |
| **환경 인프라** | Docker/LLM 실행 환경 재구성, GPU/CPU 설정과 메모리 한도 확인 | Run B에서 비정상 종료 가능성 |

---

## 다음 단계

1. **Run B를 동일한 구성과 프롬프트로 재실행**
   * 프롬프트 스냅샷을 확보하고, `ollama/gpt-oss-safeguard:20b`와 동일한 이미지 사용.
2. **데이터셋 확대**
   * `test_dataset`에 추가 질문·정답을 삽입해 `faithfulness`와 `answer_relevancy`의 분산을 확인.
3. **분석 리포트 자동화**
   * `comparison_details`와 `change_summary`를 파이프라인에 내장해 변동사항을 쉽게 추적.
4. **통계 검증**
   * `p_value`가 중요한 메트릭(`answer_relevancy`)에 대해 유의수준 0.05 이하 확인, `faithfulness`를 위해 T‑검정으로 효과 크기 재계산.

> **추가 데이터 필요**: 현재 `faithfulness` 변동이 통계적으로 유의미하지 않으므로, 더 많은 케이스와 재실행을 통해 신뢰도를 높여야 한다.

---
