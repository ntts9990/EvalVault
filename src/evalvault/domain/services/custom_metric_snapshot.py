from __future__ import annotations

import hashlib
import inspect
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from evalvault.domain.metrics.registry import get_metric_spec_map

SCHEMA_VERSION = 1

_CUSTOM_METRIC_DETAILS: dict[str, dict[str, Any]] = {
    "entity_preservation": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "contexts"],
        "output": "0.0-1.0 (preserved_entities / context_entities)",
        "evaluation_process": "Extract numeric/keyword entities from contexts and measure how many appear in the summary.",
        "rules": {
            "numeric_entities": ["percent", "currency", "duration", "date"],
            "keywords_ko": [
                "면책",
                "제외",
                "단서",
                "다만",
                "조건",
                "자기부담",
                "한도",
                "감액",
            ],
            "keywords_en": [
                "exclusion",
                "deductible",
                "limit",
                "cap",
                "copay",
                "coinsurance",
            ],
        },
        "notes": "Insurance-risk oriented entity coverage check.",
    },
    "insurance_term_accuracy": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "contexts"],
        "output": "0.0-1.0 (verified_terms / answer_terms)",
        "evaluation_process": "Detect insurance terms in the answer and verify their presence in contexts.",
        "rules": {"terms_dictionary": "terms_dictionary.json"},
        "notes": "Insurance glossary matching with canonical/variant terms.",
    },
    "summary_accuracy": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "contexts"],
        "output": "0.0-1.0 (supported_summary_entities / summary_entities)",
        "evaluation_process": "Extract numeric/keyword entities from summary and verify their presence in contexts.",
        "rules": {
            "numeric_entities": ["percent", "currency", "duration", "date"],
            "keywords_ko": ["면책", "제외", "단서", "다만", "조건", "자기부담", "한도", "감액"],
            "keywords_en": ["exclusion", "deductible", "limit", "cap", "waiting period"],
        },
        "notes": "Penalizes summary entities not grounded in contexts.",
    },
    "summary_risk_coverage": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "metadata.summary_tags"],
        "output": "0.0-1.0 (covered_tags / expected_tags)",
        "evaluation_process": "Check if summary mentions expected insurance risk tags.",
        "rules": {
            "exclusion": ["면책", "보장 제외", "지급 불가", "exclusion"],
            "deductible": ["자기부담", "본인부담금", "deductible", "copay"],
            "limit": ["한도", "상한", "최대", "limit", "cap"],
            "waiting_period": ["면책기간", "대기기간", "waiting period"],
            "condition": ["조건", "단서", "다만", "condition"],
            "documents_required": ["서류", "진단서", "영수증", "documents"],
            "needs_followup": ["확인 필요", "추가 확인", "담당자 확인", "재문의", "follow up"],
        },
        "notes": "Uses metadata summary_tags to define expected coverage.",
    },
    "summary_non_definitive": {
        "evaluation_method": "rule-based",
        "inputs": ["answer"],
        "output": "1.0 if definitive claims absent else 0.0",
        "evaluation_process": "Detect definitive expressions that increase liability risk.",
        "rules": {
            "patterns_ko": ["무조건", "반드시", "100%", "전액 지급", "확실히", "분명히", "절대"],
            "patterns_en": [
                "always",
                "guaranteed",
                "definitely",
                "certainly",
                "absolutely",
                "100%",
            ],
        },
        "notes": "Higher is safer; penalizes absolute guarantees.",
    },
    "summary_needs_followup": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "metadata.summary_tags"],
        "output": "1.0 if follow-up guidance matches expected need",
        "evaluation_process": "Check follow-up guidance when needs_followup tag exists.",
        "rules": {
            "followup_keywords": [
                "확인 필요",
                "추가 확인",
                "담당자 확인",
                "재문의",
                "추가 문의",
                "follow up",
            ]
        },
        "notes": "Requires tags to avoid false penalties.",
    },
    "no_answer_accuracy": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "ground_truth"],
        "output": "1.0 if abstention behavior matches, else 0.0",
        "evaluation_process": "Detect abstention patterns in answer and ground_truth and compare behavior.",
        "rules": {"patterns": "Korean/English regex patterns"},
        "notes": "Hallucination/abstention behavior check.",
    },
    "exact_match": {
        "evaluation_method": "string-match",
        "inputs": ["answer", "ground_truth"],
        "output": "1.0 exact match else 0.0",
        "evaluation_process": "Normalize text and compare exact match with optional strict number matching.",
        "rules": {"normalize": True, "number_strict": True},
        "notes": "Token/number strict matching for factual answers.",
    },
    "f1_score": {
        "evaluation_method": "token-overlap",
        "inputs": ["answer", "ground_truth"],
        "output": "0.0-1.0 (weighted F1)",
        "evaluation_process": "Tokenize, compute weighted precision/recall/F1 with number emphasis.",
        "rules": {"number_weight": 2.0},
        "notes": "Token-level overlap with numeric weighting.",
    },
    "mrr": {
        "evaluation_method": "retrieval-rank",
        "inputs": ["ground_truth", "contexts"],
        "output": "0.0-1.0 (1/rank of first relevant context)",
        "evaluation_process": "Compute relevance by token overlap and take reciprocal rank of first hit.",
        "rules": {"relevance_threshold": 0.3},
        "notes": "Ranking quality of retrieved contexts.",
    },
    "ndcg": {
        "evaluation_method": "retrieval-rank",
        "inputs": ["ground_truth", "contexts"],
        "output": "0.0-1.0 (NDCG@K)",
        "evaluation_process": "Compute graded relevance per context and calculate NDCG.",
        "rules": {"k": 10, "use_graded": True},
        "notes": "Ranking quality across all relevant contexts.",
    },
    "hit_rate": {
        "evaluation_method": "retrieval-rank",
        "inputs": ["ground_truth", "contexts"],
        "output": "1.0 if any relevant context in top K else 0.0",
        "evaluation_process": "Check whether top-K contexts contain a relevant hit.",
        "rules": {"k": 10, "relevance_threshold": 0.3},
        "notes": "Recall@K style coverage check.",
    },
    "confidence_score": {
        "evaluation_method": "rule-based",
        "inputs": ["answer", "ground_truth", "contexts"],
        "output": "0.0-1.0 (weighted confidence)",
        "evaluation_process": "Combine context coverage, answer specificity, and consistency scores.",
        "rules": {"coverage": 0.4, "specificity": 0.3, "consistency": 0.3},
        "notes": "Heuristic confidence signal for human escalation.",
    },
    "contextual_relevancy": {
        "evaluation_method": "token-overlap",
        "inputs": ["question", "contexts"],
        "output": "0.0-1.0 (avg relevancy)",
        "evaluation_process": "Measure question-context token overlap and average across contexts.",
        "rules": {"relevance_threshold": 0.35},
        "notes": "Reference-free context relevance check.",
    },
}


def _hash_file(path: str | Path | None) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    payload = file_path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def _resolve_source_path(metric_class: type[Any]) -> str | None:
    try:
        source = inspect.getsourcefile(metric_class)
    except TypeError:
        return None
    if not source:
        return None
    return str(Path(source).resolve())


def build_custom_metric_snapshot(
    metric_classes: dict[str, type[Any]],
    metrics: Iterable[str],
) -> dict[str, Any] | None:
    custom_names = [name for name in metrics if name in metric_classes]
    if not custom_names:
        return None

    spec_map = get_metric_spec_map()
    rows: list[dict[str, Any]] = []
    for metric_name in custom_names:
        metric_class = metric_classes.get(metric_name)
        if metric_class is None:
            continue
        source_path = _resolve_source_path(metric_class)
        details = _CUSTOM_METRIC_DETAILS.get(metric_name, {})
        spec = spec_map.get(metric_name)
        rows.append(
            {
                "metric_name": metric_name,
                "source": "custom",
                "description": spec.description if spec else None,
                "evaluation_method": details.get("evaluation_method"),
                "inputs": details.get("inputs"),
                "output": details.get("output"),
                "evaluation_process": details.get("evaluation_process"),
                "rules": details.get("rules"),
                "notes": details.get("notes"),
                "implementation_path": source_path,
                "implementation_hash": _hash_file(source_path),
            }
        )

    return {"schema_version": SCHEMA_VERSION, "metrics": rows}
