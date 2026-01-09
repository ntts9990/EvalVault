"""Run change detector module."""

from __future__ import annotations

import difflib
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, truncate_text
from evalvault.domain.entities import EvaluationRun, PromptSetBundle
from evalvault.ports.outbound.storage_port import StoragePort


class RunChangeDetectorModule(BaseAnalysisModule):
    """Detect configuration/prompt changes between two runs."""

    module_id = "run_change_detector"
    name = "Run Change Detector"
    description = "Compare run metadata and prompt snapshots to summarize changes."
    input_types = ["runs"]
    output_types = ["change_summary"]
    requires = ["run_loader"]
    tags = ["comparison", "prompt", "config"]

    def __init__(self, storage: StoragePort | None = None) -> None:
        self._storage = storage

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}
        max_lines = params.get("max_lines")
        if max_lines is None:
            max_lines = additional.get("prompt_diff_max_lines", 40)
        try:
            max_lines = int(max_lines)
        except (TypeError, ValueError):
            max_lines = 40

        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs: list[EvaluationRun] = runs_output.get("runs", [])
        missing_run_ids = runs_output.get("missing_run_ids", [])

        if len(runs) < 2:
            return {
                "summary": {
                    "note": "Not enough runs to compare.",
                    "missing_run_ids": missing_run_ids,
                },
                "dataset_changes": [],
                "config_changes": [],
                "prompt_changes": {
                    "status": "missing",
                    "changes": [],
                    "summary": {},
                    "prompt_sets": {},
                    "notes": ["비교 대상 실행이 부족합니다."],
                },
            }

        run_a, run_b = runs[0], runs[1]

        dataset_changes = self._compare_dataset(run_a, run_b)
        config_changes = self._compare_config(run_a, run_b)
        prompt_changes = self._compare_prompts(run_a, run_b, max_lines=max_lines)

        summary = {
            "run_a": run_a.run_id,
            "run_b": run_b.run_id,
            "dataset_changed": bool(dataset_changes),
            "config_change_count": len(config_changes),
            "prompt_change_count": prompt_changes.get("summary", {}).get("changed", 0),
            "missing_run_ids": missing_run_ids,
        }

        return {
            "summary": summary,
            "dataset_changes": dataset_changes,
            "config_changes": config_changes,
            "prompt_changes": prompt_changes,
        }

    def _compare_dataset(self, run_a: EvaluationRun, run_b: EvaluationRun) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        changes.extend(self._diff_value("dataset_name", run_a.dataset_name, run_b.dataset_name))
        changes.extend(
            self._diff_value("dataset_version", run_a.dataset_version, run_b.dataset_version)
        )
        changes.extend(
            self._diff_value(
                "total_test_cases",
                run_a.total_test_cases,
                run_b.total_test_cases,
            )
        )
        return changes

    def _compare_config(self, run_a: EvaluationRun, run_b: EvaluationRun) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        changes.extend(self._diff_value("model_name", run_a.model_name, run_b.model_name))

        metrics_a = sorted(set(run_a.metrics_evaluated or []))
        metrics_b = sorted(set(run_b.metrics_evaluated or []))
        changes.extend(self._diff_value("metrics_evaluated", metrics_a, metrics_b))

        thresholds_a = {metric: round(run_a._get_threshold(metric), 4) for metric in metrics_a}
        thresholds_b = {metric: round(run_b._get_threshold(metric), 4) for metric in metrics_b}
        changes.extend(self._diff_value("thresholds", thresholds_a, thresholds_b))

        tracker_keys = [
            "run_mode",
            "threshold_profile",
            "evaluation_task",
            "project",
            "prompt_config",
            "retriever",
            "domain_memory",
        ]
        for key in tracker_keys:
            changes.extend(
                self._diff_value(
                    key,
                    run_a.tracker_metadata.get(key),
                    run_b.tracker_metadata.get(key),
                )
            )

        changes.extend(
            self._diff_value(
                "ragas_prompt_overrides",
                run_a.tracker_metadata.get("ragas_prompt_overrides"),
                run_b.tracker_metadata.get("ragas_prompt_overrides"),
            )
        )

        return [change for change in changes if change]

    def _compare_prompts(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
        *,
        max_lines: int,
    ) -> dict[str, Any]:
        prompt_bundle_a = self._load_prompt_set(run_a.run_id)
        prompt_bundle_b = self._load_prompt_set(run_b.run_id)
        prompt_sets = {
            "run_a": self._prompt_set_summary(prompt_bundle_a),
            "run_b": self._prompt_set_summary(prompt_bundle_b),
        }

        if prompt_bundle_a and prompt_bundle_b:
            roles_a = self._bundle_to_role_map(prompt_bundle_a)
            roles_b = self._bundle_to_role_map(prompt_bundle_b)
            all_roles = sorted(set(roles_a) | set(roles_b))
            changes = []
            same = 0
            changed = 0
            missing = 0

            for role in all_roles:
                item_a = roles_a.get(role)
                item_b = roles_b.get(role)
                if not item_a or not item_b:
                    missing += 1
                    changes.append(
                        {
                            "role": role,
                            "status": "missing",
                            "prompt_a": self._prompt_brief(item_a),
                            "prompt_b": self._prompt_brief(item_b),
                        }
                    )
                    continue

                if item_a["checksum"] == item_b["checksum"]:
                    same += 1
                    continue

                changed += 1
                diff_lines = list(
                    difflib.unified_diff(
                        item_a["content"].splitlines(),
                        item_b["content"].splitlines(),
                        fromfile=f"{run_a.run_id[:8]}:{role}",
                        tofile=f"{run_b.run_id[:8]}:{role}",
                        lineterm="",
                    )
                )
                changes.append(
                    {
                        "role": role,
                        "status": "changed",
                        "prompt_a": self._prompt_brief(item_a),
                        "prompt_b": self._prompt_brief(item_b),
                        "diff_preview": diff_lines[:max_lines],
                    }
                )

            return {
                "status": "available",
                "changes": changes,
                "summary": {"same": same, "changed": changed, "missing": missing},
                "prompt_sets": prompt_sets,
                "notes": [],
            }

        summary_only = self._compare_prompt_summary(run_a, run_b)
        if summary_only:
            return {
                "status": "summary_only",
                "changes": summary_only.get("changes", []),
                "summary": summary_only.get("summary", {}),
                "prompt_sets": prompt_sets,
                "notes": [
                    "Prompt snapshot 본문이 없어 체크섬만 비교했습니다.",
                    "상세 diff를 보려면 --db로 prompt_set을 저장하세요.",
                ],
            }

        return {
            "status": "missing",
            "changes": [],
            "summary": {},
            "prompt_sets": prompt_sets,
            "notes": [
                "Prompt snapshot을 찾을 수 없습니다.",
                "평가 시 --db와 --system-prompt/--ragas-prompts 옵션을 사용하세요.",
            ],
        }

    def _compare_prompt_summary(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
    ) -> dict[str, Any] | None:
        summary_a = run_a.tracker_metadata.get("prompt_set")
        summary_b = run_b.tracker_metadata.get("prompt_set")
        if not isinstance(summary_a, dict) or not isinstance(summary_b, dict):
            return None

        changes = []
        same = 0
        changed = 0
        missing = 0

        def record(role: str, checksum_a: str | None, checksum_b: str | None) -> None:
            nonlocal same, changed, missing
            if not checksum_a or not checksum_b:
                missing += 1
                changes.append(
                    {
                        "role": role,
                        "status": "missing",
                        "checksum_a": checksum_a,
                        "checksum_b": checksum_b,
                    }
                )
                return
            if checksum_a == checksum_b:
                same += 1
                return
            changed += 1
            changes.append(
                {
                    "role": role,
                    "status": "changed",
                    "checksum_a": checksum_a,
                    "checksum_b": checksum_b,
                }
            )

        record(
            "system",
            summary_a.get("system_prompt_checksum"),
            summary_b.get("system_prompt_checksum"),
        )
        ragas_a = summary_a.get("ragas_prompt_checksums") or {}
        ragas_b = summary_b.get("ragas_prompt_checksums") or {}
        for role in sorted(set(ragas_a) | set(ragas_b)):
            record(role, ragas_a.get(role), ragas_b.get(role))

        return {
            "summary": {"same": same, "changed": changed, "missing": missing},
            "changes": changes,
        }

    def _load_prompt_set(self, run_id: str) -> PromptSetBundle | None:
        if not run_id or self._storage is None:
            return None
        try:
            return self._storage.get_prompt_set_for_run(run_id)
        except Exception:
            return None

    @staticmethod
    def _prompt_set_summary(bundle: PromptSetBundle | None) -> dict[str, Any] | None:
        if not bundle:
            return None
        return {
            "prompt_set_id": bundle.prompt_set.prompt_set_id,
            "name": bundle.prompt_set.name,
            "description": bundle.prompt_set.description,
            "created_at": bundle.prompt_set.created_at.isoformat(),
        }

    @staticmethod
    def _bundle_to_role_map(bundle: PromptSetBundle) -> dict[str, dict[str, Any]]:
        prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
        roles: dict[str, dict[str, Any]] = {}
        for item in bundle.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            roles[item.role] = {
                "checksum": prompt.checksum,
                "content": prompt.content,
                "name": prompt.name,
                "kind": prompt.kind,
                "source": prompt.source,
            }
        return roles

    @staticmethod
    def _prompt_brief(item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        content = item.get("content")
        return {
            "checksum": item.get("checksum"),
            "name": item.get("name"),
            "kind": item.get("kind"),
            "source": item.get("source"),
            "preview": truncate_text(content, 160),
        }

    @staticmethod
    def _diff_value(field: str, before: Any, after: Any) -> list[dict[str, Any]]:
        if before == after:
            return []
        return [{"field": field, "before": before, "after": after}]
