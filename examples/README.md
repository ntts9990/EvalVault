# Examples

EvalVault 사용 예제를 담고 있는 디렉터리입니다.

## 예제 목록

### stage_events.jsonl

Stage 이벤트 샘플 데이터입니다. `evalvault stage` 명령으로 수집/요약/평가를 확인할 때
사용합니다.

```bash
uv run evalvault stage ingest examples/stage_events.jsonl --db data/db/evalvault.db
uv run evalvault stage summary run_20260103_001 --db data/db/evalvault.db
uv run evalvault stage compute-metrics run_20260103_001 --thresholds-json config/stage_metric_thresholds.json
```

### kg_generator_demo.py

Knowledge Graph 기반 테스트셋 생성 데모입니다.

**기능:**
- 보험 문서에서 Knowledge Graph 구축
- 단순 질문 (Simple Questions) 생성
- 다중 홉 질문 (Multi-hop Questions) 생성
- 비교 질문 (Comparison Questions) 생성
- 엔티티 타입별 질문 생성

**실행 방법:**

```bash
# 프로젝트 루트에서 실행
cd /path/to/EvalVault

# 의존성 설치 (최초 1회)
uv sync --extra dev

# 데모 실행
uv run python examples/kg_generator_demo.py
```

**예상 출력:**

```
=== Building Knowledge Graph ===

Graph Statistics:
  Total entities: 8
  Total relations: 12
  Entity types: {'organization': 3, 'product': 3, 'money': 4, ...}

=== Simple Questions ===

1. Question: 삼성생명의 종신보험 사망보험금은 얼마인가요?
   Entity: 삼성생명
   Type: organization
   Context: 삼성생명의 종신보험은 사망보험금 1억원을 보장...

=== Multi-hop Questions (2 hops) ===
...
```

## 새 예제 추가 가이드

1. `examples/` 디렉터리에 Python 파일 추가
2. 파일 상단에 docstring으로 목적 설명
3. `if __name__ == "__main__":` 블록으로 직접 실행 가능하게 작성
4. 이 README에 예제 설명 추가

## 관련 문서

- [Docs Index](../docs/INDEX.md) - 문서 허브
- [Handbook](../docs/handbook/INDEX.md) - 내부 문서 SSoT(아키텍처/워크플로/운영/품질)
