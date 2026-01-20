# 보험 도메인 요약(Summary) 메트릭 확장 PRD/SDD (EvalVault)

## 1) 목표
- 보험 상담/약관 요약에 대해 “요약 품질 + 리스크 안내 + 단정 표현 억제”를 평가하는 커스텀 메트릭 4종을 추가한다.
- 기존 EvalVault 평가 파이프라인(메트릭 레지스트리, CUSTOM_METRIC_MAP, 리포트/엑셀/UI)에 일관되게 통합한다.
- 메트릭 정의/룰/스냅샷을 명시하여 재현성과 운영 튜닝을 확보한다.

## 2) 범위
### 포함
- 신규 메트릭 4종
  - summary_accuracy
  - summary_risk_coverage
  - summary_non_definitive
  - summary_needs_followup
- TestCase metadata 확장
  - summary_tags: list[str]
  - summary_intent: "agent_notes"
- 통합 순서
  1) CLI
  2) Excel/리포트
  3) Web UI

### 제외
- 신규 평가 파이프라인 도입
- Ragas 요약 메트릭의 의미 변경
- 합의되지 않은 추가 메트릭 도입

## 3) 현황 및 통일성 기준
- EvalVault는 custom metric을 evaluator.CUSTOM_METRIC_MAP에 등록하고, registry에서 노출 스펙을 관리한다.
- summary 메트릭은 CLI/리포트/UI에서 별도 정렬/임계값 기준을 유지한다.
- TestCase.metadata는 JSON 로더에서 이미 지원되므로, summary_tags/summary_intent는 metadata에 추가하는 방식이 통일적이다.

## 4) 데이터 스키마
### TestCase.metadata
- summary_tags: list[str] (선택)
- summary_intent: "agent_notes" (선택, 내부용 고정)

예시:
```json
{
  "id": "tc-001",
  "question": "상담 요약 요청",
  "answer": "요약문 ...",
  "contexts": ["대화 원문 ..."],
  "ground_truth": "현업 요약 ...",
  "metadata": {
    "summary_intent": "agent_notes",
    "summary_tags": ["exclusion", "deductible", "limit", "needs_followup"]
  }
}
```

## 5) 메트릭 정의
### 5.1 summary_accuracy
- 목적: 요약문 내 핵심 엔티티(금액/기간/조건 등)가 컨텍스트에 근거하는지 평가
- 입력: answer, contexts
- 점수: supported_entities / summary_entities
- 보정 정책:
  - summary_entities가 비어있고 context_entities가 있으면 0.5
  - context_entities가 없으면 0.0

### 5.2 summary_risk_coverage
- 목적: 보험 리스크 항목(면책/감액/자기부담금/한도 등) 누락 여부 평가
- 입력: answer, metadata.summary_tags
- 점수: covered_tags / expected_tags
- expected_tags가 없으면 1.0

### 5.3 summary_non_definitive
- 목적: 단정 표현(“무조건 지급”, “반드시”)을 억제했는지 평가
- 입력: answer
- 점수: 단정 표현이 없으면 1.0, 있으면 0.0

### 5.4 summary_needs_followup
- 목적: 추가 확인이 필요한 경우 요약에 “추가 확인 필요”를 명시했는지 평가
- 입력: answer, metadata.summary_tags
- 규칙:
  - needs_followup 태그가 있으면 followup 표현 포함 시 1.0, 아니면 0.0
  - 태그가 없으면 followup 표현이 없을 때 1.0

## 6) 임계값(초기 권장)
- summary_accuracy: 0.90
- summary_risk_coverage: 0.90
- summary_non_definitive: 0.80
- summary_needs_followup: 0.80

## 7) 룰셋(초기)
### tag -> keyword 매핑
- exclusion: 면책, 보장 제외, 지급 불가, exclusion
- deductible: 자기부담, 본인부담금, deductible, copay
- limit: 한도, 상한, 최대, limit, cap
- waiting_period: 면책기간, 대기기간, waiting period
- condition: 조건, 단서, 다만, condition
- documents_required: 서류, 진단서, 영수증, documents
- needs_followup: 확인 필요, 추가 확인, 담당자 확인, 재문의, follow up

### 단정 표현 탐지
- 무조건, 반드시, 100%, 전액 지급, 확실히, 분명히, always, guaranteed

## 8) 통합 지점 (구현 순서)
### 8.1 CLI
- 신규 메트릭 클래스 추가
- evaluator.CUSTOM_METRIC_MAP 등록
- metrics.registry에 스펙 추가
- summary threshold profile 및 SUMMARY_METRIC_ORDER 확장

### 8.2 Excel/리포트
- custom_metric_snapshot에 신규 메트릭 상세 기록
- Excel export에서 JSON 컬럼 안전 변환(호환성 보강)
- 요약 리포트/LLM 리포트에서 summary 메트릭 경고 라인 확장

### 8.3 Web UI
- SUMMARY_METRICS/thresholds 확장
- 요약 메트릭 카드/차트/필터 반영

## 9) 리스크/주의사항
- CSV/Excel 로더는 test_case metadata를 현재 지원하지 않음 (JSON 우선)
- 단정 표현/리스크 키워드는 표현 다양성으로 과소/과대 탐지 가능
- summary_non_definitive는 “단정 억제” 점수임을 명확히 표기 필요
- Excel export는 JSON 컬럼이 섞여있어 변환 실패 가능 → json_columns 강제 변환 유지

## 10) 하이브리드(규칙 + LLM 보정) 설계안

### 10.1 공통 흐름
1) 규칙 기반 1차 점수 계산
2) 경계 사례/태그 누락 등 불확실 구간에서만 LLM 보정
3) 최종 점수 합성
- 기본: `final = 0.7 * rule + 0.3 * llm`
- 또는 LLM이 높은 확신을 줄 때만 override

### 10.2 메트릭별 보정 기준
- `summary_accuracy`
  - 경계 조건: rule 점수 0.3~0.7, 엔티티 수가 매우 적음
  - LLM 질문: “요약의 수치/기간/조건이 컨텍스트에 근거하는가?” (0~1)
- `summary_risk_coverage`
  - 태그가 없는 경우 LLM이 리스크 항목 존재 여부를 추정 → 가상 태그 생성
  - LLM 질문: “요약에 면책/감액/자기부담/한도/조건이 포함되었는가?”
- `summary_non_definitive`
  - 규칙이 0.0인 경우만 LLM 재판정
  - LLM 질문: “요약이 사실을 단정적으로 확정하는가?” (0~1)
- `summary_needs_followup`
  - needs_followup 태그가 있거나 규칙 판단이 모호할 때만 LLM 사용
  - LLM 질문: “요약에 추가 확인/재문의 안내가 포함되어 있는가?” (0/1)

### 10.3 운영 가이드
- LLM 보정은 **경계 사례에만 제한**하여 비용/분산을 줄인다.
- 프롬프트/모델 버전을 스냅샷에 기록해 회귀를 추적한다.
- 규칙 기반 점수와 보정 점수를 함께 저장하여 디버깅 가능하게 한다.

## 11) 롤아웃
1) CLI (메트릭 계산/표시)
2) Excel/리포트
3) Web UI
