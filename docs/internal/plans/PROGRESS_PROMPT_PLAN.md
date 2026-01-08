# CLI/Web 진행률 + 프롬프트 커스터마이징 확장 계획

## 배경
- CLI `evalvault run`은 스피너만 출력되어 ETA/처리 수를 알기 어렵다.
- Web UI는 진행 퍼센트만 보여주고, completed/total이나 ETA가 없다.
- Ragas 메트릭 프롬프트 커스터마이징과 “대상 시스템”의 시스템 프롬프트 기록·비교·분석 기능이 요구된다.

---

## 목표
1. CLI와 Web 모두 `completed/total + ETA`를 기본 출력한다.
2. Ragas 메트릭 프롬프트를 안전하게 오버라이드할 수 있다.
3. 대상 시스템의 시스템 프롬프트를 입력·저장(DB 포함)하고, 실행 간 비교·분석이 가능하다.
4. 사용자가 쉽게 쓰는 흐름(입력→평가→비교/분석)이 문서와 UI에 일관되게 반영된다.

## 비목표(초기 범위 제외)
- 정확한 “모델 내부 실제 프롬프트” 자동 추출(대상 시스템이 외부일 수 있음).
- 모든 외부 툴(promptfoo, dspy)과의 완전 자동 양방향 동기화.
- 복잡한 실시간 ETA 예측(스트리밍/병렬 상황은 근사치 제공).

---

## 현재 상태 요약
- CLI 진행률 유틸(`evaluation_progress`, `streaming_progress`)은 있으나 `run`에서 사용하지 않음.
- API는 SSE로 진행률 이벤트를 보내지만, UI는 퍼센트만 사용.
- 프롬프트 관련:
  - Phoenix prompt manifest/metadata 추적 기능은 존재(`--prompt-files`, `--prompt-manifest`).
  - Ragas 메트릭 프롬프트 오버라이드, 시스템 프롬프트 저장 기능은 없음.
  - DB에는 prompt 전용 테이블이 없음(메타데이터 JSON 저장만 가능).

---

## 진행률 표시 설계

### CLI
- 비스트리밍: `evaluation_progress` 사용해 `completed/total + ETA` 표시.
- 병렬: `on_progress` 콜백을 통해 완료 카운트 업데이트.
- 스트리밍:
  - `streaming_progress`로 처리된 케이스 수와 처리 속도 표기.
  - 총량을 알 수 있으면 `total` 업데이트, 알 수 없으면 `?/` 형태로 유지.
  - 필요 시 `--stream-estimate` 옵션으로 사전 카운트(추가 비용 명시).

### Web
- SSE 이벤트에 `current`, `total`, `elapsed_seconds`, `eta_seconds`, `rate` 추가.
- UI에 `completed/total`, `ETA`, 처리 속도를 표시.
- 백엔드 ETA가 없을 경우 프론트에서 간단 추정(최근 진행률 기반).

### 진행률 이벤트 표준(안)
```json
{
  "type": "progress",
  "data": {
    "current": 120,
    "total": 500,
    "percent": 24.0,
    "elapsed_seconds": 85.2,
    "eta_seconds": 270.3,
    "rate": 1.4,
    "status": "running",
    "message": "Evaluated tc-0120"
  }
}
```

---

## 프롬프트 커스터마이징 설계

### 용어 정리
- **평가 프롬프트**: Ragas 메트릭이 사용하는 평가용 프롬프트.
- **대상 시스템 프롬프트**: 실제 서비스 LLM의 시스템 프롬프트(정답 생성에 영향).
- **프롬프트 세트**: 위 두 종류를 묶어 “평가 시점의 프롬프트 상태”로 관리.

### 기능 축
1. **Ragas 프롬프트 오버라이드**
   - 메트릭별 템플릿 파일 또는 YAML로 입력.
   - 런타임에서 Ragas 메트릭 객체에 프롬프트 주입.
   - 버전/체크섬을 함께 기록.

2. **대상 시스템 프롬프트 저장**
   - CLI/Web 입력 지원(`--system-prompt`, `--system-prompt-file`).
   - DB 저장(텍스트 + 체크섬 + 메타).
   - 평가 실행 시 run과 연결.

3. **비교/분석**
   - 프롬프트 변경 내역(diff)과 평가 결과를 연결.
   - 프롬프트 세트별 평균/분산, 통계 유의성(가능하면 ANOVA/효과크기).
   - LLM 기반 요약(자연어 분석) + 수치 지표 병행.

4. **외부 툴 연계**
   - promptfoo: 프롬프트 세트 → promptfoo YAML 내보내기, 결과 JSON 가져오기.
   - dspy: prompt 템플릿/파라미터를 EvalVault prompt 세트로 스냅샷.

---

## 데이터 모델(안)

### Option A: 메타데이터 JSON 확장(가장 빠름)
- `evaluation_runs.metadata`에 `prompts` 필드 추가:
  - `system_prompt`: { content, checksum, source, version }
  - `ragas_prompts`: { metric_name: { content, checksum, source } }
- 장점: 마이그레이션 간단.
- 단점: 쿼리/비교가 어렵고 UI/분석에 추가 파싱 필요.

### Option B: 전용 테이블(권장)
- `prompts`: prompt_id, name, kind(system|ragas), content, checksum, source, created_at, notes
- `prompt_sets`: set_id, name, description, created_at
- `prompt_set_items`: set_id, prompt_id, role(metric_name/system), order
- `run_prompt_sets`: run_id, set_id
- 장점: 비교/분석/이력 관리에 유리.
- 단점: 마이그레이션 필요.

초기에는 Option A로 빠르게 가고, 분석/비교 UI가 필요해지면 Option B로 확장.

---

## UX 흐름(사용자 관점)

### CLI (MVP)
1. 프롬프트 저장(선택)
   - `evalvault prompts register --name "prod-sys-v3" --file sys.txt --kind system`
2. 평가 실행
   - `evalvault run dataset.json --metrics faithfulness --system-prompt-file sys.txt`
   - `evalvault run dataset.json --metrics faithfulness --ragas-prompts config/ragas_prompts.yaml`
3. 비교/확인
   - `evalvault prompts diff run_1 run_2`
   - `evalvault history --format table`에서 프롬프트 변경 표기

### Web
- Evaluation Studio: 시스템 프롬프트 입력/선택 + 메트릭 프롬프트 세트 선택.
- Run Details: 프롬프트 스냅샷/체크섬 표시, diff 버튼 제공.
- 비교 화면: 프롬프트 세트 별 성능 차이/상관 분석 표시.

---

## 단계별 개발 로드맵

### Phase 1: 진행률 개선 (CLI/Web 공통)
- CLI `evalvault run`에서 `evaluation_progress` 사용.
- API SSE에 elapsed/eta/rate 포함.
- Web UI에 completed/total, ETA, 속도 표시.
- 스트리밍 모드에서는 total 미정 가능성을 UI에 명시.

### Phase 2: 프롬프트 저장/추적 최소 기능
- `--system-prompt` / `--system-prompt-file` 추가 (CLI + API).
- `--ragas-prompts`(YAML)로 메트릭 프롬프트 오버라이드.
- run metadata에 프롬프트 스냅샷/체크섬 저장.

### Phase 3: 비교/분석
- prompt diff CLI/화면 추가.
- 프롬프트 세트별 통계(평균/분산/효과크기/상관).
- 자연어 요약 리포트(기존 분석 파이프라인에 플러그인).

### Phase 4: 외부 툴 연계
- promptfoo/dspy export/import CLI 추가.
- 자동 평가 파이프라인(예: promptfoo 결과를 EvalVault run으로 수집).

---

## 리스크와 대응
- **Ragas API 변화**: 메트릭 프롬프트 오버라이드 대상 속성명이 버전마다 다름 → 버전별 어댑터와 경고 로그 필요.
- **ETA 정확도**: 네트워크 지연/병렬 실행 영향 → “근사치”임을 명시.
- **민감정보**: 시스템 프롬프트에 민감 데이터 포함 가능 → 마스킹 옵션과 저장 길이 제한 제공.

---

## 테스트/검증 포인트
- CLI 진행률 출력: 단일/병렬/스트리밍 모드별 ETA/수량 확인.
- Web SSE 이벤트: 필드 누락 시 UI fallback 확인.
- 프롬프트 오버라이드: 특정 메트릭만 변경되는지 검증.
- 메타데이터 저장: run 조회 시 프롬프트 스냅샷 확인.

---

## 오픈 질문
1. Ragas 메트릭별 프롬프트 오버라이드를 어떤 포맷(YAML/JSON)으로 받을지?
2. 시스템 프롬프트 저장을 “메타데이터 JSON”으로 시작해도 되는지, 즉시 테이블로 갈지?
3. promptfoo/dspy 연계는 먼저 export만 제공하고 import는 후순위로 둘지?
