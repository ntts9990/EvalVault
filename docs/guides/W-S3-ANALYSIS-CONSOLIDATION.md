# W-S3 — Analysis 페이지 통합 계획

> **상태**: 제안 (W-S6 직후, W-S5b 이전 시점). IA 변경은 별도 사용자 승인 필요.
> **작성**: Phase 4 W-S3 slice
> **범위**: `frontend/src/pages/Analysis*.tsx` + `ComprehensiveAnalysis.tsx`

## 1. 현재 상태

| 페이지 | 라우트 | LOC | 역할 |
|---|---|---:|---|
| `AnalysisLab.tsx` | `/analysis` | 2562 | 분석 실행기 + 현재 결과 뷰어 (런처) |
| `AnalysisCompareView.tsx` | `/analysis/compare` | 1294 | 두 분석 결과 비교 |
| `AnalysisResultView.tsx` | `/analysis/results/:id` | 680 | 저장된 분석 결과 상세 (deep-link) |
| `ComprehensiveAnalysis.tsx` | **(미라우팅)** | 801 | 풀-파이프라인 자율 분석 (orphan) |

**전체 LOC**: 5,337. 공유 컴포넌트: `AnalysisNodeOutputs`, `PrioritySummaryPanel`, `StatusBadge`, `MarkdownContent`, `VirtualizedText`.

## 2. 핵심 발견

- **`ComprehensiveAnalysis.tsx`는 `App.tsx`에서 라우팅되지 않음**. 다른 곳에서도 import되지 않음 (`grep -rn ComprehensiveAnalysis frontend/src/` → 자기 자신만). **데드 코드** 가능성.
- **Lab과 ResultView는 결과 본문 렌더링이 거의 동일**. 차이점은 데이터 소스(in-memory vs persisted) 뿐.
- **Lab과 Compare는 인텐트 카탈로그/메트릭 스펙 fetch를 중복**.

## 3. 통합 옵션

### Option A — 보수적 (4→3 페이지, 권장)
- **유지**: `AnalysisLab` (런처+현재), `AnalysisCompareView` (비교), `AnalysisResultView` (저장 결과 deep-link)
- **삭제**: `ComprehensiveAnalysis.tsx` (orphan 확정 후)
- **추출**: `<AnalysisResultBody>` 공용 컴포넌트 — Lab과 ResultView가 공유, 중복 ~400 LOC 제거 가능
- **장점**: IA 변경 최소, deep-link URL 유지, 회귀 위험 ↓
- **단점**: 페이지 수 그대로 (3개)

### Option B — 통합형 (4→2 페이지)
- **`/analysis`**: 탭/쿼리 파라미터로 런처-현재-저장결과 통합. URL 예: `/analysis?result_id=...` → 자동 ResultView 모드
- **`/analysis/compare`**: 비교 전용 유지
- **삭제**: `ComprehensiveAnalysis.tsx`, `AnalysisResultView.tsx` (라우트 보존 위해 redirect)
- **장점**: 메뉴/IA 단순화
- **단점**: deep-link 동작이 query-param 의존으로 변경됨. 외부 링크 호환성 필요

### Option C — 풀-리라이트 (4→1 페이지)
- 모든 분석 surface를 단일 `/analysis`로 통합, 좌측 사이드바 모드 스위처
- **반대 권장**: 5,337 LOC 한 페이지에 통합은 maintenance 부담↑↑. 코드 스플릿팅 안티패턴.

## 4. 권장: **Option A** (보수적 3-page)

### Phase 1 (이번 W-S3 슬라이스에서 surgical 수준만 진행)
- destructive-state alert 토큰화 (W-S2/W-S5 패턴 일치)
- `EmptyState` 적용 가능 지점 식별 + 적용 (오직 history empty, no-runs-eligible 등)
- T2 인증 surface가 있다면 `AuthorityBadge` 부착 (현재로선 없음 — Compare에 regression 경고가 표시되긴 함; **T3 promote/rollback 텍스트 금지** 재확인)
- IA 변경 없음, 라우트 변경 없음, `ComprehensiveAnalysis` 삭제 보류

### Phase 2 (별도 슬라이스, 사용자 승인 필요)
- `ComprehensiveAnalysis.tsx` 삭제 (orphan 검증 후 `git rm`)
- `<AnalysisResultBody>` 공용 컴포넌트 추출 (Lab 1208~1660 / ResultView 360~660 중복 분석)

### Phase 3 (Option B로 전환 결정 시)
- `/analysis/results/:id` → `/analysis?result_id=:id` 리라이트
- 외부 deep-link 호환 위해 `<Navigate>` redirect 설치
- 사이드바 메뉴 항목 정리

## 5. 위험 요소

- **`ComprehensiveAnalysis.tsx` 삭제 위험**: 미사용 검증을 더 강하게 해야 함. 사이드 채널(직접 URL 입력, 외부 링크) 확인 필요. CHANGELOG 명시.
- **Compare 페이지의 regression 표기**: 현재 "regression"/"개선" 텍스트가 들어가 있는지 점검 필요. **promote/rollback 텍스트 절대 금지** (Reverra-Gate T3 권한).
- **deep-link 호환성**: Phase 3 전환 시 `/analysis/results/:id` 외부 링크 (Slack, 이메일, MLflow 노트 등)가 깨질 수 있음. 영구 redirect 필요.

## 6. 본 슬라이스(W-S3) 실제 적용 범위

| 작업 | 적용 여부 | 비고 |
|---|---|---|
| AnalysisCompareView 알림 블록 토큰화 | ✅ | 1개 블록 (L761~) |
| AnalysisResultView 알림 블록 토큰화 | ✅ | 1개 블록 (L365~) |
| AnalysisLab 알림 블록 추가 토큰화 | ⏭️ | W-S2d에서 이미 처리됨 |
| `ComprehensiveAnalysis` 삭제 | ⏸️ | orphan 검증 후 별도 슬라이스 |
| `<AnalysisResultBody>` 추출 | ⏸️ | Phase 2 |
| 라우트 변경 | ⏸️ | Phase 3 (Option B 채택 시) |

## 7. 차후 슬라이스 의존 관계

```
W-S3 (이번)
   └─ Phase 2 (orphan 삭제 + 공용 컴포넌트)
        └─ Phase 3 (Option B IA 전환, 선택)
```

각 단계는 독립 PR로 분할; 사용자 승인 후 진행.
