#!/usr/bin/env python3
"""RAGAS 0.4.2 호환성 및 재현성 검증 스크립트.

이 스크립트는 EvalVault가 RAGAS 0.4.2 프레임워크를 올바르게 사용하고 있는지,
그리고 재현 가능한 결과를 생성하는지 검증합니다.

사용법:
    uv run python scripts/verify_ragas_compliance.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_ragas_version() -> dict[str, Any]:
    """RAGAS 버전 확인."""
    try:
        import ragas

        version = ragas.__version__
        return {
            "status": "ok",
            "version": version,
            "expected": "0.4.2",
            "matches": version.startswith("0.4.2"),
        }
    except ImportError:
        return {"status": "error", "message": "ragas not installed"}
    except AttributeError:
        return {"status": "warning", "message": "ragas version not available"}


def check_ragas_api_usage() -> dict[str, Any]:
    """RAGAS API 사용 방식 확인."""
    from ragas import SingleTurnSample
    from ragas.metrics.collections import Faithfulness

    issues = []

    # SingleTurnSample 필드 확인
    try:
        sample = SingleTurnSample(
            user_input="test",
            response="test",
            retrieved_contexts=["test"],
            reference="test",
        )
        required_fields = {"user_input", "response", "retrieved_contexts", "reference"}
        actual_fields = set(sample.__dict__.keys())
        if not required_fields.issubset(actual_fields):
            issues.append(f"Missing fields in SingleTurnSample: {required_fields - actual_fields}")
    except Exception as e:
        issues.append(f"SingleTurnSample creation failed: {e}")

    # 메트릭 초기화 확인
    try:
        # Mock LLM이 필요하지만 구조 확인은 가능
        from unittest.mock import MagicMock

        mock_llm = MagicMock()
        metric = Faithfulness(llm=mock_llm)
        if not hasattr(metric, "ascore") and not hasattr(metric, "single_turn_ascore"):
            issues.append("Metric does not have ascore() or single_turn_ascore() method")
    except Exception as e:
        issues.append(f"Metric initialization check failed: {e}")

    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
    }


def check_evaluator_implementation() -> dict[str, Any]:
    """RagasEvaluator 구현 확인."""
    from evalvault.domain.services.evaluator import RagasEvaluator

    issues = []

    evaluator = RagasEvaluator()

    # METRIC_MAP 확인
    required_metrics = {
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "factual_correctness",
        "semantic_similarity",
    }
    actual_metrics = set(evaluator.METRIC_MAP.keys())
    if not required_metrics.issubset(actual_metrics):
        issues.append(f"Missing metrics: {required_metrics - actual_metrics}")

    # METRIC_ARGS 확인
    for metric_name in required_metrics:
        if metric_name not in evaluator.METRIC_ARGS:
            issues.append(f"Missing METRIC_ARGS for {metric_name}")

    # ascore() API 사용 확인
    import inspect

    source = inspect.getsource(evaluator._score_single_sample)
    if "ascore" not in source:
        issues.append("_score_single_sample does not use ascore() API")

    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
    }


def check_llm_adapter_integration() -> dict[str, Any]:
    """LLM 어댑터와 RAGAS 통합 확인."""
    issues = []

    try:
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.config.settings import get_settings

        settings = get_settings()
        adapter = get_llm_adapter(settings)

        # as_ragas_llm() 메서드 확인
        if not hasattr(adapter, "as_ragas_llm"):
            issues.append("LLM adapter does not have as_ragas_llm() method")
        else:
            try:
                ragas_llm = adapter.as_ragas_llm()
                if ragas_llm is None:
                    issues.append("as_ragas_llm() returned None")
            except Exception as e:
                issues.append(f"as_ragas_llm() failed: {e}")

        # as_ragas_embeddings() 메서드 확인 (선택적)
        if hasattr(adapter, "as_ragas_embeddings"):
            try:
                adapter.as_ragas_embeddings()
                # None이어도 괜찮음 (일부 메트릭만 필요)
            except Exception as e:
                issues.append(f"as_ragas_embeddings() failed: {e}")

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
    }


async def test_reproducibility(dataset_path: Path, num_runs: int = 3) -> dict[str, Any]:
    """재현성 테스트: 동일 환경에서 여러 번 실행."""
    try:
        from evalvault.adapters.outbound.dataset import get_loader
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.config.settings import get_settings
        from evalvault.domain.services.evaluator import RagasEvaluator

        settings = get_settings()
        adapter = get_llm_adapter(settings)
        evaluator = RagasEvaluator()

        # 데이터셋 로드
        loader = get_loader(dataset_path)
        dataset = loader.load(dataset_path)

        results = []
        for run_num in range(num_runs):
            print(f"  실행 {run_num + 1}/{num_runs}...", end=" ", flush=True)

            run = await evaluator.evaluate(
                dataset=dataset,
                metrics=["faithfulness"],  # 빠른 테스트를 위해 하나만
                llm=adapter,
                parallel=False,  # 순차 실행으로 일관성 확보
            )

            # 결과 요약
            scores = [m.score for r in run.results for m in r.metrics]
            results.append(
                {
                    "run": run_num + 1,
                    "mean_score": sum(scores) / len(scores) if scores else 0.0,
                    "scores": scores,
                    "total_tokens": run.total_tokens,
                }
            )
            print(f"완료 (평균 점수: {results[-1]['mean_score']:.4f})")

        # 결과 비교
        mean_scores = [r["mean_score"] for r in results]
        score_variance = max(mean_scores) - min(mean_scores)

        return {
            "status": "ok",
            "num_runs": num_runs,
            "results": results,
            "score_variance": score_variance,
            "is_reproducible": score_variance < 0.05,  # 5% 이내 차이면 재현 가능
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def print_report(report: dict[str, Any]) -> None:
    """검증 결과 리포트 출력."""
    print("\n" + "=" * 70)
    print("RAGAS 0.4.2 호환성 및 재현성 검증 리포트")
    print("=" * 70)

    # 1. RAGAS 버전 확인
    print("\n[1] RAGAS 버전 확인")
    version_check = report["ragas_version"]
    if version_check["status"] == "ok":
        status_icon = "✅" if version_check["matches"] else "⚠️"
        print(f"  {status_icon} 버전: {version_check['version']}")
        if not version_check["matches"]:
            print(f"     예상: {version_check['expected']}")
    else:
        print(f"  ❌ {version_check.get('message', 'Unknown error')}")

    # 2. RAGAS API 사용 확인
    print("\n[2] RAGAS API 사용 확인")
    api_check = report["ragas_api"]
    status_icon = "✅" if api_check["status"] == "ok" else "⚠️"
    print(f"  {status_icon} 상태: {api_check['status']}")
    if api_check.get("issues"):
        for issue in api_check["issues"]:
            print(f"     - {issue}")

    # 3. Evaluator 구현 확인
    print("\n[3] RagasEvaluator 구현 확인")
    eval_check = report["evaluator_impl"]
    status_icon = "✅" if eval_check["status"] == "ok" else "⚠️"
    print(f"  {status_icon} 상태: {eval_check['status']}")
    if eval_check.get("issues"):
        for issue in eval_check["issues"]:
            print(f"     - {issue}")

    # 4. LLM 어댑터 통합 확인
    print("\n[4] LLM 어댑터 통합 확인")
    adapter_check = report["llm_adapter"]
    status_icon = "✅" if adapter_check["status"] == "ok" else "⚠️"
    print(f"  {status_icon} 상태: {adapter_check['status']}")
    if adapter_check.get("issues"):
        for issue in adapter_check["issues"]:
            print(f"     - {issue}")

    # 5. 재현성 테스트
    if "reproducibility" in report:
        print("\n[5] 재현성 테스트")
        repro_check = report["reproducibility"]
        if repro_check["status"] == "ok":
            status_icon = "✅" if repro_check["is_reproducible"] else "⚠️"
            print(f"  {status_icon} 재현 가능: {repro_check['is_reproducible']}")
            print(f"     점수 분산: {repro_check['score_variance']:.6f}")
            print(f"     실행 횟수: {repro_check['num_runs']}")
            for result in repro_check["results"]:
                print(f"       실행 {result['run']}: 평균 {result['mean_score']:.4f}")
        else:
            print(f"  ❌ {repro_check.get('message', 'Unknown error')}")

    print("\n" + "=" * 70)


async def main() -> int:
    """메인 함수."""
    print("RAGAS 0.4.2 호환성 검증 시작...\n")

    report: dict[str, Any] = {}

    # 1. RAGAS 버전 확인
    print("[1/5] RAGAS 버전 확인 중...")
    report["ragas_version"] = check_ragas_version()

    # 2. RAGAS API 사용 확인
    print("[2/5] RAGAS API 사용 확인 중...")
    report["ragas_api"] = check_ragas_api_usage()

    # 3. Evaluator 구현 확인
    print("[3/5] RagasEvaluator 구현 확인 중...")
    report["evaluator_impl"] = check_evaluator_implementation()

    # 4. LLM 어댑터 통합 확인
    print("[4/5] LLM 어댑터 통합 확인 중...")
    report["llm_adapter"] = check_llm_adapter_integration()

    # 5. 재현성 테스트 (선택적, 데이터셋이 있으면 실행)
    dataset_path = project_root / "tests" / "fixtures" / "e2e" / "insurance_qa_korean.json"
    if dataset_path.exists():
        print("[5/5] 재현성 테스트 실행 중...")
        print("  (이 테스트는 LLM API 호출이 필요하며 시간이 걸릴 수 있습니다)")
        report["reproducibility"] = await test_reproducibility(dataset_path, num_runs=2)
    else:
        print("[5/5] 재현성 테스트 건너뜀 (테스트 데이터셋 없음)")
        report["reproducibility"] = {"status": "skipped", "message": "Dataset not found"}

    # 리포트 출력
    print_report(report)

    # 종료 코드 결정
    has_errors = any(
        check.get("status") == "error" for check in report.values() if isinstance(check, dict)
    )
    return 1 if has_errors else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
