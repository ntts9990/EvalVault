EvalVault는 평가/저장/추적/분석의 “기능 세트”는 이미 상당히 탄탄합니다(헥사고날 아키텍처 + Domain Memory + DAG 분석 파이프라인 + Phoenix/Langfuse/MLflow 추적 + 스트리밍 로더 등).  ￼  ￼  ￼
다만 “엔터프라이즈 급”에서 요구되는 건 기능 자체보다 운영 모델(멀티유저/멀티테넌시), 신뢰성/보안/컴플라이언스, 확장성(워크로드 분리), 관측성의 표준화 같은 비기능 요구사항(NFR) 이고, 현재 문서 상으로는 CLI/Web UI 중심 단일 애플리케이션 모델이어서 이 부분이 가장 큰 개선 포인트입니다.  ￼  ￼

아래는 “엔터프라이즈에서 제대로 굴러가게” 만들기 위한 개선점을 체계적으로(우선순위/영역/구현 방향) 정리한 내용입니다.

⸻

1) 현재 아키텍처의 강점(엔터프라이즈 전환에 유리한 이유)

문서에서 확인되는 강점은, 엔터프라이즈화에 필요한 변경을 “기능을 뜯어고치기”가 아니라 “어댑터를 추가/교체” 하는 방식으로 가져갈 수 있다는 점입니다.
	•	Hexagonal (Ports & Adapters) + Clean + DDD 구조로 도메인 로직을 외부 의존성에서 분리  ￼
	•	멀티 LLM/멀티 DB/멀티 Tracker (OpenAI/Ollama/Azure/Anthropic, SQLite/Postgres, Langfuse/MLflow/Phoenix) 이미 포트 기반으로 교체 가능  ￼  ￼
	•	StreamingDatasetLoader + AsyncBatchExecutor 등 “대규모 평가”를 의식한 실행기 존재  ￼  ￼
	•	Phoenix 기반 관측성(트레이싱/데이터셋/실험/프롬프트/임베딩)과 Drift → Gate → 릴리즈 노트 자동화 플레이북이 이미 존재  ￼  ￼
	•	테스트/CI 기반이 큼(테스트 1,671, 커버리지 89% 등) → 엔터프라이즈에서 중요한 “변경 안정성” 확보에 유리  ￼  ￼

즉, “기능을 새로 만들기”보다 운영/플랫폼 레이어를 얹는 방향이 맞습니다.

⸻

2) 엔터프라이즈 레디의 핵심 관점(비기능 요구사항 체크리스트)

엔터프라이즈에서 “제대로 작동”은 보통 아래 항목을 의미합니다.
	1.	멀티유저/멀티테넌시: 조직/프로젝트/권한(RBAC), SSO, 감사로그
	2.	신뢰성: 재시도/타임아웃/부분실패 격리, 작업 취소/재개, idempotency
	3.	확장성: 대량 평가를 “웹/CLI 프로세스”에서 분리해 워커 풀로 수평 확장
	4.	보안/컴플라이언스: 비밀키 관리, 데이터 암호화/마스킹, 보존/삭제 정책
	5.	관측성 표준화: tracing 뿐 아니라 metrics/logs, SLO/알람/런북
	6.	데이터 거버넌스: 데이터셋/프롬프트/모델/환경 스냅샷의 재현성과 계보(lineage)
	7.	운영 자동화: 스케줄 평가, 회귀 스위트, 정책 기반 게이트, 릴리즈 노트 자동 생성

EvalVault는 5,7의 일부는 이미 잘 되어 있지만(Phoenix playbook, gate, regression runner), 1~4와 6은 “제품/플랫폼 관점”에서 보강이 필요합니다.  ￼  ￼

⸻

3) 현재 문서 기반 Gap 분석(무엇이 부족한가)

A. 실행 모델(Execution Model)
	•	현 상태: CLI/Web UI가 평가를 직접 실행하는 흐름이 중심  ￼  ￼
	•	엔터프라이즈 갭:
	•	장시간 작업(수천 TC)을 UI/CLI 프로세스에서 돌리면 타임아웃/리소스 경쟁/사용자 세션 종료에 취약
	•	워크로드를 분리하지 않으면 수평 확장이 어려움
	•	“취소/재개/재시도/중복요청 방지(idempotency)” 같은 작업 관리가 어려움

B. 보안/멀티테넌시
	•	현 상태: .env 기반 키/프로필, 로컬 실행 중심 가이드  ￼
	•	엔터프라이즈 갭:
	•	SSO/OIDC, RBAC, 프로젝트 단위 격리(tenant_id) 등 언급 없음
	•	감사로그(누가 어떤 데이터로 어떤 모델을 돌렸는지)와 데이터 접근 통제 필요

C. 데이터/스토리지/재현성
	•	현 상태: SQLite/Postgres 저장, 실행 히스토리/비교, Prompt manifest diff, Phoenix 업로드  ￼  ￼
	•	엔터프라이즈 갭:
	•	DB 스키마 마이그레이션/버전 관리(예: Alembic) 운영 체계가 문서 상 명확하지 않음
	•	대형 아티팩트(리포트/원본 데이터셋/임베딩/로그) 저장을 DB에만 의존하면 비용/성능 이슈
	•	“재현 가능한 평가”를 위해 모델 버전/프롬프트 체크섬/설정 스냅샷/의존성 버전을 강제 저장하는 정책이 필요

D. 관측성(Observability)
	•	현 상태: Phoenix 중심 트레이싱 + Drift watcher + 릴리즈 노트 자동화  ￼
	•	엔터프라이즈 갭:
	•	tracing 외에 metrics(log 기반이 아닌 Prometheus형), structured logs, SLO/알람이 표준화되어야 함
	•	온콜/장애 대응에서 “무엇을 봐야 하는지”를 서비스 레벨로 정리해야 함(런북은 좋은 시작)

E. 문서/버전의 SSoT 일관성
	•	STATUS/ROADMAP은 1.5.0 기반으로 보이는데, Observability playbook에는 “EvalVault 3.2” 표기가 있습니다. 운영팀/개발팀 관점에서 이런 불일치는 엔터프라이즈에서 큰 리스크(혼선/오배포/운영오류)입니다.  ￼  ￼  ￼
	•	Docs Hub는 STATUS를 단일 진실 소스로 두는 규칙을 말하고 있으니, “버전/호환 범위 표기”를 자동화하는 게 좋습니다.  ￼  ￼

또한 ROADMAP의 단기 작업은 “기존 개발 가이드 범위 내” 기준이므로, 엔터프라이즈화 백로그는 별도로 정의되어야 합니다.  ￼

⸻

4) 엔터프라이즈 급 개선안: 우선순위(P0/P1/P2)로 정리

아래는 “기능이 아니라 운영 가능성” 기준으로 우선순위를 매겼습니다.

P0. 엔터프라이즈에서 ‘없으면 운영이 깨지는’ 항목(필수)

P0-1) 서비스 모드 + 비동기 잡 오케스트레이션(워크로드 분리)
목표: CLI/웹은 “요청/조회”만, 실제 평가는 “워커”가 수행.
	•	추가할 것
	•	Inbound Adapter: REST API (FastAPI) 또는 gRPC
	•	Outbound Port: JobQueuePort(큐), LockPort(idempotency/중복 실행 방지)
	•	컴포넌트: Orchestrator(API) + Worker(평가 실행) + Result Store(DB)
	•	핵심 기능
	•	submit_run() → job_id 반환
	•	get_status(job_id) / cancel(job_id) / retry(job_id)
	•	평가 결과는 run_id로 조회(저장소는 기존 StoragePort 활용)
	•	왜 지금 구조에 잘 맞나
	•	도메인 서비스는 이미 포트 기반이라 “실행 위치”만 바꾸면 됨  ￼

결과적으로 “Web UI 세션 끊김”, “CLI 종료”, “장시간 작업 타임아웃”과 같은 운영 이슈를 구조적으로 제거합니다.

P0-2) 멀티테넌시 데이터 모델 + AuthN/AuthZ(RBAC/SSO)
목표: 조직/프로젝트/사용자 단위로 데이터와 실행을 격리.
	•	도메인 엔티티 확장 예
	•	EvaluationRun에 tenant_id, project_id, created_by, created_at, tags, config_snapshot_hash 같은 필드 추가
	•	저장소 변경
	•	Storage 스키마에 tenant/project 컬럼 추가 + 인덱스
	•	Inbound 인증
	•	OIDC 기반 SSO, 최소 RBAC(예: viewer/editor/admin)
	•	감사로그
	•	“누가/언제/무엇을/어떤 키/어떤 모델로/어떤 데이터셋을 실행했는지” 기록

CLI/Web UI 중심 툴은 보통 이 단계에서 “내부 플랫폼”으로 진화합니다. (현재는 사용자 가이드가 로컬/개인 실행 흐름에 최적화되어 있음)  ￼

P0-3) 비밀키/설정 관리의 엔터프라이즈 표준화
목표: .env는 로컬 전용, 운영은 Secret Manager/Vault/KMS로.
	•	Settings(Pydantic) 구조는 유지하되, 설정 소스 체인을 명시:
	•	env → secret store → config file → default
	•	키 로테이션/권한 분리(프로젝트별 키), egress 정책(LLM API 도메인 allowlist)
	•	민감 데이터(프롬프트/컨텍스트/정답)의 로그/트레이스 내 저장 정책도 분리

P0-4) DB 마이그레이션/백업/DR(복구) 체계
목표: 운영 DB(Postgres)에서 스키마 변경을 안전하게.
	•	Alembic 같은 migration 도입 + 배포 파이프라인에 포함
	•	백업/복구(runbook) + 데이터 보존기간/아카이브 정책
	•	대형 아티팩트는 Object Storage(S3/GCS/MinIO)로 분리하고 DB에는 메타데이터/포인터만 저장

현재도 Postgres 어댑터가 존재하지만, 엔터프라이즈 운영에선 “마이그레이션 + DR”이 없으면 사실상 못 씁니다.  ￼  ￼

P0-5) 관측성 3종 세트(Logs/Metrics/Traces) + SLO
목표: Phoenix tracing은 유지하되, 서비스 레벨 운영을 가능하게.
	•	Traces: OpenTelemetry 컨텍스트 전파(이미 Phoenix 기반)  ￼
	•	Metrics:
	•	eval_runs_total, eval_run_duration_seconds, llm_requests_total, llm_cost_usd_total, queue_depth, cache_hit_rate
	•	Logs: JSON structured logging + PII redaction + trace_id correlation
	•	SLO/알람: “평가 완료율, p95 레이턴시, 실패율, 비용 폭주” 같은 운영 지표 정의

⸻

P1. 엔터프라이즈에서 ‘확실히 비용을 줄이는’ 항목(강력 권장)

P1-1) Dataset/Prompt/Model “레지스트리” + 재현성 강제
현재도 Prompt manifest diff를 다루고(Phoenix/CLI), 모델 프로필이 있지만, 엔터프라이즈에선 이것을 “레지스트리/승인 흐름”으로 올려야 합니다.  ￼  ￼
	•	Dataset Registry: 데이터셋 업로드/버전/해시/승인/접근권한
	•	Prompt Registry: 프롬프트 파일 체크섬 + 리뷰/승인 + 어떤 run에 쓰였는지 lineage
	•	Model Registry: 프로필(모델/파라미터/임베딩) 스냅샷 + 변경 이력

효과: “왜 성능이 달라졌지?”를 사람 기억이 아니라 시스템이 답함.

P1-2) 평가 실행의 “정책/예산” 레이어
	•	프로젝트별 월간/일간 비용 상한
	•	모델/메트릭/트래커 사용 정책(예: 프로덕션은 특정 모델만)
	•	대량 평가에서 rate limit + adaptive batch는 이미 있지만, 멀티 워커 환경에서 “전역 제한”이 필요  ￼

P1-3) Domain Memory의 엔터프라이즈화(격리/신뢰도/프라이버시)
Domain Memory가 강력한 차별점이 될 수 있지만, 엔터프라이즈에서 가장 민감한 영역입니다.  ￼
	•	멀티테넌시 격리(tenant_id)
	•	사실/학습/행동의 검증 워크플로우(누가 승인했는지)
	•	“망각/감쇠/삭제 요청” 정책(컴플라이언스)
	•	스토리지 확장(예: Postgres+FTS/pgvector 또는 별도 벡터DB) 고려

P1-4) 플러그인/확장 시스템의 “배포 가능한 형태” 정리
현재는 포트/어댑터 구조가 확장에 유리한데, 엔터프라이즈에서는 이를 배포/호환성/서명/버전까지 포함해 정리해야 합니다.  ￼  ￼
	•	entrypoint 기반 플러그인 로딩(메트릭/분석모듈/리포트)
	•	플러그인 호환성 체크(코어 버전 범위)
	•	(필요하면) 플러그인 승인/서명

P1-5) 운영 자동화의 서비스화
현재 Drift watcher는 스크립트/크론 형태인데, 엔터프라이즈에서는 이를 “서비스”로 만들면 운영 난이도가 급감합니다.  ￼
	•	watcher를 long-running service로 운영(k8s CronJob/Deployment)
	•	알람을 Slack뿐 아니라 PagerDuty/Teams 등으로 확장
	•	Gate 실패 시 자동 티켓/이슈 생성

⸻

P2. 있으면 ‘차별화/확산’이 쉬워지는 항목(선택)
	•	Web UI를 “내부 관리자용”으로 두고, 일반 사용자는 별도 포털로 분리(SSO/RBAC/UI 일관성)
	•	조직별 대시보드(리더보드, 모델 비교, 드리프트 히트맵)
	•	Airflow/Dagster/Argo와의 네이티브 연동(스케줄 평가)
	•	대규모 고객사 대응을 위한 멀티리전/DR 자동화(정책에 따라)

⸻

5) “엔터프라이즈 레퍼런스 아키텍처” 제안(현재 구조를 살리는 방식)

현재 EvalVault의 Ports & Adapters를 그대로 살리면서, “실행을 서비스/워커로 분리” 하는 레퍼런스를 제안하면 아래처럼 됩니다.

[Client Layer]
  - CLI (Typer)        - Web UI (React + FastAPI)      - Python SDK
          |                     |                           |
          +---------- HTTP/gRPC API -----------+-------------+
                                               |
[Service Layer / Inbound Adapter]
  - EvalVault API (FastAPI)
    - Auth (OIDC) / RBAC
    - Run Submit / Status / Cancel
    - Dataset Registry API
    - Prompt/Model Registry API
               |
               +--> Job Queue (Redis/Rabbit/SQS)  <-- Outbound Port
               |
[Worker Layer]
  - Eval Workers (N replicas)
    - RagasEvaluator / Analysis Pipeline / DomainMemory Hook
    - Provider rate limit / retry / circuit breaker
               |
[Data Layer / Outbound Adapters]
  - Postgres (metadata, run, audit, registry)
  - Object Storage (datasets, artifacts, reports)
  - Domain Memory Store (FTS/Vector)
  - Tracker (Phoenix/Langfuse/MLflow)

[Observability]
  - OpenTelemetry: logs + metrics + traces
  - Phoenix (LLM/RAG trace 분석)
  - Prometheus/Grafana, Alerting

이 방식이 좋은 이유:
	•	도메인 로직은 건드리지 않고, inbound/outbound 어댑터만 추가하면 됩니다(핵심 강점).  ￼
	•	CLI/Web UI는 여전히 유효하지만, 엔터프라이즈에 필요한 수평 확장/권한/감사/운영을 API 레이어가 담당하게 됩니다.  ￼

⸻

6) 구현 방향을 보여주는 최소 코드 스케치(핵심 3개)

아래 코드는 “어떻게 포트/어댑터로 enterprise 기능을 붙일지” 감을 주는 예시입니다.

(1) JobQueuePort 추가 + Celery 어댑터(개념 예시)

# ports/outbound/job_queue_port.py
from __future__ import annotations
from typing import Protocol, Any, Mapping

class JobQueuePort(Protocol):
    def enqueue(self, job_type: str, payload: Mapping[str, Any], *, idempotency_key: str) -> str: ...
    def get_status(self, job_id: str) -> Mapping[str, Any]: ...
    def cancel(self, job_id: str) -> bool: ...

# adapters/outbound/queue/celery_adapter.py (개념)
from __future__ import annotations
from typing import Any, Mapping
from celery import Celery

class CeleryJobQueueAdapter:
    def __init__(self, broker_url: str):
        self._celery = Celery("evalvault", broker=broker_url)

    def enqueue(self, job_type: str, payload: Mapping[str, Any], *, idempotency_key: str) -> str:
        # 실제론 idempotency_key를 DB/락으로 관리
        task = self._celery.send_task(job_type, kwargs=dict(payload))
        return task.id

(2) FastAPI Inbound Adapter: “평가 제출 → job_id 반환”

# adapters/inbound/api/app.py (개념)
from __future__ import annotations
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Any

app = FastAPI()

class SubmitRunRequest(BaseModel):
    dataset_id: str
    profile: str
    metrics: list[str]
    tenant_id: str
    project_id: str

class SubmitRunResponse(BaseModel):
    job_id: str

@app.post("/v1/runs:submit", response_model=SubmitRunResponse)
def submit_run(req: SubmitRunRequest, queue=Depends(...)) -> Any:
    # idempotency_key는 (tenant, project, dataset_id, profile, metrics, prompt_checksum, ...)로 구성
    job_id = queue.enqueue(
        job_type="evalvault.tasks.run_evaluation",
        payload=req.model_dump(),
        idempotency_key=f"{req.tenant_id}:{req.project_id}:{req.dataset_id}:{req.profile}:{','.join(req.metrics)}",
    )
    return SubmitRunResponse(job_id=job_id)

(3) 구조화 로그 + trace_id 연동(운영 필수)

import logging
import json
from opentelemetry.trace import get_current_span

logger = logging.getLogger("evalvault")

def log_event(event: str, **fields):
    span = get_current_span()
    ctx = span.get_span_context() if span else None
    payload = {
        "event": event,
        "trace_id": format(ctx.trace_id, "032x") if ctx else None,
        **fields,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))

이렇게 하면 Phoenix/OTel trace와 서버 로그를 “하나의 ID”로 묶어 장애 분석이 쉬워집니다. (현재도 Phoenix 중심 트레이싱이 있으니 확장 방향이 자연스럽습니다.)  ￼

⸻

7) 문서/운영 관점의 “즉시 개선” 체크(Quick Wins)

엔터프라이즈로 가기 전에, 지금 문서/운영에서 바로 정리하면 효과 큰 것들입니다.
	1.	버전 표기 일관성 자동 검증

	•	STATUS를 SSoT로 둔다고 했으니, 플레이북/가이드 문서의 “EvalVault 버전 표기”를 CI에서 검증(문서 간 불일치 차단)  ￼  ￼  ￼

	2.	Gate/Regression/Release Notes의 “표준 파이프라인 템플릿” 제공

	•	이미 drift watcher → gate → regressions → release notes의 연결 고리가 문서화되어 있으니, 이것을 “조직 표준 CI 템플릿”으로 고정  ￼

	3.	운영 환경 권장 구성을 문서에 명시

	•	“엔터프라이즈는 기본 Postgres + object storage + API/worker 분리” 같은 권장안을 USER_GUIDE에 추가(현재는 로컬/개발자 중심 흐름이 강함)  ￼

	4.	ROADMAP 단기 작업의 범위 재정의

	•	“기존 개발 가이드 기준 미완료 없음”과 “엔터프라이즈화 백로그”를 분리해서, 운영/플랫폼 로드맵을 따로 관리  ￼  ￼

⸻

8) 최종 정리: 엔터프라이즈 급을 위한 “가장 중요한 5개”

문서 기반으로 봤을 때, 우선순위를 가장 압축하면 아래 5개가 핵심입니다.
	1.	실행을 서비스/워커로 분리(비동기 잡, 수평 확장)
	2.	멀티테넌시 + SSO/RBAC + 감사로그
	3.	운영 DB 마이그레이션/백업/아티팩트 스토리지 분리
	4.	Logs/Metrics/Traces + SLO/알람 표준화(피닉스는 강점으로 유지)
	5.	재현성(데이터셋/프롬프트/모델/설정 스냅샷) 레지스트리화

이 5개가 갖춰지면, EvalVault는 현재의 강점(헥사고날 구조, Domain Memory, Phoenix 기반 옵저버빌리티)을 유지하면서도 엔터프라이즈 운영에서 요구하는 “안전성/확장성/거버넌스”를 충족할 수 있습니다.  ￼  ￼

⸻
