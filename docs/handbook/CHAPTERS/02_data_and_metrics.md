# 02. Data & Metrics

## 목표

데이터셋 포맷, 메트릭, 임계값(threshold), 산출물(artifacts)이 어떻게 연결되는지 이해한다.

## 핵심 관찰

- 데이터셋은 평가의 중심이며, threshold(합격 기준)를 포함한다.
- 메트릭은 실행 결과를 점수화/요약하고, 결과는 run 단위로 저장/비교된다.

## 주요 참고 경로

- 데이터셋 템플릿: `../templates/`
- E2E fixture: `../../tests/fixtures/`
- 사용자 가이드: `../guides/USER_GUIDE.md`
- 도메인 엔티티: `../../src/evalvault/domain/entities/`
- 메트릭 구현: `../../src/evalvault/domain/metrics/`
