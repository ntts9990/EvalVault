# 방법론 7: 테스트 기반 기능 지도

> Audience: 개발자/기여자
> Purpose: 테스트를 기준으로 핵심 기능/행동을 역추적
> Last Updated: 2026-01-06

---

## 핵심 질문

- “테스트가 보장하는 핵심 기능은 무엇인가?”

---

## 사용 목적

- 실제로 중요한 기능/흐름을 우선 파악
- 변경 시 영향 범위를 테스트 단위로 추정
- 테스트 공백(미커버 영역) 탐지

---

## 빠른 절차

1. 테스트 디렉터리를 분류한다(단위/통합/E2E).
2. 주요 테스트 파일을 기능 단위로 묶는다.
3. 테스트가 참조하는 모듈을 매핑한다.
4. 미커버 영역을 별도로 표시한다.

---

## 짧은 예시 (개념 파악용)

```text
tests/integration/test_data_flow.py  -> dataset loader + evaluator
tests/unit/test_cli_init.py          -> CLI 옵션/엔트리포인트
```

---

## 다른 방법론 대비 장점/단점

| 구분 | 내용 |
|---|---|
| 장점 | 실행 흐름을 “보증 범위” 중심으로 요약할 수 있다. |
| 단점 | 테스트가 없는 영역은 구조 파악이 불완전해질 수 있다. |

---

## 시각화/도구

- `pytest --collect-only`로 수집 목록 확인
- `rg "Evaluator" tests/`로 테스트-모듈 연결
- 표 형태로 테스트 ↔ 모듈 매핑

---

## EvalVault 적용 포인트

- `tests/unit`
- `tests/integration`
- `tests/e2e_data`
- `tests/fixtures`
