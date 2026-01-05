"""Dataset template generators for JSON/CSV/XLSX."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from openpyxl import Workbook

from evalvault.adapters.outbound.dataset.thresholds import THRESHOLD_COLUMNS

TEMPLATE_COLUMNS = ("id", "question", "answer", "contexts", "ground_truth", *THRESHOLD_COLUMNS)


def build_dataset_template_payload() -> dict[str, Any]:
    """Build an empty dataset template payload for JSON exports."""
    return {
        "name": "",
        "version": "",
        "description": "",
        "thresholds": {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
            "factual_correctness": None,
            "semantic_similarity": None,
        },
        "metadata": {},
        "test_cases": [
            {
                "id": "",
                "question": "",
                "answer": "",
                "contexts": [],
                "ground_truth": "",
                "metadata": {},
            }
        ],
    }


def render_dataset_template_json() -> str:
    """Render the dataset template as JSON string."""
    payload = build_dataset_template_payload()
    return json.dumps(payload, indent=2)


def render_dataset_template_csv() -> str:
    """Render the dataset template as CSV string."""
    return ",".join(TEMPLATE_COLUMNS) + "\n"


def render_dataset_template_xlsx() -> bytes:
    """Render the dataset template as XLSX bytes."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "dataset"
    worksheet.append(list(TEMPLATE_COLUMNS))

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


__all__ = [
    "build_dataset_template_payload",
    "render_dataset_template_csv",
    "render_dataset_template_json",
    "render_dataset_template_xlsx",
]
