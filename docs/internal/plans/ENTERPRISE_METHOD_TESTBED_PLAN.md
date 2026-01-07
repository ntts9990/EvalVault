# 엔터프라이즈 Method Testbed 확장 계획서

> **작성일**: 2026-01-06
> **목적**: 테스트 베드에서 검증된 Method 기능을 엔터프라이즈 버전에 이관하고,
> RAG 단계별 방법론 선택·평가·개선(자동화 포함) 흐름을 정식 기능으로 확립
> **범위**: Method 플러그인/레지스트리 → Stage 분리 → 자동 탐색(AutoRAG/AutoML)

---

## 1. 배경 및 현재 위치

Method Testbed는 다음 기능을 제공한다:
- 메서드 플러그인 인터페이스(`RagMethodPort`)와 레지스트리(내부 YAML + entry point)
- 외부 커맨드 실행(의존성 격리)과 결과 수집
- 질문 중심 데이터셋 로더 + 평가/추적 파이프라인 연결
- `evalvault method list/run` CLI로 실행 및 평가

이 기반을 엔터프라이즈 버전에서 **RAG 단계 분리 + 방법론 선택 + 평가/개선 피드백**까지
확장해 “성능 개선 루프”를 자동화하는 것이 목표다.

---

## 2. 다각도 검토 요약

### 2.1 제품/사용자 관점
- **가치**: 팀별 RAG 전략을 모듈화 → 비교·검증·확산이 쉬워짐
- **요구**: 단계별 선택(검색/재랭크/생성)을 직관적으로 조합, 리더보드/추천 제공
- **리스크**: 방법론 수가 늘면 선택 피로가 커짐 → 추천/자동화 필요

### 2.2 아키텍처/확장성 관점
- **강점**: Hexagonal 구조로 플러그인 확장 용이
- **과제**: 단계별 포트 분해, I/O 계약 명확화, 실행 오케스트레이션 필요

### 2.3 데이터/평가 관점
- **강점**: 기존 평가 메트릭/트래커/threshold 구조 활용 가능
- **과제**: 단계별 품질 지표 정의(검색/재랭크/생성), 원인 추적 모델 필요

### 2.4 운영/보안/컴플라이언스 관점
- **필수**: 멀티테넌시, RBAC, 감사로그, 비밀키 관리, PII 마스킹
- **추가**: 외부 메서드 실행 시 샌드박스/권한 제한

### 2.5 성능/비용 관점
- **이슈**: AutoRAG 탐색은 비용 폭발 위험
- **대응**: 평가 예산/시간/비용 상한 + 캐시/재사용 전략

### 2.6 UX/통합 관점
- **요구**: Web UI에서 Stage Builder + Method Catalog 제공
- **추가**: CLI/API에서 동일 구성 가능, 재현 가능한 파이프라인 스냅샷

### 2.7 테스트/품질 관점
- **필수**: 방법론 조합 테스트, 회귀 스위트, 비용/지연 제한 테스트
- **추가**: 외부 커맨드 실패 복구/타임아웃 검증

---

## 3. 엔터프라이즈 반영 원칙

1) **성공 검증된 기능만 이관**
   - CLI 사용/테스트 통과/문서화 완료된 Method 기능만 승격
2) **단계별 계약(I/O) 표준화**
   - 단계별 입력·출력 스키마를 고정해 호환성과 자동 조합을 보장
3) **자동화는 “옵션”으로 시작**
   - AutoRAG/AutoML은 기본 OFF, 예산/정책이 있는 환경에서만 실행

---

## 4. 기능 범위

### 4.1 In-Scope (엔터프라이즈 핵심)
- RAG 단계 분리 및 단계별 Method 등록/선택
- Method Catalog(버전/태그/비용/호환성/의존성) 관리
- 단계별 평가 지표 + 개선 추천(원인 추적)
- 파이프라인 실행 결과의 재현성과 스냅샷 저장

### 4.2 Out-of-Scope (후순위)
- 실시간 온라인 최적화(실시간 트래픽 실험)
- 완전 자동 배포(프로덕션 롤아웃 자동화)

---

## 5. 아키텍처 설계 초안

### 5.1 Stage 분해(예시)
```
ingest → chunk → index → retrieve → rerank → generate → postprocess → evaluate
```

### 5.2 Stage Port 확장(안)
- `RetrievalMethodPort`, `RerankMethodPort`, `GenerationMethodPort`, `PostProcessPort`
- 또는 단일 `StageMethodPort(stage_type=...)`로 통합

### 5.3 Method Spec 확장(안)
```yaml
methods:
  dense_retriever:
    stage: retrieve
    class_path: "..."
    tags: ["dense", "gpu"]
    cost_profile: { latency_ms: 120, cost_usd: 0.002 }
    compatibility: { requires_docs: true, supports_lang: ["ko", "en"] }
```

### 5.4 Pipeline Manifest(안)
```yaml
pipeline:
  name: "rag_v1"
  stages:
    retrieve: dense_retriever
    rerank: cross_encoder_v2
    generate: gpt_4o
```

### 5.5 개선 추천 흐름
1) Stage별 평가(검색 Recall/Precision, 생성 Faithfulness 등)
2) 실패 패턴 분류(컨텍스트 누락/환각/재랭크 손실)
3) 개선 힌트 제공(“retriever top-k 상향” 등)

---

## 6. AutoRAG/AutoML 전략

### 6.1 탐색 공간
- Stage별 방법론 + 파라미터(예: top-k, chunk size, rerank 모델)

### 6.2 최적화 방식
- 기본: Grid/Random Search
- 고급: Bayesian Optimization, Evolutionary Search, Bandit

### 6.3 제약 조건
- 실행 예산(시간/비용/호출 수) 상한
- 품질 기준 충족 시 조기 종료
- 캐시 기반 중복 실행 제거

---

## 7. UI/CLI/API 설계 방향

### UI
- Method Catalog: 단계별 필터/추천/버전 관리
- Stage Builder: 드래그 조합 + 평가 실행
- Improvement Lab: 실패 원인과 개선 조치 제공

### CLI
- `evalvault method run` 유지
- 신규: `evalvault pipeline plan/run/autotune`

### API
- `/methods`, `/pipelines`, `/runs`, `/autotune`
- 결과는 재현 가능한 스냅샷(모델/프롬프트/설정 해시 포함)

---

## 8. 테스트 전략

- Unit: Stage Port 계약, Method Registry, Config 파서
- Integration: 단계별 실행 + 평가 결과 일관성
- E2E: 파이프라인 조합 + 자동탐색 시나리오
- Performance: 비용/지연 상한 테스트

---

## 9. 단계별 로드맵(제안)

### Phase 0: 스펙 정리
- [ ] Stage taxonomy 확정
- [ ] Method Spec/Manifest 초안 확정

### Phase 1: Method Catalog + Stage 실행기
- [ ] Stage Port 도입
- [ ] Method Catalog API/CLI
- [ ] Pipeline Manifest 저장/로드

### Phase 2: 평가/개선 추천
- [ ] Stage별 평가 지표 연결
- [ ] 개선 추천 룰 엔진

### Phase 3: AutoRAG/AutoML
- [ ] 탐색 엔진(기본 Random/Grid)
- [ ] 예산/정책 기반 자동화

### Phase 4: 엔터프라이즈 운영화
- [ ] 멀티테넌시 + RBAC + 감사로그
- [ ] 워커 분리/큐 기반 실행

---

## 10. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| 방법론 폭발(조합 수 급증) | 탐색 예산/휴리스틱/추천 우선순위 |
| 비용 과다 | 실행 예산 상한 + 캐시 |
| 외부 메서드 의존성 충돌 | 외부 커맨드 실행 + 샌드박스 |
| 데이터 민감성 | PII 마스킹 + 접근 제어 |

---

## 11. 오픈 질문

1) Stage taxonomy를 도메인별로 확장할 것인가?
2) AutoRAG 결과의 승인/배포 흐름은 어떻게 할 것인가?
3) Method Catalog의 배포/버전 승인 정책은 어디까지 강제할 것인가?
