# Web UI 분석 기능 이관 계획 (SPSS/SAS 스타일)

## 1. 목적
CLI(`evalvault analyze`, `analyze-compare`)의 분석 기능을 Web UI로 이관하여, SPSS/SAS와 같은 **메뉴 기반 기능 선택 + 파라미터 입력** 흐름을 제공한다.

## 2. 범위 (CLI 기능 기준)
- 기초 통계 분석
- NLP 분석
- 인과 분석
- 플레이북 기반 개선 인사이트
- 시계열 이상 탐지 및 예측
- 메트릭 상관 네트워크 분석
- 가설 자동 생성
- 비교 분석 (t-test / mann-whitney)

## 3. UI 구조 설계 (메뉴 구조)
### 3.1 메뉴 트리
- **기초 통계**
  - 통계 요약
  - 상관관계 분석
- **시계열 분석**
  - 이상 탐지
  - 성능 예측
- **구조/원인 분석**
  - 인과 분석
  - 메트릭 네트워크
- **지능형 인사이트**
  - 가설 생성
  - 플레이북 분석
- **비교 분석**
  - Run A/B 비교
  - 테스트 타입 선택

### 3.2 사용자 흐름
1) 메뉴 선택
2) 파라미터 입력/선택
3) 실행
4) 결과 표시 및 리포트 다운로드

## 4. CLI 옵션 → UI 컨트롤 매핑
| CLI 옵션 | UI 컨트롤 | 비고 |
| --- | --- | --- |
| `--nlp` | Switch | NLP 분석 활성화 |
| `--causal` | Switch | 인과 분석 활성화 |
| `--dashboard` | Switch | 시각화 대시보드 생성 |
| `--anomaly-detect` | Switch | 이상 탐지 |
| `--window-size` | Number Input | 50~500 |
| `--forecast` | Switch | 성능 예측 |
| `--forecast-horizon` | Number Input | 1~10 |
| `--network` | Switch | 네트워크 분석 |
| `--min-correlation` | Slider | 0.0~1.0 |
| `--generate-hypothesis` | Switch | 가설 생성 |
| `--hypothesis-method` | Select | heuristic/hyporefine/union |
| `--num-hypotheses` | Number Input | 1~20 |
| `--test` | Radio | t-test / mann-whitney |

## 5. 데이터 흐름 (가정 포함)
- UI → API → AnalysisService/Pipeline → 결과 반환
- 일부 기능은 CLI 전용 흐름일 수 있어 API 라우팅 또는 인텐트 매핑 추가가 필요할 수 있음.

## 6. 단계별 이행 계획
### Phase 0: 타입 오류 정리
- `hypothesis_generator_module.py`의 Optional 값 처리 보강
- `pipeline.py`의 `db_path` None 가드 추가

### Phase 1: 메뉴/파라미터 패널 기반 UI 구축
- 메뉴/서브메뉴 구조 고정
- 선택한 기능에 따라 파라미터 폼 동적 렌더링

### Phase 2: 기초 통계 + 시계열 기능 이관
- 기초 통계, 상관 분석
- 이상 탐지, 예측

### Phase 3: 네트워크/가설/플레이북 이관
- 메트릭 네트워크
- 가설 생성
- 플레이북 분석

### Phase 4: 비교 분석 및 리포트 기능 고도화
- Run A/B 비교 UI
- 결과 리포트 다운로드

## 7. 리스크 및 확인 사항
- `--extra analysis/timeseries/dashboard` 설치 여부에 따라 기능 사용 가능 여부 표시 필요
- 장시간 분석 시 진행 상태 표시 필요 (SSE 또는 폴링)
- 일부 기능은 백엔드 API 추가 필요 가능성

## 8. 확인 필요 사항 (Open Questions)
- Web UI 분석 요청 시 API 호출 방식 (기존 `pipeline` 재사용 vs 신규 API)
- 결과 시각화 방식 (이미지 다운로드 vs UI 차트 렌더링)
- 분석 실행 이력 저장/조회 범위
