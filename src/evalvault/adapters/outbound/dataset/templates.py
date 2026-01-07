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


def build_method_input_template_payload() -> dict[str, Any]:
    """Build a question-first template payload for method inputs."""
    return {
        "name": "base_questions_template",
        "version": "1.0.0",
        "metadata": {
            "domain": "auto_insurance",
            "language": "en",
            "description": "Question-first template for method plugins",
        },
        "thresholds": {
            "faithfulness": 0.7,
            "answer_relevancy": 0.7,
        },
        "test_cases": [
            {
                "id": "tc-001",
                "question": "How is auto insurance premium calculated?",
                "ground_truth": (
                    "Premiums depend on vehicle details, driver profile, and selected coverage."
                ),
                "contexts": [
                    "Premiums are calculated based on vehicle type, driver age, claim history, and coverage."
                ],
                "metadata": {
                    "intent": "explanation",
                    "difficulty": "medium",
                },
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


def render_method_input_template_json() -> str:
    """Render the method input template as JSON string."""
    payload = build_method_input_template_payload()
    return json.dumps(payload, indent=2)


__all__ = [
    "build_dataset_template_payload",
    "build_method_input_template_payload",
    "render_dataset_template_csv",
    "render_dataset_template_json",
    "render_dataset_template_xlsx",
    "render_method_input_template_json",
]
