"""Numeric serialization determinism for RegressionGateReport (Phase 1 hash readiness).

`canonical_float` collapses cross-platform / cross-scipy-version float noise to a
single representation so the regress JSON is deterministic and hash-anchorable.
Calculation logic is unchanged — only serialization is canonicalized.
"""

from __future__ import annotations

import json
import math

from evalvault.domain.entities.analysis import EffectSizeLevel
from evalvault.domain.services.regression_gate_service import (
    CANONICAL_FLOAT_DECIMALS,
    RegressionMetricResult,
    canonical_float,
)


def test_canonical_float_collapses_ulp_jitter() -> None:
    assert canonical_float(0.1 + 0.2) == 0.3
    assert canonical_float(0.05000000001) == 0.05


def test_canonical_float_normalizes_negative_zero() -> None:
    assert canonical_float(-0.0) == 0.0
    assert json.dumps(canonical_float(-0.0)) == "0.0"
    assert json.dumps(canonical_float(-1e-20)) == "0.0"


def test_canonical_float_passes_through_non_finite() -> None:
    assert math.isnan(canonical_float(float("nan")))
    assert canonical_float(float("inf")) == float("inf")
    assert canonical_float(float("-inf")) == float("-inf")


def test_canonical_decimals_is_six() -> None:
    assert CANONICAL_FLOAT_DECIMALS == 6


def _result(baseline_score: float) -> RegressionMetricResult:
    return RegressionMetricResult(
        metric="faithfulness",
        baseline_score=baseline_score,
        candidate_score=0.6,
        diff=0.1 + 0.2,  # 0.30000000000000004 in IEEE-754
        diff_percent=12.3456789,
        p_value=0.0123456789,
        effect_size=-0.5000000001,
        effect_level=EffectSizeLevel.MEDIUM,
        is_significant=True,
        regression=False,
    )


def test_to_dict_canonicalizes_float_jitter() -> None:
    data = _result(0.8000000001).to_dict()
    assert data["baseline_score"] == 0.8
    assert data["diff"] == 0.3
    assert data["effect_size"] == -0.5
    # Serialized form is the short canonical decimal, not the jittery repr.
    assert json.dumps(data["diff"]) == "0.3"
    assert "0.30000000" not in json.dumps(data)


def test_serialization_is_deterministic_below_precision() -> None:
    # Two results differing by < half a canonical unit serialize identically.
    a = json.dumps(_result(0.8000000001).to_dict(), sort_keys=True)
    b = json.dumps(_result(0.8000000002).to_dict(), sort_keys=True)
    assert a == b


def test_serialization_is_stable_across_calls() -> None:
    result = _result(0.8)
    assert json.dumps(result.to_dict(), sort_keys=True) == json.dumps(
        result.to_dict(), sort_keys=True
    )
