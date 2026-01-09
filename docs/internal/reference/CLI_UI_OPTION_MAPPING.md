# CLI 옵션-UI 매핑표

> 작성일: 2026-01-09
> 목적: CLI 옵션을 웹 UI에서 계층적으로 노출하기 위한 매핑 기준을 고정한다.
> 범위: `run`, `analyze`, `analyze-compare`, `pipeline analyze`, `compare`, `stage`.

## 1) 매핑 원칙

- **기본은 간결, 고급은 접힘**: 기본 입력(데이터/메트릭/프리셋)을 상단에 고정.
- **컨텍스트 우선**: Evaluation Studio → Run Details → Analysis Lab 순으로 인지 흐름 일치.
- **의존성/제약 선노출**: 상호 배타 옵션과 필수 조건을 UI에서 즉시 안내.

## 2) `evalvault run` 매핑

### 2.1 실행 모드/프리셋

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 실행 모드 | `--mode` | Evaluation Studio 상단 | 모드 토글 (Simple/Full) | Simple: 기본 메트릭 2종 + Phoenix 고정 |
| 간편/전체 별칭 | `run-simple`, `run-full` | 실행 메뉴 | 빠른 실행 버튼 | 내부적으로 `--mode` 설정 |
| 프리셋 | `--preset` | 메트릭 섹션 | 프리셋 카드 | `quick/production/summary/comprehensive` |
| 요약 평가 | `--summary` | 메트릭 섹션 | 요약 토글 | `--preset`과 충돌 시 경고 |

### 2.2 기본 입력/모델

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 데이터셋 | `<dataset>` | Evaluation Studio 1단계 | 업로드/경로 선택 | 스키마 검증 포함 |
| 메트릭 | `--metrics` | Evaluation Studio 2단계 | 멀티 선택 | Simple 모드는 강제 값 |
| 임계값 프로필 | `--threshold-profile` | 메트릭 상세 | 프로필 드롭다운 | `summary/qa` |
| 모델 프로필 | `--profile` | 상단 컨텍스트 바 | 프로필 선택 | `.env`/`models.yaml` 연동 |
| 모델 오버라이드 | `--model` | 상단/고급 | 모델 입력 | 프로필 우선순위 경고 |

### 2.3 분석/출력

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 결과 저장 | `--output` | 실행 전/후 | 저장 경로 | JSON 요약 |
| 자동 분석 | `--auto-analyze` | 실행 옵션 | 토글 | 완료 후 파이프라인 실행 |
| 분석 JSON | `--analysis-json` | 분석 옵션 | 저장 경로 | 기본 `reports/analysis` |
| 분석 보고서 | `--analysis-report` | 분석 옵션 | 저장 경로 | Markdown |
| 분석 디렉터리 | `--analysis-dir` | 분석 옵션 | 저장 디렉터리 | 아티팩트 포함 |

### 2.4 Retriever/KG

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| Retriever | `--retriever` | Evaluation Studio 3단계 | 라디오 선택 | `bm25/dense/hybrid/graphrag` |
| Retriever 문서 | `--retriever-docs` | Retriever 설정 | 파일 선택 | `.json/.jsonl/.txt` |
| KG 파일 | `--kg` | GraphRAG 설정 | 파일 선택 | GraphRAG 전용 |
| Top-K | `--retriever-top-k` | Retriever 설정 | 슬라이더 | 기본 5 |

### 2.5 트래커/관측(Phoenix/Langfuse/MLflow)

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 트래커 | `--tracker` | Observability 섹션 | 드롭다운 | Simple 모드 Phoenix 고정 |
| (Deprecated) | `--langfuse` | 없음 | 숨김 | 유지하지 않음 |
| Phoenix 최대 트레이스 | `--phoenix-max-traces` | Phoenix 설정 | 숫자 입력 | 선택 |
| Phoenix dataset | `--phoenix-dataset` | Phoenix 설정 | 텍스트 | 업로드 이름 |
| dataset 설명 | `--phoenix-dataset-description` | Phoenix 설정 | 텍스트 | 선택 |
| Phoenix experiment | `--phoenix-experiment` | Phoenix 설정 | 텍스트 | dataset 필요 |
| experiment 설명 | `--phoenix-experiment-description` | Phoenix 설정 | 텍스트 | 선택 |

### 2.6 프롬프트/메타데이터

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 프롬프트 매니페스트 | `--prompt-manifest` | 고급 설정 | 파일 선택 | Simple 모드 비활성 |
| 프롬프트 파일 | `--prompt-files` | 고급 설정 | 다중 선택 | Phoenix diff |
| 프롬프트 세트 이름 | `--prompt-set-name` | 고급 설정 | 텍스트 | DB 저장 |
| 프롬프트 세트 설명 | `--prompt-set-description` | 고급 설정 | 텍스트 | 선택 |
| 시스템 프롬프트 | `--system-prompt` | 고급 설정 | 텍스트 | 파일과 배타 |
| 시스템 프롬프트 파일 | `--system-prompt-file` | 고급 설정 | 파일 선택 | 텍스트와 배타 |
| 시스템 프롬프트 이름 | `--system-prompt-name` | 고급 설정 | 텍스트 | 선택 |
| Ragas 프롬프트 | `--ragas-prompts` | 고급 설정 | 파일 선택 | YAML |

### 2.7 Domain Memory

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| Domain Memory 사용 | `--use-domain-memory` | Evaluation Studio 3단계 | 토글 | Simple 모드 비활성 |
| 도메인 | `--memory-domain` | Memory 설정 | 텍스트 | 기본: dataset 메타 |
| 언어 | `--memory-language` | Memory 설정 | 드롭다운 | 기본 `ko` |
| 메모리 DB | `--memory-db` | Memory 설정 | 경로 선택 | 기본 DB |
| 컨텍스트 증강 | `--augment-context` | Memory 설정 | 토글 | 사실 추가 |

### 2.8 성능/실행/저장

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 로그 상세 | `--verbose` | 고급 설정 | 토글 | 디버그 |
| 병렬 실행 | `--parallel` | 성능 설정 | 토글 | 배치 필수 |
| 배치 크기 | `--batch-size` | 성능 설정 | 슬라이더 | 기본 5 |
| 스트리밍 | `--stream` | 성능 설정 | 토글 | 대용량 대응 |
| 스트림 청크 | `--stream-chunk-size` | 성능 설정 | 숫자 입력 | 기본 200 |
| Stage 이벤트 저장 | `--stage-events` | Performance | 파일 경로 | JSONL |
| Stage DB 저장 | `--stage-store` | Performance | 토글 | `--db` 필요 |
| DB 경로 | `--db` | Settings/고급 | 경로 선택 | SQLite |

### 2.9 제약/검증 규칙

- `--summary`와 `--preset`은 동시에 사용할 수 없음.
- `--system-prompt`와 `--system-prompt-file`은 상호 배타.
- Simple 모드는 기본 메트릭/트래커/프롬프트 메타가 강제됨.
- `--stage-store`는 `--db`가 필요.
- Retriever 사용 시 문서/GraphRAG 입력 누락 여부를 사전 검증.

## 3) `evalvault analyze` 매핑

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 런 선택 | `<run_id>` | Analysis Lab | 런 선택기 | 필수 |
| NLP 분석 | `--nlp` | 분석 옵션 | 토글 | 임베딩 사용 |
| 인과 분석 | `--causal` | 분석 옵션 | 토글 | 선택 |
| 개선 플레이북 | `--playbook` | 개선안 | 토글 | stage metrics 필요 |
| LLM 기반 개선안 | `--enable-llm` | 개선안 | 토글 | 프로필 필요 |
| 출력 JSON | `--output` | 결과 저장 | 파일 경로 | 분석 결과 |
| 리포트 | `--report` | 결과 저장 | 파일 경로 | Markdown/HTML |
| DB 저장 | `--save` | 결과 저장 | 토글 | Analysis 저장 |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |
| 프로필 | `--profile` | 상단 컨텍스트 | 프로필 선택 | NLP/LLM용 |

## 4) `evalvault analyze-compare` 매핑

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 비교 런 | `<run_id1> <run_id2>` | Compare/Analysis Lab | Base/Target 선택 | 필수 |
| 메트릭 필터 | `--metrics` | 비교 옵션 | 멀티 선택 | 선택 |
| 통계 테스트 | `--test` | 비교 옵션 | 드롭다운 | `t-test`, `mann-whitney` |
| JSON 출력 | `--output` | 결과 저장 | 파일 경로 | 파이프라인 결과 |
| 리포트 | `--report` | 결과 저장 | 파일 경로 | Markdown |
| 출력 디렉터리 | `--output-dir` | 결과 저장 | 디렉터리 | 아티팩트 포함 |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |
| 프로필 | `--profile` | 상단 컨텍스트 | 프로필 선택 | LLM 리포트 |

## 5) `evalvault pipeline analyze` 매핑

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 분석 쿼리 | `<query>` | Analysis Lab | 자연어 입력 | 필수 |
| 런 선택 | `--run` | Analysis Lab | 런 선택기 | 선택 |
| JSON 출력 | `--output` | 결과 저장 | 파일 경로 | 요약 JSON |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |

## 6) `evalvault compare` 매핑

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 비교 런 | `<run_id1> <run_id2>` | Compare | Base/Target 선택 | 필수 |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |

## 7) `evalvault stage` 매핑

### 7.1 ingest

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 이벤트 파일 | `<file>` | Run Details > Performance | 파일 업로드 | JSON/JSONL |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |

### 7.2 list/summary

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 런 ID | `<run_id>` | Run Details > Performance | 런 선택 | 필수 |
| Stage 타입 | `--stage-type` | 필터 | 드롭다운 | list 전용 |
| 최대 행 | `--limit` | 필터 | 숫자 입력 | list 전용 |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |

### 7.3 compute-metrics/report

| 항목 | CLI 옵션 | UI 위치 | UI 요소 | 비고 |
| --- | --- | --- | --- | --- |
| 런 ID | `<run_id>` | Performance | 런 선택 | 필수 |
| relevance JSON | `--relevance-json` | 고급 | 파일 선택 | 선택 |
| thresholds JSON | `--thresholds-json` | 고급 | 파일 선택 | 선택 |
| thresholds profile | `--thresholds-profile` | 고급 | 텍스트 | 기본 프로필 |
| playbook | `--playbook` | 고급 | 파일 선택 | report 전용 |
| save metrics | `--save-metrics` | 고급 | 토글 | report 전용 |
| DB 경로 | `--db` | Settings | 경로 선택 | SQLite |
