# 의존성 주입/모듈 분리 전체 계획서

이 문서는 모듈 이식성을 높이기 위한 전체 계획과 상세 계획을 동시에 제공한다.
현재 단계에서는 설계와 범위를 확정하고, 단계별 리팩터링의 기준을 문서화한다.

## 목표
- Settings 의존을 진입점(Entry point)으로만 제한
- Storage/LLM/Tracker 생성 책임을 외부로 이동
- 도메인/포트 계층을 별도 패키지로 분리 가능한 구조로 정리
- 기능/동작의 하위 호환을 유지하며 점진적 전환

## 성공 기준 (Definition of Done)
- 모든 도메인 서비스가 Settings를 직접 참조하지 않음
- 모든 inbound 계층에서 Settings 직접 생성 제거
- 어댑터 생성은 entrypoint에서만 수행
- 도메인/포트 패키지 분리 후에도 기존 CLI/API 동작 유지
- 테스트/CI 정상 통과

## 전체 단계 요약
1) PR1: 컨테이너 스캐폴딩 + 주입 경로 추가 (하위 호환)
2) PR2: CLI commands에서 Settings 직접 호출 제거
3) PR3: API adapter에서 Settings 직접 호출 제거
4) PR4: Storage/LLM/Tracker factory 호출 외부화
5) PR5: 도메인/포트 분리 패키징

## 상세 계획

### PR1: 컨테이너 스캐폴딩 + 주입 경로 추가
**목표**: 외부 주입 경로를 만들고 기존 동작은 유지한다.

**신규 파일**
- `src/evalvault/app/context.py`
- `src/evalvault/app/container.py`

**컨테이너 인터페이스**
- `AppContext` (dataclass)
  - settings: Settings
  - storage: StoragePort
  - llm: LLMPort
  - tracker: TrackerPort
  - domain_memory: DomainMemoryPort

- `build_app_context(settings: Settings | None = None) -> AppContext`
  - settings가 없으면 Settings 생성
  - 내부 factory로 의존성 생성 (임시)

**수정 대상 (주입 경로 추가)**
- `src/evalvault/adapters/inbound/cli/commands/run.py`
  - 기존 동작 유지, `context: AppContext | None = None` 옵션 추가
- `src/evalvault/adapters/inbound/api/adapter.py`
  - 기존 동작 유지, `context` 주입 경로 추가
- `src/evalvault/adapters/inbound/mcp/tools.py`
  - context에서 storage/llm 사용

**검증**
- 기존 CLI/API 사용 방식 그대로 동작
- context 주입 시 동일 결과

---

### PR2: CLI Settings 직접 호출 제거
**목표**: CLI 계층에서 Settings 직접 생성 제거

**변경 방향**
- CLI entrypoint에서 Settings/Context 생성
- commands는 settings 대신 context에서 의존성 사용

**주요 파일**
- `src/evalvault/adapters/inbound/cli/commands/*.py`
- `src/evalvault/adapters/inbound/cli/app.py`

**검증**
- CLI 기능 전체 동작 유지
- 환경변수 변경 시 동일 결과

---

### PR3: API Settings 직접 호출 제거
**목표**: API 계층에서 Settings 직접 생성 제거

**변경 방향**
- FastAPI create_app에서 Settings/Context 생성
- routers/adapters에서 context를 통해 접근

**주요 파일**
- `src/evalvault/adapters/inbound/api/main.py`
- `src/evalvault/adapters/inbound/api/adapter.py`
- `src/evalvault/adapters/inbound/api/routers/*.py`

**검증**
- API 기능 전체 동작 유지
- CORS/Rate limit/Auth 설정 유지

---

### PR4: Factory 호출 외부화
**목표**: 내부 factory 의존 제거 (external wiring)

**변경 방향**
- build_storage_adapter/build_domain_memory_adapter를 entrypoint에서 호출
- 서비스/핸들러는 포트 인터페이스만 받음

**주요 파일**
- `src/evalvault/adapters/outbound/storage/factory.py`
- `src/evalvault/adapters/outbound/domain_memory/factory.py`
- `src/evalvault/adapters/outbound/llm/factory.py`
- `src/evalvault/adapters/inbound/*` (호출 제거)

**검증**
- 동일 설정으로 동일한 어댑터 생성
- 테스트 통과

---

### PR5: 도메인/포트 분리 패키징
**목표**: 모듈 분리 구조 완성

**제안 구조**
```
evalvault-core/
  domain/
  ports/
  services/

evalvault-adapters/
  outbound/
  inbound/

evalvault-app/
  cli/
  api/
  wiring/
```

**패키징 원칙**
- core는 외부 라이브러리 의존 최소화
- adapters는 core에 의존하지만 core는 adapters를 모름
- app은 core+adapters를 묶는 역할

**검증**
- core만 별도 설치 가능
- adapters/app에서 기존 CLI/API 동작 유지

---

## 리스크 및 대응
- 리스크: Settings 직접 접근 제거 과정에서 옵션 누락
  - 대응: PR마다 테스트/스냅샷 비교
- 리스크: CLI/APIs에서 초기화 순서 문제
  - 대응: AppContext 초기화 순서 문서화
- 리스크: 외부 의존성 분리 시 import 경로 붕괴
  - 대응: 단계적 패키지 이동

## 테스트 전략
- PR1~PR3: 기존 테스트 그대로 통과
- PR4: storage/llm/tracker 관련 unit/integration 테스트 추가
- PR5: core 패키지 단독 설치 테스트

## 결정 필요 항목
- 컨테이너 네이밍: `AppContext` vs `AppContainer`
- 외부 wiring 위치: CLI entrypoint vs API create_app
- 분리 레포 구조(모노레포 vs 멀티레포)
