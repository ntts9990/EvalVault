# 실험/아티팩트 추적 스택 (MLflow + Phoenix)

## 목적
- 폐쇄망/자가호스팅 환경에서 실험 버전, 아티팩트, 관찰(트레이스)을 안정적으로 관리한다.
- 소수 협업(웹/리포트 공유 수준)을 전제로 운영 복잡도를 최소화한다.

## 요구사항 요약
- 폐쇄망(air-gapped) 운영 가능
- 상업적 사용 가능
- 아티팩트 유형 다양(데이터셋, 분석방법, 메타데이터, 분석결과, 엑셀, 보고서, 프롬프트 스냅샷, 2축/3축 지표)

## 권장 스택
### MLflow + Phoenix
- MLflow: 실험/버전/아티팩트 저장
- Phoenix: LLM 트레이싱/관찰/디버깅

### 운영 규칙 (필수)
- 모든 평가 run은 **MLflow + Phoenix에 동시에 로깅**된다.
- tracker 옵션에서 둘 중 하나라도 누락되면 실행이 실패한다.
- 기본 tracker: `mlflow+phoenix`

### 라이선스/자가호스팅 참고
- MLflow: Apache 2.0 (상업 사용 가능) https://raw.githubusercontent.com/mlflow/mlflow/master/LICENSE.txt
- Phoenix: Elastic License 2.0 (자가호스팅 허용, 제3자에게 SaaS 제공 금지) https://raw.githubusercontent.com/Arize-ai/phoenix/main/LICENSE

## 아키텍처/데이터 흐름
1. EvalVault 실행으로 run 생성
2. MLflow에 실험 메타데이터, 지표, 아티팩트 저장
3. Phoenix에 트레이스/스팬 전송
4. 리포트 공유는 MLflow 결과와 Phoenix 트레이스를 함께 참조

### 핵심 연결 키
- run_id (EvalVault Run ID)
- dataset_name / dataset_version
- model_name / model_version
- prompt_version / retrieval_version
- evaluation_profile (dev/prod 등)

## 폐쇄망 배포 체크리스트
### 네트워크/보안
- [ ] 외부 outbound 차단 환경 테스트 완료
- [ ] 내부 PKI 또는 사설 TLS 인증서 적용
- [ ] 사설 DNS/레지스트리 준비

### 스토리지
- [ ] MLflow backend store: Postgres
- [ ] MLflow artifact store: MinIO(S3 호환) 또는 내부 오브젝트 스토리지
- [ ] Phoenix 저장소: Postgres

### 서비스 구성
- [ ] MLflow Tracking Server
- [ ] Phoenix Server
- [ ] Postgres (MLflow/Phoenix 분리 권장)
- [ ] Object Storage (MinIO)

### 운영
- [ ] 백업/복구 정책 수립
- [ ] 아티팩트 보관 기간/정책 정의
- [ ] 접근 제어(사용자/토큰/권한) 설정

## 아티팩트/메타데이터 규약 (권장)
### 공통 메타데이터 (MLflow tags/params)
- run_id (필수)
- dataset_name, dataset_version
- model_name, model_version
- prompt_version, retrieval_version
- evaluation_profile
- git_commit, git_branch
- pipeline_version (EvalVault 버전)

### 아티팩트 폴더 구조 (예시)
artifacts/
  dataset/
  metrics/
    metrics.json
    metrics.csv
  analysis/
    analysis.json
    analysis.md
  reports/
    report.pdf
    report.xlsx
  prompts/
    prompt_snapshot.json
  config/
    run_config.json
    model_config.json

### 지표 규약 (2축/3축)
metrics.json 구조 예시:
{
  "axes": ["faithfulness", "relevance", "groundedness"],
  "scores": {
    "faithfulness": 0.83,
    "relevance": 0.79,
    "groundedness": 0.74
  },
  "aggregations": {
    "mean": 0.79,
    "median": 0.80,
    "p50": 0.80,
    "p90": 0.92
  },
  "by_group": {
    "dataset_split": {
      "train": 0.78,
      "test": 0.81
    }
  }
}

### 스냅샷 규칙
- 데이터셋/프롬프트/파라미터는 immutable snapshot으로 저장
- 각 스냅샷에 sha256 기록

## EvalVault 연동 참고
- MLflow 어댑터: src/evalvault/adapters/outbound/tracker/mlflow_adapter.py
- Phoenix 어댑터: src/evalvault/adapters/outbound/tracker/phoenix_adapter.py

## 설정 값
- `MLFLOW_TRACKING_URI`: MLflow tracking server URI
- `MLFLOW_EXPERIMENT_NAME`: 실험 이름 (기본: evalvault)
- `PHOENIX_ENDPOINT`: Phoenix OTLP endpoint (예: http://localhost:6006/v1/traces)
- `PHOENIX_API_TOKEN`: Phoenix API 토큰 (옵션)

## CLI 기본 사용
```bash
uv run evalvault run <DATASET> --tracker mlflow+phoenix
```
