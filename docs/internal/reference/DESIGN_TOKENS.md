# 디자인 토큰 정의서

> 작성일: 2026-01-09
> 상태: v0.1 (초안)
> 목적: Web UI의 색상/타이포/레이아웃/모션 토큰을 고정한다.

## 1) 디자인 원칙

- 기본 톤: **흰색 배경 + 검은 텍스트**.
- 강조색: **#4E81EE** (버튼/링크/핵심 CTA).
- 정보 밀도: 요약 → 상세의 계층 구조 유지.
- 데이터 시각화는 색 대비와 범주 구분을 최우선.

## 2) 색상 토큰 (기본)

| 토큰 | 값 | 용도 |
| --- | --- | --- |
| `--background` | `#FFFFFF` | 기본 배경 |
| `--foreground` | `#0B0D10` | 기본 텍스트 |
| `--surface` | `#F7F8FA` | 카드/패널 배경 |
| `--surface-2` | `#F1F3F6` | 서브 패널 |
| `--border` | `#E4E7EC` | 기본 보더 |
| `--muted` | `#5B6577` | 보조 텍스트 |
| `--muted-2` | `#8B93A4` | 약한 설명 |

## 3) 브랜드/액센트

| 토큰 | 값 | 용도 |
| --- | --- | --- |
| `--primary` | `#4E81EE` | CTA, 활성 상태 |
| `--primary-strong` | `#2F66E0` | hover/active |
| `--primary-soft` | `#E7EFFF` | 강조 배경 |
| `--primary-foreground` | `#FFFFFF` | CTA 텍스트 |

## 4) 상태 색상 (평가/경고)

| 상태 | 토큰 | 값 |
| --- | --- | --- |
| 성공 | `--success` | `#2E7D32` |
| 주의 | `--warning` | `#F4A62A` |
| 위험 | `--danger` | `#E5474E` |
| 정보 | `--info` | `#1F6FEB` |
| 중립 | `--neutral` | `#667085` |

## 5) 차트 팔레트 (색맹 안전 우선)

- `#4E81EE` (Primary Blue)
- `#26A69A` (Teal)
- `#F2994A` (Orange)
- `#7BC96F` (Green)
- `#EB5757` (Red)
- `#B08968` (Brown)
- `#8A8FD1` (Indigo)
- `#F2C94C` (Yellow)

## 6) 타이포그래피

| 토큰 | 값 | 용도 |
| --- | --- | --- |
| `--font-sans` | `"IBM Plex Sans KR"` | 본문 |
| `--font-display` | `"Space Grotesk"` | 헤더/수치 |
| `--font-mono` | `"JetBrains Mono"` | 코드/ID |

**크기 스케일 (px)**: 12 / 14 / 16 / 18 / 20 / 24 / 28 / 32 / 40
**라인 높이**: 1.2 (헤더), 1.4 (본문), 1.6 (설명)

## 7) 간격/레이아웃

**Spacing (px)**: 2 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64
**Container**: 1200px (Desktop), 100% (Mobile)
**Grid**: 12 columns, gutter 24px

## 8) 라운드/보더

| 토큰 | 값 |
| --- | --- |
| `--radius-xs` | 4px |
| `--radius-sm` | 8px |
| `--radius-md` | 12px |
| `--radius-lg` | 16px |

## 9) 그림자

| 토큰 | 값 |
| --- | --- |
| `--shadow-xs` | `0 1px 2px rgba(16,24,40,0.08)` |
| `--shadow-sm` | `0 2px 6px rgba(16,24,40,0.12)` |
| `--shadow-md` | `0 8px 24px rgba(16,24,40,0.14)` |

## 10) 모션

| 토큰 | 값 | 용도 |
| --- | --- | --- |
| `--duration-fast` | 120ms | 토글/버튼 |
| `--duration-med` | 200ms | 카드/탭 |
| `--duration-slow` | 420ms | 페이지 전환 |
| `--ease-standard` | `cubic-bezier(0.2,0.8,0.2,1)` | 기본 |
| `--ease-spring` | `cubic-bezier(0.16,1,0.3,1)` | 강조 |

## 11) 컴포넌트 토큰 (핵심)

### 버튼

- **Primary**: `--primary` 배경 + `--primary-foreground` 텍스트.
- **Secondary**: `--surface` 배경 + `--foreground`.
- **Ghost**: 투명 + `--foreground` + hover `--surface-2`.

### 카드/패널

- 배경: `--surface`
- 보더: `--border`
- 그림자: `--shadow-xs`

### 입력

- 기본: `--surface` + `--border`
- 포커스 링: `--primary` 2px
- 에러 상태: `--danger` 보더

### 배지/태그

- Success: `--success` 텍스트 + `#ECFDF3` 배경
- Warning: `--warning` 텍스트 + `#FFFAEB` 배경
- Danger: `--danger` 텍스트 + `#FEF3F2` 배경

## 12) 데이터 시각화 토큰

- 라인 두께: 2px
- 그리드 라인: `#EEF1F5`
- 기준선: `#D0D5DD` 점선
- 강조 포인트: `--primary`

## 13) 접근성 기준

- 텍스트 대비 최소 4.5:1.
- 포커스 링은 항상 시각적으로 구분.
- 색상만으로 상태를 구분하지 않음(아이콘/텍스트 병행).

## 14) Tailwind 적용 메모

기존 `frontend/src/index.css`의 CSS 변수 구조를 유지하되, HSL 변환이 필요하다.
예: `#4E81EE` → HSL 변환 후 `--primary`로 적용.

```css
:root {
  --background: 0 0% 100%;
  --foreground: 220 14% 4%;
  --primary: 219 80% 62%;
  --primary-foreground: 0 0% 100%;
}
```

## 15) 요약 카드 표준 용어

| 구분 | 표준 용어 | 설명 |
| --- | --- | --- |
| 증감 표현 | 증가 / 감소 / 유지 | 수치 변화는 가치 판단 없이 표현 |
| 품질 변화 | 개선 / 악화 | 실패/오류 등 품질 지표에만 사용 |
| 시간 변화 | 지연 / 단축 | 처리 시간의 증가/감소를 표현 |
| 케이스 변화 | 추가 / 해소 | 우선순위 케이스 증감 표현 |
| 비교 기준 | A → B 비교 기준 | 비교 방향을 항상 명시 |
