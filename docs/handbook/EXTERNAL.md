# EvalVault Handbook (External Summary)

> 외부 공개용 요약본입니다. 내부 경로/운영 절차/실데이터/수치/시크릿은 포함하지 않습니다.

## EvalVault가 하는 일

EvalVault는 RAG(Retrieval-Augmented Generation) 시스템을 대상으로,
"변경이 진짜 개선인지"를 데이터셋과 메트릭으로 재현 가능하게 검증하고
결과를 이해/비교/공유할 수 있도록 돕는 평가·분석 워크플로 도구입니다.

## 핵심 흐름

1) 데이터셋 준비
2) 메트릭 평가 실행
3) 결과 요약 및 비교
4) 문제 원인 분석(선택)

## 발표/커뮤니케이션 포인트

비전문가 대상 설명에서는 "평가 → 분석 → 비교 → 개선"의 반복 흐름과
각 실행이 `run_id`로 묶여 결과를 공유/재현할 수 있다는 점을 강조합니다.
점수만 보여주기보다 "왜 그렇게 나왔는지"를 근거와 함께 설명하는 구조가 핵심입니다.

## 문서

- 내부 상세 handbook: `INDEX.md`
- 사용자/운영 가이드: `../guides/USER_GUIDE.md` (deprecated 스텁, 최신은 handbook)
- 상태/로드맵: `CHAPTERS/08_roadmap.md` (SSoT, 내부 상세)
